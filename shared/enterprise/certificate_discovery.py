"""
Automated SSL Certificate Discovery and Validation
Finds, validates, and configures SSL certificates in corporate environments
"""

import os
import sys
import ssl
import json
import socket
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import hashlib
import base64

# Certificate parsing
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("⚠️  cryptography library not available. Some certificate features may be limited.")

logger = logging.getLogger(__name__)


class CorporateCertificateDiscovery:
    """
    Comprehensive SSL certificate discovery and validation for corporate environments
    """
    
    def __init__(self):
        self.discovered_certificates = []
        self.validation_results = {}
        self.certificate_chains = {}
        
    def auto_discover_certificates(self) -> Dict[str, Any]:
        """
        Automatically discover SSL certificates in corporate environment
        
        Returns:
            Dict: Discovery results with found certificates and recommendations
        """
        logger.info("🔍 Starting automated SSL certificate discovery...")
        
        discovery_results = {
            "certificates_found": [],
            "validation_results": {},
            "recommendations": [],
            "corporate_indicators": [],
            "discovery_methods": []
        }
        
        # 1. Environment variable discovery
        env_certs = self._discover_from_environment()
        if env_certs:
            discovery_results["certificates_found"].extend(env_certs)
            discovery_results["discovery_methods"].append("environment_variables")
        
        # 2. File system discovery
        fs_certs = self._discover_from_filesystem()
        if fs_certs:
            discovery_results["certificates_found"].extend(fs_certs)
            discovery_results["discovery_methods"].append("filesystem_scan")
        
        # 3. System certificate store discovery
        sys_certs = self._discover_from_system_store()
        if sys_certs:
            discovery_results["certificates_found"].extend(sys_certs)
            discovery_results["discovery_methods"].append("system_certificate_store")
        
        # 4. Network-based discovery (test actual SSL connections)
        network_certs = self._discover_from_network_connections()
        if network_certs:
            discovery_results["certificates_found"].extend(network_certs)
            discovery_results["discovery_methods"].append("network_analysis")
        
        # 5. Corporate software detection
        corporate_indicators = self._detect_corporate_software()
        discovery_results["corporate_indicators"] = corporate_indicators
        
        # 6. Validate discovered certificates
        for cert_info in discovery_results["certificates_found"]:
            validation = self._validate_certificate(cert_info)
            discovery_results["validation_results"][cert_info["path"]] = validation
        
        # 7. Generate recommendations
        discovery_results["recommendations"] = self._generate_certificate_recommendations(discovery_results)
        
        logger.info(f"✅ Certificate discovery completed. Found {len(discovery_results['certificates_found'])} certificates")
        
        return discovery_results
    
    def validate_certificate_chain(self, cert_path: str, test_url: str = "https://httpbin.org") -> Dict[str, Any]:
        """
        Validate certificate chain for a specific certificate
        
        Args:
            cert_path: Path to certificate file
            test_url: URL to test certificate against
            
        Returns:
            Dict: Validation results
        """
        logger.info(f"🔐 Validating certificate chain: {cert_path}")
        
        validation_result = {
            "certificate_path": cert_path,
            "is_valid": False,
            "chain_length": 0,
            "issues": [],
            "test_results": {},
            "certificate_info": {}
        }
        
        try:
            # Load and parse certificate
            with open(cert_path, 'rb') as cert_file:
                cert_data = cert_file.read()
            
            if CRYPTOGRAPHY_AVAILABLE:
                cert_info = self._parse_certificate_details(cert_data)
                validation_result["certificate_info"] = cert_info
                
                # Check certificate validity
                if cert_info.get("expired", False):
                    validation_result["issues"].append("Certificate is expired")
                
                if cert_info.get("not_yet_valid", False):
                    validation_result["issues"].append("Certificate is not yet valid")
            
            # Test certificate with actual SSL connection
            test_result = self._test_certificate_connection(cert_path, test_url)
            validation_result["test_results"] = test_result
            
            if test_result["connection_successful"]:
                validation_result["is_valid"] = True
            else:
                validation_result["issues"].extend(test_result.get("errors", []))
            
        except Exception as e:
            validation_result["issues"].append(f"Certificate validation error: {e}")
            logger.error(f"❌ Certificate validation failed: {e}")
        
        return validation_result
    
    def export_zscaler_certificate(self, output_path: str = None) -> Optional[str]:
        """
        Attempt to export Zscaler root certificate from system
        
        Args:
            output_path: Where to save the exported certificate
            
        Returns:
            str: Path to exported certificate if successful
        """
        logger.info("📤 Attempting to export Zscaler certificate...")
        
        if not output_path:
            output_path = "zscaler-root-exported.pem"
        
        export_methods = []
        
        if platform.system() == "Windows":
            export_methods = [
                self._export_zscaler_windows_registry,
                self._export_zscaler_windows_certstore,
                self._export_zscaler_windows_files
            ]
        else:
            export_methods = [
                self._export_zscaler_linux_files,
                self._export_zscaler_system_store
            ]
        
        for method in export_methods:
            try:
                cert_path = method(output_path)
                if cert_path and Path(cert_path).exists():
                    logger.info(f"✅ Zscaler certificate exported: {cert_path}")
                    return cert_path
            except Exception as e:
                logger.debug(f"Export method failed: {e}")
        
        logger.warning("⚠️  Could not automatically export Zscaler certificate")
        logger.info("💡 Manual export steps:")
        logger.info("   1. Open Zscaler app")
        logger.info("   2. Go to Settings → Export Root Certificate")
        logger.info("   3. Save as PEM format")
        logger.info("   4. Set ZSCALER_CA_PATH environment variable")
        
        return None
    
    def create_certificate_bundle(self, cert_paths: List[str], bundle_path: str = "corporate-ca-bundle.pem") -> str:
        """
        Create a certificate bundle from multiple certificate files
        
        Args:
            cert_paths: List of certificate file paths
            bundle_path: Output bundle file path
            
        Returns:
            str: Path to created bundle
        """
        logger.info(f"📦 Creating certificate bundle: {bundle_path}")
        
        bundle_content = []
        bundle_content.append("# Corporate Certificate Bundle")
        bundle_content.append(f"# Created: {datetime.now().isoformat()}")
        bundle_content.append("# Sources:")
        
        for cert_path in cert_paths:
            bundle_content.append(f"#   - {cert_path}")
        
        bundle_content.append("")
        
        for cert_path in cert_paths:
            cert_file = Path(cert_path)
            if cert_file.exists():
                logger.info(f"  📄 Adding certificate: {cert_file.name}")
                bundle_content.append(f"# Certificate from: {cert_path}")
                
                with open(cert_file, 'r') as f:
                    cert_data = f.read().strip()
                
                bundle_content.append(cert_data)
                bundle_content.append("")
            else:
                logger.warning(f"  ⚠️  Certificate not found: {cert_path}")
        
        # Write bundle
        with open(bundle_path, 'w') as bundle_file:
            bundle_file.write("\\n".join(bundle_content))
        
        logger.info(f"✅ Certificate bundle created: {bundle_path}")
        return bundle_path
    
    def _discover_from_environment(self) -> List[Dict[str, Any]]:
        """Discover certificates from environment variables"""
        certificates = []
        
        env_vars = [
            "ZSCALER_CA_PATH",
            "CORPORATE_CA_PATH",
            "SSL_CERT_FILE", 
            "REQUESTS_CA_BUNDLE",
            "CURL_CA_BUNDLE",
            "SSL_CERT_DIR"
        ]
        
        for var in env_vars:
            cert_path = os.environ.get(var)
            if cert_path and Path(cert_path).exists():
                certificates.append({
                    "path": cert_path,
                    "source": f"environment_variable_{var}",
                    "type": "file"
                })
                logger.info(f"  📄 Found certificate from {var}: {cert_path}")
        
        return certificates
    
    def _discover_from_filesystem(self) -> List[Dict[str, Any]]:
        """Discover certificates from common file system locations"""
        certificates = []
        
        search_locations = []
        
        if platform.system() == "Windows":
            search_locations = [
                r"C:\\Program Files\\Zscaler",
                r"C:\\Program Files (x86)\\Zscaler",
                r"C:\\certificates",
                r"C:\\tools\\certificates",
                Path.home() / "certificates",
                Path.home() / ".certificates"
            ]
        else:
            search_locations = [
                "/etc/ssl/certs",
                "/usr/local/share/ca-certificates",
                "/opt/certificates",
                Path.home() / ".certificates",
                Path.home() / ".ssl",
                "/usr/share/ca-certificates"
            ]
        
        # Common certificate file patterns
        cert_patterns = [
            "*zscaler*.pem", "*zscaler*.crt",
            "*corporate*.pem", "*corporate*.crt", 
            "*ca-bundle*.pem", "*ca-bundle*.crt",
            "*root*.pem", "*root*.crt"
        ]
        
        for location in search_locations:
            location_path = Path(location)
            if location_path.exists():
                for pattern in cert_patterns:
                    for cert_file in location_path.glob(pattern):
                        if cert_file.is_file():
                            certificates.append({
                                "path": str(cert_file),
                                "source": f"filesystem_{location}",
                                "type": "file",
                                "pattern_matched": pattern
                            })
                            logger.info(f"  📄 Found certificate: {cert_file}")
        
        return certificates
    
    def _discover_from_system_store(self) -> List[Dict[str, Any]]:
        """Discover certificates from system certificate store"""
        certificates = []
        
        if platform.system() == "Windows":
            # Try to access Windows certificate store
            certificates.extend(self._discover_windows_cert_store())
        else:
            # Try common system certificate locations
            system_locations = [
                "/etc/ssl/certs/ca-certificates.crt",
                "/etc/pki/tls/certs/ca-bundle.crt",
                "/etc/ssl/ca-bundle.pem",
                "/usr/local/etc/ssl/certs/cacert.pem"
            ]
            
            for location in system_locations:
                if Path(location).exists():
                    certificates.append({
                        "path": location,
                        "source": "system_certificate_store",
                        "type": "bundle"
                    })
                    logger.info(f"  📦 Found system certificate bundle: {location}")
        
        return certificates
    
    def _discover_from_network_connections(self) -> List[Dict[str, Any]]:
        """Discover certificates by analyzing network connections"""
        certificates = []
        
        # Test common sites to see what certificates are being used
        test_sites = [
            ("httpbin.org", 443),
            ("api.github.com", 443),
            ("www.google.com", 443)
        ]
        
        for host, port in test_sites:
            try:
                cert_info = self._get_certificate_from_connection(host, port)
                if cert_info and cert_info.get("issuer_indicates_interception"):
                    certificates.append({
                        "path": f"network_discovery_{host}",
                        "source": "network_analysis",
                        "type": "network_discovered",
                        "host": host,
                        "port": port,
                        "issuer": cert_info.get("issuer"),
                        "interception_detected": True
                    })
                    logger.info(f"  🌐 SSL interception detected for {host}: {cert_info.get('issuer')}")
                    
            except Exception as e:
                logger.debug(f"Network certificate discovery failed for {host}: {e}")
        
        return certificates
    
    def _detect_corporate_software(self) -> List[Dict[str, str]]:
        """Detect installed corporate software that might affect SSL"""
        indicators = []
        
        if platform.system() == "Windows":
            # Check for Zscaler
            zscaler_paths = [
                r"C:\\Program Files\\Zscaler",
                r"C:\\Program Files (x86)\\Zscaler"
            ]
            
            for path in zscaler_paths:
                if Path(path).exists():
                    indicators.append({
                        "software": "Zscaler",
                        "path": path,
                        "type": "ssl_interception"
                    })
            
            # Check for Blue Coat
            bluecoat_indicators = [
                r"C:\\Program Files\\Blue Coat",
                r"C:\\Program Files (x86)\\Blue Coat"
            ]
            
            for path in bluecoat_indicators:
                if Path(path).exists():
                    indicators.append({
                        "software": "Blue Coat ProxySG", 
                        "path": path,
                        "type": "ssl_interception"
                    })
        
        return indicators
    
    def _validate_certificate(self, cert_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a discovered certificate"""
        validation = {
            "is_readable": False,
            "is_valid_format": False,
            "certificate_details": {},
            "issues": [],
            "recommendations": []
        }
        
        cert_path = cert_info.get("path")
        if not cert_path or not Path(cert_path).exists():
            validation["issues"].append("Certificate file not found")
            return validation
        
        try:
            with open(cert_path, 'r') as f:
                cert_content = f.read()
            
            validation["is_readable"] = True
            
            # Check if it looks like a certificate
            if "BEGIN CERTIFICATE" in cert_content or "BEGIN TRUSTED CERTIFICATE" in cert_content:
                validation["is_valid_format"] = True
                
                if CRYPTOGRAPHY_AVAILABLE:
                    try:
                        cert_data = cert_content.encode()
                        cert_details = self._parse_certificate_details(cert_data)
                        validation["certificate_details"] = cert_details
                        
                        if cert_details.get("expired"):
                            validation["issues"].append("Certificate is expired")
                        
                        if cert_details.get("self_signed"):
                            validation["recommendations"].append("Self-signed certificate detected")
                            
                    except Exception as e:
                        validation["issues"].append(f"Certificate parsing error: {e}")
            else:
                validation["issues"].append("File does not appear to contain a valid certificate")
                
        except Exception as e:
            validation["issues"].append(f"Error reading certificate file: {e}")
        
        return validation
    
    def _parse_certificate_details(self, cert_data: bytes) -> Dict[str, Any]:
        """Parse certificate details using cryptography library"""
        if not CRYPTOGRAPHY_AVAILABLE:
            return {"error": "cryptography library not available"}
        
        try:
            # Try PEM format first
            try:
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            except ValueError:
                # Try DER format
                cert = x509.load_der_x509_certificate(cert_data, default_backend())
            
            # Extract certificate details
            details = {
                "subject": dict(cert.subject),
                "issuer": dict(cert.issuer),
                "serial_number": str(cert.serial_number),
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "expired": cert.not_valid_after < datetime.now(),
                "not_yet_valid": cert.not_valid_before > datetime.now(),
                "self_signed": cert.subject == cert.issuer,
                "fingerprint": hashlib.sha256(cert.public_bytes(x509.Encoding.DER)).hexdigest()
            }
            
            return details
            
        except Exception as e:
            return {"error": f"Certificate parsing failed: {e}"}
    
    def _test_certificate_connection(self, cert_path: str, test_url: str) -> Dict[str, Any]:
        """Test certificate by making an SSL connection"""
        test_result = {
            "connection_successful": False,
            "errors": [],
            "ssl_info": {}
        }
        
        try:
            import requests
            
            # Create session with custom certificate
            session = requests.Session()
            session.verify = cert_path
            
            response = session.get(test_url, timeout=10)
            test_result["connection_successful"] = True
            test_result["ssl_info"]["status_code"] = response.status_code
            
        except requests.exceptions.SSLError as e:
            test_result["errors"].append(f"SSL verification failed: {e}")
        except Exception as e:
            test_result["errors"].append(f"Connection test failed: {e}")
        
        return test_result
    
    def _get_certificate_from_connection(self, host: str, port: int) -> Optional[Dict[str, Any]]:
        """Get certificate information from an SSL connection"""
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check if issuer indicates SSL interception
                    issuer = dict(x[0] for x in cert['issuer'])
                    
                    interception_indicators = [
                        "zscaler", "blue coat", "corporate", "proxy", "firewall"
                    ]
                    
                    issuer_text = " ".join(issuer.values()).lower()
                    interception_detected = any(indicator in issuer_text 
                                              for indicator in interception_indicators)
                    
                    return {
                        "issuer": issuer,
                        "subject": dict(x[0] for x in cert['subject']),
                        "issuer_indicates_interception": interception_detected,
                        "serial_number": cert.get('serialNumber'),
                        "not_after": cert.get('notAfter'),
                        "not_before": cert.get('notBefore')
                    }
                    
        except Exception as e:
            logger.debug(f"Could not get certificate from {host}:{port}: {e}")
            return None
    
    def _generate_certificate_recommendations(self, discovery_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on certificate discovery"""
        recommendations = []
        
        certificates_found = len(discovery_results["certificates_found"])
        
        if certificates_found == 0:
            recommendations.extend([
                "No certificates found automatically",
                "Manual certificate export may be required",
                "Contact IT department for corporate certificate",
                "Check Zscaler/Blue Coat application for certificate export"
            ])
        elif certificates_found == 1:
            cert_path = discovery_results["certificates_found"][0]["path"]
            recommendations.extend([
                f"Configure applications to use: {cert_path}",
                f"Set ZSCALER_CA_PATH={cert_path}",
                "Test certificate with sample applications"
            ])
        else:
            recommendations.extend([
                "Multiple certificates found - create certificate bundle",
                "Test each certificate to determine which works best",
                "Configure applications to use the most comprehensive bundle"
            ])
        
        if discovery_results["corporate_indicators"]:
            recommendations.append("Corporate SSL interception software detected")
            recommendations.append("Certificate configuration is strongly recommended")
        
        return recommendations
    
    def _discover_windows_cert_store(self) -> List[Dict[str, Any]]:
        """Discover certificates from Windows certificate store"""
        certificates = []
        
        try:
            # This would require additional Windows-specific libraries
            # For now, we'll just indicate that the system store should be checked
            certificates.append({
                "path": "windows_certificate_store",
                "source": "windows_system_store", 
                "type": "system_store",
                "note": "Check Windows Certificate Manager (certmgr.msc)"
            })
        except Exception as e:
            logger.debug(f"Windows certificate store discovery failed: {e}")
        
        return certificates


# Convenience functions

def auto_discover_corporate_certificates() -> Dict[str, Any]:
    """Auto-discover corporate certificates"""
    discovery = CorporateCertificateDiscovery()
    return discovery.auto_discover_certificates()


def validate_certificate(cert_path: str) -> Dict[str, Any]:
    """Validate a specific certificate"""
    discovery = CorporateCertificateDiscovery()
    return discovery.validate_certificate_chain(cert_path)


def export_zscaler_certificate(output_path: str = None) -> Optional[str]:
    """Export Zscaler certificate"""
    discovery = CorporateCertificateDiscovery()
    return discovery.export_zscaler_certificate(output_path)


# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Corporate Certificate Discovery")
    parser.add_argument("--discover", action="store_true", help="Auto-discover certificates")
    parser.add_argument("--validate", help="Validate specific certificate")
    parser.add_argument("--export-zscaler", action="store_true", help="Export Zscaler certificate")
    parser.add_argument("--create-bundle", nargs="+", help="Create certificate bundle from files")
    parser.add_argument("--test-url", default="https://httpbin.org", help="URL to test certificates against")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    discovery = CorporateCertificateDiscovery()
    
    if args.discover:
        print("🔍 Discovering corporate certificates...")
        results = discovery.auto_discover_certificates()
        
        print(f"\\nFound {len(results['certificates_found'])} certificates:")
        for cert in results['certificates_found']:
            print(f"  📄 {cert['path']} (from {cert['source']})")
        
        if results['recommendations']:
            print("\\nRecommendations:")
            for rec in results['recommendations']:
                print(f"  💡 {rec}")
    
    if args.validate:
        print(f"🔐 Validating certificate: {args.validate}")
        result = discovery.validate_certificate_chain(args.validate, args.test_url)
        
        print(f"Valid: {result['is_valid']}")
        if result['issues']:
            print("Issues:")
            for issue in result['issues']:
                print(f"  ❌ {issue}")
    
    if args.export_zscaler:
        print("📤 Attempting to export Zscaler certificate...")
        cert_path = discovery.export_zscaler_certificate(args.output)
        if cert_path:
            print(f"✅ Certificate exported: {cert_path}")
        else:
            print("❌ Could not export Zscaler certificate automatically")
    
    if args.create_bundle:
        output_path = args.output or "corporate-ca-bundle.pem"
        print(f"📦 Creating certificate bundle: {output_path}")
        bundle_path = discovery.create_certificate_bundle(args.create_bundle, output_path)
        print(f"✅ Bundle created: {bundle_path}")


if __name__ == "__main__":
    main()