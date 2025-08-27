# Figma to DaVinci Bridge - Complete Workflow Runner
# This script runs the complete workflow step by step

param(
    [switch]$StartBridge,
    [switch]$SetupFigma, 
    [switch]$RunImport,
    [switch]$All
)

function Show-Header {
    Clear-Host
    Write-Host "╔═══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                     🎬 FIGMA TO DAVINCI BRIDGE 🎬                     ║" -ForegroundColor Cyan
    Write-Host "║                                                                       ║" -ForegroundColor Cyan
    Write-Host "║                Complete Workflow for Design to Video                  ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Menu {
    Write-Host "Choose your action:" -ForegroundColor White
    Write-Host ""
    Write-Host "  [1] Start Bridge Server         - Launch Flask bridge server" -ForegroundColor Yellow
    Write-Host "  [2] Setup Figma Plugin          - Compile and install Figma plugin" -ForegroundColor Yellow
    Write-Host "  [3] Run DaVinci Import           - Import Figma data to DaVinci Resolve" -ForegroundColor Yellow
    Write-Host "  [4] Run All Steps                - Complete end-to-end workflow" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  [H] Help & Instructions          - Show detailed workflow guide" -ForegroundColor Gray
    Write-Host "  [Q] Quit                         - Exit this script" -ForegroundColor Gray
    Write-Host ""
}

function Show-Help {
    Clear-Host
    Show-Header
    Write-Host "=== FIGMA TO DAVINCI BRIDGE - WORKFLOW GUIDE ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This system creates a bridge between Figma designs and DaVinci Resolve:" -ForegroundColor White
    Write-Host ""
    Write-Host "🏗️  ARCHITECTURE:" -ForegroundColor Yellow
    Write-Host "   • Flask Bridge Server: Temporary storage for design data" -ForegroundColor Gray
    Write-Host "   • Figma Plugin: Exports selected elements as JSON + images" -ForegroundColor Gray
    Write-Host "   • DaVinci Script: Creates Fusion nodes from exported data" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📋 COMPLETE WORKFLOW:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1️⃣  START BRIDGE SERVER" -ForegroundColor Green
    Write-Host "   • Runs Flask server on localhost:5000" -ForegroundColor Gray
    Write-Host "   • Provides REST API for data transfer" -ForegroundColor Gray
    Write-Host "   • Keep this running during the entire workflow" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2️⃣  SETUP FIGMA PLUGIN" -ForegroundColor Green
    Write-Host "   • Compiles TypeScript plugin code" -ForegroundColor Gray
    Write-Host "   • Provides installation instructions" -ForegroundColor Gray
    Write-Host "   • Install in Figma Desktop: Plugins > Development > Import plugin..." -ForegroundColor Gray
    Write-Host ""
    Write-Host "3️⃣  EXPORT FROM FIGMA" -ForegroundColor Green
    Write-Host "   • Select elements in your Figma canvas" -ForegroundColor Gray
    Write-Host "   • Run the installed plugin: Plugins > Figma to DaVinci Bridge" -ForegroundColor Gray
    Write-Host "   • Click 'Export to DaVinci' to send data to bridge server" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4️⃣  IMPORT TO DAVINCI RESOLVE" -ForegroundColor Green
    Write-Host "   • Open DaVinci Resolve with a project" -ForegroundColor Gray
    Write-Host "   • Run the import script (Step 3)" -ForegroundColor Gray
    Write-Host "   • Creates new composition with Fusion nodes" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🎯 SUPPORTED ELEMENTS:" -ForegroundColor Yellow
    Write-Host "   • Text → Text+ nodes with positioning and styling" -ForegroundColor Gray
    Write-Host "   • Rectangles → sRectangle nodes with colors and corner radius" -ForegroundColor Gray
    Write-Host "   • Images/Vectors → Loader nodes with positioning" -ForegroundColor Gray
    Write-Host "   • Groups/Frames → Merged compositions with child elements" -ForegroundColor Gray
    Write-Host ""
    Write-Host "⚠️  REQUIREMENTS:" -ForegroundColor Yellow
    Write-Host "   • Python 3.7+ (for bridge server and DaVinci script)" -ForegroundColor Gray
    Write-Host "   • Node.js & npm (optional, for TypeScript compilation)" -ForegroundColor Gray
    Write-Host "   • Figma Desktop (for plugin installation)" -ForegroundColor Gray
    Write-Host "   • DaVinci Resolve 17+ (for Fusion integration)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press any key to return to main menu..." -ForegroundColor White
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

function Start-BridgeServer {
    Show-Header
    Write-Host "Starting Bridge Server..." -ForegroundColor Cyan
    Write-Host ""
    & (Join-Path $PSScriptRoot "1-start-bridge-server.ps1")
}

function Setup-FigmaPlugin {
    Show-Header
    Write-Host "Setting up Figma Plugin..." -ForegroundColor Cyan
    Write-Host ""
    & (Join-Path $PSScriptRoot "2-setup-figma-plugin.ps1")
}

function Run-DaVinciImport {
    Show-Header
    Write-Host "Running DaVinci Resolve Import..." -ForegroundColor Cyan
    Write-Host ""
    & (Join-Path $PSScriptRoot "3-run-davinci-import.ps1")
}

function Run-AllSteps {
    Show-Header
    Write-Host "Running Complete Workflow..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This will run all steps sequentially:" -ForegroundColor Yellow
    Write-Host "1. Setup Figma Plugin (compilation only)" -ForegroundColor Gray
    Write-Host "2. Start Bridge Server (you'll need to stop it manually)" -ForegroundColor Gray
    Write-Host "3. Import to DaVinci (after you export from Figma)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Note: You'll need to manually install the Figma plugin and export data" -ForegroundColor Yellow
    Write-Host "between steps. Continue? (y/N): " -NoNewline -ForegroundColor White
    
    $continue = Read-Host
    if ($continue -ne "y" -and $continue -ne "Y") {
        return
    }
    
    Write-Host ""
    Write-Host "Step 1/3: Setting up Figma Plugin..." -ForegroundColor Cyan
    Setup-FigmaPlugin
    
    Write-Host ""
    Write-Host "Step 2/3: Starting Bridge Server..." -ForegroundColor Cyan
    Write-Host "The server will start in a new window. Keep it running!" -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$(Join-Path $PSScriptRoot '1-start-bridge-server.ps1')`""
    
    Write-Host ""
    Write-Host "Bridge server is starting in a separate window..." -ForegroundColor Green
    Write-Host ""
    Write-Host "Now:" -ForegroundColor Yellow
    Write-Host "1. Install the Figma plugin (follow instructions from Step 1)" -ForegroundColor Gray
    Write-Host "2. Export your design from Figma using the plugin" -ForegroundColor Gray
    Write-Host "3. Come back here and press any key to run DaVinci import..." -ForegroundColor Gray
    Write-Host ""
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    
    Write-Host ""
    Write-Host "Step 3/3: Running DaVinci Import..." -ForegroundColor Cyan
    Run-DaVinciImport
}

# Handle command line parameters
if ($StartBridge) {
    Start-BridgeServer
    return
}

if ($SetupFigma) {
    Setup-FigmaPlugin
    return
}

if ($RunImport) {
    Run-DaVinciImport
    return
}

if ($All) {
    Run-AllSteps
    return
}

# Interactive mode
do {
    Show-Header
    Show-Menu
    
    Write-Host "Enter your choice (1-4, H, Q): " -NoNewline -ForegroundColor White
    $choice = Read-Host
    Write-Host ""
    
    switch ($choice.ToUpper()) {
        "1" { Start-BridgeServer }
        "2" { Setup-FigmaPlugin }
        "3" { Run-DaVinciImport }
        "4" { Run-AllSteps }
        "H" { Show-Help }
        "Q" { 
            Write-Host "Thanks for using Figma to DaVinci Bridge! 👋" -ForegroundColor Cyan
            return 
        }
        default { 
            Write-Host "Invalid choice. Please enter 1-4, H, or Q." -ForegroundColor Red
            Start-Sleep 2
        }
    }
    
    if ($choice -ne "H" -and $choice.ToUpper() -ne "Q") {
        Write-Host ""
        Write-Host "Press any key to return to main menu..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    
} while ($choice.ToUpper() -ne "Q")
