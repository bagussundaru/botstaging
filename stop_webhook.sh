#!/bin/bash

# Sniper Webhook Trading Bot Stop Script
# Author: Sniper AI Trading Agent

echo "🛑 Stopping Sniper Webhook Trading Bot..."

# Check if running
if pgrep -f "python3 app.py" > /dev/null; then
    # Get PID
    PID=$(pgrep -f "python3 app.py")
    echo "🔍 Found webhook process with PID: $PID"
    
    # Stop the process
    pkill -f "python3 app.py"
    
    # Wait for graceful shutdown
    sleep 2
    
    # Check if stopped
    if ! pgrep -f "python3 app.py" > /dev/null; then
        echo "✅ Webhook stopped successfully"
    else
        echo "⚠️  Force killing webhook process..."
        pkill -9 -f "python3 app.py"
        echo "✅ Webhook force stopped"
    fi
else
    echo "ℹ️  Webhook is not running"
fi