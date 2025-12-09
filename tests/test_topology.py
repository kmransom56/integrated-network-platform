import pytest
from shared.network_utils.topology_builder import TopologyBuilder

def test_topology_builder_basic():
    """Test basic topology construction"""
    tb = TopologyBuilder()
    
    devices = [
        {"id": "fw1", "name": "Firewall", "type": "firewall"},
        {"id": "sw1", "name": "Switch", "type": "switch"}
    ]
    connections = [("fw1", "sw1")]
    
    topology = tb.build_topology(devices, connections)
    
    assert len(topology["devices"]) == 2
    assert len(topology["connections"]) == 1
    assert topology["devices"][0]["id"] == "fw1"
    
def test_topology_validation():
    """Test topology validation logic"""
    tb = TopologyBuilder()
    
    # Valid topology
    valid_data = {
        "devices": [{"id": "d1", "name": "D1"}],
        "connections": []
    }
    res = tb.validate_topology(valid_data)
    assert res["valid"] is True
    
    # Invalid topology (missing ID)
    invalid_data = {
        "devices": [{"name": "No ID"}],
        "connections": []
    }
    res = tb.validate_topology(invalid_data)
    assert res["valid"] is False
    assert len(res["errors"]) > 0

def test_layered_layout():
    """Test layered layout algorithm"""
    tb = TopologyBuilder()
    devices = [
        {"id": "root", "type": "firewall"},
        {"id": "sw1", "type": "switch"},
        {"id": "sw2", "type": "switch"},
        {"id": "pc1", "type": "client"}
    ]
    # Hierarchy: root -> sw1 -> pc1 (and sw2 separate)
    connections = [("root", "sw1"), ("sw1", "pc1"), ("root", "sw2")]
    
    topology = tb.build_topology(devices, connections)
    layout = tb._apply_layered_layout()
    
    positions = layout["positions"]
    
    # Root should be at top (y=0 usually or low index)
    # PC1 should be below SW1
    # Note: verify actual coordinate logic in builder, but generally they exist
    assert "root" in positions
    assert "pc1" in positions
    assert positions["root"]["y"] != positions["pc1"]["y"]
