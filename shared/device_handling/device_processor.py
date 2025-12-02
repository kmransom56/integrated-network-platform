"""
Device Processor
Combines device processing from both applications
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DeviceMatcher:
    """
    Device matcher combining logic from:
    - network_map_3d classifier/device_model_matcher.py
    - enhanced-network-api-corporate device processing
    """

    def __init__(self, rules_file: Optional[str] = None):
        self.rules = {}
        if rules_file:
            self.load_rules(rules_file)

    def load_rules(self, rules_file: str):
        """Load device matching rules"""
        try:
            with open(rules_file, 'r') as f:
                self.rules = json.load(f)
            logger.info(f"Loaded {len(self.rules)} device matching rules")
        except Exception as e:
            logger.error(f"Failed to load rules file {rules_file}: {e}")
            self.rules = {}

    def match(self, mac: Optional[str] = None, model_name: Optional[str] = None,
              ip: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Match device to model and capabilities"""
        result = {
            'model': 'unknown',
            'vendor': 'unknown',
            'type': 'unknown',
            'capabilities': [],
            'confidence': 0.0
        }

        # Try MAC address matching first
        if mac:
            mac_result = self._match_by_mac(mac)
            if mac_result['confidence'] > result['confidence']:
                result.update(mac_result)

        # Try model name matching
        if model_name:
            model_result = self._match_by_model(model_name)
            if model_result['confidence'] > result['confidence']:
                result.update(model_result)

        # Try IP-based matching
        if ip:
            ip_result = self._match_by_ip(ip)
            if ip_result['confidence'] > result['confidence']:
                result.update(ip_result)

        return result

    def _match_by_mac(self, mac: str) -> Dict[str, Any]:
        """Match device by MAC address OUI"""
        mac = mac.upper().replace(':', '').replace('-', '')

        # Common vendor OUIs
        oui_mappings = {
            '00:09:0F': {'vendor': 'fortinet', 'type': 'network_device'},
            '00:0C:29': {'vendor': 'vmware', 'type': 'virtual_machine'},
            '00:50:56': {'vendor': 'vmware', 'type': 'virtual_machine'},
            '08:00:27': {'vendor': 'virtualbox', 'type': 'virtual_machine'},
            # Add more OUIs as needed
        }

        oui = mac[:8]  # First 6 hex digits with colons
        if oui in oui_mappings:
            return {
                **oui_mappings[oui],
                'confidence': 0.8,
                'matched_by': 'mac_oui'
            }

        return {'confidence': 0.0}

    def _match_by_model(self, model_name: str) -> Dict[str, Any]:
        """Match device by model name"""
        model_lower = model_name.lower()

        # Fortinet devices
        if 'fortigate' in model_lower:
            return {
                'model': model_name,
                'vendor': 'fortinet',
                'type': 'firewall',
                'capabilities': ['firewall', 'routing', 'vpn'],
                'confidence': 0.9,
                'matched_by': 'model_name'
            }
        elif 'fortiswitch' in model_lower:
            return {
                'model': model_name,
                'vendor': 'fortinet',
                'type': 'switch',
                'capabilities': ['switching', 'poe'],
                'confidence': 0.9,
                'matched_by': 'model_name'
            }
        elif 'fortiap' in model_lower:
            return {
                'model': model_name,
                'vendor': 'fortinet',
                'type': 'access_point',
                'capabilities': ['wifi', 'wlan'],
                'confidence': 0.9,
                'matched_by': 'model_name'
            }

        # Meraki devices
        if 'mx' in model_lower:
            return {
                'model': model_name,
                'vendor': 'meraki',
                'type': 'security_appliance',
                'capabilities': ['firewall', 'routing', 'vpn'],
                'confidence': 0.9,
                'matched_by': 'model_name'
            }
        elif 'ms' in model_lower:
            return {
                'model': model_name,
                'vendor': 'meraki',
                'type': 'switch',
                'capabilities': ['switching', 'poe'],
                'confidence': 0.9,
                'matched_by': 'model_name'
            }
        elif 'mr' in model_lower:
            return {
                'model': model_name,
                'vendor': 'meraki',
                'type': 'access_point',
                'capabilities': ['wifi', 'wlan'],
                'confidence': 0.9,
                'matched_by': 'model_name'
            }

        return {'confidence': 0.0}

    def _match_by_ip(self, ip: str) -> Dict[str, Any]:
        """Match device by IP address patterns"""
        # This could be extended to match known IP ranges
        # For now, return low confidence
        return {'confidence': 0.1}


class DeviceProcessor:
    """
    Device processor combining processing logic from both applications
    """

    def __init__(self, matcher: Optional[DeviceMatcher] = None):
        self.matcher = matcher or DeviceMatcher()

    def process_devices(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of devices, enriching with model information"""
        processed_devices = []

        for device in devices:
            processed = self.process_device(device)
            processed_devices.append(processed)

        logger.info(f"Processed {len(processed_devices)} devices")
        return processed_devices

    def process_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single device"""
        # Make a copy to avoid modifying the original
        processed = device.copy()

        # Enrich with model information
        model_info = self.matcher.match(
            mac=device.get('mac_address') or device.get('mac'),
            model_name=device.get('model') or device.get('name'),
            ip=device.get('ip_address') or device.get('ip')
        )

        # Update device with matched information
        if model_info['confidence'] > 0.0:
            processed.update({
                'matched_model': model_info.get('model'),
                'vendor': model_info.get('vendor'),
                'device_type': model_info.get('type'),
                'capabilities': model_info.get('capabilities', []),
                'match_confidence': model_info.get('confidence'),
                'matched_by': model_info.get('matched_by')
            })

        # Add processing metadata
        processed['processed_at'] = str(datetime.now())
        processed['processing_version'] = 'integrated-v1.0'

        return processed

    def filter_devices(self, devices: List[Dict[str, Any]],
                      filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter devices based on criteria"""
        filtered = devices.copy()

        # Filter by vendor
        if 'vendor' in filters:
            vendor_filter = filters['vendor'].lower()
            filtered = [d for d in filtered if d.get('vendor', '').lower() == vendor_filter]

        # Filter by type
        if 'type' in filters:
            type_filter = filters['type'].lower()
            filtered = [d for d in filtered if d.get('device_type', '').lower() == type_filter]

        # Filter by status
        if 'status' in filters:
            status_filter = filters['status'].lower()
            filtered = [d for d in filtered if d.get('status', '').lower() == status_filter]

        # Filter by capability
        if 'capability' in filters:
            capability_filter = filters['capability'].lower()
            filtered = [d for d in filtered
                       if capability_filter in [c.lower() for c in d.get('capabilities', [])]]

        return filtered

    def group_devices(self, devices: List[Dict[str, Any]],
                     group_by: str = 'vendor') -> Dict[str, List[Dict[str, Any]]]:
        """Group devices by specified attribute"""
        groups = {}

        for device in devices:
            key = device.get(group_by, 'unknown')
            if key not in groups:
                groups[key] = []
            groups[key].append(device)

        return groups

    def validate_devices(self, devices: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Validate device data and return valid devices with error messages"""
        valid_devices = []
        errors = []

        for i, device in enumerate(devices):
            device_errors = self._validate_device(device)
            if device_errors:
                errors.extend([f"Device {i} ({device.get('name', 'unknown')}): {error}"
                             for error in device_errors])
            else:
                valid_devices.append(device)

        return valid_devices, errors

    def _validate_device(self, device: Dict[str, Any]) -> List[str]:
        """Validate a single device"""
        errors = []

        # Required fields
        required_fields = ['id', 'name']
        for field in required_fields:
            if not device.get(field):
                errors.append(f"Missing required field: {field}")

        # MAC address format
        mac = device.get('mac_address') or device.get('mac')
        if mac:
            if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
                errors.append(f"Invalid MAC address format: {mac}")

        # IP address format
        ip = device.get('ip_address') or device.get('ip')
        if ip:
            if not re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip):
                errors.append(f"Invalid IP address format: {ip}")

        return errors