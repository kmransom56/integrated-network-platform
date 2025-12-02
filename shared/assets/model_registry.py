"""
Model Registry
Manages 3D model assets for devices
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for 3D models used in network visualizations"""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.registry_file = models_dir / "registry.json"
        self.models = {}
        self._load_registry()

    def _load_registry(self):
        """Load model registry from file"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    self.models = json.load(f)
                logger.info(f"Loaded {len(self.models)} models from registry")
            except Exception as e:
                logger.error(f"Failed to load model registry: {e}")
                self.models = {}
        else:
            self.models = {}

    def _save_registry(self):
        """Save model registry to file"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.models, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model registry: {e}")

    def discover_models(self) -> List[Dict[str, Any]]:
        """Discover all 3D models in the models directory"""
        models = []

        if not self.models_dir.exists():
            return models

        # Supported 3D formats
        model_extensions = {'.glb', '.gltf', '.obj', '.fbx', '.dae', '.3ds'}

        for file_path in self.models_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in model_extensions:
                model_info = self._analyze_model_file(file_path)
                if model_info:
                    models.append(model_info)

        return models

    def _analyze_model_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a 3D model file"""
        try:
            stat = file_path.stat()

            model_info = {
                'name': file_path.stem,
                'path': str(file_path),
                'format': file_path.suffix[1:].lower(),  # Remove the dot
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'relative_path': str(file_path.relative_to(self.models_dir)),
                'device_types': self._infer_device_types(file_path),
                'vendor': self._infer_vendor(file_path)
            }

            return model_info

        except Exception as e:
            logger.warning(f"Failed to analyze model {file_path}: {e}")
            return None

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

    def register_model(self, file_path: Path) -> bool:
        """Register a new model"""
        model_info = self._analyze_model_file(file_path)
        if model_info:
            model_id = file_path.stem
            self.models[model_id] = model_info
            self._save_registry()
            logger.info(f"Registered model: {model_id}")
            return True
        return False

    def get_model_for_device(self, device_type: str, vendor: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the best model for a device type and vendor"""
        candidates = []

        for model_id, model_info in self.models.items():
            # Check if model supports this device type
            if device_type in model_info.get('device_types', []):
                score = 1  # Base score for device type match

                # Bonus for vendor match
                if vendor and model_info.get('vendor') == vendor:
                    score += 2

                # Bonus for exact name match
                if device_type.lower() in model_id.lower():
                    score += 1

                candidates.append((score, model_info))

        if candidates:
            # Return highest scoring model
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]

        # Fallback to generic model
        return self._get_generic_model()

    def _get_generic_model(self) -> Optional[Dict[str, Any]]:
        """Get a generic fallback model"""
        for model_id, model_info in self.models.items():
            if 'generic' in model_info.get('device_types', []):
                return model_info

        # If no generic model, return any model
        return next(iter(self.models.values()), None) if self.models else None

    def get_models_by_vendor(self, vendor: str) -> List[Dict[str, Any]]:
        """Get all models for a specific vendor"""
        return [model for model in self.models.values() if model.get('vendor') == vendor]

    def get_models_by_type(self, device_type: str) -> List[Dict[str, Any]]:
        """Get all models for a specific device type"""
        return [model for model in self.models.values() if device_type in model.get('device_types', [])]

    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the registry"""
        if model_id in self.models:
            del self.models[model_id]
            self._save_registry()
            logger.info(f"Removed model: {model_id}")
            return True
        return False