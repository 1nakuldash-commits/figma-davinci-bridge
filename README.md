# 🎬 Figma to DaVinci Resolve Bridge

A complete workflow system that bridges Figma designs with DaVinci Resolve's Fusion compositor. Export selected elements from Figma and automatically create corresponding Fusion node trees for professional video production.

## 🏗️ Architecture

The system consists of three main components:

1. **Flask Bridge Server** - Temporary storage and API for data transfer
2. **Figma Plugin** - TypeScript plugin that exports selected elements with properties and images
3. **DaVinci Resolve Script** - Python script that creates Fusion nodes from exported data

## 📋 Quick Start

### Prerequisites

- **Python 3.7+** (required for bridge server and DaVinci script)
- **Node.js & npm** (optional, for TypeScript compilation)
- **Figma Desktop** (for plugin installation)
- **DaVinci Resolve 17+** (for Fusion integration)

### One-Command Setup

```powershell
# Navigate to the workflow directory and run:
.\workflow\run-workflow.ps1
```

This launches an interactive menu where you can:
- Start the bridge server
- Setup the Figma plugin  
- Import data to DaVinci Resolve
- Run the complete workflow

## 🚀 Manual Step-by-Step Workflow

### Step 1: Start Bridge Server

```powershell
.\workflow\1-start-bridge-server.ps1
```

This will:
- Create a Python virtual environment
- Install Flask and dependencies
- Start the server on `http://localhost:5000`

Keep this server running throughout your workflow.

### Step 2: Setup Figma Plugin

```powershell
.\workflow\2-setup-figma-plugin.ps1
```

This will:
- Compile the TypeScript plugin (if Node.js is available)
- Provide installation instructions

To install the plugin:
1. Open Figma Desktop
2. Go to **Plugins → Development → Import plugin from manifest...**
3. Select the `manifest.json` file in the `figma-plugin` directory
4. The plugin will appear in your plugins list

### Step 3: Export from Figma

1. Select elements in your Figma canvas
2. Run **Plugins → Figma to DaVinci Bridge**
3. Click **"Export to DaVinci"** in the plugin UI
4. Wait for confirmation that data was sent to the bridge server

### Step 4: Import to DaVinci Resolve

```powershell
.\workflow\3-run-davinci-import.ps1
```

Before running:
- Make sure DaVinci Resolve is open with a project loaded
- Ensure you've exported data from Figma (Step 3)

This will:
- Connect to the bridge server
- Fetch the exported Figma data
- Create a new timeline/composition in DaVinci Resolve
- Build Fusion node tree based on your Figma elements

## 🎯 Supported Elements

| Figma Element | DaVinci Node | Features |
|---------------|--------------|----------|
| **Text** | Text+ | Position, size, content, font size, opacity |
| **Rectangle** | sRectangle | Position, size, corner radius, fill color, opacity |
| **Images/Vectors** | Loader | Exported as PNG with positioning |
| **Groups/Frames** | Merge | Hierarchical composition of child elements |
| **Other Shapes** | Loader | Exported as image with positioning |

## 📁 Project Structure

```
figma-davinci-bridge/
├── flask-bridge/          # Bridge server
│   ├── app.py            # Flask application
│   ├── requirements.txt  # Python dependencies
│   └── figma_data.json   # Persistent data storage
├── figma-plugin/         # Figma plugin
│   ├── manifest.json     # Plugin manifest
│   ├── code.ts          # Main plugin logic
│   ├── ui.html          # Plugin UI
│   ├── package.json     # Node dependencies
│   └── tsconfig.json    # TypeScript config
├── davinci-script/       # DaVinci Resolve integration
│   ├── figma_to_fusion.py # Main import script
│   └── requirements.txt   # Python dependencies
└── workflow/             # Automation scripts
    ├── run-workflow.ps1           # Main workflow runner
    ├── 1-start-bridge-server.ps1  # Start Flask server
    ├── 2-setup-figma-plugin.ps1   # Setup plugin
    └── 3-run-davinci-import.ps1   # DaVinci import
```

## 🔧 API Endpoints

The Flask bridge server provides these endpoints:

- `POST /send_data` - Receive data from Figma plugin
- `GET /get_data` - Retrieve data for DaVinci Resolve
- `GET /list_data` - List all available datasets
- `GET /health` - Server health check

## 🐛 Troubleshooting

### Bridge Server Issues
- **Connection refused**: Make sure Python is installed and the server script is running
- **CORS errors**: The Flask server includes CORS headers for localhost connections

### Figma Plugin Issues  
- **Plugin not loading**: Ensure `code.js` exists (compile TypeScript or rename `code.ts`)
- **Export fails**: Check that the bridge server is running on localhost:5000
- **No elements selected**: Select at least one element before running the plugin

### DaVinci Resolve Issues
- **API not available**: Ensure DaVinci Resolve is running with a project open
- **Import fails**: Verify the bridge server is accessible and contains data
- **Nodes not created**: Check DaVinci Resolve console for error messages

### Common Solutions
1. **Restart all components** in order: Bridge Server → Figma Plugin → DaVinci Script
2. **Check network connectivity** to localhost:5000
3. **Verify permissions** for file operations and network access
4. **Update DaVinci Resolve** to the latest version for best API compatibility

## 🎨 Workflow Tips

1. **Organize your Figma design**: Use clear, descriptive names for elements
2. **Group related elements**: Use frames or groups to create organized node hierarchies  
3. **Consider performance**: Large numbers of elements may take time to process
4. **Test incrementally**: Start with simple designs before complex compositions
5. **Keep the bridge server running**: Don't stop it between exports and imports

## 🚧 Advanced Usage

### Command Line Options

```powershell
# Run specific steps directly:
.\workflow\run-workflow.ps1 -StartBridge    # Start bridge server only
.\workflow\run-workflow.ps1 -SetupFigma     # Setup Figma plugin only  
.\workflow\run-workflow.ps1 -RunImport      # Run DaVinci import only
.\workflow\run-workflow.ps1 -All            # Run complete workflow
```

### Custom Bridge Server URL

Edit the DaVinci script to use a different server:

```python
importer = FigmaToFusion("http://your-server:port")
```

### Multiple Exports

The bridge server stores multiple datasets with timestamps. You can select which dataset to import in the DaVinci import script.

## 🤝 Contributing

This is a proof-of-concept system that can be extended with:
- Additional Figma element types
- More sophisticated Fusion node configurations  
- Animation and timeline support
- Cloud-based bridge server
- Real-time synchronization

## 📄 License

This project is provided as-is for educational and development purposes.

---

**Built with ❤️ for the creative workflow between design and video production.**
