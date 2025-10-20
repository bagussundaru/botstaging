#!/bin/bash

# Sniper Webhook Trading Bot Startup Script
# Author: Sniper AI Trading Agent

echo "🎯 Starting Sniper Webhook Trading Bot..."

# Check if already running
if pgrep -f "python3 bybit_webhook_app.py" > /dev/null; then
    echo "⚠️  Webhook already running. Stopping existing process..."
    pkill -f "python3 bybit_webhook_app.py"
    sleep 2
fi

# Navigate to webhook directory
cd /home/clurut/binance_webhook

# Start webhook in background
nohup python3 bybit_webhook_app.py > app_background.log 2>&1 &

# Get process ID
PID=$!
echo "✅ Webhook started with PID: $PID"

# Wait a moment for startup
sleep 3

# Check if process is still running
if ps -p $PID > /dev/null; then
    echo "✅ Webhook is running successfully in background"
    echo "📊 Log file: app_background.log"
    echo "🌐 Webhook URL: http://103.189.234.15/webhook_v2"
    echo "🔍 Check status: ps aux | grep 'python3 app.py'"
    echo "📋 View logs: tail -f app_background.log"
    echo "🛑 Stop webhook: pkill -f 'python3 app.py'"
else
    echo "❌ Failed to start webhook. Check app_background.log for errors."
    exit 1
fi