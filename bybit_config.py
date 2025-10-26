"""
🎯 SNIPER BYBIT PRODUCTION - Configuration
Konfigurasi untuk Bybit Production Trading Bot dengan Modal $30
Author: Sniper AI Trading Agent
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BybitProductionConfig:
    """Bybit Production Configuration untuk Modal $30"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sniper-bybit-production-2024'
    DEBUG = False  # Production mode
    
    # Bybit API Configuration
    BYBIT_API_KEY = os.environ.get('BYBIT_API_KEY')
    BYBIT_SECRET_KEY = os.environ.get('BYBIT_SECRET_KEY')
    BYBIT_TESTNET = False  # Production mode
    
    # Bybit URLs
    BYBIT_MAINNET_URL = 'https://api.bybit.com'
    BYBIT_TESTNET_URL = 'https://api-testnet.bybit.com'
    
    # Contract Specifications (OPTIMIZED FOR 0.03 ETH TARGET)
    CONTRACT_SPECS = {
        'ETHUSDT': {
            'minOrderQty': 0.03,       # Minimum order quantity (optimized to 0.03 ETH target)
            'maxOrderQty': 100.0,      # Maximum order quantity  
            'qtyStep': 0.001,          # Quantity step size
            'minNotionalValue': 1.0,   # Minimum notional value in USDT
            'tickSize': 0.01           # Price tick size
        }
    }
    
    # Trading Configuration - ETHUSDT Perpetual Focus
    TARGET_SYMBOL = 'ETHUSDT'
    ACCOUNT_BALANCE = 29.74  # $29.74 modal
    
    # Professional Risk Management - Metode Sniper (OPTIMIZED)
    RISK_PER_TRADE = 0.025  # 2.5% risk per trade = $0.74 per trade (optimized)
    MAX_POSITION_SIZE = 0.08  # 8% max equity exposure per position
    LEVERAGE = 10  # 10x leverage untuk ETHUSDT
    
    # Sniper Method - Professional Calculations (OPTIMIZED)
    SNIPER_CONFIG = {
        'min_confidence': 0.35,  # 35% minimum confidence (increased selectivity)
        'atr_multiplier': 2.2,   # 2.2x ATR multiplier untuk SL (wider stops)
        'risk_reward_ratio': 1.5, # 1:1.5 Risk-Reward (optimized - reduced from 2.0)
        'cooldown_bars': 15,     # 15 bar cooldown (reduced overtrading)
        'max_trades_per_day': 6, # Maximum 6 trades per day (quality over quantity)
        'position_sizing_method': 'fixed_risk'  # Fixed risk per trade
    }
    
    # Multi-Timeframe Analysis
    TIMEFRAME_CONFIG = {
        'entry_tf': '1h',        # Entry timeframe (updated for better accuracy)
        'trend_tf': '4h',        # Trend confirmation timeframe
        'htf_tf': '1d',          # Higher timeframe trend
        'supported_tf': ['15m', '1h', '4h', '1d']
    }
    
    # Technical Indicators - Sniper Method
    INDICATORS = {
        'ema_fast': 20,          # EMA 20 untuk trend lokal
        'ema_slow': 60,          # EMA 60 untuk trend confirmation
        'rsi_period': 14,        # RSI period
        'rsi_oversold': 25,      # RSI oversold level
        'rsi_overbought': 75,    # RSI overbought level
        'atr_period': 14         # ATR period untuk volatility
    }
    
    # Position Sizing Calculation
    def calculate_position_size(self, entry_price, stop_loss_price):
        """
        Calculate position size based on fixed risk
        Formula: Position Size = (Account Balance * Risk%) / (Entry Price - Stop Loss Price)
        """
        risk_amount = self.ACCOUNT_BALANCE * self.RISK_PER_TRADE
        price_diff = abs(entry_price - stop_loss_price)
        
        if price_diff == 0:
            return 0
        
        position_size = risk_amount / price_diff
        max_position = (self.ACCOUNT_BALANCE * self.MAX_POSITION_SIZE) / entry_price
        
        return min(position_size, max_position)
    
    # Take Profit & Stop Loss Configuration
    TP_SL_CONFIG = {
        'sl_method': 'atr_based',   # ATR-based SL (ENABLED)
        'tp_method': 'risk_reward', # Risk-reward based TP (ENABLED)
        'trailing_sl': False,       # Trailing SL (DISABLED for stability)
        'partial_tp': True,         # Partial take profit (ENABLED)
        'sl_buffer': 0.0005,        # 0.05% buffer untuk SL
        'tp_buffer': 0.0005,        # 0.05% buffer untuk TP
        # Partial TP Levels (untuk mengurangi jarak TP yang terlalu jauh)
        'partial_tp_levels': [
            {'ratio': 1.0, 'percentage': 50},  # TP1: 1.0 R:R, close 50% posisi
            {'ratio': 1.5, 'percentage': 30},  # TP2: 1.5 R:R, close 30% posisi  
            {'ratio': 2.0, 'percentage': 20}   # TP3: 2.0 R:R, close 20% posisi
        ]
    }
    
    # CONSERVATIVE SCALPING CONFIG - FOR SMALL CAPITAL ($65-70)
    SCALPING_CONFIG = {
        'enabled': True,
        'target_profit_pct': 0.02,      # 2% target profit ⭐
        'max_risk_pct': 0.015,          # 1.5% max risk per trade ⭐
        'min_account_balance': 50.0,    # Minimum balance to continue trading
        'position_sizing_method': 'conservative_fixed',  # Conservative approach
        'min_position_size': 0.01,      # Minimum position size (ETHUSDT)
        'max_position_size': 0.05,      # Maximum position size for safety
        'daily_profit_target': 0.05,    # 5% daily profit target (realistic)
        'daily_loss_limit': 0.08,       # 8% daily loss limit (capital protection)
        'max_consecutive_losses': 3,    # Stop after 3 consecutive losses
        'cooldown_after_loss': 30,      # 30 minutes cooldown after loss
        'balance_protection': {
            'stop_trading_below': 45.0,  # Stop trading if balance < $45
            'emergency_exit_pct': 0.05,  # Emergency exit if 5% daily loss
            'max_drawdown_pct': 0.15     # Maximum 15% drawdown allowed
        }
    }
    
    # Confluence Scoring System
    CONFLUENCE_WEIGHTS = {
        'trend_alignment': 2.0,      # Trend alignment weight
        'mtf_alignment': 1.5,        # Multi-timeframe alignment
        'sr_zone': 1.5,              # Support/Resistance zone
        'price_action': 1.0,         # Price action pattern
        'rsi_signal': 1.0,           # RSI signal
        'divergence': 2.0            # Divergence signal
    }
    
    # Webhook Security
    AUTH_TOKEN = os.environ.get('BYBIT_AUTH_TOKEN') or 'sniper-bybit-production-2024'
    ALLOWED_IPS = os.environ.get('ALLOWED_IPS', '').split(',') if os.environ.get('ALLOWED_IPS') else []
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'bybit_production.log'
    TRADE_LOG_FILE = 'bybit_trades.log'
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = 30
    COOLDOWN_SECONDS = 60  # 1 minute cooldown between trades
    
    # Emergency Settings
    MAX_DAILY_LOSS = 0.10  # 10% maximum daily loss ($3)
    MAX_DRAWDOWN = 0.20    # 20% maximum drawdown ($6)
    EMERGENCY_STOP = True  # Emergency stop pada max loss
    
    @classmethod
    def get_bybit_base_url(cls):
        """Get appropriate Bybit base URL"""
        if cls.BYBIT_TESTNET:
            return cls.BYBIT_TESTNET_URL
        return cls.BYBIT_MAINNET_URL
    
    @classmethod
    def validate_config(cls):
        """Validate configuration"""
        errors = []
        
        if not cls.BYBIT_API_KEY:
            errors.append("BYBIT_API_KEY is required for production")
        
        if not cls.BYBIT_SECRET_KEY:
            errors.append("BYBIT_SECRET_KEY is required for production")
        
        if cls.ACCOUNT_BALANCE <= 0:
            errors.append("ACCOUNT_BALANCE must be greater than 0")
        
        if cls.RISK_PER_TRADE <= 0 or cls.RISK_PER_TRADE > 0.05:
            errors.append("RISK_PER_TRADE must be between 0 and 0.05 (5%) for $30 account - Current: 4% (Optimized)")
        
        return errors
    
    @classmethod
    def get_position_info(cls, signal_type, entry_price, atr_value):
        """
        Calculate complete position information
        """
        # Calculate Stop Loss based on ATR
        if signal_type.upper() == 'BUY':
            stop_loss = entry_price - (atr_value * cls.SNIPER_CONFIG['atr_multiplier'])
        else:  # SELL
            stop_loss = entry_price + (atr_value * cls.SNIPER_CONFIG['atr_multiplier'])
        
        # Calculate position size
        risk_amount = cls.ACCOUNT_BALANCE * cls.RISK_PER_TRADE
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            position_size = 0
        else:
            position_size = risk_amount / price_diff
            max_position = (cls.ACCOUNT_BALANCE * cls.MAX_POSITION_SIZE) / entry_price
            position_size = min(position_size, max_position)
        
        # Apply minimum position size and quantity step validation
        contract_spec = cls.CONTRACT_SPECS.get(cls.TARGET_SYMBOL, {})
        min_qty = contract_spec.get('minOrderQty', 0.001)
        qty_step = contract_spec.get('qtyStep', 0.001)
        min_notional = contract_spec.get('minNotionalValue', 1.0)
        
        # Ensure position size meets minimum requirements
        if position_size < min_qty:
            position_size = min_qty
        
        # Round to proper quantity step
        position_size = round(position_size / qty_step) * qty_step
        
        # Ensure minimum notional value is met
        notional_value = position_size * entry_price
        if notional_value < min_notional:
            position_size = min_notional / entry_price
            position_size = round(position_size / qty_step) * qty_step
        
        # Calculate Take Profit
        risk_amount = abs(entry_price - stop_loss)
        reward_amount = risk_amount * cls.SNIPER_CONFIG['risk_reward_ratio']
        
        if signal_type.upper() == 'BUY':
            take_profit = entry_price + reward_amount
        else:  # SELL
            take_profit = entry_price - reward_amount
        
        return {
            'symbol': cls.TARGET_SYMBOL,
            'side': signal_type.upper(),
            'entry_price': entry_price,
            'position_size': round(position_size, 4),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'risk_amount': round(risk_amount * position_size, 2),
            'reward_amount': round(reward_amount * position_size, 2),
            'risk_reward_ratio': cls.SNIPER_CONFIG['risk_reward_ratio']
        }

# 🚀 ENHANCED TRADING CONFIGURATION (Added: 24 Oct 2025)
# Solusi untuk TP lama dan sinyal konflik
class EnhancedTradingConfig:
    """Enhanced configuration for faster TP and conflict management"""
    
    # Enhanced TP/SL Configuration
    ENHANCED_TP_CONFIG = {
        'enabled': True,
        'faster_tp_ratio': 1.2,  # Faster TP: 1.2:1 vs 1.5:1
        'optimized_sl_multiplier': 1.8,  # Tighter SL: 1.8x ATR vs 2.2x ATR
        'multi_level_tp': True,
        'tp_levels': [
            {'ratio': 0.8, 'percentage': 40},  # TP1: 40% at 0.8:1
            {'ratio': 1.2, 'percentage': 35},  # TP2: 35% at 1.2:1
            {'ratio': 1.6, 'percentage': 25}   # TP3: 25% at 1.6:1
        ]
    }
    
    # Conflict Management Configuration
    CONFLICT_MANAGEMENT = {
        'enabled': True,
        'auto_reversal_enabled': True,
        'profit_threshold_for_partial_close': 5.0,  # $5 profit
        'loss_threshold_for_reversal': 3.0,  # $3 loss
        'daily_reversal_limit': 3,  # Max 3 reversals per day per account
        'hold_threshold': 3.0  # Hold position if loss > $3
    }
    
    # Optimized Risk Management for Small Accounts ($66)
    SMALL_ACCOUNT_CONFIG = {
        'enabled': True,
        'balance_threshold': 100.0,  # Apply if balance < $100
        'reduced_risk_per_trade': 0.02,  # 2% vs 2.5%
        'max_equity_exposure': 0.06,  # 6% vs 10%
        'min_position_size': 0.03,  # ETHUSDT minimum
        'enhanced_risk_calculation': True
    }
    
    @classmethod
    def get_enhanced_tp_sl(cls, entry_price: float, signal_type: str, atr: float, account_balance: float = None):
        """Calculate enhanced TP/SL with faster ratios"""
        
        # Use enhanced configuration
        config = cls.ENHANCED_TP_CONFIG
        
        # Calculate enhanced SL (tighter)
        sl_distance = atr * config['optimized_sl_multiplier']
        
        if signal_type.upper() == 'BUY':
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + (sl_distance * config['faster_tp_ratio'])
        else:  # SELL
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - (sl_distance * config['faster_tp_ratio'])
        
        # Calculate multi-level TPs if enabled
        tp_levels = []
        if config['multi_level_tp']:
            for level in config['tp_levels']:
                if signal_type.upper() == 'BUY':
                    tp_price = entry_price + (sl_distance * level['ratio'])
                else:
                    tp_price = entry_price - (sl_distance * level['ratio'])
                
                tp_levels.append({
                    'price': round(tp_price, 2),
                    'percentage': level['percentage'],
                    'ratio': level['ratio']
                })
        
        return {
            'entry_price': entry_price,
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'tp_levels': tp_levels,
            'enhanced': True,
            'faster_ratio': config['faster_tp_ratio']
        }
    
    @classmethod
    def get_enhanced_position_size(cls, entry_price: float, stop_loss: float, account_balance: float):
        """Calculate enhanced position size with small account optimization"""
        
        small_config = cls.SMALL_ACCOUNT_CONFIG
        
        # Check if small account optimization should be applied
        if small_config['enabled'] and account_balance < small_config['balance_threshold']:
            risk_per_trade = small_config['reduced_risk_per_trade']
            max_exposure = small_config['max_equity_exposure']
        else:
            risk_per_trade = 0.025  # Default 2.5%
            max_exposure = 0.10  # Default 10%
        
        # Calculate position size
        risk_amount = account_balance * risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff <= 0:
            return small_config['min_position_size']
        
        position_size = risk_amount / price_diff
        
        # Apply maximum exposure limit
        max_position = (account_balance * max_exposure) / entry_price
        position_size = min(position_size, max_position)
        
        # Ensure minimum position size
        position_size = max(position_size, small_config['min_position_size'])
        
        # Calculate final risk percentage
        final_risk = (position_size * price_diff) / account_balance
        
        return {
            'position_size': round(position_size, 3),
            'risk_amount': round(position_size * price_diff, 2),
            'risk_percentage': round(final_risk * 100, 2),
            'enhanced': True,
            'small_account_optimized': account_balance < small_config['balance_threshold']
        }