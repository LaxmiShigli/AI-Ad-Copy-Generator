@echo off
echo.
echo  ================================
echo   AdForge AI - Setup and Launch
echo  ================================
echo.

:: Install dependencies
echo [1/2] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2/2] Starting AdForge AI...
echo.
echo  Open your browser at: http://127.0.0.1:5000
echo  Press Ctrl+C to stop the server.
echo.

python app.py
pause
