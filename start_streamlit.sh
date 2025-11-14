#!/bin/bash
# Start Streamlit UI with MCP server

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Starting CVE Agent - Streamlit Interface${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if MCP server is running
echo -e "${YELLOW}Checking MCP server...${NC}"
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MCP server is running${NC}"
else
    echo -e "${YELLOW}⚠ MCP server is not running${NC}"
    echo -e "${YELLOW}Starting MCP server in background...${NC}"
    ./start_server_background.sh
    echo -e "${YELLOW}Waiting for server to be ready...${NC}"
    sleep 5
fi

# Start Streamlit
echo ""
echo -e "${GREEN}Starting Streamlit UI...${NC}"
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✓ Access the UI at: http://localhost:8501${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

cd llm_agent_client
streamlit run streamlit_app.py --server.port 8501

