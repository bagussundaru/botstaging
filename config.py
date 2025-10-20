"""
🎯 SNIPER WEBHOOK - Configuration
Konfigurasi untuk Binance Futures Trading Bot
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sniper-webhook-secret-key-2024'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Binance API Configuration
    BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.environ.get('BINANCE_SECRET_KEY')
    BINANCE_TESTNET = os.environ.get('BINANCE_TESTNET', 'True').lower() == 'true'
    
    # Binance Futures Testnet URLs
    BINANCE_FUTURES_TESTNET_URL = 'https://testnet.binancefuture.com'
    BINANCE_FUTURES_MAINNET_URL = 'https://fapi.binance.com'
    
    # Trading Configuration - Multi-Symbol Support
    TARGET_SYMBOLS = ['ETHUSDT', 'SOLANAUSDT', 'BTCUSDT']  # Support multiple symbols
    DEFAULT_SYMBOL = 'ETHUSDT'  # Primary symbol untuk trading
    
    # Multi-Timeframe Configuration
    SUPPORTED_TIMEFRAMES = {
        '1m': {'name': '1 minute', 'scalping': True},
        '3m': {'name': '3 minutes', 'scalping': True},
        '5m': {'name': '5 minutes', 'scalping': True},
        '15m': {'name': '15 minutes', 'sniper': True},
        '1h': {'name': '1 hour', 'swing': True},
        '5': '5m',  # TradingView format mapping
        '15': '15m',  # TradingView format mapping
        '60': '1h'   # TradingView format mapping
    }
    
    # Hybrid Strategy Configuration - OPTIMIZED FOR HIGHER EXECUTION RATE
    TRADING_MODES = {
        'scalping': {
            'timeframes': ['1m', '3m', '5m'],
            'min_confidence': 0.05,  # 5% for scalping (lebih agresif)
            'target_profit': 0.005,  # 0.5% target
            'stop_loss': 0.003,      # 0.3% stop loss
            'max_trades_per_hour': 15  # Dinaikkan dari 10
        },
        'sniper': {
            'timeframes': ['15m'],
            'min_confidence': 0.05,  # 5% for sniper (turun dari 10%)
            'target_profit': 0.02,   # 2% target
            'stop_loss': 0.01,       # 1% stop loss
            'max_trades_per_hour': 8  # Dinaikkan dari 4 ke 8
        },
        'swing': {
            'timeframes': ['1h'],
            'min_confidence': 0.07,  # 7% for swing (turun dari 10%)
            'target_profit': 0.05,   # 5% target
            'stop_loss': 0.02,       # 2% stop loss
            'max_trades_per_hour': 4  # Dinaikkan dari 2 ke 4
        }
    }
    
    # Symbol-specific confidence thresholds - OPTIMIZED FOR HIGHER EXECUTION
    SYMBOL_SPECIFIC_CONFIG = {
        'ETHUSDT': {
            'min_confidence': 0.03,      # Turun dari 0.08 ke 0.03 (3%)
            'cooldown_bars': 1,          # Turun dari 2 ke 1 bar
            'rsi_long_threshold': 45,    # Lebih fleksibel (dari 40)
            'rsi_short_threshold': 55,   # Lebih fleksibel (dari 60)
            'max_position_size': 0.1,    # Tetap 0.1 ETH
            'stop_loss_pct': 0.008,      # Turun dari 1% ke 0.8%
            'take_profit_pct': 0.025,    # Turun dari 3% ke 2.5%
            'volatility_multiplier': 1.2, # Tetap
            'quantity_precision': 3      # Tetap
        }
    }
    
    # Legacy Configuration (for backward compatibility)
    TARGET_SYMBOL = 'ETHUSDT'  # Fokus pada ETHUSDT
    MIN_CONFIDENCE = 0.30  # 30% minimum confidence (adjusted for TradingView alerts)
    RISK_PER_TRADE = 0.02  # 2% risk per trade
    MAX_POSITION_SIZE = 0.95  # 95% max equity exposure
    
    # Risk Management
    DEFAULT_LEVERAGE = 10  # 10x leverage
    STOP_LOSS_PERCENTAGE = 0.02  # 2% stop loss
    TAKE_PROFIT_RATIO = 2.0  # 1:2 Risk-Reward ratio
    
    # Webhook Security
    AUTH_TOKEN = os.environ.get('AUTH_TOKEN') or 'sniper-auth-token-2024'
    ALLOWED_IPS = os.environ.get('ALLOWED_IPS', '').split(',') if os.environ.get('ALLOWED_IPS') else []
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'trading_bot.log'
    
    # Timezone Configuration
    TIMEZONE = 'Asia/Jakarta'  # UTC+7 (WIB - Waktu Indonesia Barat)
    TIMEZONE_OFFSET = 7  # UTC+7 offset in hours
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = 60
    COOLDOWN_SECONDS = 30  # Cooldown between trades
    
    # Position Management
    AUTO_CLOSE_ON_REVERSE = True  # Auto close position on reverse signal
    PARTIAL_CLOSE_ENABLED = False  # Partial position closing
    
    @classmethod
    def get_binance_base_url(cls):
        """Get appropriate Binance base URL"""
        if cls.BINANCE_TESTNET:
            return cls.BINANCE_FUTURES_TESTNET_URL
        return cls.BINANCE_FUTURES_MAINNET_URL
    
    @classmethod
    def validate_config(cls):
        """Validate configuration"""
        errors = []
        
        if not cls.BINANCE_API_KEY:
            errors.append("BINANCE_API_KEY is required")
        
        if not cls.BINANCE_SECRET_KEY:
            errors.append("BINANCE_SECRET_KEY is required")
        
        if cls.RISK_PER_TRADE <= 0 or cls.RISK_PER_TRADE > 0.1:
            errors.append("RISK_PER_TRADE must be between 0 and 0.1 (10%)")
        
        if cls.MIN_CONFIDENCE < 0.1 or cls.MIN_CONFIDENCE > 1.0:
            errors.append("MIN_CONFIDENCE must be between 0.1 and 1.0")
        
        return errors

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    BINANCE_TESTNET = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    BINANCE_TESTNET = False  # Set to True if using testnet in production

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    BINANCE_TESTNET = True
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}