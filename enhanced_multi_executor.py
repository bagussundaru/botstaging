"""
ENHANCED MULTI-ACCOUNT EXECUTOR WITH CONFLICT MANAGEMENT
Solusi untuk:
1. TP lama tercapai -> Optimized TP levels
2. Sinyal konflik -> Smart conflict resolution
3. Profit optimization untuk modal $66
"""

import logging
from typing import Dict, List
from datetime import datetime
from bybit_client import BybitProductionClient
from bybit_config import BybitProductionConfig
from sniper_calculator import SniperCalculator
from signal_conflict_manager import SignalConflictManager
from optimized_config_66usd import OptimizedConfig66USD

logger = logging.getLogger(__name__)

class EnhancedMultiAccountExecutor:
    """Enhanced executor with conflict management and optimized TP/SL"""
    
    def __init__(self, symbol: str = 'ETHUSDT'):
        self.symbol = symbol
        self.leverage = BybitProductionConfig.LEVERAGE
        self.conflict_manager = SignalConflictManager()
        self.optimized_config = OptimizedConfig66USD()
        
        # Contract specifications
        self.qty_step = BybitProductionConfig.CONTRACT_SPECS.get(self.symbol, {}).get('qtyStep', 0.001)
        self.min_qty = BybitProductionConfig.CONTRACT_SPECS.get(self.symbol, {}).get('minOrderQty', 0.001)
        self.min_notional = BybitProductionConfig.CONTRACT_SPECS.get(self.symbol, {}).get('minNotionalValue', 1.0)
        
        logger.info(f"🚀 Enhanced Multi-Account Executor initialized for {symbol}")
        logger.info(f"⚡ Conflict management: ENABLED")
        logger.info(f"🎯 Optimized for $66 accounts with faster TP")
    
    def execute_signal(self, signal_data: Dict, accounts: Dict[str, BybitProductionClient]) -> Dict:
        """Execute signal with enhanced conflict management"""
        
        results = {}
        successful_accounts = []
        failed_accounts = []
        conflict_resolutions = []
        
        logger.info(f"🎯 Executing enhanced signal for {len(accounts)} accounts")
        logger.info(f"📊 Signal: {signal_data.get('action')} {signal_data.get('symbol')}")
        
        for account_name, client in accounts.items():
            try:
                logger.info(f"🔄 Processing account: {account_name}")
                
                # Step 1: Analyze signal conflict
                conflict_analysis = self.conflict_manager.analyze_signal_conflict(
                    account_name, client, signal_data, self.symbol
                )
                
                logger.info(f"🔍 {account_name} conflict analysis: {conflict_analysis['action']} - {conflict_analysis['reason']}")
                conflict_resolutions.append({
                    'account': account_name,
                    'analysis': conflict_analysis
                })
                
                # Step 2: Handle conflict resolution
                if conflict_analysis['action'] == 'ignore':
                    results[account_name] = {
                        'success': False,
                        'account': account_name,
                        'error': conflict_analysis['reason'],
                        'conflict_resolution': 'ignored'
                    }
                    failed_accounts.append(account_name)
                    continue
                
                elif conflict_analysis['action'] in ['reverse', 'partial_close']:
                    # Execute conflict resolution first
                    resolution_result = self.conflict_manager.execute_conflict_resolution(
                        account_name, client, conflict_analysis, signal_data, self.symbol
                    )
                    
                    logger.info(f"🔄 {account_name} conflict resolution: {resolution_result}")
                    
                    if not resolution_result.get('success'):
                        results[account_name] = {
                            'success': False,
                            'account': account_name,
                            'error': f"Conflict resolution failed: {resolution_result.get('message')}",
                            'conflict_resolution': resolution_result
                        }
                        failed_accounts.append(account_name)
                        continue
                    
                    # If reversal was executed, proceed with new signal
                    if resolution_result.get('ready_for_new_signal'):
                        logger.info(f"✅ {account_name} ready for new signal after reversal")
                    else:
                        # Partial close only, don't execute new signal
                        results[account_name] = {
                            'success': True,
                            'account': account_name,
                            'message': 'Partial close executed, no new position opened',
                            'conflict_resolution': resolution_result
                        }
                        successful_accounts.append(account_name)
                        continue
                
                # Step 3: Execute enhanced signal with optimized TP/SL
                execution_result = self._execute_enhanced_signal(account_name, client, signal_data)
                
                if execution_result.get('success'):
                    successful_accounts.append(account_name)
                    logger.info(f"✅ {account_name} execution successful")
                else:
                    failed_accounts.append(account_name)
                    logger.error(f"❌ {account_name} execution failed: {execution_result.get('error')}")
                
                results[account_name] = execution_result
                
            except Exception as e:
                logger.error(f"❌ Error processing {account_name}: {e}")
                results[account_name] = {
                    'success': False,
                    'account': account_name,
                    'error': f'Processing error: {str(e)}'
                }
                failed_accounts.append(account_name)
        
        # Summary
        summary = {
            'total_accounts': len(accounts),
            'successful_accounts': len(successful_accounts),
            'failed_accounts': len(failed_accounts),
            'success_rate': f"{(len(successful_accounts)/len(accounts)*100):.1f}%" if accounts else "0%",
            'successful_list': successful_accounts,
            'failed_list': failed_accounts,
            'conflict_resolutions': conflict_resolutions,
            'results': results
        }
        
        logger.info(f"📊 Enhanced execution summary: {summary['success_rate']} success rate")
        logger.info(f"✅ Successful: {successful_accounts}")
        logger.info(f"❌ Failed: {failed_accounts}")
        
        return summary
    
    def _execute_enhanced_signal(self, account_name: str, client: BybitProductionClient, signal_data: Dict) -> Dict:
        """Execute signal with enhanced TP/SL optimization"""
        
        try:
            side = signal_data.get('action', '').upper()
            symbol = signal_data.get('symbol', self.symbol)
            
            # Get market data
            current_price = signal_data.get('current_price')
            if not current_price:
                current_price = client.get_current_price(symbol)
                if not current_price:
                    return {'success': False, 'account': account_name, 'error': 'Unable to get current price'}
            
            # Get ATR
            atr_value = signal_data.get('atr')
            if not atr_value or atr_value <= 0:
                atr_value = client.calculate_atr(symbol)
            
            # Get account balance
            balance_info = client.get_account_balance()
            if not balance_info.get('success'):
                return {'success': False, 'account': account_name, 'error': 'Unable to get account balance'}
            available_balance = float(balance_info.get('available_balance', 0))
            
            if available_balance <= 0:
                return {'success': False, 'account': account_name, 'error': f'Insufficient balance: ${available_balance:.2f}'}
            
            # Set leverage
            try:
                leverage_val = int(self.leverage)
                _ = client._make_request('POST', '/v5/position/set-leverage', {
                    'category': 'linear',
                    'symbol': symbol,
                    'buyLeverage': str(leverage_val),
                    'sellLeverage': str(leverage_val),
                })
            except Exception:
                pass
            
            # Enhanced calculator with optimized settings
            calculator = SniperCalculator(account_balance=available_balance)
            
            # OPTIMIZED SL calculation (tighter for faster TP)
            sl_multiplier = self.optimized_config.FAST_TP_CONFIG['atr_multiplier']  # 1.8x instead of 2.2x
            stop_loss = calculator.calculate_atr_stop_loss(current_price, atr_value, side, multiplier=sl_multiplier)
            
            # OPTIMIZED position sizing for $66 accounts
            risk_amount_usd = available_balance * self.optimized_config.RISK_PER_TRADE  # 2% instead of 2.5%
            price_diff = abs(current_price - stop_loss)
            
            if price_diff <= 0:
                return {'success': False, 'account': account_name, 'error': 'Invalid price difference'}
            
            base_position_size = risk_amount_usd / price_diff
            max_position_size = (available_balance * self.optimized_config.MAX_POSITION_SIZE) / current_price
            position_size = min(base_position_size, max_position_size)
            
            # Ensure minimum requirements
            notional_value = position_size * current_price
            if notional_value < self.min_notional:
                position_size = self.min_notional / current_price
            
            if position_size < self.min_qty:
                position_size = self.min_qty
            
            position_size = self._round_to_step(position_size)
            
            # ENHANCED TP calculation with multiple levels
            tp_levels = self._calculate_enhanced_tp_levels(current_price, stop_loss, side)
            primary_tp = tp_levels['tp2']  # Use TP2 as primary target (1.2 R:R)
            
            # Risk validation
            final_risk_amount = position_size * price_diff
            final_risk_percentage = (final_risk_amount / available_balance) * 100
            
            if final_risk_percentage > 6.0:  # Lower risk cap for $66 accounts
                safe_position_size = (available_balance * 0.06) / price_diff
                position_size = max(self.min_qty, self._round_to_step(safe_position_size))
            
            # Margin check
            margin_required = (position_size * current_price) / self.leverage
            max_usable = available_balance * 0.8
            if margin_required > max_usable:
                scaled_position = (max_usable * self.leverage) / current_price
                position_size = max(self.min_qty, self._round_to_step(scaled_position))
            
            # Place enhanced order with optimized TP/SL
            order_result = client.place_order(
                symbol=symbol,
                side=side,
                qty=position_size,
                price=None,  # market order
                stop_loss=stop_loss,
                take_profit=primary_tp
            )
            
            if order_result.get('success'):
                # Calculate final metrics
                final_risk_amount = position_size * price_diff
                final_risk_percentage = (final_risk_amount / available_balance) * 100
                potential_profit = position_size * abs(primary_tp - current_price)
                
                return {
                    'success': True,
                    'account': account_name,
                    'order_id': order_result.get('order_id'),
                    'position_info': {
                        'symbol': symbol,
                        'side': side,
                        'position_size': position_size,
                        'entry_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': primary_tp,
                        'tp_levels': tp_levels,
                        'risk_amount': final_risk_amount,
                        'risk_percentage': final_risk_percentage,
                        'potential_profit': potential_profit,
                        'risk_reward_ratio': abs(primary_tp - current_price) / price_diff,
                        'available_balance': available_balance,
                        'optimized_settings': {
                            'atr_multiplier': sl_multiplier,
                            'risk_per_trade': self.optimized_config.RISK_PER_TRADE,
                            'tp_strategy': 'enhanced_multi_level'
                        }
                    }
                }
            else:
                return {
                    'success': False,
                    'account': account_name,
                    'error': f"Order placement failed: {order_result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            logger.error(f"❌ Enhanced execution error for {account_name}: {e}")
            return {
                'success': False,
                'account': account_name,
                'error': f'Enhanced execution error: {str(e)}'
            }
    
    def _calculate_enhanced_tp_levels(self, entry_price: float, stop_loss: float, side: str) -> Dict:
        """Calculate enhanced TP levels for faster profit realization"""
        
        price_diff = abs(entry_price - stop_loss)
        
        if side.upper() == 'BUY':
            tp1 = entry_price + (price_diff * 0.8)   # Quick TP (40% close)
            tp2 = entry_price + (price_diff * 1.2)   # Target TP (35% close)
            tp3 = entry_price + (price_diff * 1.8)   # Bonus TP (25% close)
        else:  # SELL
            tp1 = entry_price - (price_diff * 0.8)
            tp2 = entry_price - (price_diff * 1.2)
            tp3 = entry_price - (price_diff * 1.8)
        
        return {
            'tp1': round(tp1, 2),
            'tp2': round(tp2, 2),
            'tp3': round(tp3, 2),
            'percentages': [40, 35, 25],
            'ratios': [0.8, 1.2, 1.8],
            'strategy': 'enhanced_multi_level'
        }
    
    def _round_to_step(self, qty: float) -> float:
        """Round quantity to valid step size"""
        step = self.qty_step or 0.001
        if step <= 0:
            return round(qty, 4)
        return round((qty / step)) * step
    
    def get_conflict_stats(self, accounts: Dict[str, BybitProductionClient]) -> Dict:
        """Get conflict resolution statistics for all accounts"""
        
        stats = {}
        for account_name in accounts.keys():
            stats[account_name] = self.conflict_manager.get_conflict_stats(account_name)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'account_stats': stats,
            'total_accounts': len(accounts)
        }

# USAGE EXAMPLE
"""
# Initialize enhanced executor
enhanced_executor = EnhancedMultiAccountExecutor('ETHUSDT')

# Execute signal with conflict management
signal_data = {
    'action': 'BUY',
    'symbol': 'ETHUSDT',
    'current_price': 3800.0,
    'atr': 45.0
}

accounts = {
    'apifan': apifan_client,
    'apiarif': apiarif_client
}

result = enhanced_executor.execute_signal(signal_data, accounts)
print(f"Enhanced execution result: {result}")

# Get conflict statistics
stats = enhanced_executor.get_conflict_stats(accounts)
print(f"Conflict stats: {stats}")
"""