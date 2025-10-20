#!/bin/bash

# Secure Dashboard HTTP Server Management Script
# Usage: ./manage_secure_server.sh [start|stop|status|restart]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/secure_server.log"
PID_FILE="$SCRIPT_DIR/secure_server.pid"
PORT=8080
PYTHON_SCRIPT="$SCRIPT_DIR/secure_http_server.py"

start_server() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "🔐 Secure server already running with PID $(cat $PID_FILE)"
        return 1
    fi
    
    echo "🚀 Starting secure HTTP server on port $PORT..."
    cd "$SCRIPT_DIR"
    
    # Make sure the Python script is executable
    chmod +x "$PYTHON_SCRIPT"
    
    # Start the secure server
    nohup python3 "$PYTHON_SCRIPT" $PORT > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 3
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ Secure server started successfully with PID $(cat $PID_FILE)"
        echo "🌐 Dashboard available at: http://localhost:8080/"
    echo "🌍 Public access: http://103.189.234.15:8080/"
    echo "🔑 Authentication required for access"
    echo "📝 Log file: $LOG_FILE"
        echo ""
        echo "🛡️  All files are now PROTECTED with authentication!"
        echo "🚫 No more public file exposure!"
    else
        echo "❌ Failed to start secure server. Check log: $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_server() {
    if [ ! -f "$PID_FILE" ]; then
        echo "📄 PID file not found. Server may not be running."
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "🛑 Stopping secure server with PID $PID..."
        kill "$PID"
        sleep 3
        
        if kill -0 "$PID" 2>/dev/null; then
            echo "💀 Force killing server..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ Secure server stopped successfully"
    else
        echo "⚠️  Server with PID $PID is not running"
        rm -f "$PID_FILE"
    fi
}

status_server() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo "✅ Secure server is RUNNING with PID $PID"
        echo "🌐 Local access: http://localhost:$PORT/"
        echo "🌍 Public access: http://103.189.234.15:$PORT/"
        echo "🔐 Authentication: ENABLED"
        echo "📝 Log file: $LOG_FILE"
        
        # Show recent log entries
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "📋 Recent log entries:"
            tail -n 5 "$LOG_FILE" 2>/dev/null || echo "No recent logs"
        fi
    else
        echo "❌ Secure server is NOT running"
        if [ -f "$PID_FILE" ]; then
            echo "🧹 Cleaning up stale PID file..."
            rm -f "$PID_FILE"
        fi
    fi
}

restart_server() {
    echo "🔄 Restarting secure server..."
    stop_server
    sleep 2
    start_server
}

show_help() {
    echo "🔐 Secure Dashboard Server Management"
    echo ""
    echo "Usage: $0 [start|stop|status|restart|help]"
    echo ""
    echo "Commands:"
    echo "  start   - Start the secure HTTP server with authentication"
    echo "  stop    - Stop the secure HTTP server"
    echo "  status  - Show server status and connection info"
    echo "  restart - Restart the secure HTTP server"
    echo "  help    - Show this help message"
    echo ""
    echo "🛡️  Security Features:"
    echo "  ✅ Username/password authentication"
    echo "  ✅ Session management"
    echo "  ✅ Protected file access"
    echo "  ✅ Secure directory listing"
    echo "  ✅ Anti-directory traversal"
    echo ""

}

# Main script logic
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    status)
        status_server
        ;;
    restart)
        restart_server
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Invalid command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac