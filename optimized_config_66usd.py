"""
OPTIMIZED CONFIGURATION FOR $66 USD ACCOUNTS
Solusi untuk:
1. TP lama tercapai -> Faster TP dengan risk-reward ratio yang lebih dekat
2. Sinyal konflik -> Smart conflict management
3. Profit optimization untuk modal kecil
"""

class OptimizedConfig66USD:
    """Konfigurasi optimal untuk akun $66 - Focus: Faster TP + Better Signal Management"""
    
    # ACCOUNT SETTINGS
    ACCOUNT_BALANCE = 66.0  # $66 per account
    TARGET_SYMBOL = 'ETHUSDT'
    
    # OPTIMIZED RISK MANAGEMENT - FASTER TP FOCUS
    RISK_PER_TRADE = 0.02  # 2% risk = $1.32 per trade (reduced for faster TP)
    MAX_POSITION_SIZE = 0.06  # 6% max equity exposure
    LEVERAGE = 10  # 10x leverage
    
    # FASTER TP CONFIGURATION - SOLUTION FOR SLOW TP PROBLEM
    FAST_TP_CONFIG = {
        'atr_multiplier': 1.8,   # 1.8x ATR (tighter SL = closer TP)
        'risk_reward_ratio': 1.2, # 1:1.2 RR (closer TP target)
        'scalping_mode': True,   # Enable scalping for faster profits
        'quick_tp_enabled': True, # Enable quick TP levels
        'max_hold_time': 4,      # Max 4 hours per position
    }
    
    # MULTI-LEVEL TP STRATEGY - FASTER PROFIT REALIZATION
    MULTI_LEVEL_TP = {
        'enabled': True,
        'levels': [
            {'rr_ratio': 0.8, 'close_percentage': 40},  # TP1: 40% posisi pada R:R 0.8:1 (QUICK)
            {'rr_ratio': 1.2, 'close_percentage': 35},  # TP2: 35% posisi pada R:R 1.2:1 (TARGET)
            {'rr_ratio': 1.8, 'close_percentage': 25}   # TP3: 25% posisi pada R:R 1.8:1 (BONUS)
        ]
    }
    
    # SIGNAL CONFLICT MANAGEMENT - SOLUTION FOR OPPOSING SIGNALS
    CONFLICT_MANAGEMENT = {
        'enabled': True,
        'strategy': 'smart_reversal',  # Smart reversal strategy
        'close_opposite_threshold': 0.5,  # Close if opposite signal confidence > 50%
        'partial_close_on_conflict': True,  # Close 50% on conflict
        'reversal_confirmation_required': True,  # Require confirmation for reversal
        'max_reversal_per_day': 3,  # Max 3 reversals per day
    }
    
    # POSITION MANAGEMENT RULES
    POSITION_RULES = {
        'allow_position_reversal': True,   # Allow closing + opening opposite
        'reversal_method': 'close_and_reverse',  # Close existing, then open new
        'min_profit_for_reversal': -0.5,  # Allow reversal if loss < 0.5%
        'force_close_on_strong_opposite': True,  # Force close on strong opposite signal
        'partial_close_percentage': 50,   # Close 50% on conflict
    }
    
    # SCALPING OPTIMIZATION - FOR FASTER PROFITS
    SCALPING_ENHANCED = {
        'enabled': True,
        'target_profit_pct': 1.5,      # 1.5% target profit (faster)
        'max_risk_pct': 1.5,           # 1.5% max risk per trade
        'quick_exit_enabled': True,    # Enable quick exit on profit
        'trailing_stop_enabled': True, # Enable trailing stop
        'breakeven_move': 0.8,         # Move SL to breakeven at 0.8 R:R
    }
    
    # TIME-BASED MANAGEMENT
    TIME_MANAGEMENT = {
        'max_position_duration': 4,    # Max 4 hours per position
        'force_close_before_news': True,  # Close before major news
        'avoid_weekend_holds': True,   # Close before weekend
        'session_based_trading': True, # Trade based on sessions
    }
    
    # SIGNAL FILTERING - ENHANCED
    SIGNAL_FILTERING = {
        'position_95_only': True,      # Only position 95 signals
        'confidence_threshold': 0.4,  # 40% minimum confidence
        'trend_confirmation': True,   # Require trend confirmation
        'volume_confirmation': False, # Skip volume confirmation for speed
        'rsi_filter': True,           # Use RSI filter
        'rsi_oversold': 30,           # RSI oversold level
        'rsi_overbought': 70,         # RSI overbought level
    }
    
    # EMERGENCY PROTOCOLS
    EMERGENCY_CONFIG = {
        'daily_loss_limit': 6.6,      # $6.60 daily loss limit (10%)
        'consecutive_loss_limit': 3,  # Stop after 3 consecutive losses
        'drawdown_limit': 15.0,       # 15% max drawdown
        'force_stop_conditions': [
            'daily_loss_exceeded',
            'consecutive_losses',
            'max_drawdown_reached'
        ]
    }
    
    def calculate_optimized_tp_levels(self, entry_price: float, stop_loss: float, side: str) -> dict:
        """Calculate optimized TP levels for faster profit realization"""
        
        price_diff = abs(entry_price - stop_loss)
        
        if side.upper() == 'BUY':
            tp1 = entry_price + (price_diff * 0.8)   # Quick TP
            tp2 = entry_price + (price_diff * 1.2)   # Target TP
            tp3 = entry_price + (price_diff * 1.8)   # Bonus TP
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
            'strategy': 'optimized_multi_level'
        }
    
    def calculate_optimized_position_size(self, account_balance: float, entry_price: float, stop_loss: float) -> dict:
        """Calculate optimized position size for $66 accounts"""
        
        risk_amount = account_balance * self.RISK_PER_TRADE
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff <= 0:
            return {'error': 'Invalid price difference'}
        
        base_position_size = risk_amount / price_diff
        max_position_size = (account_balance * self.MAX_POSITION_SIZE) / entry_price
        
        optimized_size = min(base_position_size, max_position_size)
        
        return {
            'position_size': round(optimized_size, 4),
            'risk_amount': risk_amount,
            'risk_percentage': self.RISK_PER_TRADE * 100,
            'max_position_percentage': self.MAX_POSITION_SIZE * 100,
            'price_diff': price_diff,
            'optimized': True
        }
    
    def should_reverse_position(self, current_side: str, new_signal_side: str, current_pnl: float) -> bool:
        """Determine if position should be reversed based on optimized criteria"""
        
        # Conditions for reversal:
        # 1. Opposite signal received
        # 2. Current loss is acceptable (< 0.5%)
        # 3. Reversal limit not exceeded
        
        if current_side != new_signal_side and current_pnl > -0.5:  # Loss < 0.5%
            return True
        
        return False

# UTILITY FUNCTIONS
def calculate_optimized_position_size(balance: float, entry_price: float, stop_loss: float) -> float:
    """Calculate position size optimized for $66 accounts"""
    
    config = OptimizedConfig66USD()
    result = config.calculate_optimized_position_size(balance, entry_price, stop_loss)
    
    if 'error' in result:
        return 0.03  # Fallback to minimum
    
    return result['position_size']

def get_optimized_tp_levels(entry_price: float, stop_loss: float, side: str) -> dict:
    """Get optimized TP levels for faster profits"""
    
    config = OptimizedConfig66USD()
    return config.calculate_optimized_tp_levels(entry_price, stop_loss, side)

def is_reversal_recommended(current_side: str, new_signal: str, pnl: float) -> bool:
    """Check if position reversal is recommended"""
    
    config = OptimizedConfig66USD()
    return config.should_reverse_position(current_side, new_signal, pnl)

# CONFIGURATION VALIDATION
def validate_config() -> bool:
    """Validate optimized configuration"""
    
    config = OptimizedConfig66USD()
    
    # Check risk parameters
    if config.RISK_PER_TRADE > 0.03:  # Max 3% risk
        return False
    
    if config.MAX_POSITION_SIZE > 0.08:  # Max 8% position size
        return False
    
    # Check TP configuration
    if config.FAST_TP_CONFIG['risk_reward_ratio'] > 2.0:  # Max 2:1 RR
        return False
    
    return True

# USAGE EXAMPLE
"""
# Initialize optimized config
config = OptimizedConfig66USD()

# Calculate optimized position size
position_info = config.calculate_optimized_position_size(66.0, 3800.0, 3720.0)
print(f"Optimized position: {position_info}")

# Get TP levels
tp_levels = config.calculate_optimized_tp_levels(3800.0, 3720.0, 'BUY')
print(f"TP levels: {tp_levels}")

# Check reversal recommendation
should_reverse = config.should_reverse_position('BUY', 'SELL', -0.3)
print(f"Should reverse: {should_reverse}")
"""