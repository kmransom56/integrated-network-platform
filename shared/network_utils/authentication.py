"""
Unified Authentication Manager
Combines authentication methods from both applications
"""

import requests
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Unified authentication manager combining:
    - FortiGate auth from network_map_3d (fortigate_auth.py)
    - FortiManager auth from enhanced-network-api-corporate
    - Meraki auth from enhanced-network-api-corporate
    """

    def __init__(self):
        self.sessions = {}
        self.credentials = {}

    def authenticate_fortigate(self, host: str, username: str, password: str) -> Optional[requests.Session]:
        """Authenticate with FortiGate (from network_map_3d)"""
        try:
            session = requests.Session()
            session.verify = False

            # FortiGate login
            login_url = f"https://{host}/logincheck"
            login_data = {
                'username': username,
                'secretkey': password,
                'ajax': '1'
            }

            response = session.post(login_url, data=login_data, timeout=30)
            if response.status_code == 200:
                self.sessions[f"fortigate_{host}"] = session
                logger.info(f"Successfully authenticated with FortiGate {host}")
                return session
            else:
                logger.error(f"Failed to authenticate with FortiGate {host}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"FortiGate authentication error: {e}")
            return None

    def authenticate_fortimanager(self, host: str, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate with FortiManager (from enhanced-network-api-corporate)"""
        try:
            session = requests.Session()
            session.verify = False

            # FortiManager login
            login_url = f"https://{host}/jsonrpc"
            login_payload = {
                "id": 1,
                "method": "exec",
                "params": [
                    {
                        "url": "/sys/login/user",
                        "data": {
                            "user": username,
                            "passwd": password
                        }
                    }
                ]
            }

            response = session.post(login_url, json=login_payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
                session_info = {
                    'session': session,
                    'session_id': result.get('session'),
                    'host': host
                }
                self.sessions[f"fortimanager_{host}"] = session_info
                logger.info(f"Successfully authenticated with FortiManager {host}")
                return session_info
            else:
                logger.error(f"FortiManager login failed: {result}")
                return None

        except Exception as e:
            logger.error(f"FortiManager authentication error: {e}")
            return None

    def authenticate_meraki(self, api_key: str) -> bool:
        """Set up Meraki API authentication"""
        try:
            self.credentials['meraki'] = {'api_key': api_key}
            logger.info("Meraki API key configured")
            return True
        except Exception as e:
            logger.error(f"Meraki authentication setup error: {e}")
            return False

    def get_session(self, service_type: str, host: Optional[str] = None) -> Optional[requests.Session]:
        """Get authenticated session for service type"""
        key = f"{service_type}_{host}" if host else service_type
        session_info = self.sessions.get(key)

        if isinstance(session_info, dict):
            return session_info.get('session')
        return session_info

    def is_authenticated(self, service_type: str, host: Optional[str] = None) -> bool:
        """Check if authenticated for service type"""
        key = f"{service_type}_{host}" if host else service_type
        return key in self.sessions

    def logout_all(self):
        """Logout from all authenticated sessions"""
        for key, session_info in self.sessions.items():
            try:
                if isinstance(session_info, dict):
                    session = session_info.get('session')
                    if session:
                        # Attempt logout if possible
                        pass  # Implement specific logout logic per service
                else:
                    # Direct session
                    pass
            except Exception as e:
                logger.warning(f"Error during logout for {key}: {e}")

        self.sessions.clear()
        logger.info("Logged out from all sessions")