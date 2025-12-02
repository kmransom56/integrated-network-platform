"""
Environment Detector
Corporate environment detection from enhanced-network-api-corporate
"""

import os
import ssl
import socket
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class EnvironmentDetector:
    """
    Environment detector combining detection logic from:
    - enhanced-network-api-corporate corporate_environment_detector.py
    - SSL and proxy detection
    """

    def __init__(self):
        self.environment_info = {}

    def detect_all(self) -> Dict[str, Any]:
        """Run all environment detection checks"""
        logger.info("Detecting environment configuration...")

        self.environment_info = {
            'is_corporate': self._detect_corporate_environment(),
            'proxy_detected': self._detect_proxy_settings(),
            'ssl_configuration': self._detect_ssl_configuration(),
            'certificate_paths': self._find_certificate_paths(),
            'network_restrictions': self._detect_network_restrictions(),
            'available_services': self._detect_available_services()
        }

        logger.info(f"Environment detection complete: corporate={self.environment_info['is_corporate']}")
        return self.environment_info

    def _detect_corporate_environment(self) -> bool:
        """Detect if running in a corporate environment"""
        corporate_indicators = [
            # Environment variables
            'ZSCALER_CA_PATH',
            'BLUECOAT_PROXY',
            'CORPORATE_SSL',

            # Process names that might indicate corporate software
            'zscaler',
            'bluecoat',
            'cisco_anyconnect',
            'globalprotect',

            # Common corporate domains in environment
            '.corporate',
            '.internal',
            '.local',

            # Certificate stores
            '/etc/ssl/certs/ca-certificates.crt',
            '/etc/ssl/certs/ca-bundle.crt',
            '/usr/local/share/ca-certificates',

            # Proxy settings
            'http_proxy',
            'https_proxy',
            'no_proxy'
        ]

        # Check environment variables
        env_indicators = sum(1 for indicator in corporate_indicators
                           if any(indicator.upper() in key.upper() for key in os.environ.keys()))

        # Check environment values
        env_values_indicators = sum(1 for indicator in corporate_indicators
                                  if any(indicator.lower() in value.lower()
                                        for value in os.environ.values()))

        # Check for corporate certificate files
        cert_files_exist = any(Path(cert_path).exists()
                             for cert_path in ['/etc/ssl/certs/ca-certificates.crt',
                                             '/etc/ssl/certs/ca-bundle.crt',
                                             './corporate-ca.pem'])

        total_indicators = env_indicators + env_values_indicators + (1 if cert_files_exist else 0)

        return total_indicators >= 2  # Require at least 2 indicators

    def _detect_proxy_settings(self) -> Optional[Dict[str, str]]:
        """Detect proxy settings"""
        proxies = {}

        # Check environment variables
        for protocol in ['http', 'https', 'ftp', 'socks']:
            proxy_env = os.getenv(f'{protocol}_proxy')
            if proxy_env:
                proxies[protocol] = proxy_env

        # Check for no_proxy
        no_proxy = os.getenv('no_proxy')
        if no_proxy:
            proxies['no_proxy'] = no_proxy

        return proxies if proxies else None

    def _detect_ssl_configuration(self) -> Dict[str, Any]:
        """Detect SSL/TLS configuration"""
        ssl_info = {
            'ca_certs_available': False,
            'ssl_verify_default': True,
            'custom_cert_path': None,
            'ssl_version': None
        }

        try:
            # Check default SSL context
            context = ssl.create_default_context()
            ssl_info['ssl_version'] = context.protocol.name if hasattr(context, 'protocol') else 'unknown'

            # Check if CA certificates are loaded
            if context.cert_store_stats():
                ssl_info['ca_certs_available'] = True

        except Exception as e:
            logger.warning(f"SSL detection error: {e}")

        # Check for custom certificate paths
        custom_paths = [
            Path('./corporate-ca.pem'),
            Path('./zscaler-ca.pem'),
            Path('./bluecoat-ca.pem'),
            Path('/etc/ssl/certs/corporate-ca.pem')
        ]

        for cert_path in custom_paths:
            if cert_path.exists():
                ssl_info['custom_cert_path'] = str(cert_path)
                ssl_info['ssl_verify_default'] = False  # Custom cert usually means disable verify
                break

        return ssl_info

    def _find_certificate_paths(self) -> List[str]:
        """Find available certificate paths"""
        cert_paths = []

        common_paths = [
            '/etc/ssl/certs/ca-certificates.crt',
            '/etc/ssl/certs/ca-bundle.crt',
            '/usr/local/share/ca-certificates',
            '/etc/pki/tls/certs/ca-bundle.crt',
            './corporate-ca.pem',
            './zscaler-ca.pem'
        ]

        for path_str in common_paths:
            path = Path(path_str)
            if path.exists():
                cert_paths.append(path_str)

        return cert_paths

    def _detect_network_restrictions(self) -> Dict[str, Any]:
        """Detect network restrictions and connectivity"""
        restrictions = {
            'internet_access': False,
            'proxy_required': False,
            'ssl_inspection': False,
            'corporate_firewall': False
        }

        try:
            # Test internet connectivity
            response = requests.get('https://www.google.com', timeout=5, verify=False)
            if response.status_code == 200:
                restrictions['internet_access'] = True

        except requests.exceptions.RequestException:
            # Check if it's a proxy/firewall issue
            if self._detect_proxy_settings():
                restrictions['proxy_required'] = True

            # Try with proxy disabled
            try:
                response = requests.get('https://www.google.com', timeout=5,
                                      verify=False, proxies={})
                if response.status_code == 200:
                    restrictions['internet_access'] = True
            except:
                pass

        # Detect SSL inspection (common in corporate environments)
        try:
            # Test against a known SSL-inspecting proxy signature
            response = requests.get('https://httpbin.org/get', timeout=5, verify=True)
            if 'zscaler' in response.headers.get('server', '').lower():
                restrictions['ssl_inspection'] = True
                restrictions['corporate_firewall'] = True
        except:
            pass

        return restrictions

    def _detect_available_services(self) -> Dict[str, Any]:
        """Detect what network services are available"""
        services = {
            'fortigate_api': False,
            'fortimanager_api': False,
            'meraki_api': False,
            'dns_resolution': False,
            'external_api_access': False
        }

        # Test DNS resolution
        try:
            socket.gethostbyname('google.com')
            services['dns_resolution'] = True
        except:
            pass

        # Test external API access
        try:
            response = requests.get('https://api.github.com', timeout=5, verify=False)
            if response.status_code == 200:
                services['external_api_access'] = True
        except:
            pass

        # Note: FortiGate/Meraki API tests would require credentials
        # They would be tested during actual API calls

        return services

    def get_recommended_config(self) -> Dict[str, Any]:
        """Get recommended configuration based on detected environment"""
        if not self.environment_info:
            self.detect_all()

        config = {}

        if self.environment_info.get('is_corporate'):
            config.update({
                'ssl_verify': False,
                'timeout': 60,  # Longer timeouts for corporate networks
                'retries': 5
            })

            # Set proxy if detected
            proxy_settings = self.environment_info.get('proxy_detected')
            if proxy_settings:
                config['proxies'] = proxy_settings

            # Set custom certificate path if found
            cert_paths = self.environment_info.get('certificate_paths', [])
            if cert_paths:
                config['ca_cert_path'] = cert_paths[0]

        return config

    def print_environment_report(self):
        """Print a human-readable environment report"""
        if not self.environment_info:
            self.detect_all()

        print("🔍 Environment Detection Report")
        print("=" * 40)

        env = self.environment_info

        print(f"Corporate Environment: {'✅ Yes' if env['is_corporate'] else '❌ No'}")

        if env.get('proxy_detected'):
            print(f"Proxy Detected: ✅ Yes")
            for protocol, proxy in env['proxy_detected'].items():
                print(f"  {protocol}: {proxy}")
        else:
            print(f"Proxy Detected: ❌ No")

        ssl_config = env.get('ssl_configuration', {})
        print(f"SSL Verification: {'⚠️  Disabled' if not ssl_config.get('ssl_verify_default') else '✅ Enabled'}")

        if env.get('certificate_paths'):
            print(f"Certificate Paths: ✅ Found {len(env['certificate_paths'])} paths")

        restrictions = env.get('network_restrictions', {})
        if restrictions.get('corporate_firewall'):
            print("Corporate Firewall: ✅ Detected")

        services = env.get('available_services', {})
        print(f"DNS Resolution: {'✅ Working' if services.get('dns_resolution') else '❌ Failed'}")
        print(f"External API Access: {'✅ Working' if services.get('external_api_access') else '❌ Blocked'}")

        # Recommendations
        print("\n💡 Recommendations:")
        recommended = self.get_recommended_config()
        for key, value in recommended.items():
            if key == 'proxies':
                print(f"  • Configure proxies: {value}")
            elif key == 'ca_cert_path':
                print(f"  • Use custom CA certificate: {value}")
            else:
                print(f"  • Set {key}: {value}")