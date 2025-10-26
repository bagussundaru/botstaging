#!/usr/bin/env python3
"""
Dashboard untuk menampilkan hasil detailed API check Bybit
Port: 7000
Format: Card-based layout seperti e-commerce
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_cors import CORS
import json
import subprocess
import os
import re
from datetime import datetime, timedelta
import sys
import json
import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from detailed_api_check import DetailedBybitChecker
from focused_trading_analysis import FocusedTradingAnalyzer

app = Flask(__name__)
app.secret_key = os.getenv('DASHBOARD_SECRET_KEY', 'fallback-secret-key-2024')
CORS(app)  # Enable CORS for all routes

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class APIDashboard:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        
        # API credentials for both accounts
        self.api_details = {
            "apifan": {
                "api_key": "GpT4GPwOXzvW8nEqhx",
                "api_secret": "SCJpSe8YIsGoKvElxxIibeLrEUVtkgnPT2xD",
                "name": "APIFAN",
                "color": "#3498db"
            },
            "apiarif": {
                "api_key": "BHnZNnIFOPvAIFlFMl",
                "api_secret": "2lDPi5iT2wlyiJ0RB5uxGDIKZM54cJrCm2LL",
                "name": "APIARIF", 
                "color": "#e74c3c"
            }
        }
        
        # Log files untuk alerts
        self.log_files = {
            "webhook": "/home/clurut/binance_webhook/webhook.log",
            "app": "/home/clurut/binance_webhook/app.log", 
            "trades": "/home/clurut/binance_webhook/bybit_trades.log",
            "tradingview": "/home/clurut/logalerttradingview.txt"
        }
    
    def safe_float(self, value, default=0.0):
        """Safely convert value to float, handling empty strings and None"""
        if value is None or value == '' or value == 'None':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def generate_signature(self, api_secret, timestamp, api_key, recv_window, params_str):
        """Generate signature untuk autentikasi Bybit V5 API"""
        param_str = f"{timestamp}{api_key}{recv_window}{params_str}"
        return hmac.new(
            api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def make_direct_request(self, credentials, endpoint, params=None):
        """Membuat request langsung ke Bybit API dengan autentikasi"""
        if params is None:
            params = {}
            
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        api_key = credentials['api_key']
        
        sorted_params = sorted(params.items())
        params_str = urlencode(sorted_params)
        
        signature = self.generate_signature(
            credentials['api_secret'], 
            timestamp, 
            api_key, 
            recv_window, 
            params_str
        )
        
        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window,
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        if params_str:
            url += f"?{params_str}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
             return {"error": str(e), "retCode": -1}
    
    def get_direct_positions(self, account_key):
        """Mengambil posisi langsung dari Bybit API"""
        credentials = self.api_details[account_key]
        
        # Get positions
        positions_response = self.make_direct_request(
            credentials, 
            "/v5/position/list",
            {"category": "linear", "settleCoin": "USDT"}
        )
        
        positions = []
        if positions_response.get("retCode") == 0:
            for pos in positions_response.get("result", {}).get("list", []):
                size = self.safe_float(pos.get("size", "0"))
                if size > 0:  # Only active positions
                    # Format field names to match what format_positions_data expects
                    tp_value = pos.get("takeProfit", "0")
                    sl_value = pos.get("stopLoss", "0")
                    
                    positions.append({
                        "symbol": pos.get("symbol", ""),
                        "side": pos.get("side", ""),
                        "size": size,
                        "entry_price": self.safe_float(pos.get("avgPrice", "0")),
                        "mark_price": self.safe_float(pos.get("markPrice", "0")),
                        "unrealized_pnl": self.safe_float(pos.get("unrealisedPnl", "0")),
                        "leverage": pos.get("leverage", "1"),
                        "stop_loss": sl_value if sl_value and sl_value != "0" else "None",
                        "take_profit": tp_value if tp_value and tp_value != "0" else "None"
                    })
        
        return positions
    
    def read_alert_logs(self, hours_back=24):
        """Membaca alert signals dari log files dengan detail eksekusi"""
        alerts = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Update log files untuk include bybit_production.log
        production_log = "/home/clurut/binance_webhook/bybit_production.log"
        
        # Pattern untuk mencari alerts di log dengan detail eksekusi
        patterns = {
            "webhook_received": r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - INFO - 📨 Webhook received: \{'action': '(BUY|SELL)', 'symbol': '([^']+)', 'price': ([^,]+), 'token': '([^']+)'\}",
            "processing_signal": r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - INFO - 📊 Processing TradingView signal: \{'action': '(BUY|SELL)', 'symbol': '([^']+)', 'price': ([^,]+), 'token': '([^']+)'\}",
            "trade_executed": r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - INFO - 🎯 TRADE EXECUTED SUCCESSFULLY!",
            "trade_failed": r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - ERROR - ❌ Trade execution failed: (.+)",
            "position_info": r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - INFO - 💰 Position: ([0-9.]+) \| Entry: \$([0-9.]+)",
            "sl_tp_info": r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - INFO - 🛑 SL: \$([0-9.]+) \| 🎯 TP: \$([0-9.]+)",
            "invalid_token": r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - WARNING - ⚠️ Invalid authentication token: (.+)",
            "tradingview": r".*?order (buy|sell) @ [\d.]+.*?ETHUSDT.*?(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"
        }
        
        # Baca bybit_production.log
        if os.path.exists(production_log):
            try:
                with open(production_log, 'r') as f:
                    lines = f.readlines()
                    
                # Group related log entries with better tracking
                alert_tracking = {}  # Track alerts by timestamp for better matching
                
                for line in lines[-2000:]:  # Check last 2000 lines
                    for pattern_type, pattern in patterns.items():
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            try:
                                if pattern_type == "tradingview":
                                    # TradingView format
                                    timestamp_str = match.group(2)
                                    log_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
                                    action = match.group(1).upper()
                                    
                                    if log_time >= cutoff_time:
                                        alerts.append({
                                            "timestamp": log_time.strftime("%Y-%m-%d %H:%M:%S"),
                                            "type": "tradingview",
                                            "action": action,
                                            "symbol": "ETHUSDT",
                                            "status": "received",
                                            "message": line.strip(),
                                            "details": {}
                                        })
                                        
                                elif pattern_type == "webhook_received":
                                    timestamp_str = match.group(1)
                                    log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                    symbol = match.group(3)
                                    
                                    # Filter hanya ETHUSDT perpetual (ETHUSDT, ETHUSDT.P, ETHUSDT-PERP)
                                    if log_time >= cutoff_time and symbol.upper().startswith('ETHUSDT'):
                                        alert_key = f"{timestamp_str}_{match.group(2)}_{symbol}"
                                        new_alert = {
                                            "timestamp": log_time.strftime("%Y-%m-%d %H:%M:%S"),
                                            "type": "webhook",
                                            "action": match.group(2),
                                            "symbol": symbol,
                                            "price": float(match.group(4)),
                                            "token": match.group(5),
                                            "status": "received",
                                            "message": line.strip(),
                                            "details": {}
                                        }
                                        alerts.append(new_alert)
                                        alert_tracking[alert_key] = new_alert
                                        
                                elif pattern_type == "processing_signal":
                                    timestamp_str = match.group(1)
                                    action = match.group(2)
                                    symbol = match.group(3)
                                    alert_key = f"{timestamp_str}_{action}_{symbol}"
                                    
                                    if alert_key in alert_tracking:
                                        alert_tracking[alert_key]["status"] = "processing"
                                    
                                elif pattern_type == "trade_executed":
                                    timestamp_str = match.group(1)
                                    # Find the most recent alert within 5 minutes
                                    log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                    
                                    for alert in reversed(alerts):
                                        if alert["type"] == "webhook":
                                            alert_time = datetime.strptime(alert["timestamp"], "%Y-%m-%d %H:%M:%S")
                                            time_diff = (log_time - alert_time).total_seconds()
                                            if 0 <= time_diff <= 300:  # Within 5 minutes
                                                alert["status"] = "executed"
                                                alert["details"]["execution"] = "SUCCESS"
                                                break
                                    
                                elif pattern_type == "trade_failed":
                                    timestamp_str = match.group(1)
                                    error_msg = match.group(2)
                                    log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                    
                                    for alert in reversed(alerts):
                                        if alert["type"] == "webhook":
                                            alert_time = datetime.strptime(alert["timestamp"], "%Y-%m-%d %H:%M:%S")
                                            time_diff = (log_time - alert_time).total_seconds()
                                            if 0 <= time_diff <= 300:  # Within 5 minutes
                                                alert["status"] = "failed"
                                                alert["details"]["error"] = error_msg
                                                break
                                    
                                elif pattern_type == "position_info":
                                    timestamp_str = match.group(1)
                                    position_size = float(match.group(2))
                                    entry_price = float(match.group(3))
                                    log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                    
                                    for alert in reversed(alerts):
                                        if alert["type"] == "webhook":
                                            alert_time = datetime.strptime(alert["timestamp"], "%Y-%m-%d %H:%M:%S")
                                            time_diff = (log_time - alert_time).total_seconds()
                                            if 0 <= time_diff <= 300:  # Within 5 minutes
                                                alert["details"]["position_size"] = position_size
                                                alert["details"]["entry_price"] = entry_price
                                                break
                                    
                                elif pattern_type == "sl_tp_info":
                                    timestamp_str = match.group(1)
                                    stop_loss = float(match.group(2))
                                    take_profit = float(match.group(3))
                                    log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                    
                                    for alert in reversed(alerts):
                                        if alert["type"] == "webhook":
                                            alert_time = datetime.strptime(alert["timestamp"], "%Y-%m-%d %H:%M:%S")
                                            time_diff = (log_time - alert_time).total_seconds()
                                            if 0 <= time_diff <= 300:  # Within 5 minutes
                                                alert["details"]["stop_loss"] = stop_loss
                                                alert["details"]["take_profit"] = take_profit
                                                break
                                    
                                elif pattern_type == "invalid_token":
                                    timestamp_str = match.group(1)
                                    log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                    
                                    if log_time >= cutoff_time:
                                        alerts.append({
                                            "timestamp": log_time.strftime("%Y-%m-%d %H:%M:%S"),
                                            "type": "error",
                                            "action": "INVALID_TOKEN",
                                            "status": "rejected",
                                            "message": line.strip(),
                                            "details": {"invalid_token": match.group(2)}
                                        })
                                        
                            except (ValueError, IndexError) as e:
                                continue
                                
            except Exception as e:
                print(f"Error reading production log: {e}")
        
        # Baca log TradingView lama juga
        for log_type, log_file in self.log_files.items():
            if log_type == "tradingview" and os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        
                    for line in lines[-500:]:
                        match = re.search(patterns["tradingview"], line, re.IGNORECASE)
                        if match:
                            try:
                                timestamp_str = match.group(2)
                                log_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
                                action = match.group(1).upper()
                                
                                if log_time >= cutoff_time:
                                    alerts.append({
                                        "timestamp": log_time.strftime("%Y-%m-%d %H:%M:%S"),
                                        "type": "tradingview_legacy",
                                        "action": action,
                                        "symbol": "ETHUSDT",
                                        "status": "received",
                                        "message": line.strip(),
                                        "details": {}
                                    })
                            except ValueError:
                                continue
                except Exception as e:
                    continue
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        return alerts
    
    def get_api_data(self):
        """Get fresh API data from both accounts with direct API calls"""
        results = {}
        
        for account_id, credentials in self.api_details.items():
            try:
                # Get wallet balance
                wallet_response = self.make_direct_request(
                    credentials, 
                    "/v5/account/wallet-balance",
                    {"accountType": "UNIFIED"}
                )
                
                # Get positions (direct API call)
                positions = self.get_direct_positions(account_id)
                
                # Get recent trades
                trades_response = self.make_direct_request(
                    credentials,
                    "/v5/execution/list",
                    {"category": "linear", "limit": "20"}
                )
                
                # Get orders
                orders_response = self.make_direct_request(
                    credentials,
                    "/v5/order/history",
                    {"category": "linear", "limit": "20"}
                )
                
                results[account_id] = {
                    "name": credentials["name"],
                    "color": credentials["color"],
                    "wallet": wallet_response,
                    "positions": positions,
                    "orders": orders_response,
                    "trades": trades_response,
                    "status": "success",
                    "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
            except Exception as e:
                results[account_id] = {
                    "name": credentials["name"],
                    "color": credentials["color"],
                    "error": str(e),
                    "status": "error",
                    "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return results
    
    def format_wallet_data(self, wallet_result):
        """Format wallet data for display"""
        if wallet_result.get("retCode") != 0:
            return None
            
        # Handle direct API response format
        if "result" in wallet_result and "list" in wallet_result["result"]:
            wallet_data = wallet_result["result"]["list"][0]
        else:
            return None
        
        # Get USDT coin data
        usdt_data = None
        for coin in wallet_data.get('coin', []):
            if coin['coin'] == 'USDT':
                usdt_data = coin
                break
        
        return {
            "total_equity": self.safe_float(wallet_data.get('totalEquity', 0)),
            "total_balance": self.safe_float(wallet_data.get('totalWalletBalance', 0)),
            "available_balance": self.safe_float(wallet_data.get('totalAvailableBalance', 0)),
            "margin_balance": self.safe_float(wallet_data.get('totalMarginBalance', 0)),
            "unrealized_pnl": self.safe_float(wallet_data.get('totalPerpUPL', 0)),
            "usdt_balance": self.safe_float(usdt_data.get('walletBalance', 0)) if usdt_data else 0,
            "usdt_available": self.safe_float(usdt_data.get('availableToWithdraw', 0)) if usdt_data else 0
        }
    
    def format_positions_data(self, positions_data):
        """Format positions data for display"""
        # positions_data is already formatted from get_direct_positions
        if isinstance(positions_data, list):
            return positions_data
            
        # Fallback for old format
        if positions_data.get("retCode") != 0:
            return []
            
        positions = positions_data["result"]["list"]
        active_positions = []
        
        for pos in positions:
            if self.safe_float(pos.get('size', 0)) > 0:
                active_positions.append({
                    "symbol": pos.get('symbol', 'N/A'),
                    "side": pos.get('side', 'N/A'),
                    "size": self.safe_float(pos.get('size', 0)),
                    "entry_price": self.safe_float(pos.get('avgPrice', 0)),
                    "mark_price": self.safe_float(pos.get('markPrice', 0)),
                    "unrealized_pnl": self.safe_float(pos.get('unrealisedPnl', 0)),
                    "leverage": pos.get('leverage', '0'),
                    "stop_loss": pos.get('stopLoss', 'None'),
                    "take_profit": pos.get('takeProfit', 'None')
                })
        
        return active_positions
    
    def format_orders_data(self, orders_result, limit=5):
        """Format recent orders data for display"""
        if orders_result.get("retCode") != 0:
            return []
            
        orders = orders_result["result"]["list"]
        formatted_orders = []
        
        for order in orders[:limit]:
            created_time = datetime.fromtimestamp(int(order['createdTime'])/1000)
            formatted_orders.append({
                "symbol": order.get('symbol', 'N/A'),
                "side": order.get('side', 'N/A'),
                "qty": self.safe_float(order.get('qty', 0)),
                "price": self.safe_float(order.get('price', 0)),
                "status": order.get('orderStatus', 'N/A'),
                "time": created_time.strftime('%Y-%m-%d %H:%M:%S'),
                "time_ago": self.time_ago(created_time)
            })
        
        return formatted_orders
    
    def format_trades_data(self, trades_result, limit=5):
        """Format recent trades data for display"""
        if trades_result.get("retCode") != 0:
            return []
            
        trades = trades_result["result"]["list"]
        formatted_trades = []
        
        for trade in trades[:limit]:
            exec_time = datetime.fromtimestamp(int(trade['execTime'])/1000)
            formatted_trades.append({
                "symbol": trade.get('symbol', 'N/A'),
                "side": trade.get('side', 'N/A'),
                "qty": self.safe_float(trade.get('execQty', 0)),
                "price": self.safe_float(trade.get('execPrice', 0)),
                "value": self.safe_float(trade.get('execValue', 0)),
                "fee": self.safe_float(trade.get('execFee', 0)),
                "time": exec_time.strftime('%Y-%m-%d %H:%M:%S'),
                "time_ago": self.time_ago(exec_time)
            })
        
        return formatted_trades
    
    def time_ago(self, past_time):
        """Calculate time ago string"""
        now = datetime.now()
        diff = now - past_time
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
    
    def get_trading_analysis(self):
        """Get focused trading analysis data"""
        try:
            # Check if focused trading report exists
            report_file = '/home/clurut/binance_webhook/focused_trading_report.json'
            if os.path.exists(report_file):
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                return report_data
            else:
                # Generate new analysis if file doesn't exist
                analyzer = FocusedTradingAnalyzer()
                return analyzer.generate_focused_report()
        except Exception as e:
            return {"error": str(e)}
    
    def emergency_close_all_positions(self):
        """Emergency close all positions for all accounts"""
        try:
            # Import here to avoid circular imports
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from bybit_client import BybitProductionClient
            from bybit_config import BybitProductionConfig
            
            # Account configurations
            accounts = [
                {
                    'name': 'APIFAN',
                    'api_key': os.getenv('BYBIT_API_KEY_APIFAN'),
                    'secret_key': os.getenv('BYBIT_SECRET_KEY_APIFAN')
                },
                {
                    'name': 'APIARIF', 
                    'api_key': os.getenv('BYBIT_API_KEY_APIARIF'),
                    'secret_key': os.getenv('BYBIT_SECRET_KEY_APIARIF')
                }
            ]
            
            symbol = BybitProductionConfig.TARGET_SYMBOL
            results = []
            
            for account in accounts:
                name = account['name']
                api_key = account['api_key']
                secret_key = account['secret_key']
                
                if not api_key or not secret_key:
                    results.append({'account': name, 'success': False, 'error': 'Missing API credentials'})
                    continue
                    
                try:
                    # Initialize client
                    client = BybitProductionClient(api_key, secret_key, testnet=False)
                    
                    # Get current position
                    position_info = client.get_position_info(symbol)
                    
                    if not position_info.get('success'):
                        results.append({'account': name, 'success': False, 'error': 'Failed to get position info'})
                        continue
                    
                    position_size = position_info.get('size', 0)
                    
                    if position_size == 0:
                        results.append({'account': name, 'success': True, 'action': 'no_position'})
                        continue
                    
                    # Close position
                    close_result = client.close_position(symbol)
                    
                    if close_result.get('success'):
                        results.append({
                            'account': name, 
                            'success': True, 
                            'action': 'closed',
                            'order_id': close_result.get('order_id'),
                            'closed_size': position_size,
                            'closed_side': position_info.get('side', 'Unknown')
                        })
                    else:
                        results.append({'account': name, 'success': False, 'error': close_result.get('error', 'Unknown error')})
                        
                except Exception as e:
                    results.append({'account': name, 'success': False, 'error': str(e)})
            
            # Calculate summary
            successful_closes = len([r for r in results if r['success'] and r.get('action') == 'closed'])
            no_positions = len([r for r in results if r['success'] and r.get('action') == 'no_position'])
            failed_closes = len([r for r in results if not r['success']])
            
            return {
                'success': failed_closes == 0,
                'results': results,
                'summary': {
                    'successful_closes': successful_closes,
                    'no_positions': no_positions,
                    'failed_closes': failed_closes,
                    'total_accounts': len(accounts)
                },
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

dashboard = APIDashboard()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check credentials
        if (username == os.getenv('DASHBOARD_USERNAME') and 
            password == os.getenv('DASHBOARD_PASSWORD')):
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/emergency-close', methods=['POST'])
@login_required
def emergency_close():
    """Emergency close all positions endpoint"""
    try:
        result = dashboard.emergency_close_all_positions()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/api/data')
@login_required
def api_data():
    """API endpoint to get fresh data"""
    try:
        raw_data = dashboard.get_api_data()
        formatted_data = {}
        
        for account_id, data in raw_data.items():
            if data["status"] == "success":
                formatted_data[account_id] = {
                    "name": data["name"],
                    "color": data["color"],
                    "status": "success",
                    "last_update": data["last_update"],
                    "wallet": dashboard.format_wallet_data(data["wallet"]),
                    "positions": dashboard.format_positions_data(data["positions"]),
                    "orders": dashboard.format_orders_data(data["orders"]),
                    "trades": dashboard.format_trades_data(data["trades"])
                }
            else:
                formatted_data[account_id] = {
                    "name": data["name"],
                    "color": data["color"],
                    "status": "error",
                    "error": data["error"],
                    "last_update": data["last_update"]
                }
        
        return jsonify(formatted_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/trading-analysis')
@login_required
def trading_analysis():
    """API endpoint to get focused trading analysis"""
    try:
        analysis_data = dashboard.get_trading_analysis()
        return jsonify(analysis_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/multi-account-summary')
@login_required
def multi_account_summary():
    """API endpoint untuk data gabungan multi-akun dengan perbandingan konsistensi"""
    try:
        raw_data = dashboard.get_api_data()
        
        # Initialize summary data
        summary = {
            "accounts": {},
            "combined_summary": {
                "total_equity": 0,
                "total_balance": 0,
                "total_unrealized_pnl": 0,
                "total_positions": 0,
                "active_symbols": set()
            },
            "consistency_check": {
                "positions_match": True,
                "entry_prices_match": True,
                "tp_sl_active": True,
                "details": []
            },
            "trading_stats": {
                "daily_trades": 0,
                "total_volume": 0,
                "win_rate": 0
            },
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "success": True
        }
        
        positions_by_symbol = {}
        
        # Process each account
        for account_id, data in raw_data.items():
            if data["status"] == "success":
                wallet = dashboard.format_wallet_data(data["wallet"])
                positions = dashboard.format_positions_data(data["positions"])
                orders = dashboard.format_orders_data(data["orders"])
                trades = dashboard.format_trades_data(data["trades"])
                
                # Add to summary
                if wallet:
                    summary["combined_summary"]["total_equity"] += wallet["total_equity"]
                    summary["combined_summary"]["total_balance"] += wallet["total_balance"]
                    summary["combined_summary"]["total_unrealized_pnl"] += wallet["unrealized_pnl"]
                
                summary["combined_summary"]["total_positions"] += len(positions)
                
                # Track positions by symbol for consistency check
                for pos in positions:
                    symbol = pos["symbol"]
                    summary["combined_summary"]["active_symbols"].add(symbol)
                    
                    if symbol not in positions_by_symbol:
                        positions_by_symbol[symbol] = []
                    positions_by_symbol[symbol].append({
                        "account": account_id,
                        "position": pos
                    })
                
                # Format account data
                summary["accounts"][account_id] = {
                    "name": data["name"],
                    "color": data["color"],
                    "status": "success",
                    "wallet": wallet,
                    "positions": positions,
                    "recent_orders": orders,
                    "recent_trades": trades,
                    "last_update": data["last_update"]
                }
                
                # Add to trading stats
                summary["trading_stats"]["daily_trades"] += len(trades)
                for trade in trades:
                    summary["trading_stats"]["total_volume"] += trade["value"]
            
            else:
                summary["accounts"][account_id] = {
                    "name": data["name"],
                    "color": data["color"],
                    "status": "error",
                    "error": data["error"],
                    "last_update": data["last_update"]
                }
        
        # Convert set to list for JSON serialization
        summary["combined_summary"]["active_symbols"] = list(summary["combined_summary"]["active_symbols"])
        
        # Consistency checks
        for symbol, symbol_positions in positions_by_symbol.items():
            if len(symbol_positions) > 1:
                # Check if entry prices match
                entry_prices = [pos["position"]["entry_price"] for pos in symbol_positions]
                sides = [pos["position"]["side"] for pos in symbol_positions]
                sizes = [pos["position"]["size"] for pos in symbol_positions]
                
                entry_price_match = len(set(entry_prices)) <= 1
                side_match = len(set(sides)) <= 1
                size_match = len(set(sizes)) <= 1
                
                # Check TP/SL
                tp_sl_active = all(
                    pos["position"]["stop_loss"] != "None" and pos["position"]["take_profit"] != "None"
                    for pos in symbol_positions
                )
                
                summary["consistency_check"]["details"].append({
                    "symbol": symbol,
                    "entry_price_match": entry_price_match,
                    "side_match": side_match,
                    "size_match": size_match,
                    "tp_sl_active": tp_sl_active,
                    "accounts": [pos["account"] for pos in symbol_positions]
                })
                
                if not entry_price_match:
                    summary["consistency_check"]["entry_prices_match"] = False
                if not tp_sl_active:
                    summary["consistency_check"]["tp_sl_active"] = False
        
        return jsonify(summary)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/api/alerts')
def get_alerts():
    """API endpoint untuk mendapatkan alert signals dari log"""
    try:
        dashboard = APIDashboard()
        alerts = dashboard.read_alert_logs(hours=24)
        
        return jsonify({
            "success": True,
            "alerts": alerts,
            "total_alerts": len(alerts),
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/api/alert-history')
def get_alert_history():
    """API endpoint untuk mendapatkan alert history dengan detail eksekusi"""
    try:
        hours = request.args.get('hours', 24, type=int)
        status_filter = request.args.get('status', None)  # executed, failed, received, processing
        action_filter = request.args.get('action', None)  # BUY, SELL
        
        dashboard = APIDashboard()
        alerts = dashboard.read_alert_logs(hours_back=hours)
        
        # Filter berdasarkan status jika diminta
        if status_filter:
            alerts = [alert for alert in alerts if alert.get('status') == status_filter]
            
        # Filter berdasarkan action jika diminta
        if action_filter:
            alerts = [alert for alert in alerts if alert.get('action', '').upper() == action_filter.upper()]
        
        # Statistik
        stats = {
            "total_alerts": len(alerts),
            "executed": len([a for a in alerts if a.get('status') == 'executed']),
            "failed": len([a for a in alerts if a.get('status') == 'failed']),
            "received": len([a for a in alerts if a.get('status') == 'received']),
            "processing": len([a for a in alerts if a.get('status') == 'processing']),
            "rejected": len([a for a in alerts if a.get('status') == 'rejected']),
            "buy_signals": len([a for a in alerts if a.get('action') == 'BUY']),
            "sell_signals": len([a for a in alerts if a.get('action') == 'SELL']),
            "success_rate": 0
        }
        
        if stats["total_alerts"] > 0:
            stats["success_rate"] = round((stats["executed"] / stats["total_alerts"]) * 100, 2)
        
        return jsonify({
            "success": True,
            "alerts": alerts[:100],  # Limit to 100 most recent
            "statistics": stats,
            "filters": {
                "hours": hours,
                "status": status_filter,
                "action": action_filter
            },
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/alerts')
def alerts_view():
    """Route untuk tampilan alert history"""
    return render_template('alerts_view.html')

@app.route('/multi')
def multi_account_view():
    """Route untuk tampilan multi-akun"""
    return render_template('multi_account_view.html')

@app.route('/api/trading-period-summary')
@login_required
def trading_period_summary():
    """API endpoint untuk ringkasan periode trading"""
    try:
        dashboard = APIDashboard()
        
        # Get alert history for period analysis
        alerts = dashboard.read_alert_logs(hours_back=48)  # 2 hari data
        
        # Get multi-account summary
        multi_data = dashboard.get_api_data()
        
        # Calculate period dates (last 2 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        
        # Process alerts for period summary
        period_alerts = [alert for alert in alerts if alert.get('timestamp')]
        
        # Calculate statistics
        total_signals = len(period_alerts)
        executed_signals = len([a for a in period_alerts if a.get('status') == 'executed'])
        
        # Get trading status from multi-account data
        trading_active = False
        total_positions = 0
        
        for account_id, data in multi_data.items():
            if data.get("status") == "success":
                positions = data.get("positions", [])
                if positions:
                    trading_active = True
                    total_positions += len(positions)
        
        summary = {
            "success": True,
            "period": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "duration_hours": 48,
                "display_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            },
            "signals": {
                "total_signals": total_signals,
                "executed_signals": executed_signals,
                "success_rate": round((executed_signals / total_signals * 100) if total_signals > 0 else 0, 1)
            },
            "trading_status": {
                "is_active": trading_active,
                "active_positions": total_positions,
                "status_text": "Trading Aktif" if trading_active else "Tidak Ada Posisi Aktif",
                "execution_status": "Status Eksekusi Real"
            },
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/trading-period')
@login_required
def trading_period_view():
    """Route untuk tampilan ringkasan periode trading"""
    return render_template('trading_period_summary.html')

if __name__ == '__main__':
    print("🚀 Starting API Dashboard on port 7000...")
    print("📊 Dashboard URL: http://localhost:7000")
    app.run(host='0.0.0.0', port=7000, debug=True)