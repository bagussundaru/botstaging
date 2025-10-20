"""
🎯 SNIPER BYBIT CLIENT - Production Trading
Bybit API Client untuk Production Trading dengan Modal $30
Author: Sniper AI Trading Agent
"""

import hashlib
import hmac
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bybit_config import BybitProductionConfig

class BybitProductionClient:
    """Bybit Production Client untuk Sniper Trading Bot"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.base_url = BybitProductionConfig.get_bybit_base_url()
        self.session = requests.Session()
        
        # Set headers
        self.session.headers.update({
            'X-BAPI-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        })
        
        print(f"🎯 Bybit Client initialized - {'Testnet' if testnet else 'Production'}")
        print(f"📊 Base URL: {self.base_url}")
    
    def _generate_signature(self, timestamp: str, params: str) -> str:
        """Generate signature for Bybit API"""
        param_str = f"{timestamp}{self.api_key}5000{params}"
        return hmac.new(
            self.secret_key.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Bybit API"""
        timestamp = str(int(time.time() * 1000))
        
        if params is None:
            params = {}
        
        # Prepare request
        if method.upper() == 'GET':
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.base_url}{endpoint}?{query_string}" if query_string else f"{self.base_url}{endpoint}"
            signature = self._generate_signature(timestamp, query_string)
        else:
            json_params = json.dumps(params) if params else ""
            url = f"{self.base_url}{endpoint}"
            signature = self._generate_signature(timestamp, json_params)
        
        # Set headers
        headers = {
            'X-BAPI-API-KEY': self.api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': '5000',
            'Content-Type': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request Error: {e}")
            return {'retCode': -1, 'retMsg': str(e)}
    
    def get_account_balance(self) -> Dict:
        """Get account balance"""
        endpoint = "/v5/account/wallet-balance"
        params = {'accountType': 'UNIFIED'}
        
        response = self._make_request('GET', endpoint, params)
        
        if response.get('retCode') == 0:
            try:
                wallet_balance = response['result']['list'][0]
                total_balance = float(wallet_balance['totalWalletBalance'])
                available_balance = float(wallet_balance['totalAvailableBalance'])
                
                return {
                    'success': True,
                    'total_balance': total_balance,
                    'available_balance': available_balance,
                    'currency': 'USDT'
                }
            except (KeyError, IndexError, ValueError) as e:
                return {'success': False, 'error': f'Balance parsing error: {e}'}
        else:
            return {'success': False, 'error': response.get('retMsg', 'Unknown error')}
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        endpoint = "/v5/market/tickers"
        params = {'category': 'linear', 'symbol': symbol}
        
        response = self._make_request('GET', endpoint, params)
        
        if response.get('retCode') == 0:
            try:
                ticker = response['result']['list'][0]
                return float(ticker['lastPrice'])
            except (KeyError, IndexError, ValueError):
                return None
        return None
    
    def get_position_info(self, symbol: str) -> Dict:
        """Get current position information"""
        endpoint = "/v5/position/list"
        params = {'category': 'linear', 'symbol': symbol}
        
        response = self._make_request('GET', endpoint, params)
        
        if response.get('retCode') == 0:
            positions = response['result']['list']
            if positions:
                position = positions[0]
                
                # Safe parsing with empty string handling
                try:
                    size = float(position['size']) if position['size'] and position['size'] != '' else 0
                    avg_price = float(position['avgPrice']) if position['avgPrice'] and position['avgPrice'] != '' else 0
                    unrealized_pnl = float(position['unrealisedPnl']) if position['unrealisedPnl'] and position['unrealisedPnl'] != '' else 0
                    
                    # Only return position if size > 0
                    if size > 0:
                        return {
                            'success': True,
                            'symbol': position['symbol'],
                            'side': position['side'],
                            'size': size,
                            'entry_price': avg_price,
                            'unrealized_pnl': unrealized_pnl,
                            'percentage': unrealized_pnl / BybitProductionConfig.ACCOUNT_BALANCE * 100 if BybitProductionConfig.ACCOUNT_BALANCE > 0 else 0
                        }
                    else:
                        return {'success': True, 'size': 0, 'message': 'No position'}
                except (ValueError, TypeError) as e:
                    return {'success': False, 'error': f'Position parsing error: {e}'}
            else:
                return {'success': True, 'size': 0, 'message': 'No position'}
        else:
            return {'success': False, 'error': response.get('retMsg', 'Unknown error')}
    
    def place_order(self, symbol: str, side: str, qty: float, price: float = None, 
                   stop_loss: float = None, take_profit: float = None) -> Dict:
        """
        Place order with professional Sniper Method calculations
        """
        endpoint = "/v5/order/create"
        
        # Determine order type
        order_type = "Market" if price is None else "Limit"
        
        params = {
            'category': 'linear',
            'symbol': symbol,
            'side': side.capitalize(),
            'orderType': order_type,
            'qty': str(qty),
            'timeInForce': 'GTC'
        }
        
        if price:
            params['price'] = str(price)
        
        # Add Stop Loss and Take Profit
        if stop_loss:
            params['stopLoss'] = str(stop_loss)
        
        if take_profit:
            params['takeProfit'] = str(take_profit)
        
        print(f"🎯 Placing {side.upper()} order for {symbol}")
        print(f"📊 Quantity: {qty}")
        print(f"💰 Price: {price if price else 'Market'}")
        print(f"🛑 Stop Loss: {stop_loss}")
        print(f"🎯 Take Profit: {take_profit}")
        
        response = self._make_request('POST', endpoint, params)
        
        if response.get('retCode') == 0:
            order_id = response['result']['orderId']
            return {
                'success': True,
                'order_id': order_id,
                'symbol': symbol,
                'side': side,
                'quantity': qty,
                'price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': response.get('retMsg', 'Unknown error'),
                'code': response.get('retCode')
            }
    
    def close_position(self, symbol: str) -> Dict:
        """Close current position"""
        # Get current position
        position_info = self.get_position_info(symbol)
        
        if not position_info['success'] or position_info.get('size', 0) == 0:
            return {'success': False, 'error': 'No position to close'}
        
        # Determine opposite side
        current_side = position_info['side']
        close_side = 'Sell' if current_side == 'Buy' else 'Buy'
        position_size = position_info['size']
        
        # Place market order to close
        return self.place_order(
            symbol=symbol,
            side=close_side,
            qty=position_size,
            price=None  # Market order
        )
    
    def calculate_atr(self, symbol: str, period: int = 14) -> float:
        """
        Calculate ATR (Average True Range) for volatility-based SL/TP
        Simplified calculation using recent price data
        """
        endpoint = "/v5/market/kline"
        params = {
            'category': 'linear',
            'symbol': symbol,
            'interval': '60',  # 1-hour candles for better accuracy
            'limit': period + 1
        }
        
        response = self._make_request('GET', endpoint, params)
        
        if response.get('retCode') == 0:
            klines = response['result']['list']
            
            if len(klines) >= period:
                true_ranges = []
                
                for i in range(1, len(klines)):
                    current = klines[i]
                    previous = klines[i-1]
                    
                    high = float(current[2])
                    low = float(current[3])
                    prev_close = float(previous[4])
                    
                    tr1 = high - low
                    tr2 = abs(high - prev_close)
                    tr3 = abs(low - prev_close)
                    
                    true_range = max(tr1, tr2, tr3)
                    true_ranges.append(true_range)
                
                # Calculate ATR as simple moving average
                atr = sum(true_ranges[-period:]) / period
                return atr
        
        # Fallback: use 0.5% of current price as ATR estimate
        current_price = self.get_current_price(symbol)
        return current_price * 0.005 if current_price else 0
    
    def execute_sniper_trade(self, signal_data: Dict) -> Dict:
        """
        Execute trade using Sniper Method with professional calculations
        """
        try:
            symbol = signal_data.get('symbol', BybitProductionConfig.TARGET_SYMBOL)
            side = signal_data.get('action', '').upper()
            confidence = float(signal_data.get('confidence', 0))
            
            # Validate confidence
            if confidence < BybitProductionConfig.SNIPER_CONFIG['min_confidence']:
                return {
                    'success': False,
                    'error': f'Confidence {confidence:.1%} below minimum {BybitProductionConfig.SNIPER_CONFIG["min_confidence"]:.1%}'
                }
            
            # Get current price and ATR
            current_price = self.get_current_price(symbol)
            if not current_price:
                return {'success': False, 'error': 'Unable to get current price'}
            
            atr_value = self.calculate_atr(symbol)
            
            # Calculate position details using Sniper Method
            position_info = BybitProductionConfig.get_position_info(
                side, current_price, atr_value
            )
            
            # Check account balance
            balance_info = self.get_account_balance()
            if not balance_info['success']:
                return {'success': False, 'error': 'Unable to get account balance'}
            
            available_balance = balance_info['available_balance']
            required_margin = position_info['position_size'] * current_price / BybitProductionConfig.LEVERAGE
            
            if required_margin > available_balance * 0.8:  # Use max 80% of available balance
                return {
                    'success': False,
                    'error': f'Insufficient balance. Required: ${required_margin:.2f}, Available: ${available_balance:.2f}'
                }
            
            # Execute the trade
            result = self.place_order(
                symbol=symbol,
                side=side,
                qty=position_info['position_size'],
                price=None,  # Market order
                stop_loss=position_info['stop_loss'],
                take_profit=position_info['take_profit']
            )
            
            if result['success']:
                # Add Sniper Method details to result
                result.update({
                    'sniper_method': True,
                    'confidence': confidence,
                    'atr_value': atr_value,
                    'risk_amount': position_info['risk_amount'],
                    'reward_amount': position_info['reward_amount'],
                    'risk_reward_ratio': position_info['risk_reward_ratio'],
                    'entry_price': current_price,
                    'account_balance': BybitProductionConfig.ACCOUNT_BALANCE
                })
                
                print(f"✅ Sniper Trade Executed Successfully!")
                print(f"📊 Symbol: {symbol} | Side: {side} | Confidence: {confidence:.1%}")
                print(f"💰 Position Size: {position_info['position_size']} | Entry: ${current_price}")
                print(f"🛑 Stop Loss: ${position_info['stop_loss']} | 🎯 Take Profit: ${position_info['take_profit']}")
                print(f"⚖️ Risk: ${position_info['risk_amount']} | Reward: ${position_info['reward_amount']} | R:R = 1:{position_info['risk_reward_ratio']}")
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'Trade execution error: {str(e)}'}
    
    def get_open_orders(self, symbol: str = None) -> Dict:
        """Get all open orders including TP/SL orders"""
        endpoint = "/v5/order/realtime"
        params = {
            'category': 'linear'
        }
        
        if symbol:
            params['symbol'] = symbol
        
        response = self._make_request('GET', endpoint, params)
        
        if response.get('retCode') == 0:
            orders = response['result']['list']
            
            # Categorize orders
            open_orders = []
            tp_orders = []
            sl_orders = []
            
            for order in orders:
                # For TP/SL orders, use triggerPrice instead of price
                price_value = order.get('triggerPrice') if order.get('stopOrderType') in ['TakeProfit', 'StopLoss'] else order.get('price')
                
                order_info = {
                    'orderId': order.get('orderId'),
                    'symbol': order.get('symbol'),
                    'side': order.get('side'),
                    'orderType': order.get('orderType'),
                    'qty': order.get('qty'),
                    'price': price_value or order.get('price', '0'),
                    'triggerPrice': order.get('triggerPrice', '0'),
                    'orderStatus': order.get('orderStatus'),
                    'createdTime': order.get('createdTime'),
                    'stopOrderType': order.get('stopOrderType', '')
                }
                
                # Categorize based on order type
                if order.get('stopOrderType') == 'TakeProfit':
                    tp_orders.append(order_info)
                elif order.get('stopOrderType') == 'StopLoss':
                    sl_orders.append(order_info)
                else:
                    open_orders.append(order_info)
            
            return {
                'success': True,
                'total_orders': len(orders),
                'open_orders': open_orders,
                'take_profit_orders': tp_orders,
                'stop_loss_orders': sl_orders,
                'has_tp': len(tp_orders) > 0,
                'has_sl': len(sl_orders) > 0
            }
        else:
            return {
                'success': False,
                'error': response.get('retMsg', 'Unknown error')
            }

    def close_position(self, symbol: str) -> Dict:
        """Close open position for specified symbol"""
        try:
            # First, get current position info
            position_info = self.get_position_info(symbol)
            
            if not position_info['success']:
                return {'success': False, 'error': 'Unable to get position info'}
            
            if position_info.get('size', 0) == 0:
                return {'success': False, 'error': 'No open position to close'}
            
            # Determine opposite side for closing
            current_side = position_info['side']
            close_side = 'Sell' if current_side == 'Buy' else 'Buy'
            position_size = position_info['size']
            
            # Place market order to close position
            endpoint = "/v5/order/create"
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': close_side,
                'orderType': 'Market',
                'qty': str(position_size),
                'timeInForce': 'IOC',  # Immediate or Cancel
                'reduceOnly': True  # This ensures we're closing, not opening new position
            }
            
            print(f"🔄 Closing {current_side} position for {symbol}")
            print(f"📊 Position Size: {position_size}")
            print(f"💰 Close Side: {close_side}")
            
            response = self._make_request('POST', endpoint, params)
            
            if response.get('retCode') == 0:
                order_id = response['result']['orderId']
                
                print(f"✅ Position close order placed successfully!")
                print(f"📋 Order ID: {order_id}")
                
                return {
                    'success': True,
                    'message': 'Position closed successfully',
                    'order_id': order_id,
                    'symbol': symbol,
                    'side': close_side,
                    'quantity': position_size,
                    'closed_position_side': current_side
                }
            else:
                error_msg = response.get('retMsg', 'Unknown error')
                print(f"❌ Failed to close position: {error_msg}")
                return {
                    'success': False,
                    'error': f'Failed to close position: {error_msg}'
                }
                
        except Exception as e:
            print(f"❌ Error closing position: {e}")
            return {
                'success': False,
                'error': f'Error closing position: {str(e)}'
            }

    def get_trade_history(self, symbol: str, limit: int = 50) -> Dict:
        """Get recent trade history"""
        endpoint = "/v5/execution/list"
        params = {
            'category': 'linear',
            'symbol': symbol,
            'limit': limit
        }
        
        response = self._make_request('GET', endpoint, params)
        
        if response.get('retCode') == 0:
            return {
                'success': True,
                'trades': response['result']['list']
            }
        else:
            return {
                'success': False,
                'error': response.get('retMsg', 'Unknown error')
            }