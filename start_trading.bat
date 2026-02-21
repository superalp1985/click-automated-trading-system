@echo off
chcp 65001 >nul
cd /d E:\TradingSystem

echo ============================================
echo    AutoGPT Trading System - Startup
echo ============================================
echo.

REM Install required packages
echo [1/7] Checking Python packages...
pip show opencv-python >nul 2>&1
if errorlevel 1 (
    echo     Installing OpenCV...
    pip install opencv-python -q
)

pip show pillow >nul 2>&1
if errorlevel 1 (
    pip install pillow -q
)

pip show MetaTrader5 >nul 2>&1
if errorlevel 1 (
    pip install MetaTrader5 -q
)

pip show pyautogui >nul 2>&1
if errorlevel 1 (
    pip install pyautogui -q
)

pip show pywin32 >nul 2>&1
if errorlevel 1 (
    pip install pywin32 -q
)

echo [2/7] Starting MT5...
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    start "" "C:\Program Files\MetaTrader 5\terminal64.exe"
    echo     MT5 started (64-bit)
) else if exist "C:\Program Files (x86)\MetaTrader 5\terminal.exe" (
    start "" "C:\Program Files (x86)\MetaTrader 5\terminal.exe"
    echo     MT5 started (32-bit)
) else (
    echo     MT5 not found
)

timeout /t 8 /nobreak >nul

echo [3/7] Starting Flask web server...
start "" python web_interface.py

timeout /t 5 /nobreak >nul

echo [4/7] Starting AutoGPT trading engine...
start "AutoGPT Trading" cmd /k "cd /d E:\TradingSystem && python autogpt_trading.py"
timeout /t 5 /nobreak >nul

echo [5/7] Starting Executor...
start "" python executor_agent.py

echo [6/7] Opening Edge browser...
start "" msedge --new-window "http://127.0.0.1:5000"

echo.
echo ============================================
echo    System Started!
echo ============================================
echo.
echo MT5: Left side of screen
echo AutoGPT: http://127.0.0.1:5000
echo.
echo Next step: Run "calibrate" in Executor
echo.
pause
