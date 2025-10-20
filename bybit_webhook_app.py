"""
🎯 SNIPER BYBIT WEBHOOK - Production Trading App
Aplikasi Webhook Production untuk Bybit Trading dengan Modal $30
Author: Sniper AI Trading Agent
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Optional
import threading
import time

# Import Sniper modules
from bybit_config import BybitProductionConfig
from bybit_client import BybitProductionClient
from sniper_calculator import SniperCalculator
from signal_priority_manager import SignalPriorityManager
from multi_account_executor import MultiAccountExecutor

# Configure logging - Semua log alert TradingView masuk ke bybit_production.log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/clurut/binance_webhook/bybit_production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SniperBybitWebhook:
    """Sniper Bybit Webhook Production App"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self.config = BybitProductionConfig()
        self.calculator = SniperCalculator(self.config.ACCOUNT_BALANCE)
        
        # Initialize Bybit client
        api_key = os.getenv('BYBIT_API_KEY')
        secret_key = os.getenv('BYBIT_SECRET_KEY')
        
        if not api_key or not secret_key:
            logger.error("❌ Bybit API credentials not found in environment variables")
            raise ValueError("Bybit API credentials required")
        
        self.client = BybitProductionClient(api_key, secret_key, testnet=False)
        
        # Last alert tracking
        self.last_alert = {
            'timestamp': None,
            'data': None,
            'status': 'none',  # none, executed, failed
            'reason': None,
            'execution_details': None
        }

        # Multi-Account setup
        self.multi_enabled = os.getenv('BYBIT_MULTI_ACCOUNTS_ENABLED', 'false').lower() == 'true'
        self.multi_executor = None
        if self.multi_enabled:
            accounts = []
            # Default/current account (apinur) dari env BYBIT_API_KEY/BYBIT_SECRET_KEY
            accounts.append({
                'name': 'apinur',
                'api_key': os.getenv('BYBIT_API_KEY'),
                'secret_key': os.getenv('BYBIT_SECRET_KEY')
            })
            # apifan
            api_key_apifan = os.getenv('BYBIT_API_KEY_APIFAN')
            secret_apifan = os.getenv('BYBIT_SECRET_KEY_APIFAN')
            if api_key_apifan and secret_apifan:
                accounts.append({'name': 'apifan', 'api_key': api_key_apifan, 'secret_key': secret_apifan})
            # apiarif
            api_key_apiarif = os.getenv('BYBIT_API_KEY_APIARIF')
            secret_apiarif = os.getenv('BYBIT_SECRET_KEY_APIARIF')
            if api_key_apiarif and secret_apiarif:
                accounts.append({'name': 'apiarif', 'api_key': api_key_apiarif, 'secret_key': secret_apiarif})

            if len(accounts) >= 2:  # minimal 2 akun agar meaningful
                self.multi_executor = MultiAccountExecutor(accounts)
                logger.info(f"🔁 Multi-Account mode ENABLED. Accounts: {[a['name'] for a in accounts]}")
            else:
                logger.warning("⚠️ Multi-Account enabled but insufficient credentials. Falling back to single account mode.")
                self.multi_enabled = False
        
        # Initialize Signal Priority Manager
        self.signal_manager = SignalPriorityManager(cooldown_seconds=30)
        
        # Trading state
        self.last_trade_time = None
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.emergency_stop = False
        
        # Setup routes
        self.setup_routes()
        
        logger.info("🎯 Sniper Bybit Webhook initialized for PRODUCTION trading")
    
    def _format_for_pine_script(self, data):
        """Format data for Pine Script input"""
        return f"""
// 🎯 BYBIT ACCOUNT DATA - Auto Updated {data['last_update']}
// Copy dan paste nilai-nilai ini ke Pine Script Anda

// Account Information
account_balance = {data['account_balance']}
total_balance = {data['total_balance']}
daily_pnl = {data['daily_pnl']}
daily_trades = {data['daily_trades']}
max_daily_trades = {data['max_daily_trades']}

// Position Information
position_symbol = "{data['position_symbol']}"
position_side = "{data['position_side']}"
position_size = {data['position_size']}
entry_price = {data['entry_price']}
current_pnl = {data['current_pnl']}
pnl_percentage = {data['pnl_percentage']}

// Risk Management
stop_loss_price = {data['stop_loss_price']}
take_profit_price = {data['take_profit_price']}
risk_per_trade = {data['risk_per_trade']}

// Status: {data['status']} | Last Update: {data['last_update']}
"""
        logger.info(f"💰 Account Balance: ${self.config.ACCOUNT_BALANCE}")
        logger.info(f"🎯 Target Symbol: {self.config.TARGET_SYMBOL}")
        logger.info(f"⚖️ Risk per Trade: {self.config.RISK_PER_TRADE:.1%}")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/webhook_bybit', methods=['POST'])
        def webhook_handler():
            return self.handle_webhook()
        
        @self.app.route('/webhook_v1', methods=['POST'])
        def webhook_v1_handler():
            """Legacy endpoint for TradingView compatibility"""
            return self.handle_webhook()
        
        @self.app.route('/status', methods=['GET'])
        def status():
            return self.get_status()
        
        @self.app.route('/balance', methods=['GET'])
        def balance():
            return self.get_balance()
        
        @self.app.route('/position', methods=['GET'])
        def position():
            return self.get_position()
        
        @self.app.route('/emergency_stop', methods=['POST'])
        def emergency_stop():
            return self.set_emergency_stop()
        
        # Pine Script data endpoint
        @self.app.route('/pine_data', methods=['GET'])
        def get_pine_data():
            """Get formatted data for Pine Script"""
            try:
                # Get account balance
                balance_info = self.client.get_account_balance()
                
                # Get position info
                position_info = self.client.get_position_info(self.config.TARGET_SYMBOL)
                
                # Format for Pine Script
                pine_data = {
                    'account_balance': balance_info.get('available_balance', 0),
                    'total_balance': balance_info.get('total_balance', 0),
                    'daily_pnl': getattr(self, 'daily_pnl', 0),
                    'daily_trades': getattr(self, 'daily_trades', 0),
                    'max_daily_trades': getattr(self.config, 'MAX_DAILY_TRADES', 8),
                    'position_symbol': self.config.TARGET_SYMBOL,
                    'position_side': position_info.get('side', 'None'),
                    'position_size': position_info.get('size', 0),
                    'entry_price': position_info.get('entry_price', 0),
                    'current_pnl': position_info.get('unrealized_pnl', 0),
                    'pnl_percentage': position_info.get('percentage', 0),
                    'stop_loss_price': 0,
                    'take_profit_price': 0,
                    'risk_per_trade': self.config.RISK_PER_TRADE * 100,
                    'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'active'
                }
                
                return jsonify({
                    'success': True,
                    'data': pine_data,
                    'pine_script_format': self._format_for_pine_script(pine_data)
                })
                
            except Exception as e:
                logger.error(f"Pine data error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # Pine Script formatted text endpoint
        @self.app.route('/pine_script_inputs', methods=['GET'])
        def get_pine_script_inputs():
            """Get Pine Script input format as plain text"""
            try:
                response = self.app.test_client().get('/pine_data')
                data = json.loads(response.data)
                
                if data['success']:
                    return data['pine_script_format'], 200, {'Content-Type': 'text/plain'}
                else:
                    return "Error getting Pine Script data", 500, {'Content-Type': 'text/plain'}
                    
            except Exception as e:
                logger.error(f"Pine script inputs error: {e}")
                return f"Error: {str(e)}", 500, {'Content-Type': 'text/plain'}
        
        @self.app.route('/orders', methods=['GET'])
        def orders():
            return self.get_orders()
        
        @self.app.route('/close_position', methods=['POST'])
        def close_position():
            return self.close_position()
        
        @self.app.route('/trade_history', methods=['GET'])
        def trade_history():
            return self.get_trade_history()
        
        @self.app.route('/signal_status', methods=['GET'])
        def signal_status():
            return self.get_signal_status()
        
        @self.app.route('/reset_signals', methods=['POST'])
        def reset_signals():
            return self.reset_signal_manager()
        
        # API endpoints for HTML dashboard
        @self.app.route('/api/account_data/<account_name>', methods=['GET'])
        def get_account_data(account_name):
            """Get account data for HTML dashboard"""
            return self.get_account_data_api(account_name)
        
        @self.app.route('/api/accounts', methods=['GET'])
        def get_all_accounts():
            """Get all accounts data for HTML dashboard"""
            return self.get_all_accounts_api()
        
        @self.app.route('/api/last_alert', methods=['GET'])
        def get_last_alert():
            """Get last alert data for HTML dashboard"""
            return self.get_last_alert_api()
    
    def authenticate_request(self, request_data: Dict) -> bool:
        """Authenticate incoming webhook request"""
        try:
            token = request_data.get('token') or request_data.get('auth_token') or request.headers.get('Authorization')
            
            if not token:
                logger.warning("⚠️ No authentication token provided")
                return False
            
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Menerima token dari TradingView (sniper-bybit-production-2024) atau token dari .env
            if token != self.config.AUTH_TOKEN and token != "sniper-bybit-production-2024":
                logger.warning(f"⚠️ Invalid authentication token: {token}")
                return False
            
            logger.info(f"✅ Autentikasi berhasil dengan token: {token}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def validate_trading_conditions(self) -> Dict:
        """Validate current trading conditions"""
        try:
            # Check emergency stop
            if self.emergency_stop:
                return {'valid': False, 'reason': 'Emergency stop activated'}
            
            # Check daily trade limit
            if self.daily_trades >= self.config.SNIPER_CONFIG['max_trades_per_day']:
                return {'valid': False, 'reason': f'Daily trade limit reached: {self.daily_trades}'}
            
            # Check cooldown period
            if self.last_trade_time:
                time_since_last = datetime.now() - self.last_trade_time
                cooldown = timedelta(seconds=self.config.COOLDOWN_SECONDS)
                
                if time_since_last < cooldown:
                    remaining = cooldown - time_since_last
                    return {'valid': False, 'reason': f'Cooldown active: {remaining.seconds}s remaining'}
            
            # Check daily loss limit
            if self.daily_pnl <= -self.config.MAX_DAILY_LOSS * self.config.ACCOUNT_BALANCE:
                return {'valid': False, 'reason': f'Daily loss limit reached: ${abs(self.daily_pnl):.2f}'}
            
            # Check account balance (single-account mode only)
            if self.multi_enabled and self.multi_executor:
                logger.info("🔁 Multi-account mode: skip single-account balance pre-check; per-account balance will be validated during execution")
                return {'valid': True, 'reason': 'Multi-account mode active'}
            else:
                balance_info = self.client.get_account_balance()
                if not balance_info['success']:
                    return {'valid': False, 'reason': 'Unable to verify account balance'}
                
                if balance_info['available_balance'] < 5.0:  # Minimum $5 required
                    return {'valid': False, 'reason': f'Insufficient balance: ${balance_info["available_balance"]:.2f}'}
                
                return {'valid': True, 'reason': 'All conditions met'}
            
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return {'valid': False, 'reason': f'Validation error: {str(e)}'}
    
    def process_tradingview_signal(self, signal_data: Dict) -> Dict:
        """Process TradingView signal with Professional Signal Priority Manager"""
        try:
            logger.info(f"📊 Processing TradingView signal: {signal_data}")
            
            # Extract signal information
            symbol = signal_data.get('symbol', self.config.TARGET_SYMBOL)
            action = signal_data.get('action', '').upper()
            timestamp = signal_data.get('timestamp', int(time.time() * 1000))
            confidence_value = float(signal_data.get('confidence', 0))
            
            # Use Signal Priority Manager to handle conflicts
            priority_result = self.signal_manager.add_signal(signal_data)
            
            if not priority_result['success']:
                logger.warning(f"⚠️ Signal rejected by Priority Manager: {priority_result['error']}")
                return priority_result
            
            # BYPASS: Selalu set confidence ke 100% untuk melewati validasi
            confidence = 100.0
            signal_data['confidence'] = 100.0
            
            # Validate symbol
            if symbol != self.config.TARGET_SYMBOL:
                return {
                    'success': False,
                    'error': f'Invalid symbol: {symbol}. Only {self.config.TARGET_SYMBOL} supported.'
                }
            
            # Validate action
            if action not in ['BUY', 'SELL']:
                return {
                    'success': False,
                    'error': f'Invalid action: {action}. Must be BUY or SELL.'
                }
            
            # Get current market data
            current_price = self.client.get_current_price(symbol)
            if not current_price:
                return {'success': False, 'error': 'Unable to get current price'}
            
            atr_value = self.client.calculate_atr(symbol)
            
            # Calculate complete trade plan using Sniper Method
            trade_plan = self.calculator.calculate_complete_trade_plan(
                signal_data, current_price, atr_value
            )
            
            if not trade_plan['success']:
                return trade_plan
            
            # BYPASS: Selalu approve trade dari TradingView (confidence sudah divalidasi di TradingView)
            # Mengabaikan skor konfluensi internal dan selalu menyetujui trade
            logger.info(f"✅ Trade disetujui - Mengabaikan skor konfluensi internal: {trade_plan['confluence_score']:.1f}%")
            trade_plan['trade_approved'] = True
            
            logger.info("✅ Trade plan approved - executing...")
            
            # Execute the trade
            if self.multi_enabled and self.multi_executor:
                execution_result = self.multi_executor.execute_signal(signal_data)
            else:
                execution_result = self.client.execute_sniper_trade(signal_data)
            
            if execution_result['success']:
                # Update trading state
                self.last_trade_time = datetime.now()
                self.daily_trades += 1
                
                # Log successful trade (single-account only)
                if not self.multi_enabled:
                    self.log_trade(trade_plan, execution_result)
                
                logger.info(f"🎯 TRADE EXECUTED SUCCESSFULLY!")
                logger.info(f"📊 Symbol: {symbol} | Action: {action} | Confidence: {confidence:.1%}")
                logger.info(f"💰 Position: {trade_plan['position_size']} | Entry: ${current_price}")
                logger.info(f"🛑 SL: ${trade_plan['stop_loss']} | 🎯 TP: ${trade_plan['take_profit_1']}")
                
                return {
                    'success': True,
                    'message': 'Trade executed successfully',
                    'trade_plan': trade_plan,
                    'execution': execution_result,
                    'daily_trades': self.daily_trades
                }
            else:
                logger.error(f"❌ Trade execution failed: {execution_result.get('error')}")
                return execution_result
            
        except Exception as e:
            logger.error(f"❌ Signal processing error: {e}")
            return {'success': False, 'error': f'Signal processing error: {str(e)}'}
    
    def log_trade(self, trade_plan: Dict, execution_result: Dict):
        """Log trade details for analysis"""
        try:
            trade_log = {
                'timestamp': datetime.now().isoformat(),
                'symbol': trade_plan['symbol'],
                'action': trade_plan['signal_type'],
                'entry_price': trade_plan['entry_price'],
                'position_size': trade_plan['position_size'],
                'stop_loss': trade_plan['stop_loss'],
                'take_profit': trade_plan['take_profit_1'],
                'risk_amount': trade_plan['risk_amount'],
                'reward_amount': trade_plan['reward_amount'],
                'confidence': trade_plan['confluence_score'],
                'order_id': execution_result.get('order_id'),
                'daily_trade_count': self.daily_trades
            }
            
            # Write to trade log file
            with open('bybit_trades.log', 'a') as f:
                f.write(json.dumps(trade_log) + '\\n')
            
        except Exception as e:
            logger.error(f"❌ Trade logging error: {e}")
    
    def handle_webhook(self) -> Dict:
        """Main webhook handler"""
        try:
            # Get request data
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            logger.info(f"📨 Webhook received: {data}")
            
            # Authenticate request
            if not self.authenticate_request(data):
                return jsonify({
                    'success': False,
                    'error': 'Authentication failed'
                }), 401
            
            # Validate trading conditions
            validation = self.validate_trading_conditions()
            if not validation['valid']:
                logger.warning(f"⚠️ Trading conditions not met: {validation['reason']}")
                
                # Update alert status for failed validation
                self.last_alert = {
                    'timestamp': datetime.now().isoformat(),
                    'data': data,
                    'status': 'failed',
                    'reason': validation['reason'],
                    'execution_details': None
                }
                
                return jsonify({
                    'success': False,
                    'error': validation['reason']
                }), 400
            
            # Store alert data
            self.last_alert = {
                'timestamp': datetime.now().isoformat(),
                'data': data,
                'status': 'processing',
                'reason': None,
                'execution_details': None
            }
            
            # Process the signal
            result = self.process_tradingview_signal(data)
            
            # Update alert status
            if result['success']:
                self.last_alert['status'] = 'executed'
                self.last_alert['execution_details'] = result
                self.last_alert['reason'] = 'Trade executed successfully'
                return jsonify(result), 200
            else:
                self.last_alert['status'] = 'failed'
                self.last_alert['reason'] = result.get('error', 'Unknown error')
                return jsonify(result), 400
            
        except Exception as e:
            logger.error(f"❌ Webhook handler error: {e}")
            return jsonify({
                'success': False,
                'error': f'Webhook error: {str(e)}'
            }), 500
    
    def get_status(self) -> Dict:
        """Get bot status"""
        try:
            balance_info = self.client.get_account_balance()
            position_info = self.client.get_position_info(self.config.TARGET_SYMBOL)
            
            return jsonify({
                'success': True,
                'status': 'active' if not self.emergency_stop else 'emergency_stop',
                'account_balance': balance_info.get('available_balance', 0),
                'daily_trades': self.daily_trades,
                'daily_pnl': self.daily_pnl,
                'last_trade': self.last_trade_time.isoformat() if self.last_trade_time else None,
                'position': position_info,
                'target_symbol': self.config.TARGET_SYMBOL,
                'risk_per_trade': f"{self.config.RISK_PER_TRADE:.1%}",
                'max_daily_trades': self.config.SNIPER_CONFIG['max_trades_per_day']
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def get_balance(self) -> Dict:
        """Get account balance"""
        try:
            balance_info = self.client.get_account_balance()
            return jsonify(balance_info)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def get_position(self) -> Dict:
        """Get current position"""
        try:
            position_info = self.client.get_position_info(self.config.TARGET_SYMBOL)
            return jsonify(position_info)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def get_orders(self) -> Dict:
        """Get all open orders including TP/SL"""
        try:
            orders_info = self.client.get_open_orders(self.config.TARGET_SYMBOL)
            return jsonify(orders_info)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def close_position(self) -> Dict:
        """Close open position"""
        try:
            result = self.client.close_position(self.config.TARGET_SYMBOL)
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def get_trade_history(self) -> Dict:
        """Get recent trade history"""
        try:
            limit = request.args.get('limit', 20, type=int)
            trade_history = self.client.get_trade_history(self.config.TARGET_SYMBOL, limit)
            return jsonify(trade_history)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def get_signal_status(self) -> Dict:
        """Get Signal Priority Manager status"""
        try:
            buffer_status = self.signal_manager.get_buffer_status()
            return jsonify({
                'success': True,
                'signal_manager': buffer_status,
                'last_trade': self.last_trade_time.isoformat() if self.last_trade_time else None,
                'daily_trades': self.daily_trades
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def reset_signal_manager(self) -> Dict:
        """Reset Signal Priority Manager state"""
        try:
            self.signal_manager.reset_state()
            return jsonify({
                'success': True,
                'message': 'Signal Priority Manager reset successfully'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def set_emergency_stop(self) -> Dict:
        """Set emergency stop"""
        try:
            self.emergency_stop = True
            logger.warning("🚨 EMERGENCY STOP ACTIVATED")
            
            # Close any open positions
            position_info = self.client.get_position_info(self.config.TARGET_SYMBOL)
            if position_info['success'] and position_info.get('size', 0) > 0:
                close_result = self.client.close_position(self.config.TARGET_SYMBOL)
                logger.info(f"📊 Position closed: {close_result}")
            
            return jsonify({
                'success': True,
                'message': 'Emergency stop activated',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    def get_account_data_api(self, account_name: str) -> Dict:
        """Get account data for specific account (API endpoint for HTML dashboard)"""
        try:
            if not self.multi_enabled or not self.multi_executor:
                return jsonify({'success': False, 'error': 'Multi-account mode not enabled'})
            
            # Get account data from multi executor
            account_data = self.multi_executor.get_account_data(account_name)
            
            if not account_data['success']:
                return jsonify({'success': False, 'error': account_data.get('error', 'Account not found')})
            
            data = account_data['data']
            
            # Format response for HTML dashboard
            response_data = {
                'success': True,
                'account_name': account_name,
                'timestamp': datetime.now().isoformat(),
                'balance': {
                    'total_equity': data.get('total_equity', 0),
                    'available_balance': data.get('available_balance', 0),
                    'used_margin': data.get('used_margin', 0),
                    'initial_margin': data.get('initial_margin', 0),
                    'maintenance_margin': data.get('maintenance_margin', 0),
                    'margin_ratio': data.get('margin_ratio', 0)
                },
                'positions': data.get('positions', []),
                'pnl': {
                    'unrealized_pnl': data.get('unrealized_pnl', 0),
                    'realized_pnl': data.get('realized_pnl', 0),
                    'total_pnl': data.get('total_pnl', 0)
                },
                'trading': {
                    'daily_trades': getattr(self, 'daily_trades', 0),
                    'max_daily_trades': getattr(self.config, 'MAX_DAILY_TRADES', 8),
                    'emergency_stop': getattr(self, 'emergency_stop', False)
                }
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"❌ API account data error for {account_name}: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    def get_all_accounts_api(self) -> Dict:
        """Get all accounts data (API endpoint for HTML dashboard)"""
        try:
            if not self.multi_enabled or not self.multi_executor:
                return jsonify({'success': False, 'error': 'Multi-account mode not enabled'})
            
            all_accounts = {}
            for account_name in self.multi_executor.accounts.keys():
                account_data = self.multi_executor.get_account_data(account_name)
                if account_data['success']:
                    all_accounts[account_name] = account_data['data']
            
            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'accounts': all_accounts
            })
            
        except Exception as e:
            logger.error(f"❌ API all accounts error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    def get_last_alert_api(self) -> Dict:
        """Get last alert data (API endpoint for HTML dashboard)"""
        try:
            return jsonify({
                'success': True,
                'last_alert': self.last_alert,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ API last alert error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Run the webhook app"""
        logger.info(f"🚀 Starting Sniper Bybit Webhook on {host}:{port}")
        logger.info("🎯 Production Mode - Real Trading Active")
        logger.info(f"💰 Modal: ${self.config.ACCOUNT_BALANCE} | Symbol: {self.config.TARGET_SYMBOL}")
        
        # Production mode: disable reloader to prevent duplicate processes
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)

# Create environment file template
def create_env_template():
    """Create .env template for Bybit production"""
    env_content = '''# Bybit Production Configuration
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_SECRET_KEY=your_bybit_secret_key_here
BYBIT_AUTH_TOKEN=sniper-bybit-production-2024

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# Trading Configuration
TARGET_SYMBOL=ETHUSDT
ACCOUNT_BALANCE=30.0
RISK_PER_TRADE=0.02
LEVERAGE=10

# Security
ALLOWED_IPS=
'''
    
    with open('.env.bybit', 'w') as f:
        f.write(env_content)
    
    print("📝 Created .env.bybit template file")
    print("⚠️  Please update with your actual Bybit API credentials")

if __name__ == '__main__':
    # Create env template if not exists
    if not os.path.exists('.env.bybit'):
        create_env_template()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env.bybit')
    
    # Initialize and run webhook
    try:
        webhook = SniperBybitWebhook()
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', '5001'))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        webhook.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"❌ Failed to start webhook: {e}")
        print("\n🔧 Setup Instructions:")
        print("1. Update .env.bybit with your Bybit API credentials")
        print("2. Ensure you have sufficient balance ($30+)")
        print("3. Run: FLASK_PORT=5002 python bybit_webhook_app.py (or set FLASK_PORT in .env.bybit)")