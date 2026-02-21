"""
Executor Agent - Controls MT5 via PyAutoGUI + OpenCV Image Recognition
Monitors commands and executes trades by recognizing MT5 buttons and clicking
"""

import os
import sys
import time
import json
import threading
import pyautogui
import numpy as np
from datetime import datetime
import requests

# Try to import pyperclip for copy-paste
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("[WARNING] pyperclip not installed. Install with: pip install pyperclip")

# Try to import OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("[WARNING] OpenCV not available, using fallback mode")

# Try to import MT5 for API verification
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("[WARNING] MetaTrader5 not installed. Install with: pip install MetaTrader5")

# Configuration
COMMANDS_FILE = "E:\\TradingSystem\\commands.txt"
LOG_FILE = "E:\\TradingSystem\\executor.log"
CONFIG_FILE = "E:\\TradingSystem\\config.json"
MT5_WINDOW_TITLE = "MetaTrader 5"

# MT5 window positions (will be calibrated on first run)
MT5_CONFIG_FILE = "E:\\TradingSystem\\mt5_positions.json"

# Button templates directory
TEMPLATES_DIR = "E:\\TradingSystem\\templates"

class ExecutorAgent:
    def __init__(self):
        self.running = True
        self.last_command = ""
        self.mt5_positions = {}
        self.mt5_connected = False
        self.load_positions()

        # PyAutoGUI settings
        pyautogui.PAUSE = 0.01  # Pause between actions (minimum for speed)
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort

        # OpenCV settings - 已禁用，使用坐标点击
        self.use_opencv = False
        self.confidence = 0.8  # Template matching confidence

        # Ensure templates directory exists
        if not os.path.exists(TEMPLATES_DIR):
            os.makedirs(TEMPLATES_DIR)
        
        # Try to connect to MT5 for API verification
        self.connect_mt5()

    def load_positions(self):
        """Load MT5 window positions"""
        if os.path.exists(MT5_CONFIG_FILE):
            try:
                with open(MT5_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.mt5_positions = json.load(f)
            except:
                self.mt5_positions = {}

    def save_positions(self):
        """Save MT5 window positions"""
        with open(MT5_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.mt5_positions, f, indent=2)

    def connect_mt5(self):
        """Connect to MT5 terminal for API verification"""
        if not MT5_AVAILABLE:
            self.log("MT5 API不可用，跳过API验证")
            return False
        
        try:
            # Initialize MT5
            if not mt5.initialize():
                self.log(f"MT5 API初始化失败: {mt5.last_error()}")
                self.mt5_connected = False
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.log("无法获取MT5账户信息")
                self.mt5_connected = False
                return False
            
            self.log(f"MT5 API已连接 - 账户: {account_info.login}, 余额: {account_info.balance}")
            self.mt5_connected = True
            return True
            
        except Exception as e:
            self.log(f"MT5 API连接错误: {str(e)}")
            self.mt5_connected = False
            return False
    
    def check_mt5_positions(self, timeout_seconds=30):
        """Check if new position was opened in MT5 (API verification)"""
        if not self.mt5_connected or not MT5_AVAILABLE:
            self.log("MT5 API未连接，跳过交易验证")
            return False
        
        try:
            # Get initial positions count
            initial_positions = mt5.positions_get()
            initial_count = len(initial_positions) if initial_positions else 0
            self.log(f"初始持仓数: {initial_count}")
            
            # Wait for new position (polling)
            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                current_positions = mt5.positions_get()
                current_count = len(current_positions) if current_positions else 0
                
                if current_count > initial_count:
                    # New position opened
                    self.log(f"交易验证成功: 新持仓已打开 (当前持仓数: {current_count})")
                    return True
                
                time.sleep(1)  # Check every second
            
            # Timeout reached, no new position
            self.log(f"交易验证失败: {timeout_seconds}秒内未检测到新持仓")
            return False
            
        except Exception as e:
            self.log(f"持仓检查错误: {str(e)}")
            return False

    def log(self, message):
        """Log message to file and web interface"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        # Write to log file
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_message + "\n")
        except:
            pass
        
        # Also send to web interface logs
        try:
            requests.post('http://localhost:5000/save_log', 
                         json={'type': 'log', 'message': message},
                         timeout=1)
        except:
            # Web interface might not be running or not accessible
            # Silently ignore errors to avoid disrupting trading
            pass

    def find_mt5_window(self):
        """Find MT5 window"""
        try:
            # Try to find MT5 window
            windows = self.get_windows()
            for title, handle in windows.items():
                if "MetaTrader" in title or "MT5" in title:
                    return title, handle
            return None, None
        except:
            return None, None

    def get_windows(self):
        """Get list of windows (Windows only)"""
        try:
            import win32gui
            windows = {}
            def enum_handler(hwnd, ctx):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        windows[title] = hwnd
            win32gui.EnumWindows(enum_handler, None)
            return windows
        except:
            return {}

    def activate_mt5_window(self):
        """激活MT5窗口，确保窗口处于前台"""
        try:
            import win32gui
            import win32con
            
            mt5_title, handle = self.find_mt5_window()
            if handle:
                # 确保窗口不是最小化
                if win32gui.IsIconic(handle):
                    win32gui.ShowWindow(handle, win32con.SW_RESTORE)
                
                # 激活窗口到前台
                win32gui.SetForegroundWindow(handle)
                
                # 等待窗口完全激活
                time.sleep(0.05)  # 短暂等待
                self.log("✅ MT5窗口已激活")
                return True
            else:
                self.log("❌ 未找到MT5窗口")
                return False
        except Exception as e:
            self.log(f"激活MT5窗口失败: {str(e)}")
            return False

    def find_button_opencv(self, template_name, region=None):
        """Find button using OpenCV template matching"""
        if not self.use_opencv:
            return None

        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

            # Load template
            template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.png")
            if not os.path.exists(template_path):
                self.log(f"模板不存在: {template_path}")
                return None

            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                self.log(f"无法读取模板: {template_path}")
                return None

            # Template matching
            result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= self.confidence:
                # Get center of matched template
                h, w = template.shape
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                self.log(f"找到 {template_name} 位置: ({center_x}, {center_y}), 置信度: {max_val:.2f}")
                return (center_x, center_y)
            else:
                self.log(f"未找到 {template_name}, 最高置信度: {max_val:.2f}")
                return None

        except Exception as e:
            self.log(f"OpenCV匹配错误: {str(e)}")
            return None

    def click_at(self, x, y):
        """Click at specific coordinates"""
        try:
            # 不再激活MT5窗口，直接点击（假设MT5窗口已在前台）
            pyautogui.click(x, y)
            time.sleep(0.3)
            return True
        except Exception as e:
            self.log(f"点击失败: {str(e)}")
            return False

    def find_and_click(self, template_name):
        """Find button and click it"""
        pos = self.find_button_opencv(template_name)
        if pos:
            return self.click_at(pos[0], pos[1])
        return False

    def capture_mt5_screenshot(self, region=None):
        """Capture screenshot of MT5 window"""
        try:
            mt5_title, handle = self.find_mt5_window()
            if not handle:
                self.log("未找到MT5窗口")
                return None

            # Get window bounds
            import win32gui
            left, top, right, bottom = win32gui.GetWindowRect(handle)

            if region:
                # Capture specific region
                screenshot = pyautogui.screenshot(region=(left + region[0], top + region[1], region[2], region[3]))
            else:
                # Capture entire window
                screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))

            return screenshot
        except Exception as e:
            self.log(f"截图失败: {str(e)}")
            return None

    def save_button_template(self, template_name, x, y, width=50, height=30):
        """Save a button template for OpenCV matching"""
        try:
            # Capture area around the specified position
            screenshot = pyautogui.screenshot(region=(x - width//2, y - height//2, width, height))

            # Ensure templates directory exists
            os.makedirs(TEMPLATES_DIR, exist_ok=True)

            # Save template
            template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.png")
            screenshot.save(template_path)

            self.log(f"已保存模板: {template_path}")
            return True
        except Exception as e:
            self.log(f"保存模板失败: {str(e)}")
            return False

    def calibrate_positions(self):
        """Calibrate MT5 window positions"""
        self.log("开始位置校准...")
        self.log("请将鼠标移动到以下位置（停留10秒后自动记录）")

        positions_to_calibrate = [
            "lot_input",        # 交易量输入框
            "sl_input",         # 止损输入框
            "tp_input",         # 止盈输入框
            "buy_btn",          # 按市场价买入按钮
            "sell_btn",         # 按市场价卖出按钮
            "close_btn",        # 平仓按钮
        ]

        for pos_name in positions_to_calibrate:
            print(f"\n请将鼠标移动到 '{pos_name}' 位置...")
            print("10秒后开始记录...")
            time.sleep(10)
            x, y = pyautogui.position()
            self.mt5_positions[pos_name] = {"x": x, "y": y}
            self.log(f"记录 {pos_name}: ({x}, {y})")
            time.sleep(1)

        self.save_positions()
        self.log("位置校准完成！")
        print(f"\n已校准位置: {list(self.mt5_positions.keys())}")

    def click_position(self, pos_name):
        """Click on a calibrated position - tries OpenCV first, then falls back to calibrated positions"""
        # Try OpenCV first if available
        if self.use_opencv:
            pos = self.find_button_opencv(pos_name)
            if pos:
                self.log(f"使用OpenCV点击: {pos_name}")
                return self.click_at(pos[0], pos[1])

        # Fall back to calibrated positions
        if pos_name not in self.mt5_positions:
            self.log(f"位置未校准: {pos_name}")
            return False

        pos = self.mt5_positions[pos_name]

        # 不再激活MT5窗口，直接点击（假设MT5窗口已在前台）
        pyautogui.click(pos['x'], pos['y'])
        time.sleep(0.3)
        return True

    def execute_buy(self, symbol, lot, stop_loss=None, take_profit=None, current_price=None, digits=5, stop_loss_is_percent=False, take_profit_is_percent=False):
        """Execute buy order - with strict timing rules"""
        self.log(f"🟢 执行买入操作 - 止损: {stop_loss}, 止盈: {take_profit}, 当前价格: {current_price}")
        self.log(f"📊 价格类型 - 止损是否为百分比: {stop_loss_is_percent}, 止盈是否为百分比: {take_profit_is_percent}")
        
        # Calculate actual SL/TP prices from percentages
        sl_price = None
        tp_price = None
        
        if current_price is not None and (stop_loss is not None or take_profit is not None):
            # For BUY: SL is below current price, TP is above current price
            if stop_loss is not None:
                if stop_loss_is_percent:
                    # Percentage-based: SL = current_price * (1 - X%)
                    sl_price = round(current_price * (1 - stop_loss/100), digits)
                    self.log(f"📐 计算止损价格(百分比{stop_loss}%): {current_price} * (1 - {stop_loss}/100) = {sl_price}")
                else:
                    # Already actual price - use directly
                    sl_price = stop_loss
                    self.log(f"📏 使用实际止损价格: {sl_price}")
            
            if take_profit is not None:
                if take_profit_is_percent:
                    # Percentage-based: TP = current_price * (1 + X%)
                    tp_price = round(current_price * (1 + take_profit/100), digits)
                    self.log(f"📐 计算止盈价格(百分比{take_profit}%): {current_price} * (1 + {take_profit}/100) = {tp_price}")
                else:
                    # Already actual price - use directly
                    tp_price = take_profit
                    self.log(f"📏 使用实际止盈价格: {tp_price}")
        
        try:
            # 不再激活MT5窗口，直接按F9（假设MT5窗口已在前台）
            self.log("⌨️ 步骤1: 按F9打开订单窗口...")
            pyautogui.press('f9')
            time.sleep(0.8)  # 等待订单窗口完全打开
            self.log("✅ 订单窗口已打开")
            
            # Step 1: Input stop loss price using copy+paste
            if sl_price is not None:
                if "sl_input" in self.mt5_positions:
                    self.log(f"输入止损价格: {sl_price}")
                    self.click_position("sl_input")
                    time.sleep(0.4)  # Rule 4: Click wait
                    # Copy price to clipboard and paste
                    if PYPERCLIP_AVAILABLE:
                        pyperclip.copy(str(sl_price))
                        time.sleep(0.3)  # Rule 2: Activate input box wait
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.2)  # Rule 3: Paste complete wait
                    else:
                        # 直接输入，不使用剪贴板
                        pyautogui.typewrite(str(sl_price))
                        time.sleep(0.3)  # 等待输入完成
                        self.log("警告: pyperclip未安装，使用直接输入")
                else:
                    self.log("警告: 止损输入框位置未校准，跳过止损设置")
            
            time.sleep(0.5)  # Rule 5: Between clicks wait
            
            # Step 2: Input take profit price using copy+paste
            if tp_price is not None:
                if "tp_input" in self.mt5_positions:
                    self.log(f"输入止盈价格: {tp_price}")
                    self.click_position("tp_input")
                    time.sleep(0.4)  # Rule 4: Click wait
                    # Copy price to clipboard and paste
                    if PYPERCLIP_AVAILABLE:
                        pyperclip.copy(str(tp_price))
                        time.sleep(0.3)  # Rule 2: Activate input box wait
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.2)  # Rule 3: Paste complete wait
                    else:
                        # 直接输入，不使用剪贴板
                        pyautogui.typewrite(str(tp_price))
                        time.sleep(0.3)  # 等待输入完成
                        self.log("警告: pyperclip未安装，使用直接输入")
                else:
                    self.log("警告: 止盈输入框位置未校准，跳过止盈设置")
            
            time.sleep(0.5)  # Rule 5: Between clicks wait
            
            # Step 3: Click the buy button
            self.click_position("buy_btn")
            time.sleep(0.8)  # Rule 7: Confirm order wait
            self.log("买入订单已提交")
            return True
            
        except Exception as e:
            self.log(f"买入失败: {str(e)}")
            return False
    
    def _execute_buy_fallback(self, sl_price, tp_price):
        """Fallback if pyperclip not available"""
        self.log("使用备用输入方式...")
        return False
        
    def execute_sell(self, symbol, lot, stop_loss=None, take_profit=None, current_price=None, digits=5, stop_loss_is_percent=False, take_profit_is_percent=False):
        """Execute sell order - 与买入相同的4步流程: 按F9, 输入止损, 输入止盈, 点击卖出按钮"""
        self.log(f"🔴 执行卖出操作 - 止损: {stop_loss}, 止盈: {take_profit}, 当前价格: {current_price}")
        self.log(f"📊 价格类型 - 止损是否为百分比: {stop_loss_is_percent}, 止盈是否为百分比: {take_profit_is_percent}")

        # 直接使用发过来的止损止盈价格，不重新计算
        sl_price = None
        tp_price = None

        if stop_loss is not None:
            if stop_loss_is_percent:
                # 百分比: 需要计算实际价格
                if current_price is not None and current_price > 0:
                    sl_price = round(current_price * (1 + stop_loss/100), digits)
                    self.log(f"📐 计算止损价格(百分比{stop_loss}%): {current_price} * (1 + {stop_loss}/100) = {sl_price}")
                else:
                    self.log("❌ 无法计算止损价格: 当前价格无效")
            else:
                # 已经是实际价格: 直接使用
                sl_price = stop_loss
                self.log(f"📏 使用实际止损价格: {sl_price}")

        if take_profit is not None:
            if take_profit_is_percent:
                # 百分比: 需要计算实际价格
                if current_price is not None and current_price > 0:
                    tp_price = round(current_price * (1 - take_profit/100), digits)
                    self.log(f"📐 计算止盈价格(百分比{take_profit}%): {current_price} * (1 - {take_profit}/100) = {tp_price}")
                else:
                    self.log("❌ 无法计算止盈价格: 当前价格无效")
            else:
                # 已经是实际价格: 直接使用
                tp_price = take_profit
                self.log(f"📏 使用实际止盈价格: {tp_price}")

        try:
            # 不再激活MT5窗口，直接按F9（假设MT5窗口已在前台）
            self.log("⌨️ 步骤1: 按F9打开订单窗口...")
            pyautogui.press('f9')
            time.sleep(0.8)  # 等待订单窗口完全打开
            self.log("✅ 订单窗口已打开")
            
            # Step 1: Input stop loss price
            if sl_price is not None:
                if "sl_input" in self.mt5_positions:
                    self.log(f"输入止损价格: {sl_price}")
                    self.click_position("sl_input")
                    time.sleep(0.2)
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.1)
                    pyautogui.press('backspace')
                    time.sleep(0.1)
                    pyautogui.typewrite(str(sl_price))
                    time.sleep(0.3)
                else:
                    self.log("警告: 止损输入框位置未校准，跳过止损设置")

            # Step 2: Input take profit price
            if tp_price is not None:
                if "tp_input" in self.mt5_positions:
                    self.log(f"输入止盈价格: {tp_price}")
                    self.click_position("tp_input")
                    time.sleep(0.2)
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.1)
                    pyautogui.press('backspace')
                    time.sleep(0.1)
                    pyautogui.typewrite(str(tp_price))
                    time.sleep(0.3)
                else:
                    self.log("警告: 止盈输入框位置未校准，跳过止盈设置")

            # Step 3: Click the sell button
            self.click_position("sell_btn")
            time.sleep(0.3)
            self.log("卖出订单已提交")
            return True

        except Exception as e:
            self.log(f"卖出失败: {str(e)}")
            return False

    def parse_command(self, command):
        """Parse trading command - with percentage support"""
        command = command.strip()

        # Try to extract SL and TP values
        import re

        # Check for percentage format: 止损20% or 止损 20%
        # Use more flexible regex to handle various formats
        sl_match = re.search(r'止损\s*(\d+(?:\.\d+)?)\s*%?', command)
        tp_match = re.search(r'止盈\s*(\d+(?:\.\d+)?)\s*%?', command)

        # Determine if using percentage (if % is present)
        if '%' in command:
            stop_loss_is_percent = True
            take_profit_is_percent = True
        else:
            stop_loss_is_percent = False
            take_profit_is_percent = False
        
        # Extract values
        if sl_match:
            try:
                stop_loss = float(sl_match.group(1))
            except:
                stop_loss = None
        else:
            stop_loss = None
            
        if tp_match:
            try:
                take_profit = float(tp_match.group(1))
            except:
                take_profit = None
        else:
            take_profit = None

        # Simplified commands - just click at coordinates
        if command in ["买入", "买", "做多", "buy"] or command.startswith("做多"):
            return "buy", None, None, stop_loss, take_profit, stop_loss_is_percent, take_profit_is_percent

        elif command in ["卖出", "卖", "做空", "sell"] or command.startswith("做空"):
            return "sell", None, None, stop_loss, take_profit, stop_loss_is_percent, take_profit_is_percent

        elif "待机" in command or "不操作" in command:
            return "none", None, None, None, None, False, False

        return None, None, None, None, None, False, False
        # Extract symbol and lot
        if "做多" in command:
            parts = command.replace("做多", "").strip().split()
            if len(parts) >= 2:
                symbol = parts[0]
                lot = float(parts[1].replace("手", ""))
                return "buy", symbol, lot, stop_loss, take_profit, stop_loss_is_percent, take_profit_is_percent

        if "做空" in command:
            parts = command.replace("做空", "").strip().split()
            if len(parts) >= 2:
                symbol = parts[0]
                lot = float(parts[1].replace("手", ""))
                return "sell", symbol, lot, stop_loss, take_profit, stop_loss_is_percent, take_profit_is_percent

        return None, None, None, None, None, False, False

    def execute_command(self, command, current_price=None, digits=5):
        """Execute a trading command"""
        if not command or command == self.last_command:
            return False

        self.last_command = command
        self.log(f"🎯 开始执行交易指令: {command}")
        self.log(f"💰 价格信息 - 当前价格: {current_price}, 小数位数: {digits}")

        cmd_type, symbol, lot, stop_loss, take_profit, stop_loss_is_percent, take_profit_is_percent = self.parse_command(command)
        
        # 记录解析结果
        if cmd_type == "buy":
            self.log(f"🟢 指令类型: 买入, 止损: {stop_loss}, 止盈: {take_profit}")
        elif cmd_type == "sell":
            self.log(f"🔴 指令类型: 卖出, 止损: {stop_loss}, 止盈: {take_profit}")
        elif cmd_type == "none":
            self.log("⚪ 指令类型: 待机")
        else:
            self.log(f"❓ 未知指令类型: {cmd_type}")

        if cmd_type == "buy":
            self.log("🟢 开始执行买入操作...")
            # 执行买入操作（不再激活MT5窗口，直接按F9）
            self.log("🔄 调用买入执行函数...")
            success = self.execute_buy(symbol, lot, stop_loss, take_profit, current_price, digits, stop_loss_is_percent, take_profit_is_percent)
            
            if success:
                self.log("✅ 买入订单已提交，等待MT5 API验证...")
                # 验证交易是否成功
                self.log("🔍 验证MT5持仓状态...")
                if self.check_mt5_positions():
                    self.log("✅ 交易验证成功：MT5账户确认新持仓")
                    return True
                else:
                    self.log("❌ 交易验证失败：MT5账户未检测到新持仓，放弃此次交易")
                    return False
            else:
                self.log("❌ 买入操作失败，放弃此次交易")
                return False
                
        elif cmd_type == "sell":
            self.log("🔴 开始执行卖出操作...")
            # 执行卖出操作（不再激活MT5窗口，直接按F9）
            self.log("🔄 调用卖出执行函数...")
            success = self.execute_sell(symbol, lot, stop_loss, take_profit, current_price, digits, stop_loss_is_percent, take_profit_is_percent)
            
            if success:
                self.log("✅ 卖出订单已提交，等待MT5 API验证...")
                # 验证交易是否成功
                self.log("🔍 验证MT5持仓状态...")
                if self.check_mt5_positions():
                    self.log("✅ 交易验证成功：MT5账户确认新持仓")
                    return True
                else:
                    self.log("❌ 交易验证失败：MT5账户未检测到新持仓，放弃此次交易")
                    return False
            else:
                self.log("❌ 卖出操作失败，放弃此次交易")
                return False
                
        elif cmd_type == "none":
            self.log("待机模式：不执行任何操作")
            return True

        return False

    def monitor_commands(self):
        """Monitor commands file"""
        self.log("开始监控指令文件...")
        
        # Track last processed command to avoid re-executing
        self.last_processed_command = ""

        while self.running:
            try:
                if os.path.exists(COMMANDS_FILE):
                    with open(COMMANDS_FILE, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    if lines:
                        first_line = lines[0].strip()
                        
                        # Only process commands that start with "NEW:"
                        if first_line.startswith("NEW:"):
                            # Extract the actual command (remove "NEW:" prefix)
                            command = first_line[4:].strip()  # Remove "NEW:" prefix
                            
                            # Skip if this is the same command as last processed
                            if command == self.last_processed_command:
                                time.sleep(1)
                                continue
                            
                            price_info = lines[1].strip() if len(lines) > 1 else ""

                            # Parse price info: @price=1.0850@digits=5
                            current_price = None
                            digits = 5
                            import re
                            price_match = re.search(r'@price=([\d.]+)', price_info)
                            digits_match = re.search(r'@digits=(\d+)', price_info)

                            if price_match:
                                current_price = float(price_match.group(1))
                            if digits_match:
                                digits = int(digits_match.group(1))

                            if command:
                                self.last_processed_command = command
                                self.log(f"📥 检测到新交易指令: {command}")
                                self.log(f"📊 价格信息: {price_info}")
                                if current_price:
                                    self.log(f"💰 当前价格: {current_price}, 小数位数: {digits}")
                                
                                # 执行命令
                                result = self.execute_command(command, current_price, digits)
                                
                                if result:
                                    self.log("✅ 交易执行成功")
                                else:
                                    self.log("❌ 交易执行失败")
                                
                                # Mark command as DONE
                                try:
                                    with open(COMMANDS_FILE, 'w', encoding='utf-8') as wf:
                                        wf.write("DONE:" + command + "\n")
                                        wf.write(price_info + "\n")
                                    self.log("📝 指令已标记为DONE")
                                except Exception as e:
                                    self.log(f"❌ 标记命令为DONE失败: {str(e)}")

                time.sleep(1)  # Check every second

            except Exception as e:
                self.log(f"监控循环错误: {str(e)}")
                time.sleep(5)

    def start(self):
        """Start the executor"""
        self.log("Executor Agent 启动")
        
        # Clear commands.txt on startup to avoid executing old commands from previous session
        try:
            with open(COMMANDS_FILE, 'w', encoding='utf-8') as f:
                f.write('')
            self.log("已清空命令文件")
        except Exception as e:
            self.log(f"清空命令文件失败: {str(e)}")

        # Check if positions are calibrated
        if not self.mt5_positions:
            self.log("警告: MT5位置未校准，请运行校准")
            print("\n输入 '校准' 开始位置校准")
            print("输入 '退出' 退出程序")
        else:
            self.log(f"已加载 {len(self.mt5_positions)} 个位置配置")

        # Start monitoring in background
        monitor_thread = threading.Thread(target=self.monitor_commands)
        monitor_thread.daemon = True
        monitor_thread.start()

        # Interactive loop
        while True:
            try:
                user_input = input("\nExecutor> ").strip()

                if user_input == "退出":
                    self.running = False
                    print("再见!")
                    break

                elif user_input == "校准":
                    self.calibrate_positions()

                elif user_input == "状态":
                    print(f"运行状态: {'运行中' if self.running else '已停止'}")
                    print(f"已校准位置: {list(self.mt5_positions.keys())}")
                    print(f"OpenCV可用: {self.use_opencv}")

                elif user_input.startswith("capture "):
                    # Capture button template: capture <button_name>
                    button_name = user_input.replace("capture ", "").strip()
                    if button_name:
                        print(f"请移动鼠标到 '{button_name}' 按钮位置，3秒后保存...")
                        time.sleep(3)
                        x, y = pyautogui.position()
                        self.save_button_template(button_name, x, y)
                    else:
                        print("用法: capture <按钮名称>")

                elif user_input.startswith("执行 "):
                    command = user_input.replace("执行 ", "")
                    self.execute_command(command)

                else:
                    print("可用命令:")
                    print("  校准 - 校准MT5窗口位置")
                    print("  状态 - 查看状态")
                    print("  capture <名称> - 保存按钮模板(将鼠标移到按钮位置)")
                    print("  执行 [指令] - 执行交易指令")
                    print("  退出 - 退出程序")

            except KeyboardInterrupt:
                self.running = False
                print("\n程序已停止")
                break
            except Exception as e:
                print(f"错误: {str(e)}")

def main():
    """Main entry point"""
    import sys
    # Set UTF-8 encoding for output
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

    print("=" * 50)
    print("Executor Agent - MT5 trading executor")
    print("=" * 50)

    # Check PyAutoGUI
    try:
        print("[OK] PyAutoGUI installed")
    except ImportError:
        print("[ERROR] PyAutoGUI not installed, installing...")
        os.system("pip install pyautogui")

    # Check win32gui for Windows
    try:
        import win32gui
        print("[OK] win32gui installed")
    except ImportError:
        print("[ERROR] win32gui not installed, installing...")
        os.system("pip install pywin32")

    agent = ExecutorAgent()
    agent.start()

if __name__ == "__main__":
    main()
