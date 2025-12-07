"""
Unified Device Collector
Combines device collection from both applications
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from ..network_utils.network_client import NetworkClient, DeviceType, NetworkDevice
from ..network_utils.authentication import AuthManager
import logging

logger = logging.getLogger(__name__)


class UnifiedDeviceCollector:
    """
    Unified device collector combining functionality from:
    - network_map_3d device_collector.py (FortiGate direct API)
    - enhanced-network-api-corporate device_collector.py (FortiManager + Meraki)
    """

    def __init__(self, auth_manager: Optional[AuthManager] = None):
        self.auth_manager = auth_manager or AuthManager()
        self.network_client = NetworkClient()
        self.collected_devices = []

    def collect_from_fortigate(self, host: str, username: str, password: str, port: int = 443, token: Optional[str] = None) -> List[NetworkDevice]:
        """Collect devices from FortiGate (network_map_3d approach)"""
        print(f"DEBUG: collect_from_fortigate called. Host: {host}, Port: {port}, Token present: {bool(token)}")
        logger.info(f"Collecting devices from FortiGate: {host}:{port}")

        session = None
        if not token:
            # Authenticate (Session based) only if no token
            session = self.auth_manager.authenticate_fortigate(host, username, password, port=port)
            if not session:
                logger.error("Failed to authenticate with FortiGate")
                return []
        else:
            logger.info("Using API token for FortiGate authentication")

        # Update network client
        self.network_client = NetworkClient(
            fortigate_host=host,
            fortigate_port=port,
            fortigate_auth=session,
            fortigate_token=token
        )

        # Collect devices
        devices = []
        
        # 1. FortiSwitch & Connected Clients (Enhanced)
        try:
            from ..services.fortiswitch_service import get_fortiswitch_service
            # Initialize service with our configured client
            sw_service = get_fortiswitch_service(self.network_client)
            enhanced_switches = sw_service.get_enhanced_switches()
            
            for sw_data in enhanced_switches:
                # Create Switch Device
                sw_dev = NetworkDevice(
                    id=sw_data.get('serial'),
                    name=sw_data.get('name') or sw_data.get('serial'),
                    device_type=DeviceType.FORTISWITCH,
                    ip_address=sw_data.get('ip'),
                    serial=sw_data.get('serial'),
                    model=sw_data.get('model'),
                    status=sw_data.get('status'),
                    metadata={'ports': sw_data.get('ports')} # Store full port info
                )
                devices.append(sw_dev)
                
                # Extract Connected Clients from Ports
                for port in sw_data.get('ports', []):
                    for client_data in port.get('connected_devices', []):
                        # Create Client Device
                        # Check metadata for classification
                        metadata = {
                            'connected_to_switch': sw_data.get('serial'),
                            'connected_port': port.get('name'),
                            'vlan': client_data.get('vlan'),
                            'restaurant_category': client_data.get('restaurant_category')
                        }
                        
                        client_dev = NetworkDevice(
                            id=client_data.get('device_mac'),
                            name=client_data.get('device_name'),
                            device_type=DeviceType.CLIENT,
                            ip_address=client_data.get('device_ip'),
                            mac_address=client_data.get('device_mac'),
                            metadata=metadata
                        )
                        devices.append(client_dev)
                        
        except Exception as e:
            logger.error(f"Failed to run Enhanced Switch Discovery: {e}")
            # Fallback to legacy methods if enhanced fails
            try:
                devices.extend(self.network_client._get_fortiswitches())
            except: pass

        # 2. FortiAPs (Legacy method for now)
        try:
            devices.extend(self.network_client._get_fortiaps())
        except Exception as e:
            logger.error(f"Failed to collect APs: {e}")

        self.collected_devices.extend(devices)
        logger.info(f"Collected {len(devices)} devices from FortiGate (Enhanced)")
        
        # Auto-save to disk
        self.export_devices("data/discovered_devices.json")
        
        return devices

    def collect_from_fortimanager(self, host: str, username: str, password: str) -> List[NetworkDevice]:
        """Collect devices from FortiManager (enhanced-network-api-corporate approach)"""
        logger.info(f"Collecting devices from FortiManager: {host}")

        # Authenticate
        fm_auth = self.auth_manager.authenticate_fortimanager(host, username, password)
        if not fm_auth:
            logger.error("Failed to authenticate with FortiManager")
            return []

        # Use FortiManager API to get managed devices
        devices = self._collect_fortimanager_devices(fm_auth)
        self.collected_devices.extend(devices)
        logger.info(f"Collected {len(devices)} devices from FortiManager")
        return devices

    def _collect_fortimanager_devices(self, fm_auth: Dict[str, Any]) -> List[NetworkDevice]:
        """Collect devices using FortiManager API"""
        devices = []

        try:
            session = fm_auth['session']
            host = fm_auth['host']

            # Get managed devices
            devices_url = f"https://{host}/jsonrpc"
            devices_payload = {
                "id": 2,
                "method": "get",
                "params": [
                    {
                        "url": "/dvmdb/device"
                    }
                ],
                "session": fm_auth.get('session_id')
            }

            response = session.post(devices_url, json=devices_payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
                device_data = result['result'][0].get('data', [])

                for device_info in device_data:
                    device = NetworkDevice(
                        id=device_info.get('sn', ''),
                        name=device_info.get('name', device_info.get('sn', 'Unknown')),
                        device_type=self._map_fortimanager_device_type(device_info),
                        ip_address=device_info.get('ip'),
                        model=device_info.get('dev_mod', {}).get('name'),
                        serial=device_info.get('sn'),
                        status=device_info.get('conn_status', 'unknown')
                    )
                    devices.append(device)

        except Exception as e:
            logger.error(f"Error collecting FortiManager devices: {e}")

        return devices

    def _map_fortimanager_device_type(self, device_info: Dict[str, Any]) -> DeviceType:
        """Map FortiManager device type to unified enum"""
        category = device_info.get('category', '').lower()

        if 'fortigate' in category:
            return DeviceType.FORTIGATE
        elif 'fortiswitch' in category:
            return DeviceType.FORTISWITCH
        elif 'fortiap' in category:
            return DeviceType.FORTIAP
        else:
            return DeviceType.FORTIGATE  # Default

    def collect_from_meraki(self, api_key: str, org_id: Optional[str] = None) -> List[NetworkDevice]:
        """Collect devices from Meraki (enhanced-network-api-corporate approach)"""
        logger.info("Collecting devices from Meraki")

        # Set up authentication
        if not self.auth_manager.authenticate_meraki(api_key):
            logger.error("Failed to set up Meraki authentication")
            return []

        # Use Meraki API to collect devices
        devices = self._collect_meraki_devices(api_key, org_id)
        self.collected_devices.extend(devices)
        logger.info(f"Collected {len(devices)} devices from Meraki")
        return devices

    def _collect_meraki_devices(self, api_key: str, org_id: Optional[str] = None) -> List[NetworkDevice]:
        """Collect devices using Meraki API"""
        devices = []

        try:
            headers = {
                'X-Cisco-Meraki-API-Key': api_key,
                'Content-Type': 'application/json'
            }

            # Get organizations if not provided
            if not org_id:
                org_url = "https://api.meraki.com/api/v1/organizations"
                org_response = requests.get(org_url, headers=headers, timeout=30)
                org_response.raise_for_status()
                organizations = org_response.json()
                if organizations:
                    org_id = organizations[0]['id']

            if not org_id:
                logger.error("No Meraki organization found")
                return devices

            # Get devices from organization
            devices_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/devices"
            devices_response = requests.get(devices_url, headers=headers, timeout=30)
            devices_response.raise_for_status()

            device_data = devices_response.json()

            for device_info in device_data:
                device = NetworkDevice(
                    id=device_info.get('serial', ''),
                    name=device_info.get('name', device_info.get('serial', 'Unknown')),
                    device_type=self._map_meraki_device_type(device_info),
                    ip_address=device_info.get('lanIp'),
                    model=device_info.get('model'),
                    serial=device_info.get('serial'),
                    status='online' if device_info.get('lanIp') else 'offline'
                )
                devices.append(device)

        except Exception as e:
            logger.error(f"Error collecting Meraki devices: {e}")

        return devices

    def _map_meraki_device_type(self, device_info: Dict[str, Any]) -> DeviceType:
        """Map Meraki device type to unified enum"""
        model = device_info.get('model', '').upper()

        if model.startswith('MX'):
            return DeviceType.MERAKI_DEVICE  # Security appliance
        elif model.startswith('MS'):
            return DeviceType.MERAKI_SWITCH
        elif model.startswith('MR'):
            return DeviceType.MERAKI_AP
        else:
            return DeviceType.MERAKI_DEVICE  # Default

    def get_all_devices(self) -> List[NetworkDevice]:
        """Get all collected devices"""
        return self.collected_devices.copy()

    def clear_collected_devices(self):
        """Clear the collected devices list"""
        self.collected_devices.clear()

    def export_devices(self, filepath: str) -> bool:
        """Export collected devices to JSON file"""
        try:
            # Convert devices to dicts, handling Enum serialization
            devices_data = []
            for device in self.collected_devices:
                d_dict = device.__dict__.copy()
                if isinstance(d_dict.get('device_type'), DeviceType):
                    d_dict['device_type'] = d_dict['device_type'].value
                devices_data.append(d_dict)

            with open(filepath, 'w') as f:
                json.dump({
                    'devices': devices_data,
                    'total_count': len(devices_data),
                    'exported_at': str(datetime.now())
                }, f, indent=2, default=str)
            logger.info(f"Exported {len(devices_data)} devices to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export devices: {e}")
            return False

    def load_devices(self, filepath: str) -> bool:
        """Load devices from JSON file"""
        print(f"DEBUG: Loading devices from {filepath}")
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            devices_data = data.get('devices', [])
            self.collected_devices = []
            
            for d_data in devices_data:
                # Handle DeviceType enum conversion
                dev_type_str = d_data.get('device_type')
                dev_type = DeviceType.FORTIGATE # Default
                try:
                    if dev_type_str:
                        # Handle both "fortiswitch" and "DeviceType.FORTISWITCH" formats
                        if "DeviceType." in dev_type_str:
                             # Legacy format fallback
                             clean_type = dev_type_str.split('.')[-1].lower()
                             # Map legacy names if needed, or iterate enum
                             for dt in DeviceType:
                                 if dt.name.lower() == clean_type:
                                     dev_type = dt
                                     break
                        else:
                            dev_type = DeviceType(dev_type_str)
                except ValueError:
                    pass

                device = NetworkDevice(
                    id=d_data.get('id'),
                    name=d_data.get('name'),
                    device_type=dev_type,
                    ip_address=d_data.get('ip_address'),
                    mac_address=d_data.get('mac_address'),
                    model=d_data.get('model'),
                    serial=d_data.get('serial'),
                    status=d_data.get('status'),
                    location=d_data.get('location'),
                    metadata=d_data.get('metadata')
                )
                self.collected_devices.append(device)
                
            print(f"DEBUG: Loaded {len(self.collected_devices)} devices")
            logger.info(f"Loaded {len(self.collected_devices)} devices from {filepath}")
            return True
        except Exception as e:
            print(f"DEBUG: Failed to load devices: {e}")
            logger.error(f"Failed to load devices: {e}")
            return False