"""
FortiGate Inventory Service
Loads and manages real FortiGate management IP addresses from CSV file.
"""

import logging
import csv
import os
import ipaddress
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FortiGateLocation:
    store_number: str
    mgmt_interface: str
    ip_address: str
    subnet_mask: str
    brand: str
    region: Optional[str] = None
    status: str = "unknown"

class FortiGateInventoryService:
    def __init__(self, csv_path: str = "downloaded_files/vlan10_interfaces.csv"):
        self.csv_path = csv_path
        self.locations: Dict[str, FortiGateLocation] = {}
        self._load_fortigate_inventory()

    def _load_fortigate_inventory(self) -> None:
        if not os.path.exists(self.csv_path):
            logger.error(f"Inventory CSV not found: {self.csv_path}")
            return
            
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    store = row.get('store_number', '').strip()
                    ip_cidr = row.get('ip_address', '').strip()
                    if not store or not ip_cidr: continue
                    
                    ip_addr = ip_cidr.split('/')[0] if '/' in ip_cidr else ip_cidr
                    
                    self.locations[store] = FortiGateLocation(
                        store_number=store,
                        mgmt_interface=row.get('mgmtintname', ''),
                        ip_address=ip_addr,
                        subnet_mask="255.255.255.0", # Simplified
                        brand=row.get('brand', 'Unknown'),
                        region=self._determine_region(store, ip_addr)
                    )
        except Exception as e:
            logger.error(f"Failed to load inventory: {e}")

    def _determine_region(self, store: str, ip: str) -> str:
        # Simplified region logic
        if "SONIC" in store: return "central"
        if "BWW" in store: return "east"
        if "ARG" in store: return "west"
        return "unknown"

    def get_location_by_ip(self, ip: str) -> Optional[FortiGateLocation]:
        for loc in self.locations.values():
            if loc.ip_address == ip:
                return loc
        return None

    def get_inventory_summary(self) -> Dict[str, Any]:
        brands = {}
        for loc in self.locations.values():
            if loc.brand not in brands:
                brands[loc.brand] = {"count": 0, "regions": set()}
            brands[loc.brand]["count"] += 1
            if loc.region:
                brands[loc.brand]["regions"].add(loc.region)
        
        # Serialize sets
        for b in brands.values():
            b["regions"] = list(b["regions"])

        return {
            "total_locations": len(self.locations),
            "brands": brands
        }

_svc = None
def get_fortigate_inventory_service() -> FortiGateInventoryService:
    global _svc
    if _svc is None:
        _svc = FortiGateInventoryService()
    return _svc
