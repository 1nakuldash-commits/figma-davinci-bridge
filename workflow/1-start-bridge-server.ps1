# Start Flask Bridge Server
# This script sets up and starts the Flask bridge server

Write-Host "=== Figma to DaVinci Bridge - Step 1: Start Bridge Server ===" -ForegroundColor Cyan
Write-Host ""

# Navigate to flask-bridge directory
$bridgeDir = Join-Path $PSScriptRoot "..\flask-bridge"
if (-not (Test-Path $bridgeDir)) {
    Write-Host "Error: Flask bridge directory not found: $bridgeDir" -ForegroundColor Red
    exit 1
}

Set-Location $bridgeDir
Write-Host "Navigated to: $bridgeDir" -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not available. Please install Python 3.7+ and try again." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists, if not create it
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Install requirements
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies installed successfully!" -ForegroundColor Green

Write-Host ""
Write-Host "Starting Flask bridge server..." -ForegroundColor Cyan
Write-Host "Server will be available at: http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Endpoints:" -ForegroundColor White
Write-Host "  POST /send_data - Receive data from Figma plugin" -ForegroundColor Gray
Write-Host "  GET  /get_data  - Retrieve data for DaVinci Resolve" -ForegroundColor Gray
Write-Host "  GET  /list_data - List all available datasets" -ForegroundColor Gray
Write-Host "  GET  /health    - Health check" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python app.py
