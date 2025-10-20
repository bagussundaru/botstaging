"""
🔁 MULTI-ACCOUNT EXECUTOR - Bybit
Eksekusi sinyal TradingView secara paralel ke beberapa akun Bybit (apinur, apifan, apiarif)
Author: Sniper AI Trading Agent
"""

import os
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

from bybit_client import BybitProductionClient
from bybit_config import BybitProductionConfig
from sniper_calculator import SniperCalculator

class MultiAccountExecutor:
    """Executor untuk mengeksekusi sinyal ke banyak akun Bybit secara paralel"""

    def __init__(self, accounts: List[Dict]):
        """
        accounts: List[{
            'name': str,
            'api_key': str,
            'secret_key': str
        }]
        """
        self.accounts = accounts
        self.clients: Dict[str, BybitProductionClient] = {}

        # Inisialisasi client untuk tiap akun
        for acc in accounts:
            name = acc['name']
            api_key = acc['api_key']
            secret_key = acc['secret_key']
            self.clients[name] = BybitProductionClient(api_key, secret_key, testnet=False)

        self.symbol = BybitProductionConfig.TARGET_SYMBOL
        self.leverage = BybitProductionConfig.LEVERAGE
        self.qty_step = BybitProductionConfig.CONTRACT_SPECS.get(self.symbol, {}).get('qtyStep', 0.001)
        self.min_qty = BybitProductionConfig.CONTRACT_SPECS.get(self.symbol, {}).get('minOrderQty', 0.001)
        self.min_notional = BybitProductionConfig.CONTRACT_SPECS.get(self.symbol, {}).get('minNotionalValue', 1.0)

    def _round_to_step(self, qty: float) -> float:
        step = self.qty_step or 0.001
        if step <= 0:
            return round(qty, 4)
        return round((qty / step)) * step

    def _execute_for_account(self, name: str, client: BybitProductionClient, signal_data: Dict) -> Dict:
        """Eksekusi sinyal untuk satu akun"""
        try:
            side = signal_data.get('action', '').upper()
            symbol = signal_data.get('symbol', self.symbol)

            # Data pasar
            current_price = client.get_current_price(symbol)
            if not current_price:
                return {'success': False, 'account': name, 'error': 'Unable to get current price'}

            atr_value = client.calculate_atr(symbol)

            # Ambil saldo akun
            balance_info = client.get_account_balance()
            if not balance_info.get('success'):
                return {'success': False, 'account': name, 'error': 'Unable to get account balance'}
            available_balance = float(balance_info.get('available_balance', 0))

            # Set leverage untuk simbol (buy & sell leverage sama)
            try:
                leverage_val = int(BybitProductionConfig.LEVERAGE)
                _ = client._make_request('POST', '/v5/position/set-leverage', {
                    'category': 'linear',
                    'symbol': symbol,
                    'buyLeverage': str(leverage_val),
                    'sellLeverage': str(leverage_val),
                })
            except Exception as _e:
                pass  # jika gagal, lanjut dengan leverage default akun

            # Calculator dengan saldo per akun
            calculator = SniperCalculator(account_balance=available_balance)

            # Hitung SL berbasis ATR sesuai konfigurasi
            sl_multiplier = BybitProductionConfig.SNIPER_CONFIG['atr_multiplier']
            stop_loss = calculator.calculate_atr_stop_loss(current_price, atr_value, side, multiplier=sl_multiplier)

            # Position sizing per akun berdasarkan saldo (tanpa mengalikan leverage ke qty)
            risk_amount_usd = available_balance * BybitProductionConfig.RISK_PER_TRADE
            price_diff = abs(current_price - stop_loss)
            if price_diff <= 0:
                return {'success': False, 'account': name, 'error': 'Invalid price difference'}

            base_position_size = risk_amount_usd / price_diff
            max_position_size = (available_balance * BybitProductionConfig.MAX_POSITION_SIZE) / current_price
            position_size = min(base_position_size, max_position_size)

            # Pastikan memenuhi min notional dan min qty
            notional_value = position_size * current_price
            if notional_value < self.min_notional:
                position_size = self.min_notional / current_price

            if position_size < self.min_qty:
                position_size = self.min_qty

            # Round ke step
            position_size = self._round_to_step(position_size)

            # Cek margin dan skala jika perlu (gunakan max 80% balance)
            margin_required = (position_size * current_price) / self.leverage
            max_usable = available_balance * 0.8
            if margin_required > max_usable and current_price > 0:
                # Skala turun sesuai margin maksimum yang bisa dipakai
                scaled_position = (max_usable * self.leverage) / current_price
                position_size = max(self.min_qty, self._round_to_step(scaled_position))
                margin_required = (position_size * current_price) / self.leverage

            # Hitung TP
            tp_calc = calculator.calculate_take_profit_levels(
                entry_price=current_price,
                stop_loss_price=stop_loss,
                signal_type=side,
                risk_reward_ratio=BybitProductionConfig.SNIPER_CONFIG['risk_reward_ratio']
            )
            take_profit = tp_calc.get('take_profit_1')

            # Place order
            order_result = client.place_order(
                symbol=symbol,
                side=side,
                qty=position_size,
                price=None,  # market order
                stop_loss=stop_loss,
                take_profit=take_profit
            )

            if order_result.get('success'):
                return {
                    'success': True,
                    'account': name,
                    'order_id': order_result.get('order_id'),
                    'position_size': position_size,
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'atr_value': atr_value,
                    'available_balance': available_balance,
                    'margin_required': margin_required,
                    # Informasi risiko dengan estimasi berbasis posisi aktual
                    'risk_amount': round(position_size * abs(current_price - stop_loss), 2),
                    'reward_amount': round(position_size * abs(take_profit - current_price), 2),
                    'risk_percentage': round(((position_size * abs(current_price - stop_loss)) / available_balance) * 100, 2)
                }
            else:
                return {
                    'success': False,
                    'account': name,
                    'error': order_result.get('error', 'Unknown error'),
                    'code': order_result.get('code'),
                    'position_size': position_size,
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'available_balance': available_balance,
                    'margin_required': margin_required
                }
        except Exception as e:
            return {'success': False, 'account': name, 'error': f'Execution error: {str(e)}'}

    def execute_signal(self, signal_data: Dict) -> Dict:
        """
        Menjalankan sinyal secara paralel ke semua akun yang dikonfigurasi
        """
        results = []
        success_count = 0
        fail_count = 0

        with ThreadPoolExecutor(max_workers=len(self.accounts)) as executor:
            futures = []
            for acc in self.accounts:
                name = acc['name']
                client = self.clients[name]
                futures.append(executor.submit(self._execute_for_account, name, client, signal_data))

            for future in as_completed(futures):
                res = future.result()
                results.append(res)
                if res.get('success'):
                    success_count += 1
                else:
                    fail_count += 1

        # Susun hasil agregat
        return {
            'success': success_count > 0,
            'success_count': success_count,
            'fail_count': fail_count,
            'accounts': results,
            'symbol': signal_data.get('symbol', self.symbol),
            'action': signal_data.get('action', '').upper(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_account_data(self, account_name: str) -> Dict:
        """Get account data for specific account"""
        try:
            if account_name not in self.clients:
                return {'success': False, 'error': f'Account {account_name} not found'}
            
            client = self.clients[account_name]
            
            # Get account balance
            balance_info = client.get_account_balance()
            if not balance_info.get('success'):
                return {'success': False, 'error': 'Unable to get account balance'}
            
            # Get position info
            position_info = client.get_position_info(self.symbol)
            
            # Format data for dashboard
            data = {
                'total_equity': balance_info.get('total_balance', 0),
                'available_balance': balance_info.get('available_balance', 0),
                'used_margin': balance_info.get('used_margin', 0),
                'initial_margin': balance_info.get('initial_margin', 0),
                'maintenance_margin': balance_info.get('maintenance_margin', 0),
                'margin_ratio': balance_info.get('margin_ratio', 0),
                'unrealized_pnl': position_info.get('unrealized_pnl', 0) if position_info.get('success') else 0,
                'realized_pnl': 0,  # Could be enhanced to get from trade history
                'total_pnl': position_info.get('unrealized_pnl', 0) if position_info.get('success') else 0,
                'positions': []
            }
            
            # Add position data if exists
            if position_info.get('success') and position_info.get('size', 0) > 0:
                data['positions'].append({
                    'symbol': self.symbol,
                    'side': position_info.get('side', 'None'),
                    'size': position_info.get('size', 0),
                    'entry_price': position_info.get('entry_price', 0),
                    'mark_price': position_info.get('mark_price', 0),
                    'unrealized_pnl': position_info.get('unrealized_pnl', 0),
                    'percentage': position_info.get('percentage', 0)
                })
            
            return {'success': True, 'data': data}
            
        except Exception as e:
            return {'success': False, 'error': f'Error getting account data: {str(e)}'}