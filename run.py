#!/usr/bin/env python3
"""
🎯 SNIPER WEBHOOK - Application Runner
Start the Binance Futures Trading Bot webhook server
"""

import os
import sys
from app import app, logger
from config import Config

def main():
    """Main function to run the application"""
    
    # Validate configuration
    config_errors = Config.validate_config()
    if config_errors:
        logger.error("❌ Configuration errors:")
        for error in config_errors:
            logger.error(f"   - {error}")
        sys.exit(1)
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info("🎯 SNIPER WEBHOOK TRADING BOT")
    logger.info("=" * 50)
    logger.info(f"🚀 Starting server on {host}:{port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"🏦 Binance Testnet: {Config.BINANCE_TESTNET}")
    logger.info(f"📊 Target Symbol: {Config.TARGET_SYMBOL}")
    logger.info(f"🎯 Min Confidence: {Config.MIN_CONFIDENCE:.0%}")
    logger.info(f"⚠️  Risk per Trade: {Config.RISK_PER_TRADE:.1%}")
    logger.info("=" * 50)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()