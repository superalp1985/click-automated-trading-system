@echo off
chcp 65001 >nul
echo ============================================
echo   AutoGPT Trading System 恢复脚本（最终版本）
echo ============================================
echo.

echo 警告: 此操作将覆盖当前目录中的文件！
echo 此备份包含最终版本修改（移除重试机制）。
echo.
set /p confirm="确认要恢复备份吗？(y/n): "
if /i not "%confirm%"=="y" (
    echo 恢复操作已取消。
    pause
    exit /b 0
)

echo.
echo [1/7] 恢复主程序文件...
copy autogpt_trading.py ..\autogpt_trading.py /Y
copy executor_agent.py ..\executor_agent.py /Y
copy web_interface.py ..\web_interface.py /Y

echo [2/7] 恢复配置文件...
copy config.json ..\config.json /Y
copy mt5_positions.json ..\mt5_positions.json /Y

echo [3/7] 恢复启动脚本...
copy start_trading_fixed.bat ..\start_trading_fixed.bat /Y
copy start_manual.bat ..\start_manual.bat /Y
copy window_manager.py ..\window_manager.py /Y

echo [4/7] 恢复修改记录...
copy executor_changes_20260220_2224.txt ..\executor_changes_20260220_2224.txt /Y

echo [5/7] 恢复模板文件...
if exist templates (
    xcopy templates ..\templates /E /I /Y
) else (
    echo templates目录不存在，跳过
)

echo [6/7] 系统状态检查...
echo 最终版本特性:
echo   1. 快速失败机制: 出错立即放弃，不重试
echo   2. 窗口激活: 0.05秒等待（用户手动确保MT5在前台）
echo   3. 价格输出: AutoGPT输出具体价格数值
echo   4. 推荐启动: start_manual.bat（避开UAC）

echo.
echo [7/7] 恢复完成！
echo.
echo 下一步:
echo   1. 启动MT5并登录
echo   2. 运行 start_manual.bat 启动系统
echo   3. 在Web界面 (http://127.0.0.1:5000) 进行校准
echo   4. 手动切换到MT5窗口（系统激活只需0.05秒）
echo   5. 设置交易策略并开始盯盘
echo.
echo 重要: 此版本使用快速失败机制，任何操作失败都会立即放弃，
echo       等待下次交易机会出现。
echo.
echo ============================================
echo  最终版本恢复完成 - 2026-02-20 22:26
echo ============================================
echo.
pause