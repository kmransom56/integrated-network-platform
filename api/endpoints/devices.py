"""
Device Management Endpoints
Combines device APIs from both applications
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from shared.device_handling.device_collector import UnifiedDeviceCollector
from shared.device_handling.device_processor import DeviceProcessor, DeviceMatcher
from shared.device_handling.device_classifier import DeviceClassifier
from shared.network_utils.authentication import AuthManager
from shared.config.config_manager import ConfigManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class DeviceCredentials(BaseModel):
    """Device authentication credentials"""
    host: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    org_id: Optional[str] = None


class DeviceFilter(BaseModel):
    """Device filtering options"""
    vendor: Optional[str] = None
    device_type: Optional[str] = None
    status: Optional[str] = None
    capability: Optional[str] = None


@router.post("/collect")
async def collect_devices(credentials: DeviceCredentials, background_tasks: BackgroundTasks, req: Request = None):
    """
    Collect devices from configured sources
    Combines FortiGate, FortiManager, and Meraki collection
    """
    print(f"DEBUG: collect_devices endpoint called")
    logger.info(f"Collect request received. Host: {credentials.host}, User: {credentials.username}, Pass provided: {bool(credentials.password)}")
    try:
        # Initialize components
        auth_manager = AuthManager()
        collector = UnifiedDeviceCollector(auth_manager)
        
        # Get config from app state if available
        config = None
        if req and hasattr(req.app.state, 'config'):
            config = req.app.state.config

        # Fallback to env/config if credentials missing
        import os
        if not credentials.host:
            credentials.host = (config.get('fortigate_host') if config else None) or os.getenv('FORTIGATE_HOST') or os.getenv('FORTIGATE_HOSTS')
        if not credentials.username:
            credentials.username = (config.get('fortigate_username') if config else None) or os.getenv('FORTIGATE_USERNAME')
        if not credentials.password:
            credentials.password = (config.get('fortigate_password') if config else None) or os.getenv('FORTIGATE_PASSWORD')
        
        if not credentials.api_key:
            credentials.api_key = (config.get('meraki_api_key') if config else None) or os.getenv('MERAKI_API_KEY')

        logger.info(f"Resolved credentials - Host: {credentials.host}, User: {credentials.username}, Pass: {'*' * 8 if credentials.password else 'None'}")

        # Configure authentication based on provided credentials
        if credentials.host and credentials.username:
            logger.info(f"Processing FortiGate credentials for host: {credentials.host}")
            
            # Strip protocol if present
            if credentials.host.startswith('https://'):
                credentials.host = credentials.host[8:]
            elif credentials.host.startswith('http://'):
                credentials.host = credentials.host[7:]

            # Determine port
            port = 443
            
            # Check if host has port
            if ':' in credentials.host:
                try:
                    host_parts = credentials.host.split(':')
                    credentials.host = host_parts[0]
                    port = int(host_parts[1])
                except (ValueError, IndexError):
                    pass
            
            logger.info(f"Resolved FortiGate host: {credentials.host}, port: {port}")

            # If port is still default, try env lookup
            if port == 443 and credentials.host:
                # Try to find specific port for this host
                # Env var format: FORTIGATE_192_168_0_254_PORT
                env_host_key = credentials.host.replace('.', '_')
                port_key = f"FORTIGATE_{env_host_key}_PORT"
                port_str = os.getenv(port_key)
                if port_str:
                    try:
                        port = int(port_str)
                    except ValueError:
                        pass

            # Try to find specific token for this host
            # Env var format: FORTIGATE_192_168_0_254_TOKEN
            env_host_key = credentials.host.replace('.', '_')
            token_key = f"FORTIGATE_{env_host_key}_TOKEN"
            token = os.getenv(token_key)
            
            if token:
                print(f"DEBUG: Found API token for host {credentials.host}")
            
            # Only authenticate session if no token
            if not token:
                print(f"DEBUG: Authenticating with session (no token)")
                auth_manager.authenticate_fortigate(
                    credentials.host,
                    credentials.username,
                    credentials.password,
                    port=port
                )
            
            print(f"DEBUG: Adding background task for FortiGate")
            background_tasks.add_task(
                collector.collect_from_fortigate,
                credentials.host,
                credentials.username,
                credentials.password,
                port=port,
                token=token
            )

        if credentials.api_key:
            # Meraki authentication
            auth_manager.authenticate_meraki(credentials.api_key)
            background_tasks.add_task(
                collector.collect_from_meraki,
                credentials.api_key,
                credentials.org_id
            )
        
        if not (credentials.host or credentials.api_key):
             return {
                "message": "No credentials provided and no defaults found in configuration.",
                "status": "failed",
                "sources": {}
            }

        # Return initial response - collection happens in background
        return {
            "message": "Device collection started",
            "status": "running",
            "sources": {
                "fortigate": bool(credentials.host),
                "meraki": bool(credentials.api_key)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")


@router.get("/")
async def get_devices(filter: DeviceFilter = None):
    """Get collected devices with optional filtering"""
    try:
        # Initialize collector (would typically use cached/persisted data)
        auth_manager = AuthManager()
        collector = UnifiedDeviceCollector(auth_manager)

        devices = collector.get_all_devices()

        # Apply filtering if requested
        if filter:
            processor = DeviceProcessor()
            devices = processor.filter_devices(devices, filter.dict(exclude_unset=True))

        return {
            "devices": devices,
            "total_count": len(devices),
            "filter_applied": filter is not None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve devices: {str(e)}")


@router.get("/{device_id}")
async def get_device(device_id: str):
    """Get detailed information for a specific device"""
    try:
        auth_manager = AuthManager()
        collector = UnifiedDeviceCollector(auth_manager)

        # Get device details (would need to implement proper lookup)
        devices = collector.get_all_devices()
        device = next((d for d in devices if d.id == device_id), None)

        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

        # Process device with additional information
        processor = DeviceProcessor()
        processed_device = processor.process_device(device.__dict__)

        return processed_device

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get device: {str(e)}")


@router.post("/classify")
async def classify_devices():
    """Classify all collected devices"""
    try:
        auth_manager = AuthManager()
        collector = UnifiedDeviceCollector(auth_manager)
        classifier = DeviceClassifier()

        devices = collector.get_all_devices()
        device_dicts = [device.__dict__ for device in devices]

        classified_devices = classifier.classify_devices_batch(device_dicts)
        stats = classifier.get_category_stats(classified_devices)

        return {
            "classified_devices": classified_devices,
            "category_stats": stats,
            "total_classified": len(classified_devices)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/match")
async def match_device(mac: Optional[str] = None, model: Optional[str] = None, ip: Optional[str] = None):
    """Match a device using available information"""
    try:
        matcher = DeviceMatcher()
        result = matcher.match(mac=mac, model_name=model, ip=ip)

        return {
            "match_result": result,
            "input": {
                "mac": mac,
                "model": model,
                "ip": ip
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Device matching failed: {str(e)}")


@router.get("/stats")
async def get_device_stats():
    """Get statistics about collected devices"""
    try:
        auth_manager = AuthManager()
        collector = UnifiedDeviceCollector(auth_manager)
        classifier = DeviceClassifier()

        devices = collector.get_all_devices()
        device_dicts = [device.__dict__ for device in devices]

        # Get classification stats
        if device_dicts:
            classified = classifier.classify_devices_batch(device_dicts)
            category_stats = classifier.get_category_stats(classified)
        else:
            category_stats = {}

        # Basic stats
        vendors = {}
        device_types = {}
        statuses = {}

        for device in devices:
            # Count vendors
            vendor = getattr(device, 'vendor', 'unknown')
            vendors[vendor] = vendors.get(vendor, 0) + 1

            # Count device types
            device_type = getattr(device, 'device_type', 'unknown')
            device_types[device_type] = device_types.get(device_type, 0) + 1

            # Count statuses
            status = getattr(device, 'status', 'unknown')
            statuses[status] = statuses.get(status, 0) + 1

        return {
            "total_devices": len(devices),
            "by_vendor": vendors,
            "by_type": device_types,
            "by_status": statuses,
            "by_category": category_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/export")
async def export_devices(format: str = "json", filepath: Optional[str] = None):
    """Export device data"""
    try:
        auth_manager = AuthManager()
        collector = UnifiedDeviceCollector(auth_manager)

        if not filepath:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"devices_export_{timestamp}.{format}"

        success = collector.export_devices(filepath)

        if success:
            return {
                "message": "Devices exported successfully",
                "filepath": filepath,
                "format": format
            }
        else:
            raise HTTPException(status_code=500, detail="Export failed")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")