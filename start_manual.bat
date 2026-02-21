@echo off
chcp 65001 >nul
cd /d E:\TradingSystem

echo ============================================
echo    AutoGPT Trading System - Manual Start
echo    (手动启动指南，绕过所有UAC限制)
echo ============================================
echo.

echo 由于UAC限制，请按以下顺序手动启动：
echo.
echo 1. 首先手动启动MT5:
echo    - 双击桌面上的MetaTrader 5图标
echo    - 或运行: C:\Program Files\MetaTrader 5\terminal64.exe
echo.
echo 2. 等待MT5完全加载后，按任意键继续...
pause >nul

echo.
echo 3. 启动Flask Web服务器 (新窗口):
echo    - 按任意键打开Web服务器...
pause >nul
start "" python web_interface.py
timeout /t 3 /nobreak >nul

echo.
echo 4. 启动AutoGPT主程序 (新窗口):
echo    - 按任意键打开AutoGPT交易引擎...
pause >nul
start "AutoGPT Trading" cmd /k "cd /d E:\TradingSystem && python autogpt_trading.py"
timeout /t 8 /nobreak >nul

echo.
echo 5. 启动Executor (新窗口):
echo    - 按任意键打开Executor...
pause >nul
start "" python executor_agent.py
timeout /t 2 /nobreak >nul

echo.
echo 6. 打开浏览器 (新窗口):
echo    - 按任意键打开浏览器...
pause >nul
start "" msedge --new-window "http://127.0.0.1:5000"
timeout /t 3 /nobreak >nul

echo.
echo 7. 窗口布局调整:
echo    - 按任意键调整窗口位置...
pause >nul
start "" python window_manager.py

echo.
echo ============================================
echo    系统启动完成！
echo ============================================
echo.
echo 请手动调整窗口布局:
echo   1. 将MT5窗口拖动到屏幕左侧
echo   2. 将浏览器窗口拖动到屏幕右侧
echo   3. 调整窗口大小使其各占一半屏幕
echo.
echo Web界面: http://127.0.0.1:5000
echo.
echo 下一步:
echo   1. 在Web界面中设置交易品种和策略
echo   2. 点击"校准"按钮设置MT5按钮位置
echo   3. 切换到"自动盯盘"模式
echo.
pause