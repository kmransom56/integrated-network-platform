"""
Topology Agent
Responsible for building the network graph and exporting visualizations.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from shared.network_utils.network_client import NetworkDevice
from shared.visualization.drawio_exporter import DrawIOExporter

logger = logging.getLogger(__name__)

class TopologyAgent:
    """
    Agent resposible for:
    1. Building the network topology (nodes + links)
    2. Exporting to various formats (Babylon, DrawIO, JSON)
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_topology(self, devices: List[NetworkDevice]) -> Dict[str, Any]:
        """
        Construct the topology graph from a list of devices.
        Returns a dict with 'nodes' and 'links'.
        """
        nodes = []
        links = []
        
        # 1. Create Nodes
        device_map = {}
        for d in devices:
            metadata = d.metadata or {}
            
            node = {
                'id': d.id,
                'name': d.name,
                'type': str(d.device_type),
                'ip': d.ip_address,
                'mac': d.mac_address,
                'vendor': d.vendor,
                # Visual metadata
                'icon': metadata.get('icon_svg'),
                'model': metadata.get('model_3d'),
                # Extended Metrics (from FortiGateMonitor)
                'metrics': {
                    'cpu': metadata.get('cpu'),
                    'memory': metadata.get('memory'),
                    'sessions': metadata.get('sessions'),
                    'system_status': metadata.get('system_status')
                }
            }
            nodes.append(node)
            device_map[d.id] = d
            
        # 2. Create Links
        # Basic link logic: Connect everything to the first FortiGate found (Hub and Spoke default)
        # In a real scenario, this would rely on LLDP or 'connected_via' attributes
        gateway_nodes = [n for n in nodes if 'fortigate' in n['type'].lower() or 'firewall' in n['type'].lower()]
        gateway_id = gateway_nodes[0]['id'] if gateway_nodes else None

        if gateway_id:
            for n in nodes:
                if n['id'] != gateway_id:
                    links.append({
                        'source': gateway_id,
                        'target': n['id'],
                        'value': 1
                    })

        topology = {
            'nodes': nodes,
            'links': links,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'device_count': len(nodes)
            }
        }
        return topology

    def export_topology(self, topology: Dict[str, Any], format_type: str = "json") -> str:
        """
        Export topology to file.
        Returns path to exported file.
        """
        filename = f"topology_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        out_path = self.output_dir / filename
        
        if format_type == 'json':
            with open(out_path, 'w') as f:
                json.dump(topology, f, indent=2)
        elif format_type == 'html':
            # Create a simple 3d-force-graph HTML wrapper
            self._create_html_viz(topology, out_path)
        elif format_type == 'drawio' or format_type == 'xml':
            # Use DrawIO Exporter
            xml_content = DrawIOExporter.generate_drawio_xml(topology)
            with open(out_path, 'w') as f:
                f.write(xml_content)
            
        logger.info(f"Exported topology to {out_path}")
        return str(out_path)

    def _create_html_viz(self, topology: Dict[str, Any], path: Path):
        """Generate a standalone HTML file for 3D visualization"""
        json_data = json.dumps(topology)
        html_content = f"""
        <html>
        <head>
            <style>body {{ margin: 0; }}</style>
            <!-- Using unpkg for simplicity, but could be local -->
            <script src="//unpkg.com/3d-force-graph"></script>
        </head>
        <body>
            <div id="3d-graph"></div>
            <script>
                const gData = {json_data};
                
                const Graph = ForceGraph3D()
                    (document.getElementById('3d-graph'))
                    .graphData(gData)
                    .nodeLabel(node => {{
                        let label = `<b>${{node.name}}</b><br>${{node.ip}}<br>${{node.type}}`;
                        if (node.metrics && node.metrics.cpu) {{
                            // Safe check for structure
                            const cpuVal = typeof node.metrics.cpu === 'object' ? JSON.stringify(node.metrics.cpu) : node.metrics.cpu;
                            label += `<br>CPU: ${{cpuVal}}`; 
                        }}
                        return label;
                    }})
                    .nodeAutoColorBy('type')
                    .nodeThreeObject(node => {{
                        // Advanced: Could load the GLTF model here using ThreeJS logic
                        // For now we use standard spheres/shapes
                        return false; 
                    }});
            </script>
        </body>
        </html>
        """
        with open(path, 'w') as f:
            f.write(html_content)
