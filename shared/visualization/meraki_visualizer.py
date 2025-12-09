"""
Meraki Visualizer
Ported from cisco-meraki-cli-enhanced/utilities/enhanced_visualizer.py
Integrated into the Unified Platform.
"""
import os
import logging
from pathlib import Path
import uuid
import json
from ..network_utils import mac_vendor

# Initialize Config to get paths
try:
    cm = ConfigManager()
    if cm.config.data_dir:
        mac_vendor.set_db_path(cm.config.data_dir / "mac_vendor_cache.db")
        # Re-init DB at new path
        mac_vendor._init_db()
except Exception:
    pass

# Wrapper for legacy compatibility in this file
def get_vendor_from_mac(mac):
    return mac_vendor.get_vendor(mac)

def update_oui_database():
    # Pass through or implement if needed
    pass

# --- MAPS ---
VENDOR_DEVICE_TYPE_MAP = {
    "Apple, Inc.": "mobile", "Samsung Electronics": "mobile", "Cisco Systems": "network_device",
    "Meraki": "network_device", "Fortinet": "network_device", "Dell": "desktop", "HP": "printer",
    "Sonos": "speaker", "Roku": "streaming_device", "Zebra": "scanner", "Ubiquiti": "network_device"
}
# (Simplified map for brevity in port, can expand later if needed)

HOSTNAME_DEVICE_TYPE_MAP = {
    "pos": "point_of_sale", "printer": "printer", "phone": "voip", "cam": "camera",
    "mobile": "mobile", "tablet": "tablet", "desktop": "desktop", "laptop": "desktop"
}

HOSTNAME_ICON_MAP = {
    "fortiap": "fortiap.svg", "ms120": "meraki_switch.svg", "ms220": "meraki_switch.svg",
    "ms225": "meraki_switch.svg", "ms250": "meraki_switch.svg", "ms350": "meraki_switch.svg",
    "ms425": "meraki_switch.svg"
}

DEVICE_ICONS = {
    'appliance': 'firewall', 'switch': 'switch', 'wireless': 'ap', 'camera': 'videocam',
    'phone': 'phone', 'desktop': 'desktop_windows', 'mobile': 'smartphone', 'printer': 'printer',
    'server': 'dns', 'voip': 'phone', 'tablet': 'tablet', 'gateway': 'router',
    'client': 'devices_other', 'point_of_sale': 'point-of-sale', 'network_device': 'router',
    'iot': 'memory', 'speaker': 'speaker', 'streaming_device': 'cast', 'scanner': 'qr_code_scanner',
    'unknown': 'device_unknown'
}

CONNECTION_STYLES = {
    'uplink': {'color': '#00C853', 'width': 3, 'dashes': False, 'label': 'Uplink', 'highlight': '#00C853', 'arrow': True},
    'switch': {'color': '#2196F3', 'width': 2, 'dashes': False, 'label': 'Switch Connection', 'highlight': '#2196F3', 'arrow': True},
    'wireless': {'color': '#FF9800', 'width': 2, 'dashes': True, 'label': 'Wireless Connection', 'highlight': '#FF9800', 'arrow': False},
    'wired': {'color': '#607D8B', 'width': 1, 'dashes': False, 'label': 'Wired Client', 'highlight': '#607D8B', 'arrow': True},
    'unknown': {'color': '#9E9E9E', 'width': 1, 'dashes': True, 'label': 'Unknown Connection', 'highlight': '#9E9E9E', 'arrow': False}
}

MAC_DEVICE_OVERRIDE = {
    "00:0C:E6:86:11:E0": {"type": "appliance", "vendor": "Fortinet", "label": "FortiGate 81E", "icon": "fortigate.svg"},
    "000CE68611E0": {"type": "appliance", "vendor": "Fortinet", "label": "FortiGate 81E", "icon": "fortigate.svg"},
}

def get_device_type_from_hostname(hostname):
    if not hostname: return None
    hostname = hostname.lower()
    for pattern, device_type in HOSTNAME_DEVICE_TYPE_MAP.items():
        if pattern in hostname: return device_type
    return None

def get_device_type_from_vendor(vendor):
    if not vendor: return "unknown"
    for key, dtype in VENDOR_DEVICE_TYPE_MAP.items():
        if key.lower() in vendor.lower(): return dtype
    return "unknown"

class MerakiVisualizer:
    """
    Enhanced Meraki Visualizer class
    """
    def __init__(self, dashboard):
        self.dashboard = dashboard

    def create_visualization(self, network_id, network_name):
        try:
            if MacLookup:
                try:
                    MacLookup().lookup("00:00:00:00:00:00")
                except:
                    update_oui_database()

            devices = self.dashboard.networks.getNetworkDevices(network_id)
            clients = self.dashboard.networks.getNetworkClients(network_id, timespan=86400)
            
            topology_data = self.build_topology(devices, clients)
            topology_data['network_name'] = network_name
            
            return self.generate_html(topology_data, network_name)
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            return None

    def build_topology(self, devices, clients, links=None):
        topology = {'nodes': [], 'links': []}
        device_map = {}
        device_relationships = {} # network_id -> {appliances:[], switches:[], wireless:[]}
        
        # Process Devices
        for device in devices:
            device_id = device.get('serial', device.get('mac', str(uuid.uuid4())))
            device_map[device_id] = device
            model = device.get('model', '').lower()
            name = device.get('name', '').lower()
            # Infer Type
            d_type = 'unknown'
            if 'mx' in model or 'security appliance' in name: d_type = 'appliance'
            elif 'mr' in model or 'access point' in name: d_type = 'wireless'
            elif 'ms' in model or 'switch' in name: d_type = 'switch'
            
            node = {
                'id': device_id,
                'label': device.get('name', device.get('mac', 'Unknown')),
                'type': d_type,
                'model': device.get('model'),
                'ip': device.get('lanIp', device.get('ip')),
                'mac': device.get('mac'),
                'status': device.get('status')
            }
            if device.get('ports'): node['ports'] = device['ports']
            topology['nodes'].append(node)
            
            nid = device.get('networkId')
            if nid:
                if nid not in device_relationships: device_relationships[nid] = {'appliances':[], 'switches':[], 'wireless':[]}
                if d_type == 'appliance': device_relationships[nid]['appliances'].append(device_id)
                elif d_type == 'switch': device_relationships[nid]['switches'].append(device_id)
                elif d_type == 'wireless': device_relationships[nid]['wireless'].append(device_id)

        # Process Clients
        client_map = {}
        for client in clients:
            client_id = client.get('id', client.get('mac', str(uuid.uuid4())))
            client_map[client_id] = client
            
            # Type Inference Logic
            c_type = 'unknown'
            if client.get('deviceTypePrediction'): c_type = client.get('deviceTypePrediction').lower()
            elif client.get('os'):
                 os_name = client.get('os', '').lower()
                 if 'windows' in os_name: c_type = 'desktop'
                 elif 'ios' in os_name or 'android' in os_name: c_type = 'mobile'
            
            if c_type == 'unknown' and client.get('manufacturer'):
                manu = client.get('manufacturer', '').lower()
                if 'apple' in manu: c_type = 'mobile'
            
            node = {
                'id': client_id,
                'label': client.get('description') or client.get('mac'),
                'type': 'client',
                'client_type': c_type,
                'ip': client.get('ip'),
                'mac': client.get('mac'),
                'status': client.get('status'),
                'manufacturer': client.get('manufacturer')
            }
            topology['nodes'].append(node)
            
            # Link to Device
            recent_device = client.get('recentDeviceSerial')
            if recent_device and recent_device in device_map:
                link_type = 'wireless' if client.get('ssid') else 'wired'
                topology['links'].append({
                    'source': client_id, 'target': recent_device,
                    'type': link_type,
                    'interface': client.get('switchport') or client.get('ssid')
                })

        # Infrastructure Links
        existing = set()
        for l in topology['links']: existing.add((l['source'], l['target']))
        
        for nid, rels in device_relationships.items():
            # App -> Switch
            for app in rels['appliances']:
                for sw in rels['switches']:
                    if (app, sw) not in existing:
                        topology['links'].append({'source': app, 'target': sw, 'type': 'uplink'})
                        existing.add((app, sw))
                # App -> Wireless (if no switch)
                if not rels['switches']:
                    for wap in rels['wireless']:
                        if (app, wap) not in existing:
                             topology['links'].append({'source': app, 'target': wap, 'type': 'uplink'})
                             
            # Switch -> Wireless
            for sw in rels['switches']:
                for wap in rels['wireless']:
                    if (sw, wap) not in existing:
                        topology['links'].append({'source': sw, 'target': wap, 'type': 'switch'})
                        existing.add((sw, wap))
                        
        return topology

    def generate_html(self, topology_data, network_name):
        # Generate VisJS Data
        vis_nodes = []
        vis_edges = []
        
        for n in topology_data['nodes']:
            # Minimal VisJS Mapping
            icon_path = None
            # Icon logic (simplified)
            ntype = n.get('type')
            is_client = ntype == 'client'
            ctype = n.get('client_type', 'unknown')
            
            label = n.get('label', 'Unknown')
            mac = n.get('mac', '')
            
            # Check Override
            clean_mac = mac.upper().replace(':','').replace('.','') if mac else ''
            if clean_mac in MAC_DEVICE_OVERRIDE:
                ntype = 'appliance' # Override type
                # In real app we might want specific icon path from map
            
            icon_key = ntype
            if is_client and ctype in DEVICE_ICONS: icon_key = ctype
            
            # Path Logic (Assuming served under /icons/)
            # We will use /icons/filename.svg
            # Need to map DEVICE_ICONS to filenames
            # DEVICE_ICONS maps 'appliance' -> 'firewall'
            # We assume firewall.svg or firewall.png exists
            
            icon_name = DEVICE_ICONS.get(icon_key, 'device_unknown')
            icon_path = f"/icons/{icon_name}.svg" # Default to SVG
            
            # Vendor specific check?
            if n.get('manufacturer') == 'Apple':
                 icon_path = "/icons/apple.png" # Example
            
            vis_nodes.append({
                'id': n['id'],
                'label': label,
                'shape': 'circularImage',
                'image': icon_path,
                'title': f"{label}\n{n.get('ip','')}\n{mac}",
                'size': 20 if is_client else 30
            })
            
        for l in topology_data['links']:
            style = CONNECTION_STYLES.get(l.get('type'), CONNECTION_STYLES['unknown'])
            vis_edges.append({
                'from': l['source'], 'to': l['target'],
                'color': {'color': style['color']},
                'width': style['width'],
                'dashes': style['dashes']
            })
            
        # HTML Template
        html = f"""<!DOCTYPE html>
<html><head>
<title>{network_name}</title>
<script type="text/javascript" src="/static/vendor/vis.min.js"></script>
<link href="/static/vendor/vis-network.min.css" rel="stylesheet" />
<style>#network {{ width: 100vw; height: 100vh; }}</style>
</head><body>
<div id="network"></div>
<script>
var nodes = new vis.DataSet({json.dumps(vis_nodes)});
var edges = new vis.DataSet({json.dumps(vis_edges)});
var container = document.getElementById('network');
var data = {{nodes: nodes, edges: edges}};
var options = {{
    nodes: {{borderWidth: 2, shadow: true}},
    layout: {{improvedLayout: true}}
}};
var network = new vis.Network(container, data, options);
</script>
</body></html>"""
        return html
