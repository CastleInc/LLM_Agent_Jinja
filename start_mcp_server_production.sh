#!/bin/bash
# Start MCP Server

echo "🚀 Starting CVE MCP Server..."
cd "$(dirname "$0")/mcp_server"

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  Warning: MongoDB doesn't appear to be running"
    echo "   Start MongoDB with: mongod"
fi

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
    echo "✓ Activated virtual environment"
fi

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt
fi

# Run the server
echo "✓ Starting server on port 8001..."
python main.py

