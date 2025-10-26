#!/usr/bin/env python3
"""
Script detail untuk mengecek balance dan posisi riil API Bybit
Menampilkan informasi lengkap untuk verifikasi
"""

import requests
import hmac
import hashlib
import time
import json
from urllib.parse import urlencode
from datetime import datetime

class DetailedBybitChecker:
    def __init__(self, api_key, api_secret, testnet=False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
        
    def _generate_signature(self, params, timestamp):
        """Generate signature for Bybit API"""
        param_str = f"{timestamp}{self.api_key}5000{urlencode(sorted(params.items()))}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, endpoint, params=None):
        """Make authenticated request to Bybit API"""
        if params is None:
            params = {}
            
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(params, timestamp)
        
        headers = {
            'X-BAPI-API-KEY': self.api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': '5000',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        if params:
            url += f"?{urlencode(params)}"
            
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_detailed_wallet_balance(self):
        """Get detailed wallet balance"""
        params = {"accountType": "UNIFIED"}
        result = self._make_request("/v5/account/wallet-balance", params)
        return result
    
    def get_all_positions(self):
        """Get all positions (not just ETHUSDT)"""
        params = {"category": "linear"}
        result = self._make_request("/v5/position/list", params)
        return result
    
    def get_order_history(self):
        """Get recent order history"""
        params = {"category": "linear", "limit": 20}
        result = self._make_request("/v5/order/history", params)
        return result
    
    def get_trade_history(self):
        """Get recent trade history"""
        params = {"category": "linear", "limit": 20}
        result = self._make_request("/v5/execution/list", params)
        return result
    
    def run_detailed_check(self, account_name):
        """Run detailed check with comprehensive information"""
        print(f"\n{'='*80}")
        print(f"🔍 DETAILED CHECK: {account_name.upper()}")
        print(f"🔑 API Key: {self.api_key}")
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # 1. Detailed Wallet Balance
        print(f"\n💰 WALLET BALANCE DETAILS:")
        print("-" * 50)
        wallet_result = self.get_detailed_wallet_balance()
        
        if wallet_result.get("retCode") == 0:
            wallet_data = wallet_result["result"]["list"][0]
            print(f"✅ Account Type: {wallet_data.get('accountType', 'N/A')}")
            print(f"💵 Total Equity: ${wallet_data.get('totalEquity', '0')}")
            print(f"💰 Total Wallet Balance: ${wallet_data.get('totalWalletBalance', '0')}")
            print(f"📊 Total Available Balance: ${wallet_data.get('totalAvailableBalance', '0')}")
            print(f"🔒 Total Margin Balance: ${wallet_data.get('totalMarginBalance', '0')}")
            print(f"📈 Total PnL: ${wallet_data.get('totalPerpUPL', '0')}")
            
            # Detail per coin
            print(f"\n💎 COIN DETAILS:")
            for coin in wallet_data.get('coin', []):
                if float(coin.get('walletBalance', 0)) > 0:
                    print(f"  🪙 {coin['coin']}:")
                    print(f"    💰 Wallet Balance: {coin.get('walletBalance', '0')}")
                    print(f"    📊 Available: {coin.get('availableToWithdraw', '0')}")
                    print(f"    🔒 Used Margin: {coin.get('totalOrderIM', '0')}")
                    print(f"    📈 Unrealized PnL: {coin.get('unrealisedPnl', '0')}")
        else:
            print(f"❌ Error: {wallet_result.get('retMsg', 'Unknown error')}")
        
        # 2. All Positions
        print(f"\n📊 ALL POSITIONS:")
        print("-" * 50)
        positions_result = self.get_all_positions()
        
        if positions_result.get("retCode") == 0:
            positions = positions_result["result"]["list"]
            active_positions = [p for p in positions if float(p.get('size', 0)) > 0]
            
            if active_positions:
                for pos in active_positions:
                    print(f"  📈 {pos['symbol']}:")
                    print(f"    🔄 Side: {pos.get('side', 'N/A')}")
                    print(f"    📏 Size: {pos.get('size', '0')}")
                    print(f"    💰 Entry Price: ${pos.get('avgPrice', '0')}")
                    print(f"    📊 Mark Price: ${pos.get('markPrice', '0')}")
                    print(f"    📈 Unrealized PnL: ${pos.get('unrealisedPnl', '0')}")
                    print(f"    🎯 Leverage: {pos.get('leverage', '0')}x")
                    print(f"    🛡️ Stop Loss: {pos.get('stopLoss', 'None')}")
                    print(f"    🎯 Take Profit: {pos.get('takeProfit', 'None')}")
            else:
                print("  ✅ No active positions")
        else:
            print(f"❌ Error: {positions_result.get('retMsg', 'Unknown error')}")
        
        # 3. Recent Orders
        print(f"\n📋 RECENT ORDERS (Last 20):")
        print("-" * 50)
        orders_result = self.get_order_history()
        
        if orders_result.get("retCode") == 0:
            orders = orders_result["result"]["list"]
            if orders:
                for i, order in enumerate(orders[:5]):  # Show only last 5
                    created_time = datetime.fromtimestamp(int(order['createdTime'])/1000)
                    print(f"  📝 Order {i+1}:")
                    print(f"    🎯 Symbol: {order.get('symbol', 'N/A')}")
                    print(f"    🔄 Side: {order.get('side', 'N/A')}")
                    print(f"    📏 Qty: {order.get('qty', '0')}")
                    print(f"    💰 Price: ${order.get('price', '0')}")
                    print(f"    📊 Status: {order.get('orderStatus', 'N/A')}")
                    print(f"    ⏰ Time: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
            else:
                print("  ✅ No recent orders")
        else:
            print(f"❌ Error: {orders_result.get('retMsg', 'Unknown error')}")
        
        # 4. Recent Trades
        print(f"\n💹 RECENT TRADES (Last 20):")
        print("-" * 50)
        trades_result = self.get_trade_history()
        
        if trades_result.get("retCode") == 0:
            trades = trades_result["result"]["list"]
            if trades:
                for i, trade in enumerate(trades[:5]):  # Show only last 5
                    exec_time = datetime.fromtimestamp(int(trade['execTime'])/1000)
                    print(f"  💰 Trade {i+1}:")
                    print(f"    🎯 Symbol: {trade.get('symbol', 'N/A')}")
                    print(f"    🔄 Side: {trade.get('side', 'N/A')}")
                    print(f"    📏 Qty: {trade.get('execQty', '0')}")
                    print(f"    💰 Price: ${trade.get('execPrice', '0')}")
                    print(f"    💵 Value: ${trade.get('execValue', '0')}")
                    print(f"    💸 Fee: ${trade.get('execFee', '0')}")
                    print(f"    ⏰ Time: {exec_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
            else:
                print("  ✅ No recent trades")
        else:
            print(f"❌ Error: {trades_result.get('retMsg', 'Unknown error')}")
        
        return {
            "wallet": wallet_result,
            "positions": positions_result,
            "orders": orders_result,
            "trades": trades_result
        }

def main():
    """Main function to check both APIs in detail"""
    print("🔍 DETAILED BYBIT API CHECKER")
    print("=" * 80)
    
    # API credentials
    apis = {
        "apifan": {
            "api_key": "GpT4GPwOXzvW8nEqhx",
            "api_secret": "SCJpSe8YIsGoKvElxxIibeLrEUVtkgnPT2xD"
        },
        "apiarif": {
            "api_key": "BHnZNnIFOPvAIFlFMl", 
            "api_secret": "2lDPi5iT2wlyiJ0RB5uxGDIKZM54cJrCm2LL"
        }
    }
    
    results = {}
    
    # Check each API in detail
    for account_name, credentials in apis.items():
        try:
            checker = DetailedBybitChecker(
                credentials["api_key"],
                credentials["api_secret"],
                testnet=False
            )
            results[account_name] = checker.run_detailed_check(account_name)
        except Exception as e:
            print(f"❌ Error checking {account_name}: {str(e)}")
            results[account_name] = {"error": str(e)}
    
    # Final Summary
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*80}")
    
    for account_name, result in results.items():
        print(f"\n🔸 {account_name.upper()}:")
        if "error" in result:
            print(f"  ❌ Failed: {result['error']}")
        else:
            # Wallet summary
            if result.get("wallet", {}).get("retCode") == 0:
                wallet_data = result["wallet"]["result"]["list"][0]
                total_equity = wallet_data.get('totalEquity', '0')
                available_balance = wallet_data.get('totalAvailableBalance', '0')
                print(f"  💰 Total Equity: ${total_equity}")
                print(f"  📊 Available Balance: ${available_balance}")
            
            # Position summary
            if result.get("positions", {}).get("retCode") == 0:
                positions = result["positions"]["result"]["list"]
                active_positions = [p for p in positions if float(p.get('size', 0)) > 0]
                print(f"  📈 Active Positions: {len(active_positions)}")
            
            # Order summary
            if result.get("orders", {}).get("retCode") == 0:
                orders = result["orders"]["result"]["list"]
                print(f"  📋 Recent Orders: {len(orders)}")
            
            # Trade summary
            if result.get("trades", {}).get("retCode") == 0:
                trades = result["trades"]["result"]["list"]
                print(f"  💹 Recent Trades: {len(trades)}")

if __name__ == "__main__":
    main()