#!/usr/bin/env python3
"""
AutoGPT Trading Web Interface - Full Features
"""

from flask import Flask, render_template_string, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

SESSION_LOG_FILE = "E:\\TradingSystem\\session_log.txt"
chat_history = []

HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AutoGPT Trading System</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #1a1a2e; color: #eee; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: #00d4ff; }
        h2 { color: #00ff88; margin-top: 20px; }
        h3 { color: #ffaa00; margin: 15px 0 10px; }
        .section { background: #16213e; padding: 20px; margin: 20px 0; border-radius: 10px; }
        .row { display: flex; gap: 20px; }
        .col { flex: 1; }
        label { display: block; margin: 8px 0 3px; font-size: 12px; color: #aaa; }
        input, select, textarea { width: 100%; padding: 8px; margin: 3px 0; background: #0f3460; border: 1px solid #533483; color: #eee; border-radius: 5px; box-sizing: border-box; }
        .checkbox-group { display: flex; align-items: center; gap: 5px; margin: 3px 0; }
        .checkbox-group input { width: auto; }
        button { padding: 10px 20px; margin: 10px 5px 10px 0; background: #00d4ff; border: none; color: #1a1a2e; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #00a8cc; }
        button.success { background: #28a745; color: #fff; }
        button.danger { background: #dc3545; color: #fff; }
        .log-container { background: #0f3460; padding: 15px; height: 300px; overflow-y: auto; border-radius: 5px; font-family: monospace; font-size: 12px; scroll-behavior: smooth; }
        .log-entry { margin: 3px 0; color: #00ff88; }
        .chat-messages { background: #0f3460; padding: 15px; height: 180px; overflow-y: auto; border-radius: 5px; }
        .chat-msg { margin: 5px 0; }
        .test-result { background: #0f3460; padding: 10px; border-radius: 5px; margin-top: 10px; max-height: 500px; overflow-y: auto; }
        .test-section { margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #2a4569; }
        .test-section:last-child { border-bottom: none; }
        .test-section-title { color: #00d4ff; font-weight: bold; margin-bottom: 8px; font-size: 14px; }
        .test-item { display: flex; margin: 4px 0; }
        .test-label { min-width: 150px; color: #aaa; }
        .test-value { color: #eee; flex-grow: 1; }
        .test-value.success { color: #28a745; }
        .test-value.error { color: #dc3545; }
        .test-signal-list { list-style: none; padding-left: 0; }
        .test-signal-item { background: #2a4569; padding: 6px 10px; margin: 4px 0; border-radius: 4px; border-left: 3px solid #00d4ff; }
        .test-signal-item.buy { border-left-color: #28a745; }
        .test-signal-item.sell { border-left-color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AutoGPT Trading System</h1>
        
        <div class="section">
            <h2>Configuration</h2>
            <div class="row">
                <div class="col">
                    <label>Trading Pair:</label>
                    <input type="text" id="trading-pair" value="XAUUSD">
                    <label>Lot Size:</label>
                    <input type="number" id="lot-size" value="0.01" step="0.01">
                    <label>Monitoring Interval (seconds):</label>
                    <input type="number" id="monitoring-interval" value="1" step="0.5">
                </div>
                <div class="col">
                    <label>Mode:</label>
                    <select id="mode">
                        <option value="discussion">Discussion</option>
                        <option value="monitor">Monitor</option>
                    </select>
                </div>
            </div>
            
            <h3>Technical Indicators</h3>
            <div class="row">
                <div class="col">
                    <label>MA:</label>
                    <div class="checkbox-group"><input type="checkbox" id="ma5" checked> <span>MA5</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="ma10" checked> <span>MA10</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="ma20" checked> <span>MA20</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="ma50"> <span>MA50</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="ma200"> <span>MA200</span></div>
                </div>
                <div class="col">
                    <label>EMA:</label>
                    <div class="checkbox-group"><input type="checkbox" id="ema9"> <span>EMA9</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="ema12"> <span>EMA12</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="ema21"> <span>EMA21</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="ema26"> <span>EMA26</span></div>
                </div>
                <div class="col">
                    <label>Other:</label>
                    <div class="checkbox-group"><input type="checkbox" id="rsi" checked> <span>RSI</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="macd" checked> <span>MACD</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="bollinger" checked> <span>Bollinger</span></div>
                    <div class="checkbox-group"><input type="checkbox" id="atr"> <span>ATR</span></div>
                </div>
            </div>
            
            <h3>Long Strategy</h3>
            <div class="row">
                <div class="col">
                    <label>Strategy:</label>
                    <textarea id="long-strategy" rows="2"></textarea>
                </div>
                <div class="col">
                    <label>Stop Loss (%):</label>
                    <input type="number" id="long-sl" value="0.3" step="0.1">
                    <label>Take Profit (%):</label>
                    <input type="number" id="long-tp" value="0.6" step="0.1">
                </div>
            </div>
            
            <h3>Short Strategy</h3>
            <div class="row">
                <div class="col">
                    <label>Strategy:</label>
                    <textarea id="short-strategy" rows="2"></textarea>
                </div>
                <div class="col">
                    <label>Stop Loss (%):</label>
                    <input type="number" id="short-sl" value="0.3" step="0.1">
                    <label>Take Profit (%):</label>
                    <input type="number" id="short-tp" value="0.6" step="0.1">
                </div>
            </div>
            
            <h3>Rules</h3>
            <textarea id="rules" rows="2" placeholder="e.g., No martingale"></textarea>
            
            <button onclick="saveConfig()">Save Config</button>
            <button onclick="reloadConfig()">Reload Config</button>
            <button onclick="testData()">Test Data</button>
            <div id="test-result" class="test-result"></div>
        </div>
        
        <div class="section">
            <h2>Chat</h2>
            <input type="text" id="user-input" placeholder="Type message..." onkeypress="if(event.key==='Enter')sendMessage()">
            <button onclick="sendMessage()">Send</button>
            <button onclick="autoConfig()">Auto Config</button>
            <div class="chat-messages" id="chat-messages"></div>
        </div>
        
        <div class="section">
            <button onclick="startMonitor()" class="success">Start Monitor</button>
            <button onclick="stopMonitor()" class="danger">Stop Monitor</button>
        </div>
        
        <div class="section">
            <h2>Logs</h2>
            <div class="log-container" id="log-container"></div>
        </div>
    </div>
    
    <script>
        function saveConfig() {
            var config = {
                trading_pair: document.getElementById('trading-pair').value,
                lot_size: parseFloat(document.getElementById('lot-size').value),
                monitoring_interval: parseFloat(document.getElementById('monitoring-interval').value),
                mode: document.getElementById('mode').value,
                indicators: {
                    ma5: document.getElementById('ma5').checked,
                    ma10: document.getElementById('ma10').checked,
                    ma20: document.getElementById('ma20').checked,
                    ma50: document.getElementById('ma50').checked,
                    ma200: document.getElementById('ma200').checked,
                    ema9: document.getElementById('ema9').checked,
                    ema12: document.getElementById('ema12').checked,
                    ema21: document.getElementById('ema21').checked,
                    ema26: document.getElementById('ema26').checked,
                    rsi: document.getElementById('rsi').checked,
                    macd: document.getElementById('macd').checked,
                    bollinger: document.getElementById('bollinger').checked,
                    atr: document.getElementById('atr').checked
                },
                long_strategy: document.getElementById('long-strategy').value,
                long_sl_percent: parseFloat(document.getElementById('long-sl').value),
                long_tp_percent: parseFloat(document.getElementById('long-tp').value),
                short_strategy: document.getElementById('short-strategy').value,
                short_sl_percent: parseFloat(document.getElementById('short-sl').value),
                short_tp_percent: parseFloat(document.getElementById('short-tp').value),
                rules: document.getElementById('rules').value
            };
            fetch('/save_config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            }).then(function(r){return r.json()}).then(function(data){
                document.getElementById('test-result').innerHTML = 'Config saved!';
                addLog('[System] Config saved - Strictly following');
            });
        }
        
        function reloadConfig() {
            fetch('/reload_config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            }).then(function(r){return r.json()}).then(function(data){
                document.getElementById('test-result').innerHTML = data.message || 'Config reloaded!';
                addLog('[System] Config reloaded - ' + (data.message || 'Success'));
                loadConfig(); // Refresh the displayed config
            });
        }
        
        function testData() {
            var symbol = document.getElementById('trading-pair').value;
            document.getElementById('test-result').innerHTML = 'Testing ' + symbol + '...';
            fetch('/test_data?symbol=' + symbol).then(function(r){return r.json()}).then(function(data){
                // Build HTML with clear sections
                var html = '';
                
                // Symbol and connection status section
                html += '<div class="test-section">';
                html += '<div class="test-section-title">Symbol & Connection</div>';
                html += '<div class="test-item"><div class="test-label">Symbol:</div><div class="test-value">' + data.symbol + '</div></div>';
                html += '<div class="test-item"><div class="test-label">MT5 Connected:</div><div class="test-value ' + (data.mt5_connected ? 'success' : 'error') + '">' + (data.mt5_connected ? 'Yes' : 'No') + '</div></div>';
                html += '</div>';
                
                if (data.mt5_connected) {
                    // Candles and Level2 data section
                    html += '<div class="test-section">';
                    html += '<div class="test-section-title">Market Data</div>';
                    html += '<div class="test-item"><div class="test-label">Candles:</div><div class="test-value">' + data.candle_count + ' bars</div></div>';
                    if (data.current_price) {
                        html += '<div class="test-item"><div class="test-label">Current Price:</div><div class="test-value">' + data.current_price.toFixed(5) + '</div></div>';
                    }
                    html += '<div class="test-item"><div class="test-label">Level2:</div><div class="test-value ' + (data.level2_available ? 'success' : '') + '">' + (data.level2_available ? 'Available' : 'Not available') + '</div></div>';
                    if (data.bid_volume && data.ask_volume) {
                        html += '<div class="test-item"><div class="test-label">Bid Volume:</div><div class="test-value">' + data.bid_volume + '</div></div>';
                        html += '<div class="test-item"><div class="test-label">Ask Volume:</div><div class="test-value">' + data.ask_volume + '</div></div>';
                        var totalVol = data.bid_volume + data.ask_volume;
                        var bidRatio = totalVol > 0 ? (data.bid_volume / totalVol * 100).toFixed(1) : 0;
                        html += '<div class="test-item"><div class="test-label">Bid Ratio:</div><div class="test-value">' + bidRatio + '%</div></div>';
                    }
                    html += '</div>';
                    
                    // Indicators section
                    var indicators = data.indicators_calculated;
                    if (Object.keys(indicators).length > 0) {
                        html += '<div class="test-section">';
                        html += '<div class="test-section-title">Technical Indicators</div>';
                        // Group indicators by type for better organization
                        var maIndicators = {};
                        var emaIndicators = {};
                        var otherIndicators = {};
                        
                        for (var key in indicators) {
                            if (key.startsWith('MA') || key.startsWith('SMA')) {
                                maIndicators[key] = indicators[key];
                            } else if (key.startsWith('EMA')) {
                                emaIndicators[key] = indicators[key];
                            } else if (key.startsWith('BB_')) {
                                otherIndicators[key] = indicators[key];
                            } else {
                                otherIndicators[key] = indicators[key];
                            }
                        }
                        
                        // Display MA indicators
                        if (Object.keys(maIndicators).length > 0) {
                            html += '<div style="margin-bottom: 10px;">';
                            html += '<div style="color: #aaa; font-size: 12px; margin-bottom: 5px;">Moving Averages:</div>';
                            for (var key in maIndicators) {
                                html += '<div class="test-item"><div class="test-label">' + key + ':</div><div class="test-value">' + maIndicators[key] + '</div></div>';
                            }
                            html += '</div>';
                        }
                        
                        // Display EMA indicators
                        if (Object.keys(emaIndicators).length > 0) {
                            html += '<div style="margin-bottom: 10px;">';
                            html += '<div style="color: #aaa; font-size: 12px; margin-bottom: 5px;">Exponential MAs:</div>';
                            for (var key in emaIndicators) {
                                html += '<div class="test-item"><div class="test-label">' + key + ':</div><div class="test-value">' + emaIndicators[key] + '</div></div>';
                            }
                            html += '</div>';
                        }
                        
                        // Display other indicators
                        if (Object.keys(otherIndicators).length > 0) {
                            html += '<div>';
                            html += '<div style="color: #aaa; font-size: 12px; margin-bottom: 5px;">Other Indicators:</div>';
                            for (var key in otherIndicators) {
                                var value = otherIndicators[key];
                                var valueClass = '';
                                if (key === 'RSI') {
                                    valueClass = value < 30 ? 'success' : value > 70 ? 'error' : '';
                                }
                                html += '<div class="test-item"><div class="test-label">' + key + ':</div><div class="test-value ' + valueClass + '">' + value + '</div></div>';
                            }
                            html += '</div>';
                        }
                        html += '</div>';
                    }
                    
                    // Signals section
                    var signals = data.signals;
                    if (signals && signals.length > 0) {
                        html += '<div class="test-section">';
                        html += '<div class="test-section-title">Technical Signals Detected</div>';
                        html += '<ul class="test-signal-list">';
                        for (var i = 0; i < signals.length; i++) {
                            var signal = signals[i];
                            var signalClass = '';
                            if (signal.includes('做多') || signal.includes('金叉') || signal.includes('多头') || signal.includes('向上突破') || signal.includes('超卖')) {
                                signalClass = 'buy';
                            } else if (signal.includes('做空') || signal.includes('死叉') || signal.includes('空头') || signal.includes('向下突破') || signal.includes('超买')) {
                                signalClass = 'sell';
                            }
                            html += '<li class="test-signal-item ' + signalClass + '">' + signal + '</li>';
                        }
                        html += '</ul>';
                        html += '</div>';
                    } else {
                        html += '<div class="test-section">';
                        html += '<div class="test-section-title">Technical Signals</div>';
                        html += '<div class="test-item"><div class="test-label">Signals:</div><div class="test-value">None detected</div></div>';
                        html += '</div>';
                    }
                } else {
                    // MT5 not connected
                    html += '<div class="test-section">';
                    html += '<div class="test-section-title">Connection Error</div>';
                    html += '<div class="test-item"><div class="test-label">Status:</div><div class="test-value error">MT5 not connected. Please check MT5 installation and ensure terminal is running.</div></div>';
                    html += '</div>';
                }
                
                // Error section (if any)
                if (data.error) {
                    html += '<div class="test-section">';
                    html += '<div class="test-section-title">Error Details</div>';
                    html += '<div class="test-item"><div class="test-label">Error:</div><div class="test-value error">' + data.error + '</div></div>';
                    html += '</div>';
                }
                
                document.getElementById('test-result').innerHTML = html;
                addLog('[System] Data test complete');
            });
        }
        
        function sendMessage() {
            var input = document.getElementById('user-input');
            var msg = input.value.trim();
            if (!msg) return;
            addChat('You', msg);
            input.value = '';
            fetch('/send_message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg})
            }).then(function(r){return r.json()}).then(function(data){
                addChat('Bot', data.response || 'OK');
            });
        }
        
        function autoConfig() {
            var tp = document.getElementById('trading-pair').value;
            var ls = document.getElementById('lot-size').value;
            var intv = document.getElementById('monitoring-interval').value;
            var longStr = document.getElementById('long-strategy').value;
            var longSL = document.getElementById('long-sl').value;
            var longTP = document.getElementById('long-tp').value;
            var shortStr = document.getElementById('short-strategy').value;
            var shortSL = document.getElementById('short-sl').value;
            var shortTP = document.getElementById('short-tp').value;
            var rules = document.getElementById('rules').value;
            
            addLog('=== AUTO CONFIG ===', 'system');
            addLog('Pair: ' + tp + ', Lot: ' + ls + ', Interval: ' + intv + 's', 'system');
            addLog('Long: ' + longStr + ', SL: ' + longSL + '%, TP: ' + longTP + '%', 'system');
            addLog('Short: ' + shortStr + ', SL: ' + shortSL + '%, TP: ' + shortTP + '%', 'system');
            addLog('Rules: ' + rules, 'system');
            addLog('======================', 'system');
        }
        
        function startMonitor() {
            fetch('/start_monitor', {method:'POST'}).then(function(r){return r.json()}).then(function(d){
                addLog('[System] Monitor started');
                document.getElementById('mode').value = 'monitor';
            });
        }
        
        function stopMonitor() {
            fetch('/stop_monitor', {method:'POST'}).then(function(r){return r.json()}).then(function(d){
                addLog('[System] Monitor stopped');
                document.getElementById('mode').value = 'discussion';
            });
        }
        
        function addChat(sender, msg) {
            var div = document.createElement('div');
            div.className = 'chat-msg';
            div.innerHTML = '<b>' + sender + ':</b> ' + msg;
            document.getElementById('chat-messages').appendChild(div);
            document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
            fetch('/save_log', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type:'chat', sender:sender, message:msg})});
        }
        
        function addLog(msg) {
            var div = document.createElement('div');
            div.className = 'log-entry';
            div.textContent = msg;
            var container = document.getElementById('log-container');
            container.appendChild(div);
            // 使用setTimeout确保在DOM更新后滚动到底部
            setTimeout(function() {
                container.scrollTop = container.scrollHeight;
            }, 0);
            fetch('/save_log', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type:'log', message:msg})});
        }
        
        function loadConfig() {
            fetch('/get_config').then(function(r){return r.json()}).then(function(data){
                if(data.trading_pair) document.getElementById('trading-pair').value = data.trading_pair;
                if(data.lot_size) document.getElementById('lot-size').value = data.lot_size;
                if(data.monitoring_interval) document.getElementById('monitoring-interval').value = data.monitoring_interval;
                if(data.mode) document.getElementById('mode').value = data.mode;
                if(data.indicators) {
                    if(data.indicators.ma5!==undefined) document.getElementById('ma5').checked = data.indicators.ma5;
                    if(data.indicators.ma10!==undefined) document.getElementById('ma10').checked = data.indicators.ma10;
                    if(data.indicators.ma20!==undefined) document.getElementById('ma20').checked = data.indicators.ma20;
                    if(data.indicators.ma50!==undefined) document.getElementById('ma50').checked = data.indicators.ma50;
                    if(data.indicators.ma200!==undefined) document.getElementById('ma200').checked = data.indicators.ma200;
                    if(data.indicators.ema9!==undefined) document.getElementById('ema9').checked = data.indicators.ema9;
                    if(data.indicators.ema12!==undefined) document.getElementById('ema12').checked = data.indicators.ema12;
                    if(data.indicators.ema21!==undefined) document.getElementById('ema21').checked = data.indicators.ema21;
                    if(data.indicators.ema26!==undefined) document.getElementById('ema26').checked = data.indicators.ema26;
                    if(data.indicators.rsi!==undefined) document.getElementById('rsi').checked = data.indicators.rsi;
                    if(data.indicators.macd!==undefined) document.getElementById('macd').checked = data.indicators.macd;
                    if(data.indicators.bollinger!==undefined) document.getElementById('bollinger').checked = data.indicators.bollinger;
                    if(data.indicators.atr!==undefined) document.getElementById('atr').checked = data.indicators.atr;
                }
                if(data.long_strategy) document.getElementById('long-strategy').value = data.long_strategy;
                if(data.long_sl_percent) document.getElementById('long-sl').value = data.long_sl_percent;
                if(data.long_tp_percent) document.getElementById('long-tp').value = data.long_tp_percent;
                if(data.short_strategy) document.getElementById('short-strategy').value = data.short_strategy;
                if(data.short_sl_percent) document.getElementById('short-sl').value = data.short_sl_percent;
                if(data.short_tp_percent) document.getElementById('short-tp').value = data.short_tp_percent;
                if(data.rules) document.getElementById('rules').value = data.rules;
            });
        }
        
        window.onload = function() {
            loadConfig();
            addLog('[System] Ready');
            setInterval(function(){
                fetch('/get_logs').then(function(r){return r.json()}).then(function(data){
                    if(data.logs) {
                        var container = document.getElementById('log-container');
                        container.innerHTML = '';
                        data.logs.forEach(function(l){
                            var div = document.createElement('div');
                            div.className = 'log-entry';
                            div.textContent = l.message;
                            container.appendChild(div);
                        });
                        // 滚动到最新日志
                        setTimeout(function() {
                            container.scrollTop = container.scrollHeight;
                        }, 0);
                    }
                });
            }, 3000);
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/favicon.ico')
def favicon():
    # Return empty response to avoid 404 errors
    return '', 204

@app.route('/save_config', methods=['POST'])
def save_config():
    data = request.json
    try:
        with open('E:\\TradingSystem\\config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_config')
def get_config():
    try:
        with open('E:\\TradingSystem\\config.json', 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({})

@app.route('/test_data')
def test_data():
    symbol = request.args.get('symbol', 'XAUUSD')
    result = {
        'symbol': symbol, 
        'mt5_connected': False,
        'candle_count': 0,
        'level2_available': False,
        'indicators_calculated': {},
        'signals': [],
        'error': None
    }
    
    # Load config to get selected indicators
    try:
        with open('E:\\TradingSystem\\config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        config = {}
    
    indicators_config = config.get('indicators', {})
    
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            result['mt5_connected'] = True
            
            # Get Level 2 data
            if hasattr(mt5, 'market_book_get'):
                book = mt5.market_book_get(symbol)
                if book and len(book) > 0:
                    result['level2_available'] = True
                    result['bid_volume'] = sum(e.volume for e in book if e.type == 0)
                    result['ask_volume'] = sum(e.volume for e in book if e.type == 1)
            
            # Get historical candles
            rates = mt5.copy_rates_from_pos(symbol, 1, 0, 200)
            if rates is not None and len(rates) > 0:
                result['candle_count'] = len(rates)
                opens = [r[1] for r in rates]
                highs = [r[2] for r in rates]
                lows = [r[3] for r in rates]
                closes = [r[4] for r in rates]
                current_price = closes[-1] if closes else None
                result['current_price'] = current_price
                
                # Helper functions
                def calc_sma(data, period):
                    if len(data) >= period:
                        return sum(data[-period:]) / period
                    return None
                
                def calc_ema(data, period):
                    if len(data) < period:
                        return None
                    ema = data[0]
                    multiplier = 2 / (period + 1)
                    for price in data[1:]:
                        ema = (price - ema) * multiplier + ema
                    return ema
                
                def calc_rsi(data, period=14):
                    if len(data) < period + 1:
                        return None
                    deltas = [data[i] - data[i-1] for i in range(1, len(data))]
                    gains = [d if d > 0 else 0 for d in deltas]
                    losses = [-d if d < 0 else 0 for d in deltas]
                    avg_gain = sum(gains[-period:]) / period
                    avg_loss = sum(losses[-period:]) / period
                    if avg_loss == 0:
                        return 100
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    return rsi
                
                def calc_macd(data, fast=12, slow=26, signal=9):
                    ema_fast = calc_ema(data, fast)
                    ema_slow = calc_ema(data, slow)
                    if ema_fast is None or ema_slow is None:
                        return None, None, None
                    macd_line = ema_fast - ema_slow
                    return macd_line, ema_fast, ema_slow
                
                def calc_bollinger(data, period=20, std_dev=2):
                    sma = calc_sma(data, period)
                    if sma is None:
                        return None, None, None
                    std = (sum((p - sma) ** 2 for p in data[-period:]) / period) ** 0.5
                    upper = sma + std_dev * std
                    lower = sma - std_dev * std
                    return upper, sma, lower
                
                def calc_atr(highs, lows, closes, period=14):
                    if len(highs) < period + 1:
                        return None
                    trs = []
                    for i in range(1, len(highs)):
                        tr = max(
                            highs[i] - lows[i],
                            abs(highs[i] - closes[i-1]),
                            abs(lows[i] - closes[i-1])
                        )
                        trs.append(tr)
                    return sum(trs[-period:]) / period
                
                # Calculate selected indicators
                indicators_calc = {}
                
                # Moving Averages
                if indicators_config.get('ma5', True):
                    ma5 = calc_sma(closes, 5)
                    if ma5 is not None: indicators_calc['MA5'] = round(ma5, 5)
                if indicators_config.get('ma10', True):
                    ma10 = calc_sma(closes, 10)
                    if ma10 is not None: indicators_calc['MA10'] = round(ma10, 5)
                if indicators_config.get('ma20', True):
                    ma20 = calc_sma(closes, 20)
                    if ma20 is not None: indicators_calc['MA20'] = round(ma20, 5)
                if indicators_config.get('ma50', False):
                    ma50 = calc_sma(closes, 50)
                    if ma50 is not None: indicators_calc['MA50'] = round(ma50, 5)
                if indicators_config.get('ma200', False):
                    ma200 = calc_sma(closes, 200)
                    if ma200 is not None: indicators_calc['MA200'] = round(ma200, 5)
                
                # Exponential Moving Averages
                if indicators_config.get('ema9', False):
                    ema9 = calc_ema(closes, 9)
                    if ema9 is not None: indicators_calc['EMA9'] = round(ema9, 5)
                if indicators_config.get('ema12', False):
                    ema12 = calc_ema(closes, 12)
                    if ema12 is not None: indicators_calc['EMA12'] = round(ema12, 5)
                if indicators_config.get('ema21', False):
                    ema21 = calc_ema(closes, 21)
                    if ema21 is not None: indicators_calc['EMA21'] = round(ema21, 5)
                if indicators_config.get('ema26', False):
                    ema26 = calc_ema(closes, 26)
                    if ema26 is not None: indicators_calc['EMA26'] = round(ema26, 5)
                
                # RSI
                if indicators_config.get('rsi', True):
                    rsi = calc_rsi(closes, 14)
                    if rsi is not None: indicators_calc['RSI'] = round(rsi, 2)
                
                # MACD
                if indicators_config.get('macd', True):
                    macd_line, macd_fast, macd_slow = calc_macd(closes)
                    if macd_line is not None: indicators_calc['MACD'] = round(macd_line, 5)
                    if macd_fast is not None: indicators_calc['MACD_FAST'] = round(macd_fast, 5)
                    if macd_slow is not None: indicators_calc['MACD_SLOW'] = round(macd_slow, 5)
                
                # Bollinger Bands
                if indicators_config.get('bollinger', True):
                    bb_upper, bb_middle, bb_lower = calc_bollinger(closes)
                    if bb_upper is not None: indicators_calc['BB_UPPER'] = round(bb_upper, 5)
                    if bb_middle is not None: indicators_calc['BB_MIDDLE'] = round(bb_middle, 5)
                    if bb_lower is not None: indicators_calc['BB_LOWER'] = round(bb_lower, 5)
                
                # ATR
                if indicators_config.get('atr', False):
                    atr = calc_atr(highs, lows, closes, 14)
                    if atr is not None: indicators_calc['ATR'] = round(atr, 5)
                
                result['indicators_calculated'] = indicators_calc
                
                # Simple signal detection (based on current values)
                signals = []
                current_price = closes[-1] if closes else None
                
                # MA cross signals (simplified)
                ma10 = calc_sma(closes, 10)
                ma50 = calc_sma(closes, 50)
                ma10_prev = calc_sma(closes[:-1], 10) if len(closes) > 10 else None
                ma50_prev = calc_sma(closes[:-1], 50) if len(closes) > 50 else None
                if ma10 is not None and ma50 is not None and ma10_prev is not None and ma50_prev is not None:
                    if ma10_prev <= ma50_prev and ma10 > ma50:
                        signals.append("MA金叉(MA10上穿MA50) - 做多")
                    elif ma10_prev >= ma50_prev and ma10 < ma50:
                        signals.append("MA死叉(MA10下穿MA50) - 做空")
                
                # RSI signals
                if 'RSI' in indicators_calc:
                    rsi_val = indicators_calc['RSI']
                    if rsi_val < 30:
                        signals.append(f"RSI超卖({rsi_val:.1f}) - 可能反转做多")
                    elif rsi_val > 70:
                        signals.append(f"RSI超买({rsi_val:.1f}) - 可能反转做空")
                
                # Breakout detection (simplified)
                if len(closes) >= 21:
                    recent_20_closes = closes[-21:-1]
                    recent_20_high = max(recent_20_closes)
                    recent_20_low = min(recent_20_closes)
                    current_close = closes[-1]
                    current_open = opens[-1]
                    if current_close > recent_20_high and current_close > current_open:
                        signals.append(f"向上突破: {current_close:.5f} > {recent_20_high:.5f}")
                    if current_close < recent_20_low and current_close < current_open:
                        signals.append(f"向下突破: {current_close:.5f} < {recent_20_low:.5f}")
                
                result['signals'] = signals
            
            mt5.shutdown()
    except Exception as e:
        result['error'] = str(e)
    
    return jsonify(result)

@app.route('/send_message', methods=['POST'])
def send_message():
    global chat_history
    data = request.json
    user_msg = data.get('message', '')
    chat_history.append({'type': 'chat', 'sender': 'You', 'message': user_msg})
    
    # Call Ollama for AI response
    try:
        import requests
        # Build conversation history for context
        recent_msgs = chat_history[-10:]  # Last 10 messages
        context = ""
        for msg in recent_msgs:
            if msg.get('type') == 'chat':
                context += f"{msg.get('sender')}: {msg.get('message')}\n"
        
        prompt = f"""You are a professional forex trading assistant. The user is asking: {user_msg}

Conversation history:
{context}

Please provide a helpful response about forex trading. Keep it concise."""

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:3b-instruct-q4_K_M", "prompt": prompt, "stream": False},
            timeout=60
        )
        if response.status_code == 200:
            bot_response = response.json().get('response', '').strip()
        else:
            bot_response = "Error: Could not get response from AI"
    except Exception as e:
        bot_response = f"AI connection error: {str(e)}"
    
    chat_history.append({'type': 'chat', 'sender': 'Bot', 'message': bot_response})
    return jsonify({'response': bot_response})

@app.route('/start_monitor', methods=['POST'])
def start_monitor():
    try:
        # 更新config.json中的mode为monitor
        config_path = 'E:\\TradingSystem\\config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['mode'] = 'monitor'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 创建监控标志文件，通知autogpt_trading.py
            flag_path = 'E:\\TradingSystem\\start_monitor.flag'
            with open(flag_path, 'w', encoding='utf-8') as f:
                f.write(str(datetime.now().isoformat()))
            
            print(f"[WEB] 监控模式已启用 - {datetime.now()}")
            return jsonify({'ok': True, 'message': '监控模式已启动'})
        else:
            return jsonify({'error': 'config.json not found'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/stop_monitor', methods=['POST'])
def stop_monitor():
    try:
        # 更新config.json中的mode为discussion
        config_path = 'E:\\TradingSystem\\config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['mode'] = 'discussion'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 创建停止标志文件
            flag_path = 'E:\\TradingSystem\\stop_monitor.flag'
            with open(flag_path, 'w', encoding='utf-8') as f:
                f.write(str(datetime.now().isoformat()))
            
            print(f"[WEB] 监控模式已停止 - {datetime.now()}")
            return jsonify({'ok': True, 'message': '监控模式已停止'})
        else:
            return jsonify({'error': 'config.json not found'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/reload_config', methods=['POST'])
def reload_config():
    """Reload config from config.json and notify AutoGPT to reload"""
    try:
        config_path = 'E:\\TradingSystem\\config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 创建重新加载标志文件
            flag_path = 'E:\\TradingSystem\\reload_config.flag'
            with open(flag_path, 'w', encoding='utf-8') as f:
                f.write(str(datetime.now().isoformat()))
            
            print(f"[WEB] 配置已重新加载 - 交易品种: {config.get('trading_pair', 'N/A')}")
            return jsonify({'ok': True, 'message': f'配置已重新加载，交易品种: {config.get("trading_pair")}'})
        else:
            return jsonify({'error': 'config.json not found'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_logs')
def get_logs():
    return jsonify({'logs': chat_history[-50:]})

@app.route('/save_log', methods=['POST'])
def save_log():
    global chat_history
    data = request.json
    chat_history.append({'type': data.get('type', 'log'), 'message': data.get('message', ''), 'timestamp': datetime.now().isoformat()})
    # Note: Chat logs are now only stored in memory (chat_history) for the web interface
    # The actual log file (autogpt.log) is rotated to logs folder on exit
    # This prevents duplicate chat content in the logs folder
    return jsonify({'ok': True})

# 处理浏览器常见但未定义的资源请求
@app.route('/apple-touch-icon.png')
@app.route('/apple-touch-icon-precomposed.png')
@app.route('/robots.txt')
def handle_common_resources():
    return '', 204

if __name__ == '__main__':
    print("Starting on port 5000...")
    app.run(port=5000, debug=False)
