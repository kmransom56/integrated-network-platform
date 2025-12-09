"""
Compatibility Endpoints
To serve legacy D3 frontend requests using the new architecture.
"""
from fastapi import APIRouter, HTTPException
from shared.device_handling.device_collector import UnifiedDeviceCollector
from shared.network_utils.authentication import AuthManager
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/topology")
async def get_legacy_topology():
    """
    Serve topology in the format expected by D3 frontend.
    """
    try:
        auth_manager = AuthManager()
        collector = UnifiedDeviceCollector(auth_manager)
        
        # Attempt to get credentials from Environment (compatible with network-d3js .env)
        host = os.getenv('FORTIGATE_HOST') or "192.168.0.254"
        token = os.getenv('API_TOKEN') or os.getenv('FORTIGATE_TOKEN')
        
        if host and token:
             logger.info(f"Compat: Collecting from {host}...")
             collector.collect_from_fortigate(host, "admin", "", token=token)
        
        devices = collector.get_all_devices()
        
        nodes = []
        links = []
        
        for d in devices:
            # Map Unified Device structure to D3 expected structure
            # index.html expects: id, name, type, ip, mac...
            
            dtype = d.device_type.value if hasattr(d.device_type, 'value') else str(d.device_type)
            
            # Icon selection logic in index.html relies on 'type' (FortiGate, FortiSwitch, FortiAP)
            # Map enum values to these strings
            if dtype == 'fortigate': dtype = 'FortiGate'
            elif dtype == 'fortiswitch': dtype = 'FortiSwitch'
            elif dtype == 'fortiap': dtype = 'FortiAP'
            elif dtype == 'client': dtype = 'Client' # or generic
            
            node = {
                "id": d.id,
                "name": d.name,
                "type": dtype,
                "ip": d.ip_address,
                "mac": d.mac_address,
                "status": d.status,
                "vendor": "Fortinet" if "forti" in dtype.lower() else "Unknown",
                "model": d.model
            }
            if d.metadata:
                # Flattens metadata for easy access
                for k, v in d.metadata.items():
                    if k not in node:
                        node[k] = v
            
            nodes.append(node)
            
            # Generate Links
            # 1. Client -> Switch
            if d.metadata and d.metadata.get('connected_to_switch'):
                target = d.metadata.get('connected_to_switch')
                # Check if target exists in nodes? D3 might handle it, but better safe.
                links.append({
                    "source": d.id,
                    "target": target,
                    "type": "ethernet"
                })
        
        # Logic to link Switch -> Gate is usually missing in simple collection unless manual
        # Add basic Uplink logic (All switches -> Gate) if not present?
        # For now, return what we have.
        
        return {"nodes": nodes, "links": links}

    except Exception as e:
        logger.error(f"Error generating topology: {e}")
        return {"nodes": [], "links": []}

@router.get("/node-status")
async def get_node_status():
    """Return empty or basic status to satisfy D3 polling"""
    return {}
