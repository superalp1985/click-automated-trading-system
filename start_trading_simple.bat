@echo off
cd /d E:\TradingSystem
echo ============================================
echo AutoGPT Trading System
echo ============================================
echo.

echo Starting MT5...
start "" "C:\Program Files\MetaTrader 5\terminal64.exe"
timeout 5 /nobreak >nul

echo Starting Flask...
start "" python web_interface.py
timeout /t 3 /nobreak >nul

echo Starting AutoGPT...
start "AutoGPT Trading" cmd /k "cd /d E:\TradingSystem && python autogpt_trading.py"
timeout /t 5 /nobreak >nul

echo Starting Executor...
start "" python executor_agent.py
timeout /t 2 /nobreak >nul

echo Opening Browser...
start "" msedge --new-window "http://127.0.0.1:5000"

echo.
echo ============================================
echo System Started!
echo ============================================
echo.
echo MT5: Left side
echo AutoGPT: http://127.0.0.1:5000
echo.
pause