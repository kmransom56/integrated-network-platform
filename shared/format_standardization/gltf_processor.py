"""
GLTF Processor
Standardizes GLTF 3D model formats for consistent visualization
"""

import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class GLTFProcessor:
    """
    GLTF processor for standardizing 3D models
    Combines GLTF processing from both applications
    """

    def __init__(self):
        self.supported_versions = ["2.0"]
        self.required_extensions = []

    def validate_gltf(self, gltf_path: Path) -> Dict[str, Any]:
        """Validate a GLTF file"""
        validation_result = {
            'valid': False,
            'version': None,
            'issues': [],
            'recommendations': []
        }

        try:
            if gltf_path.suffix.lower() == '.glb':
                # Binary GLTF - would need proper parsing
                validation_result['issues'].append('GLB validation not yet implemented')
                return validation_result
            elif gltf_path.suffix.lower() == '.gltf':
                # JSON GLTF
                with open(gltf_path, 'r', encoding='utf-8') as f:
                    gltf_data = json.load(f)

                return self._validate_gltf_json(gltf_data)
            else:
                validation_result['issues'].append(f'Unsupported file extension: {gltf_path.suffix}')
                return validation_result

        except Exception as e:
            validation_result['issues'].append(f'Failed to parse GLTF: {str(e)}')
            return validation_result

    def _validate_gltf_json(self, gltf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GLTF JSON structure"""
        result = {
            'valid': True,
            'version': gltf_data.get('asset', {}).get('version'),
            'issues': [],
            'recommendations': []
        }

        # Check required fields
        required_fields = ['asset', 'scene']
        for field in required_fields:
            if field not in gltf_data:
                result['issues'].append(f'Missing required field: {field}')
                result['valid'] = False

        # Validate asset version
        asset = gltf_data.get('asset', {})
        version = asset.get('version')
        if version not in self.supported_versions:
            result['issues'].append(f'Unsupported GLTF version: {version}')
            result['valid'] = False

        # Check for scenes
        scenes = gltf_data.get('scenes', [])
        if not scenes:
            result['issues'].append('No scenes defined')
            result['valid'] = False

        # Validate scene references
        default_scene = gltf_data.get('scene', 0)
        if default_scene >= len(scenes):
            result['issues'].append('Invalid default scene index')
            result['valid'] = False

        # Check nodes
        nodes = gltf_data.get('nodes', [])
        if not nodes:
            result['recommendations'].append('No nodes defined - empty model')

        # Validate node hierarchies
        for i, node in enumerate(nodes):
            issues = self._validate_node(node, i, nodes)
            result['issues'].extend(issues)

        return result

    def _validate_node(self, node: Dict[str, Any], index: int, all_nodes: List[Dict[str, Any]]) -> List[str]:
        """Validate a single node"""
        issues = []

        # Check children references
        children = node.get('children', [])
        for child_index in children:
            if child_index >= len(all_nodes):
                issues.append(f'Node {index}: Invalid child reference {child_index}')

        return issues

    def standardize_gltf(self, gltf_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """Standardize a GLTF file to ensure consistency"""
        if not output_path:
            output_path = gltf_path.parent / f"{gltf_path.stem}_standardized{gltf_path.suffix}"

        try:
            if gltf_path.suffix.lower() == '.gltf':
                with open(gltf_path, 'r', encoding='utf-8') as f:
                    gltf_data = json.load(f)

                # Apply standardization
                standardized_data = self._apply_gltf_standardization(gltf_data)

                # Write standardized version
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(standardized_data, f, indent=2, ensure_ascii=False)

                logger.info(f"Standardized GLTF saved to {output_path}")
                return output_path
            else:
                # For GLB files, just copy for now
                import shutil
                shutil.copy2(gltf_path, output_path)
                return output_path

        except Exception as e:
            logger.error(f"Failed to standardize GLTF {gltf_path}: {e}")
            return None

    def _apply_gltf_standardization(self, gltf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply standardization transformations to GLTF data"""
        # Ensure consistent asset metadata
        if 'asset' not in gltf_data:
            gltf_data['asset'] = {}

        asset = gltf_data['asset']
        asset['version'] = "2.0"
        asset['generator'] = "Integrated Network Platform GLTF Processor"
        asset['copyright'] = f"Generated {datetime.now().isoformat()}"

        # Ensure scene exists
        if 'scenes' not in gltf_data:
            gltf_data['scenes'] = [{}]

        if 'scene' not in gltf_data:
            gltf_data['scene'] = 0

        # Add default scene if empty
        scenes = gltf_data['scenes']
        if not scenes:
            scenes.append({})

        # Ensure nodes array exists
        if 'nodes' not in gltf_data:
            gltf_data['nodes'] = []

        # Standardize node structure
        for node in gltf_data.get('nodes', []):
            self._standardize_node(node)

        return gltf_data

    def _standardize_node(self, node: Dict[str, Any]):
        """Standardize a node's structure"""
        # Ensure name exists
        if 'name' not in node:
            node['name'] = f"Node_{id(node)}"

        # Ensure translation is present
        if 'translation' not in node:
            node['translation'] = [0.0, 0.0, 0.0]

        # Ensure scale is present
        if 'scale' not in node:
            node['scale'] = [1.0, 1.0, 1.0]

        # Ensure rotation is present
        if 'rotation' not in node:
            node['rotation'] = [0.0, 0.0, 0.0, 1.0]  # Identity quaternion

    def optimize_gltf(self, gltf_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """Optimize GLTF file for better performance"""
        if not output_path:
            output_path = gltf_path.parent / f"{gltf_path.stem}_optimized{gltf_path.suffix}"

        try:
            if gltf_path.suffix.lower() == '.gltf':
                with open(gltf_path, 'r', encoding='utf-8') as f:
                    gltf_data = json.load(f)

                # Apply optimizations
                optimized_data = self._apply_gltf_optimizations(gltf_data)

                # Write optimized version
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(optimized_data, f, indent=2, ensure_ascii=False)

                logger.info(f"Optimized GLTF saved to {output_path}")
                return output_path
            else:
                # For GLB files, just copy for now
                import shutil
                shutil.copy2(gltf_path, output_path)
                return output_path

        except Exception as e:
            logger.error(f"Failed to optimize GLTF {gltf_path}: {e}")
            return None

    def _apply_gltf_optimizations(self, gltf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply optimization transformations to GLTF data"""
        # Remove unused data
        self._remove_unused_elements(gltf_data)

        # Compress floating point values
        self._compress_floats(gltf_data)

        # Optimize node hierarchy
        self._optimize_node_hierarchy(gltf_data)

        return gltf_data

    def _remove_unused_elements(self, gltf_data: Dict[str, Any]):
        """Remove unused elements from GLTF"""
        # This would implement logic to remove unused buffers, images, etc.
        # For now, it's a placeholder
        pass

    def _compress_floats(self, gltf_data: Dict[str, Any]):
        """Compress floating point precision"""
        def compress_float_list(float_list, precision=6):
            return [round(f, precision) for f in float_list]

        # Compress node transformations
        for node in gltf_data.get('nodes', []):
            if 'translation' in node:
                node['translation'] = compress_float_list(node['translation'])
            if 'scale' in node:
                node['scale'] = compress_float_list(node['scale'])
            if 'rotation' in node:
                node['rotation'] = compress_float_list(node['rotation'])

    def _optimize_node_hierarchy(self, gltf_data: Dict[str, Any]):
        """Optimize node hierarchy for better performance"""
        # This would implement node hierarchy optimization
        # For now, it's a placeholder
        pass

    def merge_gltf_models(self, model_paths: List[Path], output_path: Path) -> Optional[Path]:
        """Merge multiple GLTF models into one"""
        try:
            merged_data = {
                'asset': {
                    'version': '2.0',
                    'generator': 'Integrated Network Platform GLTF Merger'
                },
                'scenes': [{'nodes': []}],
                'scene': 0,
                'nodes': []
            }

            node_offset = 0
            for model_path in model_paths:
                if model_path.suffix.lower() == '.gltf':
                    with open(model_path, 'r', encoding='utf-8') as f:
                        model_data = json.load(f)

                    # Merge nodes
                    model_nodes = model_data.get('nodes', [])
                    for node in model_nodes:
                        # Offset node indices if needed
                        merged_data['nodes'].append(node)

                    # Add to scene
                    scene_nodes = merged_data['scenes'][0]['nodes']
                    scene_nodes.extend(range(node_offset, node_offset + len(model_nodes)))
                    node_offset += len(model_nodes)

            # Save merged model
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Merged GLTF models saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to merge GLTF models: {e}")
            return None