@echo off
:: ============================================================================
:: Logix Project - Automated Workflow Runner
:: ============================================================================
:: This script automates the process of running the Figma-to-DaVinci bridge.
:: It performs the following steps:
:: 1. Starts the Python Flask server in a new window.
:: 2. Waits a few seconds for the server to initialize.
:: 3. Runs the Python script to import the data into DaVinci Resolve.
::
:: Instructions:
:: 1. Make sure you have Python 3 installed.
:: 2. Simply double-click this file to run the workflow.
:: ============================================================================

echo.
echo =======================================================
echo.
echo  🎬 Logix - Figma to DaVinci Automated Workflow
echo.
echo =======================================================
echo [1/2] Setting up the Bridge Server environment...
echo This may take a moment on the first run.
echo.

:: --- Setup and run Flask Bridge Server ---
cd flask-bridge
if not exist venv (
    echo Creating server virtual environment...
    python -m venv venv
    echo Installing server requirements...
    call venv\\Scripts\\activate.bat
    pip install -r requirements.txt
)
cd ..
echo.

echo [2/2] Starting the Bridge Server...
START "Logix Bridge Server" cmd /c "title Logix Bridge Server && cd flask-bridge && call venv\\Scripts\\activate.bat && echo Server is running at http://localhost:5000 && python app.py"
echo.
echo ============================================================================
echo.
echo  ✅ The Logix Bridge Server has been started in a new window.
echo     You can minimize the server window, but do not close it.
echo.
echo  Next Steps:
echo  1. Open Figma and use the 'Logix' plugin to export your elements.
echo  2. Open DaVinci Resolve and run the 'figma_to_fusion' script.
echo.
echo ============================================================================
echo.
echo This window will now close.
timeout /t 10
exit
