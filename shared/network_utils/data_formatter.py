"""
Network Data Formatter
Standardizes data formats from both applications for unified processing
"""

import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NetworkDataFormatter:
    """
    Unified data formatter combining formatting approaches from:
    - network_map_3d format_device_data.py
    - enhanced-network-api-corporate data processing
    """

    @staticmethod
    def standardize_device_data(device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize device data to unified format"""
        standardized = {
            'id': device_data.get('id') or device_data.get('serial') or device_data.get('mac'),
            'name': device_data.get('name') or device_data.get('hostname') or device_data.get('label'),
            'type': device_data.get('type') or device_data.get('device_type'),
            'model': device_data.get('model'),
            'serial': device_data.get('serial'),
            'ip_address': device_data.get('ip') or device_data.get('ip_address'),
            'mac_address': device_data.get('mac') or device_data.get('mac_address'),
            'status': device_data.get('status', 'unknown'),
            'location': device_data.get('location'),
            'metadata': device_data.get('metadata', {}),
            'last_seen': device_data.get('last_seen') or datetime.now().isoformat(),
            'vendor': NetworkDataFormatter._detect_vendor(device_data)
        }

        # Clean up empty values
        return {k: v for k, v in standardized.items() if v is not None}

    @staticmethod
    def _detect_vendor(device_data: Dict[str, Any]) -> Optional[str]:
        """Detect device vendor from various fields"""
        # Check model field
        model = device_data.get('model', '').lower()
        if 'forti' in model:
            return 'fortinet'
        if 'meraki' in model or 'mx' in model or 'ms' in model or 'mr' in model:
            return 'meraki'
        if 'cisco' in model:
            return 'cisco'

        # Check name field
        name = device_data.get('name', '').lower()
        if 'forti' in name:
            return 'fortinet'
        if 'meraki' in name:
            return 'meraki'

        # Check type field
        device_type = str(device_data.get('type', '')).lower()
        if 'forti' in device_type:
            return 'fortinet'
        if 'meraki' in device_type:
            return 'meraki'

        return None

    @staticmethod
    def format_topology_data(devices: List[Dict[str, Any]],
                           connections: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Format topology data for visualization"""
        formatted_devices = [NetworkDataFormatter.standardize_device_data(d) for d in devices]

        formatted_connections = []
        for source, target in connections:
            connection = {
                'source': source,
                'target': target,
                'type': 'network_link',
                'metadata': {}
            }
            formatted_connections.append(connection)

        return {
            'devices': formatted_devices,
            'connections': formatted_connections,
            'metadata': {
                'total_devices': len(formatted_devices),
                'total_connections': len(formatted_connections),
                'generated_at': datetime.now().isoformat(),
                'format_version': '1.0'
            }
        }

    @staticmethod
    def format_for_3d_visualization(topology_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format data specifically for 3D visualization (from network_map_3d)"""
        devices = []
        for device in topology_data['devices']:
            # Add 3D-specific fields
            device_3d = {
                **device,
                'position': device.get('position', {'x': 0, 'y': 0, 'z': 0}),
                'model_path': NetworkDataFormatter._get_3d_model_path(device),
                'icon_path': NetworkDataFormatter._get_icon_path(device),
                'scale': device.get('scale', 1.0)
            }
            devices.append(device_3d)

        return {
            'devices': devices,
            'connections': topology_data['connections'],
            'metadata': {
                **topology_data['metadata'],
                'visualization_type': '3d',
                'renderer_support': ['three.js', 'babylon.js']
            }
        }

    @staticmethod
    def _get_3d_model_path(device: Dict[str, Any]) -> Optional[str]:
        """Get appropriate 3D model path for device"""
        vendor = device.get('vendor')
        model = device.get('model', '').lower()

        if vendor == 'fortinet':
            if 'fortigate' in model:
                return 'models/assets/fortinet/FG-600E.glb'
            elif 'fortiswitch' in model:
                return 'models/assets/fortinet/FS-148E.glb'
            elif 'fortiap' in model:
                return 'models/assets/fortinet/FAP-432F.glb'

        # Default model
        return 'models/assets/server.glb'

    @staticmethod
    def _get_icon_path(device: Dict[str, Any]) -> Optional[str]:
        """Get appropriate icon path for device"""
        vendor = device.get('vendor')
        model = device.get('model', '').lower()

        if vendor == 'fortinet':
            if 'fortigate' in model:
                return 'icons/fortigate.svg'
            elif 'fortiswitch' in model:
                return 'icons/fortiswitch.svg'
            elif 'fortiap' in model:
                return 'icons/fortiap.svg'

        # Default icon
        return 'icons/device_generic.svg'

    @staticmethod
    def export_to_json(data: Dict[str, Any], filepath: str) -> bool:
        """Export formatted data to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Data exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export data to {filepath}: {e}")
            return False

    @staticmethod
    def export_to_manifest(devices: List[Dict[str, Any]],
                          connections: List[Tuple[str, str]],
                          layout: Dict[str, Any],
                          filepath: str) -> bool:
        """Export manifest format (from network_map_3d)"""
        try:
            manifest = {
                'devices': devices,
                'connections': [{'source': s, 'target': t} for s, t in connections],
                'layout': layout,
                'exported_at': datetime.now().isoformat(),
                'version': 'integrated-v1.0'
            }

            with open(filepath, 'w') as f:
                json.dump(manifest, f, indent=2, default=str)

            logger.info(f"Manifest exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export manifest to {filepath}: {e}")
            return False