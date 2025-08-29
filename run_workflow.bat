@echo off
:: ============================================================================
:: Logix Project - Automated Workflow Runner
:: ============================================================================
:: This script starts the Logix Bridge Server.
::
:: Instructions:
:: 1. Make sure you have Python 3 installed.
:: 2. Double-click this file to start the server.
:: 3. Follow the on-screen instructions.
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
echo  ========================= IMPORTANT NEXT STEP ============================
echo.
echo  Your work is not finished! You must now go into DaVinci Resolve.
echo.
echo  From the top menu, run the script at:
echo  Workspace -> Scripts -> Comp -> figma_to_fusion
echo.
echo  ============================================================================
echo.
PAUSE
exit
