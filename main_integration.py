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

    def run_demonstration(self) -> Dict[str, Any]:
        """Run a complete demonstration of the integrated platform"""
        print("🚀 Starting Integrated Network Platform Demonstration")
        print("=" * 60)

        results = {}

        # 1. Test asset discovery
        print("\n📦 Step 1: Asset Discovery")
        assets = self.manage_assets('discover')
        results['assets'] = assets
        print(f"   Found {assets['summary']['total_models']} models, {assets['summary']['total_icons']} icons")

        # 2. Create sample topology
        print("\n🏗️ Step 2: Sample Topology Creation")
        sample_devices = [
            {'id': 'SW001', 'name': 'Core Switch', 'type': 'switch', 'vendor': 'fortinet'},
            {'id': 'AP001', 'name': 'Access Point', 'type': 'access_point', 'vendor': 'fortinet'},
            {'id': 'FW001', 'name': 'Firewall', 'type': 'router', 'vendor': 'fortinet'}
        ]
        sample_connections = [('SW001', 'AP001'), ('FW001', 'SW001')]

        topology_result = self.build_network_topology(sample_devices, sample_connections)
        results['topology'] = topology_result

        # 3. Create visualization
        print("\n🎨 Step 3: Visualization Creation")
        viz_result = self.create_visualization(
            topology_result['topology'],
            'demo_network_topology'
        )
        results['visualization'] = viz_result

        # 4. Test format processing
        print("\n🔧 Step 4: Format Processing")
        test_files = []  # Would include actual test files
        format_results = self.standardize_formats(test_files, ['validate'])
        results['format_processing'] = format_results

        print("\n🎉 Demonstration Complete!")
        print("=" * 60)
        print("Summary:")
        print(f"  • Assets discovered: {assets['summary']['total_models'] + assets['summary']['total_icons']}")
        print(f"  • Topology built: {len(sample_devices)} devices")
        print(f"  • Visualizations created: {len(viz_result['files_created'])}")
        print(f"  • Format operations: {format_results['processed']}")

        return results

    # async def start_api_server(self, host: str = "0.0.0.0", port: int = 8000):
    #     """Start the integrated API server"""
    #     print(f"🌐 Starting API server on {host}:{port}")
    #
    #     app = create_application()
    #     config = uvicorn.Config(app, host=host, port=port, log_level="info")
    #     server = uvicorn.Server(config)
    #
    #     await server.serve()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Integrated Network Platform")
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    parser.add_argument('--api', action='store_true', help='Start API server')
    parser.add_argument('--host', default='0.0.0.0', help='API server host')
    parser.add_argument('--port', type=int, default=8000, help='API server port')

    args = parser.parse_args()

    # Initialize platform
    platform = IntegratedNetworkPlatform(args.config)

    if args.demo:
        # Run demonstration
        results = platform.run_demonstration()
        print("\n📊 Demonstration Results:")
        for key, value in results.items():
            if isinstance(value, dict) and 'summary' in value:
                print(f"  {key}: {value['summary']}")

    # elif args.api:
    #     # Start API server
    #     asyncio.run(platform.start_api_server(args.host, args.port))

    else:
        print("🤖 Integrated Network Platform")
        print("Use --demo to run demonstration")
        print("Example: python main_integration.py --demo")


if __name__ == "__main__":
    main()