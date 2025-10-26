"""
WEBHOOK ENHANCED PATCH
Patch untuk mengintegrasikan Enhanced Multi-Account Executor ke webhook
Solusi untuk TP lama dan sinyal konflik
"""

import logging
from enhanced_multi_executor import EnhancedMultiAccountExecutor

logger = logging.getLogger(__name__)

class WebhookEnhancedPatch:
    """Patch untuk webhook dengan enhanced executor"""
    
    def __init__(self):
        self.enhanced_executor = None
        logger.info("🚀 Webhook Enhanced Patch initialized")
    
    def patch_webhook_app(self, webhook_app_instance):
        """Apply patch to existing webhook app"""
        
        # Initialize enhanced executor
        self.enhanced_executor = EnhancedMultiAccountExecutor('ETHUSDT')
        
        # Store original method
        webhook_app_instance._original_execute_multi_account = getattr(
            webhook_app_instance, 'execute_multi_account_signal', None
        )
        
        # Patch the method
        webhook_app_instance.execute_multi_account_signal = self._enhanced_execute_multi_account
        webhook_app_instance.enhanced_executor = self.enhanced_executor
        
        logger.info("✅ Webhook patched with enhanced multi-account executor")
        logger.info("🎯 Features enabled: Conflict management, Optimized TP/SL, Faster profits")
    
    def _enhanced_execute_multi_account(self, signal_data: dict) -> dict:
        """Enhanced multi-account execution with conflict management"""
        
        try:
            logger.info("🚀 Enhanced multi-account execution started")
            logger.info(f"📊 Signal: {signal_data.get('action')} {signal_data.get('symbol')}")
            
            # Import clients (assuming they're available in the webhook app)
            from bybit_webhook_app import BybitWebhookApp
            
            # Get accounts from environment
            import os
            from dotenv import load_dotenv
            from bybit_client import BybitProductionClient
            
            load_dotenv()
            
            accounts = {}
            
            # APIFAN account
            apifan_key = os.getenv('BYBIT_APIFAN_API_KEY')
            apifan_secret = os.getenv('BYBIT_APIFAN_SECRET_KEY')
            if apifan_key and apifan_secret:
                accounts['apifan'] = BybitProductionClient(apifan_key, apifan_secret)
                logger.info("✅ APIFAN client initialized")
            
            # APIARIF account
            apiarif_key = os.getenv('BYBIT_APIARIF_API_KEY')
            apiarif_secret = os.getenv('BYBIT_APIARIF_SECRET_KEY')
            if apiarif_key and apiarif_secret:
                accounts['apiarif'] = BybitProductionClient(apiarif_key, apiarif_secret)
                logger.info("✅ APIARIF client initialized")
            
            if not accounts:
                return {
                    'success': False,
                    'error': 'No valid accounts configured',
                    'enhanced': True
                }
            
            # Execute with enhanced executor
            result = self.enhanced_executor.execute_signal(signal_data, accounts)
            
            # Add enhanced flag
            result['enhanced'] = True
            result['features'] = [
                'conflict_management',
                'optimized_tp_sl',
                'faster_profits',
                'multi_level_tp'
            ]
            
            # Log enhanced results
            logger.info(f"🎯 Enhanced execution completed: {result['success_rate']} success rate")
            
            if result['conflict_resolutions']:
                logger.info("🔄 Conflict resolutions applied:")
                for resolution in result['conflict_resolutions']:
                    logger.info(f"  - {resolution['account']}: {resolution['analysis']['action']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced execution error: {e}")
            return {
                'success': False,
                'error': f'Enhanced execution failed: {str(e)}',
                'enhanced': True
            }

# INTEGRATION INSTRUCTIONS
"""
Untuk mengintegrasikan patch ini ke webhook yang sudah ada:

1. Import patch di bybit_webhook_app.py:
   from webhook_enhanced_patch import WebhookEnhancedPatch

2. Apply patch setelah inisialisasi webhook:
   patch = WebhookEnhancedPatch()
   patch.patch_webhook_app(webhook_app_instance)

3. Atau gunakan sebagai decorator:
   @WebhookEnhancedPatch().patch_webhook_app
   class BybitWebhookApp:
       ...

BENEFITS:
- ✅ Mengatasi TP yang lama tercapai
- ✅ Menangani sinyal konflik dengan cerdas
- ✅ Optimized untuk akun $66
- ✅ Multi-level TP untuk profit maksimal
- ✅ Risk management yang lebih ketat
- ✅ Backward compatible dengan sistem lama
"""