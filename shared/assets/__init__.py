"""
Shared Assets Management
Combines asset management from both applications
"""

from .asset_manager import AssetManager
from .model_registry import ModelRegistry
from .icon_library import IconLibrary

__all__ = [
    'AssetManager',
    'ModelRegistry',
    'IconLibrary'
]