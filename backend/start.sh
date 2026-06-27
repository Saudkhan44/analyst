#!/bin/bash
# Startup script for AI Analytics Dashboard backend

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AI Analytics Dashboard Backend Startup${NC}"
echo "==========================================="

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "\n${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Dependencies installed${NC}"
else
    echo -e "${RED}Failed to install dependencies${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${RED}Please edit .env with your configuration${NC}"
    exit 1
fi

# Start the application
echo -e "\n${YELLOW}Starting FastAPI application...${NC}"
echo -e "${GREEN}API documentation available at: http://localhost:8000/docs${NC}"
echo -e "${GREEN}Press Ctrl+C to stop${NC}\n"

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
