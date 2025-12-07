"""
FortiSwitch Service (Optimized - Sync)
Provides logic for discovering and managing FortiSwitch devices with parallel data fetching.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class FortiSwitchService:
    def __init__(self, fgt_client):
        self.fgt_client = fgt_client
        # Lazy load restaurant service
        from .restaurant_device_service import get_restaurant_device_service
        self.restaurant_service = get_restaurant_device_service()
        
        # Regex for MAC normalization
        self.MAC_NORMALIZE_PATTERN = re.compile(r'[^0-9A-Fa-f]')
        self.MAC_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')

    def normalize_mac(self, mac: str) -> Optional[str]:
        """Optimized MAC normalization."""
        if not mac or not isinstance(mac, str):
            return None
        clean_mac = self.MAC_NORMALIZE_PATTERN.sub('', mac.upper())
        if len(clean_mac) != 12:
            return mac # Return raw if invalid length
        return ':'.join(clean_mac[i:i+2] for i in range(0, 12, 2))

    def get_enhanced_switches(self) -> List[Dict[str, Any]]:
        """
        Get switches with aggregated device information (DHCP/ARP/Detected) using parallel fetching.
        """
        logger.info("Starting Optimized FortiSwitch Discovery (Sync-Parallel)...")
        
        # 1. Parallel Fetch using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_switches = executor.submit(self.fgt_client.get_monitor, "switch-controller/managed-switch/status")
            future_detected = executor.submit(self.fgt_client.get_monitor, "switch-controller/detected-device")
            future_dhcp = executor.submit(self.fgt_client.get_monitor, "system/dhcp")
            future_arp = executor.submit(self.fgt_client.get_monitor, "system/arp")
            
            # Retrieve results (blocking until ready)
            try:
                switches_data = future_switches.result() or {}
                detected_data = future_detected.result() or {}
                dhcp_data = future_dhcp.result() or {}
                arp_data = future_arp.result() or {}
            except Exception as e:
                logger.error(f"Parallel fetch failed: {e}")
                return []

        # 2. Build Lookup Maps
        dhcp_map = self._build_dhcp_map(dhcp_data)
        arp_map = self._build_arp_map(arp_data)
        detected_map = self._build_detected_map(detected_data)

        # 3. Aggregate
        switches = []
        raw_switches = switches_data.get("results", []) if isinstance(switches_data, dict) else []
        
        for sw in raw_switches:
            serial = sw.get("serial")
            
            # Enrich ports
            enriched_ports = []
            for port in sw.get("ports", []):
                port_name = port.get("interface")
                port_key = f"{serial}:{port_name}"
                
                connected = []
                # Use detected map first (Layer 2 truth)
                if port_key in detected_map:
                    for ddev in detected_map[port_key]:
                        mac = ddev.get("mac") # Already normalized in build_map
                        
                        # Data fusion
                        dhcp_info = dhcp_map.get(mac, {})
                        arp_info = arp_map.get(mac, {})
                        
                        device_info = {
                            "device_name": dhcp_info.get("hostname") or f"Device-{mac[-4:]}",
                            "device_mac": mac,
                            "device_ip": dhcp_info.get("ip") or arp_info.get("ip", "Unknown"),
                            "manufacturer": ddev.get("manufacturer", "Unknown"),
                            "vlan": ddev.get("vlan_id"),
                            "source": "switch_controller",
                            "status": "online"
                        }
                        
                        # Restaurant Classification
                        device_info = self.restaurant_service.enhance_device_info(device_info)
                        connected.append(device_info)
                
                port["connected_devices"] = connected
                enriched_ports.append(port)
            
            sw["ports"] = enriched_ports
            switches.append(sw)
            
        logger.info(f"Optimized Discovery Complete. Found {len(switches)} switches.")
        return switches

    def _build_dhcp_map(self, data):
        mapping = {}
        if not isinstance(data, dict): return mapping
        for entry in data.get("results", []):
            mac = self.normalize_mac(entry.get("mac"))
            if mac:
                mapping[mac] = entry
        return mapping

    def _build_arp_map(self, data):
        mapping = {}
        if not isinstance(data, dict): return mapping
        for entry in data.get("results", []):
            mac = self.normalize_mac(entry.get("mac"))
            if mac:
                mapping[mac] = entry
        return mapping

    def _build_detected_map(self, data):
        mapping = {}
        if not isinstance(data, dict): return mapping
        for dev in data.get("results", []):
            sw = dev.get("switch_id")
            port = dev.get("port_name")
            if sw and port:
                key = f"{sw}:{port}"
                if key not in mapping:
                    mapping[key] = []
                
                # Normalize mac here
                dev['mac'] = self.normalize_mac(dev.get('mac'))
                mapping[key].append(dev)
        return mapping

_svc = None
def get_fortiswitch_service(fgt_client=None) -> FortiSwitchService:
    global _svc
    if _svc is None:
        if fgt_client is None:
            raise ValueError("FortiSwitchService requires fgt_client initialization")
        _svc = FortiSwitchService(fgt_client)
    return _svc
