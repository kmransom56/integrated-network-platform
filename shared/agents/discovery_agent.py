import logging
from typing import List, Dict, Any, Optional
from shared.device_handling.device_collector import UnifiedDeviceCollector
from shared.network_utils.network_client import NetworkDevice, DeviceType
from shared.network_utils.fortigate_monitor import FortiGateMonitor

logger = logging.getLogger(__name__)

class DiscoveryAgent:
    """
    Agent responsible for network discovery tasks:
    1. connecting to FortiGate (and other sources)
    2. discovering infrastructure (switches, APs)
    3. discovering endpoints
    """

    def __init__(self, auth_manager=None):
        self.collector = UnifiedDeviceCollector(auth_manager)
        self.devices: List[NetworkDevice] = []

    def connect_and_discover(self, config: Dict[str, Any], deep_scan: bool = True) -> List[NetworkDevice]:
        """
        Connect to configured sources and discover all devices.
        
        Args:
            config: Dictionary containing credentials/hosts for:
                    - fortigate: {host, username, password, token, ca_path}
                    - meraki: {api_key}
                    - fortimanager: {host, username, password}
            deep_scan: If True, uses FortiGateMonitor for advanced metrics (CPU, Memory, etc.)
        
        Returns:
            List of discovered NetworkDevice objects
        """
        logger.info("DiscoveryAgent starting discovery...")
        self.devices = []

        # 1. FortiGate Discovery
        if config.get('fortigate'):
            fg = config['fortigate']
            host = fg.get('host')
            logger.info(f"Discovering FortiGate at {host}...")
            
            # Base collection
            fg_devices = self.collector.collect_from_fortigate(
                host=fg.get('host'),
                username=fg.get('username'),
                password=fg.get('password'),
                token=fg.get('token')
            )
            
            # Deep Scan Enrichment
            if deep_scan and fg.get('token'): # Monitor requires token
                try:
                    # FortiGateMonitor expects ca_bundle to be None, bool, or str
                    # Handle the case where ca_path might be missing or None
                    ca_bundle = fg.get('ca_path')
                    
                    monitor = FortiGateMonitor(
                        host=host,
                        token=fg.get('token'),
                        ca_bundle=ca_bundle
                    )
                    logger.info("Performing deep scan with FortiGateMonitor...")
                    system_status = monitor.system_status()
                    
                    # Enrich the Gateway Node
                    for dev in fg_devices:
                        if dev.device_type == DeviceType.FORTIGATE:
                            dev.metadata = dev.metadata or {}
                            # Check for error dict in system_status results
                            if isinstance(system_status, dict) and not system_status.get('error'): 
                                dev.metadata['system_status'] = system_status
                                dev.metadata['cpu'] = monitor.cpu()
                                dev.metadata['memory'] = monitor.memory()
                                dev.metadata['sessions'] = monitor.sessions()
                                logger.info(f"Enriched {dev.name} with deep metrics")
                            
                except Exception as e:
                    logger.warning(f"Deep scan failed: {e}")

            self.devices.extend(fg_devices)

        # 2. Meraki Discovery
        if config.get('meraki'):
            mk = config['meraki']
            logger.info("Discovering Meraki devices...")
            mk_devices = self.collector.collect_from_meraki(
                api_key=mk.get('api_key'),
                org_id=mk.get('org_id')
            )
            self.devices.extend(mk_devices)

        # 3. FortiManager Discovery
        if config.get('fortimanager'):
            fm = config['fortimanager']
            logger.info(f"Discovering FortiManager at {fm.get('host')}...")
            fm_devices = self.collector.collect_from_fortimanager(
                host=fm.get('host'),
                username=fm.get('username'),
                password=fm.get('password')
            )
            self.devices.extend(fm_devices)

        logger.info(f"Discovery complete. Found {len(self.devices)} total devices.")
        return self.devices

    def get_infrastructure_devices(self) -> List[NetworkDevice]:
        """Return only infrastructure devices (Firewalls, Switches, APs)"""
        infra_types = [
            DeviceType.FORTIGATE, DeviceType.FORTISWITCH, DeviceType.FORTIAP,
            DeviceType.MERAKI_DEVICE, DeviceType.MERAKI_SWITCH, DeviceType.MERAKI_AP
        ]
        return [d for d in self.devices if d.device_type in infra_types]

    def get_client_devices(self) -> List[NetworkDevice]:
        """Return only client/endpoint devices"""
        return [d for d in self.devices if d.device_type == DeviceType.CLIENT]
