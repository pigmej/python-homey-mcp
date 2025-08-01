#!/bin/bash
# HomeyPro MCP Server Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    HomeyPro MCP Server Startup${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file with your HomeyPro credentials${NC}"
    echo -e "${YELLOW}See .env.example for reference${NC}"
    echo ""
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed${NC}"
    echo -e "${RED}Please install uv: https://docs.astral.sh/uv/getting-started/installation/${NC}"
    exit 1
fi

echo -e "${GREEN}Starting HomeyPro MCP Server...${NC}"
echo ""

# Run the server using uv
uv run python run_server.py