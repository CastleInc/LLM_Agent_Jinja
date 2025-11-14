#!/bin/bash
# Complete system startup script - MCP Server + Streamlit UI

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================"
echo "CVE Agent - Complete System Startup"
echo "======================================"
echo ""

# Create logs directory
mkdir -p logs

# Check if MongoDB is running
echo "1. Checking MongoDB connection..."
if ! mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
    echo "⚠️  WARNING: MongoDB may not be running on localhost:27017"
    echo "   Please start MongoDB or update MONGO_URI in .env file"
    echo ""
else
    echo "✅ MongoDB is running"
    echo ""
fi

# Stop any existing servers
echo "2. Stopping existing servers..."
if [ -f "logs/mcp_server.pid" ]; then
    OLD_PID=$(cat logs/mcp_server.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "   Stopping old MCP server (PID: $OLD_PID)..."
        kill $OLD_PID 2>/dev/null || true
        sleep 2
    fi
fi
echo "✅ Clean slate ready"
echo ""

# Start MCP Server
echo "3. Starting MCP Server (FastAPI)..."
cd mcp_server
nohup python main.py > ../logs/mcp_server.log 2>&1 &
MCP_PID=$!
echo $MCP_PID > ../logs/mcp_server.pid
cd ..
echo "✅ MCP Server started (PID: $MCP_PID)"
echo "   Logs: logs/mcp_server.log"
echo ""

# Wait for server to be ready
echo "4. Waiting for MCP Server to initialize..."
sleep 3

# Check server health
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ MCP Server is healthy"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ MCP Server failed to start. Check logs/mcp_server.log"
    exit 1
fi
echo ""

# Display server info
echo "5. Server Information:"
curl -s http://localhost:8001/health | python -m json.tool 2>/dev/null || echo "   Could not fetch health info"
echo ""

# Start Streamlit UI
echo "6. Starting Streamlit UI (LLM-Powered)..."
echo "   Opening browser at http://localhost:8501"
echo ""
cd llm_agent_client
streamlit run app.py

# Note: Streamlit runs in foreground, so this won't be reached until Ctrl+C
