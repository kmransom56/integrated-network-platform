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
        """Create HTML content for 3D topology viewer"""
        devices = topology_data.get('devices', [])
        connections = topology_data.get('connections', [])
        layout = topology_data.get('layout', {})

        # Convert topology data to JavaScript
        devices_js = json.dumps(devices, indent=2)
        connections_js = json.dumps(connections, indent=2)
        layout_js = json.dumps(layout, indent=2)

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Network Topology Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        body {{ margin: 0; background: #f0f0f0; }}
        #viewer {{ width: 100vw; height: 100vh; }}
        #info {{ position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.8); padding: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div id="viewer"></div>
    <div id="info">
        <h3>Network Topology Viewer</h3>
        <p>Devices: {len(devices)} | Connections: {len(connections)}</p>
        <p>Use mouse to orbit, zoom, and pan</p>
    </div>

    <script>
        // Topology data
        const devices = {devices_js};
        const connections = {connections_js};
        const layout = {layout_js};

        // Three.js scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f0f0);

        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(200, 200, 200);

        const renderer = new THREE.WebGLRenderer();
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.getElementById('viewer').appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 100, 50);
        scene.add(directionalLight);

        // Add devices
        const deviceGeometry = new THREE.BoxGeometry(10, 10, 10);
        const deviceMaterial = new THREE.MeshLambertMaterial({{ color: 0x4a90e2 }});

        devices.forEach((device, index) => {{
            const pos = layout.positions ? layout.positions[device.id] : {{x: index * 50, y: 0, z: 0}};

            const mesh = new THREE.Mesh(deviceGeometry, deviceMaterial);
            mesh.position.set(pos.x || 0, pos.y || 0, pos.z || 0);
            mesh.userData = device;
            scene.add(mesh);

            // Add label
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            context.font = '24px Arial';
            context.fillStyle = 'rgba(255,255,255,1)';
            context.fillText(device.name, 0, 24);

            const texture = new THREE.CanvasTexture(canvas);
            const spriteMaterial = new THREE.SpriteMaterial({{ map: texture }});
            const sprite = new THREE.Sprite(spriteMaterial);
            sprite.position.set(pos.x || 0, pos.y + 20 || 20, pos.z || 0);
            scene.add(sprite);
        }});

        // Add connections
        connections.forEach(connection => {{
            const sourcePos = layout.positions ? layout.positions[connection.source] : {{x: 0, y: 0, z: 0}};
            const targetPos = layout.positions ? layout.positions[connection.target] : {{x: 100, y: 0, z: 0}};

            const points = [
                new THREE.Vector3(sourcePos.x || 0, sourcePos.y || 0, sourcePos.z || 0),
                new THREE.Vector3(targetPos.x || 0, targetPos.y || 0, targetPos.z || 0)
            ];

            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const material = new THREE.LineBasicMaterial({{ color: 0x666666, linewidth: 2 }});
            const line = new THREE.Line(geometry, material);
            scene.add(line);
        }});

        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        // Handle window resize
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
    </script>
</body>
</html>'''

        return html