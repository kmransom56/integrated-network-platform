#!/usr/bin/env python3
"""
Generate Real Network Maps from Device Data
Creates both 2D and 3D network topology visualizations using real device data
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Import integrated platform modules
from shared.network_utils.data_formatter import NetworkDataFormatter
from shared.network_utils.topology_builder import TopologyBuilder
from shared.visualization.renderer import VisualizationRenderer
from shared.device_handling.device_processor import DeviceProcessor

logger = logging.getLogger(__name__)


class RealNetworkMapGenerator:
    """Generate network maps from real device data"""

    def __init__(self, data_source: str = "network_map_3d"):
        self.data_source = data_source
        self.data_formatter = NetworkDataFormatter()
        self.topology_builder = TopologyBuilder()
        self.visualization_renderer = VisualizationRenderer()
        self.device_processor = DeviceProcessor()

        # Set up paths
        if data_source == "network_map_3d":
            self.data_path = Path("/media/keith/DATASTORE/CascadeProjects/network_map_3d")
        else:
            self.data_path = Path("/home/keith/enhanced-network-api-corporate")

        self.output_dir = Path("./real_network_maps")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_real_device_data(self) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
        """Load real device data from the original applications"""
        if self.data_source == "network_map_3d":
            return self._load_network_map_3d_data()
        else:
            return self._load_enhanced_api_data()

    def _load_network_map_3d_data(self) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
        """Load data from network_map_3d application"""
        # First try to load from updated 2D topology file if it exists
        updated_2d_file = Path("./real_network_maps/real_network_topology_2d.json")
        if updated_2d_file.exists():
            try:
                with open(updated_2d_file, 'r') as f:
                    data = json.load(f)
                devices = data.get('devices', [])
                connections = [(conn[0], conn[1]) for conn in data.get('connections', [])]
                logger.info(f"Loaded updated {len(devices)} devices and {len(connections)} connections from 2D topology")
                return devices, connections
            except Exception as e:
                logger.warning(f"Failed to load updated topology: {e}")

        # Fall back to original manifest
        manifest_file = self.data_path / "topology_manifest.json"

        if not manifest_file.exists():
            logger.error(f"Topology manifest not found: {manifest_file}")
            return [], []

        with open(manifest_file, 'r') as f:
            manifest = json.load(f)

        devices = manifest.get('nodes', [])
        connections = [(edge[0], edge[1]) for edge in manifest.get('edges', [])]

        logger.info(f"Loaded {len(devices)} devices and {len(connections)} connections from network_map_3d")
        return devices, connections

    def _load_enhanced_api_data(self) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
        """Load data from enhanced-network-api-corporate application"""
        # This would integrate with the actual API to fetch real device data
        # For now, return empty as we need API credentials
        logger.warning("Enhanced API data loading requires API credentials")
        return [], []

    def create_network_maps(self, devices: List[Dict[str, Any]], connections: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Create both 2D and 3D network maps"""
        logger.info("Creating network maps from real data...")

        results = {
            'devices_count': len(devices),
            'connections_count': len(connections),
            'maps_created': []
        }

        if not devices:
            logger.error("No devices to process")
            return results

        # Process devices (preserve existing labels from JSON data)
        processed_devices = []
        for device in devices:
            processed = self.device_processor.process_device(device)
            # Preserve the original label if it exists
            if 'label' in device and device['label']:
                processed['label'] = device['label']
            processed_devices.append(processed)

        # Create 3D topology
        topology_3d = self._create_3d_topology(processed_devices, connections)
        results['maps_created'].append('3d_topology')

        # Create 2D topology
        topology_2d = self._create_2d_topology(processed_devices, connections)
        results['maps_created'].append('2d_topology')

        # Generate visualizations
        viz_results = self._generate_visualizations(topology_3d, topology_2d)
        results.update(viz_results)

        return results

    def _create_3d_topology(self, devices: List[Dict[str, Any]], connections: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Create 3D topology with proper positioning"""
        logger.info("Building 3D network topology...")

        # Use existing positions from the manifest or apply layered layout
        topology = self.topology_builder.build_topology(devices, connections)

        # Enhance with device-specific information
        for device in topology['devices']:
            device['processed_at'] = 'real_data'
            device['data_source'] = self.data_source

        return topology

    def _create_2d_topology(self, devices: List[Dict[str, Any]], connections: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Create 2D topology visualization"""
        logger.info("Building 2D network topology...")

        # Create a 2D version of the topology
        topology_2d = {
            'devices': [],
            'connections': connections,
            'layout': {'type': '2d_force_directed'},
            'metadata': {
                'total_devices': len(devices),
                'total_connections': len(connections),
                'visualization_type': '2d',
                'data_source': self.data_source
            }
        }

        # Convert 3D positions to 2D for top-down view
        for device in devices:
            device_2d = device.copy()
            # Use existing x,y coordinates, ignore z for 2D view
            if 'x' in device and 'y' in device:
                device_2d['position_2d'] = {'x': device['x'], 'y': device['y']}
            else:
                # Default positioning if no coordinates
                device_2d['position_2d'] = {'x': 0, 'y': 0}

            topology_2d['devices'].append(device_2d)

        return topology_2d

    def _generate_visualizations(self, topology_3d: Dict[str, Any], topology_2d: Dict[str, Any]) -> Dict[str, Any]:
        """Generate all visualization formats"""
        results = {'visualizations': []}

        # 3D Visualizations
        logger.info("Generating 3D visualizations...")

        # HTML interactive 3D view
        html_3d_file = self.output_dir / "real_network_topology_3d.html"
        html_success = self.visualization_renderer.render_html_viewer(
            topology_3d, html_3d_file
        )
        if html_success:
            results['visualizations'].append({
                'type': '3d_html',
                'file': str(html_3d_file),
                'description': 'Interactive 3D HTML visualization'
            })

        # GLTF 3D model
        gltf_3d_file = self.output_dir / "real_network_topology_3d.gltf"
        gltf_success = self.visualization_renderer.export_gltf(
            topology_3d, gltf_3d_file
        )
        if gltf_success:
            results['visualizations'].append({
                'type': '3d_gltf',
                'file': str(gltf_3d_file),
                'description': '3D GLTF model file'
            })

        # 2D Visualizations
        logger.info("Generating 2D visualizations...")

        # SVG 2D topology
        svg_2d_file = self.output_dir / "real_network_topology_2d.svg"
        svg_success = self._create_svg_2d_topology(topology_2d, svg_2d_file)
        if svg_success:
            results['visualizations'].append({
                'type': '2d_svg',
                'file': str(svg_2d_file),
                'description': '2D SVG network topology'
            })

        # JSON data exports
        json_3d_file = self.output_dir / "real_network_topology_3d.json"
        json_2d_file = self.output_dir / "real_network_topology_2d.json"

        with open(json_3d_file, 'w') as f:
            json.dump(topology_3d, f, indent=2)
        results['visualizations'].append({
            'type': '3d_json',
            'file': str(json_3d_file),
            'description': '3D topology data (JSON)'
        })

        with open(json_2d_file, 'w') as f:
            json.dump(topology_2d, f, indent=2)
        results['visualizations'].append({
            'type': '2d_json',
            'file': str(json_2d_file),
            'description': '2D topology data (JSON)'
        })

        return results

    def _create_svg_2d_topology(self, topology_2d: Dict[str, Any], output_file: Path) -> bool:
        """Create a 2D SVG network topology"""
        try:
            devices = topology_2d['devices']
            connections = topology_2d['connections']

            # Calculate bounds
            if devices:
                positions = [d.get('position_2d', {'x': 0, 'y': 0}) for d in devices]
                x_coords = [p['x'] for p in positions]
                y_coords = [p['y'] for p in positions]

                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)

                # Add padding
                padding = 100
                width = max(max_x - min_x + 2 * padding, 800)
                height = max(max_y - min_y + 2 * padding, 600)
            else:
                width, height = 800, 600
                min_x = min_y = 0
                padding = 50

            # Create SVG content
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7"
     refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
    </marker>
    <!-- Device type styles -->
    <style>
      .device {{ fill: #e3f2fd; stroke: #1976d2; stroke-width: 2; }}
      .firewall {{ fill: #ffebee; stroke: #d32f2f; stroke-width: 2; }}
      .switch {{ fill: #e8f5e8; stroke: #388e3c; stroke-width: 2; }}
      .access-point {{ fill: #fff3e0; stroke: #f57c00; stroke-width: 2; }}
      .cloud {{ fill: #f3e5f5; stroke: #7b1fa2; stroke-width: 2; }}
      .connection {{ stroke: #666; stroke-width: 2; }}
      .device-label {{ font-family: Arial, sans-serif; font-size: 12px; text-anchor: middle; fill: #333; }}
    </style>
  </defs>

  <!-- Background -->
  <rect width="100%" height="100%" fill="#fafafa" stroke="#e0e0e0" stroke-width="1"/>

  <!-- Title -->
  <text x="20" y="30" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#333">
    Network Topology Map
  </text>
  <text x="20" y="50" font-family="Arial, sans-serif" font-size="12" fill="#666">
    Generated from real device data • {len(devices)} devices • {len(connections)} connections
  </text>
'''

            # Draw connections first (behind devices)
            device_positions = {}
            for device in devices:
                device_id = device.get('id')
                pos = device.get('position_2d', {'x': 0, 'y': 0})
                device_positions[device_id] = {
                    'x': pos['x'] - min_x + padding,
                    'y': pos['y'] - min_y + padding
                }

            for source_id, target_id in connections:
                if source_id in device_positions and target_id in device_positions:
                    source_pos = device_positions[source_id]
                    target_pos = device_positions[target_id]

                    svg_content += f'''
  <!-- Connection {source_id} -> {target_id} -->
  <line x1="{source_pos['x']}" y1="{source_pos['y']}"
        x2="{target_pos['x']}" y2="{target_pos['y']}"
        class="connection" marker-end="url(#arrowhead)"/>
'''

            # Draw devices
            for device in devices:
                device_id = device.get('id')
                device_name = device.get('label', device_id)
                device_type = device.get('device_type', 'device')

                if device_id in device_positions:
                    pos = device_positions[device_id]

                    # Choose CSS class based on device type
                    css_class = self._get_device_css_class(device_type)

                    # Draw device rectangle
                    svg_content += f'''
  <!-- Device {device_name} -->
  <rect x="{pos['x'] - 40}" y="{pos['y'] - 20}" width="80" height="40"
        class="{css_class}" rx="8"/>
  <text x="{pos['x']}" y="{pos['y'] + 5}" class="device-label">
    {device_name}
  </text>
'''

            # Add legend
            svg_content += self._create_svg_legend(width - 200, 80)

            svg_content += '\n</svg>'

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(svg_content)

            logger.info(f"Created 2D SVG topology: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to create 2D SVG topology: {e}")
            return False

    def _get_device_css_class(self, device_type: str) -> str:
        """Get CSS class for device type"""
        type_mapping = {
            'firewall': 'firewall',
            'switch': 'switch',
            'access_point': 'access-point',
            'cloud': 'cloud',
            'router': 'firewall',  # Use firewall style for routers
            'gateway': 'firewall'
        }
        return type_mapping.get(device_type.lower(), 'device')

    def _create_svg_legend(self, x: int, y: int) -> str:
        """Create SVG legend"""
        legend = f'''
  <!-- Legend -->
  <g transform="translate({x},{y})">
    <rect x="0" y="0" width="180" height="140" fill="white" stroke="#ccc" stroke-width="1" rx="5"/>
    <text x="10" y="20" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#333">Legend</text>

    <!-- Firewall -->
    <rect x="10" y="30" width="20" height="12" class="firewall"/>
    <text x="40" y="40" font-family="Arial, sans-serif" font-size="11" fill="#333">Firewall</text>

    <!-- Switch -->
    <rect x="10" y="50" width="20" height="12" class="switch"/>
    <text x="40" y="60" font-family="Arial, sans-serif" font-size="11" fill="#333">Switch</text>

    <!-- Access Point -->
    <rect x="10" y="70" width="20" height="12" class="access-point"/>
    <text x="40" y="80" font-family="Arial, sans-serif" font-size="11" fill="#333">Access Point</text>

    <!-- Cloud -->
    <rect x="10" y="90" width="20" height="12" class="cloud"/>
    <text x="40" y="100" font-family="Arial, sans-serif" font-size="11" fill="#333">Internet</text>

    <!-- Device -->
    <rect x="10" y="110" width="20" height="12" class="device"/>
    <text x="40" y="120" font-family="Arial, sans-serif" font-size="11" fill="#333">Device</text>
  </g>'''

        return legend


def main():
    """Main function to generate real network maps"""
    print("🗺️  Real Network Map Generator")
    print("=" * 50)

    # Initialize generator
    generator = RealNetworkMapGenerator(data_source="network_map_3d")

    # Load real device data
    print("\n📡 Loading real device data...")
    devices, connections = generator.load_real_device_data()

    if not devices:
        print("❌ No device data found. Please check data source.")
        return

    print(f"✅ Loaded {len(devices)} devices and {len(connections)} connections")

    # Create network maps
    print("\n🎨 Generating network maps...")
    results = generator.create_network_maps(devices, connections)

    # Display results
    print("\n📊 Generation Results:")
    print(f"   Devices processed: {results['devices_count']}")
    print(f"   Connections processed: {results['connections_count']}")
    print(f"   Maps created: {', '.join(results['maps_created'])}")

    if 'visualizations' in results:
        print(f"\n📁 Generated Files ({len(results['visualizations'])}):")
        for viz in results['visualizations']:
            print(f"   • {viz['type'].upper()}: {viz['file']}")
            print(f"     {viz['description']}")

    # Show how to view the maps
    print("\n🎯 View Your Maps:")
    print(f"   3D Interactive: file://{generator.output_dir}/real_network_topology_3d.html")
    print(f"   2D SVG: file://{generator.output_dir}/real_network_topology_2d.svg")

    print("\n✨ Network map generation complete!")
    print(f"   Output directory: {generator.output_dir}")


if __name__ == "__main__":
    main()