@echo off
chcp 65001 >nul
cd /d E:\TradingSystem

echo ============================================
echo    AutoGPT Trading System - Fixed Version
echo ============================================
echo.

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或不在PATH中
    echo 请安装Python 3.8+并添加到系统PATH
    pause
    exit /b 1
)

echo.
echo 检查必要模块...
python -c "import flask, requests, MetaTrader5" >nul 2>&1
if errorlevel 1 (
    echo 警告: 某些Python模块可能未安装
    echo 将尝试继续运行...
)

echo.
echo 第1步: 启动MT5 (如果尚未运行)...
tasklist | findstr /i "terminal64.exe" >nul
if errorlevel 1 (
    echo 启动MT5终端...
    start "" "C:\Program Files\MetaTrader 5\terminal64.exe"
    timeout /t 8 /nobreak >nul
    echo 等待MT5加载完成...
) else (
    echo MT5已在运行
)

echo.
echo 第2步: 启动Flask Web服务器...
tasklist | findstr /i "python.*web_interface" >nul
if errorlevel 1 (
    echo 启动Flask服务器...
    start "Flask Web Server" python web_interface.py
    timeout /t 5 /nobreak >nul
    
    echo 检查Flask服务器状态...
    python -c "import urllib.request; import json; import sys; url='http://127.0.0.1:5000/'; try: r=urllib.request.urlopen(url); print('✓ Flask服务器正常'); sys.exit(0); except: print('✗ Flask服务器异常'); sys.exit(1)" >nul 2>&1
    if errorlevel 1 (
        echo 错误: Flask服务器启动失败，请检查控制台输出
        timeout /t 3 /nobreak >nul
    ) else (
        echo ✓ Flask服务器已启动: http://127.0.0.1:5000
    )
) else (
    echo Flask服务器已在运行
)

echo.
echo 第3步: 启动AutoGPT主程序...
tasklist | findstr /i "python.*autogpt_trading" >nul
if errorlevel 1 (
    echo 启动AutoGPT...
    start "AutoGPT Trading" python autogpt_trading.py
    timeout /t 3 /nobreak >nul
    echo ✓ AutoGPT已启动
) else (
    echo AutoGPT已在运行
)

echo.
echo 第4步: 启动Executor...
tasklist | findstr /i "python.*executor_agent" >nul
if errorlevel 1 (
    echo 启动Executor...
    start "Executor Agent" python executor_agent.py
    timeout /t 2 /nobreak >nul
    echo ✓ Executor已启动
) else (
    echo Executor已在运行
)

echo.
echo 第5步: 打开浏览器...
echo 打开Edge浏览器访问Web界面...
start "" msedge --new-window "http://127.0.0.1:5000"

echo.
echo 第6步: 自动窗口布局 (如果可用)...
if exist window_manager.py (
    echo 执行窗口布局调整...
    start "" python window_manager.py
) else (
    echo 窗口布局脚本不存在，跳过...
)

echo.
echo ============================================
echo    系统启动完成!
echo ============================================
echo.
echo 组件状态:
echo - MT5终端: 运行中
echo - Flask服务器: http://127.0.0.1:5000
echo - AutoGPT: 运行中
echo - Executor: 运行中
echo.
echo 重要提示:
echo 1. 如果看到404错误，可能是favicon.ico请求导致的，不影响功能
echo 2. 首次使用请等待MT5完全加载后再进行操作
echo 3. 在Web界面中配置交易品种和策略
echo 4. 实时日志将在"Logs"区域显示扫描、分析、执行全过程
echo.
echo 手动窗口布局建议:
echo - 将MT5拖动到屏幕左侧
echo - 将浏览器拖动到屏幕右侧
echo.
pause