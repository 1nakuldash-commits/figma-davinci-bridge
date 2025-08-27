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
echo [1/4] Setting up the environment...
echo This may take a moment on the first run.
echo.

:: --- Setup and run Flask Bridge Server ---
cd flask-bridge
echo Checking server dependencies...
if not exist venv (
    echo Creating server virtual environment...
    python -m venv venv
    echo Installing server requirements...
    call venv\\Scripts\\activate.bat
    pip install -r requirements.txt
)
echo Starting Flask bridge server in a new window...
START "Logix Bridge Server" cmd /c "title Logix Bridge Server && call venv\\Scripts\\activate.bat && echo Server is running at http://localhost:5000 && python app.py"
cd ..
echo.

echo [2/4] Waiting for server to initialize...
timeout /t 5 /nobreak > nul
echo.

:: --- Setup and run DaVinci Resolve Import Script ---
echo [3/4] Setting up DaVinci Resolve import script...
cd davinci-script
echo Checking import script dependencies...
if not exist venv (
    echo Creating script virtual environment...
    python -m venv venv
    echo Installing script requirements...
    call venv\\Scripts\\activate.bat
    pip install -r requirements.txt
)
echo.
echo [4/4] Running DaVinci Resolve import script...
echo Please follow the prompts in this window.
echo.
call venv\\Scripts\\activate.bat
python figma_to_fusion.py
cd ..
echo.

echo.
echo Workflow script finished.
echo The server window will remain open. You can close it manually when you are done.
echo This window will now close.
timeout /t 15
exit
