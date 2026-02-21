# Trading System Features & Command Manual

## 1. System Overview

This is a Python-based automated trading system that integrates MetaTrader 5 (MT5), Ollama local LLM for decision-making, and PyAutoGUI for interface automation.

### Core Modules

| Module | File | Function |
|--------|------|----------|
| Main Program | autogpt_trading.py | Connect to MT5, calculate technical indicators, call AI for decisions |
| Executor | executor_agent.py | Control MT5 interface via PyAutoGUI to execute trades |
| Web Interface | web_interface.py | Flask web interface for configuration and monitoring |
| Window Manager | window_manager.py | Auto-arrange MT5 and browser window positions |

---

## 2. Recent Updates (2026-02-21)

### 2.1 Today's Update Log

| Time | Update Content |
|------|----------------|
| 02:45 | Backup version backup_20260221_0245 |
| 08:23 | Backup version backup_20260221_0823 - Optimized monitoring logic |
| 08:26 | Backup version backup_20260221_0823 |
| 09:04 | Backup version backup_20260221_0904 - Enhanced RSI signal detection |
| 09:25 | Backup version backup_20260221_0925 - Final test version |
| 09:26 | System test run - XAUUSD, 1-minute period, RSI overbought signal detected normally |
| 21:04 | Latest source update - autogpt_trading.py (98KB) |

### 2.2 Main Feature Updates

1. **Quick Fail Mechanism** - Immediately give up if any trading step fails, wait for next opportunity
2. **Enhanced RSI Signals** - 71.2 overbought detection, 40/60 key level detection
3. **Multi-Timeframe Support** - 1min/5min/15min multi-timeframe confirmation
4. **Enhanced Rules Parsing** - Auto-parse timeframe and max positions from Rules field
5. **Trailing Stop** - Activate trailing stop when profit reaches threshold
6. **Partial Close** - Automatically close partial position when profit reaches threshold

---

## 3. Feature Details

### 3.1 Risk Control

| Feature | Config Example | Description |
|---------|----------------|-------------|
| Max Drawdown | `最大回撤率: 5%` | Pause trading and close all positions when loss reaches 5% |
| Daily Max Loss | `每日最大亏损: 100` | Pause trading when daily loss reaches $100 |
| Spread Limit | `点差限制: 30点` | Do not execute trades when spread exceeds 30 points |
| Position Limit | `最大持仓: 5单` | Maximum 5 concurrent orders |

### 3.2 Trading Session Control

```
交易时段: 09:00-17:00    # Trade only during this period
交易时段: 22:00-02:00    # Overnight trading session
```

### 3.3 Trailing Stop

```
移动止损: 激活0.5%, 距离0.3%
# Activate trailing stop when profit reaches 0.3%, stop distance is 0.3%
```

### 3.4 Partial Close

```
部分平仓: 0.3%, 50%
# Close 50% of position when profit reaches 0.3%
```

### 3.5 Higher Timeframe Confirmation

```
更高周期: 5分钟    # Use 5-minute period to confirm trend direction
更高周期: 15分钟   # Use 15-minute period to confirm trend direction
```

### 3.6 One-Click Close

```
平仓热键: ctrl+shift+c    # Hotkey for MT5 one-click close all
```

---

## 4. Command Set (Prompt Recognition)

### 4.1 Discussion Mode Commands

| Command | Description | Example |
|---------|-------------|---------|
| `设置品种 [symbol]` | Set trading symbol | `设置品种 XAUUSD` |
| `设置手数 [lot]` | Set lot size | `设置手数 0.1` |
| `设置策略 [strategy]` | Set trading strategy | `设置策略 MA金叉` |
| `设置间隔 [seconds]` | Set monitoring interval | `设置间隔 1` |
| `查看配置` | Show current config | `查看配置` |
| `策略固定，开始盯盘` | Start auto-trading | `策略固定，开始盯盘` |
| `自动配置` | AI auto-analyze config | `自动配置` |
| `退出` | Exit program | `退出` |

### 4.2 Web Interface Rules Field Commands

The system automatically parses the following rules from the Rules field:

#### Risk Control
```
最大回撤率: 5%
每日最大亏损: 100
```

#### Trading Session
```
交易时段: 09:00-17:00
```

#### Spread Filter
```
点差限制: 30点
```

#### Trailing Stop
```
移动止损: 激活0.5%, 距离0.3%
```

#### Partial Close
```
部分平仓: 0.3%, 50%
```

#### Higher Timeframe Confirmation
```
更高周期: 5分钟
```

#### Position Limit
```
最大持仓: 5单
```

#### Close All Hotkey
```
平仓热键: ctrl+shift+c
```

### 4.3 Trading Conditions Configuration

#### Long Strategy (long_strategy)

```
1. Price > EMA9 > EMA21
2. Current candle volume ≥ 150% of 3-period average
3. RSI crosses above 40
```

#### Short Strategy (short_strategy)

```
1. Price < EMA9 < EMA21
2. Current candle volume ≥ 150% of 3-period average
3. RSI crosses below 60
```

### 4.4 Stop Loss / Take Profit Settings

| Setting | Description |
|---------|-------------|
| Long Stop Loss % | Long position stop loss % (e.g., 0.3%) |
| Long Take Profit % | Long position take profit % (e.g., 0.6%) |
| Short Stop Loss % | Short position stop loss % (e.g., 0.3%) |
| Short Take Profit % | Short position take profit % (e.g., 0.6%) |

---

## 5. Technical Indicators

### 5.1 Moving Averages

| Indicator | Period | Use |
|-----------|--------|-----|
| MA5 | 5 | Short-term trend |
| MA10 | 10 | Short-term trend |
| MA20 | 20 | Medium-term trend |
| MA50 | 50 | Medium-long term trend |
| MA200 | 200 | Long-term trend |
| EMA9 | 9 | Fast exponential moving average |
| EMA21 | 21 | Medium-speed exponential moving average |
| EMA12 | 12 | MACD component |
| EMA26 | 26 | MACD component |

### 5.2 Oscillators

| Indicator | Description | Signal |
|-----------|-------------|--------|
| RSI | Relative Strength Index | <30 oversold, >70 overbought |
| MACD | Moving Average Convergence Divergence | Golden cross/death cross |
| Bollinger | Bollinger Bands | Break upper/lower rail |
| ATR | Average True Range | Volatility |

### 5.3 Volume Analysis

```
Current volume ≥ 150% × 3-period average = Volume surge signal
```

### 5.4 Candlestick Patterns

| Pattern | Signal |
|---------|--------|
| Bullish Engulfing | Long signal |
| Bearish Engulfing | Short signal |
| Hammer | Possible reversal long |
| Hanging Man | Possible reversal short |
| Doji | Wait and see |

---

## 6. Trading Flow

### 6.1 Auto-Monitoring Flow

```
1. Get market data (MT5)
2. Calculate technical indicators (MA, RSI, MACD, etc.)
3. AI analysis and decision (Ollama)
4. Send trade command to Executor
5. Executor executes trade:
   - Activate MT5 window (0.05s)
   - Press F9 to open order window (0.8s)
   - Enter stop loss / take profit prices
   - Click Buy/Sell button
6. Verify trade result
7. Any step fails → Immediately give up → Wait for next opportunity
```

### 6.2 Quick Fail Mechanism

- Window activation fails → Immediately give up
- Trade verification fails → Immediately give up
- Click operation fails → Immediately give up
- Exception occurs → Immediately give up

---

## 7. Pause & Resume

### 7.1 Pause Trigger Conditions

- Loss reaches max drawdown
- Loss reaches daily max loss amount

### 7.2 Behavior After Pause

1. Immediately send one-click close command
2. Wait for existing positions to close
3. Remain paused

### 7.3 Ways to Resume Trading

1. Manual program restart
2. After midnight local time 24:00 (automatic reset next day)

---

## 8. File Locations

| File | Description |
|------|-------------|
| config.json | Configuration file |
| commands.txt | Trading commands (written by program) |
| market_cache.json | Market data cache |
| autogpt.log | Main program log |
| executor.log | Executor log |
| mt5_positions.json | MT5 button position calibration |

---

## 9. Startup Methods

### Recommended: Manual Startup

```bash
cd E:\TradingSystem
start_manual.bat
```

### Alternative: Auto Startup

```bash
cd E:\TradingSystem
start_trading_fixed.bat
```

### Window Layout Adjustment

```bash
cd E:\TradingSystem
python window_manager.py
```

---

## 10. Web Interface

- Address: http://127.0.0.1:5000
- Features:
  - Configure trading symbol and strategy
  - Set stop loss / take profit ratios
  - Test MT5 connection
  - Calibrate MT5 button positions
  - Switch discussion/monitoring mode
  - View real-time signals

---

Last Updated: 2026-02-21 23:51
