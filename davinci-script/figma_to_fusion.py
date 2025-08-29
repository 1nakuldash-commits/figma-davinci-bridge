#!/usr/bin/env python3
"""
DaVinci Resolve Script: Import Figma Elements to Fusion
This script fetches JSON data from the Flask bridge and creates a Fusion composition
"""

import json
import urllib.request
import urllib.error
import base64
import os
import tempfile
from typing import Dict, List, Any, Optional
import sys

# DaVinci Resolve API imports
try:
    import DaVinciResolveScript as dvs
    resolve = dvs.scriptapp("Resolve")
except ImportError:
    # This will be caught by the safety check in main()
    resolve = None

class FigmaToFusion:
    def __init__(self, bridge_url: str = "http://localhost:5000"):
        self.bridge_url = bridge_url
        self.resolve = resolve
        self.project_manager = None
        self.project = None
        self.media_pool = None
        self.composition = None
        self.temp_image_files = []
        
        self.node_x = 0
        self.node_y = 0
        self.node_spacing_x = 150
        self.node_spacing_y = 100
        
        self.fusion_width = 1920
        self.fusion_height = 1080
        
        if self.resolve:
            self.initialize_resolve()
    
    def initialize_resolve(self):
        """Initialize DaVinci Resolve components and get the active composition."""
        try:
            self.project_manager = self.resolve.GetProjectManager()
            self.project = self.project_manager.GetCurrentProject()
            
            if not self.project:
                print("Error: No project is currently open in DaVinci Resolve.")
                return False
            
            self.media_pool = self.project.GetMediaPool()
            
            fusion = self.resolve.Fusion()
            if not fusion:
                print("Error: Could not get the Fusion object from DaVinci Resolve.")
                return False

            self.composition = fusion.GetCurrentComp()

            if not self.composition:
                print("Error: No active Fusion composition.")
                print("Please open a timeline and go to the Fusion page before running the script.")
                return False

            self.fusion_width = self.composition.GetAttrs("COMPN_Width")
            self.fusion_height = self.composition.GetAttrs("COMPN_Height")

            print(f"Successfully connected to project: {self.project.GetName()}")
            print(f"Working with active composition: {self.composition.GetAttrs('COMPS_Name')} ({self.fusion_width}x{self.fusion_height})")
            return True
            
        except Exception as e:
            print(f"An unexpected error occurred during initialization: {e}")
            return False
    
    def fetch_figma_data(self, data_id: Optional[str] = None) -> Optional[Dict]:
        """Fetch JSON data from Flask bridge using built-in urllib"""
        try:
            url = f"{self.bridge_url}/get_data"
            if data_id:
                url += f"?id={data_id}"
            
            print(f"Fetching data from: {url}")
            
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    response_text = response.read().decode('utf-8')
                    result = json.loads(response_text)
                    if result.get('success'):
                        return result['data']
                    else:
                        print(f"Bridge server error: {result.get('error', 'Unknown error')}")
                else:
                    print(f"HTTP Error {response.status}: {response.reason}")

        except urllib.error.URLError as e:
            if isinstance(e.reason, ConnectionRefusedError):
                print("Error: Could not connect to Flask bridge server. Is it running on localhost:5000?")
            else:
                print(f"Error: Could not connect to the server. Reason: {e.reason}")
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON response from the server.")
        except Exception as e:
            print(f"An unexpected error occurred while fetching data: {e}")

        return None
    
    def save_base64_image(self, base64_data: str, element_name: str) -> Optional[str]:
        """Save base64 image data to temporary file"""
        try:
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            image_data = base64.b64decode(base64_data)
            temp_dir = tempfile.gettempdir()
            safe_name = "".join(c for c in element_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            temp_file = os.path.join(temp_dir, f"figma_{safe_name}_{len(self.temp_image_files)}.png")
            with open(temp_file, 'wb') as f:
                f.write(image_data)
            self.temp_image_files.append(temp_file)
            return temp_file
        except Exception as e:
            print(f"Error saving image for {element_name}: {e}")
            return None
    
    def get_next_node_position(self) -> tuple:
        pos = (self.node_x, self.node_y)
        self.node_x += self.node_spacing_x
        if self.node_x > 2000:
            self.node_x = 0
            self.node_y += self.node_spacing_y
        return pos
    
    def figma_to_fusion_coords(self, figma_x: float, figma_y: float, figma_width: float, figma_height: float, element_width: float, element_height: float) -> Dict:
        center_x = (figma_x + element_width / 2) / figma_width
        center_y = (figma_y + element_height / 2) / figma_height
        fusion_x = center_x
        fusion_y = 1.0 - center_y
        scale_x = element_width / figma_width
        scale_y = element_height / figma_height
        return {'Center': [fusion_x, fusion_y], 'Size': min(scale_x, scale_y)}
    
    def create_loader_node(self, image_path: str, element: Dict, figma_canvas: Dict) -> Optional[Any]:
        node_name = f"Loader_{element['name']}"
        if not self.resolve: return f"loader_{element['name']}"
        pos_x, pos_y = self.get_next_node_position()
        loader = self.composition.AddTool("Loader", pos_x, pos_y)
        loader.SetAttrs({"TOOLS_Name": node_name})
        loader.Clip = image_path
        transform_data = self.figma_to_fusion_coords(element['position']['x'], element['position']['y'], figma_canvas['width'], figma_canvas['height'], element['size']['width'], element['size']['height'])
        loader.Center = transform_data['Center']
        if element.get('opacity', 1.0) < 1.0: loader.Opacity = element['opacity']
        return loader
    
    def create_text_node(self, element: Dict, figma_canvas: Dict) -> Optional[Any]:
        node_name = f"Text_{element['name']}"
        if not self.resolve: return f"text_{element['name']}"
        pos_x, pos_y = self.get_next_node_position()
        text_node = self.composition.AddTool("Text+", pos_x, pos_y)
        text_node.SetAttrs({"TOOLS_Name": node_name})
        if element.get('characters'): text_node.StyledText = element['characters']
        transform_data = self.figma_to_fusion_coords(element['position']['x'], element['position']['y'], figma_canvas['width'], figma_canvas['height'], element['size']['width'], element['size']['height'])
        text_node.Center = transform_data['Center']
        if element.get('fontSize') and isinstance(element['fontSize'], (int, float)): text_node.Size = element['fontSize'] / 16.0
        if element.get('opacity', 1.0) < 1.0: text_node.Opacity = element['opacity']
        return text_node
    
    def create_rectangle_node(self, element: Dict, figma_canvas: Dict) -> Optional[Any]:
        node_name = f"Rect_{element['name']}"
        if not self.resolve: return f"rect_{element['name']}"
        fills, strokes = element.get('fills', []), element.get('strokes', [])
        fill_node, stroke_node = None, None
        pos_x, pos_y = self.get_next_node_position()
        if strokes:
            stroke_color = strokes[0].get('color', {})
            stroke_node = self.composition.AddTool("sRectangle", pos_x, pos_y)
            stroke_node.SetAttrs({"TOOLS_Name": f"{node_name}_Stroke"})
            transform_data = self.figma_to_fusion_coords(element['position']['x'], element['position']['y'], figma_canvas['width'], figma_canvas['height'], element['size']['width'], element['size']['height'])
            stroke_node.Center, stroke_node.Width, stroke_node.Height = transform_data['Center'], element['size']['width'] / self.fusion_width, element['size']['height'] / self.fusion_height
            stroke_node.Red, stroke_node.Green, stroke_node.Blue, stroke_node.Alpha = stroke_color.get('r', 0), stroke_color.get('g', 0), stroke_color.get('b', 0), stroke_color.get('a', 1)
            if element.get('cornerRadius'): stroke_node.CornerRadius = element['cornerRadius'] / min(element['size']['width'], element['size']['height'])
        if fills and fills[0].get('visible', True):
            fill_color = fills[0].get('color', {})
            fill_pos_x, fill_pos_y = (pos_x + 20, pos_y + 20) if stroke_node else (pos_x, pos_y)
            fill_node = self.composition.AddTool("sRectangle", fill_pos_x, fill_pos_y)
            fill_node.SetAttrs({"TOOLS_Name": f"{node_name}_Fill"})
            transform_data = self.figma_to_fusion_coords(element['position']['x'], element['position']['y'], figma_canvas['width'], figma_canvas['height'], element['size']['width'], element['size']['height'])
            fill_node.Center = transform_data['Center']
            stroke_weight = element.get('strokeWeight') or 0 if stroke_node else 0
            fill_node.Width, fill_node.Height = (element['size']['width'] - 2 * stroke_weight) / self.fusion_width, (element['size']['height'] - 2 * stroke_weight) / self.fusion_height
            fill_node.Red, fill_node.Green, fill_node.Blue, fill_node.Alpha = fill_color.get('r', 1), fill_color.get('g', 1), fill_color.get('b', 1), fill_color.get('a', 1)
            corner_radius = element.get('cornerRadius')
            if corner_radius is not None:
                fill_node.CornerRadius = (corner_radius - stroke_weight) / min(element['size']['width'], element['size']['height'])
        if stroke_node and fill_node: return self.create_merge_node([stroke_node, fill_node], name=node_name)
        return fill_node or stroke_node

    def create_ellipse_node(self, element: Dict, figma_canvas: Dict) -> Optional[Any]:
        node_name = f"Ellipse_{element['name']}"
        if not self.resolve: return f"ellipse_{element['name']}"
        fills, strokes = element.get('fills', []), element.get('strokes', [])
        fill_node, stroke_node = None, None
        pos_x, pos_y = self.get_next_node_position()
        if strokes:
            stroke_color = strokes[0].get('color', {})
            stroke_node = self.composition.AddTool("sEllipse", pos_x, pos_y)
            stroke_node.SetAttrs({"TOOLS_Name": f"{node_name}_Stroke"})
            transform_data = self.figma_to_fusion_coords(element['position']['x'], element['position']['y'], figma_canvas['width'], figma_canvas['height'], element['size']['width'], element['size']['height'])
            stroke_node.Center, stroke_node.Width, stroke_node.Height = transform_data['Center'], element['size']['width'] / self.fusion_width, element['size']['height'] / self.fusion_height
            stroke_node.Red, stroke_node.Green, stroke_node.Blue, stroke_node.Alpha = stroke_color.get('r', 0), stroke_color.get('g', 0), stroke_color.get('b', 0), stroke_color.get('a', 1)
        if fills and fills[0].get('visible', True):
            fill_color = fills[0].get('color', {})
            fill_pos_x, fill_pos_y = (pos_x + 20, pos_y + 20) if stroke_node else (pos_x, pos_y)
            fill_node = self.composition.AddTool("sEllipse", fill_pos_x, fill_pos_y)
            fill_node.SetAttrs({"TOOLS_Name": f"{node_name}_Fill"})
            transform_data = self.figma_to_fusion_coords(element['position']['x'], element['position']['y'], figma_canvas['width'], figma_canvas['height'], element['size']['width'], element['size']['height'])
            fill_node.Center = transform_data['Center']
            stroke_weight = element.get('strokeWeight') or 0 if stroke_node else 0
            fill_node.Width, fill_node.Height = (element['size']['width'] - 2 * stroke_weight) / self.fusion_width, (element['size']['height'] - 2 * stroke_weight) / self.fusion_height
            fill_node.Red, fill_node.Green, fill_node.Blue, fill_node.Alpha = fill_color.get('r', 1), fill_color.get('g', 1), fill_color.get('b', 1), fill_color.get('a', 1)
        if stroke_node and fill_node: return self.create_merge_node([stroke_node, fill_node], name=node_name)
        return fill_node or stroke_node

    def create_merge_node(self, input_nodes: List[Any], name: str = "Merge") -> Optional[Any]:
        if not input_nodes: return None
        if len(input_nodes) == 1: return input_nodes[0]
        node_name = f"Merge_{name}"
        if not self.resolve: return f"merged_{name}"
        pos_x, pos_y = self.get_next_node_position()
        merge_node = self.composition.AddTool("Merge", pos_x, pos_y)
        merge_node.SetAttrs({"TOOLS_Name": f"{node_name}_1"})
        merge_node.ConnectInput("Background", input_nodes[0])
        merge_node.ConnectInput("Foreground", input_nodes[1])
        last_merge_node = merge_node
        for i in range(2, len(input_nodes)):
            pos_x, pos_y = self.get_next_node_position()
            new_merge_node = self.composition.AddTool("Merge", pos_x, pos_y)
            new_merge_node.SetAttrs({"TOOLS_Name": f"{node_name}_{i}"})
            new_merge_node.ConnectInput("Background", last_merge_node)
            new_merge_node.ConnectInput("Foreground", input_nodes[i])
            last_merge_node = new_merge_node
        return last_merge_node

    def apply_effects(self, parent_node: Any, effects: List[Dict]) -> Any:
        last_node = parent_node
        for effect in effects:
            if not effect.get('visible', True): continue
            effect_type = effect.get('type')
            new_effect_node = None
            if effect_type == 'LAYER_BLUR':
                new_effect_node = self.composition.AddTool("Blur")
                if new_effect_node: new_effect_node.Blur = effect.get('radius', 0.0) / 20.0
            elif effect_type == 'DROP_SHADOW':
                new_effect_node = self.composition.AddTool("DropShadow")
                if new_effect_node:
                    color = effect.get('color', {})
                    new_effect_node.Red, new_effect_node.Green, new_effect_node.Blue, new_effect_node.Alpha = color.get('r', 0), color.get('g', 0), color.get('b', 0), color.get('a', 1)
                    new_effect_node.ShadowStrength, new_effect_node.Blur = effect.get('spread', 0.0), effect.get('radius', 0.0)
                    offset = effect.get('offset', {})
                    new_effect_node.Distance = (offset.get('x', 0)**2 + offset.get('y', 0)**2)**0.5 / 100.0
            if new_effect_node:
                new_effect_node.ConnectInput("Input", last_node)
                last_node = new_effect_node
        return last_node
    
    def process_element(self, element: Dict, figma_canvas: Dict) -> Optional[Any]:
        """
        Process a single Figma element and create a corresponding Fusion node chain.
        Handles basic elements, groups, and masks.
        """
        element_type = element.get('type', '').upper()
        element_name = element.get('name', 'Unknown')

        # Handle Groups and Frames, which may contain masks
        if element_type in ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE']:
            children = element.get('children', [])
            # In Figma, a mask is the layer below the content it masks.
            # We iterate backwards to find the mask and apply it to the item above it.
            i = len(children) - 1
            child_nodes = []
            while i >= 0:
                child = children[i]
                if child.get('isMask') and i > 0:
                    mask_node_data = child
                    content_node_data = children[i-1] # The layer above the mask is masked by it

                    print(f"  - Found mask '{mask_node_data.get('name')}' applied to '{content_node_data.get('name')}'")

                    # Process the content and the mask shape
                    content_node = self.process_element(content_node_data, figma_canvas)
                    mask_shape_node = self.process_element(mask_node_data, figma_canvas)

                    if content_node and mask_shape_node:
                        # Create a merge, connect content to foreground, mask to mask input
                        merge_node = self.composition.AddTool("Merge")
                        if merge_node:
                            merge_node.ConnectInput("Foreground", content_node)
                            merge_node.ConnectInput("Mask", mask_shape_node)
                            merge_node.SetInput("Operator", "In") # Use 'In' to apply the mask
                            child_nodes.insert(0, merge_node) # Add the merged result to the list
                        else:
                            child_nodes.insert(0, content_node) # Failsafe
                    i -= 2 # We processed two children (mask + content), so skip both
                else:
                    node = self.process_element(child, figma_canvas)
                    if node:
                        child_nodes.insert(0, node) # Add to the beginning to maintain layer order
                    i -= 1

            if len(child_nodes) > 1:
                return self.create_merge_node(child_nodes, element_name)
            elif len(child_nodes) == 1:
                return child_nodes[0]
            return None

        # Handle basic element types
        base_node = None
        if element_type == 'TEXT':
            base_node = self.create_text_node(element, figma_canvas)
        elif element_type == 'RECTANGLE':
            base_node = self.create_rectangle_node(element, figma_canvas)
        elif element_type == 'ELLIPSE':
            base_node = self.create_ellipse_node(element, figma_canvas)
        elif element.get('imageData'):
            image_path = self.save_base64_image(element['imageData'], element_name)
            if image_path:
                base_node = self.create_loader_node(image_path, element, figma_canvas)

        if not base_node:
            return None

        # Apply effects to the created node
        return self.apply_effects(base_node, element.get('effects', []))
    
    def import_figma_composition(self, data_id: Optional[str] = None) -> bool:
        print("Starting Figma to Fusion import...")
        if not self.composition: return False
        figma_data = self.fetch_figma_data(data_id)
        if not figma_data: return False
        canvas_size = figma_data.get('canvasSize', {'width': self.fusion_width, 'height': self.fusion_height})
        root_nodes = [self.process_element(element, canvas_size) for element in figma_data.get('elements', [])]
        root_nodes = [node for node in root_nodes if node]
        if len(root_nodes) > 1: self.create_merge_node(root_nodes, "Final")
        print("✅ Import completed successfully!")
        return True
    
    def cleanup(self):
        for temp_file in self.temp_image_files:
            try:
                if os.path.exists(temp_file): os.remove(temp_file)
            except Exception as e: print(f"Could not clean up {temp_file}: {e}")
        self.temp_image_files.clear()

def main():
    try:
        if not resolve or not resolve.GetProjectManager(): raise AttributeError
    except (ImportError, AttributeError, NameError):
        print("❌ ERROR: DaVinci Resolve API Not Found!")
        print("This script must be run from the menu inside DaVinci Resolve.")
        return 1
    importer = FigmaToFusion()
    try:
        importer.import_figma_composition(sys.argv[1] if len(sys.argv) > 1 else None)
    finally:
        importer.cleanup()
    return 0

if __name__ == "__main__":
    exit(main())
