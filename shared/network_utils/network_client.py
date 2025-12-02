"""
Unified Network Client
Combines FortiGate and Meraki API access from both applications
"""

import requests
import json
from enum import Enum
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    FORTIGATE = "fortigate"
    FORTISWITCH = "fortiswitch"
    FORTIAP = "fortiap"
    MERAKI_DEVICE = "meraki_device"
    MERAKI_SWITCH = "meraki_switch"
    MERAKI_AP = "meraki_ap"


@dataclass
class NetworkDevice:
    """Unified device representation"""
    id: str
    name: str
    device_type: DeviceType
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    status: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class NetworkClient:
    """
    Unified network client combining functionality from:
    - network_map_3d device_collector.py
    - enhanced-network-api-corporate device_collector.py
    """

    def __init__(self, fortigate_host: Optional[str] = None, fortigate_auth=None,
                 meraki_config=None, timeout: int = 30):
        self.fortigate_host = fortigate_host
        self.fortigate_auth = fortigate_auth
        self.meraki_config = meraki_config
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False  # Handle SSL certificates

    def get_connected_clients(self, device_type: DeviceType = DeviceType.FORTIGATE) -> List[NetworkDevice]:
        """Get connected clients from specified device type"""
        if device_type == DeviceType.FORTIGATE and self.fortigate_host:
            return self._get_fortigate_clients()
        elif device_type in [DeviceType.MERAKI_DEVICE, DeviceType.MERAKI_SWITCH, DeviceType.MERAKI_AP]:
            return self._get_meraki_clients()
        return []

    def _get_fortigate_clients(self) -> List[NetworkDevice]:
        """Get clients from FortiGate (from network_map_3d)"""
        if not self.fortigate_host:
            return []

        url = f'https://{self.fortigate_host}/api/v2/monitor/wifi/client'
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            clients = []
            for client_data in data.get('results', []):
                client = NetworkDevice(
                    id=client_data.get('mac', ''),
                    name=client_data.get('hostname', client_data.get('mac', 'Unknown')),
                    device_type=DeviceType.FORTIGATE,
                    mac_address=client_data.get('mac'),
                    ip_address=client_data.get('ip'),
                    status=client_data.get('status', 'unknown')
                )
                clients.append(client)
            return clients
        except Exception as e:
            logger.error(f"Failed to fetch FortiGate clients: {e}")
            return []

    def _get_meraki_clients(self) -> List[NetworkDevice]:
        """Get clients from Meraki (from enhanced-network-api-corporate)"""
        if not self.meraki_config or not hasattr(self.meraki_config, 'api_key'):
            return []

        # This would use the Meraki API integration from enhanced-network-api-corporate
        # For now, return empty list as we need to integrate the full Meraki client
        logger.info("Meraki client integration pending")
        return []

    def get_network_devices(self) -> List[NetworkDevice]:
        """Get all network devices from configured sources"""
        devices = []

        # Get FortiGate devices
        if self.fortigate_host:
            devices.extend(self._get_fortigate_devices())

        # Get Meraki devices
        if self.meraki_config:
            devices.extend(self._get_meraki_devices())

        return devices

    def _get_fortigate_devices(self) -> List[NetworkDevice]:
        """Get FortiGate managed devices"""
        devices = []

        # Get FortiSwitches
        switches = self._get_fortiswitches()
        devices.extend(switches)

        # Get FortiAPs
        aps = self._get_fortiaps()
        devices.extend(aps)

        return devices

    def _get_fortiswitches(self) -> List[NetworkDevice]:
        """Get FortiSwitch devices (from network_map_3d)"""
        if not self.fortigate_host:
            return []

        url = f'https://{self.fortigate_host}/api/v2/monitor/switch-controller/managed-switch'
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            switches = []
            for switch_data in data.get('results', []):
                switch = NetworkDevice(
                    id=switch_data.get('serial', ''),
                    name=switch_data.get('name', switch_data.get('serial', 'Unknown')),
                    device_type=DeviceType.FORTISWITCH,
                    ip_address=switch_data.get('ip'),
                    model=switch_data.get('model'),
                    serial=switch_data.get('serial'),
                    status=switch_data.get('status', 'unknown')
                )
                switches.append(switch)
            return switches
        except Exception as e:
            logger.error(f"Failed to fetch FortiSwitches: {e}")
            return []

    def _get_fortiaps(self) -> List[NetworkDevice]:
        """Get FortiAP devices (from network_map_3d)"""
        if not self.fortigate_host:
            return []

        url = f'https://{self.fortigate_host}/api/v2/monitor/wifi/managed_ap'
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            aps = []
            for ap_data in data.get('results', []):
                ap = NetworkDevice(
                    id=ap_data.get('serial', ''),
                    name=ap_data.get('name', ap_data.get('serial', 'Unknown')),
                    device_type=DeviceType.FORTIAP,
                    ip_address=ap_data.get('ip'),
                    model=ap_data.get('model'),
                    serial=ap_data.get('serial'),
                    status=ap_data.get('status', 'unknown')
                )
                aps.append(ap)
            return aps
        except Exception as e:
            logger.error(f"Failed to fetch FortiAPs: {e}")
            return []

    def _get_meraki_devices(self) -> List[NetworkDevice]:
        """Get Meraki devices (placeholder for integration)"""
        # This would integrate the Meraki API client from enhanced-network-api-corporate
        logger.info("Meraki device integration pending")
        return []

    def get_device_details(self, device_id: str, device_type: DeviceType) -> Optional[NetworkDevice]:
        """Get detailed information for a specific device"""
        devices = self.get_network_devices()
        for device in devices:
            if device.id == device_id and device.device_type == device_type:
                return device
        return None