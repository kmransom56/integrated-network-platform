"""
Unified Configuration Manager
Combines configuration management from both applications
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class NetworkConfig:
    """Unified network configuration"""
    # Authentication
    fortigate_host: Optional[str] = None
    fortigate_username: Optional[str] = None
    fortigate_password: Optional[str] = None

    fortimanager_host: Optional[str] = None
    fortimanager_username: Optional[str] = None
    fortimanager_password: Optional[str] = None

    meraki_api_key: Optional[str] = None
    meraki_org_id: Optional[str] = None

    # Application settings
    app_name: str = "integrated_network_platform"
    debug_mode: bool = False
    log_level: str = "INFO"

    # Paths
    data_dir: Path = field(default_factory=lambda: Path("./data"))
    logs_dir: Path = field(default_factory=lambda: Path("./logs"))
    exports_dir: Path = field(default_factory=lambda: Path("./exports"))
    models_dir: Path = field(default_factory=lambda: Path("./models"))
    icons_dir: Path = field(default_factory=lambda: Path("./icons"))

    # Network settings
    default_timeout: int = 30
    max_retries: int = 3
    concurrent_requests: int = 5

    # Visualization settings
    enable_3d: bool = True
    renderer: str = "three.js"  # or "babylon.js"
    default_layout: str = "layered"

    # Enterprise features
    enable_ssl_verification: bool = True
    corporate_proxy: Optional[str] = None
    certificate_path: Optional[str] = None

    # Advanced settings
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    export_formats: List[str] = field(default_factory=lambda: ["json", "gltf", "svg"])


class ConfigManager:
    """
    Unified configuration manager combining approaches from:
    - network_map_3d configuration
    - enhanced-network-api-corporate config.py and corporate environment detection
    """

    def __init__(self, config_file: Optional[str] = None):
        self.config = NetworkConfig()
        self.config_sources = []
        self._load_config(config_file)

    def _load_config(self, config_file: Optional[str] = None):
        """Load configuration from multiple sources"""

        # Load from environment variables first
        self._load_from_env()

        # Load from config file if provided
        if config_file:
            self._load_from_file(config_file)

        # Auto-detect corporate environment
        self._detect_corporate_environment()

        # Validate configuration
        self._validate_config()

        logger.info(f"Configuration loaded from {len(self.config_sources)} sources")

    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Try loading from multiple .env files (like enhanced-network-api-corporate)
        env_paths = [
            Path(".env"),
            Path("config.env"),
            Path("corporate.env"),
            Path("../.env"),
            Path("../../.env")
        ]

        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path, override=False)
                self.config_sources.append(f"env:{env_path}")
                break

        # Load network credentials
        self.config.fortigate_host = os.getenv('FORTIGATE_HOST')
        self.config.fortigate_username = os.getenv('FORTIGATE_USERNAME')
        self.config.fortigate_password = os.getenv('FORTIGATE_PASSWORD')

        self.config.fortimanager_host = os.getenv('FORTIMANAGER_HOST')
        self.config.fortimanager_username = os.getenv('FORTIMANAGER_USERNAME')
        self.config.fortimanager_password = os.getenv('FORTIMANAGER_PASSWORD')

        self.config.meraki_api_key = os.getenv('MERAKI_API_KEY')
        self.config.meraki_org_id = os.getenv('MERAKI_ORG_ID')

        # Load application settings
        self.config.debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
        self.config.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # Load paths
        if os.getenv('DATA_DIR'):
            self.config.data_dir = Path(os.getenv('DATA_DIR'))
        if os.getenv('EXPORTS_DIR'):
            self.config.exports_dir = Path(os.getenv('EXPORTS_DIR'))

        # Load enterprise settings
        self.config.enable_ssl_verification = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
        self.config.corporate_proxy = os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
        self.config.certificate_path = os.getenv('CERTIFICATE_PATH')

    def _load_from_file(self, config_file: str):
        """Load configuration from YAML/JSON file"""
        config_path = Path(config_file)

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_file}")
            return

        try:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
            elif config_file.endswith('.json'):
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
            else:
                logger.error(f"Unsupported config file format: {config_file}")
                return

            # Update config object with file values
            for key, value in file_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            self.config_sources.append(f"file:{config_path}")

        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e}")

    def _detect_corporate_environment(self):
        """Detect corporate environment settings (from enhanced-network-api-corporate)"""
        # Check for corporate indicators
        corporate_indicators = [
            '/etc/ssl/certs',  # Linux cert store
            'Zscaler',  # Zscaler proxy
            'Blue Coat',  # Blue Coat proxy
            '.corporate',  # Corporate domain
        ]

        is_corporate = any(indicator in str(os.environ) for indicator in corporate_indicators)

        if is_corporate:
            logger.info("Corporate environment detected")
            self.config.enable_ssl_verification = False  # Often needed in corporate envs

            # Try to find certificate paths
            cert_paths = [
                Path('/etc/ssl/certs/ca-certificates.crt'),
                Path('/etc/ssl/certs/ca-bundle.crt'),
                Path('./corporate-ca.pem')
            ]

            for cert_path in cert_paths:
                if cert_path.exists():
                    self.config.certificate_path = str(cert_path)
                    break

    def _validate_config(self):
        """Validate configuration values"""
        # Create required directories
        for dir_path in [self.config.data_dir, self.config.logs_dir,
                        self.config.exports_dir, self.config.models_dir, self.config.icons_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Validate network settings
        if self.config.default_timeout < 1:
            self.config.default_timeout = 30

        if self.config.concurrent_requests < 1:
            self.config.concurrent_requests = 1

        # Validate renderer setting
        if self.config.renderer not in ['three.js', 'babylon.js']:
            self.config.renderer = 'three.js'

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        if hasattr(self.config, key):
            return getattr(self.config, key)
        return default

    def set(self, key: str, value: Any):
        """Set configuration value"""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
        else:
            logger.warning(f"Unknown configuration key: {key}")

    def save_to_file(self, filepath: str):
        """Save current configuration to file"""
        config_dict = {}
        for key in dir(self.config):
            if not key.startswith('_'):
                value = getattr(self.config, key)
                # Convert Path objects to strings
                if isinstance(value, Path):
                    value = str(value)
                config_dict[key] = value

        try:
            with open(filepath, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
            logger.info(f"Configuration saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def get_network_credentials(self) -> Dict[str, Any]:
        """Get all network credentials"""
        return {
            'fortigate': {
                'host': self.config.fortigate_host,
                'username': self.config.fortigate_username,
                'password': self.config.fortigate_password
            },
            'fortimanager': {
                'host': self.config.fortimanager_host,
                'username': self.config.fortimanager_username,
                'password': self.config.fortimanager_password
            },
            'meraki': {
                'api_key': self.config.meraki_api_key,
                'org_id': self.config.meraki_org_id
            }
        }

    def is_configured(self, service: str) -> bool:
        """Check if a service is properly configured"""
        creds = self.get_network_credentials()

        if service == 'fortigate':
            fg = creds['fortigate']
            return all([fg['host'], fg['username'], fg['password']])

        elif service == 'fortimanager':
            fm = creds['fortimanager']
            return all([fm['host'], fm['username'], fm['password']])

        elif service == 'meraki':
            mk = creds['meraki']
            return bool(mk['api_key'])

        return False


class ConfigValidator:
    """Configuration validation utilities"""

    @staticmethod
    def validate_network_config(config: NetworkConfig) -> List[str]:
        """Validate network configuration"""
        errors = []

        # Check required directories exist
        for dir_path in [config.data_dir, config.logs_dir, config.exports_dir]:
            if not dir_path.exists():
                errors.append(f"Directory does not exist: {dir_path}")

        # Validate timeouts
        if config.default_timeout <= 0:
            errors.append("Default timeout must be positive")

        # Validate concurrent requests
        if config.concurrent_requests <= 0:
            errors.append("Concurrent requests must be positive")

        # Validate renderer
        if config.renderer not in ['three.js', 'babylon.js']:
            errors.append(f"Invalid renderer: {config.renderer}")

        return errors

    @staticmethod
    def validate_credentials(credentials: Dict[str, Any]) -> List[str]:
        """Validate network credentials"""
        errors = []

        # Check credential formats
        for service, creds in credentials.items():
            if service == 'fortigate':
                required = ['host', 'username', 'password']
            elif service == 'fortimanager':
                required = ['host', 'username', 'password']
            elif service == 'meraki':
                required = ['api_key']
            else:
                continue

            for field in required:
                if not creds.get(field):
                    errors.append(f"Missing {service} {field}")

        return errors