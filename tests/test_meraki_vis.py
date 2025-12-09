import pytest
from unittest.mock import MagicMock
from shared.visualization.meraki_visualizer import MerakiVisualizer

@pytest.fixture
def mock_dashboard():
    dashboard = MagicMock()
    # Mock devices
    dashboard.networks.getNetworkDevices.return_value = [
        {"serial": "Q234-5678-90AB", "model": "MX68", "name": "Main FW", "networkId": "N_1"}
    ]
    # Mock clients
    dashboard.networks.getNetworkClients.return_value = [
        {"id": "k123", "mac": "00:11:22:33:44:55", "description": "User Laptop", "ip": "10.0.0.5"}
    ]
    return dashboard

def test_meraki_vis_generation(mock_dashboard):
    """Test HTML generation from Meraki data"""
    visualizer = MerakiVisualizer(mock_dashboard)
    
    html = visualizer.create_visualization("N_1", "Test Network")
    
    assert html is not None
    assert "<!DOCTYPE html>" in html
    assert "Test Network" in html
    assert "Main FW" in html
    assert "User Laptop" in html
    
    # Check for local assets
    assert "/static/vendor/vis.min.js" in html

def test_meraki_topology_build(mock_dashboard):
    """Test internal topology structure"""
    visualizer = MerakiVisualizer(mock_dashboard)
    
    devices = [{"serial": "d1", "model": "MS120", "name": "Switch"}]
    clients = [{"id": "c1", "mac": "aa:bb:cc:dd:ee:ff", "recentDeviceSerial": "d1"}]
    
    topo = visualizer.build_topology(devices, clients)
    
    assert len(topo["nodes"]) == 2
    assert len(topo["links"]) == 1 # c1 -> d1
    
    # Verify link
    link = topo["links"][0]
    assert link["source"] == "c1"
    assert link["target"] == "d1"
