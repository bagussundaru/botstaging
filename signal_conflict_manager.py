"""
SIGNAL CONFLICT MANAGER
Menangani sinyal yang bertentangan saat ada posisi terbuka
Solusi untuk masalah: "sinyal kebalikan dari open posisi"
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from bybit_client import BybitProductionClient
from optimized_config_66usd import OptimizedConfig66USD

logger = logging.getLogger(__name__)

class SignalConflictManager:
    """Manages conflicting signals during open positions"""
    
    def __init__(self):
        self.config = OptimizedConfig66USD()
        self.daily_reversals = {}  # Track daily reversals per account
        self.daily_reversal_limit = 3  # Max 3 reversals per day per account
        self.last_reset_date = datetime.now().date()
        
        logger.info("🔄 Signal Conflict Manager initialized")
        logger.info("📊 Features: Smart reversal, Partial close, Daily limits")
        logger.info(f"⚠️ Daily reversal limit: {self.daily_reversal_limit} per account")
        
    def analyze_signal_conflict(self, account_name: str, client: BybitProductionClient, 
                              new_signal: Dict, symbol: str = 'ETHUSDT') -> Dict:
        """
        Analyze if new signal conflicts with existing position
        Returns action recommendation: 'execute', 'ignore', 'reverse', 'partial_close'
        """
        try:
            # Get current position
            position_info = client.get_position_info(symbol)
            
            if not position_info.get('success') or position_info.get('size', 0) == 0:
                # No position exists, execute normally
                return {
                    'action': 'execute',
                    'reason': 'No existing position',
                    'recommendation': 'Execute new signal normally'
                }
            
            current_side = position_info.get('side', '').upper()
            current_size = position_info.get('size', 0)
            current_pnl = position_info.get('unrealised_pnl', 0)
            entry_price = position_info.get('entry_price', 0)
            
            new_side = new_signal.get('action', '').upper()
            
            # Same direction signal - ignore
            if current_side == new_side:
                return {
                    'action': 'ignore',
                    'reason': 'Same direction as existing position',
                    'recommendation': 'Ignore signal - already in same direction'
                }
            
            # Opposite direction signal - analyze conflict
            return self._handle_opposite_signal(
                account_name, client, current_side, current_size, 
                current_pnl, entry_price, new_side, symbol
            )
            
        except Exception as e:
            logging.error(f"Error analyzing signal conflict for {account_name}: {e}")
            return {
                'action': 'ignore',
                'reason': f'Error: {str(e)}',
                'recommendation': 'Ignore due to error'
            }
    
    def _handle_opposite_signal(self, account_name: str, client: BybitProductionClient,
                               current_side: str, current_size: float, current_pnl: float,
                               entry_price: float, new_side: str, symbol: str) -> Dict:
        """Handle opposite direction signal"""
        
        # Calculate current profit/loss percentage
        current_price = client.get_current_price(symbol)
        if not current_price:
            return {'action': 'ignore', 'reason': 'Cannot get current price'}
        
        if current_side == 'BUY':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SELL
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Decision matrix based on current P&L and configuration
        decision = self._make_reversal_decision(
            account_name, pnl_pct, current_pnl, current_side, new_side
        )
        
        return decision
    
    def _make_reversal_decision(self, account_name: str, pnl_pct: float, 
                               current_pnl: float, current_side: str, new_side: str) -> Dict:
        """Make decision on how to handle reversal"""
        
        config = self.config.CONFLICT_MANAGEMENT
        
        # Check daily reversal limit
        today = datetime.now().date()
        daily_reversals = self.reversal_count.get(f"{account_name}_{today}", 0)
        
        if daily_reversals >= config['max_reversal_per_day']:
            return {
                'action': 'ignore',
                'reason': f'Daily reversal limit reached ({daily_reversals})',
                'recommendation': 'Ignore - too many reversals today'
            }
        
        # Decision based on P&L
        if pnl_pct >= 1.0:  # Profit >= 1%
            return {
                'action': 'partial_close',
                'reason': f'In profit {pnl_pct:.2f}% - take partial profit before reversal',
                'recommendation': 'Close 50% position, then reverse remaining',
                'close_percentage': 50
            }
        
        elif pnl_pct >= -0.5:  # Small loss or breakeven
            return {
                'action': 'reverse',
                'reason': f'Small loss {pnl_pct:.2f}% - safe to reverse',
                'recommendation': 'Close current position and open opposite',
                'close_percentage': 100
            }
        
        elif pnl_pct >= -2.0:  # Medium loss
            return {
                'action': 'partial_close',
                'reason': f'Medium loss {pnl_pct:.2f}% - reduce exposure',
                'recommendation': 'Close 50% to reduce risk, keep 50%',
                'close_percentage': 50
            }
        
        else:  # Large loss > 2%
            return {
                'action': 'ignore',
                'reason': f'Large loss {pnl_pct:.2f}% - hold position',
                'recommendation': 'Ignore signal - loss too large for reversal'
            }
    
    def execute_conflict_resolution(self, account_name: str, client: BybitProductionClient,
                                  decision: Dict, new_signal: Dict, symbol: str = 'ETHUSDT') -> Dict:
        """Execute the conflict resolution decision"""
        
        action = decision['action']
        
        try:
            if action == 'ignore':
                return {
                    'success': True,
                    'action': 'ignored',
                    'message': decision['recommendation']
                }
            
            elif action == 'execute':
                # No conflict, execute normally
                return {
                    'success': True,
                    'action': 'execute_normal',
                    'message': 'No conflict - executing new signal'
                }
            
            elif action == 'reverse':
                # Close current position and open opposite
                return self._execute_reversal(account_name, client, new_signal, symbol, 100)
            
            elif action == 'partial_close':
                # Partial close based on decision
                close_pct = decision.get('close_percentage', 50)
                return self._execute_partial_close(account_name, client, close_pct, symbol)
            
            else:
                return {
                    'success': False,
                    'action': 'unknown',
                    'message': f'Unknown action: {action}'
                }
                
        except Exception as e:
            logging.error(f"Error executing conflict resolution for {account_name}: {e}")
            return {
                'success': False,
                'action': 'error',
                'message': f'Execution error: {str(e)}'
            }
    
    def _execute_reversal(self, account_name: str, client: BybitProductionClient,
                         new_signal: Dict, symbol: str, close_percentage: int) -> Dict:
        """Execute position reversal"""
        
        try:
            # Step 1: Close current position
            close_result = client.close_position(symbol, percentage=close_percentage)
            
            if not close_result.get('success'):
                return {
                    'success': False,
                    'action': 'reversal_failed',
                    'message': f'Failed to close position: {close_result.get("error")}'
                }
            
            # Step 2: Wait a moment for settlement
            import time
            time.sleep(2)
            
            # Step 3: Update reversal tracking
            today = datetime.now().date()
            key = f"{account_name}_{today}"
            self.reversal_count[key] = self.reversal_count.get(key, 0) + 1
            self.last_reversal[account_name] = datetime.now()
            
            return {
                'success': True,
                'action': 'reversed',
                'message': f'Position reversed successfully. Reversal count today: {self.reversal_count[key]}',
                'close_result': close_result,
                'ready_for_new_signal': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'action': 'reversal_error',
                'message': f'Reversal error: {str(e)}'
            }
    
    def _execute_partial_close(self, account_name: str, client: BybitProductionClient,
                              close_percentage: int, symbol: str) -> Dict:
        """Execute partial position close"""
        
        try:
            close_result = client.close_position(symbol, percentage=close_percentage)
            
            if close_result.get('success'):
                return {
                    'success': True,
                    'action': 'partial_closed',
                    'message': f'{close_percentage}% of position closed successfully',
                    'close_result': close_result
                }
            else:
                return {
                    'success': False,
                    'action': 'partial_close_failed',
                    'message': f'Failed to close {close_percentage}% of position: {close_result.get("error")}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'action': 'partial_close_error',
                'message': f'Partial close error: {str(e)}'
            }
    
    def _make_conflict_decision(self, current_pnl: float, position_side: str, signal_action: str) -> Dict:
        """Make decision on how to handle signal conflict"""
        
        # If profitable position (>$5), consider partial close
        if current_pnl > 5.0:
            return {
                'action': 'partial_close',
                'reason': f'Profitable position (+${current_pnl:.2f}), taking partial profit',
                'close_percentage': 50
            }
        
        # If small loss (<$3), consider reversal
        elif current_pnl > -3.0:
            return {
                'action': 'reverse',
                'reason': f'Small loss (${current_pnl:.2f}), reversing position',
                'close_percentage': 100
            }
        
        # If significant loss (>$3), hold position
        else:
            return {
                'action': 'ignore',
                'reason': f'Significant loss (${current_pnl:.2f}), holding position',
                'close_percentage': 0
            }
    
    def get_conflict_stats(self, account_name: str) -> Dict:
        """Get conflict resolution statistics for account"""
        
        today = datetime.now().date()
        key = f"{account_name}_{today}"
        
        return {
            'account': account_name,
            'daily_reversals': self.reversal_count.get(key, 0),
            'max_daily_reversals': self.config.CONFLICT_MANAGEMENT['max_reversal_per_day'],
            'last_reversal': self.last_reversal.get(account_name),
            'reversal_limit_reached': self.reversal_count.get(key, 0) >= self.config.CONFLICT_MANAGEMENT['max_reversal_per_day']
        }

# USAGE EXAMPLE
"""
# Initialize conflict manager
conflict_manager = SignalConflictManager()

# Analyze new signal against existing position
decision = conflict_manager.analyze_signal_conflict(
    account_name='apifan',
    client=bybit_client,
    new_signal={'action': 'SELL', 'symbol': 'ETHUSDT'},
    symbol='ETHUSDT'
)

# Execute the decision
result = conflict_manager.execute_conflict_resolution(
    account_name='apifan',
    client=bybit_client,
    decision=decision,
    new_signal={'action': 'SELL', 'symbol': 'ETHUSDT'}
)

print(f"Decision: {decision}")
print(f"Result: {result}")
"""