#!/bin/bash

# Script untuk mengecek status bot dan dashboard

echo "🔍 Checking Sniper Bot services status..."
echo ""

# Check webhook bot
WEBHOOK_PIDS=$(pgrep -f "bybit_webhook_app.py")
if [ ! -z "$WEBHOOK_PIDS" ]; then
    echo "📡 Webhook Bot: ✅ RUNNING (PIDs: $WEBHOOK_PIDS)"
    echo "   URL: http://localhost:5001/status"
    
    # Test webhook response
    WEBHOOK_STATUS=$(curl -s http://localhost:5001/status 2>/dev/null | jq -r '.status' 2>/dev/null || echo "unknown")
    echo "   Status: $WEBHOOK_STATUS"
else
    echo "📡 Webhook Bot: ❌ NOT RUNNING"
fi

echo ""

# Check dashboard
DASHBOARD_PIDS=$(pgrep -f "dashboard_live.py")
if [ ! -z "$DASHBOARD_PIDS" ]; then
    echo "📊 Dashboard: ✅ RUNNING (PIDs: $DASHBOARD_PIDS)"
    echo "   URL: http://localhost:3000"
else
    echo "📊 Dashboard: ❌ NOT RUNNING"
fi

echo ""

# Check ports
echo "🔌 Port Status:"
ss -tlnp | grep -E "(5001|3000)" | while read line; do
    if echo "$line" | grep -q "5001"; then
        echo "   Port 5001 (Webhook): ✅ LISTENING"
    elif echo "$line" | grep -q "3000"; then
        echo "   Port 3000 (Dashboard): ✅ LISTENING"
    fi
done

echo ""
echo "📋 Recent logs:"
echo "   Webhook: tail -f bybit_webhook.log"
echo "   Dashboard: tail -f dashboard_live.log"