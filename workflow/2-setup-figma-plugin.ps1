# Setup Figma Plugin
# This script compiles the TypeScript plugin and provides installation instructions

Write-Host "=== Figma to DaVinci Bridge - Step 2: Setup Figma Plugin ===" -ForegroundColor Cyan
Write-Host ""

# Navigate to figma-plugin directory
$pluginDir = Join-Path $PSScriptRoot "..\figma-plugin"
if (-not (Test-Path $pluginDir)) {
    Write-Host "Error: Figma plugin directory not found: $pluginDir" -ForegroundColor Red
    exit 1
}

Set-Location $pluginDir
Write-Host "Navigated to: $pluginDir" -ForegroundColor Green

# Check if Node.js is available
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Found Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Warning: Node.js not found. You may need to install it to compile TypeScript." -ForegroundColor Yellow
    Write-Host "However, you can still install the plugin manually in Figma Desktop." -ForegroundColor Yellow
}

# Check if npm is available and install dependencies
try {
    $npmVersion = npm --version 2>&1
    Write-Host "Found npm: $npmVersion" -ForegroundColor Green
    
    # Install dependencies
    if (Test-Path "package.json") {
        Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Dependencies installed successfully!" -ForegroundColor Green
            
            # Compile TypeScript
            Write-Host "Compiling TypeScript..." -ForegroundColor Yellow
            npm run build-once
            if ($LASTEXITCODE -eq 0) {
                Write-Host "TypeScript compiled successfully!" -ForegroundColor Green
            } else {
                Write-Host "Warning: TypeScript compilation failed. You can still install the plugin manually." -ForegroundColor Yellow
            }
        } else {
            Write-Host "Warning: Failed to install dependencies. You can still install the plugin manually." -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "Warning: npm not found. You can still install the plugin manually." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Figma Plugin Installation Instructions ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open Figma Desktop application" -ForegroundColor White
Write-Host "2. Go to Plugins > Development > Import plugin from manifest..." -ForegroundColor White
Write-Host "3. Navigate to and select the manifest.json file in this directory:" -ForegroundColor White
Write-Host "   $pluginDir\manifest.json" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. The plugin will be added to your Figma plugins list" -ForegroundColor White
Write-Host "5. To use the plugin:" -ForegroundColor White
Write-Host "   - Select elements in your Figma canvas" -ForegroundColor Gray
Write-Host "   - Go to Plugins > Development > Figma to DaVinci Bridge" -ForegroundColor Gray
Write-Host "   - Click 'Export to DaVinci' in the plugin UI" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: Make sure the Flask bridge server (Step 1) is running before using the plugin!" -ForegroundColor Yellow
Write-Host ""

# Check if code.js exists (compiled TypeScript)
if (Test-Path "code.js") {
    Write-Host "✅ Plugin is ready to install (code.js found)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Plugin needs manual setup (code.js not found)" -ForegroundColor Yellow
    Write-Host "   You can either:" -ForegroundColor White
    Write-Host "   - Install Node.js and run this script again to compile TypeScript" -ForegroundColor Gray
    Write-Host "   - Manually rename code.ts to code.js (basic setup)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
