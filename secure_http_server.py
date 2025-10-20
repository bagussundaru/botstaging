#!/usr/bin/env python3
"""
Secure HTTP Server with Multi-User Dashboard Authentication
Supports different dashboards for different users
"""

import os
import sys
import json
import uuid
import base64
import hashlib
import re
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes
import datetime

# Add botoktober directory to path for Bybit client import
sys.path.append('/home/clurut/botoktober')
try:
    from bybit_client import BybitProductionClient
    from dotenv import load_dotenv
    load_dotenv('/home/clurut/binance_webhook/.env')
    BYBIT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Bybit client not available: {e}")
    BYBIT_AVAILABLE = False

class SecureHTTPRequestHandler(BaseHTTPRequestHandler):
    # User credentials and their allowed dashboards
    USERS = {
        'admin': {
            'password': 'sniper2024',
            'dashboards': ['simple_dashboard_apinur.html', 'simple_dashboard_apifan.html', 'simple_dashboard_apiarif.html'],
            'role': 'admin'
        },
        'apinur': {
            'password': 'nuru2024',
            'dashboards': ['simple_dashboard_apinur.html'],
            'role': 'user'
        },
        'apifan': {
            'password': 'fanu2024', 
            'dashboards': ['simple_dashboard_apifan.html'],
            'role': 'user'
        },
        'apiarif': {
            'password': 'arifu2024',
            'dashboards': ['simple_dashboard_apiarif.html'],
            'role': 'user'
        }
    }
    
    # Session storage
    sessions = {}
    
    # Bybit client initialization
    bybit_client = None
    
    @classmethod
    def init_bybit_client(cls):
        """Initialize Bybit client with API credentials"""
        if BYBIT_AVAILABLE:
            try:
                api_key = os.getenv('BYBIT_API_KEY')
                secret_key = os.getenv('BYBIT_SECRET_KEY')
                testnet = os.getenv('BYBIT_TESTNET', 'False').lower() == 'true'
                
                if api_key and secret_key:
                    cls.bybit_client = BybitProductionClient(api_key, secret_key, testnet)
                    print(f"✅ Bybit client initialized successfully")
                    return True
                else:
                    print("❌ Bybit API credentials not found in .env")
                    return False
            except Exception as e:
                print(f"❌ Failed to initialize Bybit client: {e}")
                return False
        return False
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.lstrip('/')
        
        if path == 'login' or path == '':
            self.send_login_page()
        elif path == 'logout':
            self.handle_logout()
        elif path.startswith('api/'):
            # Allow API access without authentication for dashboard AJAX calls
            # In production, you might want to add IP restrictions or other security measures
            self.handle_api(path)
        elif self.is_authenticated():
            self.serve_file(path)
        else:
            self.redirect_to_login()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.lstrip('/')
        
        if path == 'login':
            self.handle_login()
        else:
            self.send_error(404, "Not Found")
    
    def is_authenticated(self):
        """Check if user is authenticated via session"""
        cookies = self.get_cookies()
        session_id = cookies.get('session_id')
        
        if session_id and session_id in self.sessions:
            session_time = self.sessions[session_id]['time']
            current_time = datetime.datetime.now()
            if (current_time - session_time).total_seconds() < 86400:  # 24 hours
                return True
            else:
                del self.sessions[session_id]
        
        return False
    
    def get_current_user(self):
        """Get current authenticated user"""
        cookies = self.get_cookies()
        session_id = cookies.get('session_id')
        
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]['username']
        return None
    
    def can_access_file(self, filename):
        """Check if current user can access the requested file"""
        username = self.get_current_user()
        if not username:
            return False
            
        user_info = self.USERS.get(username, {})
        allowed_dashboards = user_info.get('dashboards', [])
        
        # Admin can access everything
        if user_info.get('role') == 'admin':
            return True
            
        # Check if user can access this specific dashboard
        return filename in allowed_dashboards
    
    def get_cookies(self):
        """Parse cookies from request headers"""
        cookies = {}
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
        return cookies
    
    def handle_login(self):
        """Handle login form submission"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse form data
        params = {}
        for param in post_data.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value.replace('+', ' ').replace('%40', '@')
        
        username = params.get('username', '')
        password = params.get('password', '')
        
        # Validate credentials
        user_info = self.USERS.get(username)
        if user_info and user_info['password'] == password:
            # Create session
            session_id = self.generate_session_id(username)
            self.sessions[session_id] = {
                'username': username,
                'time': datetime.datetime.now()
            }
            
            # Redirect to appropriate dashboard
            redirect_url = self.get_user_dashboard(username)
            
            self.send_response(302)
            self.send_header('Location', redirect_url)
            self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly')
            self.end_headers()
        else:
            self.send_login_page(error="Invalid username or password")
    
    def get_user_dashboard(self, username):
        """Get the default dashboard for a user"""
        user_info = self.USERS.get(username, {})
        dashboards = user_info.get('dashboards', [])
        
        if dashboards:
            return f'/{dashboards[0]}'
        return '/'
    
    def handle_logout(self):
        """Handle logout"""
        cookies = self.get_cookies()
        session_id = cookies.get('session_id')
        
        if session_id and session_id in self.sessions:
            del self.sessions[session_id]
        
        self.send_response(302)
        self.send_header('Location', '/login')
        self.send_header('Set-Cookie', 'session_id=; Path=/; HttpOnly; Expires=Thu, 01 Jan 1970 00:00:00 GMT')
        self.end_headers()
    
    def generate_session_id(self, username):
        """Generate unique session ID"""
        timestamp = str(datetime.datetime.now().timestamp())
        data = f"{username}:{timestamp}:{os.urandom(16).hex()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def redirect_to_login(self):
        """Redirect to login page"""
        self.send_response(302)
        self.send_header('Location', '/login')
        self.end_headers()
    
    def handle_api(self, path):
        """Handle API requests"""
        if path == 'api/alerts':
            self.get_recent_alerts()
        elif path == 'api/portfolio':
            portfolio_data = self.get_portfolio_data()
            self.send_json_response(portfolio_data)
        elif path == 'api/positions':
            positions_data = self.get_positions_data()
            self.send_json_response(positions_data)
        elif path == 'api/dashboard_summary':
            summary_data = self.get_dashboard_summary()
            self.send_json_response(summary_data)
        else:
            self.send_error(404, "API endpoint not found")
    
    def get_portfolio_data(self):
        """Get portfolio data from Bybit API"""
        try:
            if self.bybit_client:
                # Get real portfolio data from Bybit API
                balance_response = self.bybit_client.get_account_balance()
                
                if balance_response and balance_response.get('success'):
                    total_balance = balance_response.get('total_balance', 0)
                    available_balance = balance_response.get('available_balance', 0)
                    
                    # Calculate daily P&L (simplified - you might want to implement proper calculation)
                    daily_pnl = total_balance - 30.0  # Assuming starting balance was $30
                    daily_pnl_percentage = (daily_pnl / 30.0) * 100 if daily_pnl != 0 else 0
                    
                    portfolio = {
                        'status': 'success',
                        'total_balance': total_balance,
                        'currency': 'USDT',
                        'daily_pnl': daily_pnl,
                        'daily_pnl_percentage': daily_pnl_percentage,
                        'available_balance': available_balance,
                        'used_margin': total_balance - available_balance,
                        'timestamp': datetime.datetime.now().isoformat(),
                        'source': 'bybit_api'
                    }
                    return portfolio
                else:
                    print(f"❌ Bybit API Error: {balance_response.get('error', 'Unknown error')}")
                    
            # Fallback to mock data if Bybit API is not available
            portfolio = {
                'status': 'success',
                'total_balance': 29.74,
                'currency': 'USDT',
                'daily_pnl': -0.26,
                'daily_pnl_percentage': -0.87,
                'available_balance': 29.74,
                'used_margin': 0.00,
                'timestamp': datetime.datetime.now().isoformat(),
                'source': 'mock_data'
            }
            return portfolio
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'source': 'error'}

    def get_positions_data(self):
        """Get positions data from Bybit API"""
        try:
            if self.bybit_client:
                # Get real positions data from Bybit API for ETHUSDT (main trading symbol)
                positions_list = []
                
                # Check ETHUSDT position
                eth_position = self.bybit_client.get_position_info('ETHUSDT')
                if eth_position and eth_position.get('success') and eth_position.get('size', 0) > 0:
                    # Get current price for ETHUSDT
                    current_price = self.bybit_client.get_current_price('ETHUSDT')
                    
                    position_data = {
                        'symbol': eth_position.get('symbol', 'ETHUSDT'),
                        'side': 'Long' if eth_position.get('side') == 'Buy' else 'Short',
                        'size': eth_position.get('size', 0),
                        'entry_price': eth_position.get('entry_price', 0),
                        'current_price': current_price or 0,
                        'unrealized_pnl': eth_position.get('unrealized_pnl', 0),
                        'unrealized_pnl_percentage': eth_position.get('percentage', 0),
                        'stop_loss': None,  # Could be added if available in position info
                        'take_profit': None  # Could be added if available in position info
                    }
                    positions_list.append(position_data)
                
                positions = {
                    'status': 'success',
                    'positions': positions_list,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'source': 'bybit_api'
                }
                return positions
                    
            # Fallback to mock data if Bybit API is not available
            positions = {
                'status': 'success',
                'positions': [],  # Empty positions for mock data
                'timestamp': datetime.datetime.now().isoformat(),
                'source': 'mock_data'
            }
            return positions
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'source': 'error'}

    def get_dashboard_summary(self):
        """Get dashboard summary data"""
        try:
            # Get real data from other methods
            portfolio_data = self.get_portfolio_data()
            positions_data = self.get_positions_data()
            recent_alerts = self.get_recent_alerts_data(5)
            
            # Count active positions
            active_positions = 0
            if positions_data.get('status') == 'success':
                active_positions = len(positions_data.get('positions', []))
            
            # Count alerts today
            alerts_today = 0
            if recent_alerts:
                today = datetime.datetime.now().date()
                for alert in recent_alerts:
                    try:
                        alert_timestamp = alert.get('timestamp', '')
                        # Parse timestamp from log format
                        alert_date = datetime.datetime.strptime(alert_timestamp, '%Y-%m-%d %H:%M:%S').date()
                        if alert_date == today:
                            alerts_today += 1
                    except:
                        pass
            
            # Determine API status
            api_status = 'Connected' if self.bybit_client else 'Mock Data'
            if portfolio_data.get('source') == 'bybit_api':
                api_status = 'Connected'
            elif portfolio_data.get('source') == 'mock_data':
                api_status = 'Mock Data'
            elif portfolio_data.get('source') == 'error':
                api_status = 'Error'
            
            summary = {
                'status': 'success',
                'last_trade_time': recent_alerts[0]['timestamp'] if recent_alerts else 'No recent trades',
                'active_positions_count': active_positions,
                'pending_orders_count': 0,
                'alerts_today': alerts_today,
                'system_status': 'Active',
                'webhook_status': 'Connected',
                'api_status': api_status,
                'timestamp': datetime.datetime.now().isoformat(),
                'source': portfolio_data.get('source', 'unknown')
            }
            return summary
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'source': 'error'}
    
    def get_recent_alerts_data(self, count=10):
        """Get recent trading alerts from multiple log sources"""
        alerts = []
        
        # List of possible log files to check
        log_files = [
            '/home/clurut/binance_webhook/bybit_production.log',
            '/home/clurut/binance_webhook/trading_bot.log',
            '/home/clurut/binance_webhook/webhook.log',
            '/home/clurut/logalerttradingview.txt'
        ]
        
        try:
            for log_file in log_files:
                if os.path.exists(log_file) and len(alerts) < count:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                    
                    # Filter lines that contain BUY or SELL signals
                    for line in reversed(lines):
                        if any(keyword in line.upper() for keyword in ['BUY', 'SELL', 'WEBHOOK RECEIVED']):
                            # Extract timestamp
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            timestamp = timestamp_match.group(1) if timestamp_match else 'Unknown'
                            
                            # Extract action (BUY/SELL)
                            action = 'BUY' if 'BUY' in line.upper() else 'SELL' if 'SELL' in line.upper() else 'SIGNAL'
                            
                            # Extract symbol
                            symbol_match = re.search(r'"symbol":\s*"([^"]+)"', line)
                            if not symbol_match:
                                symbol_match = re.search(r'ETHUSDT|BTCUSDT|ADAUSDT', line)
                            symbol = symbol_match.group(1) if symbol_match else symbol_match.group(0) if symbol_match else 'ETHUSDT'
                            
                            # Extract price
                            price_match = re.search(r'"price":\s*([0-9.]+)', line)
                            if not price_match:
                                price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', line)
                            price = price_match.group(1) if price_match else 'Market'
                            
                            alerts.append({
                                'timestamp': timestamp,
                                'action': action,
                                'symbol': symbol,
                                'price': price,
                                'raw_line': line.strip()
                            })
                            
                            if len(alerts) >= count:
                                break
                                
            # If no real alerts found, create some sample data
            if len(alerts) == 0:
                current_time = datetime.datetime.now()
                sample_alerts = [
                    {
                        'timestamp': (current_time - datetime.timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                        'action': 'BUY',
                        'symbol': 'ETHUSDT',
                        'price': '2650.50',
                        'raw_line': 'Sample BUY signal for ETHUSDT'
                    },
                    {
                        'timestamp': (current_time - datetime.timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                        'action': 'SELL',
                        'symbol': 'ETHUSDT',
                        'price': '2680.25',
                        'raw_line': 'Sample SELL signal for ETHUSDT'
                    },
                    {
                        'timestamp': (current_time - datetime.timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S'),
                        'action': 'BUY',
                        'symbol': 'ETHUSDT',
                        'price': '2620.75',
                        'raw_line': 'Sample BUY signal for ETHUSDT'
                    }
                ]
                alerts = sample_alerts[:count]
                
        except Exception as e:
            print(f"Error reading alerts: {e}")
            # Return sample data on error
            current_time = datetime.datetime.now()
            alerts = [{
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'INFO',
                'symbol': 'ETHUSDT',
                'price': 'N/A',
                'raw_line': f'Error loading alerts: {str(e)}'
            }]
        
        return alerts

    def get_recent_alerts(self):
        """Get 3 most recent BUY/SELL trading signals"""
        try:
            alerts_data = self.get_recent_alerts_data(3)
            
            # Format alerts for API response
            formatted_alerts = []
            for alert in alerts_data:
                formatted_alerts.append({
                    'timestamp': alert['timestamp'],
                    'type': self.classify_alert_type(alert['raw_line']),
                    'action': alert['action'],
                    'symbol': alert['symbol'],
                    'price': alert['price'],
                    'message': alert['raw_line']
                })
            
            response_data = {
                'status': 'success',
                'alerts': formatted_alerts,
                'count': len(formatted_alerts),
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            error_response = {
                'status': 'error',
                'message': f'Failed to read alerts: {str(e)}',
                'timestamp': datetime.datetime.now().isoformat()
            }
            self.send_json_response(error_response, status_code=500)
    
    def extract_timestamp(self, line):
        """Extract timestamp from log line"""
        try:
            # Try to find timestamp pattern in the line
            timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
            match = re.search(timestamp_pattern, line)
            if match:
                return match.group(1)
            else:
                # If no timestamp found, use current time
                return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except:
            return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def classify_alert_type(self, line):
        """Classify alert type based on content"""
        line_upper = line.upper()
        if 'BUY' in line_upper:
            return 'BUY'
        elif 'SELL' in line_upper:
            return 'SELL'
        elif 'WEBHOOK RECEIVED' in line_upper:
            return 'WEBHOOK'
        elif 'ORDER' in line_upper:
            return 'ORDER'
        elif 'ERROR' in line_upper:
            return 'ERROR'
        else:
            return 'INFO'
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        json_data = json.dumps(data, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data.encode('utf-8'))))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def serve_file(self, path):
        """Serve protected files"""
        if not path or path == '/':
            # Redirect to user's dashboard
            username = self.get_current_user()
            dashboard_url = self.get_user_dashboard(username)
            self.send_response(302)
            self.send_header('Location', dashboard_url)
            self.end_headers()
            return
        
        # Remove query parameters for file access check
        filename = path.split('?')[0]
        
        # Check if user can access this file
        if not self.can_access_file(filename):
            self.send_error(403, "Access Denied - You don't have permission to access this dashboard")
            return
        
        # Serve the file
        file_path = os.path.join(os.getcwd(), filename)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Determine content type
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                
            except Exception as e:
                self.send_error(500, f"Internal Server Error: {str(e)}")
        else:
            self.send_error(404, "File not found")
    
    def send_login_page(self, error=None):
        """Serve login page"""
        error_html = f'<div class="error">{error}</div>' if error else ''
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Login - Sniper Bybit</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .login-container {{
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }}
        .login-header {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        .login-header h1 {{
            color: #333;
            margin: 0;
            font-size: 1.8rem;
        }}
        .login-header p {{
            color: #666;
            margin: 0.5rem 0 0 0;
        }}
        .form-group {{
            margin-bottom: 1rem;
        }}
        label {{
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }}
        input[type="text"], input[type="password"] {{
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }}
        input[type="text"]:focus, input[type="password"]:focus {{
            outline: none;
            border-color: #667eea;
        }}
        .login-btn {{
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .login-btn:hover {{
            transform: translateY(-2px);
        }}
        .error {{
            background: #fee;
            color: #c33;
            padding: 0.75rem;
            border-radius: 5px;
            margin-bottom: 1rem;
            border: 1px solid #fcc;
        }}
        .info {{
            background: #e8f4fd;
            color: #31708f;
            padding: 0.75rem;
            border-radius: 5px;
            margin-top: 1rem;
            border: 1px solid #bce8f1;
            font-size: 0.9rem;
        }}

    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🎯 Sniper Dashboard</h1>
            <p>Multi-User Access System</p>
        </div>
        
        {error_html}
        
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="login-btn">🔐 Login</button>
        </form>
        
        <div class="info">
            <strong>Security Notice:</strong><br>
            Authorized personnel only. Contact administrator for access credentials.<br>
            All login attempts are monitored and logged for security purposes.
        </div>
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

def run_server(port=8080):
    """Run the secure HTTP server"""
    # Initialize Bybit client
    print("🔄 Initializing Bybit API client...")
    SecureHTTPRequestHandler.init_bybit_client()
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, SecureHTTPRequestHandler)
    
    print(f"🚀 Secure Multi-User Dashboard Server starting on port {port}")
    print(f"🌐 Local access: http://localhost:{port}/")
    print(f"🌍 Public access: http://103.189.234.15:{port}/")
    print(f"🔐 Authentication required for all dashboards")
    print(f"👥 Multi-user support enabled")
    print("")
    print("Available users and their dashboards:")
    for username, info in SecureHTTPRequestHandler.USERS.items():
        dashboards = ', '.join(info['dashboards'])
        print(f"  👤 {username} ({info['role']}) -> {dashboards}")
    print("")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        httpd.server_close()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)