#!/bin/bash

# NagProm API Client Installer
# Installs PHP dashboards for NagProm API integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAGIOS_HOME="/usr/local/nagios"
NAGIOS_SHARE="$NAGIOS_HOME/share"
NAGPROM_DIR="$NAGIOS_SHARE/nagprom"
NAGIOS_USER="nagios"
NAGIOS_GROUP="nagios"

# Files to install
FILES=(
    "index.php"
    "metrics.php"
    "debug.php"
    "graph.php"
    "correlation.php"
)

echo -e "${GREEN}NagProm API Client Installer${NC}"
echo "=================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Check if Nagios is installed
if [[ ! -d "$NAGIOS_HOME" ]]; then
    echo -e "${RED}Nagios not found at $NAGIOS_HOME${NC}"
    echo "Please install Nagios Core first"
    exit 1
fi

# Check if Nagios share directory exists
if [[ ! -d "$NAGIOS_SHARE" ]]; then
    echo -e "${RED}Nagios share directory not found at $NAGIOS_SHARE${NC}"
    exit 1
fi

echo -e "${BLUE}Installation Configuration:${NC}"
echo "  Nagios Home: $NAGIOS_HOME"
echo "  Nagios Share: $NAGIOS_SHARE"
echo "  NagProm Directory: $NAGPROM_DIR"
echo "  User: $NAGIOS_USER"
echo "  Group: $NAGIOS_GROUP"
echo ""

# Create NagProm directory
echo -e "${GREEN}Creating NagProm directory...${NC}"
if [[ -d "$NAGPROM_DIR" ]]; then
    echo -e "${YELLOW}Directory $NAGPROM_DIR already exists${NC}"
    
    read -p "Do you want to overwrite existing files? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Installation cancelled${NC}"
        exit 0
    fi
    
    echo -e "${YELLOW}Proceeding with overwrite...${NC}"
    echo ""
else
    mkdir -p "$NAGPROM_DIR"
    echo -e "    ${GREEN}✓ Created directory $NAGPROM_DIR${NC}"
fi

# Set directory permissions
chown "$NAGIOS_USER:$NAGIOS_GROUP" "$NAGPROM_DIR"
chmod 755 "$NAGPROM_DIR"

echo ""

# Install files
echo -e "${GREEN}Installing NagProm API client files...${NC}"

for file in "${FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  Installing $file..."
        
        # Copy the file
        cp "$file" "$NAGPROM_DIR/"
        
        # Set proper permissions
        chown "$NAGIOS_USER:$NAGIOS_GROUP" "$NAGPROM_DIR/$file"
        chmod 644 "$NAGPROM_DIR/$file"
        
        echo -e "    ${GREEN}✓ Installed $file${NC}"
    else
        echo -e "    ${RED}✗ File $file not found in current directory${NC}"
        exit 1
    fi
done

echo ""

# Installation complete
echo -e "${GREEN}✅ Installation completed successfully!${NC}"
echo ""
echo -e "${BLUE}Installed Files:${NC}"
echo "  - $NAGPROM_DIR/index.php (Main Dashboard)"
echo "  - $NAGPROM_DIR/metrics.php (Performance Metrics)"
echo "  - $NAGPROM_DIR/debug.php (Debug Information)"
echo "  - $NAGPROM_DIR/graph.php (Metrics Graphing)"
echo "  - $NAGPROM_DIR/correlation.php (Alert Correlation)"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "  Main Dashboard: http://your-server/nagios/nagprom/"
echo "  Performance Metrics: http://your-server/nagios/nagprom/metrics.php"
echo "  Debug Information: http://your-server/nagios/nagprom/debug.php"
echo "  Metrics Graphing: http://your-server/nagios/nagprom/graph.php"
echo "  Alert Correlation: http://your-server/nagios/nagprom/correlation.php"
echo ""
echo -e "${YELLOW}Note:${NC} Make sure the NagProm API is running and accessible at http://127.0.0.1/nagprom/api/v1"
echo ""
echo -e "${GREEN}Installation complete!${NC}"
