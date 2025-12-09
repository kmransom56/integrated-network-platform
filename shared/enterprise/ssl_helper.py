"""
SSL Helper for Corporate Network Environments
Python adaptation of https://github.com/kmransom56/node-ssl-helper

Handles SSL certificate issues commonly encountered in corporate environments
with SSL interception (Zscaler, Blue Coat, etc.)
"""

import os
import ssl
import sys
import requests
import urllib3
from pathlib import Path
from typing import Optional, List, Dict, Any
import warnings
import logging
from urllib3.exceptions import InsecureRequestWarning

logger = logging.getLogger(__name__)


class CorporateSSLHelper:
    """
    Comprehensive SSL certificate handler for corporate environments
    
    Handles common corporate network challenges:
    - Zscaler SSL interception
    - Corporate proxy certificates
    - Self-signed internal certificates
    - Certificate bundle management
    """
    
    def __init__(self):
        self.custom_ca_paths = []
        self.ssl_verify_disabled = False
        self.original_ssl_context = None
        self.session_configured = False
        
    def auto_configure_corporate_ssl(self) -> bool:
        """
        Automatically detect and configure SSL settings for corporate environment
        
        Returns:
            bool: True if SSL configuration was successful
        """
        logger.info("🔧 Auto-configuring SSL for corporate environment...")
        
        # Try multiple configuration approaches
        configured = False
        
        # 1. Try environment-specified CA
        if self._configure_from_environment():
            configured = True
            logger.info("✅ SSL configured from environment variables")
        
        # 2. Try common corporate CA locations
        if not configured and self._discover_corporate_cas():
            configured = True
            logger.info("✅ SSL configured from discovered corporate CAs")
        
        # 3. Try system certificate stores
        if not configured and self._configure_system_certificates():
            configured = True
            logger.info("✅ SSL configured from system certificate store")
        
        # 4. Last resort - controlled SSL verification bypass (with warnings)
        if not configured:
            logger.warning("⚠️  Could not find corporate certificates, using fallback SSL configuration")
            self._configure_fallback_ssl()
            configured = True
        
        return configured
    
    def trust_custom_ca(self, ca_path: Optional[str] = None, ca_env_var: str = "ZSCALER_CA_PATH") -> bool:
        """
        Trust a custom CA certificate for all requests
        
        Args:
            ca_path: Path to CA certificate file
            ca_env_var: Environment variable containing CA path
            
        Returns:
            bool: True if CA was successfully configured
        """
        # Get CA path from parameter or environment
        if not ca_path:
            ca_path = os.environ.get(ca_env_var)
        
        if not ca_path:
            logger.warning(f"No CA path provided and {ca_env_var} not set")
            return False
        
        ca_file = Path(ca_path)
        if not ca_file.exists():
            logger.error(f"CA file not found: {ca_path}")
            return False
        
        try:
            # Add to custom CA paths
            self.custom_ca_paths.append(str(ca_file))
            
            # Configure requests to use the CA
            self._configure_requests_ca()
            
            # Set environment variable for other libraries
            os.environ["REQUESTS_CA_BUNDLE"] = str(ca_file)
            os.environ["CURL_CA_BUNDLE"] = str(ca_file)
            os.environ["SSL_CERT_FILE"] = str(ca_file)
            
            logger.info(f"✅ Custom CA configured: {ca_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure custom CA: {e}")
            return False
    
    def create_corporate_session(self) -> requests.Session:
        """
        Create a requests session configured for corporate environment
        
        Returns:
            requests.Session: Configured session with corporate SSL handling
        """
        session = requests.Session()
        
        # Configure SSL verification
        if self.custom_ca_paths:
            # Use custom CA bundle
            session.verify = self.custom_ca_paths[0]
        elif self.ssl_verify_disabled:
            # Disable verification with warnings
            session.verify = False
            urllib3.disable_warnings(InsecureRequestWarning)
        
        # Configure common corporate proxy headers
        session.headers.update({
            'User-Agent': 'Corporate-Network-Tool/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Configure timeouts for corporate networks
        session.timeout = (30, 60)  # (connect, read) timeouts
        
        self.session_configured = True
        logger.info("✅ Corporate session configured")
        
        return session
    
    def allow_corporate_self_signed(self, strict: bool = False) -> None:
        """
        Allow self-signed certificates (corporate development environments)
        
        Args:
            strict: If True, only disable for localhost/internal IPs
        """
        if not strict:
            # Global SSL verification bypass
            self.ssl_verify_disabled = True
            urllib3.disable_warnings(InsecureRequestWarning)
            logger.warning("⚠️  SSL certificate verification DISABLED globally")
        else:
            # More controlled bypass for internal networks
            logger.info("🔒 Strict mode: SSL bypass only for internal networks")
            # Implementation would check IP ranges, localhost, etc.
    
    def _configure_from_environment(self) -> bool:
        """Configure SSL from environment variables"""
        env_vars = [
            "ZSCALER_CA_PATH",
            "CORPORATE_CA_PATH", 
            "SSL_CERT_FILE",
            "REQUESTS_CA_BUNDLE",
            "CURL_CA_BUNDLE"
        ]
        
        for var in env_vars:
            ca_path = os.environ.get(var)
            if ca_path and Path(ca_path).exists():
                return self.trust_custom_ca(ca_path)
        
        return False
    
    def _discover_corporate_cas(self) -> bool:
        """Discover corporate CAs in common locations"""
        common_locations = []
        
        if sys.platform == "win32":
            # Windows common locations
            common_locations.extend([
                r"C:\Program Files\Zscaler\ZSARoot.pem",
                r"C:\Program Files (x86)\Zscaler\ZSARoot.pem",
                r"C:\certificates\zscaler-root.pem",
                r"C:\certificates\corporate-ca.pem",
                r"C:\tools\certificates\ca-bundle.pem"
            ])
        else:
            # Linux/macOS common locations
            common_locations.extend([
                "/etc/ssl/certs/zscaler-root.pem",
                "/etc/ssl/certs/corporate-ca.pem", 
                "/usr/local/share/ca-certificates/zscaler.crt",
                "/opt/certificates/ca-bundle.pem",
                os.path.expanduser("~/.certificates/zscaler.pem"),
                os.path.expanduser("~/.certificates/corporate-ca.pem")
            ])
        
        for location in common_locations:
            if Path(location).exists():
                logger.info(f"🔍 Found corporate CA at: {location}")
                return self.trust_custom_ca(location)
        
        return False
    
    def _configure_system_certificates(self) -> bool:
        """Configure to use system certificate store"""
        try:
            # Use system CA bundle
            import certifi
            ca_bundle = certifi.where()
            
            if Path(ca_bundle).exists():
                self.custom_ca_paths.append(ca_bundle)
                self._configure_requests_ca()
                logger.info(f"✅ Using system CA bundle: {ca_bundle}")
                return True
        except ImportError:
            logger.debug("certifi not available, skipping system certificate configuration")
        
        return False
    
    def _configure_fallback_ssl(self) -> None:
        """Configure fallback SSL settings with warnings"""
        logger.warning("⚠️  Using fallback SSL configuration")
        logger.warning("⚠️  This may bypass SSL certificate verification")
        
        # Set environment for debugging
        os.environ["PYTHONHTTPSVERIFY"] = "0"
        
        # Configure for corporate environment
        self.ssl_verify_disabled = True
        
        # Show guidance
        logger.info("💡 To fix SSL issues properly:")
        logger.info("   1. Export Zscaler/corporate root certificate")
        logger.info("   2. Set ZSCALER_CA_PATH environment variable")
        logger.info("   3. Or place certificate in common location")
    
    def _configure_requests_ca(self) -> None:
        """Configure requests library with custom CA"""
        if self.custom_ca_paths:
            os.environ["REQUESTS_CA_BUNDLE"] = self.custom_ca_paths[0]
    
    def get_ssl_verification_status(self) -> Dict[str, Any]:
        """Get current SSL configuration status"""
        return {
            "custom_ca_paths": self.custom_ca_paths,
            "ssl_verify_disabled": self.ssl_verify_disabled,
            "session_configured": self.session_configured,
            "environment_variables": {
                "REQUESTS_CA_BUNDLE": os.environ.get("REQUESTS_CA_BUNDLE"),
                "SSL_CERT_FILE": os.environ.get("SSL_CERT_FILE"),
                "ZSCALER_CA_PATH": os.environ.get("ZSCALER_CA_PATH"),
                "PYTHONHTTPSVERIFY": os.environ.get("PYTHONHTTPSVERIFY")
            }
        }


# Global SSL helper instance
ssl_helper = CorporateSSLHelper()


def configure_corporate_ssl(auto_configure: bool = True) -> requests.Session:
    """
    Convenience function to configure SSL for corporate environment
    
    Args:
        auto_configure: Whether to automatically detect and configure SSL
        
    Returns:
        requests.Session: Configured session for corporate use
    """
    if auto_configure:
        ssl_helper.auto_configure_corporate_ssl()
    
    return ssl_helper.create_corporate_session()


def trust_zscaler_ca(ca_path: Optional[str] = None) -> bool:
    """
    Convenience function specifically for Zscaler environments
    
    Args:
        ca_path: Path to Zscaler root certificate
        
    Returns:
        bool: True if successfully configured
    """
    return ssl_helper.trust_custom_ca(ca_path, "ZSCALER_CA_PATH")


def allow_corporate_development_ssl() -> None:
    """
    Convenience function to allow self-signed certificates in corporate development
    
    WARNING: Use only in development environments
    """
    ssl_helper.allow_corporate_self_signed(strict=False)


# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Corporate SSL Helper")
    parser.add_argument("--test", action="store_true", help="Test SSL configuration")
    parser.add_argument("--auto-configure", action="store_true", help="Auto-configure SSL")
    parser.add_argument("--ca-path", help="Path to custom CA certificate")
    parser.add_argument("--status", action="store_true", help="Show SSL configuration status")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if args.auto_configure:
        configure_corporate_ssl(auto_configure=True)
    
    if args.ca_path:
        trust_zscaler_ca(args.ca_path)
    
    if args.status:
        status = ssl_helper.get_ssl_verification_status()
        print("SSL Configuration Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    if args.test:
        print("Testing SSL configuration...")
        session = configure_corporate_ssl()
        
        # Test with a few common sites
        test_urls = [
            "https://httpbin.org/json",
            "https://api.github.com",
            "https://www.google.com"
        ]
        
        for url in test_urls:
            try:
                response = session.get(url, timeout=10)
                print(f"✅ {url}: {response.status_code}")
            except Exception as e:
                print(f"❌ {url}: {e}")