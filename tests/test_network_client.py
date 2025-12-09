import pytest
from shared.network_utils.network_client import NetworkClient, DeviceType

def test_enums():
    """Test device types"""
    assert DeviceType.FORTIGATE.value == "fortigate"

def test_client_instantiation():
    """Test standard init"""
    # This will trigger AuthManager init, which reads env.
    # We should mock env to avoid warnings?
    client = NetworkClient()
    assert client is not None
