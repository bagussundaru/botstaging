#!/usr/bin/env python3
"""
🎯 MONITORING DASHBOARD - APIFAN
Dashboard ringan untuk monitoring akun apifan di port 9001
Author: Sniper AI Trading Agent
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.bybit')

app = Flask(__name__)

# Bybit API Configuration untuk apifan
BYBIT_API_KEY = os.environ.get('BYBIT_API_KEY_APIFAN')
BYBIT_SECRET_KEY = os.environ.get('BYBIT_SECRET_KEY_APIFAN')
BYBIT_TESTNET = False

# Initialize Bybit client
session = HTTP(
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_SECRET_KEY,
    testnet=BYBIT_TESTNET
)

def get_account_data():
    """Ambil data akun dari Bybit API"""
    try:
        # Get wallet balance
        wallet_response = session.get_wallet_balance(accountType="UNIFIED")
        
        # Get positions
        positions_response = session.get_positions(category="linear", symbol="ETHUSDT")
        
        # Process wallet data
        wallet_data = wallet_response.get('result', {}).get('list', [])
        total_equity = 0
        available_balance = 0
        total_margin_balance = 0
        
        if wallet_data:
            coins = wallet_data[0].get('coin', [])
            for coin in coins:
                if coin.get('coin') == 'USDT':
                    total_equity = float(coin.get('equity', 0))
                    available_balance = float(coin.get('availableToWithdraw', 0))
                    total_margin_balance = float(coin.get('walletBalance', 0))
                    break
        
        # Process position data
        positions_data = positions_response.get('result', {}).get('list', [])
        open_positions = []
        total_unrealized_pnl = 0
        
        for position in positions_data:
            if float(position.get('size', 0)) != 0:
                unrealized_pnl = float(position.get('unrealisedPnl', 0))
                total_unrealized_pnl += unrealized_pnl
                
                open_positions.append({
                    'symbol': position.get('symbol'),
                    'side': position.get('side'),
                    'size': float(position.get('size', 0)),
                    'entry_price': float(position.get('avgPrice', 0)),
                    'mark_price': float(position.get('markPrice', 0)),
                    'unrealized_pnl': unrealized_pnl,
                    'pnl_percentage': float(position.get('unrealisedPnl', 0)) / float(position.get('positionValue', 1)) * 100 if float(position.get('positionValue', 0)) > 0 else 0
                })
        
        return {
            'success': True,
            'account_name': 'APIFAN',
            'modal_awal': 30.0,  # Asumsi modal awal
            'total_equity': total_equity,
            'available_balance': available_balance,
            'total_margin_balance': total_margin_balance,
            'margin_used': total_margin_balance - available_balance,
            'open_positions': open_positions,
            'total_unrealized_pnl': total_unrealized_pnl,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

# HTML Template untuk dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Monitor APIFAN - Port 9001</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff; 
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.1); 
            border-radius: 15px; 
            padding: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 20px;
        }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .stat-card { 
            background: rgba(255,255,255,0.15); 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card h3 { 
            font-size: 0.9em; 
            margin-bottom: 10px; 
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-card .value { 
            font-size: 1.8em; 
            font-weight: bold; 
            margin-bottom: 5px;
        }
        .positive { color: #4ade80; }
        .negative { color: #f87171; }
        .neutral { color: #fbbf24; }
        .positions-section { 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px;
        }
        .positions-section h2 { 
            margin-bottom: 15px; 
            color: #fbbf24;
            border-bottom: 1px solid rgba(255,255,255,0.2);
            padding-bottom: 10px;
        }
        .position-item { 
            background: rgba(255,255,255,0.1); 
            padding: 15px; 
            margin-bottom: 10px; 
            border-radius: 8px;
            border-left: 4px solid #4ade80;
        }
        .position-item.short { border-left-color: #f87171; }
        .position-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 10px; 
            margin-top: 10px;
        }
        .position-detail { 
            text-align: center; 
        }
        .position-detail .label { 
            font-size: 0.8em; 
            opacity: 0.7; 
            margin-bottom: 5px;
        }
        .position-detail .value { 
            font-weight: bold; 
        }
        .footer { 
            text-align: center; 
            margin-top: 20px; 
            opacity: 0.7;
            font-size: 0.9em;
        }
        .refresh-btn { 
            background: rgba(255,255,255,0.2); 
            border: none; 
            color: white; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 10px;
            transition: background 0.3s ease;
        }
        .refresh-btn:hover { background: rgba(255,255,255,0.3); }
        .error { 
            background: rgba(248, 113, 113, 0.2); 
            border: 1px solid #f87171; 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center;
        }
    </style>
    <script>
        function refreshData() {
            location.reload();
        }
        
        // Auto refresh setiap 30 detik
        setInterval(refreshData, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 MONITOR APIFAN</h1>
            <p>Real-time Trading Dashboard - Port 9001</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
        </div>
        
        {% if data.success %}
        <div class="stats-grid">
            <div class="stat-card">
                <h3>💰 Modal Awal</h3>
                <div class="value">${{ "%.2f"|format(data.modal_awal) }}</div>
            </div>
            <div class="stat-card">
                <h3>💎 Total Equity</h3>
                <div class="value">${{ "%.2f"|format(data.total_equity) }}</div>
            </div>
            <div class="stat-card">
                <h3>💵 Available Balance</h3>
                <div class="value">${{ "%.2f"|format(data.available_balance) }}</div>
            </div>
            <div class="stat-card">
                <h3>🔒 Margin Used</h3>
                <div class="value">${{ "%.2f"|format(data.margin_used) }}</div>
            </div>
            <div class="stat-card">
                <h3>📊 Unrealized PNL</h3>
                <div class="value {% if data.total_unrealized_pnl > 0 %}positive{% elif data.total_unrealized_pnl < 0 %}negative{% else %}neutral{% endif %}">
                    ${{ "%.2f"|format(data.total_unrealized_pnl) }}
                </div>
            </div>
        </div>
        
        <div class="positions-section">
            <h2>📈 Open Positions ({{ data.open_positions|length }})</h2>
            {% if data.open_positions %}
                {% for position in data.open_positions %}
                <div class="position-item {% if position.side == 'Sell' %}short{% endif %}">
                    <h4>{{ position.symbol }} - {{ position.side|upper }}</h4>
                    <div class="position-grid">
                        <div class="position-detail">
                            <div class="label">Size</div>
                            <div class="value">{{ "%.4f"|format(position.size) }}</div>
                        </div>
                        <div class="position-detail">
                            <div class="label">Entry Price</div>
                            <div class="value">${{ "%.2f"|format(position.entry_price) }}</div>
                        </div>
                        <div class="position-detail">
                            <div class="label">Mark Price</div>
                            <div class="value">${{ "%.2f"|format(position.mark_price) }}</div>
                        </div>
                        <div class="position-detail">
                            <div class="label">Unrealized PNL</div>
                            <div class="value {% if position.unrealized_pnl > 0 %}positive{% elif position.unrealized_pnl < 0 %}negative{% else %}neutral{% endif %}">
                                ${{ "%.2f"|format(position.unrealized_pnl) }}
                            </div>
                        </div>
                        <div class="position-detail">
                            <div class="label">PNL %</div>
                            <div class="value {% if position.pnl_percentage > 0 %}positive{% elif position.pnl_percentage < 0 %}negative{% else %}neutral{% endif %}">
                                {{ "%.2f"|format(position.pnl_percentage) }}%
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; opacity: 0.7; padding: 20px;">No open positions</p>
            {% endif %}
        </div>
        {% else %}
        <div class="error">
            <h3>❌ Error Loading Data</h3>
            <p>{{ data.error }}</p>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Last Updated: {{ data.last_updated }}</p>
            <p>🎯 Sniper Trading Bot - APIFAN Monitor</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard route"""
    data = get_account_data()
    return render_template_string(DASHBOARD_TEMPLATE, data=data)

@app.route('/api/data')
def api_data():
    """API endpoint untuk data JSON"""
    return jsonify(get_account_data())

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'account': 'apifan',
        'port': 9001,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🎯 Starting APIFAN Monitor on port 9001...")
    print(f"📊 API Key: {BYBIT_API_KEY[:8]}..." if BYBIT_API_KEY else "❌ No API Key")
    app.run(host='0.0.0.0', port=9001, debug=False)