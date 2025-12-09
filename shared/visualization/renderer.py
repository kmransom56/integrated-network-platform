"""
Visualization Renderer
Handles 3D visualization exports (GLTF, SVG) from network_map_3d
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VisualizationRenderer:
    """
    Renders 3D visualizations in various formats
    Based on network_map_3d export functionality
    """

    def __init__(self, models_dir: Optional[str] = None, icons_dir: Optional[str] = None):
        self.models_dir = Path(models_dir) if models_dir else Path("./models")
        self.icons_dir = Path(icons_dir) if icons_dir else Path("./icons")

        # Ensure directories exist
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.icons_dir.mkdir(parents=True, exist_ok=True)

    def export_gltf(self, topology_data: Dict[str, Any], output_path: Path) -> bool:
        """Export topology as GLTF 3D model"""
        try:
            # Create GLTF structure
            gltf_data = self._create_gltf_structure(topology_data)

            # For now, export as JSON (would need proper GLTF binary format implementation)
            # In a full implementation, this would create binary GLTF files
            json_output = output_path.with_suffix('.json')
            with open(json_output, 'w') as f:
                json.dump(gltf_data, f, indent=2)

            logger.info(f"GLTF data exported to {json_output}")
            return True

        except Exception as e:
            logger.error(f"GLTF export failed: {e}")
            return False

    def export_svg(self, topology_data: Dict[str, Any], output_path: Path) -> bool:
        """Export topology as SVG (2D visualization)"""
        try:
            svg_content = self._create_svg_content(topology_data)

            with open(output_path, 'w') as f:
                f.write(svg_content)

            logger.info(f"SVG exported to {output_path}")
            return True

        except Exception as e:
            logger.error(f"SVG export failed: {e}")
            return False

    def export_drawio(self, topology_data: Dict[str, Any], output_path: Path, layout: str = "hierarchical") -> bool:
        """Export topology as DrawIO XML"""
        try:
            from datetime import datetime, timezone
            
            # Template
            xml_template = (
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                "<mxfile host=\"app.diagrams.net\" modified=\"{}\" agent=\"5.0\" "
                "etag=\"{}\" version=\"21.6.5\" type=\"device\">\n"
                "  <diagram name=\"Network Topology\" id=\"topology\">\n"
                "    <mxGraphModel dx=\"1422\" dy=\"794\" grid=\"1\" gridSize=\"10\" "
                "guides=\"1\" tooltips=\"1\" connect=\"1\" arrows=\"1\" fold=\"1\" "
                "page=\"1\" pageScale=\"1\" pageWidth=\"1169\" pageHeight=\"827\" "
                "math=\"0\" shadow=\"0\">\n"
                "      <root>\n"
                "        <mxCell id=\"0\" />\n"
                "        <mxCell id=\"1\" parent=\"0\" />\n"
                "        {}  <!-- Cells will be inserted here -->\n"
                "      </root>\n"
                "    </mxGraphModel>\n"
                "  </diagram>\n"
                "</mxfile>"
            ).format(datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).timestamp(), "")

            cells = []
            cell_id = 2
            
            # Nodes and Links
            nodes = topology_data.get("nodes", [])
            # Handle different formats (devices vs nodes)
            if not nodes and "devices" in topology_data:
                nodes = topology_data["devices"]
                
            links = topology_data.get("links", [])
            if not links and "connections" in topology_data:
                links_raw = topology_data["connections"]
                # Normalize links
                links = []
                for l in links_raw:
                    if isinstance(l, (list, tuple)) and len(l) >= 2:
                        links.append({"source": l[0], "target": l[1]})
                    elif isinstance(l, dict):
                        links.append(l)

            # Calculate Layout
            positions = self._calculate_drawio_positions(nodes, layout)
            
            # Helper to map node ID to cell ID for linking
            node_id_to_cell_id = {}

            # Device cells
            for node in nodes:
                # Handle different ID fields
                nid = node.get("id")
                pos = positions.get(nid, {"x": 100, "y": 100})
                style = self._get_drawio_style(node)
                
                # Format Label
                label = node.get("name", node.get("hostname", "Device"))
                if node.get("ip") or node.get("ip_address"):
                    label += f"\\n{node.get('ip') or node.get('ip_address')}"
                if node.get("type"):
                     label += f"\\n{node.get('type')}"

                cell_xml = (
                    f"        <mxCell id=\"{cell_id}\" value=\"{label}\" style=\"{style}\" "
                    f"vertex=\"1\" parent=\"1\">\n"
                    f"          <mxGeometry x=\"{pos['x']}\" y=\"{pos['y']}\" width=\"120\" height=\"60\" as=\"geometry\" />\n"
                    f"        </mxCell>"
                )
                cells.append(cell_xml)
                node_id_to_cell_id[nid] = cell_id
                cell_id += 1

            # Link cells
            for link in links:
                src_id = link.get("source")
                tgt_id = link.get("target") 
                
                if src_id not in node_id_to_cell_id or tgt_id not in node_id_to_cell_id:
                    continue

                src_cell = node_id_to_cell_id[src_id]
                tgt_cell = node_id_to_cell_id[tgt_id]
                
                style = "strokeColor=#6c757d;strokeWidth=2;endArrow=none;startArrow=none;"

                cell_xml = (
                    f"        <mxCell id=\"{cell_id}\" style=\"{style}\" edge=\"1\" parent=\"1\" "
                    f"source=\"{src_cell}\" target=\"{tgt_cell}\">\n"
                    f"          <mxGeometry width=\"50\" height=\"50\" relative=\"1\" as=\"geometry\">\n"
                    f"            <mxPoint x=\"0\" y=\"0\" as=\"sourcePoint\" />\n"
                    f"            <mxPoint x=\"0\" y=\"0\" as=\"targetPoint\" />\n"
                    f"          </mxGeometry>\n"
                    f"        </mxCell>"
                )
                cells.append(cell_xml)
                cell_id += 1

            final_xml = xml_template.replace("        {}  <!-- Cells will be inserted here -->", "\n".join(cells))
            
            with open(output_path, 'w') as f:
                f.write(final_xml)

            logger.info(f"DrawIO XML exported to {output_path}")
            return True

        except Exception as e:
            logger.error(f"DrawIO export failed: {e}")
            return False

    def _calculate_drawio_positions(self, nodes: list, layout: str) -> dict:
        """Calculate simple grid/layered positions"""
        positions = {}
        if layout == "hierarchical":
            layers = {"fortigate": 0, "firewall": 0, "interface": 1, "switch": 1, "fortiswitch": 1, "ap": 2, "fortiap": 2, "client": 3}
            layer_nodes = {}

            for n in nodes:
                ntype = str(n.get("type", "interface")).lower()
                layer = 3
                for k, v in layers.items():
                    if k in ntype:
                         layer = v
                         break
                layer_nodes.setdefault(layer, []).append(n)

            for layer, items in layer_nodes.items():
                x_start = 100
                y = 100 + layer * 150
                spacing = 220
                for i, n in enumerate(items):
                    positions[n.get("id")] = {"x": x_start + i * spacing, "y": y}
        else:
            # Grid
            for i, n in enumerate(nodes):
                positions[n.get("id")] = {
                    "x": 100 + (i % 4) * 220,
                    "y": 100 + (i // 4) * 150,
                }
        return positions

    def _get_drawio_style(self, node: dict) -> str:
        ntype = str(node.get("type", "interface")).lower()
        base_styles = {
            "fortigate": "shape=cloud;whiteSpace=wrap;html=1;fillColor=#1ba1e2;strokeColor=#006EAF;fontColor=#ffffff;",
            "firewall": "shape=cloud;whiteSpace=wrap;html=1;fillColor=#1ba1e2;strokeColor=#006EAF;fontColor=#ffffff;",
            "interface": "shape=rectangle;whiteSpace=wrap;html=1;fillColor=#60a917;strokeColor=#2D7600;fontColor=#ffffff;",
            "client": "shape=ellipse;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontColor=#000000;",
            "switch": "shape=hexagon;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#000000;",
            "ap": "shape=rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontColor=#000000;",
        }
        style = base_styles["interface"]
        for k, v in base_styles.items():
            if k in ntype:
                style = v
                break
        return style

    def _create_gltf_structure(self, topology_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GLTF JSON structure for 3D topology"""
        devices = topology_data.get('devices', [])
        layout = topology_data.get('layout', {})

        # GLTF structure (simplified)
        gltf = {
            "asset": {
                "version": "2.0",
                "generator": "Integrated Network Platform"
            },
            "scenes": [{
                "name": "NetworkTopology",
                "nodes": []
            }],
            "nodes": [],
            "meshes": [],
            "materials": [],
            "textures": [],
            "images": [],
            "buffers": [],
            "bufferViews": [],
            "accessors": []
        }

        # Add devices as nodes
        for i, device in enumerate(devices):
            position = layout.get('positions', {}).get(device.get('id'), {'x': 0, 'y': 0, 'z': 0})

            node = {
                "name": device.get('name', f"Device_{i}"),
                "translation": [position['x'], position['y'], position['z']],
                "mesh": i
            }
            gltf["nodes"].append(node)

            # Add mesh (simplified cube for now)
            mesh = {
                "name": f"Mesh_{i}",
                "primitives": [{
                    "attributes": {
                        "POSITION": 0  # Would need actual vertex data
                    },
                    "material": 0
                }]
            }
            gltf["meshes"].append(mesh)

        # Add basic material
        gltf["materials"].append({
            "name": "DeviceMaterial",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.7, 0.7, 0.9, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.5
            }
        })

        return gltf

    def _create_svg_content(self, topology_data: Dict[str, Any]) -> str:
        """Create SVG content for 2D topology visualization"""
        devices = topology_data.get('devices', [])
        connections = topology_data.get('connections', [])
        layout = topology_data.get('layout', {})

        # Calculate bounds
        positions = layout.get('positions', {})
        if positions:
            x_coords = [pos['x'] for pos in positions.values()]
            y_coords = [pos['y'] for pos in positions.values()]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
        else:
            min_x = min_y = 0
            max_x = max_y = 1000

        width = max(max_x - min_x + 200, 800)
        height = max(max_y - min_y + 200, 600)

        # SVG header
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7"
     refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="1"/>

  <!-- Title -->
  <text x="20" y="30" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#333">
    Network Topology Visualization
  </text>
'''

        # Draw connections first (so they appear behind devices)
        for connection in connections:
            source_id = None
            target_id = None
            
            if isinstance(connection, (list, tuple)) and len(connection) >= 2:
                source_id = connection[0]
                target_id = connection[1]
            elif isinstance(connection, dict):
                source_id = connection.get('source')
                target_id = connection.get('target')

            if source_id in positions and target_id in positions:
                source_pos = positions[source_id]
                target_pos = positions[target_id]

                # Offset positions to center of SVG
                offset_x = -min_x + 100
                offset_y = -min_y + 100

                svg += f'''
  <!-- Connection {source_id} -> {target_id} -->
  <line x1="{source_pos['x'] + offset_x}" y1="{source_pos['y'] + offset_y}"
        x2="{target_pos['x'] + offset_x}" y2="{target_pos['y'] + offset_y}"
        stroke="#666" stroke-width="2" marker-end="url(#arrowhead)"/>
'''

        # Draw devices
        for device in devices:
            device_id = device.get('id')
            device_name = device.get('name', device_id)

            if device_id in positions:
                pos = positions[device_id]
                offset_x = -min_x + 100
                offset_y = -min_y + 100

                # Device rectangle
                svg += f'''
  <!-- Device {device_name} -->
  <rect x="{pos['x'] + offset_x - 40}" y="{pos['y'] + offset_y - 20}"
        width="80" height="40" fill="#fff" stroke="#333" stroke-width="2" rx="5"/>
  <text x="{pos['x'] + offset_x}" y="{pos['y'] + offset_y + 5}"
        text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#333">
    {device_name}
  </text>
'''

        svg += '\n</svg>'
        return svg

    def render_html_viewer(self, topology_data: Dict[str, Any], output_path: Path) -> bool:
        """Create HTML viewer for 3D topology (Three.js based)"""
        try:
            html_content = self._create_html_viewer_content(topology_data)

            with open(output_path, 'w') as f:
                f.write(html_content)

            logger.info(f"HTML viewer created at {output_path}")
            return True

        except Exception as e:
            logger.error(f"HTML viewer creation failed: {e}")
            return False

    def _create_html_viewer_content(self, topology_data: Dict[str, Any]) -> str:
        """Create HTML content for 3D topology viewer using 3d-force-graph"""
        devices = topology_data.get('devices', [])
        connections = topology_data.get('connections', [])

        # Prepare nodes
        nodes = []
        for device in devices:
            nodes.append({
                "id": device.get('id'),
                "name": device.get('name', device.get('id')),
                "type": device.get('type', 'unknown'),
                "vendor": device.get('vendor', 'unknown'),
                "val": 10  # Default size
            })

        # Prepare links
        links = []
        for conn in connections:
            # Handle both list/tuple and dict formats for connections
            if isinstance(conn, (list, tuple)) and len(conn) >= 2:
                links.append({"source": conn[0], "target": conn[1]})
            elif isinstance(conn, dict):
                src = conn.get('source')
                dst = conn.get('target')
                if src and dst:
                    links.append({"source": src, "target": dst})

        graph_data = {
            "nodes": nodes,
            "links": links
        }

        graph_data_js = json.dumps(graph_data, indent=2)

        # Icon mapping
        icon_map = {
            "fortigate": "/icons/fortigate.svg",
            "fortiswitch": "/icons/fortiswitch.svg",
            "fortiap": "/icons/fortiap.svg",
            "access_point": "/icons/ap.svg",
            "switch": "/icons/switch.svg",
            "router": "/icons/router.svg",
            "laptop": "/icons/laptop.svg",
            "mobile": "/icons/mobile.svg",
            "generic": "/icons/device_generic.svg"
        }
        icon_map_js = json.dumps(icon_map, indent=2)

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Network Topology Viewer</title>
    <script src="/static/vendor/three.min.js"></script>
    <script src="/static/vendor/SVGLoader.js"></script>
    <script src="/static/vendor/3d-force-graph.min.js"></script>
    <script src="/static/vendor/GLTFLoader.js"></script>
    <style>
        body {{ margin: 0; }}
        #3d-graph {{ width: 100vw; height: 100vh; }}
        #error-console {{
            position: fixed; top: 10px; left: 10px; z-index: 1000;
            background: rgba(255,0,0,0.8); color: white; padding: 10px;
            border-radius: 5px; font-family: monospace; display: none;
            max-width: 80%; white-space: pre-wrap;
        }}
    </style>
    <script>
        window.onerror = function(msg, url, line, col, error) {{
            const div = document.getElementById('error-console');
            if (div) {{
                div.style.display = 'block';
                div.innerHTML += `Error: ${{msg}}\\nLine: ${{line}}\\n\\n`;
            }}
            return false;
        }};
    </script>
</head>
<body>
    <div id="error-console"></div>
    <div id="3d-graph"></div>

    <script>
        const gData = {graph_data_js};
        
        // Icon mapping (SVGs)
        const iconMap = {icon_map_js};
        // Ensure cloud icon is mapped
        iconMap['cloud'] = "/icons/cloud.svg";
        iconMap['internet'] = "/icons/cloud.svg";

        const Graph = ForceGraph3D()
            (document.getElementById('3d-graph'))
            .graphData(gData)
            .nodeLabel('name')
            .dagMode('lr') // Left-to-Right Directed Acyclic Graph layout
            .dagLevelDistance(200) // Spacing between levels
            .nodeThreeObject(node => {{
                // Determine icon based on vendor or type
                let iconUrl = iconMap['generic'];
                
                // Check specific combinations first
                const key = (node.vendor + '_' + node.type).toLowerCase();
                
                // Check vendor-specific types
                if (node.vendor && node.vendor.toLowerCase().includes('fortinet')) {{
                    if (node.type.includes('switch')) iconUrl = iconMap['fortiswitch'];
                    else if (node.type.includes('access_point') || node.type.includes('ap')) iconUrl = iconMap['fortiap'];
                    else if (node.type.includes('router') || node.type.includes('firewall') || node.type.includes('gate')) iconUrl = iconMap['fortigate'];
                }} 
                // Check generic types if no vendor match
                else if (iconMap[node.type]) {{
                    iconUrl = iconMap[node.type];
                }}
                // Special case for Internet/Cloud
                if (node.name.toLowerCase().includes('internet') || node.type.toLowerCase().includes('cloud')) {{
                    iconUrl = iconMap['cloud'];
                }}
                
                // Create a group to hold the model
                const group = new THREE.Group();

                function loadSVG() {{
                    const loader = new THREE.SVGLoader();
                    loader.load(
                        iconUrl,
                        function(data) {{
                            const paths = data.paths;
                            const groupGeo = new THREE.Group();

                            for (let i = 0; i < paths.length; i++) {{
                                const path = paths[i];
                                const material = new THREE.MeshLambertMaterial({{
                                    color: path.color,
                                    side: THREE.DoubleSide,
                                    depthWrite: true
                                }});

                                const shapes = THREE.SVGLoader.createShapes(path);

                                for (let j = 0; j < shapes.length; j++) {{
                                    const shape = shapes[j];
                                    const geometry = new THREE.ExtrudeGeometry(shape, {{
                                        depth: 5,
                                        bevelEnabled: true,
                                        bevelThickness: 0.5,
                                        bevelSize: 0.5,
                                        bevelSegments: 2
                                    }});
                                    const mesh = new THREE.Mesh(geometry, material);
                                    groupGeo.add(mesh);
                                }}
                            }}
                            
                            // Center and scale
                            const box = new THREE.Box3().setFromObject(groupGeo);
                            const size = box.getSize(new THREE.Vector3());
                            const center = box.getCenter(new THREE.Vector3());
                            
                            groupGeo.position.x = -center.x;
                            groupGeo.position.y = -center.y;
                            groupGeo.position.z = -center.z;
                            
                            // Scale to fit
                            const maxDim = Math.max(size.x, size.y);
                            const scale = 20 / maxDim;
                            groupGeo.scale.set(scale, -scale, scale); 
                            
                            group.add(groupGeo);
                        }},
                        undefined,
                        function(err) {{
                           console.error('Error loading SVG:', iconUrl, err);
                        }}
                    );
                }}

                // Check for 3D Model
                if (node.model_path && node.model_path.endsWith('.glb')) {{
                    const gltfloader = new THREE.GLTFLoader();
                    gltfloader.load(
                        '/' + node.model_path, // Ensure absolute path from root
                        (gltf) => {{
                            const model = gltf.scene;
                            
                            // Normalize Scale
                            const box = new THREE.Box3().setFromObject(model);
                            const size = box.getSize(new THREE.Vector3());
                            const maxDim = Math.max(size.x, size.y, size.z);
                            const scale = 30 / maxDim; 
                            model.scale.set(scale, scale, scale);
                            
                            // Center
                            const center = box.getCenter(new THREE.Vector3());
                            model.position.x = -center.x * scale;
                            model.position.y = -center.y * scale;
                            model.position.z = -center.z * scale;

                            group.add(model);
                        }},
                        undefined,
                        (err) => {{
                            console.warn("GLB load failed, falling back to SVG", node.model_path);
                            loadSVG();
                        }}
                    );
                }} else {{
                    loadSVG();
                }}
                
                return group;
            }})
            .backgroundColor('#000011')
            .linkDirectionalParticles(2)
            .linkDirectionalParticleSpeed(0.005)
            .linkOpacity(0.5)
            .linkWidth(1)
            .nodeLabel(node => {{
                return `<div style="background: rgba(0,0,0,0.8); color: white; padding: 5px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 0 10px rgba(0,255,255,0.3);">
                    <b>${{node.name}}</b><br>
                    ${{node.vendor}} ${{node.type}}
                </div>`;
            }});
            
        // Add lights to scene so models are visible
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        Graph.scene().add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(10, 20, 10);
        Graph.scene().add(directionalLight);
        
        // Add starfield
        const starGeo = new THREE.BufferGeometry();
        const starCount = 1000;
        const starPos = new Float32Array(starCount * 3);
        for(let i=0; i<starCount*3; i++) {{
            starPos[i] = (Math.random() - 0.5) * 2000;
        }}
        starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
        const starMat = new THREE.PointsMaterial({{color: 0x888888, size: 0.5}});
        const starField = new THREE.Points(starGeo, starMat);
        Graph.scene().add(starField);
    </script>
</body>
</html>'''

        return html