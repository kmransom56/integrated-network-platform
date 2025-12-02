"""
Device Classifier
Combines device classification from both applications
"""

from typing import Dict, List, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class DeviceClassifier:
    """
    Device classifier combining classification logic from:
    - network_map_3d device classification
    - enhanced-network-api-corporate device categorization
    """

    def __init__(self):
        self.classification_rules = self._load_default_rules()

    def _load_default_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load default classification rules"""
        return {
            # Network Infrastructure
            'core_router': {
                'keywords': ['router', 'core', 'gateway', 'fortigate', 'mx'],
                'vendors': ['cisco', 'fortinet', 'meraki', 'juniper'],
                'capabilities': ['routing', 'firewall', 'vpn'],
                'layer': 'core',
                'priority': 10
            },
            'distribution_switch': {
                'keywords': ['distribution', 'switch', 'fortiswitch', 'ms'],
                'vendors': ['cisco', 'fortinet', 'meraki'],
                'capabilities': ['switching', 'vlan', 'poe'],
                'layer': 'distribution',
                'priority': 8
            },
            'access_switch': {
                'keywords': ['access', 'switch', 'edge'],
                'vendors': ['cisco', 'fortinet', 'meraki'],
                'capabilities': ['switching', 'poe'],
                'layer': 'access',
                'priority': 6
            },
            'wireless_ap': {
                'keywords': ['ap', 'access_point', 'fortiap', 'mr', 'wireless'],
                'vendors': ['cisco', 'fortinet', 'meraki', 'aruba'],
                'capabilities': ['wifi', 'wlan'],
                'layer': 'access',
                'priority': 7
            },

            # End Devices
            'workstation': {
                'keywords': ['workstation', 'desktop', 'laptop', 'pc'],
                'capabilities': ['computing'],
                'layer': 'endpoint',
                'priority': 3
            },
            'mobile_device': {
                'keywords': ['mobile', 'phone', 'tablet', 'iphone', 'android'],
                'capabilities': ['mobile', 'computing'],
                'layer': 'endpoint',
                'priority': 3
            },
            'iot_device': {
                'keywords': ['iot', 'sensor', 'camera', 'printer', 'iot_device'],
                'capabilities': ['iot', 'sensing'],
                'layer': 'endpoint',
                'priority': 2
            },

            # Network Services
            'server': {
                'keywords': ['server', 'vm', 'virtual_machine', 'hypervisor'],
                'capabilities': ['computing', 'serving'],
                'layer': 'service',
                'priority': 5
            },
            'network_service': {
                'keywords': ['dhcp', 'dns', 'ntp', 'syslog'],
                'capabilities': ['service'],
                'layer': 'service',
                'priority': 4
            }
        }

    def classify_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a single device"""
        device_copy = device.copy()

        # Get classification scores for all categories
        scores = {}
        for category, rules in self.classification_rules.items():
            score = self._calculate_classification_score(device, rules)
            if score > 0:
                scores[category] = score

        # Select best classification
        if scores:
            best_category = max(scores, key=scores.get)
            best_score = scores[best_category]
            rules = self.classification_rules[best_category]

            device_copy.update({
                'device_category': best_category,
                'classification_score': best_score,
                'network_layer': rules['layer'],
                'expected_capabilities': rules['capabilities'],
                'classification_confidence': min(best_score / 10.0, 1.0)  # Normalize to 0-1
            })

            # Add inferred properties
            device_copy.update(self._infer_device_properties(device, rules))
        else:
            # Default classification
            device_copy.update({
                'device_category': 'unknown',
                'classification_score': 0,
                'network_layer': 'unknown',
                'expected_capabilities': [],
                'classification_confidence': 0.0
            })

        return device_copy

    def _calculate_classification_score(self, device: Dict[str, Any], rules: Dict[str, Any]) -> float:
        """Calculate how well a device matches classification rules"""
        score = 0.0

        # Keyword matching in name and model
        name_text = (device.get('name', '') + ' ' + device.get('model', '')).lower()
        keywords = rules.get('keywords', [])

        for keyword in keywords:
            if keyword.lower() in name_text:
                score += 2.0  # Strong keyword match

        # Vendor matching
        device_vendor = device.get('vendor', '').lower()
        rule_vendors = [v.lower() for v in rules.get('vendors', [])]

        if device_vendor in rule_vendors:
            score += 3.0  # Vendor match is very strong

        # Capability matching
        device_caps = [c.lower() for c in device.get('capabilities', [])]
        rule_caps = [c.lower() for c in rules.get('capabilities', [])]

        cap_matches = len(set(device_caps) & set(rule_caps))
        score += cap_matches * 1.5

        # MAC address patterns (for device type hints)
        mac = device.get('mac_address') or device.get('mac', '')
        if mac:
            score += self._score_mac_patterns(mac, rules)

        # Model-specific patterns
        model = device.get('model', '').lower()
        score += self._score_model_patterns(model, rules)

        return score

    def _score_mac_patterns(self, mac: str, rules: Dict[str, Any]) -> float:
        """Score MAC address patterns"""
        mac = mac.upper().replace(':', '').replace('-', '')

        # Known vendor OUIs that help with classification
        category_ouis = {
            'core_router': ['00090F'],  # Fortinet
            'wireless_ap': ['00090F'],  # Fortinet APs
            'workstation': ['000C29', '005056', '080027'],  # VMware, VirtualBox
        }

        category = None
        for cat, ouis in category_ouis.items():
            if any(mac.startswith(oui) for oui in ouis):
                category = cat
                break

        if category and category in str(rules.get('keywords', [])):
            return 2.0

        return 0.0

    def _score_model_patterns(self, model: str, rules: Dict[str, Any]) -> float:
        """Score model name patterns"""
        score = 0.0

        # Model number patterns
        if re.search(r'\d+', model):  # Contains numbers
            score += 0.5

        # Specific model patterns
        model_patterns = {
            'core_router': [r'fortigate', r'mx\d+', r'asa\d+'],
            'wireless_ap': [r'fortiap', r'mr\d+', r'ap\d+'],
            'access_switch': [r'fortiswitch', r'ms\d+', r'sg\d+']
        }

        for category, patterns in model_patterns.items():
            if category in str(rules.get('keywords', [])):
                for pattern in patterns:
                    if re.search(pattern, model, re.IGNORECASE):
                        score += 1.5

        return score

    def _infer_device_properties(self, device: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Infer additional device properties based on classification"""
        inferred = {}

        # Infer management IP if not present
        if not device.get('management_ip') and device.get('ip_address'):
            inferred['management_ip'] = device['ip_address']

        # Infer typical port counts
        layer = rules.get('layer')
        if layer == 'access':
            inferred['typical_ports'] = '24-48'
        elif layer == 'distribution':
            inferred['typical_ports'] = '24-96'
        elif layer == 'core':
            inferred['typical_ports'] = '4-16'

        # Infer power requirements
        category = device.get('device_category', '')
        if 'switch' in category:
            inferred['power_typical'] = '100-500W'
        elif 'router' in category:
            inferred['power_typical'] = '50-200W'
        elif 'ap' in category:
            inferred['power_typical'] = '10-30W'

        return inferred

    def classify_devices_batch(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify multiple devices"""
        classified = []

        for device in devices:
            classified_device = self.classify_device(device)
            classified.append(classified_device)

        logger.info(f"Classified {len(classified)} devices")
        return classified

    def get_category_stats(self, devices: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics on device categories"""
        stats = {}
        for device in devices:
            category = device.get('device_category', 'unknown')
            stats[category] = stats.get(category, 0) + 1

        return stats

    def validate_classification(self, device: Dict[str, Any]) -> List[str]:
        """Validate device classification"""
        warnings = []

        # Check for conflicting classifications
        capabilities = device.get('capabilities', [])
        category = device.get('device_category', '')

        # Example validation rules
        if category == 'wireless_ap' and 'routing' in capabilities:
            warnings.append("Wireless AP should not have routing capabilities")

        if category == 'workstation' and 'poe' in capabilities:
            warnings.append("Workstation should not have PoE capabilities")

        return warnings