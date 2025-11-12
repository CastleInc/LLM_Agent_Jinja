#!/bin/bash

echo "======================================================================="
echo "🚀 Starting CVE Intelligence Agent - Streamlit Interface"
echo "======================================================================="
echo ""
echo "🔧 MCP Tools Architecture with Beautiful Jinja Templates"
echo ""

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install streamlit if not already installed
pip install -q streamlit

# Run Streamlit app
streamlit run streamlit_app.py --server.port 8501 --server.address localhost

echo ""
echo "======================================================================="

