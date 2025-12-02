"""
Integrated Network Platform API
Combines APIs from both applications
"""

from .main import create_application
from .endpoints.devices import router as devices_router
from .endpoints.visualization import router as visualization_router
from .endpoints.topology import router as topology_router

__all__ = [
    'create_application',
    'devices_router',
    'visualization_router',
    'topology_router'
]