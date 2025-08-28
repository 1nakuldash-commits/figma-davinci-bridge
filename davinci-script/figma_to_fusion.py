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
    print("Warning: DaVinci Resolve API not available. Running in debug mode.")
    resolve = None

class FigmaToFusion:
    def __init__(self, bridge_url: str = "http://localhost:5000"):
        self.bridge_url = bridge_url
        self.resolve = resolve
        self.project_manager = None
        self.project = None
        self.media_pool = None
        self.current_timeline = None
        self.fusion_page = None
        self.composition = None
        self.temp_image_files = []
        
        # Node positioning
        self.node_x = 0
        self.node_y = 0
        self.node_spacing_x = 300
        self.node_spacing_y = 200
        
        # Color conversion constants
        self.fusion_width = 1920  # Default composition width
        self.fusion_height = 1080  # Default composition height
        
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
            
            # Ensure we are on the Fusion page
            if self.resolve.GetCurrentPage() != "fusion":
                self.resolve.OpenPage("fusion")
            
            self.fusion_page = self.resolve.GetCurrentPage()
            self.composition = self.fusion_page.GetCurrentComp()

            if not self.composition:
                print("Error: No active Fusion composition.")
                print("Please open a timeline and go to the Fusion page before running the script.")
                return False

            # Get composition dimensions
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
            # Extract base64 data (remove data:image/png;base64, prefix)
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            
            # Decode base64 data
            image_data = base64.b64decode(base64_data)
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            safe_name = "".join(c for c in element_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            temp_file = os.path.join(temp_dir, f"figma_{safe_name}_{len(self.temp_image_files)}.png")
            
            with open(temp_file, 'wb') as f:
                f.write(image_data)
            
            self.temp_image_files.append(temp_file)
            print(f"Saved image: {temp_file}")
            return temp_file
            
        except Exception as e:
            print(f"Error saving image for {element_name}: {e}")
            return None
    
    # Note: The create_new_composition method has been removed.
    # The script now operates on the currently active Fusion composition.
    
    def get_next_node_position(self) -> tuple:
        """Get the next available node position"""
        pos = (self.node_x, self.node_y)
        self.node_x += self.node_spacing_x
        if self.node_x > 2000:  # Wrap to next row
            self.node_x = 0
            self.node_y += self.node_spacing_y
        return pos
    
    def figma_to_fusion_coords(self, figma_x: float, figma_y: float, figma_width: float, figma_height: float, element_width: float, element_height: float) -> Dict:
        """Convert Figma coordinates to Fusion coordinates"""
        # Normalize coordinates to 0-1 range
        center_x = (figma_x + element_width / 2) / figma_width
        center_y = (figma_y + element_height / 2) / figma_height
        
        # Convert to Fusion coordinate system (center is 0.5, 0.5)
        fusion_x = center_x
        fusion_y = 1.0 - center_y  # Flip Y axis
        
        # Calculate scale
        scale_x = element_width / figma_width
        scale_y = element_height / figma_height
        
        return {
            'Center': [fusion_x, fusion_y],
            'Size': min(scale_x, scale_y)  # Maintain aspect ratio
        }
    
    def create_loader_node(self, image_path: str, element: Dict, figma_canvas: Dict) -> Optional[str]:
        """Create a Loader node for image elements"""
        node_name = f"Loader_{element['name']}"
        
        if not self.resolve:
            print(f"Debug: Would create Loader node: {node_name}")
            return node_name
        
        try:
            # Get node position
            pos_x, pos_y = self.get_next_node_position()
            
            # Create Loader node
            loader = self.composition.AddTool("Loader", pos_x, pos_y)
            loader.SetAttrs({"TOOLS_Name": node_name})
            
            # Set image path
            loader.Clip = image_path
            
            # Set position and scale
            transform_data = self.figma_to_fusion_coords(
                element['position']['x'], element['position']['y'],
                figma_canvas['width'], figma_canvas['height'],
                element['size']['width'], element['size']['height']
            )
            
            loader.Center = transform_data['Center']
            if element.get('opacity', 1.0) < 1.0:
                loader.Opacity = element['opacity']
            
            print(f"Created Loader node: {node_name}")
            return node_name
            
        except Exception as e:
            print(f"Error creating Loader node: {e}")
            return None
    
    def create_text_node(self, element: Dict, figma_canvas: Dict) -> Optional[str]:
        """Create a Text+ node for text elements"""
        node_name = f"Text_{element['name']}"
        
        if not self.resolve:
            print(f"Debug: Would create Text+ node: {node_name}")
            return node_name
        
        try:
            # Get node position
            pos_x, pos_y = self.get_next_node_position()
            
            # Create Text+ node
            text_node = self.composition.AddTool("Text+", pos_x, pos_y)
            text_node.SetAttrs({"TOOLS_Name": node_name})
            
            # Set text content
            if element.get('characters'):
                text_node.StyledText = element['characters']
            
            # Set position
            transform_data = self.figma_to_fusion_coords(
                element['position']['x'], element['position']['y'],
                figma_canvas['width'], figma_canvas['height'],
                element['size']['width'], element['size']['height']
            )
            
            text_node.Center = transform_data['Center']
            
            # Set font size (approximate conversion)
            if element.get('fontSize') and isinstance(element['fontSize'], (int, float)):
                relative_size = element['fontSize'] / 16.0  # Normalize to reasonable range
                text_node.Size = relative_size
            
            # Set opacity
            if element.get('opacity', 1.0) < 1.0:
                text_node.Opacity = element['opacity']
            
            print(f"Created Text+ node: {node_name}")
            return node_name
            
        except Exception as e:
            print(f"Error creating Text+ node: {e}")
            return None
    
    def create_rectangle_node(self, element: Dict, figma_canvas: Dict) -> Optional[Any]:
        """Create a Rectangle (sRectangle) node, handling fill and stroke."""
        node_name = f"Rect_{element['name']}"
        
        if not self.resolve:
            print(f"Debug: Would create sRectangle node: {node_name}")
            return f"rect_{element['name']}"

        fills = element.get('fills', [])
        strokes = element.get('strokes', [])
        
        fill_node = None
        stroke_node = None

        pos_x, pos_y = self.get_next_node_position()

        # Create the stroke node (if a stroke exists)
        if strokes and len(strokes) > 0:
            stroke_color = strokes[0].get('color', {'r': 0, 'g': 0, 'b': 0, 'a': 1})
            stroke_weight = element.get('strokeWeight', 1.0)
            
            stroke_node = self.composition.AddTool("sRectangle", pos_x, pos_y)
            stroke_node.SetAttrs({"TOOLS_Name": f"{node_name}_Stroke"})
            
            transform_data = self.figma_to_fusion_coords(
                element['position']['x'], element['position']['y'],
                figma_canvas['width'], figma_canvas['height'],
                element['size']['width'], element['size']['height']
            )
            stroke_node.Center = transform_data['Center']
            stroke_node.Width = element['size']['width'] / self.fusion_width
            stroke_node.Height = element['size']['height'] / self.fusion_height
            
            stroke_node.Red = stroke_color.get('r', 0)
            stroke_node.Green = stroke_color.get('g', 0)
            stroke_node.Blue = stroke_color.get('b', 0)
            stroke_node.Alpha = stroke_color.get('a', 1)
            stroke_node.SoftEdge = 0.001 # A little softness for antialiasing
            
            if element.get('cornerRadius') and isinstance(element['cornerRadius'], (int, float)):
                 stroke_node.CornerRadius = element['cornerRadius'] / min(element['size']['width'], element['size']['height'])

        # Create the fill node
        if fills and len(fills) > 0 and fills[0].get('visible', True):
            fill_color = fills[0].get('color', {'r': 1, 'g': 1, 'b': 1, 'a': 1})
            
            # Position fill node slightly offset to avoid overlap issues if no stroke
            fill_pos_x = pos_x + 20 if stroke_node else pos_x
            fill_pos_y = pos_y + 20 if stroke_node else pos_y

            fill_node = self.composition.AddTool("sRectangle", fill_pos_x, fill_pos_y)
            fill_node.SetAttrs({"TOOLS_Name": f"{node_name}_Fill"})
            
            transform_data = self.figma_to_fusion_coords(
                element['position']['x'], element['position']['y'],
                figma_canvas['width'], figma_canvas['height'],
                element['size']['width'], element['size']['height']
            )
            fill_node.Center = transform_data['Center']

            # Adjust size for stroke
            stroke_weight = element.get('strokeWeight', 1.0) if stroke_node else 0
            fill_width = (element['size']['width'] - 2 * stroke_weight) / self.fusion_width
            fill_height = (element['size']['height'] - 2 * stroke_weight) / self.fusion_height
            fill_node.Width = fill_width
            fill_node.Height = fill_height

            fill_node.Red = fill_color.get('r', 1)
            fill_node.Green = fill_color.get('g', 1)
            fill_node.Blue = fill_color.get('b', 1)
            fill_node.Alpha = fill_color.get('a', 1)

            if element.get('cornerRadius') and isinstance(element['cornerRadius'], (int, float)):
                 fill_node.CornerRadius = (element['cornerRadius'] - stroke_weight) / min(element['size']['width'], element['size']['height'])

        # Combine nodes
        if stroke_node and fill_node:
            print(f"Created sRectangle with Fill and Stroke: {node_name}")
            return self.create_merge_node([stroke_node, fill_node], name=node_name)
        elif fill_node:
            print(f"Created sRectangle with Fill: {node_name}")
            return fill_node
        elif stroke_node:
            print(f"Created sRectangle with Stroke only: {node_name}")
            return stroke_node

        return None

    def create_ellipse_node(self, element: Dict, figma_canvas: Dict) -> Optional[Any]:
        """Create a Ellipse (sEllipse) node, handling fill and stroke."""
        node_name = f"Ellipse_{element['name']}"

        if not self.resolve:
            print(f"Debug: Would create sEllipse node: {node_name}")
            return f"ellipse_{element['name']}"

        fills = element.get('fills', [])
        strokes = element.get('strokes', [])

        fill_node = None
        stroke_node = None

        pos_x, pos_y = self.get_next_node_position()

        if strokes and len(strokes) > 0:
            stroke_color = strokes[0].get('color', {'r': 0, 'g': 0, 'b': 0, 'a': 1})
            stroke_node = self.composition.AddTool("sEllipse", pos_x, pos_y)
            stroke_node.SetAttrs({"TOOLS_Name": f"{node_name}_Stroke"})
            
            transform_data = self.figma_to_fusion_coords(
                element['position']['x'], element['position']['y'],
                figma_canvas['width'], figma_canvas['height'],
                element['size']['width'], element['size']['height']
            )
            stroke_node.Center = transform_data['Center']
            stroke_node.Width = element['size']['width'] / self.fusion_width
            stroke_node.Height = element['size']['height'] / self.fusion_height

            stroke_node.Red = stroke_color.get('r', 0)
            stroke_node.Green = stroke_color.get('g', 0)
            stroke_node.Blue = stroke_color.get('b', 0)
            stroke_node.Alpha = stroke_color.get('a', 1)
            stroke_node.SoftEdge = 0.001

        if fills and len(fills) > 0 and fills[0].get('visible', True):
            fill_color = fills[0].get('color', {'r': 1, 'g': 1, 'b': 1, 'a': 1})
            fill_pos_x = pos_x + 20 if stroke_node else pos_x
            fill_pos_y = pos_y + 20 if stroke_node else pos_y

            fill_node = self.composition.AddTool("sEllipse", fill_pos_x, fill_pos_y)
            fill_node.SetAttrs({"TOOLS_Name": f"{node_name}_Fill"})

            transform_data = self.figma_to_fusion_coords(
                element['position']['x'], element['position']['y'],
                figma_canvas['width'], figma_canvas['height'],
                element['size']['width'], element['size']['height']
            )
            fill_node.Center = transform_data['Center']

            stroke_weight = element.get('strokeWeight', 1.0) if stroke_node else 0
            fill_node.Width = (element['size']['width'] - 2 * stroke_weight) / self.fusion_width
            fill_node.Height = (element['size']['height'] - 2 * stroke_weight) / self.fusion_height

            fill_node.Red = fill_color.get('r', 1)
            fill_node.Green = fill_color.get('g', 1)
            fill_node.Blue = fill_color.get('b', 1)
            fill_node.Alpha = fill_color.get('a', 1)

        if stroke_node and fill_node:
            print(f"Created sEllipse with Fill and Stroke: {node_name}")
            return self.create_merge_node([stroke_node, fill_node], name=node_name)
        elif fill_node:
            print(f"Created sEllipse with Fill: {node_name}")
            return fill_node
        elif stroke_node:
            print(f"Created sEllipse with Stroke only: {node_name}")
            return stroke_node

        return None
    
    def create_merge_node(self, input_nodes: List[Any], name: str = "Merge") -> Optional[Any]:
        """Create a Merge node to combine multiple inputs."""
        if not input_nodes:
            return None
        if len(input_nodes) == 1:
            return input_nodes[0]

        node_name = f"Merge_{name}"
        
        if not self.resolve:
            print(f"Debug: Would create Merge node: {node_name} with {len(input_nodes)} inputs")
            return f"merged_{name}" # Return a placeholder name

        try:
            # Position the merge node
            pos_x, pos_y = self.get_next_node_position()
            
            # Create the first merge node
            merge_node = self.composition.AddTool("Merge", pos_x, pos_y)
            merge_node.SetAttrs({"TOOLS_Name": f"{node_name}_1"})
            
            # Connect the first two nodes
            merge_node.ConnectInput("Background", input_nodes[0])
            merge_node.ConnectInput("Foreground", input_nodes[1])

            last_merge_node = merge_node

            # Chain additional merge nodes for more than 2 inputs
            for i in range(2, len(input_nodes)):
                pos_x, pos_y = self.get_next_node_position()
                new_merge_node = self.composition.AddTool("Merge", pos_x, pos_y)
                new_merge_node.SetAttrs({"TOOLS_Name": f"{node_name}_{i}"})

                new_merge_node.ConnectInput("Background", last_merge_node)
                new_merge_node.ConnectInput("Foreground", input_nodes[i])
                last_merge_node = new_merge_node

            print(f"Created Merge chain: {node_name}")
            return last_merge_node
            
        except Exception as e:
            print(f"Error creating Merge node: {e}")
            return None

    def apply_effects(self, parent_node: Any, effects: List[Dict]) -> Any:
        """Apply a chain of effect nodes to a parent node."""
        last_node = parent_node

        for effect in effects:
            effect_type = effect.get('type')
            if not effect.get('visible', True):
                continue

            # Create and connect the new effect node
            new_effect_node = None
            if effect_type == 'LAYER_BLUR':
                new_effect_node = self.composition.AddTool("Blur", self.node_x, self.node_y)
                if new_effect_node:
                    new_effect_node.Blur = effect.get('radius', 0.0) / 20.0 # Approximate conversion

            elif effect_type == 'DROP_SHADOW':
                new_effect_node = self.composition.AddTool("DropShadow", self.node_x, self.node_y)
                if new_effect_node:
                    color = effect.get('color', {})
                    new_effect_node.Red = color.get('r', 0.0)
                    new_effect_node.Green = color.get('g', 0.0)
                    new_effect_node.Blue = color.get('b', 0.0)
                    new_effect_node.Alpha = color.get('a', 1.0)
                    new_effect_node.ShadowStrength = effect.get('spread', 0.0)
                    new_effect_node.Blur = effect.get('radius', 0.0)
                    offset = effect.get('offset', {})
                    # This is a simplification, a more accurate approach would involve a Transform node
                    new_effect_node.Distance = (offset.get('x', 0)**2 + offset.get('y', 0)**2)**0.5 / 100.0

            if new_effect_node:
                print(f"Applying {effect_type} to {last_node.GetAttrs('TOOLS_Name')}")
                new_effect_node.ConnectInput("Input", last_node)
                last_node = new_effect_node
                # Move to next position
                self.node_x += 80 # Small horizontal shift for effect nodes

        return last_node
    
    def process_element(self, element: Dict, figma_canvas: Dict) -> Optional[Any]:
        """
        Process a single Figma element and create a corresponding Fusion node chain.
        Returns the last node in the chain for this element.
        """
        element_type = element.get('type', '').upper()
        element_name = element.get('name', 'Unknown')
        
        print(f"Processing element: {element_name} (Type: {element_type})")
        
        base_node = None
        # Handle different element types to create the base node
        if element_type == 'TEXT':
            base_node = self.create_text_node(element, figma_canvas)
        
        elif element_type == 'RECTANGLE':
            base_node = self.create_rectangle_node(element, figma_canvas)

        elif element_type == 'ELLIPSE':
            base_node = self.create_ellipse_node(element, figma_canvas)
        
        elif element_type in ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE']:
            # For containers, recursively process children and merge them
            child_outputs = []
            if element.get('children'):
                for child in element['children']:
                    child_output_node = self.process_element(child, figma_canvas)
                    if child_output_node:
                        child_outputs.append(child_output_node)
            
            # If the container itself has an image, treat it as another layer
            if element.get('imageData'):
                image_path = self.save_base64_image(element['imageData'], element_name)
                if image_path:
                    container_loader = self.create_loader_node(image_path, element, figma_canvas)
                    if container_loader:
                        child_outputs.append(container_loader)
            
            # Merge all child outputs
            if len(child_outputs) > 1:
                base_node = self.create_merge_node(child_outputs, element_name)
            elif len(child_outputs) == 1:
                base_node = child_outputs[0]
        
        else:
            # For other types (ELLIPSE, POLYGON, STAR, VECTOR, IMAGE, etc.), 
            # create a Loader node with the exported image if available
            if element.get('imageData'):
                image_path = self.save_base64_image(element['imageData'], element_name)
                if image_path:
                    base_node = self.create_loader_node(image_path, element, figma_canvas)

        if not base_node:
            print(f"Warning: Could not create a base node for element {element_name} (Type: {element_type})")
            return None

        # Apply effects to the base node
        effects = element.get('effects', [])
        final_node = self.apply_effects(base_node, effects)
        
        return final_node
    
    def import_figma_composition(self, data_id: Optional[str] = None) -> bool:
        """Main method to import Figma data into the active Fusion composition."""
        print("Starting Figma to Fusion import...")

        if not self.composition:
            print("Initialization failed. Cannot proceed with import.")
            return False
        
        # Fetch data from bridge
        figma_data = self.fetch_figma_data(data_id)
        if not figma_data:
            return False
        
        print(f"Retrieved data with {len(figma_data.get('elements', []))} elements")
        
        # Get canvas size from Figma data for coordinate conversion
        canvas_size = figma_data.get('canvasSize', {'width': self.fusion_width, 'height': self.fusion_height})
        
        # Process elements
        root_nodes = []
        for element in figma_data.get('elements', []):
            node_name = self.process_element(element, canvas_size)
            if node_name:
                root_nodes.append(node_name)
        
        # Create final merge node if we have multiple root elements
        if len(root_nodes) > 1:
            final_merge = self.create_merge_node(root_nodes, "Final")
            print(f"Created final merge node with {len(root_nodes)} inputs")
        
        print(f"Successfully imported {len(root_nodes)} root elements")
        print("Import completed!")
        
        return True
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_image_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"Cleaned up: {temp_file}")
            except Exception as e:
                print(f"Could not clean up {temp_file}: {e}")
        
        self.temp_image_files.clear()

def main():
    """Main entry point"""
    # Safety check: Ensure the script is run from within DaVinci Resolve
    if not resolve:
        print("="*60)
        print("❌ ERROR: DaVinci Resolve API Not Found!")
        print("This script must be run from the menu inside DaVinci Resolve.")
        print("Please do not run this file directly.")
        print("\nInstructions:")
        print("1. Start the server using the 'run_workflow.bat' script.")
        print("2. In DaVinci Resolve, go to: Workspace > Scripts > Comp > figma_to_fusion")
        print("="*60)
        return 1 # Exit with an error code

    print("=== Figma to DaVinci Resolve Bridge ===")
    print("Importing Figma elements into Fusion...")
    
    # Parse command line arguments
    data_id = None
    if len(sys.argv) > 1:
        data_id = sys.argv[1]
        print(f"Using specific data ID: {data_id}")
    
    # Create importer
    importer = FigmaToFusion()
    
    try:
        # Import composition
        success = importer.import_figma_composition(data_id)
        
        if success:
            print("✅ Import completed successfully!")
            # The input() call is removed as it causes a RuntimeError in the DaVinci Resolve environment
        else:
            print("❌ Import failed!")
            return 1
    
    finally:
        # Cleanup
        importer.cleanup()
    
    return 0

if __name__ == "__main__":
    exit(main())
