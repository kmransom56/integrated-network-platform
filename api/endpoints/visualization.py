"""
Visualization Endpoints
3D visualization API from network_map_3d
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import json
from pathlib import Path

from ...shared.network_utils.data_formatter import NetworkDataFormatter
from ...shared.network_utils.topology_builder import TopologyBuilder
from ...shared.visualization.renderer import VisualizationRenderer

router = APIRouter()


class TopologyRequest(BaseModel):
    """Topology visualization request"""
    devices: List[Dict[str, Any]]
    connections: List[List[str]]
    layout: str = "layered"
    renderer: str = "three.js"


class VisualizationExport(BaseModel):
    """Visualization export request"""
    topology_data: Dict[str, Any]
    format: str = "gltf"  # gltf, svg, json
    include_textures: bool = True


@router.post("/topology")
async def create_topology_visualization(request: TopologyRequest):
    """Create 3D topology visualization"""
    try:
        # Build topology
        topology_builder = TopologyBuilder()
        topology = topology_builder.build_topology(
            request.devices,
            [(src, tgt) for src, tgt in request.connections]
        )

        # Apply layout
        if request.layout == "layered":
            topology = topology_builder._apply_layered_layout()
        elif request.layout == "optimized":
            topology = topology_builder.optimize_layout(topology)

        # Format for 3D visualization
        formatter = NetworkDataFormatter()
        visualization_data = formatter.format_for_3d_visualization(topology)

        return {
            "topology": topology,
            "visualization": visualization_data,
            "layout": request.layout,
            "renderer": request.renderer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topology creation failed: {str(e)}")


@router.post("/export")
async def export_visualization(request: VisualizationExport, req: Request):
    """Export visualization in specified format"""
    try:
        config = req.app.state.config

        # Create export directory
        export_dir = config.config.exports_dir
        export_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"topology_{timestamp}.{request.format}"
        filepath = export_dir / filename

        # Export based on format
        if request.format == "json":
            with open(filepath, 'w') as f:
                json.dump(request.topology_data, f, indent=2)
        elif request.format == "gltf":
            # Would integrate GLTF export from network_map_3d
            renderer = VisualizationRenderer()
            renderer.export_gltf(request.topology_data, filepath)
        elif request.format == "svg":
            # Would integrate SVG export
            renderer = VisualizationRenderer()
            renderer.export_svg(request.topology_data, filepath)

        return {
            "message": "Visualization exported successfully",
            "filepath": str(filepath),
            "url": f"/static/{filename}",
            "format": request.format
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/scenes")
async def list_visualization_scenes(req: Request):
    """List available visualization scenes"""
    try:
        config = req.app.state.config
        export_dir = config.config.exports_dir

        scenes = []
        if export_dir.exists():
            for file_path in export_dir.glob("*"):
                if file_path.suffix in ['.json', '.gltf', '.glb', '.svg']:
                    scenes.append({
                        "name": file_path.stem,
                        "format": file_path.suffix[1:],  # Remove the dot
                        "path": str(file_path),
                        "url": f"/static/{file_path.name}",
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })

        return {
            "scenes": sorted(scenes, key=lambda x: x['modified'], reverse=True),
            "total_scenes": len(scenes)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scenes: {str(e)}")


@router.get("/scene/{scene_name}")
async def get_visualization_scene(scene_name: str, req: Request):
    """Get a specific visualization scene"""
    try:
        config = req.app.state.config
        export_dir = config.config.exports_dir

        # Find the scene file
        scene_file = None
        for file_path in export_dir.glob(f"{scene_name}.*"):
            scene_file = file_path
            break

        if not scene_file:
            raise HTTPException(status_code=404, detail=f"Scene {scene_name} not found")

        # Load and return scene data
        if scene_file.suffix == ".json":
            with open(scene_file, 'r') as f:
                scene_data = json.load(f)
        else:
            # For binary formats, return file info
            scene_data = {
                "type": scene_file.suffix[1:],
                "path": str(scene_file),
                "url": f"/static/{scene_file.name}",
                "size": scene_file.stat().st_size
            }

        return scene_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scene: {str(e)}")


@router.get("/renderers")
async def get_available_renderers():
    """Get available visualization renderers"""
    return {
        "renderers": [
            {
                "name": "three.js",
                "description": "WebGL-based 3D renderer",
                "formats": ["json", "gltf", "obj"],
                "features": ["real-time", "interactive", "lighting"]
            },
            {
                "name": "babylon.js",
                "description": "Alternative WebGL 3D renderer",
                "formats": ["json", "gltf"],
                "features": ["physics", "advanced_materials"]
            },
            {
                "name": "svg",
                "description": "2D SVG topology visualization",
                "formats": ["svg"],
                "features": ["scalable", "printable"]
            }
        ],
        "default_renderer": "three.js"
    }


@router.post("/validate")
async def validate_topology_data(topology_data: Dict[str, Any]):
    """Validate topology data for visualization"""
    try:
        topology_builder = TopologyBuilder()
        validation_result = topology_builder.validate_topology(topology_data)

        return {
            "valid": validation_result["valid"],
            "warnings": validation_result["warnings"],
            "errors": validation_result["errors"],
            "summary": {
                "total_warnings": len(validation_result["warnings"]),
                "total_errors": len(validation_result["errors"])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")