"""
Unified Configuration Management
Combines configuration from both applications
"""

from .config_manager import ConfigManager, ConfigValidator
from .environment_detector import EnvironmentDetector

__all__ = [
    'ConfigManager',
    'ConfigValidator',
    'EnvironmentDetector'
]