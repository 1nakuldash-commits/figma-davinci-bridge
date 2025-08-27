// Figma Plugin: Export to DaVinci Resolve Bridge
// Clean JavaScript version

// Show UI
figma.showUI(__html__, { width: 300, height: 400 });

// Track selection changes
figma.on('selectionchange', () => {
  const selectionCount = figma.currentPage.selection.length;
  figma.ui.postMessage({
    type: 'selectionChange',
    selectionCount: selectionCount
  });
});

async function exportSelectedElements() {
  const selection = figma.currentPage.selection;
  
  if (selection.length === 0) {
    figma.ui.postMessage({
      type: 'error',
      message: 'Please select at least one element to export.'
    });
    return null;
  }

  // Get canvas bounds
  const canvasBounds = figma.viewport.bounds;
  
  const payload = {
    timestamp: new Date().toISOString(),
    canvasSize: {
      width: canvasBounds.width,
      height: canvasBounds.height
    },
    elements: [],
    metadata: {
      figmaFileId: figma.fileKey || 'unknown',
      figmaFileName: figma.root.name || 'Figma Export',
      selectedCount: selection.length,
      exportSettings: {
        format: 'PNG',
        scale: 1
      }
    }
  };

  // Process each selected element
  let processedCount = 0;
  for (const node of selection) {
    try {
      figma.ui.postMessage({
        type: 'progress',
        message: `Processing element ${processedCount + 1} of ${selection.length}: ${node.name}`
      });
      
      const element = await processNode(node);
      if (element) {
        payload.elements.push(element);
        processedCount++;
      }
    } catch (error) {
      console.error(`Error processing node ${node.name}:`, error);
      figma.ui.postMessage({
        type: 'warning',
        message: `Could not process element: ${node.name} (${error.message})`
      });
    }
  }

  return payload;
}

async function processNode(node) {
  const baseElement = {
    id: node.id,
    name: node.name,
    type: node.type,
    visible: node.visible,
    opacity: 'opacity' in node ? node.opacity : 1.0,
    blendMode: 'blendMode' in node ? node.blendMode : 'NORMAL',
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
      return await processRectangle(node, baseElement);
    
    case 'TEXT':
      return await processText(node, baseElement);
    
    case 'FRAME':
    case 'GROUP':
    case 'COMPONENT':
    case 'INSTANCE':
      return await processContainer(node, baseElement);
    
    default:
      // For other types, export as image
      return await processGeneric(node, baseElement);
  }
}

async function processRectangle(node, baseElement) {
  const element = { ...baseElement };
  
  // Add rectangle-specific properties safely
  if ('fills' in node) {
    element.fills = node.fills;
  }
  if ('strokes' in node) {
    element.strokes = node.strokes;
  }
  if ('strokeWeight' in node) {
    element.strokeWeight = node.strokeWeight;
  }
  if ('cornerRadius' in node) {
    element.cornerRadius = node.cornerRadius;
  }
  if ('effects' in node) {
    element.effects = node.effects;
  }
  
  // Export as image
  try {
    const imageData = await exportNodeAsImage(node);
    element.imageData = imageData;
  } catch (error) {
    console.warn(`Could not export image for rectangle ${node.name}:`, error);
  }
  
  return element;
}

async function processText(node, baseElement) {
  const element = { ...baseElement };
  
  // Add text properties safely
  if ('characters' in node) {
    element.characters = node.characters;
  }
  if ('fontSize' in node) {
    element.fontSize = node.fontSize;
  }
  if ('fontName' in node) {
    element.fontName = node.fontName;
  }
  if ('textAlignHorizontal' in node) {
    element.textAlignHorizontal = node.textAlignHorizontal;
  }
  if ('textAlignVertical' in node) {
    element.textAlignVertical = node.textAlignVertical;
  }
  if ('fills' in node) {
    element.fills = node.fills;
  }
  if ('effects' in node) {
    element.effects = node.effects;
  }
  
  // Export text as image for positioning reference
  try {
    const imageData = await exportNodeAsImage(node);
    element.imageData = imageData;
  } catch (error) {
    console.warn(`Could not export image for text ${node.name}:`, error);
  }
  
  return element;
}

async function processContainer(node, baseElement) {
  const element = { ...baseElement };
  
  // Add container properties safely
  if ('fills' in node) {
    element.fills = node.fills;
  }
  if ('effects' in node) {
    element.effects = node.effects;
  }
  
  // Process children if they exist
  element.children = [];
  if ('children' in node && node.children) {
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

async function processGeneric(node, baseElement) {
  const element = { ...baseElement };
  
  // Export as image
  try {
    const imageData = await exportNodeAsImage(node);
    element.imageData = imageData;
  } catch (error) {
    console.warn(`Could not export image for generic node ${node.name}:`, error);
  }
  
  return element;
}

async function exportNodeAsImage(node) {
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
    throw new Error(`Failed to export image: ${error.message}`);
  }
}

async function sendToFlaskBridge(payload) {
  figma.ui.postMessage({
    type: 'progress',
    message: 'Preparing data for export...'
  });

  // Log the payload for manual use
  console.log('=== FIGMA EXPORT DATA ===');
  console.log('Copy this JSON data and send it to your bridge server:');
  console.log('POST http://localhost:5000/send_data');
  console.log('Content-Type: application/json');
  console.log('');
  console.log(JSON.stringify(payload, null, 2));
  console.log('=== END EXPORT DATA ===');
  
  figma.ui.postMessage({
    type: 'success',
    message: `Exported ${payload.elements.length} elements! Check console (F12) for JSON data.`
  });
}

// Handle UI messages
figma.ui.onmessage = async (msg) => {
  try {
    switch (msg.type) {
      case 'export':
        figma.ui.postMessage({
          type: 'progress',
          message: 'Exporting selected elements...'
        });
        
        const payload = await exportSelectedElements();
        if (payload) {
          await sendToFlaskBridge(payload);
        }
        break;
        
      case 'getSelection':
        const selectionCount = figma.currentPage.selection.length;
        figma.ui.postMessage({
          type: 'selectionChange',
          selectionCount: selectionCount
        });
        break;
        
      case 'close':
        figma.closePlugin();
        break;
        
      default:
        console.warn('Unknown message type:', msg.type);
    }
  } catch (error) {
    console.error('Plugin error:', error);
    figma.ui.postMessage({
      type: 'error',
      message: `Plugin error: ${error.message}`
    });
  }
};
