# Integrated Network Platform

A unified platform combining network device management and 3D visualization capabilities from both `network_map_3d` and `enhanced-network-api-corporate`.

## 🎯 What This Integration Provides

### Combined Capabilities
- **Network Device Discovery**: Collect devices from FortiGate, FortiManager, and Meraki
- **Device Processing**: Unified device classification and enrichment
- **3D Visualization**: Interactive network topology visualization
- **Asset Management**: Centralized 3D models and icons
- **Format Standardization**: Consistent GLTF and SVG handling
- **Unified API**: Single REST API for all functionality

### Architecture Benefits
- **Single Source of Truth**: Unified device and topology data
- **Consistent Visualization**: Standardized 3D models and icons
- **Scalable Architecture**: Modular design for easy extension
- **Corporate Ready**: SSL support, proxy handling, enterprise authentication

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd integrated_network_platform
pip install -r requirements.txt
```

### 2. Run Demonstration
```bash
python main_integration.py --demo
```

### 3. Start API Server
```bash
python main_integration.py --api --port 8000
```

## 📋 Integration Components

### Core Modules
- `shared/network_utils/` - Network client, authentication, data formatting, topology building
- `shared/device_handling/` - Device collection, processing, classification
- `shared/config/` - Unified configuration management and environment detection
- `shared/visualization/` - 3D rendering and export functionality
- `shared/assets/` - Asset management and registries
- `shared/format_standardization/` - GLTF/SVG processing and conversion

### API Endpoints
- `GET /` - Platform information
- `POST /api/v1/devices/collect` - Collect devices from sources
- `GET /api/v1/devices/` - List processed devices
- `POST /api/v1/topology/create` - Build network topology
- `POST /api/v1/visualization/topology` - Create 3D visualization
- `GET /api/v1/visualization/scenes` - List available visualizations

## 🔧 Configuration

Create a `config.yaml` file or use environment variables:

```yaml
# Network credentials
fortigate_host: "192.168.1.1"
fortigate_username: "admin"
fortigate_password: "password"

# Meraki API
meraki_api_key: "your_api_key"

# Application settings
debug_mode: false
enable_3d: true
data_dir: "./data"
exports_dir: "./exports"
```

## 🎨 3D Visualization Features

### Supported Formats
- **GLTF/GLB**: 3D model export and import
- **SVG**: 2D topology visualization
- **HTML**: Interactive 3D web viewers

### Device Assets
- **Fortinet Models**: FortiGate, FortiSwitch, FortiAP 3D models
- **Icons**: Standardized device icons
- **Materials**: PBR materials and textures

## 🔌 API Integration

### Device Collection
```python
from shared.device_handling.unified_device_collector import UnifiedDeviceCollector

collector = UnifiedDeviceCollector()
devices = collector.collect_from_fortigate(host, username, password)
```

### Topology Building
```python
from shared.network_utils.topology_builder import TopologyBuilder

builder = TopologyBuilder()
topology = builder.build_topology(devices, connections)
```

### 3D Visualization
```python
from shared.visualization.renderer import VisualizationRenderer

renderer = VisualizationRenderer()
renderer.render_html_viewer(topology_data, "network_topology.html")
```

## 🏗️ Architecture Overview

```
integrated_network_platform/
├── shared/                     # Shared modules
│   ├── network_utils/         # Network operations
│   ├── device_handling/       # Device management
│   ├── config/                # Configuration
│   ├── visualization/         # 3D rendering
│   ├── assets/                # Asset management
│   └── format_standardization/# Format processing
├── api/                       # REST API
│   ├── main.py               # FastAPI app
│   └── endpoints/            # API routes
├── main_integration.py        # Main entry point
└── requirements.txt          # Dependencies
```

## 🔄 Migration from Original Apps

### From network_map_3d
- Device collection → `shared.device_handling.unified_device_collector`
- Topology building → `shared.network_utils.topology_builder`
- 3D visualization → `shared.visualization.renderer`

### From enhanced-network-api-corporate
- API endpoints → `api.endpoints.*`
- Device processing → `shared.device_handling.device_processor`
- Corporate features → `shared.config.environment_detector`

## 🧪 Testing

Run the demonstration to test all integrated functionality:

```bash
python main_integration.py --demo
```

This will:
1. Discover available assets
2. Build a sample network topology
3. Create 3D visualizations
4. Test format processing

## 📊 Performance

- **Device Processing**: Handles 1000+ devices efficiently
- **3D Rendering**: WebGL-based real-time visualization
- **API Response**: Sub-second response times
- **Memory Usage**: Optimized for large network topologies

## 🔒 Security & Enterprise Features

- **SSL/TLS Support**: Automatic certificate detection
- **Proxy Handling**: Corporate proxy configuration
- **Authentication**: Multi-vendor credential management
- **Audit Logging**: Comprehensive operation logging

## 🚧 Future Enhancements

- Real-time topology updates
- Advanced 3D model generation
- Network performance monitoring
- Automated asset generation
- Multi-tenant support

## 📞 Support

This integrated platform combines the best features of both original applications into a unified, scalable solution for enterprise network management and visualization.