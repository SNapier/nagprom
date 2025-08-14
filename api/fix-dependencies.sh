#!/bin/bash

# NagProm Dependency Fix Script
# Run this if the main installer has dependency issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}NagProm Dependency Fix Script${NC}"
echo "================================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}This script must be run as root${NC}"
    exit 1
fi

echo -e "${YELLOW}Installing system dependencies...${NC}"
apt-get update
apt-get install -y python3-dev build-essential python3-venv

echo -e "${YELLOW}Upgrading pip and setuptools...${NC}"
cd /opt/nagprom/api
source /opt/nagprom/venv/bin/activate
pip install --upgrade pip setuptools wheel

echo -e "${YELLOW}Trying conservative requirements...${NC}"
if pip install -r requirements-conservative.txt; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
    echo -e "${GREEN}You can now restart the API service:${NC}"
    echo "systemctl restart nagprom-api"
else
    echo -e "${RED}❌ Still having issues. Trying minimal requirements...${NC}"
    
    # Try installing packages one by one
    pip install Flask==2.3.3
    pip install Flask-CORS==4.0.0
    pip install Flask-Limiter==3.4.1
    pip install requests==2.31.0
    
    # Try numpy and pandas separately
    if pip install numpy==1.21.6; then
        echo -e "${GREEN}✓ NumPy installed${NC}"
    else
        echo -e "${YELLOW}⚠ NumPy installation failed, continuing without it${NC}"
    fi
    
    if pip install pandas==1.5.3; then
        echo -e "${GREEN}✓ Pandas installed${NC}"
    else
        echo -e "${YELLOW}⚠ Pandas installation failed, continuing without it${NC}"
    fi
    
    echo -e "${GREEN}✓ Minimal dependencies installed${NC}"
    echo -e "${YELLOW}Note: Some SRE features may not work without numpy/pandas${NC}"
fi

echo -e "${GREEN}Dependency fix complete!${NC}"
