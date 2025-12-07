"""
Restaurant Device Service (Enhanced)
Identifies restaurant technology devices based on MAC addresses, hostnames, and other characteristics.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class RestaurantDeviceService:
    def __init__(self):
        # Restaurant technology device patterns
        self.patterns = {
            "pos_terminal": {
                "hostnames": [
                    r"pos\d*", r"terminal\d*", r"register\d*", r"till\d*",
                    r"cashier\d*", r"checkout\d*", r"payment\d*",
                    r"square.*", r"clover.*", r"toast.*", r"lightspeed.*", r"revel.*",
                ],
                "manufacturers": [
                    "Square", "Clover", "Toast", "Lightspeed", "Revel",
                    "TouchBistro", "Shopify", "NCR", "Ingenico", "Verifone", "PAX Technology",
                ],
                "device_type": "Point of Sale Terminal",
            },
            "kitchen_display": {
                "hostnames": [
                    r"kds\d*", r"kitchen.*display\d*", r"expo\d*", r"prep\d*",
                    r"grill\d*", r"fryer\d*", r"salad\d*", r"hot.*line\d*",
                ],
                "manufacturers": [
                    "QSR Automations", "Fresh KDS", "Revel", "Toast", "Kitchen Display",
                ],
                "device_type": "Kitchen Display System",
            },
            "digital_menu": {
                "hostnames": [
                    r"menu.*board\d*", r"digital.*menu\d*", r"signage\d*",
                    r"display.*board\d*", r"menu.*screen\d*", r"drive.*thru.*menu\d*",
                ],
                "manufacturers": [
                    "Samsung", "LG", "BrightSign", "Scala", "Four Winds Interactive",
                ],
                "device_type": "Digital Menu Board",
            },
            "kiosk": {
                "hostnames": [
                    r"kiosk\d*", r"self.*order\d*", r"order.*station\d*",
                    r"self.*service\d*", r"customer.*kiosk\d*",
                ],
                "manufacturers": [
                    "Olea Kiosks", "KIOSK Information Systems", "Meridian Kiosks", "Advanced Kiosks",
                ],
                "device_type": "Self-Service Kiosk",
            },
            "drive_thru": {
                "hostnames": [
                    r"drive.*thru\d*", r"dt.*\d*", r"order.*taking\d*",
                    r"speaker.*box\d*", r"timer.*display\d*",
                ],
                "manufacturers": ["HME", "CE Electronics", "Delphi Display Systems"],
                "device_type": "Drive-Thru Equipment",
            },
             "tablet_pos": {
                "hostnames": [
                    r"ipad.*pos\d*", r"tablet.*pos\d*", r"mobile.*pos\d*",
                    r"server.*tablet\d*", r"handheld\d*",
                ],
                "manufacturers": ["Apple", "Samsung", "Microsoft", "Zebra Technologies"],
                "device_type": "Mobile POS Device",
            },
             "receipt_printer": {
                "hostnames": [
                    r"printer\d*", r"receipt.*printer\d*", r"thermal.*printer\d*",
                    r"epson.*printer\d*", r"star.*printer\d*",
                ],
                "manufacturers": ["Epson", "Star Micronics", "Zebra", "Bixolon"],
                "device_type": "Receipt Printer",
            },
        }

        # Enhanced OUI database for restaurant technology
        self.tech_oui = {
            "00:1B:21": "Square Inc.",
            "00:50:C2": "Clover Network",
            "00:0C:29": "Toast Inc.",
            "00:15:5D": "NCR Corporation",
            "00:1E:C9": "Ingenico",
            "00:0F:EC": "Verifone",
            "00:1C:7C": "PAX Technology",
            "00:26:5A": "Epson",
            "00:11:62": "Star Micronics",
            "00:07:80": "APG Cash Drawer",
            "00:1F:12": "BrightSign",
            "3C:18:A0": "Microsoft Corporation",
            "00:50:F2": "Microsoft Corporation",
            "28:18:78": "Apple Inc.",
            "00:23:DF": "Apple Inc.",
            "00:25:00": "Apple Inc.",
        }

    def classify_device(self, hostname: str = "", manufacturer: str = "", mac: str = "", ip: str = "") -> Tuple[str, str, float]:
        hostname = hostname.lower() if hostname else ""
        manufacturer = manufacturer if manufacturer else ""
        
        best_match = None
        best_confidence = 0.0
        best_category = "Unknown Device"

        for category, patterns in self.patterns.items():
            confidence = 0.0
            
            # Hostname check
            for pattern in patterns["hostnames"]:
                if re.search(pattern, hostname, re.IGNORECASE):
                    confidence += 0.8
                    break
            
            # Manufacturer check
            for mfg in patterns["manufacturers"]:
                if mfg.lower() in manufacturer.lower():
                    confidence += 0.6
                    break
                    
            # OUI check
            if mac and len(mac) >= 8:
                oui = mac[:8].upper()
                if oui in self.tech_oui:
                    confidence += 0.5

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = patterns["device_type"]
                best_category = category

        # Fallback OUI only
        if best_confidence == 0.0 and mac:
            oui = mac[:8].upper() if len(mac) >= 8 else ""
            if oui in self.tech_oui:
                return "Restaurant Technology Device", "restaurant_tech", 0.4

        if best_confidence < 0.3:
            return "Network Device", "generic", 0.1

        return best_match or "Restaurant Technology Device", best_category, best_confidence

    def get_recommendations(self, category: str) -> Dict[str, str]:
        recs = {
            "pos_terminal": {"security": "High", "monitoring": "Critical", "backup": "Essential"},
            "kitchen_display": {"security": "Medium", "monitoring": "Important", "backup": "Moderate"},
            "payment_device": {"security": "Critical", "monitoring": "Critical", "backup": "Essential"},
            "kiosk": {"security": "High", "monitoring": "Critical", "backup": "Essential"},
        }
        return recs.get(category, {"security": "Standard", "monitoring": "Standard", "backup": "Standard"})

    def enhance_device_info(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance device dict with classification and recommendations."""
        enhanced = device_info.copy()
        
        hostname = enhanced.get("device_name", "")
        manufacturer = enhanced.get("manufacturer", "")
        mac = enhanced.get("device_mac", "")
        ip = enhanced.get("device_ip", "")

        dtype, category, conf = self.classify_device(hostname, manufacturer, mac, ip)
        recs = self.get_recommendations(category)

        enhanced.update({
            "restaurant_device_type": dtype,
            "restaurant_category": category,
            "classification_confidence": conf,
            "security_level": recs["security"],
            "monitoring_priority": recs["monitoring"],
            "is_restaurant_tech": conf > 0.3
        })
        return enhanced

_svc = None
def get_restaurant_device_service() -> RestaurantDeviceService:
    global _svc
    if _svc is None:
        _svc = RestaurantDeviceService()
    return _svc
