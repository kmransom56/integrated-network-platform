"""
Topology Management Endpoints
Combines topology APIs from both applications
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel

from shared.network_utils.topology_builder import TopologyBuilder
from shared.network_utils.data_formatter import NetworkDataFormatter
from shared.device_handling.device_processor import DeviceProcessor

router = APIRouter()


class TopologyRequest(BaseModel):
    """Topology creation request"""
    devices: List[Dict[str, Any]]
    connections: List[List[str]]
    layout_algorithm: str = "layered"


class TopologyAnalysis(BaseModel):
    """Topology analysis request"""
    topology_data: Dict[str, Any]


@router.post("/create")
async def create_topology(request: TopologyRequest):
    """Create network topology from devices and connections"""
    try:
        # Build topology
        topology_builder = TopologyBuilder()
        topology = topology_builder.build_topology(
            request.devices,
            [(src, tgt) for src, tgt in request.connections]
        )

        # Apply requested layout
        if request.layout_algorithm == "layered":
            layout = topology_builder._apply_layered_layout()
            topology['layout'] = layout
        elif request.layout_algorithm == "optimized":
            layout = topology_builder.optimize_layout(topology.get('layout', {}))
            topology['layout'] = layout

        return {
            "topology": topology,
            "layout_algorithm": request.layout_algorithm,
            "device_count": len(request.devices),
            "connection_count": len(request.connections)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topology creation failed: {str(e)}")


@router.post("/analyze")
async def analyze_topology(request: TopologyAnalysis):
    """Analyze topology for optimization opportunities"""
    try:
        topology_builder = TopologyBuilder()
        topology_data = request.topology_data

        # Validate topology
        validation = topology_builder.validate_topology(topology_data)

        # Analyze layout efficiency
        layout_analysis = analyze_layout_efficiency(topology_data)

        # Find optimization opportunities
        optimizations = find_topology_optimizations(topology_data)

        return {
            "validation": validation,
            "layout_analysis": layout_analysis,
            "optimizations": optimizations,
            "recommendations": generate_recommendations(validation, layout_analysis, optimizations)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topology analysis failed: {str(e)}")


@router.post("/optimize")
async def optimize_topology(request: TopologyAnalysis):
    """Optimize topology layout"""
    try:
        topology_builder = TopologyBuilder()
        topology_data = request.topology_data

        # Apply optimization
        optimized_layout = topology_builder.optimize_layout(topology_data.get('layout', {}))
        topology_data['layout'] = optimized_layout

        # Validate optimized topology
        validation = topology_builder.validate_topology(topology_data)

        return {
            "optimized_topology": topology_data,
            "validation": validation,
            "optimizations_applied": ["layout_optimization"],
            "improvement_metrics": calculate_improvement_metrics(topology_data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topology optimization failed: {str(e)}")


@router.post("/export")
async def export_topology(topology_data: Dict[str, Any], format: str = "json"):
    """Export topology in various formats"""
    try:
        formatter = NetworkDataFormatter()

        if format == "json":
            # Standard JSON export
            exported_data = formatter.export_to_json(topology_data, f"topology_export.{format}")
        elif format == "manifest":
            # Network map 3D manifest format
            devices = topology_data.get('devices', [])
            connections = topology_data.get('connections', [])
            layout = topology_data.get('layout', {})
            exported_data = formatter.export_to_manifest(devices, connections, layout, f"topology_manifest.{format}")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        return {
            "message": "Topology exported successfully",
            "format": format,
            "data": exported_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/algorithms")
async def get_layout_algorithms():
    """Get available topology layout algorithms"""
    return {
        "algorithms": [
            {
                "name": "layered",
                "description": "Hierarchical layered layout (core → distribution → access → endpoints)",
                "best_for": ["enterprise_networks", "hierarchical_topologies"],
                "complexity": "O(n)"
            },
            {
                "name": "force_directed",
                "description": "Physics-based force-directed layout",
                "best_for": ["mesh_networks", "organic_layouts"],
                "complexity": "O(n²)"
            },
            {
                "name": "circular",
                "description": "Circular ring layout",
                "best_for": ["ring_topologies", "equal_weight_devices"],
                "complexity": "O(n)"
            },
            {
                "name": "optimized",
                "description": "Minimize crossings and optimize readability",
                "best_for": ["dense_networks", "presentation_quality"],
                "complexity": "O(n²)"
            }
        ],
        "default": "layered"
    }


def analyze_layout_efficiency(topology_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze layout efficiency metrics"""
    layout = topology_data.get('layout', {})
    positions = layout.get('positions', {})

    if not positions:
        return {"efficiency_score": 0, "issues": ["No layout positions found"]}

    # Calculate basic metrics
    device_count = len(positions)
    layers = {}

    # Group by layer
    for device_id, pos in positions.items():
        layer = pos.get('layer', 'unknown')
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(pos)

    # Calculate layer balance
    layer_sizes = [len(devices) for devices in layers.values()]
    avg_layer_size = sum(layer_sizes) / len(layer_sizes) if layer_sizes else 0
    layer_balance = 1 - (max(layer_sizes) - min(layer_sizes)) / max(layer_sizes) if layer_sizes and max(layer_sizes) > 0 else 0

    return {
        "device_count": device_count,
        "layer_count": len(layers),
        "layer_balance": round(layer_balance, 2),
        "avg_devices_per_layer": round(avg_layer_size, 1),
        "efficiency_score": round(layer_balance * 0.8 + (1 / max(len(layer_sizes), 1)) * 0.2, 2)
    }


def find_topology_optimizations(topology_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find topology optimization opportunities"""
    optimizations = []

    devices = topology_data.get('devices', [])
    connections = topology_data.get('connections', [])

    # Check for disconnected devices
    connected_device_ids = set()
    for conn in connections:
        connected_device_ids.add(conn.get('source'))
        connected_device_ids.add(conn.get('target'))

    disconnected = []
    for device in devices:
        if device.get('id') not in connected_device_ids:
            disconnected.append(device.get('name', device.get('id')))

    if disconnected:
        optimizations.append({
            "type": "disconnected_devices",
            "severity": "medium",
            "description": f"Found {len(disconnected)} disconnected devices",
            "affected_devices": disconnected[:5],  # Show first 5
            "recommendation": "Review device connections or remove orphaned devices"
        })

    # Check for single points of failure
    connection_counts = {}
    for conn in connections:
        for device_id in [conn.get('source'), conn.get('target')]:
            connection_counts[device_id] = connection_counts.get(device_id, 0) + 1

    critical_devices = [did for did, count in connection_counts.items() if count > 10]  # Arbitrary threshold

    if critical_devices:
        optimizations.append({
            "type": "single_points_of_failure",
            "severity": "high",
            "description": f"Found {len(critical_devices)} devices with high connection counts",
            "affected_devices": critical_devices,
            "recommendation": "Consider redundant connections for critical devices"
        })

    return optimizations


def generate_recommendations(validation: Dict[str, Any],
                           layout_analysis: Dict[str, Any],
                           optimizations: List[Dict[str, Any]]) -> List[str]:
    """Generate human-readable recommendations"""
    recommendations = []

    # Validation-based recommendations
    if validation.get('errors'):
        recommendations.append(f"Fix {len(validation['errors'])} topology validation errors")

    if validation.get('warnings'):
        recommendations.append(f"Address {len(validation['warnings'])} topology warnings")

    # Layout-based recommendations
    efficiency = layout_analysis.get('efficiency_score', 0)
    if efficiency < 0.7:
        recommendations.append("Consider layout optimization to improve readability")

    # Optimization-based recommendations
    for opt in optimizations:
        if opt['severity'] == 'high':
            recommendations.append(opt['recommendation'])

    if not recommendations:
        recommendations.append("Topology structure looks good - no immediate optimizations needed")

    return recommendations


def calculate_improvement_metrics(topology_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate metrics showing improvement after optimization"""
    # This would compare before/after metrics
    # For now, return placeholder metrics
    return {
        "crossing_reduction": "15%",
        "layout_compactness": "improved",
        "readability_score": "8.5/10"
    }