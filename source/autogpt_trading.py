"""
AutoGPT Trading System - Main Application
Connects to Ollama LLM and handles trading strategy discussion and monitoring.
"""

import json
import os
import sys
import time
import threading
import requests
from datetime import datetime
from pathlib import Path

# Try to import MT5 library
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("[WARNING] MetaTrader5 not installed. Install with: pip install MetaTrader5")

# Configuration
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:3b-instruct-q4_K_M"
COMMANDS_FILE = "E:\\TradingSystem\\commands.txt"
MARKET_DATA_CACHE = "E:\\TradingSystem\\market_cache.json"
LOG_FILE = "E:\\TradingSystem\\autogpt.log"
CONFIG_FILE = "E:\\TradingSystem\\config.json"

# Market data source priorities
MARKET_SOURCES = [
    {"name": "Investing.com", "url": "https://www.investing.com"},
    {"name": "TradingView", "url": "https://www.tradingview.com"},
    {"name": "Bloomberg", "url": "https://www.bloomberg.com"},
    {"name": "Reuters", "url": "https://www.reuters.com"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com"},
]

class AutoGPTTrading:
    def __init__(self):
        self.mode = "discussion"  # "discussion" or "monitor"
        self.strategy = ""
        self.trading_pair = ""
        self.lot_size = 0.01
        self.conversation_history = []
        self.monitoring_interval = 1  # seconds (supports float like 0.5)
        self.running = True
        self.mt5_connected = False
        self.monitor_thread = None
        
        # Long/Short strategy configuration
        self.long_sl_percent = 0
        self.long_tp_percent = 0
        self.long_strategy = ""
        self.short_sl_percent = 0
        self.short_tp_percent = 0
        self.short_strategy = ""
        self.rules = ""  # Must-follow rules
        self.timeframe = 1  # Timeframe for K-lines and indicators (in minutes)
        self.max_positions = 1  # Maximum concurrent positions allowed
        
        # Indicator configuration
        self.indicators_config = {
            'enabled': True,
            'level2_enabled': True,
            'timeframe': 1,
            'candle_count': 200,
            'selected_indicators': {
                'ma5': True, 'ma10': True, 'ma20': True, 
                'ma50': True, 'ma200': False,
                'ema12': False, 'ema26': False,
                'rsi': True, 'macd': True, 
                'bollinger': True, 'atr': False
            },
            'signal_rules': {
                'require_ma_cross': True,
                'require_rsi_confirm': False,
                'require_macd_confirm': False,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
        }
        
        self.load_config()
        self.connect_mt5()
        
        # 启动后台标志检查线程
        self.flag_check_thread = threading.Thread(target=self.check_flags_loop, daemon=True)
        self.flag_check_thread.start()
    
    def connect_mt5(self):
        """Connect to MT5 terminal"""
        if not MT5_AVAILABLE:
            self.log("MT5库不可用，请安装: pip install MetaTrader5")
            return False
        
        try:
            # Initialize MT5
            if not mt5.initialize():
                self.log(f"MT5初始化失败: {mt5.last_error()}")
                self.mt5_connected = False
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.log("无法获取MT5账户信息")
                self.mt5_connected = False
                return False
            
            self.log(f"MT5已连接 - 账户: {account_info.login}, 余额: {account_info.balance}")
            self.mt5_connected = True
            return True
            
        except Exception as e:
            self.log(f"MT5连接错误: {str(e)}")
            self.mt5_connected = False
            return False
    
    def check_flags_loop(self):
        """后台线程：检查监控标志文件"""
        while self.running:
            try:
                # 检查启动监控标志
                start_flag = "E:\\TradingSystem\\start_monitor.flag"
                if os.path.exists(start_flag):
                    self.log("检测到启动监控标志，切换到监控模式")
                    self.set_mode("monitor")
                    os.remove(start_flag)
                
                # 检查停止监控标志
                stop_flag = "E:\\TradingSystem\\stop_monitor.flag"
                if os.path.exists(stop_flag):
                    self.log("检测到停止监控标志，切换到讨论模式")
                    self.set_mode("discussion")
                    os.remove(stop_flag)
                
                # 检查重新加载配置标志
                reload_flag = "E:\\TradingSystem\\reload_config.flag"
                if os.path.exists(reload_flag):
                    self.log("检测到重新加载配置标志")
                    self.load_config()
                    self.log(f"配置已重新加载 - 交易品种: {self.trading_pair}, 手数: {self.lot_size}")
                    os.remove(reload_flag)
            except Exception as e:
                self.log(f"标志检查错误: {e}")
            
            # 每2秒检查一次
            time.sleep(2)
    
    def get_mt5_symbol_info(self, symbol):
        """Get symbol info from MT5"""
        if not self.mt5_connected:
            return None
        
        try:
            # Try to get symbol info - first try full symbol name, then try without suffix
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                # Try without USD suffix for forex
                symbol_base = symbol.replace('USD', '')
                symbol_info = mt5.symbol_info(symbol_base)
            
            if symbol_info is None:
                self.log(f"MT5未找到品种: {symbol}")
                return None
            
            # Select symbol if not visible
            if not symbol_info.visible:
                mt5.symbol_select(symbol, True)
                symbol_info = mt5.symbol_info(symbol)
            
            return symbol_info
            
        except Exception as e:
            self.log(f"获取MT5品种信息错误: {str(e)}")
            return None
    
    def get_mt5_market_data(self, symbol):
        """Get real-time market data from MT5"""
        if not self.mt5_connected:
            self.log("MT5未连接，尝试重新连接...")
            if not self.connect_mt5():
                return None
        
        try:
            # Get symbol info
            symbol_info = self.get_mt5_symbol_info(symbol)
            if symbol_info is None:
                return None
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.log(f"无法获取 {symbol} 的实时报价")
                return None
            
            # Get symbol info for point size (to calculate proper prices)
            point = symbol_info.point
            
            # Get ask and bid prices
            ask = tick.ask
            bid = tick.bid
            
            # For forex, we typically need to calculate SL/TP in points
            # Get digit count
            digits = symbol_info.digits
            
            return {
                "symbol": symbol,
                "price": ask,  # Use ask as current price for buying
                "bid": bid,
                "ask": ask,
                "timestamp": datetime.now().isoformat(),
                "source": "MT5",
                "digits": digits,
                "point": point,
                "spread": round((ask - bid) / point) if point > 0 else 0
            }
            
        except Exception as e:
            self.log(f"获取MT5行情数据错误: {str(e)}")
            return None
    
    def get_mt5_level2_data(self, symbol):
        """Get Level 2 market data (market depth/order book) from MT5"""
        if not self.mt5_connected:
            return None
        
        try:
            # Subscribe to market book (depth)
            # First check if we can get the data
            if not hasattr(mt5, 'market_book_get'):
                self.log("当前MT5版本不支持market_book_get")
                return None
            
            # Try to get market depth
            book = mt5.market_book_get(symbol)
            
            if book is None or len(book) == 0:
                # Level 2 not available for this symbol
                return None
            
            # Parse the market book data
            # MT5 returns a list of MarketBookEntry objects
            bid_levels = []
            ask_levels = []
            
            for entry in book:
                # entry.type: 0 = bid, 1 = ask
                # entry.price: price level
                # entry.volume: volume at this level
                if entry.type == 0:  # Bid
                    bid_levels.append({
                        "price": entry.price,
                        "volume": entry.volume
                    })
                elif entry.type == 1:  # Ask
                    ask_levels.append({
                        "price": entry.price,
                        "volume": entry.volume
                    })
            
            # Calculate total volumes
            total_bid_vol = sum(level['volume'] for level in bid_levels)
            total_ask_vol = sum(level['volume'] for level in ask_levels)
            
            # Calculate volume imbalance
            if total_bid_vol + total_ask_vol > 0:
                bid_ratio = total_bid_vol / (total_bid_vol + total_ask_vol)
            else:
                bid_ratio = 0.5
            
            # Get best bid/ask
            best_bid = bid_levels[0]['price'] if bid_levels else None
            best_ask = ask_levels[0]['price'] if ask_levels else None
            
            # Determine order book sentiment
            sentiment = "均衡"
            if bid_ratio > 0.6:
                sentiment = "买方占优(看涨)"
            elif bid_ratio < 0.4:
                sentiment = "卖方占优(看跌)"
            
            self.log(f"Level2行情: 买量={total_bid_vol}, 卖量={total_ask_vol}, 买方占比={bid_ratio:.1%}")
            
            return {
                "available": True,
                "bid_levels": bid_levels[:10],  # Top 10 levels
                "ask_levels": ask_levels[:10],
                "total_bid_volume": total_bid_vol,
                "total_ask_volume": total_ask_vol,
                "bid_ratio": bid_ratio,
                "best_bid": best_bid,
                "best_ask": best_ask,
                "spread": (best_ask - best_bid) if (best_ask and best_bid) else None,
                "sentiment": sentiment,
                "level_count": len(book)
            }
            
        except Exception as e:
            # Level 2 not available for this symbol
            self.log(f"获取Level2行情失败: {str(e)}")
            return None
    
    def get_mt5_positions(self):
        """Get current open positions from MT5"""
        if not self.mt5_connected:
            return []
        
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            return list(positions)
        except Exception as e:
            self.log(f"获取MT5持仓错误: {str(e)}")
            return []
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.trading_pair = config.get('trading_pair', '')
                    self.lot_size = config.get('lot_size', 0.01)
                    self.strategy = config.get('strategy', '')
                    self.monitoring_interval = config.get('monitoring_interval', 1)
                    self.mode = config.get('mode', 'discussion')
                    
                    # Load long/short strategy configuration
                    self.long_sl_percent = config.get('long_sl_percent', 0)
                    self.long_tp_percent = config.get('long_tp_percent', 0)
                    self.long_strategy = config.get('long_strategy', '')
                    self.short_sl_percent = config.get('short_sl_percent', 0)
                    self.short_tp_percent = config.get('short_tp_percent', 0)
                    self.short_strategy = config.get('short_strategy', '')
                    self.rules = config.get('rules', '')
                    
                    # If strategy is empty but long/short strategies exist, create combined strategy
                    if not self.strategy and (self.long_strategy or self.short_strategy):
                        self.strategy = "长策略: " + (self.long_strategy if self.long_strategy else "未设置")
                        self.strategy += " | 短策略: " + (self.short_strategy if self.short_strategy else "未设置")
                    
                    # Load indicator configuration - handle both formats
                    raw_indicators = config.get('indicators', {})
                    
                    # Parse timeframe and max_positions from rules
                    self.rules = config.get('rules', '')
                    self._parse_rules(self.rules)
                    
                    # If raw_indicators has direct boolean values (like {"ma5": false, "rsi": true})
                    # If raw_indicators has direct boolean values (like {"ma5": false, "rsi": true})
                    # convert to the expected format
                    if raw_indicators and 'enabled' not in raw_indicators:
                        # Convert from {"ma5": false, "rsi": true} to selected_indicators format
                        self.indicators_config = {
                            'enabled': True,
                            'level2_enabled': True,
                            'timeframe': 1,
                            'candle_count': 200,
                            'selected_indicators': raw_indicators,  # Direct use of the indicator flags
                            'signal_rules': {
                                'require_ma_cross': True,
                                'require_rsi_confirm': False,
                                'require_macd_confirm': False,
                                'rsi_oversold': 30,
                                'rsi_overbought': 70
                            }
                        }
                    else:
                        self.indicators_config = raw_indicators
            except:
                pass
    
    def save_config(self):
        """Save configuration to file"""
        # Load existing config to preserve indicator settings
        existing_indicators = getattr(self, 'indicators_config', None)
        
        config = {
            'trading_pair': self.trading_pair,
            'lot_size': self.lot_size,
            'strategy': self.strategy,
            'monitoring_interval': self.monitoring_interval,
            'mode': self.mode,
            'long_sl_percent': self.long_sl_percent,
            'long_tp_percent': self.long_tp_percent,
            'long_strategy': self.long_strategy,
            'short_sl_percent': self.short_sl_percent,
            'short_tp_percent': self.short_tp_percent,
            'short_strategy': self.short_strategy,
            'rules': self.rules,
            'indicators': existing_indicators or {
                'enabled': True,
                'level2_enabled': True,
                'timeframe': 1,
                'candle_count': 200,
                'selected_indicators': {
                    'ma5': True, 'ma10': True, 'ma20': True, 
                    'ma50': True, 'ma200': False,
                    'ema12': False, 'ema26': False,
                    'rsi': True, 'macd': True, 
                    'bollinger': True, 'atr': False
                },
                'signal_rules': {
                    'require_ma_cross': True,
                    'require_rsi_confirm': False,
                    'require_macd_confirm': False,
                    'rsi_oversold': 30,
                    'rsi_overbought': 70
                }
            }
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _parse_rules(self, rules_text):
        """Parse all rules from rules text - supports both Chinese and English"""
        import re
        
        # ========== Timeframe Parsing ==========
        # Chinese: 1分钟, 5分钟, 15分钟, 1分钟级别, K线都是5分钟
        # English: 1min, 5min, 15m, 1 minute, 5 minutes, timeframe 5
        timeframe_patterns = [
            # Chinese patterns
            r'(\d+)\s*分钟',
            r'(\d+)\s*分钟级别',
            r'K线都是(\d+)分钟',
            r'更高周期[：:\s]*(\d+)\s*分钟',
            # English patterns
            r'(\d+)\s*min(?:ute)?s?',
            r'timeframe[：:\s]*(\d+)',
            r'period[：:\s]*(\d+)',
            r'higher timeframe[：:\s]*(\d+)'
        ]
        
        for pattern in timeframe_patterns:
            match = re.search(pattern, rules_text, re.IGNORECASE)
            if match:
                self.timeframe = int(match.group(1))
                self.log(f"✓ 从规则中解析时间级别: {self.timeframe} 分钟")
                break
        else:
            self.timeframe = 1
        
        # ========== Max Positions Parsing ==========
        # Chinese: 最大持仓3单, 最多持有3单, 持仓同时最多持有2单, 最多3单
        # English: max position 3, max positions 3, max orders 3, max 3 orders
        max_pos_patterns = [
            # Chinese patterns
            r'最大持仓(\d+)单',
            r'最多持有(\d+)单',
            r'持仓同时最多持有(\d+)单',
            r'最多(\d+)单',
            r'持仓(\d+)单',
            # English patterns
            r'max(?:imum)?\s*position[s]?\s*(\d+)',
            r'max(?:imum)?\s*order[s]?\s*(\d+)',
            r'max\s+(\d+)\s*order[s]?',
            r'position\s+limit\s*[：:\s]*(\d+)',
            r'order\s+limit\s*[：:\s]*(\d+)'
        ]
        
        for pattern in max_pos_patterns:
            match = re.search(pattern, rules_text, re.IGNORECASE)
            if match:
                self.max_positions = int(match.group(1))
                self.log(f"✓ 从规则中解析最大持仓数: {self.max_positions} 单")
                break
        else:
            self.max_positions = 1
        
        # ========== Max Drawdown Rate ==========
        # Chinese: 最大回撤率: 5%, 最大回撤: 5%
        # English: max drawdown: 5%, max drawdown 5%, drawdown limit 5%
        drawdown_patterns = [
            r'最大回撤率[：:\s]*(\d+(?:\.\d+)?)\s*%',
            r'最大回撤[：:\s]*(\d+(?:\.\d+)?)\s*%',
            r'max\s*drawdown[：:\s]*(\d+(?:\.\d+)?)\s*%',
            r'drawdown\s*limit[：:\s]*(\d+(?:\.\d+)?)\s*%'
        ]
        
        for pattern in drawdown_patterns:
            match = re.search(pattern, rules_text, re.IGNORECASE)
            if match:
                self.max_drawdown_percent = float(match.group(1))
                self.log(f"✓ 从规则中解析最大回撤率: {self.max_drawdown_percent}%")
                break
        else:
            self.max_drawdown_percent = None
        
        # ========== Daily Max Loss ==========
        # Chinese: 每日最大亏损: 100, 每日亏损: 100
        # English: daily max loss: 100, daily loss limit 100
        daily_loss_patterns = [
            r'每日最大亏损[：:\s]*(\d+(?:\.\d+)?)',
            r'每日亏损[：:\s]*(\d+(?:\.\d+)?)',
            r'daily\s*max\s*loss[：:\s]*(\d+(?:\.\d+)?)',
            r'daily\s*loss[：:\s]*(\d+(?:\.\d+)?)',
            r'loss\s*limit[：:\s]*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in daily_loss_patterns:
            match = re.search(pattern, rules_text, re.IGNORECASE)
            if match:
                self.daily_max_loss = float(match.group(1))
                self.log(f"✓ 从规则中解析每日最大亏损: {self.daily_max_loss}")
                break
        else:
            self.daily_max_loss = None
        
        # ========== Trading Session ==========
        # Chinese: 交易时段: 09:00-17:00
        # English: trading session: 09:00-17:00, session: 09:00-17:00
        session_patterns = [
            r'交易时段[：:\s]*(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})',
            r'trading\s*session[：:\s]*(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})',
            r'session[：:\s]*(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})',
            r'time\s*range[：:\s]*(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})'
        ]
        
        for pattern in session_patterns:
            match = re.search(pattern, rules_text, re.IGNORECASE)
            if match:
                self.trading_session_start = match.group(1)
                self.trading_session_end = match.group(2)
                self.log(f"✓ 从规则中解析交易时段: {self.trading_session_start} - {self.trading_session_end}")
                break
        else:
            self.trading_session_start = None
            self.trading_session_end = None
        
        # ========== Spread Limit ==========
        # Chinese: 点差限制: 30点
        # English: spread limit: 30, max spread 30
        spread_patterns = [
            r'点差限制[：:\s]*(\d+)\s*点?',
            r'spread\s*limit[：:\s]*(\d+)',
            r'max\s*spread[：:\s]*(\d+)',
            r'spread[：:\s]*(\d+)'
        ]
        
        for pattern in spread_patterns:
            match = re.search(pattern, rules_text, re.IGNORECASE)
            if match:
                self.spread_limit = int(match.group(1))
                self.log(f"✓ 从规则中解析点差限制: {self.spread_limit} 点")
                break
        else:
            self.spread_limit = None
        
        # ========== Trailing Stop ==========
        # Chinese: 移动止损: 激活0.5%, 距离0.3%
        # English: trailing stop: activate 0.5%, distance 0.3%
        trailing_patterns = [
            r'移动止损[：:\s]*激活(\d+(?:\.\d+)?)\s*%[，,]\s*距离(\d+(?:\.\d+)?)\s*%',
            r'trailing\s*stop[：:\s]*activate[sd]?(\d+(?:\.\d+)?)\s*%[，,]\s*distance(\d+(?:\.\d+)?)\s*%',
            r'trailing\s*stop[：:\s]*(\d+(?:\.\d+)?)\s*%.*?(\d+(?:\.\d+)?)\s*%'
        ]
        
        for pattern in trailing_patterns:
            match = re.search(pattern, rules_text, re.IGNORECASE)
            if match:
                self.trailing_stop_activation = float(match.group(1))
                self.trailing_stop_distance = float(match.group(2))
                self.log(f"✓ 从规则中解析移动止损: 激活{self.trailing_stop_activation}%, 距离{self.trailing_stop_distance}%")
                break
        else:
            self.trailing_stop_activation = None
            self.trailing_stop_distance = None
        
        # ========== Partial Close ==========
        # Chinese: 部分平仓: 0.3%, 50%
        # English: partial close: 0.3%, 50%
        partial_patterns = [
            r'部分平仓[：:\s]*(\d+(?:\.\d+)?)\s*%[，,]\s*(\d+)\s*%',
            r'partial\s*close[：:\s]*(\d+(?:\.\d+)?)\s*%[，,]\s*(\d+)\s*%',
            r'take\s*partial\s*profit[：:\s]*(\d+(?:\.\d+)?)\s*%[，,]\s*(\d+)\s*%'
        ]
        
        for pattern in partial_patterns:
            match = re.search(pattern, rules_text, re.IGNORECASE)
            if match:
                self.partial_close_activation = float(match.group(1))
                self.partial_close_percent = int(match.group(2))
                self.log(f"✓ 从规则中解析部分平仓: 激活{self.partial_close_activation}%, 平仓{self.partial_close_percent}%")
                break
        else:
            self.partial_close_activation = None
            self.partial_close_percent = None
        
        # ========== Close All Hotkey ==========
        # Chinese: 平仓热键: ctrl+shift+c
        # English: close hotkey: ctrl+shift+c, close all key: ctrl+shift+c
        hotkey_patterns = [
            r'平仓热键[：:\s]*([a-zA-Z+\^]+(?:\+[a-zA-Z]+)+)',
            r'close\s*(?:all)?\s*hotkey[：:\s]*([a-zA-Z+\^]+(?:\+[a-zA-Z]+)+)',
            r'hotkey[：:\s]*([a-zA-Z+\^]+(?:\+[a-zA-Z]+)+)'
        ]
        
        for pattern in hotkey_patterns:
            match = re.search(pattern, rules_text, re.IGNORECASE)
            if match:
                self.close_hotkey = match.group(1).lower()
                self.log(f"✓ 从规则中解析平仓热键: {self.close_hotkey}")
                break
        else:
            self.close_hotkey = None
        
        # Also update indicators_config with the parsed timeframe
        if hasattr(self, 'indicators_config') and self.indicators_config:
            self.indicators_config['timeframe'] = self.timeframe
            
    def auto_configure_from_context(self):
        """Auto-detect and configure trading parameters from conversation context"""
        self.log("自动配置分析...")
        
        # Build context from conversation history
        context = "\n".join([f"用户: {msg['content']}" for msg in self.conversation_history[-10:]])
        
        if not context:
            return "没有对话历史，请先告诉我你的交易需求，例如：我想交易黄金，手数0.01，用MA策略"
        
        # Ask LLM to extract configuration
        config_prompt = f"""请从以下对话历史中提取交易配置参数，返回JSON格式：
{{
    "trading_pair": "交易品种，如XAUUSD、EURUSD等",
    "lot_size": 交易手数，如0.01、0.1等数字,
    "strategy": 交易策略描述,
    "monitoring_interval": 监控间隔(秒)，如60、30等
}}

对话历史：
{context}

请只返回JSON，不要其他内容。如果某个参数没有明确提及，请使用null。"""

        try:
            response = self.call_ollama(config_prompt, "你是一个交易配置解析器，请提取对话中的交易参数。")
            
            if response:
                # Try to parse JSON from response
                import re
                json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
                if json_match:
                    config = json.loads(json_match.group())
                    
                    # Apply extracted configuration
                    changes = []
                    if config.get('trading_pair'):
                        self.trading_pair = config['trading_pair'].upper()
                        changes.append(f"交易品种: {self.trading_pair}")
                    
                    if config.get('lot_size'):
                        self.lot_size = float(config['lot_size'])
                        changes.append(f"手数: {self.lot_size}")
                    
                    if config.get('strategy'):
                        self.strategy = config['strategy']
                        changes.append(f"策略: {self.strategy}")
                    
                    if config.get('monitoring_interval'):
                        self.monitoring_interval = int(config['monitoring_interval'])
                        changes.append(f"监控间隔: {self.monitoring_interval}秒")
                    
                    self.save_config()
                    
                    if changes:
                        result = "自动配置完成！\n" + "\n".join(changes)
                        result += "\n\n输入 '查看配置' 确认配置"
                        result += "\n输入 '策略固定，开始盯盘' 开始自动交易"
                        return result
                    else:
                        return "未能从对话中提取到有效的交易参数，请手动输入或详细描述你的交易需求。"
                else:
                    return "无法解析配置，请手动设置或详细描述交易需求。"
            else:
                return "自动配置失败，请重试或手动设置。"
        except Exception as e:
            self.log(f"自动配置错误: {str(e)}")
            return f"自动配置出错: {str(e)}，请手动设置配置。"
            
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
    
    def _check_log_rotation(self):
        """Check if log rotation is needed and perform rotation if necessary"""
        import shutil
        
        LOG_DIR = "E:\\TradingSystem\\logs"
        MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
        
        try:
            # Create logs directory if it doesn't exist
            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR)
            
            # Check if log file exists
            if not os.path.exists(LOG_FILE):
                return
            
            # Get log file size and modification time
            log_size = os.path.getsize(LOG_FILE)
            log_mtime = datetime.fromtimestamp(os.path.getmtime(LOG_FILE))
            today = datetime.now().date()
            
            # Check if rotation is needed (size > 10MB or new day)
            need_rotation = False
            
            if log_size > MAX_LOG_SIZE:
                self.log(f"日志文件超过 {MAX_LOG_SIZE // (1024*1024)}MB，准备轮转...")
                need_rotation = True
            elif log_mtime.date() < today:
                self.log(f"新的一天到来，日志文件准备轮转...")
                need_rotation = True
            
            if need_rotation:
                # Generate timestamp for old log file
                timestamp_str = log_mtime.strftime("%Y%m%d_%H%M%S")
                log_filename = os.path.basename(LOG_FILE)
                old_log_name = f"{log_filename.replace('.log', '')}_{timestamp_str}.log"
                old_log_path = os.path.join(LOG_DIR, old_log_name)
                
                # Move old log to logs directory
                try:
                    shutil.move(LOG_FILE, old_log_path)
                    self.log(f"旧日志已保存到: {old_log_path}")
                except Exception as e:
                    self.log(f"移动日志文件失败: {str(e)}")
        except Exception as e:
            # Silently ignore errors to avoid disrupting trading
            pass
            
    def call_ollama(self, prompt, system_prompt=None):
        """Call Ollama API"""
        url = f"{OLLAMA_HOST}/api/generate"
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                self.log(f"Error calling Ollama: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.log(f"Exception calling Ollama: {str(e)}")
            return None
            
    def search_market_data(self, symbol):
        """Search for market data - now uses MT5 as primary source"""
        self.log(f"获取 {symbol} 行情数据...")
        
        # Try MT5 first (primary source)
        if self.mt5_connected:
            try:
                data = self.get_mt5_market_data(symbol)
                if data and data.get('price'):
                    self.log(f"成功从 MT5 获取数据: 买入价={data['ask']}, 卖出价={data['bid']}")
                    return data
            except Exception as e:
                self.log(f"MT5获取失败: {str(e)}")
        
        # If MT5 fails, try web sources as fallback
        self.log("MT5不可用，尝试网页数据源...")
        
        # Try to get real market data from sources in priority order
        for source in MARKET_SOURCES:
            try:
                self.log(f"Attempting to get data from {source['name']}...")
                data = self._fetch_from_source(source['name'], source['url'], symbol)
                if data and data.get('price'):
                    data['source'] = source['name']
                    self.log(f"成功从 {source['name']} 获取数据: {data['price']}")
                    return data
            except Exception as e:
                self.log(f"从 {source['name']} 获取数据失败: {str(e)}")
                continue
        
        # All sources failed, use mock data with warning
        self.log("警告: 所有数据源均不可用，使用模拟数据")
        return self.get_mock_market_data(symbol)
    
    def _fetch_from_source(self, source_name, source_url, symbol):
        """Fetch market data from a specific source"""
        import re
        
        # Yahoo Finance - most reliable for forex
        if source_name == "Yahoo Finance":
            try:
                # Yahoo Finance API for forex pairs
                yahoo_symbol = symbol.replace('USD', '=X')
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        meta = result.get('meta', {})
                        price = meta.get('regularMarketPrice', 0)
                        if price:
                            return {
                                "symbol": symbol,
                                "price": price,
                                "timestamp": datetime.now().isoformat(),
                                "bid": price - 0.0002,
                                "ask": price + 0.0002,
                                "source": "Yahoo Finance"
                            }
            except Exception as e:
                self.log(f"Yahoo Finance fetch error: {str(e)}")
        
        # Try Investing.com via web scraping (if accessible)
        if source_name == "Investing.com":
            try:
                # Try to search for the symbol price
                search_url = f"https://www.investing.com/search/?q={symbol}"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(search_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    # Look for price in the response
                    price_match = re.search(r'"price":([0-9.]+)', response.text)
                    if price_match:
                        price = float(price_match.group(1))
                        return {
                            "symbol": symbol,
                            "price": price,
                            "timestamp": datetime.now().isoformat(),
                            "bid": price - 0.0002,
                            "ask": price + 0.0002,
                            "source": "Investing.com"
                        }
            except Exception as e:
                self.log(f"Investing.com fetch error: {str(e)}")
        
        # TradingView - try to get data via their widget/embed
        if source_name == "TradingView":
            try:
                # TradingView widget approach
                tv_url = f"https://www.tradingview.com/widget/?symbol={symbol}"
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(tv_url, headers=headers, timeout=10)
                # Note: TradingView requires more complex handling
            except:
                pass
        
        # Bloomberg and Reuters - typically require authentication
        # These are included for completeness but may not work without API keys
        
        return None
        
    def get_mt5_candles_and_indicators(self, symbol, timeframe_minutes=1, count=200):
        """Get historical candles from MT5 and calculate multiple technical indicators"""
        if not self.mt5_connected:
            return None
        
        try:
            # Get symbol info
            symbol_info = self.get_mt5_symbol_info(symbol)
            if symbol_info is None:
                return None
            
            # MT5 timeframe: 1 minute = 1
            timeframe = timeframe_minutes
            
            # Get historical candles (rates)
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                self.log(f"无法获取 {symbol} 的历史K线数据")
                return None
            
            # Extract OHLC data
            opens = [r[1] for r in rates]
            highs = [r[2] for r in rates]
            lows = [r[3] for r in rates]
            closes = [r[4] for r in rates]
            
            # ========== Indicator Calculation Functions ==========
            
            # Simple Moving Average (SMA)
            def calculate_sma(prices, period):
                if len(prices) < period:
                    return None
                return sum(prices[-period:]) / period
            
            # Exponential Moving Average (EMA)
            def calculate_ema(prices, period):
                if len(prices) < period:
                    return None
                ema = prices[0]
                multiplier = 2 / (period + 1)
                for price in prices[1:]:
                    ema = (price - ema) * multiplier + ema
                return ema
            
            # Relative Strength Index (RSI)
            def calculate_rsi(prices, period=14):
                if len(prices) < period + 1:
                    return None
                deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
                gains = [d if d > 0 else 0 for d in deltas]
                losses = [-d if d < 0 else 0 for d in deltas]
                avg_gain = sum(gains[-period:]) / period
                avg_loss = sum(losses[-period:]) / period
                if avg_loss == 0:
                    return 100
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            # MACD (Moving Average Convergence Divergence)
            def calculate_macd(prices, fast=12, slow=26, signal=9):
                ema_fast = calculate_ema(prices, fast)
                ema_slow = calculate_ema(prices, slow)
                if ema_fast is None or ema_slow is None:
                    return None, None, None
                macd_line = ema_fast - ema_slow
                # Signal line would need more complex calculation, simplifying here
                return macd_line, ema_fast, ema_slow
            
            # Bollinger Bands
            def calculate_bollinger(prices, period=20, std_dev=2):
                sma = calculate_sma(prices, period)
                if sma is None:
                    return None, None, None
                std = (sum((p - sma) ** 2 for p in prices[-period:]) / period) ** 0.5
                upper = sma + std_dev * std
                lower = sma - std_dev * std
                return upper, sma, lower
            
            # Average True Range (ATR)
            def calculate_atr(period=14):
                if len(rates) < period + 1:
                    return None
                trs = []
                for i in range(1, len(rates)):
                    tr = max(
                        rates[i][2] - rates[i][3],  # High - Low
                        abs(rates[i][2] - rates[i-1][4]),  # High - Previous Close
                        abs(rates[i][3] - rates[i-1][4])   # Low - Previous Close
                    )
                    trs.append(tr)
                return sum(trs[-period:]) / period
            
            # ========== Get Selected Indicators from Config ==========
            
            # Get indicator selection from config
            selected = self.indicators_config.get('selected_indicators', {}) if hasattr(self, 'indicators_config') else {}
            
            # ========== Calculate Only Selected Indicators ==========
            
            # Moving Averages (calculate if enabled in config)
            ma5 = calculate_sma(closes, 5) if selected.get('ma5', True) else None
            ma10 = calculate_sma(closes, 10) if selected.get('ma10', True) else None
            ma20 = calculate_sma(closes, 20) if selected.get('ma20', True) else None
            ma50 = calculate_sma(closes, 50) if selected.get('ma50', True) else None
            ma200 = calculate_sma(closes, 200) if selected.get('ma200', False) else None
            
            # Exponential Moving Averages (calculate if enabled in config)
            ema12 = calculate_ema(closes, 12) if selected.get('ema12', False) else None
            ema26 = calculate_ema(closes, 26) if selected.get('ema26', False) else None
            
            # RSI (calculate if enabled in config)
            rsi = calculate_rsi(closes, 14) if selected.get('rsi', True) else None
            
            # MACD (calculate if enabled in config)
            macd_line, macd_fast, macd_slow = (calculate_macd(closes) if selected.get('macd', True) else (None, None, None))
            
            # Bollinger Bands (calculate if enabled in config)
            bb_upper, bb_middle, bb_lower = (calculate_bollinger(closes) if selected.get('bollinger', True) else (None, None, None))
            
            # ATR (calculate if enabled in config)
            atr = calculate_atr(14) if selected.get('atr', False) else None
            
            # Previous values for signal detection
            ma10_prev = calculate_sma(closes[:-1], 10) if len(closes) > 10 else None
            ma50_prev = calculate_sma(closes[:-1], 50) if len(closes) > 50 else None
            rsi_prev = calculate_rsi(closes[:-1], 14) if len(closes) > 15 else None
            
            # ========== Signal Detection ==========
            
            signals = []
            
            # Create dictionary of MA values for easy access
            ma_dict = {
                'ma5': ma5, 'ma10': ma10, 'ma20': ma20, 'ma50': ma50, 'ma200': ma200,
                'ema12': ema12, 'ema26': ema26
            }
            
            # MA Crossover Signals (general for all selected MAs)
            # Check all possible MA pairs
            ma_pairs = [
                ('ma5', 'ma10'), ('ma5', 'ma20'), ('ma5', 'ma50'), ('ma5', 'ma200'),
                ('ma10', 'ma20'), ('ma10', 'ma50'), ('ma10', 'ma200'),
                ('ma20', 'ma50'), ('ma20', 'ma200'),
                ('ma50', 'ma200'),
                ('ema12', 'ema26')
            ]
            for fast_key, slow_key in ma_pairs:
                fast = ma_dict.get(fast_key)
                slow = ma_dict.get(slow_key)
                if fast is None or slow is None:
                    continue
                # Calculate previous values
                fast_period = int(fast_key[2:]) if fast_key.startswith('ma') else 12 if fast_key == 'ema12' else 26
                slow_period = int(slow_key[2:]) if slow_key.startswith('ma') else 12 if slow_key == 'ema12' else 26
                fast_prev = calculate_sma(closes[:-1], fast_period) if fast_key.startswith('ma') else calculate_ema(closes[:-1], fast_period)
                slow_prev = calculate_sma(closes[:-1], slow_period) if slow_key.startswith('ma') else calculate_ema(closes[:-1], slow_period)
                if fast_prev is None or slow_prev is None:
                    continue
                if fast_prev <= slow_prev and fast > slow:
                    signals.append(f"{fast_key.upper()}金叉{slow_key.upper()} - 做多")
                elif fast_prev >= slow_prev and fast < slow:
                    signals.append(f"{fast_key.upper()}死叉{slow_key.upper()} - 做空")
            
            # RSI Signals (only if RSI was calculated)
            if rsi is not None:
                if rsi < 30:
                    signals.append(f"RSI超卖({rsi:.1f}) - 可能反转做多")
                elif rsi > 70:
                    signals.append(f"RSI超买({rsi:.1f}) - 可能反转做空")
                if rsi_prev is not None:
                    if rsi_prev < 30 and rsi >= 30:
                        signals.append("RSI从超卖区域回升 - 做多信号")
                    elif rsi_prev > 70 and rsi <= 70:
                        signals.append("RSI从超买区域回落 - 做空信号")
            
            # MACD Signals (only if MACD was calculated)
            if macd_line is not None and macd_fast is not None and macd_slow is not None:
                if macd_fast > macd_slow:
                    signals.append("MACD多头排列(EMA12>EMA26) - 做多")
                else:
                    signals.append("MACD空头排列(EMA12<EMA26) - 做空")
            
            # Bollinger Bands Signals (only if BB was calculated)
            current_price = closes[-1] if closes else None
            if bb_upper is not None and bb_lower is not None and current_price is not None:
                if current_price < bb_lower:
                    signals.append(f"价格触及下轨({bb_lower:.5f}) - 超卖可能反弹")
                elif current_price > bb_upper:
                    signals.append(f"价格触及上轨({bb_upper:.5f}) - 超买可能回落")
            
            # ========== Technical Signals Calculation (User Defined) ==========
            
            technical_signals = []
            
            # 1. 金叉/死叉 (already covered in MA crossover above)
            
            # 2. 顶背离/底背离 (Divergence)
            # For simplicity, we'll implement basic divergence detection
            if len(closes) >= 30 and rsi is not None:
                # Look at last 20 periods
                lookback = 20
                recent_closes = closes[-lookback:]
                recent_highs = highs[-lookback:]
                recent_lows = lows[-lookback:]
                # Find highest high and lowest low
                price_high = max(recent_highs)
                price_low = min(recent_lows)
                # Get RSI values for same period (current RSI is for entire series)
                # We need RSI for each period; simplified: use current RSI vs previous RSI
                # For proper divergence we need historical RSI values - skip for now
                pass
            
            # 3. 突破 (Breakout)
            if len(closes) >= 21:
                recent_20_closes = closes[-21:-1]  # previous 20 closes (excluding current)
                recent_20_high = max(recent_20_closes)
                recent_20_low = min(recent_20_closes)
                current_close = closes[-1]
                current_open = opens[-1]
                # 向上突破: 当前K线收盘价突破近期20根K线最高收盘价，且为阳线
                if current_close > recent_20_high and current_close > current_open:
                    technical_signals.append(f"向上突破: 收盘{current_close:.5f} > 近期最高{recent_20_high:.5f} 阳线")
                # 向下突破: 当前K线收盘价跌破近期20根K线最低收盘价，且为阴线
                if current_close < recent_20_low and current_close < current_open:
                    technical_signals.append(f"向下突破: 收盘{current_close:.5f} < 近期最低{recent_20_low:.5f} 阴线")
            
            # 4. 回踩确认 (Pullback confirmation)
            # Simplified: check if price is near recent high/low after a breakout
            if len(closes) >= 30:
                # Look back 25 periods for potential breakout level
                lookback = 25
                recent_closes = closes[-lookback:]
                recent_high = max(recent_closes[:-5])  # high before last 5 periods
                recent_low = min(recent_closes[:-5])
                current_close = closes[-1]
                # Define "near" as within 0.5% (adjustable)
                threshold = 0.005  # 0.5%
                # Check for upward breakout pullback
                if current_close > recent_high * (1 - threshold) and current_close > recent_high:
                    technical_signals.append(f"向上突破后回踩确认: 收盘{current_close:.5f} 仍高于突破位{recent_high:.5f}")
                # Check for downward breakout pullback
                if current_close < recent_low * (1 + threshold) and current_close < recent_low:
                    technical_signals.append(f"向下突破后回踩确认: 收盘{current_close:.5f} 仍低于突破位{recent_low:.5f}")
            
            # Add technical signals to main signals list
            signals.extend(technical_signals)
            
            # Recent candles for context
            recent_candles = []
            for i in range(-5, 0):
                if abs(i) <= len(rates):
                    r = rates[i]
                    recent_candles.append({
                        "time": datetime.fromtimestamp(r[0]).strftime("%H:%M"),
                        "open": r[1],
                        "high": r[2],
                        "low": r[3],
                        "close": r[4]
                    })
            
            # Log all indicators (with proper formatting)
            # Build log string - only show calculated indicators
            log_parts = []
            if ma10 is not None: log_parts.append(f"MA10={ma10:.5f}")
            if ma20 is not None: log_parts.append(f"MA20={ma20:.5f}")
            if ma50 is not None: log_parts.append(f"MA50={ma50:.5f}")
            if ma200 is not None: log_parts.append(f"MA200={ma200:.5f}")
            if rsi is not None: log_parts.append(f"RSI={rsi:.1f}")
            if macd_line is not None: log_parts.append(f"MACD={macd_line:.5f}")
            if bb_upper is not None: log_parts.append(f"BB上={bb_upper:.1f}")
            if bb_lower is not None: log_parts.append(f"BB下={bb_lower:.1f}")
            if atr is not None: log_parts.append(f"ATR={atr:.2f}")
            
            indicator_summary = "指标: " + ", ".join(log_parts) if log_parts else "指标: 无"
            self.log(indicator_summary)
            if signals:
                self.log(f"信号: {' | '.join(signals)}")
            
            return {
                # Moving Averages
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
                "ma50": ma50,
                "ma200": ma200,
                # EMAs
                "ema12": ema12,
                "ema26": ema26,
                # RSI
                "rsi": rsi,
                "rsi_prev": rsi_prev,
                # MACD
                "macd": macd_line,
                "macd_fast": macd_fast,
                "macd_slow": macd_slow,
                # Bollinger Bands
                "bb_upper": bb_upper,
                "bb_middle": bb_middle,
                "bb_lower": bb_lower,
                # ATR
                "atr": atr,
                # MA signals
                "ma10_prev": ma10_prev,
                "ma50_prev": ma50_prev,
                # Signals
                "signals": signals,
                "signal_summary": " | ".join(signals) if signals else "无明确信号",
                # Context
                "recent_candles": recent_candles,
                "close_price": closes[-1] if closes else None,
                "timeframe": f"{timeframe_minutes}分钟",
                "candle_count": len(rates)
            }
            
        except Exception as e:
            self.log(f"获取K线指标错误: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return None
    
    def get_mock_market_data(self, symbol):
        """Get market data - in production, this should fetch from actual sources"""
        # This is mock data for testing
        return {
            "symbol": symbol,
            "price": 1.0850,
            "timestamp": datetime.now().isoformat(),
            "source": "mock",
            "bid": 1.0848,
            "ask": 1.0852,
            "ma20": 1.0830,
            "ma40": 1.0820,
            "trend": "bullish"
        }
        
    def analyze_market(self, market_data):
        """Analyze market data and generate trading signals using configured strategies and percentages"""
        
        # Check if we have at least one strategy configured
        if not self.long_strategy and not self.short_strategy:
            self.log("No strategy defined. Please configure long/short strategy in web interface.")
            return None
        
        # Get indicator data from MT5 using config settings
        indicators_enabled = self.indicators_config.get('enabled', True)
        if indicators_enabled:
            timeframe = self.indicators_config.get('timeframe', 1)
            count = self.indicators_config.get('candle_count', 200)
            indicators = self.get_mt5_candles_and_indicators(self.trading_pair, timeframe_minutes=timeframe, count=count)
        else:
            indicators = None
        
        # Get Level 2 market data (order book/depth)
        level2_enabled = self.indicators_config.get('level2_enabled', True)
        if level2_enabled:
            level2_data = self.get_mt5_level2_data(self.trading_pair)
        else:
            level2_data = None
        
        # Get current price and digits for calculation
        current_price = market_data.get('price', 0)
        digits = market_data.get('digits', 5)
        
        # Save to instance variables for later use
        self._current_price = current_price
        self._current_digits = digits
        
        # Build prompt using CONFIGURED strategies and percentages (not AI generated)
        # Use the configured long/short strategies
        long_strategy_text = self.long_strategy if self.long_strategy else "未配置"
        short_strategy_text = self.short_strategy if self.short_strategy else "未配置"
        
        # Use configured percentages
        long_sl = self.long_sl_percent if self.long_sl_percent else 0
        long_tp = self.long_tp_percent if self.long_tp_percent else 0
        short_sl = self.short_sl_percent if self.short_sl_percent else 0
        short_tp = self.short_tp_percent if self.short_tp_percent else 0
        
        # Get rules
        rules_text = self.rules if self.rules else "无"
        
        # Build prompt - STRICTLY use configured values
        # Include ALL indicator data if available
        indicator_info = ""
        if indicators:
            close_price = indicators.get('close_price')
            
            # Extract all indicators
            ma5 = indicators.get('ma5')
            ma10 = indicators.get('ma10')
            ma20 = indicators.get('ma20')
            ma50 = indicators.get('ma50')
            ma200 = indicators.get('ma200')
            ema12 = indicators.get('ema12')
            ema26 = indicators.get('ema26')
            rsi = indicators.get('rsi')
            macd = indicators.get('macd')
            macd_fast = indicators.get('macd_fast')
            macd_slow = indicators.get('macd_slow')
            bb_upper = indicators.get('bb_upper')
            bb_middle = indicators.get('bb_middle')
            bb_lower = indicators.get('bb_lower')
            atr = indicators.get('atr')
            signals = indicators.get('signals', [])
            signal_summary = indicators.get('signal_summary', '无信号')
            
            # Format indicator values - only show calculated ones, hide uncalculated
            # Build indicator sections conditionally
            
            # Moving Averages section
            ma_lines = []
            if ma5 is not None: ma_lines.append(f"- SMA5: {ma5:.5f}")
            if ma10 is not None: ma_lines.append(f"- SMA10: {ma10:.5f}")
            if ma20 is not None: ma_lines.append(f"- SMA20: {ma20:.5f}")
            if ma50 is not None: ma_lines.append(f"- SMA50: {ma50:.5f}")
            if ma200 is not None: ma_lines.append(f"- SMA200: {ma200:.5f}")
            ma_section = "【移动平均线 SMA】:\n" + "\n".join(ma_lines) + "\n" if ma_lines else ""
            
            # EMA section
            ema_lines = []
            if ema12 is not None: ema_lines.append(f"- EMA12: {ema12:.5f}")
            if ema26 is not None: ema_lines.append(f"- EMA26: {ema26:.5f}")
            ema_section = "【指数移动平均线 EMA】:\n" + "\n".join(ema_lines) + "\n" if ema_lines else ""
            
            # RSI section
            rsi_section = ""
            if rsi is not None:
                rsi_section = f"""【RSI 相对强弱指标】:
- RSI(14): {rsi:.2f}
  (RSI>70=超买, RSI<30=超卖)

"""
            
            # MACD section
            macd_lines = []
            if macd is not None: macd_lines.append(f"- DIF: {macd:.5f}")
            if macd_slow is not None: macd_lines.append(f"- DEA(EMA26): {macd_slow:.5f}")
            macd_section = "【MACD 指数平滑异同移动平均线】:\n" + "\n".join(macd_lines) + "\n" if macd_lines else ""
            
            # Bollinger Bands section
            bb_lines = []
            if bb_upper is not None: bb_lines.append(f"- 上轨: {bb_upper:.5f}")
            if bb_middle is not None: bb_lines.append(f"- 中轨: {bb_middle:.5f}")
            if bb_lower is not None: bb_lines.append(f"- 下轨: {bb_lower:.5f}")
            bb_section = "【布林带 Bollinger Bands】:\n" + "\n".join(bb_lines) + "\n" if bb_lines else ""
            
            # ATR section
            atr_section = ""
            if atr is not None:
                atr_section = f"【ATR 平均真实波幅】:\n- ATR(14): {atr:.5f}\n"
            
            # Close price
            close_str = f"- 收盘价: {close_price:.5f}" if close_price is not None else ""
            
            indicator_info = f"""
【技术指标数据】(来自{indicators.get('timeframe', '1分钟')}K线, 共{indicators.get('candle_count', 0)}根):
{close_str}

{ma_section}{ema_section}{rsi_section}{macd_section}{bb_section}{atr_section}
【⚠️ 技术信号】(Python程序计算，必须基于这些信号判断):
{signal_summary}

【重要】必须根据上方计算的技术信号进行判断:
- 金叉/死叉: 短周期均线上穿/下穿长周期均线
- 突破: 价格突破近期高点/低点
- 回踩确认: 突破后价格回踩但仍保持突破方向
- 背离: 价格与指标出现背离（如顶背离、底背离）

【信号解读】:
- MA金叉(MA10上穿MA50) = 做多信号
- MA死叉(MA10下穿MA50) = 做空信号
- RSI<30 超卖，可能反转做多
- RSI>70 超买，可能反转做空
- 价格突破布林上轨可能回落，跌破下轨可能反弹
"""
        
        # Calculate SL/TP prices for both long and short
        # For BUY: SL below price, TP above price
        long_sl_price = None
        long_tp_price = None
        short_sl_price = None
        short_tp_price = None
        
        if current_price and current_price > 0:
            # Calculate prices based on configured percentages
            if long_sl > 0:
                long_sl_price = round(current_price * (1 - long_sl/100), digits)
            if long_tp > 0:
                long_tp_price = round(current_price * (1 + long_tp/100), digits)
            if short_sl > 0:
                short_sl_price = round(current_price * (1 + short_sl/100), digits)
            if short_tp > 0:
                short_tp_price = round(current_price * (1 - short_tp/100), digits)
        
        # Build Level 2 market data info
        level2_info = ""
        if level2_data and level2_data.get('available'):
            bid_vol = level2_data.get('total_bid_volume', 0)
            ask_vol = level2_data.get('total_ask_volume', 0)
            bid_ratio = level2_data.get('bid_ratio', 0.5)
            sentiment = level2_data.get('sentiment', '未知')
            best_bid = level2_data.get('best_bid')
            best_ask = level2_data.get('best_ask')
            spread = level2_data.get('spread')
            
            # Get top 5 levels for display
            bid_levels = level2_data.get('bid_levels', [])[:5]
            ask_levels = level2_data.get('ask_levels', [])[:5]
            
            bid_str = ", ".join([f"{l['price']:.5f}({l['volume']})" for l in bid_levels])
            ask_str = ", ".join([f"{l['price']:.5f}({l['volume']})" for l in ask_levels])
            
            # Format Level 2 values properly - use is not None
            best_bid_str = f"{best_bid:.5f}" if best_bid is not None else "N/A"
            best_ask_str = f"{best_ask:.5f}" if best_ask is not None else "N/A"
            spread_str = f"{spread:.5f}" if spread is not None else "N/A"
            bid_ratio_str = f"{bid_ratio:.1%}" if bid_ratio is not None else "N/A"
            
            level2_info = f"""

【Level 2 市场深度】(如有):
- 买盘总量: {bid_vol}
- 卖盘总量: {ask_vol}
- 买方占比: {bid_ratio_str}
- 市场情绪: {sentiment}
- 最佳买价: {best_bid_str}
- 最佳卖价: {best_ask_str}
- 深度点差: {spread_str}
- 买盘5档: {bid_str}
- 卖盘5档: {ask_str}

【Level2 交易提示】:
- 买方占比>60%: 市场偏多，可能上涨
- 买方占比<40%: 市场偏空，可能下跌
- 买盘挂单量突然增加: 可能护盘或诱多
- 卖盘挂单量突然增加: 可能压盘或诱空
"""
        
        # Format price info for prompt
        price_info = ""
        if long_sl_price is not None or long_tp_price is not None:
            price_info += f"\n【做多止损止盈价格】(已计算好，直接使用):\n"
            if long_sl_price is not None:
                price_info += f"- 做多止损价格: {long_sl_price}\n"
            if long_tp_price is not None:
                price_info += f"- 做多止盈价格: {long_tp_price}\n"
        
        if short_sl_price is not None or short_tp_price is not None:
            price_info += f"\n【做空止损止盈价格】(已计算好，直接使用):\n"
            if short_sl_price is not None:
                price_info += f"- 做空止损价格: {short_sl_price}\n"
            if short_tp_price is not None:
                price_info += f"- 做空止盈价格: {short_tp_price}\n"
        
        analysis_prompt = f"""
你是一个专业的外汇交易分析师。根据以下市场数据和分析策略，判断是否应该交易。

【警告】你必须【逐条检查】下方的策略条件，只有【全部满足】时才可下单！

交易品种: {self.trading_pair}
当前价格: {current_price}
买入价(Ask): {market_data.get('ask', current_price)}
卖出价(Bid): {market_data.get('bid', current_price)}
小数位数: {digits}位
点差: {market_data.get('spread', 'N/A')}点
{indicator_info}{level2_info}
【做多策略】(必须逐条检查，全部满足才可做多):
{long_strategy_text}
【重要】必须同时满足以上所有条件才可做多，任何一条不满足都必须待机！

【做多止损比例】: {long_sl}% (价格 × (1 - {long_sl}%))
【做多止盈比例】: {long_tp}% (价格 × (1 + {long_tp}%))

【做空策略】(必须逐条检查，全部满足才可做空):
{short_strategy_text}
【重要】必须同时满足以上所有条件才可做空，任何一条不满足都必须待机！

【做空止损比例】: {short_sl}% (价格 × (1 + {short_sl}%))
【做空止盈比例】: {short_tp}% (价格 × (1 - {short_tp}%))

{price_info}
【必须遵守规则】: {rules_text}

【决策流程】（必须按此流程）:
1. 逐条检查做多策略条件 → 如果全部满足 → 做多
2. 逐条检查做空策略条件 → 如果全部满足 → 做空
3. 任何条件不满足 → 待机

【输出格式】（只输出以下三种之一，不要其他内容）：
- 做多 止损{long_sl_price if long_sl_price is not None else '无'} 止盈{long_tp_price if long_tp_price is not None else '无'}
- 做空 止损{short_sl_price if short_sl_price is not None else '无'} 止盈{short_tp_price if short_tp_price is not None else '无'}
- 待机

注意：止损和止盈后面必须是计算好的具体价格数值，不是百分比！Executor会直接复制这些数值到MT5。

根据策略判断，现在应该做什么操作？
"""
        
        # Use 10 conversation rounds (increased from 2)
        history_context = ""
        if self.conversation_history:
            recent_history = self.conversation_history[-10:]  # Use last 10 rounds
            history_context = "\n".join([f"{msg['role']}: {msg['content'][:200]}" for msg in recent_history])
            analysis_prompt = f"历史对话:\n{history_context}\n\n" + analysis_prompt
        
        # Add indicator info to system prompt as well
        system_indicator_info = ""
        if indicators:
            ma10 = indicators.get('ma10')
            ma50 = indicators.get('ma50')
            signal = indicators.get('crossover_signal', '无信号')
            if ma10 is not None and ma50 is not None:
                ma10_p = f"{ma10:.5f}"
                ma50_p = f"{ma50:.5f}"
                system_indicator_info = f"""
【技术指标】:
- MA10: {ma10_p}
- MA50: {ma50_p}
- 交叉信号: {signal}
"""
        
        # Format calculated prices for system prompt
        long_sl_price_str = f"{long_sl_price}" if long_sl_price is not None else "无"
        long_tp_price_str = f"{long_tp_price}" if long_tp_price is not None else "无"
        short_sl_price_str = f"{short_sl_price}" if short_sl_price is not None else "无"
        short_tp_price_str = f"{short_tp_price}" if short_tp_price is not None else "无"
        
        system_prompt = f"""你是一个专业的外汇交易分析师。
【严格遵守规则 - 违反以下规则将导致错误交易】
1. 必须【逐条检查】配置的做多/做空策略条件，只有【全部满足】时才可下单
2. 不得自行决定止损止盈数值，【必须】使用已计算好的价格
3. 做多时【必须】使用做多策略和做多价格，做空时【必须】使用做空策略和做空价格
4. 必须根据Python程序计算的技术信号来判断，【严禁】凭感觉或猜测下单
5. 【严禁输出平仓指令】系统只等待止盈或止损，不主动平仓
6. 如果策略条件【任何一条】不满足，【必须】输出"待机"

【策略检查清单】（做多时）:
{long_strategy_text}
→ 逐条检查上述条件，全部满足才可做多，否则必须待机

【策略检查清单】（做空时）:
{short_strategy_text}
→ 逐条检查上述条件，全部满足才可做空，否则必须待机

{system_indicator_info}

当前配置（必须严格遵守）:
- 做多策略: {long_strategy_text}
- 做多止损价格: {long_sl_price_str} (基于{long_sl}%计算)
- 做多止盈价格: {long_tp_price_str} (基于{long_tp}%计算)
- 做空策略: {short_strategy_text}
- 做空止损价格: {short_sl_price_str} (基于{short_sl}%计算)
- 做空止盈价格: {short_tp_price_str} (基于{short_tp}%计算)
- 必须遵守规则: {rules_text}
- 当前价格: {current_price}

【决策依据】:
- 主要依据: Python程序计算的技术信号（金叉/死叉、突破、回踩确认、背离）
- 次要参考: 指标数值和Level2市场深度
- 必须优先考虑技术信号，再结合配置的策略

【输出规则】:
只输出以下三种指令之一（不要输出品种和数量，这些已在MT5中设定好）：
- 做多 止损{long_sl_price_str} 止盈{long_tp_price_str}
- 做空 止损{short_sl_price_str} 止盈{short_tp_price_str}
- 待机

注意：止损和止盈后面必须是计算好的具体价格数值（如"止损38300.50"），不是百分比！Executor会直接复制这些数值到MT5。

不要输出其他内容，只输出指令。"""
        
        result = self.call_ollama(analysis_prompt, system_prompt)
        
        # 清理和标准化指令输出
        if result:
            result = result.strip()
            lines = result.split('\n')
            for line in lines:
                line = line.strip()
                # 处理做多指令
                if line.startswith("做多"):
                    # 检查是否已包含止损止盈
                    if "止损" in line and "止盈" in line:
                        return line  # 直接返回
                    else:
                        # 添加配置的百分比
                        cmd = f"做多 止损{long_sl}% 止盈{long_tp}%"
                        return cmd
                # 处理做空指令
                elif line.startswith("做空"):
                    # 检查是否已包含止损止盈
                    if "止损" in line and "止盈" in line:
                        return line  # 直接返回
                    else:
                        # 添加配置的百分比
                        cmd = f"做空 止损{short_sl}% 止盈{short_tp}%"
                        return cmd
                # 处理待机/不操作指令
                elif line.startswith("待机") or "不操作" in line or "观望" in line:
                    return "待机"
                # 如果LLM错误地输出平仓，转换为待机
                elif "平仓" in line:
                    self.log("警告: LLM尝试输出平仓指令，已转换为待机")
                    return "待机"
        
        # 如果没有明确指令，默认待机
        return "待机"
        
    def parse_command(self, response):
        """Parse the LLM response to extract trading command"""
        if not response:
            return None
            
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            # 只处理做多、做空、待机指令
            if line.startswith("做多") or line.startswith("做空") or line == "待机":
                return line
        return None
        
    def calculate_sl_tp_prices(self, command, current_price, digits):
        """Calculate SL and TP prices from command with percentages"""
        import re
        
        # Extract SL and TP percentages
        sl_match = re.search(r'止损\s*(\d+(?:\.\d+)?)\s*%?', command)
        tp_match = re.search(r'止盈\s*(\d+(?:\.\d+)?)\s*%?', command)
        
        sl_price = None
        tp_price = None
        
        if current_price and current_price > 0:
            # For BUY orders: SL below price, TP above price
            if "做多" in command or "买入" in command:
                if sl_match:
                    sl_percent = float(sl_match.group(1))
                    sl_price = round(current_price * (1 - sl_percent/100), digits)
                
                if tp_match:
                    tp_percent = float(tp_match.group(1))
                    tp_price = round(current_price * (1 + tp_percent/100), digits)
            
            # For SELL orders: SL above price, TP below price
            elif "做空" in command or "卖出" in command:
                if sl_match:
                    sl_percent = float(sl_match.group(1))
                    sl_price = round(current_price * (1 + sl_percent/100), digits)
                
                if tp_match:
                    tp_percent = float(tp_match.group(1))
                    tp_price = round(current_price * (1 - tp_percent/100), digits)
        
        return sl_price, tp_price
    
    def send_command_to_executor(self, command):
        """Send command to executor agent - 直接发送命令，不重新计算价格"""
        if command:
            self.log(f"发送交易指令: {command}")
            try:
                # Get current price and digits for reference
                current_price = getattr(self, '_current_price', 0)
                digits = getattr(self, '_current_digits', 5)
                
                # 如果命令中已经有实际价格（没有%符号），直接发送，不重新计算
                # 检查命令中是否有%符号
                has_percent = '%' in command
                
                if has_percent:
                    # 如果命令中有%符号，需要计算实际价格
                    self.log("命令中包含百分比，需要计算实际价格...")
                    sl_price, tp_price = self.calculate_sl_tp_prices(command, current_price, digits)
                    
                    if sl_price is not None and tp_price is not None:
                        # 替换百分比为实际价格
                        import re
                        command_with_prices = re.sub(r'止损\s*\d+(?:\.\d+)?\s*%', f'止损 {sl_price}', command)
                        command_with_prices = re.sub(r'止盈\s*\d+(?:\.\d+)?\s*%', f'止盈 {tp_price}', command_with_prices)
                        command_to_send = command_with_prices
                        self.log(f"计算后的价格 - 止损: {sl_price}, 止盈: {tp_price}")
                    else:
                        command_to_send = command
                        self.log("警告: 无法计算止损止盈价格，发送原始命令")
                else:
                    # 命令中没有%符号，已经是实际价格，直接发送
                    command_to_send = command
                    self.log("命令中已经是实际价格，直接发送")
                
                # Send price info for reference (包含当前价格和小数位数)
                price_info = f"@price={current_price}@digits={digits}"
                
                # 如果已经计算了实际价格，也发送给executor作为参考
                if 'sl_price' in locals() and sl_price is not None:
                    price_info += f"@sl={sl_price}"
                if 'tp_price' in locals() and tp_price is not None:
                    price_info += f"@tp={tp_price}"
                
                with open(COMMANDS_FILE, 'w', encoding='utf-8') as f:
                    f.write("NEW:" + command_to_send + "\n")
                    f.write(price_info + "\n")
                return True
            except Exception as e:
                self.log(f"Error writing command: {str(e)}")
        return False
        
    def monitor_loop(self):
        """Main monitoring loop"""
        # 每次扫描时记录当前配置（帮助调试）
        self.log(f"开始自动盯盘模式 - 交易品种: {self.trading_pair}, 手数: {self.lot_size}")
        self.log(f"📋 当前配置 - 止损: 多{self.long_sl_percent}%/空{self.short_sl_percent}%, 止盈: 多{self.long_tp_percent}%/空{self.short_tp_percent}%")
        self.log(f"📈 时间级别: {self.timeframe}分钟, 最大持仓: {self.max_positions}单")
        
        # 获取并记录启用的指标
        selected_indicators = self.indicators_config.get('selected_indicators', {})
        enabled_indicators = [k for k, v in selected_indicators.items() if v]
        self.log(f"📊 启用指标: {enabled_indicators}")
        self.log(f"📜 规则: {self.rules}")
        
        while self.running and self.mode == "monitor":
            try:
                # ========== 扫描开始 ==========
                scan_time = datetime.now().strftime("%H:%M:%S")
                self.log(f"📡 开始扫描 - 时间: {scan_time}, 品种: {self.trading_pair}")
                
                # Get market data
                self.log("🔍 获取市场数据...")
                market_data = self.search_market_data(self.trading_pair)
                
                # 检查是否仍处于监控模式
                if self.mode != "monitor":
                    self.log("监控模式已切换，停止当前扫描")
                    break
                
                if market_data and 'price' in market_data and market_data['price'] > 0:
                    self.log(f"📊 市场数据获取成功 - 价格: {market_data['price']}, 时间: {market_data.get('timestamp', 'N/A')}")
                else:
                    self.log("⚠️ 市场数据获取失败或价格无效")
                
                # Save to cache
                with open(MARKET_DATA_CACHE, 'w', encoding='utf-8') as f:
                    json.dump(market_data, f, indent=2, ensure_ascii=False)
                
                # ========== 分析开始 ==========
                self.log("🧠 开始技术分析...")
                response = self.analyze_market(market_data)
                
                # 检查是否仍处于监控模式
                if self.mode != "monitor":
                    self.log("监控模式已切换，停止当前扫描")
                    break
                
                if response:
                    self.log(f"✅ AI分析完成 - 结果: {response}")
                    
                    # Parse command
                    command = self.parse_command(response)
                    
                    if command:
                        # 检查是否仍处于监控模式
                        if self.mode != "monitor":
                            self.log("监控模式已切换，取消发送指令")
                            break
                        
                        # ========== 检查最大持仓数限制 ==========
                        current_positions = self.get_mt5_positions()
                        position_count = len(current_positions)
                        
                        if position_count >= self.max_positions:
                            self.log(f"⚠️ 持仓数已达上限: {position_count}/{self.max_positions} 单，需等待平仓后才能开新单")
                            # 不发送交易指令，等待下次扫描
                        else:
                            # ========== 发送指令 ==========
                            self.log(f"🚀 发送交易指令: {command}")
                            self.send_command_to_executor(command)
                            self.log("📤 指令已发送到Executor")
                    else:
                        self.log("⚠️ 未识别到有效交易指令")
                else:
                    self.log("❌ 分析失败")
                
                # ========== 扫描完成 ==========
                self.log(f"✅ 扫描完成 - 等待下次扫描 ({self.monitoring_interval}秒后)")
                    
                # Wait for next check (supports float intervals like 0.5 seconds)
                if not self.running:
                    break
                time.sleep(self.monitoring_interval)
                    
            except Exception as e:
                self.log(f"❌ 监控循环错误: {str(e)}")
                time.sleep(10)
                
    def set_mode(self, mode):
        """Set the working mode"""
        if mode == "monitor":
            # 重新加载配置，确保使用最新设置（包括交易品种、指标、规则等）
            self.log("重新加载配置...")
            self.load_config()
            self.log(f"已加载最新配置 - 交易品种: {self.trading_pair}, 指标: {list(self.indicators_config.get('selected_indicators', {}).keys())}")
            self.log(f"止损止盈配置 - 长止损:{self.long_sl_percent}%, 长止盈:{self.long_tp_percent}%, 短止损:{self.short_sl_percent}%, 短止盈:{self.short_tp_percent}%")
            self.log(f"规则: {self.rules}")
            
            # 检查交易品种和策略配置
            if not self.trading_pair:
                self.log("错误: 请先设置交易品种")
                return False
            
            # 检查是否有策略配置（长策略或短策略）
            if not self.long_strategy and not self.short_strategy:
                self.log("错误: 请先设置长策略或短策略")
                self.log(f"当前长策略: {'已设置' if self.long_strategy else '未设置'}")
                self.log(f"当前短策略: {'已设置' if self.short_strategy else '未设置'}")
                return False
                
            self.mode = "monitor"
            self.save_config()
            self.log("切换到自动盯盘模式")
            self.log(f"交易品种: {self.trading_pair}")
            self.log(f"长策略: {'已设置' if self.long_strategy else '未设置'}")
            self.log(f"短策略: {'已设置' if self.short_strategy else '未设置'}")
            
            # 启动监控线程（如果未在运行）
            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
                self.monitor_thread.start()
                self.log("监控线程已启动")
            else:
                self.log("监控线程已在运行")
                
        else:
            self.mode = "discussion"
            self.running = True
            self.save_config()
            self.log("切换到讨论模式")
        return True
        
    def chat(self, user_input):
        """Process user input in discussion mode"""
        user_input = user_input.strip()
        
        if user_input == "策略固定，开始盯盘":
            if self.set_mode("monitor"):
                return "好的，策略已固定，开始自动盯盘模式。监控线程已启动。"
            else:
                return "错误: 请先设置交易品种和策略"
        
        # Handle configuration commands
        if user_input.startswith("设置品种 "):
            self.trading_pair = user_input.replace("设置品种 ", "").strip()
            self.save_config()
            return f"交易品种已设置为: {self.trading_pair}"
            
        if user_input.startswith("设置手数 "):
            try:
                self.lot_size = float(user_input.replace("设置手数 ", "").strip())
                self.save_config()
                return f"手数已设置为: {self.lot_size}"
            except:
                return "手数格式错误"
                
        if user_input.startswith("设置策略 "):
            self.strategy = user_input.replace("设置策略 ", "").strip()
            self.save_config()
            return f"策略已设置为: {self.strategy}"
            
        if user_input.startswith("设置间隔 "):
            try:
                # Support both integer and float (e.g., 10 or 0.5)
                interval_str = user_input.replace("设置间隔 ", "").strip()
                if '.' in interval_str:
                    self.monitoring_interval = float(interval_str)
                else:
                    self.monitoring_interval = int(interval_str)
                self.save_config()
                return f"监控间隔已设置为: {self.monitoring_interval}秒"
            except:
                return "间隔格式错误"
                
        if user_input == "查看配置":
            return f"""当前配置:
交易品种: {self.trading_pair}
手数: {self.lot_size}
策略: {self.strategy}
监控间隔: {self.monitoring_interval}秒
模式: {self.mode}"""
        
        # Auto-configure: Analyze conversation to auto-detect and set configuration
        if user_input in ["自动配置", "帮我配置", "配置交易", "开始配置"]:
            return self.auto_configure_from_context()
            
        # Regular chat with LLM
        system_prompt = """你是一个专业的外汇交易AI助手。用户会和你讨论交易策略。
你需要：
1. 理解用户的交易需求
2. 帮助用户制定交易策略
3. 回答用户关于交易的问题

当用户说"策略固定，开始盯盘"时，表示策略讨论结束，准备开始自动监控。
在此之前，请和用户充分讨论：
- 交易品种
- 交易手数
- 具体策略（如MA金叉死叉）
- 其他交易参数

请用中文回复。"""
        
        # Save to conversation history for auto-configuration
        self.conversation_history.append({"role": "user", "content": user_input})
        
        response = self.call_ollama(user_input, system_prompt)
        
        # Save AI response to history
        if response:
            self.conversation_history.append({"role": "assistant", "content": response})
        
        return response if response else "抱歉，我遇到了一些问题，请重试。"
        
    def stop(self):
        """Stop the application"""
        self.running = False
        self.mode = "discussion"
        self.save_config()
        
        # Perform log rotation when exiting
        self._rotate_log_on_exit()
    
    def _rotate_log_on_exit(self):
        """Rotate log file when the application exits"""
        import shutil
        
        LOG_DIR = "E:\\TradingSystem\\logs"
        
        try:
            # Create logs directory if it doesn't exist
            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR)
            
            # Check if log file exists
            if not os.path.exists(LOG_FILE):
                return
            
            # Get log file info
            log_size = os.path.getsize(LOG_FILE)
            log_mtime = datetime.fromtimestamp(os.path.getmtime(LOG_FILE))
            
            # Only rotate if log file has content or is from a previous day
            today = datetime.now().date()
            
            if log_size > 0 or log_mtime.date() < today:
                # Generate timestamp for old log file
                timestamp_str = log_mtime.strftime("%Y%m%d_%H%M%S")
                log_filename = os.path.basename(LOG_FILE)
                old_log_name = f"{log_filename.replace('.log', '')}_{timestamp_str}.log"
                old_log_path = os.path.join(LOG_DIR, old_log_name)
                
                # Move old log to logs directory
                try:
                    shutil.move(LOG_FILE, old_log_path)
                    print(f"[LOG] 旧日志已保存到: {old_log_path}")
                except Exception as e:
                    print(f"[LOG] 移动日志文件失败: {str(e)}")
        except Exception as e:
            # Silently ignore errors during exit
            pass

def main():
    """Main entry point"""
    print("=" * 50)
    print("AutoGPT Trading System")
    print("=" * 50)
    
    # Set UTF-8 encoding for output
    import sys
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    bot = AutoGPTTrading()
    
    # Check if Ollama is available
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            print("[OK] Ollama connected")
        else:
            print("[ERROR] Ollama connection failed")
    except:
        print("[ERROR] Cannot connect to Ollama, please make sure Ollama is running")
        
    print(f"当前模式: {bot.mode}")
    print("-" * 50)
    print("可用命令:")
    print("  设置品种 [品种]    - 设置交易品种，如 EURUSD")
    print("  设置手数 [手数]   - 设置交易手数，如 0.01")
    print("  设置策略 [策略]   - 设置交易策略")
    print("  设置间隔 [秒]     - 设置监控间隔")
    print("  查看配置          - 查看当前配置")
    print("  策略固定，开始盯盘 - 开始自动监控")
    print("  退出              - 退出程序")
    print("-" * 50)
    
    # 无论config.json中设置什么模式，始终以讨论模式启动
    # 等待用户通过Web界面或命令行控制
    if bot.mode == "monitor":
        print("注意: config.json中模式为'monitor'，已重置为'discussion'")
        print("请通过Web界面重新启动监控模式")
        bot.mode = "discussion"
        bot.save_config()
    
    # Interactive mode (discussion)
    print("当前处于交互模式，可通过以下方式启动自动交易:")
    print("  1. 在Web界面中点击 'Start Monitor' 按钮 (推荐)")
    print("  2. 或在此输入: '策略固定，开始盯盘'")
    print("  3. 或输入: '查看配置' 检查当前设置")
    print("-" * 50)
    print("提示: 监控启动后，此窗口仍可接受命令（如'退出'）")
    print("-" * 50)
    
    # Interactive loop
    while True:
        try:
            user_input = input("\n请输入: ").strip()
            
            if user_input == "退出":
                bot.stop()
                print("再见!")
                break
                
            if not user_input:
                continue
                
            response = bot.chat(user_input)
            print(f"\n{response}")
            
        except KeyboardInterrupt:
            bot.stop()
            print("\n程序已停止")
            break
        except Exception as e:
            print(f"错误: {str(e)}")

if __name__ == "__main__":
    main()
