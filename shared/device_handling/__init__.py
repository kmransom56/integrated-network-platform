"""
Shared Device Handling Module
Combines device handling from both applications
"""

from .device_processor import DeviceProcessor, DeviceMatcher
from .device_collector import UnifiedDeviceCollector
from .device_classifier import DeviceClassifier

__all__ = [
    'DeviceProcessor',
    'DeviceMatcher',
    'UnifiedDeviceCollector',
    'DeviceClassifier'
]