@echo off
chcp 65001 >nul
cd /d E:\TradingSystem

echo ============================================
echo    AutoGPT Trading System - Fixed Startup
echo    (解决UAC问题，自动布局窗口)
echo ============================================
echo.

echo [1/7] 检查Python包...
call :check_package MetaTrader5
call :check_package pyautogui
call :check_package flask
call :check_package requests

echo [2/7] 启动MT5 (使用PowerShell绕过UAC)...
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    powershell -Command "Start-Process -FilePath 'C:\Program Files\MetaTrader 5\terminal64.exe' -WindowStyle Normal"
    echo     MT5已启动 (64-bit)
) else if exist "C:\Program Files (x86)\MetaTrader 5\terminal.exe" (
    powershell -Command "Start-Process -FilePath 'C:\Program Files (x86)\MetaTrader 5\terminal.exe' -WindowStyle Normal"
    echo     MT5已启动 (32-bit)
) else (
    echo     MT5未找到，请手动启动
    pause
    exit /b 1
)

timeout /t 10 /nobreak >nul

echo [3/7] 启动Flask Web服务器...
start "" /B python web_interface.py
timeout /t 5 /nobreak >nul

echo [4/7] 启动Executor...
start "" /B python executor_agent.py
timeout /t 3 /nobreak >nul

echo [5/7] 启动窗口管理器...
start "" /B python window_manager.py
timeout /t 2 /nobreak >nul

echo [6/7] 打开浏览器...
start "" msedge --new-window "http://127.0.0.1:5000"
timeout /t 3 /nobreak >nul

echo [7/7] 检查系统状态...
echo.
echo ============================================
echo    系统启动完成！
echo ============================================
echo.
echo 窗口布局:
echo   MT5: 屏幕左侧
echo   AutoGPT Web界面: 屏幕右侧 (http://127.0.0.1:5000)
echo.
echo 下一步:
echo   1. 等待MT5完全加载
echo   2. 在Web界面中设置交易品种和策略
echo   3. 点击"校准"按钮设置MT5按钮位置
echo   4. 切换到"自动盯盘"模式
echo.
echo 如果MT5未出现在左侧，请运行: python window_manager.py
echo.
pause
exit /b 0

:check_package
set package=%1
pip show %package% >nul 2>&1
if errorlevel 1 (
    echo     安装%package%...
    pip install %package% -q
) else (
    echo     %package%已安装
)
exit /b 0