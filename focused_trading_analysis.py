#!/usr/bin/env python3
"""
Focused Trading Analysis - Mulai 21 Oktober 2025
Analisis terpisah untuk akun APIFAN dan APIARIF
"""

import json
from datetime import datetime, timedelta
import re
from collections import defaultdict
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from detailed_api_check import DetailedBybitChecker

class FocusedTradingAnalyzer:
    def __init__(self):
        self.alerts_file = "/home/clurut/logalerttradingview.txt"
        self.start_date = datetime(2025, 10, 21)  # Mulai dari 21 Oktober
        
        # API credentials
        self.apis = {
            "apifan": {
                "api_key": "GpT4GPwOXzvW8nEqhx",
                "api_secret": "SCJpSe8YIsGoKvElxxIibeLrEUVtkgnPT2xD",
                "name": "API Fan"
            },
            "apiarif": {
                "api_key": "BHnZNnIFOPvAIFlFMl", 
                "api_secret": "2lDPi5iT2wlyiJ0RB5uxGDIKZM54cJrCm2LL",
                "name": "API Arif"
            }
        }
    
    def parse_alerts_from_oct21(self):
        """Parse alerts mulai dari 21 Oktober saja"""
        alerts = []
        
        try:
            with open(self.alerts_file, 'r') as f:
                lines = f.readlines()[1:]  # Skip header
                
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Split CSV properly
                parts = []
                current_part = ""
                in_quotes = False
                
                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        parts.append(current_part.strip('"'))
                        current_part = ""
                        continue
                    current_part += char
                
                if current_part:
                    parts.append(current_part.strip('"'))
                
                if len(parts) >= 5:
                    alert_id = parts[0]
                    ticker = parts[1]
                    name = parts[2]
                    description = parts[3]
                    timestamp = parts[4].replace('Z', '')
                    
                    # Parse timestamp
                    dt = datetime.fromisoformat(timestamp)
                    
                    # Filter: hanya ambil dari 21 Oktober ke atas
                    if dt < self.start_date:
                        continue
                    
                    # Extract order info
                    order_match = re.search(r'order (buy|sell) @ ([\d.]+)', description)
                    position_match = re.search(r'New strategy position is ([-\d.]+)', description)
                    json_match = re.search(r'"action":\s*"(BUY|SELL)".*"price":\s*([\d.]+)', description)
                    
                    action = None
                    price = None
                    new_position = None
                    
                    if order_match and position_match:
                        action = order_match.group(1).upper()
                        price = float(order_match.group(2))
                        new_position = float(position_match.group(1))
                    elif json_match:
                        action = json_match.group(1)
                        price = float(json_match.group(2))
                        new_position = 0
                    
                    if action and price is not None:
                        alerts.append({
                            'alert_id': alert_id,
                            'ticker': ticker,
                            'name': name,
                            'action': action,
                            'price': price,
                            'new_position': new_position if new_position is not None else 0,
                            'timestamp': dt,
                            'date': dt.strftime('%Y-%m-%d'),
                            'time': dt.strftime('%H:%M:%S'),
                            'hour': dt.hour,
                            'description': description
                        })
        
        except Exception as e:
            print(f"❌ Error parsing alerts: {e}")
        
        return sorted(alerts, key=lambda x: x['timestamp'])
    
    def get_individual_api_data(self, api_name, credentials):
        """Get data untuk satu API saja"""
        try:
            checker = DetailedBybitChecker(credentials["api_key"], credentials["api_secret"])
            
            # Get all data
            wallet = checker.get_detailed_wallet_balance()
            positions = checker.get_all_positions()
            orders = checker.get_order_history()  # Get order history
            trades = checker.get_trade_history()  # Get trade history
            
            # Filter trades dari 21 Oktober
            filtered_trades = []
            if trades.get('retCode') == 0 and trades.get('result', {}).get('list'):
                for trade in trades['result']['list']:
                    trade_time = datetime.fromtimestamp(int(trade['execTime']) / 1000)
                    if trade_time >= self.start_date:
                        filtered_trades.append(trade)
            
            # Filter orders dari 21 Oktober
            filtered_orders = []
            if orders.get('retCode') == 0 and orders.get('result', {}).get('list'):
                for order in orders['result']['list']:
                    order_time = datetime.fromtimestamp(int(order['updatedTime']) / 1000)
                    if order_time >= self.start_date:
                        filtered_orders.append(order)
            
            return {
                'name': credentials['name'],
                'api_name': api_name,
                'wallet': wallet,
                'positions': positions,
                'orders': filtered_orders,
                'trades': filtered_trades,
                'status': 'Connected' if wallet.get('retCode') == 0 else 'Error'
            }
            
        except Exception as e:
            return {
                'name': credentials['name'],
                'api_name': api_name,
                'status': f'Error: {str(e)}',
                'error': str(e)
            }
    
    def analyze_account_performance(self, api_data):
        """Analisis performa untuk satu akun"""
        if 'error' in api_data:
            return {'error': api_data['error']}
        
        analysis = {
            'name': api_data['name'],
            'api_name': api_data['api_name']
        }
        
        # Wallet analysis
        if api_data['wallet'].get('retCode') == 0:
            wallet_list = api_data['wallet']['result']['list']
            if wallet_list:
                wallet_data = wallet_list[0]
                analysis['wallet'] = {
                    'total_equity': float(wallet_data.get('totalEquity', 0)),
                    'available_balance': float(wallet_data.get('totalAvailableBalance', 0)),
                    'unrealized_pnl': float(wallet_data.get('totalPerpUPL', 0)),
                    'wallet_balance': float(wallet_data.get('totalWalletBalance', 0))
                }
        
        # Positions analysis
        active_positions = 0
        total_unrealized_pnl = 0
        if api_data['positions'].get('retCode') == 0:
            positions_list = api_data['positions']['result']['list']
            for pos in positions_list:
                if float(pos.get('size', 0)) != 0:
                    active_positions += 1
                    total_unrealized_pnl += float(pos.get('unrealisedPnl', 0))
        
        analysis['positions'] = {
            'active_count': active_positions,
            'total_unrealized_pnl': total_unrealized_pnl
        }
        
        # Orders analysis (dari 21 Oktober)
        analysis['orders'] = {
            'total_orders': len(api_data['orders']),
            'filled_orders': len([o for o in api_data['orders'] if o.get('orderStatus') == 'Filled']),
            'cancelled_orders': len([o for o in api_data['orders'] if o.get('orderStatus') == 'Cancelled'])
        }
        
        # Trades analysis (dari 21 Oktober)
        if api_data['trades']:
            total_volume = sum(float(t.get('execValue', 0)) for t in api_data['trades'])
            total_fees = sum(float(t.get('execFee', 0)) for t in api_data['trades'])
            buy_trades = len([t for t in api_data['trades'] if t.get('side') == 'Buy'])
            sell_trades = len([t for t in api_data['trades'] if t.get('side') == 'Sell'])
            
            analysis['trades'] = {
                'total_trades': len(api_data['trades']),
                'buy_trades': buy_trades,
                'sell_trades': sell_trades,
                'total_volume': total_volume,
                'total_fees': total_fees,
                'avg_trade_size': total_volume / len(api_data['trades']) if api_data['trades'] else 0
            }
            
            # Recent trades detail
            analysis['recent_trades'] = []
            for trade in api_data['trades'][:10]:  # 10 trades terbaru
                trade_time = datetime.fromtimestamp(int(trade['execTime']) / 1000)
                analysis['recent_trades'].append({
                    'symbol': trade.get('symbol'),
                    'side': trade.get('side'),
                    'qty': float(trade.get('execQty', 0)),
                    'price': float(trade.get('execPrice', 0)),
                    'value': float(trade.get('execValue', 0)),
                    'fee': float(trade.get('execFee', 0)),
                    'time': trade_time.strftime('%Y-%m-%d %H:%M:%S')
                })
        else:
            analysis['trades'] = {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_volume': 0,
                'total_fees': 0,
                'avg_trade_size': 0
            }
            analysis['recent_trades'] = []
        
        return analysis
    
    def generate_focused_report(self):
        """Generate laporan fokus mulai 21 Oktober"""
        print("🎯 FOCUSED TRADING ANALYSIS - MULAI 21 OKTOBER 2025")
        print("=" * 80)
        
        # Parse alerts dari 21 Oktober
        print("📊 Parsing TradingView alerts dari 21 Oktober...")
        alerts = self.parse_alerts_from_oct21()
        print(f"✅ Found {len(alerts)} trading signals sejak 21 Oktober")
        
        if not alerts:
            print("❌ Tidak ada alerts ditemukan sejak 21 Oktober!")
            return
        
        # Analisis alerts
        total_signals = len(alerts)
        buy_signals = len([a for a in alerts if a['action'] == 'BUY'])
        sell_signals = len([a for a in alerts if a['action'] == 'SELL'])
        
        # Analisis per hari
        daily_counts = defaultdict(int)
        for alert in alerts:
            daily_counts[alert['date']] += 1
        
        print(f"\n📈 RINGKASAN ALERTS (21 Oktober - Sekarang)")
        print("-" * 50)
        print(f"📅 Periode: {alerts[0]['date']} sampai {alerts[-1]['date']}")
        print(f"📊 Total Signals: {total_signals}")
        print(f"🟢 Buy Signals: {buy_signals}")
        print(f"🔴 Sell Signals: {sell_signals}")
        print(f"📅 Hari Trading: {len(daily_counts)}")
        
        print(f"\n📅 DISTRIBUSI HARIAN:")
        for date, count in sorted(daily_counts.items()):
            print(f"  {date}: {count} signals")
        
        # Analisis individual per akun
        print(f"\n🔍 ANALISIS INDIVIDUAL PER AKUN")
        print("=" * 80)
        
        account_analyses = {}
        
        for api_name, credentials in self.apis.items():
            print(f"\n🔸 Menganalisis {credentials['name']} ({api_name.upper()})...")
            
            # Get API data
            api_data = self.get_individual_api_data(api_name, credentials)
            
            # Analyze performance
            analysis = self.analyze_account_performance(api_data)
            account_analyses[api_name] = analysis
            
            # Display results
            self.display_account_analysis(analysis)
        
        # Perbandingan antar akun
        print(f"\n📊 PERBANDINGAN ANTAR AKUN")
        print("=" * 80)
        self.display_account_comparison(account_analyses)
        
        # Save report
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'analysis_period': f"2025-10-21 to {datetime.now().strftime('%Y-%m-%d')}",
            'alerts_summary': {
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'daily_distribution': dict(daily_counts)
            },
            'account_analyses': account_analyses,
            'alerts_data': alerts
        }
        
        try:
            with open('/home/clurut/binance_webhook/focused_trading_report.json', 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            print(f"\n✅ Laporan disimpan ke: focused_trading_report.json")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
        
        return report_data
    
    def display_account_analysis(self, analysis):
        """Display analisis untuk satu akun"""
        if 'error' in analysis:
            name = analysis.get('name', 'Unknown Account')
            print(f"❌ {name}: {analysis['error']}")
            return
        
        print(f"\n💰 {analysis['name']} ({analysis['api_name'].upper()})")
        print("-" * 40)
        
        # Wallet info
        if 'wallet' in analysis:
            wallet = analysis['wallet']
            print(f"💰 Total Equity: ${wallet['total_equity']:.2f}")
            print(f"📊 Available Balance: ${wallet['available_balance']:.2f}")
            print(f"📈 Unrealized PnL: ${wallet['unrealized_pnl']:.2f}")
            print(f"💼 Wallet Balance: ${wallet['wallet_balance']:.2f}")
        
        # Positions
        if 'positions' in analysis:
            pos = analysis['positions']
            print(f"📊 Active Positions: {pos['active_count']}")
            if pos['total_unrealized_pnl'] != 0:
                print(f"📈 Total Unrealized PnL: ${pos['total_unrealized_pnl']:.2f}")
        
        # Orders (sejak 21 Oktober)
        if 'orders' in analysis:
            orders = analysis['orders']
            print(f"📋 Total Orders (sejak 21 Okt): {orders['total_orders']}")
            print(f"✅ Filled Orders: {orders['filled_orders']}")
            print(f"❌ Cancelled Orders: {orders['cancelled_orders']}")
        
        # Trades (sejak 21 Oktober)
        if 'trades' in analysis:
            trades = analysis['trades']
            print(f"💹 Total Trades (sejak 21 Okt): {trades['total_trades']}")
            if trades['total_trades'] > 0:
                print(f"🟢 Buy Trades: {trades['buy_trades']}")
                print(f"🔴 Sell Trades: {trades['sell_trades']}")
                print(f"💰 Total Volume: ${trades['total_volume']:.2f}")
                print(f"💸 Total Fees: ${trades['total_fees']:.4f}")
                print(f"📊 Avg Trade Size: ${trades['avg_trade_size']:.2f}")
                
                # Recent trades
                if analysis.get('recent_trades'):
                    print(f"\n📈 5 Trades Terbaru:")
                    for i, trade in enumerate(analysis['recent_trades'][:5], 1):
                        side_emoji = "🟢" if trade['side'] == 'Buy' else "🔴"
                        print(f"  {i}. {side_emoji} {trade['time']} | {trade['side']} {trade['qty']:.3f} {trade['symbol']} @ ${trade['price']:.2f}")
    
    def display_account_comparison(self, account_analyses):
        """Display perbandingan antar akun"""
        print(f"\n📊 RINGKASAN PERBANDINGAN:")
        print("-" * 50)
        
        total_equity = 0
        total_trades = 0
        total_volume = 0
        total_fees = 0
        
        for api_name, analysis in account_analyses.items():
            if 'error' not in analysis:
                if 'wallet' in analysis:
                    equity = analysis['wallet']['total_equity']
                    total_equity += equity
                    print(f"💰 {analysis['name']}: ${equity:.2f}")
                
                if 'trades' in analysis:
                    trades_count = analysis['trades']['total_trades']
                    volume = analysis['trades']['total_volume']
                    fees = analysis['trades']['total_fees']
                    
                    total_trades += trades_count
                    total_volume += volume
                    total_fees += fees
                    
                    print(f"📊 {analysis['name']}: {trades_count} trades, ${volume:.2f} volume")
        
        print(f"\n🎯 TOTAL GABUNGAN:")
        print(f"💰 Total Equity: ${total_equity:.2f}")
        print(f"📊 Total Trades: {total_trades}")
        print(f"💰 Total Volume: ${total_volume:.2f}")
        print(f"💸 Total Fees: ${total_fees:.4f}")
        
        if total_trades > 0:
            print(f"📈 Avg Trade Size: ${total_volume / total_trades:.2f}")

if __name__ == "__main__":
    analyzer = FocusedTradingAnalyzer()
    analyzer.generate_focused_report()