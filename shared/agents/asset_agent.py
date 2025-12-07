"""
Asset Agent
Responsible for managing visualization assets, including:
1. Extracting icons from Visio VSS files.
2. Matching devices to icons/models based on MAC/OUI.
3. Converting SVG icons to 3D models.
"""

import logging
import json
import base64
import struct
import io
from pathlib import Path
from typing import List, Dict, Any, Optional

# Try imports for VSS processing
try:
    import olefile
    from PIL import Image
    VSS_SUPPORT = True
except ImportError:
    VSS_SUPPORT = False

from shared.network_utils.network_client import NetworkDevice
from shared.assets.icon_generator import IconGenerator

logger = logging.getLogger(__name__)

class AssetAgent:
    """
    Agent for handling visual assets:
    - VSS/SVG extractions
    - MAC -> Icon mappings
    - SVG -> 3D conversion
    - Dynamic Icon Generation
    """

    def __init__(self, asset_dir: str = "assets"):
        # Use the shared assets directory and Affinity pack
        self.asset_dir = Path(__file__).parent.parent / "assets"
        self.svg_dir = self.asset_dir / "icons/packs/affinity/svg/square"
        self.models_dir = self.asset_dir / "models"
        
        # Ensure directories exist
        self.svg_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.extracted_icons: List[Dict] = []
        
        # Mapping from vendor/type to SVG filename
        self.icon_map = {
            'fortinet': {
                'firewall': 'FortiGate.svg',
                'switch': 'FortiSwitch.svg',
                'ap': 'FortiAP.svg',
                'fortigate': 'FortiGate.svg',
                'fortiswitch': 'FortiSwitch.svg',
                'fortiap': 'FortiAP.svg'
            },
            'cisco': {
                'switch': 'switch_generic.svg',
                'router': 'router_generic.svg'
            },
             # Generic fallbacks
            'generic': {
                'firewall': 'FortiGate.svg', # Fallback to FortiGate style for now
                'switch': 'FortiSwitch.svg',
                'ap': 'FortiAP.svg',
                'client': 'Laptop.svg',
                'laptop': 'Laptop.svg',
                'phone': 'Smartphone.svg',
                'mobile': 'Smartphone.svg'
            }
        }

    def process_vss_file(self, vss_path: str) -> int:
        """
        Extract icons from a VSS file if libraries are available.
        Returns number of extracted icons.
        """
        if not VSS_SUPPORT:
            logger.warning("olefile or Pillow not installed. VSS extraction skipped.")
            return 0
            
        path = Path(vss_path)
        if not path.exists():
            logger.error(f"VSS file not found: {vss_path}")
            return 0
            
        logger.info(f"Extracting icons from {vss_path}")
        try:
            ole = olefile.OleFileIO(path)
            visio_data = ole.openstream(['VisioDocument']).read()
            ole.close()
            
            # Simple extraction strategy (looking for JPG/BMP headers)
            # This is a simplified version of the provided code
            count = 0
            # ... (Implementation of extraction logic would go here)
            # Placeholder for actual extraction
            logger.info("VSS extraction logic would run here.")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to process VSS: {e}")
            return 0

    def assign_assets_to_devices(self, devices: List[NetworkDevice]) -> List[NetworkDevice]:
        """
        Assign appropriate SVG and 3D model paths to devices.
        Generates missing SVGs on the fly.
        """
        for device in devices:
            # 1. Determine Device Type & Vendor
            vendor = (device.vendor or 'generic').lower()
            dtype = str(device.device_type).lower()
            
            # Normalize type
            if 'fortigate' in dtype: dtype = 'firewall'
            elif 'fortiswitch' in dtype or 'switch' in dtype: dtype = 'switch'
            elif 'fortiap' in dtype or 'ap' in dtype: dtype = 'ap'
            elif 'phone' in dtype: dtype = 'phone'
            elif 'server' in dtype: dtype = 'server'
            elif 'client' in dtype: dtype = 'client'
            
            # 2. Find best SVG
            icon_name = self._find_best_icon(vendor, dtype)
            svg_path = self.svg_dir / icon_name
            
            # 3. Generate if missing
            if not svg_path.exists():
                logger.info(f"Generating missing icon: {icon_name}")
                IconGenerator.generate_icon(dtype if vendor == 'generic' else f"{vendor}_{dtype}", svg_path)
            
            # 4. Assign paths
            device.metadata = device.metadata or {}
            device.metadata['icon_svg'] = str(svg_path.absolute())
            # 3D model is often derived from the SVG
            device.metadata['model_3d'] = str((self.models_dir / f"{dtype}.glb").absolute())
            
        return devices

    def _find_best_icon(self, vendor: str, device_type: str) -> str:
        """Find the best matching SVG filename"""
        # Try vendor specific
        if vendor in self.icon_map:
             if device_type in self.icon_map[vendor]:
                 return self.icon_map[vendor][device_type]
                 
        # Fallback to generic
        curr_map = self.icon_map['generic']
        for key in curr_map:
            if key in device_type:
                return curr_map[key]
        
        # Ultimate fallback
        return 'device_unknown.svg'

    def generate_3d_models(self):
        """
        Convert assigned SVGs to 3D models.
        """
        # Feature from svg_to_3d.py could be integrated here
        logger.info("Generating 3D models from SVGs...")
        pass
