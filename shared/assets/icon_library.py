"""
Icon Library
Manages icon assets for devices
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class IconLibrary:
    """Library for device icons used in network visualizations"""

    def __init__(self, icons_dir: Path):
        self.icons_dir = icons_dir
        self.registry_file = icons_dir / "registry.json"
        self.icons = {}
        self._load_registry()

    def _load_registry(self):
        """Load icon registry from file"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    self.icons = json.load(f)
                logger.info(f"Loaded {len(self.icons)} icons from registry")
            except Exception as e:
                logger.error(f"Failed to load icon registry: {e}")
                self.icons = {}
        else:
            self.icons = {}

    def _save_registry(self):
        """Save icon registry to file"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.icons, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save icon registry: {e}")

    def discover_icons(self) -> List[Dict[str, Any]]:
        """Discover all icons in the icons directory"""
        icons = []

        if not self.icons_dir.exists():
            return icons

        # Supported icon formats
        icon_extensions = {'.svg', '.png', '.jpg', '.jpeg', '.ico', '.gif'}

        for file_path in self.icons_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in icon_extensions:
                icon_info = self._analyze_icon_file(file_path)
                if icon_info:
                    icons.append(icon_info)

        return icons

    def _analyze_icon_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze an icon file"""
        try:
            stat = file_path.stat()

            icon_info = {
                'name': file_path.stem,
                'path': str(file_path),
                'format': file_path.suffix[1:].lower(),  # Remove the dot
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'relative_path': str(file_path.relative_to(self.icons_dir)),
                'device_types': self._infer_device_types(file_path),
                'vendor': self._infer_vendor(file_path)
            }

            # Add dimensions for raster formats (would need PIL/Pillow in real implementation)
            if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                icon_info['dimensions'] = self._get_image_dimensions(file_path)

            return icon_info

        except Exception as e:
            logger.warning(f"Failed to analyze icon {file_path}: {e}")
            return None

    def _get_image_dimensions(self, file_path: Path) -> Optional[Dict[str, int]]:
        """Get image dimensions (placeholder - would use PIL in real implementation)"""
        # In a real implementation, this would use PIL to get actual dimensions
        return {'width': 64, 'height': 64}  # Default placeholder

    def _infer_device_types(self, file_path: Path) -> List[str]:
        """Infer device types from filename"""
        name = file_path.stem.lower()
        device_types = []

        # Router/gateway detection
        if any(keyword in name for keyword in ['router', 'gateway', 'fortigate', 'mx']):
            device_types.append('router')

        # Switch detection
        if any(keyword in name for keyword in ['switch', 'fortiswitch', 'ms']):
            device_types.append('switch')

        # Access point detection
        if any(keyword in name for keyword in ['ap', 'access_point', 'fortiap', 'mr']):
            device_types.append('access_point')

        # Server detection
        if 'server' in name:
            device_types.append('server')

        # Generic device if no specific type found
        if not device_types:
            device_types.append('generic')

        return device_types

    def _infer_vendor(self, file_path: Path) -> Optional[str]:
        """Infer vendor from filename"""
        name = file_path.stem.lower()

        if 'fortinet' in name or 'forti' in name:
            return 'fortinet'
        elif 'cisco' in name or 'meraki' in name:
            return 'cisco'
        elif 'juniper' in name:
            return 'juniper'
        elif 'aruba' in name or 'hp' in name:
            return 'hp'
        else:
            return None

    def register_icon(self, file_path: Path) -> bool:
        """Register a new icon"""
        icon_info = self._analyze_icon_file(file_path)
        if icon_info:
            icon_id = file_path.stem
            self.icons[icon_id] = icon_info
            self._save_registry()
            logger.info(f"Registered icon: {icon_id}")
            return True
        return False

    def get_icon_for_device(self, device_type: str, vendor: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the best icon for a device type and vendor"""
        candidates = []

        for icon_id, icon_info in self.icons.items():
            # Check if icon supports this device type
            if device_type in icon_info.get('device_types', []):
                score = 1  # Base score for device type match

                # Bonus for vendor match
                if vendor and icon_info.get('vendor') == vendor:
                    score += 2

                # Bonus for exact name match
                if device_type.lower() in icon_id.lower():
                    score += 1

                # Prefer SVG over raster formats
                if icon_info.get('format') == 'svg':
                    score += 1

                candidates.append((score, icon_info))

        if candidates:
            # Return highest scoring icon
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]

        # Fallback to generic icon
        return self._get_generic_icon()

    def _get_generic_icon(self) -> Optional[Dict[str, Any]]:
        """Get a generic fallback icon"""
        for icon_id, icon_info in self.icons.items():
            if 'generic' in icon_info.get('device_types', []):
                return icon_info

        # If no generic icon, return any icon
        return next(iter(self.icons.values()), None) if self.icons else None

    def get_icons_by_vendor(self, vendor: str) -> List[Dict[str, Any]]:
        """Get all icons for a specific vendor"""
        return [icon for icon in self.icons.values() if icon.get('vendor') == vendor]

    def get_icons_by_type(self, device_type: str) -> List[Dict[str, Any]]:
        """Get all icons for a specific device type"""
        return [icon for icon in self.icons.values() if device_type in icon.get('device_types', [])]

    def remove_icon(self, icon_id: str) -> bool:
        """Remove an icon from the registry"""
        if icon_id in self.icons:
            del self.icons[icon_id]
            self._save_registry()
            logger.info(f"Removed icon: {icon_id}")
            return True
        return False

    def create_icon_variants(self, base_icon_path: Path, variants: List[str]) -> List[str]:
        """Create variants of an icon (placeholder for future implementation)"""
        # This would implement icon variant generation
        # For example: different colors, sizes, styles
        created = []
        for variant in variants:
            # Logic to create variant would go here
            created.append(f"{base_icon_path.stem}_{variant}{base_icon_path.suffix}")
        return created