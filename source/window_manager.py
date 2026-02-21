"""
Window Manager - Position MT5 and browser windows
"""

import time
import subprocess
import pyautogui
import pygetwindow as gw
import sys

def position_windows():
    """Position MT5 on left half and browser on right half of screen"""
    print("定位窗口...")
    time.sleep(5)  # Wait for windows to open
    
    try:
        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        half_width = screen_width // 2
        
        # Find MT5 window
        mt5_windows = []
        for window in gw.getAllWindows():
            if 'MetaTrader 5' in window.title or 'MetaTrader5' in window.title:
                mt5_windows.append(window)
        
        if mt5_windows:
            mt5 = mt5_windows[0]  # Use first MT5 window
            print(f"找到MT5窗口: {mt5.title}")
            # Move to left half
            mt5.moveTo(0, 0)
            mt5.resizeTo(half_width - 2, screen_height - 50)
            print("MT5已移动到屏幕左侧")
        else:
            print("未找到MT5窗口")
        
        # Find browser windows (Edge, Chrome, etc.)
        browser_windows = []
        browser_keywords = ['Edge', 'Chrome', 'Firefox', 'Safari', '127.0.0.1:5000', 'AutoGPT']
        for window in gw.getAllWindows():
            for keyword in browser_keywords:
                if keyword in window.title:
                    browser_windows.append(window)
                    break
        
        if browser_windows:
            browser = browser_windows[0]
            print(f"找到浏览器窗口: {browser.title}")
            # Move to right half
            browser.moveTo(half_width + 2, 0)
            browser.resizeTo(half_width - 4, screen_height - 50)
            print("浏览器已移动到屏幕右侧")
        else:
            print("未找到浏览器窗口，将尝试打开")
            # Try to open browser
            try:
                subprocess.Popen(['msedge', '--new-window', 'http://127.0.0.1:5000'])
                time.sleep(3)
                # Try to position it
                for window in gw.getAllWindows():
                    if 'Edge' in window.title or '127.0.0.1:5000' in window.title:
                        window.moveTo(half_width + 2, 0)
                        window.resizeTo(half_width - 4, screen_height - 50)
                        print("新浏览器窗口已定位")
                        break
            except:
                print("无法打开浏览器")
        
        print("窗口定位完成")
        return True
        
    except Exception as e:
        print(f"窗口定位错误: {str(e)}")
        return False

def check_mt5_running():
    """Check if MT5 is running"""
    for window in gw.getAllWindows():
        if 'MetaTrader 5' in window.title or 'MetaTrader5' in window.title:
            return True
    return False

def main():
    print("窗口管理器启动")
    print("等待窗口打开...")
    
    # Wait a bit longer for windows to appear
    time.sleep(10)
    
    # Try positioning
    success = position_windows()
    
    if success:
        print("✅ 窗口定位成功")
        print("MT5: 左侧")
        print("AutoGPT Web界面: 右侧 (http://127.0.0.1:5000)")
    else:
        print("⚠️ 窗口定位可能未完成，请手动调整")
    
    # Keep script running to maintain window positions
    print("窗口管理器运行中，按Ctrl+C退出")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("窗口管理器已退出")

if __name__ == "__main__":
    main()