"""
Multi-Tenant Organization Service

Manages enterprise-scale deployments across multiple restaurant brands:
- Sonic Drive-In: 3,500 locations (FortiGate + FortiSwitch + FortiAP)
- Buffalo Wild Wings: 900 locations (FortiGate + Meraki + FortiAP)  
- Arby's: 1,500 locations (FortiGate + Meraki + FortiAP)
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

class RestaurantBrand(Enum):
    SONIC = "sonic"
    BWW = "bww"
    ARBYS = "arbys"

class InfrastructureType(Enum):
    FORTINET_FULL = "fortinet_full"      # FortiGate + FortiSwitch + FortiAP (Sonic)
    FORTINET_MERAKI = "fortinet_meraki"  # FortiGate + Meraki + FortiAP (BWW/Arby's)
    MIXED = "mixed"                      # Mixed infrastructure

class LocationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

@dataclass
class Organization:
    id: str
    name: str
    brand: RestaurantBrand
    region: str
    location_count: int
    infrastructure_type: InfrastructureType
    created_at: datetime

@dataclass
class Location:
    id: str
    organization_id: str
    store_number: str
    name: str
    address: str
    city: str
    state: str
    country: str = "USA"
    timezone: str = "America/Chicago"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: LocationStatus = LocationStatus.ACTIVE
    infrastructure_type: InfrastructureType = InfrastructureType.FORTINET_FULL
    fortigate_ip: Optional[str] = None
    fortigate_model: Optional[str] = None
    switch_count: int = 0
    ap_count: int = 0
    last_discovered: Optional[datetime] = None

class OrganizationService:
    """Enterprise organization management service"""
    
    def __init__(self):
        self.organizations = self._load_organizations()
        self.locations = self._load_locations()
        self.rate_limits = self._setup_rate_limits()
        
    def _load_organizations(self) -> Dict[str, Organization]:
        """Load organization configuration"""
        return {
            "sonic": Organization(
                id="sonic",
                name="Sonic Drive-In",
                brand=RestaurantBrand.SONIC,
                region="National",
                location_count=3500,
                infrastructure_type=InfrastructureType.FORTINET_FULL,
                created_at=datetime(2020, 1, 1)
            ),
            "bww": Organization(
                id="bww", 
                name="Buffalo Wild Wings",
                brand=RestaurantBrand.BWW,
                region="National",
                location_count=900,
                infrastructure_type=InfrastructureType.FORTINET_MERAKI,
                created_at=datetime(2019, 1, 1)
            ),
            "arbys": Organization(
                id="arbys",
                name="Arby's Restaurant Group",
                brand=RestaurantBrand.ARBYS,
                region="National", 
                location_count=1500,
                infrastructure_type=InfrastructureType.FORTINET_MERAKI,
                created_at=datetime(2018, 1, 1)
            )
        }
    
    def _load_locations(self) -> Dict[str, List[Location]]:
        """Load sample location data (in production, this would come from database)"""
        locations = {}
        
        # Sample Sonic locations
        locations["sonic"] = [
            Location(
                id="sonic_001",
                organization_id="sonic",
                store_number="0001",
                name="Sonic Drive-In #0001",
                address="123 Main St",
                city="Oklahoma City",
                state="OK",
                infrastructure_type=InfrastructureType.FORTINET_FULL,
                fortigate_ip="192.168.1.1",
                fortigate_model="FG-100F",
                switch_count=2,
                ap_count=4
            )
        ]
        
        # Sample BWW locations  
        locations["bww"] = [
            Location(
                id="bww_001",
                organization_id="bww",
                store_number="BWW001",
                name="Buffalo Wild Wings #001",
                address="456 Sports Ave",
                city="Atlanta",
                state="GA",
                infrastructure_type=InfrastructureType.FORTINET_MERAKI,
                fortigate_ip="192.168.1.1",
                fortigate_model="FG-200F", 
                switch_count=1,  # Meraki switches
                ap_count=6
            )
        ]
        
        # Sample Arby's locations
        locations["arbys"] = [
            Location(
                id="arbys_001",
                organization_id="arbys",
                store_number="ARB001",
                name="Arby's Restaurant #001",
                address="789 Beef Blvd",
                city="Atlanta",
                state="GA",
                infrastructure_type=InfrastructureType.FORTINET_MERAKI,
                fortigate_ip="192.168.1.1",
                fortigate_model="FG-100F",
                switch_count=1,  # Meraki switches
                ap_count=3
            )
        ]
        
        return locations
    
    def _setup_rate_limits(self) -> Dict[str, Dict[str, int]]:
        """Configure API rate limits per organization"""
        return {
            "sonic": {
                "requests_per_second": 100,
                "concurrent_discoveries": 50,
                "max_locations_per_batch": 25
            },
            "bww": {
                "requests_per_second": 25,
                "concurrent_discoveries": 15, 
                "max_locations_per_batch": 10
            },
            "arbys": {
                "requests_per_second": 40,
                "concurrent_discoveries": 25,
                "max_locations_per_batch": 15
            }
        }
    
    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        return self.organizations.get(org_id)
    
    def get_all_organizations(self) -> List[Organization]:
        """Get all organizations"""
        return list(self.organizations.values())
    
    def get_organization_locations(self, org_id: str, limit: int = 100, offset: int = 0) -> List[Location]:
        """Get locations for an organization with pagination"""
        org_locations = self.locations.get(org_id, [])
        return org_locations[offset:offset + limit]

    def get_enterprise_summary(self) -> Dict[str, Any]:
        """Get enterprise-wide summary statistics"""
        total_locations = sum(org.location_count for org in self.organizations.values())
        
        # Estimated device counts based on typical restaurant deployments
        device_estimates = {
            "fortigates": total_locations,  # 1 per location
            "fortiswitches": 3500,  # Sonic only
            "meraki_switches": 2400,  # BWW + Arby's
            "fortiaps": total_locations * 2,  # Average 2 per location
            "restaurant_devices": total_locations * 60,  # Average 60 restaurant devices per location
            "total_managed_devices": total_locations * 65  # Approximate total
        }
        
        return {
            "total_organizations": len(self.organizations),
            "total_locations": total_locations,
            "organizations": {
                org.brand.value: {
                    "name": org.name,
                    "locations": org.location_count,
                    "infrastructure": org.infrastructure_type.value
                }
                for org in self.organizations.values()
            },
            "device_estimates": device_estimates,
            "infrastructure_breakdown": {
                "fortinet_full": 3500,  # Sonic
                "fortinet_meraki": 2400   # BWW + Arby's
            }
        }

# Global service instance
_organization_service = None

def get_organization_service() -> OrganizationService:
    """Get the global organization service instance"""
    global _organization_service
    if _organization_service is None:
        _organization_service = OrganizationService()
    return _organization_service
