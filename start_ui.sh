#!/bin/bash

echo "🚀 Starting CVE Agent Streamlit UI..."
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  Warning: MongoDB doesn't appear to be running"
    echo "   Start it with: brew services start mongodb-community"
    echo ""
fi

# Start Streamlit with the new entry point
echo "📱 Starting Streamlit application..."
echo "🌐 URL: http://localhost:8501"
echo ""
streamlit run app.py

echo ""
echo "✅ Application closed"
