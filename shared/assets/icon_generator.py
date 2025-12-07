from pathlib import Path
from typing import Optional

class IconGenerator:
    """Generates realistic SVG icons for various device types."""

    @staticmethod
    def create_fortigate_svg(width=200, height=100) -> str:
        """Create a realistic FortiGate firewall SVG icon."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <defs>
        <linearGradient id="fortigateBody" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#4a5568;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#2d3748;stop-opacity:1" />
        </linearGradient>
        <linearGradient id="frontPanel" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#718096;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#4a5568;stop-opacity:1" />
        </linearGradient>
        <linearGradient id="fortinetLogo" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#ff6b6b;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#ee5a24;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect x="10" y="20" width="{width-20}" height="{height-40}" rx="5" ry="5" fill="url(#fortigateBody)" stroke="#1a202c" stroke-width="2"/>
    <rect x="15" y="25" width="{width-30}" height="{height-50}" rx="3" ry="3" fill="url(#frontPanel)" stroke="#2d3748" stroke-width="1"/>
    <circle cx="30" cy="45" r="3" fill="#48bb78" stroke="#2f855a" stroke-width="1"/>
    <circle cx="45" cy="45" r="3" fill="#4299e1" stroke="#2b6cb1" stroke-width="1"/>
    <circle cx="60" cy="45" r="3" fill="#ed8936" stroke="#dd6b20" stroke-width="1"/>
    <g id="ports">
        <rect x="20" y="65" width="8" height="4" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="30" y="65" width="8" height="4" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="40" y="65" width="8" height="4" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="50" y="65" width="8" height="4" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="60" y="65" width="8" height="4" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="75" y="66" width="6" height="2" fill="#4a5568" stroke="#2d3748" stroke-width="0.5"/>
    </g>
    <g transform="translate({width-40}, 35)">
        <rect x="0" y="0" width="25" height="15" rx="2" fill="url(#fortinetLogo)"/>
        <text x="12.5" y="10" text-anchor="middle" font-family="Arial, sans-serif" font-size="8" font-weight="bold" fill="white">FG</text>
    </g>
    <text x="{width//2}" y="{height-5}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#e2e8f0">FortiGate</text>
</svg>'''

    @staticmethod
    def create_fortiswitch_svg(width=200, height=60) -> str:
        """Create a realistic FortiSwitch SVG icon."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="switchBody" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#48bb78;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#2f855a;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect x="10" y="15" width="{width-20}" height="{height-30}" rx="3" ry="3" fill="url(#switchBody)" stroke="#2f855a" stroke-width="2"/>
    <g id="switchPorts">
        <rect x="20" y="25" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="28" y="25" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="36" y="25" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="44" y="25" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="52" y="25" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="60" y="25" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="68" y="25" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="76" y="25" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="20" y="32" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="28" y="32" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="36" y="32" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="44" y="32" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="52" y="32" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="60" y="32" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="68" y="32" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
        <rect x="76" y="32" width="6" height="3" fill="#2d3748" stroke="#1a202c" stroke-width="0.5"/>
    </g>
    <circle cx="100" y="30" r="2" fill="#48bb78" stroke="#2f855a" stroke-width="0.5"/>
    <circle cx="108" y="30" r="2" fill="#4299e1" stroke="#2b6cb1" stroke-width="0.5"/>
    <text x="{width//2}" y="{height-5}" text-anchor="middle" font-family="Arial, sans-serif" font-size="9" fill="#e2e8f0">FortiSwitch</text>
</svg>'''

    @staticmethod
    def create_fortiap_svg(width=80, height=80) -> str:
        """Create a realistic FortiAP SVG icon."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="apBody" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#f6ad55;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#ed8936;stop-opacity:1" />
        </linearGradient>
        <pattern id="radioWaves" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
            <circle cx="20" cy="20" r="5" fill="none" stroke="#4299e1" stroke-width="1" opacity="0.6"/>
            <circle cx="20" cy="20" r="10" fill="none" stroke="#4299e1" stroke-width="1" opacity="0.4"/>
            <circle cx="20" cy="20" r="15" fill="none" stroke="#4299e1" stroke-width="1" opacity="0.2"/>
        </pattern>
    </defs>
    <ellipse cx="{width//2}" cy="{height-20}" rx="25" ry="8" fill="url(#apBody)" stroke="#dd6b20" stroke-width="2"/>
    <rect x="{width//2-3}" y="10" width="6" height="{height-30}" fill="#4a5568" stroke="#2d3748" stroke-width="1"/>
    <rect x="{width//2-10}" y="5" width="20" height="8" rx="2" fill="#2d3748" stroke="#1a202c" stroke-width="1"/>
    <circle cx="{width//2}" cy="{height-20}" r="15" fill="url(#radioWaves)" opacity="0.7"/>
    <circle cx="{width//2}" cy="{height-20}" r="3" fill="#48bb78" stroke="#2f855a" stroke-width="1"/>
    <line x1="{width//2-15}" y1="{height-25}" x2="{width//2-20}" y2="{height-35}" stroke="#4a5568" stroke-width="2" stroke-linecap="round"/>
    <line x1="{width//2+15}" y1="{height-25}" x2="{width//2+20}" y2="{height-35}" stroke="#4a5568" stroke-width="2" stroke-linecap="round"/>
    <text x="{width//2}" y="{height-2}" text-anchor="middle" font-family="Arial, sans-serif" font-size="8" fill="#e2e8f0">FortiAP</text>
</svg>'''

    @staticmethod
    def create_client_svg(device_type="laptop", width=60, height=60) -> str:
        """Create a client device SVG icon."""
        if device_type == "laptop":
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="laptopBody" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#718096;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#4a5568;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect x="5" y="5" width="{width-10}" height="{height-20}" rx="2" fill="#1a202c" stroke="#2d3748" stroke-width="1"/>
    <rect x="8" y="8" width="{width-16}" height="{height-26}" fill="#4299e1" stroke="#2b6cb1" stroke-width="1"/>
    <rect x="2" y="{height-15}" width="{width-4}" height="10" rx="1" fill="url(#laptopBody)" stroke="#2d3748" stroke-width="1"/>
    <text x="{width//2}" y="{height-2}" text-anchor="middle" font-family="Arial, sans-serif" font-size="7" fill="#e2e8f0">Laptop</text>
</svg>'''
        elif device_type == "smartphone":
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="phoneBody" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#2d3748;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#1a202c;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect x="15" y="5" width="{width-30}" height="{height-10}" rx="5" fill="url(#phoneBody)" stroke="#1a202c" stroke-width="1"/>
    <rect x="18" y="10" width="{width-36}" height="{height-20}" rx="2" fill="#4299e1" stroke="#2b6cb1" stroke-width="1"/>
    <circle cx="{width//2}" cy="{height-8}" r="2" fill="#4a5568" stroke="#2d3748" stroke-width="1"/>
    <text x="{width//2}" y="{height-1}" text-anchor="middle" font-family="Arial, sans-serif" font-size="6" fill="#e2e8f0">Phone</text>
</svg>'''
        else:
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <rect x="10" y="10" width="{width-20}" height="{height-20}" rx="3" fill="#4a5568" stroke="#2d3748" stroke-width="2"/>
    <text x="{width//2}" y="{height//2}" text-anchor="middle" font-family="Arial, sans-serif" font-size="8" fill="#e2e8f0">Device</text>
</svg>'''

    @staticmethod
    def generate_icon(device_type: str, output_path: Path):
        """Generate and save an icon."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        device_type = device_type.lower()
        
        if "fortigate" in device_type or "firewall" in device_type:
            content = IconGenerator.create_fortigate_svg()
        elif "switch" in device_type:
            content = IconGenerator.create_fortiswitch_svg()
        elif "ap" in device_type or "access point" in device_type:
            content = IconGenerator.create_fortiap_svg()
        elif "phone" in device_type or "mobile" in device_type:
            content = IconGenerator.create_client_svg("smartphone")
        elif "laptop" in device_type or "pc" in device_type:
            content = IconGenerator.create_client_svg("laptop")
        else:
            content = IconGenerator.create_client_svg("generic")
            
        output_path.write_text(content, encoding='utf-8')
