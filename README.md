Feel free to reach out if you have any questions! Follow my WeChat Official Account: CLINGYWANG and contact me via private message, or send an email to A2747597@163.com.
# Automated Trading System
# No API Fees! The People's Quant Revolution: One-Time Install, Lifetime Use, AI-Generated Strategies, Minute-Level Trading

## 🚀 Project Overview
This is a **game-changing AI-powered automated trading system** built for ordinary investors and small trading studios. It breaks down the high barriers of traditional quantitative trading: **no API fees, no recurring costs, one-time installation for lifetime use**.

With local Ollama models (free) or online large models (for better performance), you only need to describe your trading idea in plain language—no coding, no quant knowledge required. The AI will generate, optimize, and execute strategies automatically.

It runs smoothly on a regular home computer (8GB RAM is enough), works with all major trading software, and is optimized for **minute-level / 10-minute-level medium-low frequency trading**. It’s perfect for domestic futures/indices in China and overseas T+0 markets.

## ✨ Core Advantages (Why This Is a Must-Have)

### 1. No API Fees, One-Time Install = Lifetime Zero Cost
- No more monthly/transaction-based API fees to exchanges or brokers.
- One-time purchase, lifetime use, no hidden charges.
- For medium-low frequency trading, your per-trade cost is effectively zero—far cheaper than any API-based system.

### 2. AI-Generated Strategies: No Expertise Needed
- Just tell the AI your trading idea (e.g., "Minute-level trend trading on rebar futures" or "Overseas T+0 buy-low-sell-high").
- Use local Ollama models for free, or switch to online models for deeper analysis and optimization.
- No Python, no financial modeling—AI does all the heavy lifting.

### 3. Low Hardware & Software Requirements
- Runs on a regular home computer (no need for expensive servers).
- Works with all major trading software (no vendor lock-in).
- 5-minute one-click setup, no technical skills required.

### 4. Optimized for Medium-Low Frequency Trading
- Avoids the high costs and risks of high-frequency trading.
- Perfect for regular investors who want to automate without being glued to the screen.
- Supports domestic futures/indices in China and overseas T+0 markets.

### 5. Extensible & Adaptable
- Can be deeply integrated with any trading software or platform.
- Future-proof: ready to scale into a full quant ecosystem.

## 🛠️ Quick Start (3 Steps)

1.  **Download the installer** from the repository.
2.  **Double-click `setup.iss`** to install the system.
3.  **Launch the app**, type your trading idea, and start automated trading.

## 📊 How It Compares

| Feature | This System | Traditional API-Based Quant Tools | Copy Trading Services |
|---------|-------------|-----------------------------------|-----------------------|
| Cost | One-time fee, lifetime use, no API fees | Monthly/transaction-based API fees | High profit-sharing commissions |
| Strategy Development | AI-generated from plain language | Requires Python/quant expertise | No strategy development, just follow others |
| Hardware | Runs on a regular home computer | Requires professional servers | Low hardware, but no quant capabilities |
| Trading Frequency | Optimized for minute-level / 10-minute-level | Optimized for high-frequency (only for institutions) | Passive, no control over frequency |
| Privacy | All data and strategies run locally | Data shared with third-party APIs | Account and strategy data shared with platforms |

## 📞 Get in Touch
Feel free to reach out if you have any questions!  
Follow my WeChat Official Account: **CLINGYWANG** and contact me via private message, or send an email to **A2747597@163.com**.

## 📝 License
This project is licensed under the MIT License.
A Python-based automated trading system that integrates with MetaTrader 5 (MT5) and uses local AI (Ollama) for decision-making.

## Features

- 🤖 **AI-Powered Trading**: Uses local Large Language Models (via Ollama) for trading decisions
- 📊 **MT5 Integration**: Seamless integration with MetaTrader 5
- 🎯 **Automated Execution**: Automatically executes trades based on AI signals
- 🌐 **Web Interface**: Built-in web dashboard for monitoring and control
- 🪟 **Window Management**: Automatic window positioning and management

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Ollama    │────▶│   Trading    │────▶│    MT5      │
│  (Local AI) │     │    Agent     │     │  (Broker)   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    Web       │
                    │  Interface   │
                    └──────────────┘
```

## Prerequisites

Before installing, you need to have the following software installed:

1. **MetaTrader 5 (MT5)**
   - Download from: https://www.metatrader5.com/
   - Open a demo or live trading account

2. **Ollama (Local AI Runtime)**
   - Download from: https://ollama.com/
   - Pull your preferred model: `ollama pull llama3` (or other models)

3. **Python 3.10+**
   - Download from: https://www.python.org/downloads/
   - Required packages: `pip install openai metaTrader5 python-dotenv flask`

## Installation

### Option 1: Use the Installer (Recommended)
1. Download the latest release from the Releases page
2. Run `TradingSystem_Setup_v1.0.0.exe`
3. Follow the installation wizard
4. Configure `config.json` with your MT5 credentials

### Option 2: Manual Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/automated-trading-system.git
cd automated-trading-system

# Install dependencies
pip install openai metaTrader5 python-dotenv flask

# Configure
# Edit config.json with your settings

# Run
start_manual.bat
```

## Configuration

Edit `config.json` to configure your settings:

```json
{
  "mt5_login": "your_mt5_login",
  "mt5_password": "your_mt5_password",
  "mt5_server": "your_broker_server",
  "ollama_url": "http://localhost:11434",
  "model": "llama3",
  "max_trades": 3,
  "risk_level": "medium"
}
```

## Usage

### Starting the System

**Option 1: Desktop Shortcut**
- Double-click the "一键启动交易系统" (One-Click Start) desktop shortcut

**Option 2: Manual Start**
```bash
cd "C:\Program Files\Automated Trading System"
start_manual.bat
```

### Web Interface

Access the web dashboard at: http://localhost:5000

- View current positions
- Monitor AI decision logs
- Check system status

## Project Structure

```
├── source/
│   ├── autogpt_trading.py    # Main trading logic
│   ├── executor_agent.py     # AI agent for execution
│   ├── web_interface.py      # Web dashboard
│   ├── window_manager.py     # Window positioning
│   ├── config.json           # Configuration
│   ├── mt5_positions.json    # MT5 button positions
│   ├── start_manual.bat      # Recommended startup script
│   └── start_trading_fixed.bat # Alternative startup
├── docs/
│   ├── Installation Guide.md           # Installation Guide (Chinese)
│   └── User Guide.md           # User Guide (Chinese)
└── output/
    └── TradingSystem_Setup_v*.exe # Windows Installer
```

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading in financial markets involves substantial risk. 

- **Use at your own risk**
- Always test with a demo account first
- Never trade with money you cannot afford to lose
- The authors are not responsible for any financial losses

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Note**: This project does not include MT5, Ollama, or AI models. Users must install these dependencies separately according to the installation guide.
