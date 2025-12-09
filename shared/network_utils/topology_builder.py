"""
Topology Builder
Combines topology building from both applications
"""

from typing import Dict, List, Any, Tuple, Optional
import math
import random
import logging

logger = logging.getLogger(__name__)


class TopologyBuilder:
    """
    Unified topology builder combining:
    - Layered layout from network_map_3d
    - Network topology from enhanced-network-api-corporate
    """

    def __init__(self):
        self.devices = []
        self.connections = []

    def build_topology(self, devices: List[Dict[str, Any]],
                       connections: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Build complete network topology"""
        self.devices = devices
        self.connections = connections

        # Apply layout algorithm
        layout = self._apply_layered_layout()

        # Add topology metadata
        topology = {
            'devices': devices,
            'connections': connections,
            'layout': layout,
            'metadata': {
                'total_devices': len(devices),
                'total_connections': len(connections),
                'layout_algorithm': 'layered',
                'topology_type': 'network'
            }
        }

        return topology

    def _apply_layered_layout(self) -> Dict[str, Any]:
        """Apply layered layout algorithm (from network_map_3d)"""
        # Group devices by type/layer
        layers = self._group_devices_by_layer()

        # Calculate positions for each layer
        layout_positions = {}
        layer_height = 200  # Vertical spacing between layers
        device_spacing = 150  # Horizontal spacing between devices

        current_y = 0
        for layer_name, layer_devices in layers.items():
            # Center devices in this layer
            layer_width = len(layer_devices) * device_spacing
            start_x = -layer_width / 2

            for i, device in enumerate(layer_devices):
                device_id = device.get('id')
                if device_id:
                    x = start_x + i * device_spacing
                    y = current_y
                    z = random.uniform(-50, 50)  # Add some depth variation

                    layout_positions[device_id] = {
                        'x': x,
                        'y': y,
                        'z': z,
                        'layer': layer_name
                    }

            current_y += layer_height

        return {
            'positions': layout_positions,
            'layers': list(layers.keys()),
            'dimensions': {
                'width': max(len(layer) * device_spacing for layer in layers.values()),
                'height': len(layers) * layer_height,
                'depth': 100
            }
        }

    def _group_devices_by_layer(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group devices into logical layers"""
        layers = {
            'core': [],      # Core switches, routers
            'distribution': [],  # Distribution switches
            'access': [],    # Access switches, APs
            'endpoints': []  # End devices, clients
        }

        for device in self.devices:
            device_type = device.get('type', '').lower()
            vendor = device.get('vendor', '').lower()
            name = device.get('name', '').lower()

            # Classification logic
            if any(keyword in device_type for keyword in ['router', 'gateway', 'fortigate']):
                layers['core'].append(device)
            elif any(keyword in device_type for keyword in ['switch', 'fortiswitch']):
                if 'core' in name or 'distribution' in name:
                    layers['distribution'].append(device)
                else:
                    layers['access'].append(device)
            elif any(keyword in device_type for keyword in ['ap', 'access_point', 'fortiap']):
                layers['access'].append(device)
            elif any(keyword in device_type for keyword in ['client', 'endpoint', 'device']):
                layers['endpoints'].append(device)
            else:
                # Default to access layer
                layers['access'].append(device)

        # Remove empty layers
        return {k: v for k, v in layers.items() if v}

    def add_device_relationships(self) -> List[Tuple[str, str]]:
        """Add logical relationships between devices"""
        relationships = []

        # Create relationships based on device proximity and types
        device_positions = {}
        if hasattr(self, '_current_layout') and 'positions' in self._current_layout:
            device_positions = self._current_layout['positions']

        # Add parent-child relationships for managed devices
        for device in self.devices:
            device_id = device.get('id')
            device_type = device.get('type', '').lower()

            if 'switch' in device_type:
                # Find connected APs or clients
                related_devices = self._find_related_devices(device_id, ['ap', 'client'])
                for related_id in related_devices:
                    relationships.append((device_id, related_id))

            elif 'ap' in device_type:
                # Find connected clients
                related_devices = self._find_related_devices(device_id, ['client'])
                for related_id in related_devices:
                    relationships.append((device_id, related_id))

        return relationships

    def _find_related_devices(self, device_id: str, related_types: List[str]) -> List[str]:
        """Find devices related to the given device"""
        related = []

        # This would implement logic to find related devices
        # For now, return empty list as this requires more complex analysis
        # In a full implementation, this would analyze the connection data

        return related

    def optimize_layout(self, layout: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize layout to reduce crossings and improve readability"""
        # Simple optimization: adjust positions to reduce overlap
        positions = layout['positions']

        # Separate devices by layer
        layer_positions = {}
        for device_id, pos in positions.items():
            layer = pos.get('layer', 'unknown')
            if layer not in layer_positions:
                layer_positions[layer] = []
            layer_positions[layer].append((device_id, pos))

        # Optimize each layer
        optimized_positions = {}
        for layer, devices in layer_positions.items():
            optimized_layer = self._optimize_layer(devices)
            optimized_positions.update(optimized_layer)

        layout['positions'] = optimized_positions
        layout['optimized'] = True

        return layout

    def _optimize_layer(self, devices: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """Optimize device positions within a layer"""
        if len(devices) <= 1:
            return {device_id: pos for device_id, pos in devices}

        # Sort by x position
        devices.sort(key=lambda x: x[1]['x'])

        # Adjust spacing to prevent overlap
        min_spacing = 120
        optimized = {}

        current_x = devices[0][1]['x']
        for device_id, pos in devices:
            optimized[device_id] = {
                **pos,
                'x': current_x
            }
            current_x += min_spacing

        return optimized

    def validate_topology(self, topology: Dict[str, Any]) -> Dict[str, Any]:
        """Validate topology for consistency and completeness"""
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': []
        }

        devices = topology.get('devices', [])
        connections = topology.get('connections', [])
        positions = topology.get('layout', {}).get('positions', {})

        # Check for orphaned devices
        connected_device_ids = set()
        for conn in connections:
            if isinstance(conn, tuple):
                source, target = conn
            elif isinstance(conn, dict):
                source = conn.get('source')
                target = conn.get('target')
            else:
                continue
            connected_device_ids.add(source)
            connected_device_ids.add(target)

        for device in devices:
            device_id = device.get('id')
            if device_id and device_id not in connected_device_ids:
                validation_results['warnings'].append(f"Device {device_id} has no connections")

        # Check for missing positions
        for device in devices:
            device_id = device.get('id')
            if not device_id:
                validation_results['errors'].append("Device found without ID")
            elif device_id not in positions:
                validation_results['warnings'].append(f"Device {device_id} has no position")

        # Check for invalid connections
        device_ids = {d.get('id') for d in devices if d.get('id')}
        for conn in connections:
            # Handle both tuple and dict formats
            if isinstance(conn, tuple):
                source, target = conn
            elif isinstance(conn, dict):
                source = conn.get('source')
                target = conn.get('target')
            else:
                validation_results['errors'].append(f"Invalid connection format: {conn}")
                continue

            if source not in device_ids:
                validation_results['errors'].append(f"Connection source {source} not found in devices")
            if target not in device_ids:
                validation_results['errors'].append(f"Connection target {target} not found in devices")

        if validation_results['errors']:
            validation_results['valid'] = False

        return validation_results