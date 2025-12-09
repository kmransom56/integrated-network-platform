import pytest
from pathlib import Path
import json
import shutil
from shared.visualization.renderer import VisualizationRenderer

@pytest.fixture
def temp_output_dir(tmp_path):
    d = tmp_path / "viz_out"
    d.mkdir()
    return d

def test_renderer_html_generation(temp_output_dir):
    """Test generating 3D HTML viewer"""
    renderer = VisualizationRenderer()
    
    topology_data = {
        "devices": [
            {"id": "gate1", "name": "Core Gate", "type": "fortigate", "vendor": "Fortinet"},
            {"id": "sw1", "name": "Switch 1", "type": "switch", "vendor": "Cisco"}
        ],
        "connections": [
            ["gate1", "sw1"]
        ]
    }
    
    output_path = temp_output_dir / "test_viz.html"
    success = renderer.render_html_viewer(topology_data, output_path)
    
    assert success is True
    assert output_path.exists()
    
    content = output_path.read_text()
    assert "Core Gate" in content
    assert "fortigate" in content
    assert "/icons/fortigate.svg" in content
    assert "3d-force-graph.min.js" in content

def test_renderer_svg_generation(temp_output_dir):
    """Test generating SVG topology"""
    renderer = VisualizationRenderer()
    
    topology_data = {
        "devices": [
            {"id": "d1", "name": "Device 1"},
            {"id": "d2", "name": "Device 2"}
        ],
        "connections": [
            {"source": "d1", "target": "d2"}
        ],
        "layout": {
            "positions": {
                "d1": {"x": 0, "y": 0},
                "d2": {"x": 100, "y": 100}
            }
        }
    }
    
    output_path = temp_output_dir / "test_topology.svg"
    success = renderer.export_svg(topology_data, output_path)
    
    assert success is True
    assert output_path.exists()
    
    content = output_path.read_text()
    assert "<svg" in content
    assert "Device 1" in content
