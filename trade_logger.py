#!/usr/bin/env python3
"""
🎯 SNIPER TRADE LOGGER - Detailed Trading Analytics
Modul khusus untuk logging detail trading dengan PnL tracking dan analytics
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
from datetime_utils import DateTimeUtils, log_timestamp

class TradeLogger:
    """
    🎯 Advanced Trade Logger untuk Metode Sniper
    Mencatat semua detail trading termasuk entry, exit, dan PnL
    """
    
    def __init__(self, log_file: str = "sniper_trades.log"):
        self.log_file = log_file
        self.trades_file = "trades_history.json"
        self.active_trades = {}  # Track active positions
        
        # Setup dedicated trade logger
        self.logger = logging.getLogger('TradeLogger')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for trade logs
        trade_handler = logging.FileHandler(log_file)
        trade_handler.setLevel(logging.INFO)
        
        # Create custom formatter dengan timezone UTC+7
        class UTCPlusSevenFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                return log_timestamp()
        
        # Create formatter
        formatter = UTCPlusSevenFormatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        trade_handler.setFormatter(formatter)
        
        # Add handler to logger
        if not self.logger.handlers:
            self.logger.addHandler(trade_handler)
        
        # Initialize trades history file
        self._initialize_trades_file()
    
    def _initialize_trades_file(self):
        """Initialize trades history JSON file"""
        if not os.path.exists(self.trades_file):
            with open(self.trades_file, 'w') as f:
                json.dump({
                    "trades": [],
                    "summary": {
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "total_pnl": 0.0,
                        "win_rate": 0.0,
                        "avg_win": 0.0,
                        "avg_loss": 0.0,
                        "largest_win": 0.0,
                        "largest_loss": 0.0
                    }
                }, f, indent=2)
    
    def log_entry(self, 
                  symbol: str, 
                  action: str, 
                  quantity: float, 
                  entry_price: float,
                  order_id: str,
                  confluence_score: float,
                  confluence_factors: Dict,
                  confidence: float,
                  mode: str = "sniper",
                  timeframe: str = "15m",
                  target_profit: float = 0.0,
                  stop_loss: float = 0.0) -> str:
        """
        🎯 Log trade entry dengan detail lengkap
        Returns trade_id untuk tracking
        """
        trade_id = f"{symbol}_{order_id}_{int(DateTimeUtils.now_utc7().timestamp())}"
        entry_time = DateTimeUtils.now_utc7()
        
        trade_data = {
            "trade_id": trade_id,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "entry_price": entry_price,
            "entry_time": entry_time.isoformat(),
            "order_id": order_id,
            "confluence_score": confluence_score,
            "confluence_factors": confluence_factors,
            "confidence": confidence,
            "mode": mode,
            "timeframe": timeframe,
            "target_profit": target_profit,
            "stop_loss": stop_loss,
            "status": "OPEN",
            "exit_price": None,
            "exit_time": None,
            "pnl": 0.0,
            "pnl_percentage": 0.0,
            "duration_minutes": 0,
            "exit_reason": None
        }
        
        # Store active trade
        self.active_trades[trade_id] = trade_data
        
        # Log entry details
        self.logger.info("=" * 80)
        self.logger.info("🎯 TRADE ENTRY LOGGED")
        self.logger.info("=" * 80)
        self.logger.info(f"Trade ID: {trade_id}")
        self.logger.info(f"Symbol: {symbol}")
        self.logger.info(f"Action: {action}")
        self.logger.info(f"Quantity: {quantity}")
        self.logger.info(f"Entry Price: ${entry_price:.4f}")
        self.logger.info(f"Entry Time: {DateTimeUtils.format_utc7(entry_time)}")
        self.logger.info(f"Order ID: {order_id}")
        self.logger.info(f"Mode: {mode.upper()}")
        self.logger.info(f"Timeframe: {timeframe}")
        self.logger.info(f"Target Profit: {target_profit:.1%}")
        self.logger.info(f"Stop Loss: {stop_loss:.1%}")
        self.logger.info(f"Confluence Score: {confluence_score:.1f}%")
        self.logger.info(f"Confidence: {confidence:.1%}")
        self.logger.info("Confluence Factors:")
        for factor, score in confluence_factors.items():
            status = "✅" if score > 0 else "❌"
            self.logger.info(f"  {status} {factor.replace('_', ' ').title()}: {score:.2f}")
        self.logger.info("=" * 80)
        
        return trade_id
    
    def log_exit(self, 
                 trade_id: str, 
                 exit_price: float, 
                 exit_reason: str = "MANUAL",
                 exit_order_id: Optional[str] = None) -> Dict:
        """
        🎯 Log trade exit dan hitung PnL
        """
        if trade_id not in self.active_trades:
            self.logger.error(f"❌ Trade ID {trade_id} not found in active trades")
            return {"status": "error", "message": "Trade not found"}
        
        trade_data = self.active_trades[trade_id]
        exit_time = DateTimeUtils.now_utc7()
        
        # Parse entry time dengan timezone awareness
        entry_time_str = trade_data["entry_time"]
        if entry_time_str.endswith('+07:00'):
            entry_time = datetime.fromisoformat(entry_time_str)
        else:
            # Backward compatibility untuk old format
            entry_time = datetime.fromisoformat(entry_time_str)
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=DateTimeUtils.UTC_PLUS_7)
        
        # Calculate duration
        duration = exit_time - entry_time
        duration_minutes = duration.total_seconds() / 60
        
        # Calculate PnL
        entry_price = trade_data["entry_price"]
        quantity = trade_data["quantity"]
        action = trade_data["action"]
        
        if action == "BUY":
            # Long position: profit when price goes up
            pnl = (exit_price - entry_price) * quantity
        else:
            # Short position: profit when price goes down
            pnl = (entry_price - exit_price) * quantity
        
        pnl_percentage = (pnl / (entry_price * quantity)) * 100
        
        # Update trade data
        trade_data.update({
            "exit_price": exit_price,
            "exit_time": exit_time.isoformat(),
            "exit_order_id": exit_order_id,
            "exit_reason": exit_reason,
            "pnl": pnl,
            "pnl_percentage": pnl_percentage,
            "duration_minutes": duration_minutes,
            "status": "CLOSED"
        })
        
        # Log exit details
        self.logger.info("=" * 80)
        self.logger.info("🏁 TRADE EXIT LOGGED")
        self.logger.info("=" * 80)
        self.logger.info(f"Trade ID: {trade_id}")
        self.logger.info(f"Symbol: {trade_data['symbol']}")
        self.logger.info(f"Action: {action}")
        self.logger.info(f"Quantity: {quantity}")
        self.logger.info(f"Entry Price: ${entry_price:.4f}")
        self.logger.info(f"Exit Price: ${exit_price:.4f}")
        self.logger.info(f"Entry Time: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Exit Time: {exit_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Duration: {duration_minutes:.1f} minutes")
        self.logger.info(f"Exit Reason: {exit_reason}")
        if exit_order_id:
            self.logger.info(f"Exit Order ID: {exit_order_id}")
        
        # PnL Analysis
        pnl_status = "💰 PROFIT" if pnl > 0 else "💸 LOSS" if pnl < 0 else "⚖️ BREAKEVEN"
        self.logger.info("=" * 40)
        self.logger.info("📊 PnL ANALYSIS")
        self.logger.info("=" * 40)
        self.logger.info(f"Result: {pnl_status}")
        self.logger.info(f"PnL Amount: ${pnl:.4f}")
        self.logger.info(f"PnL Percentage: {pnl_percentage:.2f}%")
        self.logger.info(f"ROI: {pnl_percentage:.2f}%")
        self.logger.info("=" * 80)
        
        # Save to history and remove from active trades
        self._save_trade_to_history(trade_data)
        del self.active_trades[trade_id]
        
        # Update summary statistics
        self._update_summary_stats()
        
        return {
            "status": "success",
            "trade_data": trade_data,
            "pnl": pnl,
            "pnl_percentage": pnl_percentage,
            "duration_minutes": duration_minutes
        }
    
    def _save_trade_to_history(self, trade_data: Dict):
        """Save completed trade to history file"""
        try:
            with open(self.trades_file, 'r') as f:
                history = json.load(f)
            
            history["trades"].append(trade_data)
            
            with open(self.trades_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving trade to history: {e}")
    
    def _update_summary_stats(self):
        """Update summary statistics"""
        try:
            with open(self.trades_file, 'r') as f:
                history = json.load(f)
            
            trades = history["trades"]
            if not trades:
                return
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t["pnl"] > 0])
            losing_trades = len([t for t in trades if t["pnl"] < 0])
            
            total_pnl = sum(t["pnl"] for t in trades)
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            winning_pnls = [t["pnl"] for t in trades if t["pnl"] > 0]
            losing_pnls = [t["pnl"] for t in trades if t["pnl"] < 0]
            
            avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
            avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0
            largest_win = max(winning_pnls) if winning_pnls else 0
            largest_loss = min(losing_pnls) if losing_pnls else 0
            
            # Update summary
            history["summary"] = {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "total_pnl": total_pnl,
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "largest_win": largest_win,
                "largest_loss": largest_loss,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.trades_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            # Log updated summary
            self.logger.info("📈 TRADING SUMMARY UPDATED")
            self.logger.info(f"Total Trades: {total_trades}")
            self.logger.info(f"Win Rate: {win_rate:.1f}%")
            self.logger.info(f"Total PnL: ${total_pnl:.4f}")
            self.logger.info(f"Avg Win: ${avg_win:.4f}")
            self.logger.info(f"Avg Loss: ${avg_loss:.4f}")
            
        except Exception as e:
            self.logger.error(f"❌ Error updating summary stats: {e}")
    
    def get_active_trades(self) -> Dict:
        """Get all active trades"""
        return self.active_trades.copy()
    
    def get_trade_summary(self) -> Dict:
        """Get trading summary statistics"""
        try:
            with open(self.trades_file, 'r') as f:
                history = json.load(f)
            return history["summary"]
        except Exception as e:
            self.logger.error(f"❌ Error getting trade summary: {e}")
            return {}
    
    def log_market_update(self, symbol: str, current_price: float):
        """Log market price updates for active trades"""
        for trade_id, trade_data in self.active_trades.items():
            if trade_data["symbol"] == symbol:
                entry_price = trade_data["entry_price"]
                action = trade_data["action"]
                quantity = trade_data["quantity"]
                
                # Calculate unrealized PnL
                if action == "BUY":
                    unrealized_pnl = (current_price - entry_price) * quantity
                else:
                    unrealized_pnl = (entry_price - current_price) * quantity
                
                unrealized_pnl_pct = (unrealized_pnl / (entry_price * quantity)) * 100
                
                self.logger.info(f"📊 {symbol} Market Update - Trade ID: {trade_id}")
                self.logger.info(f"   Current Price: ${current_price:.4f}")
                self.logger.info(f"   Entry Price: ${entry_price:.4f}")
                self.logger.info(f"   Unrealized PnL: ${unrealized_pnl:.4f} ({unrealized_pnl_pct:.2f}%)")