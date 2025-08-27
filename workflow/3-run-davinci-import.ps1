# Run DaVinci Resolve Import Script
# This script sets up and runs the Python script to import Figma data into DaVinci Resolve

Write-Host "=== Figma to DaVinci Bridge - Step 3: Import to DaVinci Resolve ===" -ForegroundColor Cyan
Write-Host ""

# Navigate to davinci-script directory
$davinciDir = Join-Path $PSScriptRoot "..\davinci-script"
if (-not (Test-Path $davinciDir)) {
    Write-Host "Error: DaVinci script directory not found: $davinciDir" -ForegroundColor Red
    exit 1
}

Set-Location $davinciDir
Write-Host "Navigated to: $davinciDir" -ForegroundColor Green

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
Write-Host "=== DaVinci Resolve Setup Check ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Before running the import script, please ensure:" -ForegroundColor White
Write-Host "1. ✅ DaVinci Resolve is open" -ForegroundColor Yellow
Write-Host "2. ✅ A project is currently open in DaVinci Resolve" -ForegroundColor Yellow
Write-Host "3. ✅ The Flask bridge server is running (Step 1)" -ForegroundColor Yellow
Write-Host "4. ✅ You have exported data from Figma (Step 2)" -ForegroundColor Yellow
Write-Host ""

# Check if bridge server is accessible
Write-Host "Checking bridge server connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method Get -TimeoutSec 5
    if ($response.status -eq "healthy") {
        Write-Host "✅ Bridge server is running and accessible" -ForegroundColor Green
        Write-Host "   Stored datasets: $($response.stored_datasets)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  Bridge server responded but status is: $($response.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Could not connect to bridge server at localhost:5000" -ForegroundColor Red
    Write-Host "   Please make sure Step 1 (Start Bridge Server) is running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Continue anyway? (y/N): " -NoNewline -ForegroundColor White
    $continue = Read-Host
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Aborting. Please start the bridge server first." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Starting DaVinci Resolve import..." -ForegroundColor Cyan
Write-Host ""

# Check for available data
Write-Host "Checking for available datasets..." -ForegroundColor Yellow
try {
    $listResponse = Invoke-RestMethod -Uri "http://localhost:5000/list_data" -Method Get -TimeoutSec 5
    if ($listResponse.success -and $listResponse.datasets.Count -gt 0) {
        Write-Host "Found $($listResponse.datasets.Count) available dataset(s):" -ForegroundColor Green
        for ($i = 0; $i -lt $listResponse.datasets.Count; $i++) {
            $dataset = $listResponse.datasets[$i]
            Write-Host "  [$($i + 1)] $($dataset.id) - $($dataset.element_count) elements - $($dataset.timestamp)" -ForegroundColor Gray
        }
        Write-Host ""
        
        if ($listResponse.datasets.Count -gt 1) {
            Write-Host "Select dataset to import (1-$($listResponse.datasets.Count), or Enter for most recent): " -NoNewline -ForegroundColor White
            $selection = Read-Host
            
            if ($selection -match '^\d+$' -and [int]$selection -ge 1 -and [int]$selection -le $listResponse.datasets.Count) {
                $selectedDataset = $listResponse.datasets[[int]$selection - 1]
                Write-Host "Selected dataset: $($selectedDataset.id)" -ForegroundColor Green
                $dataId = $selectedDataset.id
            } else {
                Write-Host "Using most recent dataset" -ForegroundColor Green
                $dataId = $null
            }
        } else {
            Write-Host "Using the only available dataset" -ForegroundColor Green
            $dataId = $null
        }
    } else {
        Write-Host "No datasets found. Make sure you have exported data from Figma first." -ForegroundColor Yellow
        $dataId = $null
    }
} catch {
    Write-Host "Could not retrieve dataset list. Will attempt to use most recent data." -ForegroundColor Yellow
    $dataId = $null
}

Write-Host ""
Write-Host "Running DaVinci Resolve import script..." -ForegroundColor Cyan
Write-Host "Note: This script will create a new composition in DaVinci Resolve" -ForegroundColor Yellow
Write-Host ""

# Run the import script
if ($dataId) {
    python figma_to_fusion.py $dataId
} else {
    python figma_to_fusion.py
}

Write-Host ""
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Import script completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Check DaVinci Resolve for the new composition with imported Figma elements." -ForegroundColor White
} else {
    Write-Host "❌ Import script failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "- DaVinci Resolve is not running or no project is open" -ForegroundColor Gray
    Write-Host "- Bridge server is not accessible" -ForegroundColor Gray
    Write-Host "- No data available from Figma export" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
