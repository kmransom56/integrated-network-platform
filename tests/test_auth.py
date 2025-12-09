import pytest
import os
from unittest.mock import patch, MagicMock
from shared.network_utils.authentication import AuthManager

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("FORTIGATE_HOST", "192.168.1.99")
    monkeypatch.setenv("FORTIGATE_TOKEN", "fake-token")
    monkeypatch.setenv("MERAKI_API_KEY", "fake-api-key")

def test_auth_meraki_config(mock_env):
    """Test Meraki configuration"""
    am = AuthManager()
    # We mock get_meraki_dashboard to avoid real API call
    with patch.object(am, 'get_meraki_dashboard') as mock_dash:
        success = am.authenticate_meraki("new-key")
        assert success is True
        assert am.credentials['meraki']['api_key'] == "new-key"
        mock_dash.assert_called_once()

def test_authenticate_fortigate_success():
    """Test FortiGate authentication flow"""
    am = AuthManager()
    with patch("requests.Session") as MockSession:
        session = MockSession.return_value
        # Explicit response mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        session.post.return_value = mock_response
        
        # Configure cookies to be iterable
        cookie = MagicMock()
        cookie.name = 'ccsrftoken'
        cookie.value = '"123"'
        session.cookies = [cookie]
        
        res = am.authenticate_fortigate("1.1.1.1", "admin", "pass")
        assert res is not None
        assert "fortigate_1.1.1.1" in am.sessions
        assert session.headers.update.called

def test_authenticate_fortigate_failure():
    """Test FortiGate failure"""
    am = AuthManager()
    with patch("requests.Session") as MockSession:
        session = MockSession.return_value
        session.post.return_value.status_code = 401
        
        res = am.authenticate_fortigate("1.1.1.1", "admin", "pass")
        assert res is None

