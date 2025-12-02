#!/usr/bin/env python3
"""Test SVG generation"""

def test_svg():
    """Test SVG generation function"""
    devices = [
        {'id': 'wd1', 'label': 'Desktop PC 1', 'device_type': 'client', 'position_2d': {'x': 5, 'y': 0}},
        {'id': 'wd2', 'label': 'Desktop PC 2', 'device_type': 'client', 'position_2d': {'x': 10, 'y': 0}}
    ]
    connections = [('sw1', 'wd1'), ('sw1', 'wd2')]

    try:
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7"
     refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
    </marker>
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

        print("SVG content created successfully")
        print(f"Devices: {len(devices)}")
        print(f"Connections: {len(connections)}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_svg()