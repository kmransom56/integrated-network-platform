"""
SVG Processor
Standardizes SVG icon formats for consistent visualization
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class SVGProcessor:
    """
    SVG processor for standardizing icon formats
    Combines SVG processing from both applications
    """

    def __init__(self):
        self.namespace = {'svg': 'http://www.w3.org/2000/svg'}

    def validate_svg(self, svg_path: Path) -> Dict[str, Any]:
        """Validate an SVG file"""
        validation_result = {
            'valid': False,
            'issues': [],
            'recommendations': [],
            'dimensions': None,
            'viewBox': None
        }

        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # Check if it's actually an SVG
            if root.tag != '{http://www.w3.org/2000/svg}svg':
                validation_result['issues'].append('File is not a valid SVG')
                return validation_result

            # Validate required attributes
            width = root.get('width')
            height = root.get('height')
            viewBox = root.get('viewBox')

            if not width or not height:
                validation_result['issues'].append('Missing width or height attributes')

            if not viewBox:
                validation_result['recommendations'].append('Consider adding viewBox for scalability')

            # Parse dimensions
            if width and height:
                validation_result['dimensions'] = {
                    'width': self._parse_svg_dimension(width),
                    'height': self._parse_svg_dimension(height)
                }

            # Parse viewBox
            if viewBox:
                try:
                    vb_parts = viewBox.split()
                    if len(vb_parts) == 4:
                        validation_result['viewBox'] = {
                            'x': float(vb_parts[0]),
                            'y': float(vb_parts[1]),
                            'width': float(vb_parts[2]),
                            'height': float(vb_parts[3])
                        }
                except ValueError:
                    validation_result['issues'].append('Invalid viewBox format')

            # Check for problematic elements
            problematic_elements = ['script', 'foreignObject', 'iframe']
            for elem in root.iter():
                if elem.tag.split('}')[-1] in problematic_elements:
                    validation_result['issues'].append(f'Potentially unsafe element: {elem.tag}')

            validation_result['valid'] = len(validation_result['issues']) == 0

            return validation_result

        except ET.ParseError as e:
            validation_result['issues'].append(f'XML parsing error: {str(e)}')
            return validation_result
        except Exception as e:
            validation_result['issues'].append(f'Validation error: {str(e)}')
            return validation_result

    def _parse_svg_dimension(self, dimension: str) -> Optional[float]:
        """Parse SVG dimension string"""
        # Remove units and convert to float
        match = re.match(r'(\d*\.?\d+)', dimension)
        if match:
            return float(match.group(1))
        return None

    def standardize_svg(self, svg_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """Standardize an SVG file"""
        if not output_path:
            output_path = svg_path.parent / f"{svg_path.stem}_standardized.svg"

        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # Apply standardization
            self._apply_svg_standardization(root)

            # Write standardized SVG
            tree.write(output_path, encoding='unicode', xml_declaration=True)

            logger.info(f"Standardized SVG saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to standardize SVG {svg_path}: {e}")
            return None

    def _apply_svg_standardization(self, root):
        """Apply standardization to SVG root element"""
        # Ensure consistent namespace
        if not root.tag.startswith('{http://www.w3.org/2000/svg}'):
            root.tag = f"{{http://www.w3.org/2000/svg}}{root.tag.split('}')[-1]}"

        # Add standard attributes
        root.set('xmlns', 'http://www.w3.org/2000/svg')

        # Ensure viewBox exists
        if 'viewBox' not in root.attrib:
            width = root.get('width', '64')
            height = root.get('height', '64')
            root.set('viewBox', f"0 0 {width} {height}")

        # Standardize dimensions to pixels if using other units
        for attr in ['width', 'height']:
            if attr in root.attrib:
                value = root.get(attr)
                if value and not value.endswith('px') and value.replace('.', '').isdigit():
                    root.set(attr, f"{value}px")

        # Clean up unnecessary attributes
        attrs_to_remove = ['xlink:href', 'xml:base', 'xml:lang']
        for attr in attrs_to_remove:
            if attr in root.attrib:
                del root.attrib[attr]

    def optimize_svg(self, svg_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """Optimize SVG for smaller file size and better performance"""
        if not output_path:
            output_path = svg_path.parent / f"{svg_path.stem}_optimized.svg"

        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # Apply optimizations
            self._apply_svg_optimizations(root)

            # Write optimized SVG
            # Use minified output
            optimized_xml = ET.tostring(root, encoding='unicode', method='xml')

            # Simple minification
            optimized_xml = re.sub(r'\s+', ' ', optimized_xml)
            optimized_xml = re.sub(r'>\s+<', '><', optimized_xml)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(optimized_xml)

            logger.info(f"Optimized SVG saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to optimize SVG {svg_path}: {e}")
            return None

    def _apply_svg_optimizations(self, root):
        """Apply optimization transformations to SVG"""
        # Remove comments
        for comment in root.findall('.//comment()'):
            comment.getparent().remove(comment)

        # Remove unnecessary groups
        self._remove_unnecessary_groups(root)

        # Simplify transforms
        self._simplify_transforms(root)

        # Remove default values
        self._remove_defaults(root)

    def _remove_unnecessary_groups(self, element):
        """Remove unnecessary group elements"""
        for child in list(element):
            if child.tag.endswith('g') and not child.attrib and len(child) == 1:
                # Group with no attributes and single child can be flattened
                grandchild = child[0]
                element.append(grandchild)
                element.remove(child)
                # Continue processing
                self._remove_unnecessary_groups(element)
            else:
                self._remove_unnecessary_groups(child)

    def _simplify_transforms(self, element):
        """Simplify transform attributes"""
        for child in element:
            if 'transform' in child.attrib:
                transform = child.get('transform')
                # This would implement transform simplification
                # For now, keep as-is
            self._simplify_transforms(child)

    def _remove_defaults(self, element):
        """Remove default attribute values"""
        default_attrs = {
            'fill': '#000000',
            'stroke': 'none',
            'stroke-width': '1',
            'opacity': '1'
        }

        for child in list(element):
            for attr, default_value in default_attrs.items():
                if child.get(attr) == default_value:
                    del child.attrib[attr]
            self._remove_defaults(child)

    def create_svg_sprite(self, svg_paths: List[Path], output_path: Path) -> Optional[Path]:
        """Create an SVG sprite from multiple SVG files"""
        try:
            sprite_root = ET.Element("svg", {
                "xmlns": "http://www.w3.org/2000/svg",
                "style": "display: none;"
            })

            for svg_path in svg_paths:
                try:
                    tree = ET.parse(svg_path)
                    root = tree.getroot()

                    # Create symbol element
                    symbol_id = svg_path.stem
                    symbol = ET.SubElement(sprite_root, "symbol", {
                        "id": symbol_id,
                        "viewBox": root.get("viewBox", "0 0 64 64")
                    })

                    # Copy contents
                    for child in root:
                        symbol.append(child)

                except Exception as e:
                    logger.warning(f"Failed to process {svg_path}: {e}")
                    continue

            # Write sprite
            tree = ET.ElementTree(sprite_root)
            tree.write(output_path, encoding='unicode', xml_declaration=True)

            logger.info(f"SVG sprite created with {len(svg_paths)} symbols")
            return output_path

        except Exception as e:
            logger.error(f"Failed to create SVG sprite: {e}")
            return None

    def convert_svg_to_icon(self, svg_path: Path, size: int = 64, output_path: Optional[Path] = None) -> Optional[Path]:
        """Convert SVG to standardized icon format"""
        if not output_path:
            output_path = svg_path.parent / f"{svg_path.stem}_icon.svg"

        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # Standardize to square icon
            root.set('width', str(size))
            root.set('height', str(size))
            root.set('viewBox', f"0 0 {size} {size}")

            # Ensure it's optimized
            self._apply_svg_optimizations(root)

            # Write icon
            tree.write(output_path, encoding='unicode', xml_declaration=True)

            logger.info(f"SVG icon created: {size}x{size}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to convert SVG to icon: {e}")
            return None

    def batch_process_svgs(self, svg_directory: Path, operations: List[str]) -> Dict[str, Any]:
        """Batch process SVG files in a directory"""
        results = {
            'processed': 0,
            'failed': 0,
            'operations': operations,
            'files': []
        }

        svg_files = list(svg_directory.glob("*.svg"))
        results['total'] = len(svg_files)

        for svg_file in svg_files:
            file_results = {'file': str(svg_file), 'operations': {}}

            for operation in operations:
                try:
                    if operation == 'validate':
                        validation = self.validate_svg(svg_file)
                        file_results['operations']['validate'] = validation['valid']
                    elif operation == 'standardize':
                        output = self.standardize_svg(svg_file)
                        file_results['operations']['standardize'] = output is not None
                    elif operation == 'optimize':
                        output = self.optimize_svg(svg_file)
                        file_results['operations']['optimize'] = output is not None
                    else:
                        file_results['operations'][operation] = False
                except Exception as e:
                    file_results['operations'][operation] = f"Error: {str(e)}"
                    results['failed'] += 1

            results['files'].append(file_results)
            if all(op_result for op_result in file_results['operations'].values()):
                results['processed'] += 1

        return results