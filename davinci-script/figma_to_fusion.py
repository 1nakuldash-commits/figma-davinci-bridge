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
        """Initialize DaVinci Resolve components"""
        try:
            self.project_manager = self.resolve.GetProjectManager()
            self.project = self.project_manager.GetCurrentProject()
            
            if not self.project:
                print("Error: No project is currently open in DaVinci Resolve")
                return False
            
            self.media_pool = self.project.GetMediaPool()
            
            # Switch to Fusion page
            self.resolve.OpenPage("fusion")
            self.fusion_page = self.resolve.GetCurrentPage()
            
            print(f"Successfully connected to project: {self.project.GetName()}")
            return True
            
        except Exception as e:
            print(f"Error initializing DaVinci Resolve: {e}")
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
    
    def create_new_composition(self, name: str, width: int = 1920, height: int = 1080, frame_rate: float = 24.0) -> bool:
        """Create a new Fusion composition"""
        if not self.resolve:
            print("Debug: Would create new composition:", name)
            return True
        
        try:
            # Create new timeline for the composition
            media_pool_folder = self.media_pool.GetRootFolder()
            new_timeline = self.media_pool.CreateEmptyTimeline(name)
            
            if new_timeline:
                self.current_timeline = new_timeline
                self.project.SetCurrentTimeline(new_timeline)
                
                # Set timeline properties
                timeline_settings = {
                    "timelineResolutionWidth": str(width),
                    "timelineResolutionHeight": str(height),
                    "timelineFrameRate": str(frame_rate)
                }
                new_timeline.SetSetting(timeline_settings)
                
                # Switch to Fusion page and get composition
                self.resolve.OpenPage("fusion")
                self.composition = self.fusion_page.GetCurrentComp()
                
                self.fusion_width = width
                self.fusion_height = height
                
                print(f"Created new composition: {name} ({width}x{height} @ {frame_rate}fps)")
                return True
            else:
                print("Error: Could not create timeline")
                return False
                
        except Exception as e:
            print(f"Error creating composition: {e}")
            return False
    
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
    
    def create_rectangle_node(self, element: Dict, figma_canvas: Dict) -> Optional[str]:
        """Create a Rectangle (sRectangle) node for rectangle elements"""
        node_name = f"Rectangle_{element['name']}"
        
        if not self.resolve:
            print(f"Debug: Would create sRectangle node: {node_name}")
            return node_name
        
        try:
            # Get node position
            pos_x, pos_y = self.get_next_node_position()
            
            # Create Rectangle node
            rect_node = self.composition.AddTool("sRectangle", pos_x, pos_y)
            rect_node.SetAttrs({"TOOLS_Name": node_name})
            
            # Set position and size
            transform_data = self.figma_to_fusion_coords(
                element['position']['x'], element['position']['y'],
                figma_canvas['width'], figma_canvas['height'],
                element['size']['width'], element['size']['height']
            )
            
            rect_node.Center = transform_data['Center']
            rect_node.Width = element['size']['width'] / figma_canvas['width']
            rect_node.Height = element['size']['height'] / figma_canvas['height']
            
            # Set corner radius if available
            if element.get('cornerRadius') and isinstance(element['cornerRadius'], (int, float)):
                corner_radius = element['cornerRadius'] / min(element['size']['width'], element['size']['height'])
                rect_node.CornerRadius = corner_radius
            
            # Set color from fills if available
            fills = element.get('fills', [])
            if fills and len(fills) > 0:
                fill = fills[0]  # Use first fill
                if fill.get('type') == 'SOLID' and fill.get('color'):
                    color = fill['color']
                    rect_node.Red = color.get('r', 1.0)
                    rect_node.Green = color.get('g', 1.0)
                    rect_node.Blue = color.get('b', 1.0)
                    if color.get('a') is not None:
                        rect_node.Alpha = color['a']
            
            # Set opacity
            if element.get('opacity', 1.0) < 1.0:
                rect_node.Opacity = element['opacity']
            
            print(f"Created sRectangle node: {node_name}")
            return node_name
            
        except Exception as e:
            print(f"Error creating sRectangle node: {e}")
            return None
    
    def create_merge_node(self, input_nodes: List[str], name: str = "Merge") -> Optional[str]:
        """Create a Merge node to combine multiple inputs"""
        node_name = f"Merge_{name}"
        
        if not self.resolve:
            print(f"Debug: Would create Merge node: {node_name} with inputs: {input_nodes}")
            return node_name
        
        try:
            # Get node position
            pos_x, pos_y = self.get_next_node_position()
            
            # Create Merge node
            merge_node = self.composition.AddTool("Merge", pos_x, pos_y)
            merge_node.SetAttrs({"TOOLS_Name": node_name})
            
            print(f"Created Merge node: {node_name}")
            return node_name
            
        except Exception as e:
            print(f"Error creating Merge node: {e}")
            return None
    
    def process_element(self, element: Dict, figma_canvas: Dict) -> Optional[str]:
        """Process a single Figma element and create corresponding Fusion node"""
        element_type = element.get('type', '').upper()
        element_name = element.get('name', 'Unknown')
        
        print(f"Processing element: {element_name} (Type: {element_type})")
        
        # Handle different element types
        if element_type == 'TEXT':
            return self.create_text_node(element, figma_canvas)
        
        elif element_type == 'RECTANGLE':
            return self.create_rectangle_node(element, figma_canvas)
        
        elif element_type in ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE']:
            # For containers, create nodes for children and merge them
            child_nodes = []
            if element.get('children'):
                for child in element['children']:
                    child_node = self.process_element(child, figma_canvas)
                    if child_node:
                        child_nodes.append(child_node)
            
            # If we have an image, create a loader for the container as well
            if element.get('imageData'):
                image_path = self.save_base64_image(element['imageData'], element_name)
                if image_path:
                    container_loader = self.create_loader_node(image_path, element, figma_canvas)
                    if container_loader:
                        child_nodes.append(container_loader)
            
            # Merge child nodes if we have multiple
            if len(child_nodes) > 1:
                return self.create_merge_node(child_nodes, element_name)
            elif len(child_nodes) == 1:
                return child_nodes[0]
        
        else:
            # For other types (ELLIPSE, POLYGON, STAR, VECTOR, IMAGE, etc.), 
            # create a Loader node with the exported image
            if element.get('imageData'):
                image_path = self.save_base64_image(element['imageData'], element_name)
                if image_path:
                    return self.create_loader_node(image_path, element, figma_canvas)
        
        print(f"Warning: Could not process element {element_name} (Type: {element_type})")
        return None
    
    def import_figma_composition(self, data_id: Optional[str] = None) -> bool:
        """Main method to import Figma data and create Fusion composition"""
        print("Starting Figma to Fusion import...")
        
        # Fetch data from bridge
        figma_data = self.fetch_figma_data(data_id)
        if not figma_data:
            return False
        
        print(f"Retrieved data with {len(figma_data.get('elements', []))} elements")
        
        # Create new composition
        canvas_size = figma_data.get('canvasSize', {'width': 1920, 'height': 1080})
        composition_name = f"Figma_Import_{figma_data.get('timestamp', '').replace(':', '-').replace('.', '-')}"
        
        if not self.create_new_composition(
            composition_name, 
            canvas_size['width'], 
            canvas_size['height']
        ):
            return False
        
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
            input("Press Enter to cleanup temporary files and exit...")
        else:
            print("❌ Import failed!")
            return 1
    
    finally:
        # Cleanup
        importer.cleanup()
    
    return 0

if __name__ == "__main__":
    exit(main())
