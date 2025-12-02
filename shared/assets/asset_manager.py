"""
Asset Manager
Manages 3D models, icons, and other visualization assets
Combines asset handling from both applications
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
from .model_registry import ModelRegistry
from .icon_library import IconLibrary

logger = logging.getLogger(__name__)


class AssetManager:
    """
    Unified asset manager combining asset handling from:
    - network_map_3d assets/ directory
    - enhanced-network-api-corporate realistic_3d_models/ and extracted_icons/
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path("./assets")
        self.models_dir = self.base_dir / "models"
        self.icons_dir = self.base_dir / "icons"
        self.textures_dir = self.base_dir / "textures"
        self.exports_dir = self.base_dir / "exports"

        # Create directories
        for dir_path in [self.models_dir, self.icons_dir, self.textures_dir, self.exports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Initialize registries
        self.model_registry = ModelRegistry(self.models_dir)
        self.icon_library = IconLibrary(self.icons_dir)

    def discover_assets(self) -> Dict[str, Any]:
        """Discover all available assets"""
        models = self.model_registry.discover_models()
        icons = self.icon_library.discover_icons()

        return {
            'models': models,
            'icons': icons,
            'summary': {
                'total_models': len(models),
                'total_icons': len(icons),
                'models_by_format': self._count_by_format(models, 'format'),
                'icons_by_format': self._count_by_format(icons, 'format')
            }
        }

    def _count_by_format(self, assets: List[Dict[str, Any]], format_key: str) -> Dict[str, int]:
        """Count assets by format"""
        counts = {}
        for asset in assets:
            fmt = asset.get(format_key, 'unknown')
            counts[fmt] = counts.get(fmt, 0) + 1
        return counts

    def get_asset_for_device(self, device_type: str, vendor: str = None) -> Dict[str, Any]:
        """Get appropriate assets for a device type"""
        # Get 3D model
        model = self.model_registry.get_model_for_device(device_type, vendor)

        # Get icon
        icon = self.icon_library.get_icon_for_device(device_type, vendor)

        return {
            'model': model,
            'icon': icon,
            'device_type': device_type,
            'vendor': vendor
        }

    def import_assets_from_directory(self, source_dir: str, asset_type: str = "auto") -> Dict[str, Any]:
        """Import assets from a directory"""
        source_path = Path(source_dir)
        if not source_path.exists():
            return {'error': f'Source directory {source_dir} does not exist'}

        results = {
            'imported': [],
            'skipped': [],
            'errors': []
        }

        # Determine asset type if auto
        if asset_type == "auto":
            asset_type = self._detect_asset_type(source_path)

        # Import based on type
        if asset_type == "models":
            results = self._import_models(source_path)
        elif asset_type == "icons":
            results = self._import_icons(source_path)
        else:
            results['errors'].append(f'Unknown asset type: {asset_type}')

        return results

    def _detect_asset_type(self, directory: Path) -> str:
        """Detect asset type from directory contents"""
        extensions = []
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                extensions.append(file_path.suffix.lower())

        # Count extensions
        ext_counts = {}
        for ext in extensions:
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

        # Determine type based on most common extensions
        model_extensions = {'.glb', '.gltf', '.obj', '.fbx', '.dae'}
        icon_extensions = {'.svg', '.png', '.jpg', '.jpeg', '.ico'}

        model_count = sum(ext_counts.get(ext, 0) for ext in model_extensions)
        icon_count = sum(ext_counts.get(ext, 0) for ext in icon_extensions)

        if model_count > icon_count:
            return "models"
        elif icon_count > model_count:
            return "icons"
        else:
            return "mixed"

    def _import_models(self, source_dir: Path) -> Dict[str, Any]:
        """Import 3D models"""
        results = {'imported': [], 'skipped': [], 'errors': []}

        model_extensions = {'.glb', '.gltf', '.obj', '.fbx', '.dae', '.3ds'}

        for file_path in source_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in model_extensions:
                try:
                    # Determine destination subdirectory
                    subdir = self._get_model_subdirectory(file_path)

                    dest_dir = self.models_dir / subdir
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    dest_file = dest_dir / file_path.name

                    if dest_file.exists():
                        results['skipped'].append(str(file_path))
                        continue

                    shutil.copy2(file_path, dest_file)
                    results['imported'].append(str(dest_file))

                    # Register the model
                    self.model_registry.register_model(dest_file)

                except Exception as e:
                    results['errors'].append(f'{file_path}: {str(e)}')

        return results

    def _import_icons(self, source_dir: Path) -> Dict[str, Any]:
        """Import icons"""
        results = {'imported': [], 'skipped': [], 'errors': []}

        icon_extensions = {'.svg', '.png', '.jpg', '.jpeg', '.ico'}

        for file_path in source_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in icon_extensions:
                try:
                    # Determine destination subdirectory
                    subdir = self._get_icon_subdirectory(file_path)

                    dest_dir = self.icons_dir / subdir
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    dest_file = dest_dir / file_path.name

                    if dest_file.exists():
                        results['skipped'].append(str(file_path))
                        continue

                    shutil.copy2(file_path, dest_file)
                    results['imported'].append(str(dest_file))

                    # Register the icon
                    self.icon_library.register_icon(dest_file)

                except Exception as e:
                    results['errors'].append(f'{file_path}: {str(e)}')

        return results

    def _get_model_subdirectory(self, file_path: Path) -> str:
        """Determine subdirectory for model based on filename/path"""
        name = file_path.stem.lower()

        # Check for vendor keywords
        if 'fortinet' in name or 'forti' in name:
            return 'fortinet'
        elif 'cisco' in name or 'meraki' in name:
            return 'cisco'
        elif 'generic' in name or 'default' in name:
            return 'generic'
        else:
            return 'custom'

    def _get_icon_subdirectory(self, file_path: Path) -> str:
        """Determine subdirectory for icon"""
        name = file_path.stem.lower()

        # Check for device type keywords
        if 'switch' in name:
            return 'switches'
        elif 'router' in name or 'gateway' in name:
            return 'routers'
        elif 'ap' in name or 'access' in name:
            return 'access_points'
        elif 'server' in name:
            return 'servers'
        else:
            return 'devices'

    def export_asset_package(self, device_types: List[str], output_path: str) -> bool:
        """Export a package of assets for specific device types"""
        try:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            exported_assets = {
                'models': [],
                'icons': [],
                'manifest': {
                    'created': datetime.now().isoformat(),
                    'device_types': device_types
                }
            }

            # Collect assets for each device type
            for device_type in device_types:
                assets = self.get_asset_for_device(device_type)

                # Copy model if available
                if assets.get('model'):
                    model_info = assets['model']
                    src_path = Path(model_info['path'])
                    dest_path = output_dir / "models" / src_path.name
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dest_path)
                    exported_assets['models'].append(str(dest_path))

                # Copy icon if available
                if assets.get('icon'):
                    icon_info = assets['icon']
                    src_path = Path(icon_info['path'])
                    dest_path = output_dir / "icons" / src_path.name
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dest_path)
                    exported_assets['icons'].append(str(dest_path))

            # Write manifest
            manifest_path = output_dir / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(exported_assets['manifest'], f, indent=2)

            logger.info(f"Asset package exported to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Asset package export failed: {e}")
            return False

    def cleanup_unused_assets(self) -> Dict[str, Any]:
        """Clean up unused assets"""
        # This would implement logic to identify and remove unused assets
        # For now, return placeholder
        return {
            'removed': [],
            'kept': [],
            'message': 'Cleanup not yet implemented'
        }

    def get_asset_stats(self) -> Dict[str, Any]:
        """Get asset statistics"""
        discovery = self.discover_assets()
        summary = discovery['summary']

        # Calculate storage usage
        total_size = 0
        for asset_list in [discovery['models'], discovery['icons']]:
            for asset in asset_list:
                total_size += asset.get('size', 0)

        return {
            **summary,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'storage_breakdown': self._get_storage_breakdown()
        }

    def _get_storage_breakdown(self) -> Dict[str, int]:
        """Get storage breakdown by asset type"""
        breakdown = {}

        # Count files by directory
        for dir_path in [self.models_dir, self.icons_dir, self.textures_dir]:
            if dir_path.exists():
                file_count = len(list(dir_path.rglob("*")))
                breakdown[dir_path.name] = file_count

        return breakdown