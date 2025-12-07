"""
Meraki Switch Integration Service

Handles Meraki switch discovery for BWW and Arby's locations.
"""

import logging
import requests
import os
import time
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class MerakiService:
    """Service for integrating with Meraki Dashboard API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MERAKI_API_KEY")
        self.base_url = "https://api.meraki.com/api/v1"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                "X-Cisco-Meraki-API-Key": self.api_key,
                "Content-Type": "application/json"
            })
        
        self.request_delay = 0.2
        self.last_request_time = 0

    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Any:
        # Rate limiting
        current_time = time.time()
        if (current_time - self.last_request_time) < self.request_delay:
            time.sleep(self.request_delay - (current_time - self.last_request_time))
            
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == "GET":
                resp = self.session.get(url)
            else:
                resp = self.session.request(method, url, json=data)
            
            self.last_request_time = time.time()
            
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                time.sleep(1)
                return self._make_request(endpoint, method, data)
            else:
                return {"error": f"API {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def get_organizations(self):
        return self._make_request("organizations")

    def get_organization_networks(self, org_id: str):
        return self._make_request(f"organizations/{org_id}/networks")

    def get_network_devices(self, network_id: str):
        return self._make_request(f"networks/{network_id}/devices")

# Global
_meraki_service = None
def get_meraki_service() -> MerakiService:
    global _meraki_service
    if _meraki_service is None:
        _meraki_service = MerakiService()
    return _meraki_service
