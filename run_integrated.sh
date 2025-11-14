#!/bin/bash
# Integrated startup script for MCP Server and Client
# Handles large MongoDB collections (500k+ documents)

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}CVE Agent System - Integrated Startup${NC}"
echo -e "${BLUE}Optimized for 500k+ document collections${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}Waiting for $service_name to be ready...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo -e "${RED}✗ $service_name failed to start${NC}"
    return 1
}

# Check MongoDB
echo -e "${YELLOW}Checking MongoDB...${NC}"
if pgrep -x "mongod" > /dev/null; then
    echo -e "${GREEN}✓ MongoDB is running${NC}"
else
    echo -e "${RED}✗ MongoDB is not running${NC}"
    echo -e "${YELLOW}Please start MongoDB: mongod${NC}"
    exit 1
fi

# Check if MCP server is already running
if check_port 8001; then
    echo -e "${YELLOW}⚠ MCP server is already running on port 8001${NC}"
    read -p "Do you want to restart it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Stopping existing MCP server...${NC}"
        lsof -ti:8001 | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo -e "${GREEN}Using existing MCP server${NC}"
        MCP_SERVER_RUNNING=true
    fi
fi

# Start MCP Server if not running
if [ -z "$MCP_SERVER_RUNNING" ]; then
    echo ""
    echo -e "${BLUE}Step 1: Starting MCP Server${NC}"
    echo -e "${YELLOW}========================================${NC}"

    cd "$SCRIPT_DIR/mcp_server"

    # Check dependencies
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}Installing/updating MCP server dependencies...${NC}"
        pip install -q -r requirements.txt
    fi

    # Start MCP server in background
    echo -e "${YELLOW}Starting MCP server on port 8001...${NC}"
    nohup python main.py > ../logs/mcp_server.log 2>&1 &
    MCP_PID=$!
    echo $MCP_PID > ../logs/mcp_server.pid

    # Wait for server to be ready
    if wait_for_service "http://localhost:8001/health" "MCP Server"; then
        # Check collection size
        echo -e "${YELLOW}Checking collection statistics...${NC}"
        HEALTH_DATA=$(curl -s http://localhost:8001/health)
        echo -e "${GREEN}Server Status: $HEALTH_DATA${NC}"
    else
        echo -e "${RED}Failed to start MCP server${NC}"
        echo -e "${YELLOW}Check logs: tail -f logs/mcp_server.log${NC}"
        exit 1
    fi
fi

# Start MCP Client
echo ""
echo -e "${BLUE}Step 2: Starting MCP Client${NC}"
echo -e "${YELLOW}========================================${NC}"

cd "$SCRIPT_DIR/llm_agent_client"

# Check dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Installing/updating client dependencies...${NC}"
    pip install -q -r requirements.txt
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ MCP Server is running on port 8001${NC}"
echo -e "${GREEN}✓ Starting CLI interface...${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Performance Tips for Large Collections:${NC}"
echo -e "  • Queries are optimized with MongoDB indexes"
echo -e "  • Text search uses full-text index"
echo -e "  • Results are limited to prevent timeouts"
echo -e "  • Sorting uses indexed fields"
echo ""
echo -e "${BLUE}Logs Location:${NC}"
echo -e "  • MCP Server: logs/mcp_server.log"
echo -e "  • PID File: logs/mcp_server.pid"
echo ""
echo -e "${YELLOW}To stop the MCP server later:${NC}"
echo -e "  kill \$(cat logs/mcp_server.pid)"
echo ""
echo -e "${GREEN}Starting CVE Agent CLI...${NC}"
echo ""

# Run the CLI
python agent_cli.py

# Cleanup on exit
echo ""
echo -e "${YELLOW}Shutting down...${NC}"
if [ -f "../logs/mcp_server.pid" ]; then
    MCP_PID=$(cat ../logs/mcp_server.pid)
    if ps -p $MCP_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping MCP server (PID: $MCP_PID)...${NC}"
        kill $MCP_PID 2>/dev/null || true
        rm ../logs/mcp_server.pid
    fi
fi

echo -e "${GREEN}✓ Shutdown complete${NC}"

