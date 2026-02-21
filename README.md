Feel free to reach out if you have any questions! Follow my WeChat Official Account: CLINGYWANG and contact me via private message, or send an email to A2747597@163.com.
# Automated Trading System

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
│   ├── 安装指南.md           # Installation Guide (Chinese)
│   └── 使用指南.md           # User Guide (Chinese)
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
