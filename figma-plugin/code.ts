// Figma Plugin: Export to DaVinci Resolve Bridge
// This plugin exports selected elements with their properties and images

interface FigmaElement {
  id: string;
  name: string;
  type: string;
  visible: boolean;
  opacity: number;
  blendMode: BlendMode;
  position: {
    x: number;
    y: number;
  };
  size: {
    width: number;
    height: number;
  };
  rotation?: number;
  fills?: readonly Paint[];
  strokes?: readonly Paint[];
  strokeWeight?: number;
  cornerRadius?: number | PluginAPI["mixed"];
  effects?: readonly Effect[];
  characters?: string;
  fontSize?: number | PluginAPI["mixed"];
  fontName?: FontName | PluginAPI["mixed"];
  textAlignHorizontal?: "LEFT" | "CENTER" | "RIGHT" | "JUSTIFIED";
  textAlignVertical?: "TOP" | "CENTER" | "BOTTOM";
  imageData?: string; // Base64 encoded image
  children?: FigmaElement[];
}

interface ExportPayload {
  timestamp: string;
  canvasSize: {
    width: number;
    height: number;
  };
  elements: FigmaElement[];
  metadata: {
    figmaFileId: string;
    figmaFileName: string;
    selectedCount: number;
    exportSettings: {
      format: "PNG" | "JPG";
      scale: number;
    };
  };
}

// Show UI
figma.showUI(__html__, { width: 300, height: 400 });

// Listen for selection changes
figma.on('selectionchange', () => {
  figma.ui.postMessage({
    type: 'selectionChange',
    selectionCount: figma.currentPage.selection.length,
  });
});

async function exportSelectedElements(): Promise<ExportPayload> {
  const selection = figma.currentPage.selection;
  
  if (selection.length === 0) {
    figma.ui.postMessage({
      type: 'error',
      message: 'Please select at least one element to export.'
    });
    throw new Error('No elements selected');
  }

  // Get canvas bounds
  const canvasBounds = figma.viewport.bounds;
  
  const payload: ExportPayload = {
    timestamp: new Date().toISOString(),
    canvasSize: {
      width: canvasBounds.width,
      height: canvasBounds.height
    },
    elements: [],
    metadata: {
      figmaFileId: figma.fileKey || 'unknown',
      figmaFileName: 'Figma Export',
      selectedCount: selection.length,
      exportSettings: {
        format: 'PNG',
        scale: 1
      }
    }
  };

  // Process each selected element
  for (const node of selection) {
    try {
      const element = await processNode(node);
      if (element) {
        payload.elements.push(element);
      }
    } catch (error) {
      console.error(`Error processing node ${node.name}:`, error);
      figma.ui.postMessage({
        type: 'warning',
        message: `Could not process element: ${node.name}`
      });
    }
  }

  return payload;
}

async function processNode(node: SceneNode): Promise<FigmaElement | null> {
  const baseElement: Partial<FigmaElement> = {
    id: node.id,
    name: node.name,
    type: node.type,
    visible: node.visible,
    opacity: node.opacity,
    blendMode: node.blendMode,
    position: {
      x: node.x,
      y: node.y
    },
    size: {
      width: node.width,
      height: node.height
    }
  };

  // Add rotation if applicable
  if ('rotation' in node && node.rotation !== 0) {
    baseElement.rotation = node.rotation;
  }

  // Process different node types
  switch (node.type) {
    case 'RECTANGLE':
    case 'ELLIPSE':
    case 'POLYGON':
    case 'STAR':
    case 'VECTOR':
      return await processGeometricNode(node as GeometryMixin & SceneNode, baseElement);
    
    case 'TEXT':
      return await processTextNode(node as TextNode, baseElement);
    
    case 'FRAME':
    case 'GROUP':
    case 'COMPONENT':
    case 'INSTANCE':
      return await processContainerNode(node as ChildrenMixin & SceneNode, baseElement);
    
    case 'IMAGE':
      return await processImageNode(node as SceneNode, baseElement);
    
    default:
      // For other types, export as image
      return await processGenericNode(node, baseElement);
  }
}

async function processGeometricNode(node: GeometryMixin & SceneNode, baseElement: Partial<FigmaElement>): Promise<FigmaElement> {
  const element = Object.assign({}, baseElement) as FigmaElement;
  
  // Add geometric properties
  element.fills = node.fills;
  element.strokes = node.strokes;
  element.strokeWeight = node.strokeWeight;
  
  // Add corner radius for rectangles
  if (node.type === 'RECTANGLE' && 'cornerRadius' in node) {
    element.cornerRadius = (node as RectangleNode).cornerRadius;
  }
  
  // Add effects
  element.effects = node.effects;
  
  // Export as image
  try {
    const imageData = await exportNodeAsImage(node);
    element.imageData = imageData;
  } catch (error) {
    console.warn(`Could not export image for ${node.name}:`, error);
  }
  
  return element;
}

async function processTextNode(node: TextNode, baseElement: Partial<FigmaElement>): Promise<FigmaElement> {
  const element = Object.assign({}, baseElement) as FigmaElement;
  
  // Add text properties
  element.characters = node.characters;
  element.fontSize = node.fontSize;
  element.fontName = node.fontName;
  element.textAlignHorizontal = node.textAlignHorizontal;
  element.textAlignVertical = node.textAlignVertical;
  element.fills = node.fills;
  element.effects = node.effects;
  
  // Export text as image for positioning reference
  try {
    const imageData = await exportNodeAsImage(node);
    element.imageData = imageData;
  } catch (error) {
    console.warn(`Could not export image for text ${node.name}:`, error);
  }
  
  return element;
}

async function processContainerNode(node: ChildrenMixin & SceneNode, baseElement: Partial<FigmaElement>): Promise<FigmaElement> {
  const element = Object.assign({}, baseElement) as FigmaElement;
  
  // Add container properties
  if ('fills' in node) {
    element.fills = (node as any).fills;
  }
  if ('effects' in node) {
    element.effects = (node as any).effects;
  }
  
  // Process children
  element.children = [];
  for (const child of node.children) {
    try {
      const childElement = await processNode(child);
      if (childElement) {
        element.children.push(childElement);
      }
    } catch (error) {
      console.warn(`Could not process child ${child.name}:`, error);
    }
  }
  
  // Export container as image
  try {
    const imageData = await exportNodeAsImage(node);
    element.imageData = imageData;
  } catch (error) {
    console.warn(`Could not export image for container ${node.name}:`, error);
  }
  
  return element;
}

async function processImageNode(node: SceneNode, baseElement: Partial<FigmaElement>): Promise<FigmaElement> {
  const element = Object.assign({}, baseElement) as FigmaElement;
  
  // Export the image
  try {
    const imageData = await exportNodeAsImage(node);
    element.imageData = imageData;
  } catch (error) {
    console.warn(`Could not export image ${node.name}:`, error);
  }
  
  return element;
}

async function processGenericNode(node: SceneNode, baseElement: Partial<FigmaElement>): Promise<FigmaElement> {
  const element = Object.assign({}, baseElement) as FigmaElement;
  
  // Export as image
  try {
    const imageData = await exportNodeAsImage(node);
    element.imageData = imageData;
  } catch (error) {
    console.warn(`Could not export image for generic node ${node.name}:`, error);
  }
  
  return element;
}

async function exportNodeAsImage(node: SceneNode): Promise<string> {
  try {
    const bytes = await node.exportAsync({
      format: 'PNG',
      constraint: {
        type: 'SCALE',
        value: 1
      }
    });
    
    // Convert to base64
    const base64 = figma.base64Encode(bytes);
    return `data:image/png;base64,${base64}`;
  } catch (error) {
    throw new Error(`Failed to export image: ${error}`);
  }
}

async function sendToFlaskBridge(payload: ExportPayload): Promise<void> {
  figma.ui.postMessage({
    type: 'progress',
    message: 'Sending data to bridge server...'
  });

  try {
    const response = await fetch('http://localhost:5000/send_data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    const result = await response.json();
    
    figma.ui.postMessage({
      type: 'success',
      message: `Successfully sent ${payload.elements.length} elements to bridge server!`,
      data: result
    });
    
  } catch (error) {
    figma.ui.postMessage({
      type: 'error',
      message: `Failed to send data to bridge server: ${error.message}`
    });
    throw error;
  }
}

// Handle UI messages
figma.ui.onmessage = async (msg) => {
  switch (msg.type) {
    case 'getSelection':
      figma.ui.postMessage({
        type: 'selectionChange',
        selectionCount: figma.currentPage.selection.length,
      });
      break;
    case 'export':
      try {
        figma.ui.postMessage({
          type: 'progress',
          message: 'Exporting selected elements...'
        });
        
        const payload = await exportSelectedElements();
        await sendToFlaskBridge(payload);
        
      } catch (error) {
        console.error('Export error:', error);
        figma.ui.postMessage({
          type: 'error',
          message: error.message || 'An unknown error occurred during export.'
        });
      }
      break;
      
    case 'close':
      figma.closePlugin();
      break;
      
    default:
      console.warn('Unknown message type:', msg.type);
  }
};
