#!/usr/bin/env python3
"""
Main Integration Platform
Demonstrates the integrated network management and 3D visualization platform
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# Import integrated modules
from shared.config.config_manager import ConfigManager
from shared.device_handling.device_collector import UnifiedDeviceCollector
from shared.device_handling.device_processor import DeviceProcessor, DeviceMatcher
from shared.device_handling.device_classifier import DeviceClassifier
from shared.network_utils.data_formatter import NetworkDataFormatter
from shared.network_utils.topology_builder import TopologyBuilder
from shared.network_utils.authentication import AuthManager
from shared.assets.asset_manager import AssetManager
from shared.visualization.renderer import VisualizationRenderer
from shared.format_standardization.gltf_processor import GLTFProcessor
from shared.format_standardization.svg_processor import SVGProcessor

# Import Agents
from shared.agents.discovery_agent import DiscoveryAgent
from shared.agents.asset_agent import AssetAgent
from shared.agents.topology_agent import TopologyAgent


class IntegratedNetworkPlatform:
    """
    Main integration platform combining all functionality
    """

    def __init__(self, config_file: Optional[str] = None):
        self.config = ConfigManager(config_file)
        self.auth_manager = AuthManager()
        self.device_collector = UnifiedDeviceCollector(self.auth_manager)
        self.device_processor = DeviceProcessor()
        self.device_classifier = DeviceClassifier()
        self.data_formatter = NetworkDataFormatter()
        self.topology_builder = TopologyBuilder()
        self.asset_manager = AssetManager()
        self.visualization_renderer = VisualizationRenderer()

        print("🔗 Integrated Network Platform initialized")
        print(f"   Config loaded: {self.config.config.app_name}")
        print(f"   3D visualization: {'Enabled' if self.config.config.enable_3d else 'Disabled'}")
        print(f"   Assets directory: {self.asset_manager.base_dir}")
        
        # Initialize Agents
        self.discovery_agent = DiscoveryAgent(self.auth_manager)
        self.asset_agent = AssetAgent(str(self.asset_manager.base_dir))
        self.topology_agent = TopologyAgent()

    def run_full_workflow(self, use_demo_data: bool = False):
        """
        Execute the consolidated workflow using agents:
        1. Discovery (Infrastructure + Clients)
        2. Asset Assignment (MAC lookup, VSS/SVG, 3D)
        3. Topology Building & Export
        """
        print("\n🚀 Starting Integrated Workflow")
        
        if use_demo_data:
            print("   Mode: DEMO/Synthetic Data")
            # Reuse the demo data logic but through agents ideally
            # For now, we will just use the run_demo_mode logic but adapted
            self.run_demo_mode()
            return
            
        # 1. Discovery
        print("\n📡 Step 1: Network Discovery")
        # Load config details (mocked for now since we don't have a real config file loaded in context)
        # In real usage, self.config.config would have these details
        discovery_config = {
            'fortigate': {
                'host': '192.168.1.99', # Example default
                'username': 'admin',
                'password': '' 
            }
        }
        
        # Override with actual config if available
        if hasattr(self.config, 'config'):
             # Map config object to dict if needed
             pass
             
        devices = self.discovery_agent.connect_and_discover(discovery_config)
        
        # 2. Asset Assignment
        print("\n🎨 Step 2: Asset & Visual Assignment")
        # Extract VSS if provided (via CLI or config)
        # vss_path = self.config.get('vss_path')
        # if vss_path:
        #    self.asset_agent.process_vss_file(vss_path)
            
        enhanced_devices = self.asset_agent.assign_assets_to_devices(devices)
        
        # 3. Topology & Visualization
        print("\n🕸️ Step 3: Topology Generation")
        topology = self.topology_agent.build_topology(enhanced_devices)
        
        path_html = self.topology_agent.export_topology(topology, format_type='html')
        path_drawio = self.topology_agent.export_topology(topology, format_type='drawio')
        
        print(f"\n✅ Workflow Complete!")
        print(f"   Interactive 3D Map: {path_html}")
        print(f"   2D DrawIO Diagram:  {path_drawio}")

    def collect_and_process_devices(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and process devices from multiple sources"""
        print("\n📡 Collecting devices from sources...")

        results = {
            'fortigate': {'devices': [], 'success': False},
            'fortimanager': {'devices': [], 'success': False},
            'meraki': {'devices': [], 'success': False}
        }

        # Collect from FortiGate
        if sources.get('fortigate'):
            fg_config = sources['fortigate']
            devices = self.device_collector.collect_from_fortigate(
                fg_config['host'], fg_config['username'], fg_config['password']
            )
            results['fortigate']['devices'] = [device.__dict__ for device in devices]
            results['fortigate']['success'] = len(devices) > 0

        # Collect from Meraki
        if sources.get('meraki'):
            mk_config = sources['meraki']
            devices = self.device_collector.collect_from_meraki(mk_config['api_key'])
            results['meraki']['devices'] = [device.__dict__ for device in devices]
            results['meraki']['success'] = len(devices) > 0

        # Process all collected devices
        all_devices = []
        for source, data in results.items():
            all_devices.extend(data['devices'])

        print(f"✅ Collected {len(all_devices)} devices total")

        # Process and classify devices
        if all_devices:
            processed_devices = self.device_processor.process_devices(all_devices)
            classified_devices = self.device_classifier.classify_devices_batch(processed_devices)

            results['processed'] = processed_devices
            results['classified'] = classified_devices
            results['summary'] = self.device_classifier.get_category_stats(classified_devices)

        return results

    def build_network_topology(self, devices: list, connections: list = None) -> Dict[str, Any]:
        """Build network topology from devices"""
        print("\n🏗️ Building network topology...")

        if connections is None:
            connections = []

        # Build topology
        topology = self.topology_builder.build_topology(devices, connections)

        # Validate topology
        validation = self.topology_builder.validate_topology(topology)

        print("✅ Topology built")
        print(f"   Devices: {len(devices)}")
        print(f"   Connections: {len(connections)}")
        print(f"   Valid: {validation['valid']}")

        return {
            'topology': topology,
            'validation': validation
        }

    def create_visualization(self, topology_data: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """Create 3D visualization from topology data"""
        print(f"\n🎨 Creating 3D visualization: {output_path}")

        output_file = Path(output_path)

        # Format for 3D visualization
        viz_data = self.data_formatter.format_for_3d_visualization(topology_data)

        # Create HTML viewer
        html_success = self.visualization_renderer.render_html_viewer(
            topology_data, output_file.with_suffix('.html')
        )

        # Create GLTF export
        gltf_success = self.visualization_renderer.export_gltf(
            topology_data, output_file.with_suffix('.gltf')
        )

        # Create SVG topology
        svg_success = self.visualization_renderer.export_svg(
            topology_data, output_file.with_suffix('.svg')
        )

        results = {
            'html_viewer': html_success is not None,
            'gltf_export': gltf_success is not None,
            'svg_export': svg_success is not None,
            'files_created': []
        }

        if html_success:
            results['files_created'].append(str(html_success))
        if gltf_success:
            results['files_created'].append(str(gltf_success))
        if svg_success:
            results['files_created'].append(str(svg_success))

        print("✅ Visualization created")
        print(f"   Files: {len(results['files_created'])}")

        return results

    def manage_assets(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Manage visualization assets"""
        print(f"\n📦 Asset management: {operation}")

        if operation == 'discover':
            return self.asset_manager.discover_assets()
        elif operation == 'import':
            source_dir = kwargs.get('source_dir')
            if source_dir:
                return self.asset_manager.import_assets_from_directory(source_dir)
        elif operation == 'get_for_device':
            device_type = kwargs.get('device_type')
            vendor = kwargs.get('vendor')
            return self.asset_manager.get_asset_for_device(device_type, vendor)

        return {'error': f'Unknown operation: {operation}'}

    def standardize_formats(self, files: list, operations: list) -> Dict[str, Any]:
        """Standardize file formats"""
        print(f"\n🔧 Standardizing {len(files)} files with {len(operations)} operations")

        results = {
            'processed': 0,
            'failed': 0,
            'operations': operations,
            'files': []
        }

        gltf_processor = GLTFProcessor()
        svg_processor = SVGProcessor()

        for file_path in files:
            file_results = {'file': str(file_path), 'operations': {}}

            for operation in operations:
                try:
                    if operation == 'validate':
                        if file_path.suffix.lower() in ['.gltf', '.glb']:
                            validation = gltf_processor.validate_gltf(file_path)
                            file_results['operations']['validate_gltf'] = validation['valid']
                        elif file_path.suffix.lower() == '.svg':
                            validation = svg_processor.validate_svg(file_path)
                            file_results['operations']['validate_svg'] = validation['valid']
                    elif operation == 'standardize':
                        if file_path.suffix.lower() in ['.gltf', '.glb']:
                            output = gltf_processor.standardize_gltf(file_path)
                            file_results['operations']['standardize_gltf'] = output is not None
                        elif file_path.suffix.lower() == '.svg':
                            output = svg_processor.standardize_svg(file_path)
                            file_results['operations']['standardize_svg'] = output is not None
                    elif operation == 'optimize':
                        if file_path.suffix.lower() in ['.gltf', '.glb']:
                            output = gltf_processor.optimize_gltf(file_path)
                            file_results['operations']['optimize_gltf'] = output is not None
                        elif file_path.suffix.lower() == '.svg':
                            output = svg_processor.optimize_svg(file_path)
                            file_results['operations']['optimize_svg'] = output is not None
                except Exception as e:
                    file_results['operations'][operation] = f"Error: {str(e)}"
                    results['failed'] += 1

            results['files'].append(file_results)
            results['processed'] += 1

        return results

    def run_demo_mode(self):
        """Run the platform in demo mode with synthetic data"""
        print("\n🎮 Running in DEMO mode")
        
        # Synthetic data
        demo_devices = [
            {'id': 'fw-01', 'name': 'Corporate-FW', 'type': 'fortigate', 'ip': '192.168.1.1', 'serial': 'FG100F-DEMO'},
            {'id': 'sw-core', 'name': 'Core-Switch', 'type': 'meraki_switch', 'ip': '192.168.1.2', 'model': 'MS390'},
            {'id': 'sw-access-1', 'name': 'Access-Switch-1', 'type': 'meraki_switch', 'ip': '192.168.1.3', 'model': 'MS120'},
            {'id': 'sw-access-2', 'name': 'Access-Switch-2', 'type': 'meraki_switch', 'ip': '192.168.1.4', 'model': 'MS120'},
            {'id': 'ap-01', 'name': 'Office-AP-1', 'type': 'meraki_ap', 'ip': '192.168.1.10', 'model': 'MR46'},
            {'id': 'ap-02', 'name': 'Office-AP-2', 'type': 'meraki_ap', 'ip': '192.168.1.11', 'model': 'MR46'},
            {'id': 'ap-03', 'name': 'Lobby-AP', 'type': 'meraki_ap', 'ip': '192.168.1.12', 'model': 'MR46'}
        ]
        
        demo_connections = [
            ('fw-01', 'sw-core'),
            ('sw-core', 'sw-access-1'),
            ('sw-core', 'sw-access-2'),
            ('sw-access-1', 'ap-01'),
            ('sw-access-1', 'ap-02'),
            ('sw-access-2', 'ap-03')
        ]
        
        print(f"   Generated {len(demo_devices)} demo devices")
        
        # Process through pipeline
        print("\n🔄 Processing demo data...")
        # 1. Process
        processed_devices = self.device_processor.process_devices(demo_devices)
        classified_devices = self.device_classifier.classify_devices_batch(processed_devices)
        
        # 2. Build Topology
        # Note: build_topology requires list of dicts for devices
        topology_result = self.build_network_topology(classified_devices, demo_connections)
        
        # 3. Visualize
        output_dir = Path("demo_output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "demo_network"
        
        results = self.create_visualization(topology_result['topology'], str(output_path))
        
        print("\n✨ Demo completed successfully!")
        print(f"   Results saved to: {output_dir.absolute()}")
        print(f"   View 3D Map: file://{output_dir.absolute()}/demo_network.html")

    async def start_api_server(self, host: str = "0.0.0.0", port: int = 12500):
        """Start the integrated API server"""
        from api.main import create_application
        import uvicorn
        import socket

        # Check if port is in use and find next available
        target_port = port
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex((host, target_port))
                if result != 0: # Port is available (connection refused)
                    break
                print(f"⚠️  Port {target_port} is already in use.")
                target_port += 1
                if target_port > port + 10:
                    print("❌ Could not find an open port in range.")
                    return

        print(f"🌐 Starting API server on {host}:{target_port}")

        app = create_application()
        config = uvicorn.Config(app, host=host, port=target_port, log_level="info")
        server = uvicorn.Server(config)

        await server.serve()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Integrated Network Platform")
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--api', action='store_true', help='Start API server')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode with synthetic data')
    parser.add_argument('--workflow', action='store_true', help='Run the full consolidated workflow (agents)')
    parser.add_argument('--host', default='0.0.0.0', help='API server host')
    parser.add_argument('--port', type=int, default=12500, help='API server port')

    args = parser.parse_args()

    # Initialize platform
    platform = IntegratedNetworkPlatform(args.config)

    if args.api:
        # Start API server
        asyncio.run(platform.start_api_server(args.host, args.port))
    elif args.demo:
        # Run demo mode
        platform.run_demo_mode()
    elif args.workflow:
        # Run full consolidated workflow
        platform.run_full_workflow()
    else:
        print("🤖 Integrated Network Platform")
        print("Use --api to start the API server")
        print("Use --demo to run a demonstration")
        print("Use --workflow to run the full consolidated workflow")


if __name__ == "__main__":
    main()