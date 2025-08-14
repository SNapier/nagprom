#!/bin/bash

# Simple NagProm API Installer
# Installs the working API server

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}NagProm API Installer${NC}"
echo "======================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Clean up old installation
echo -e "${YELLOW}Cleaning up old installation...${NC}"
systemctl stop nagprom-api 2>/dev/null || true
systemctl disable nagprom-api 2>/dev/null || true
rm -f /etc/systemd/system/nagprom-api.service
rm -rf /opt/nagprom/bin
rm -rf /opt/nagprom/venv
systemctl daemon-reload

# Create directories
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p /opt/nagprom/api
mkdir -p /opt/nagprom/config
mkdir -p /opt/nagprom/analytics

# Copy API files
echo -e "${GREEN}Installing API files...${NC}"
cp nagprom_rest_api.py /opt/nagprom/api/
cp requirements.txt /opt/nagprom/api/
cp requirements-conservative.txt /opt/nagprom/api/
cp nagprom-api.service /etc/systemd/system/

# Copy SRE Analytics files
echo -e "${GREEN}Installing SRE Analytics files...${NC}"
cp ../analytics/sre_analytics_engine.py /opt/nagprom/analytics/
cp ../analytics/alert_correlation.py /opt/nagprom/analytics/
cp ../analytics/README.md /opt/nagprom/analytics/

# Copy utility scripts
echo -e "${GREEN}Installing utility scripts...${NC}"
cp fix-dependencies.sh /opt/nagprom/api/
chmod +x /opt/nagprom/api/fix-dependencies.sh

# Configure Apache reverse proxy
echo -e "${GREEN}Configuring Apache reverse proxy...${NC}"

# Enable required Apache modules
a2enmod proxy
a2enmod proxy_http
a2enmod headers

# Create Apache configuration
cat > /etc/apache2/sites-available/nagprom-api.conf << 'EOF'
# NagProm API Apache Configuration
# Add this to your existing Apache config

# Enable required modules
# sudo a2enmod proxy
# sudo a2enmod proxy_http
# sudo a2enmod headers

# NagProm API Proxy
ProxyPass /nagprom/api/ http://127.0.0.1:5000/api/
ProxyPassReverse /nagprom/api/ http://127.0.0.1:5000/api/

# Security headers
<Location "/nagprom/">
    Header always set Access-Control-Allow-Origin "*"
    Header always set Access-Control-Allow-Methods "GET, POST, OPTIONS"
    Header always set Access-Control-Allow-Headers "Content-Type, X-API-Key"
</Location>
EOF

# Enable the site
a2ensite nagprom-api

# Test and reload Apache
if apache2ctl configtest; then
    systemctl reload apache2
    echo -e "${GREEN}Apache configuration updated successfully${NC}"
else
    echo -e "${RED}Apache configuration test failed${NC}"
    exit 1
fi

# Set permissions
echo -e "${GREEN}Setting permissions...${NC}"
chown -R nagios:nagios /opt/nagprom
chmod +x /opt/nagprom/api/nagprom_rest_api.py
chmod +x /opt/nagprom/analytics/sre_analytics_engine.py

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
cd /opt/nagprom/api

# Create virtual environment
python3 -m venv /opt/nagprom/venv
source /opt/nagprom/venv/bin/activate

# Upgrade pip and install build tools first
echo -e "${GREEN}Upgrading pip and installing build tools...${NC}"
pip install --upgrade pip
pip install --upgrade setuptools wheel

# Install dependencies
echo -e "${GREEN}Installing application dependencies...${NC}"
if pip install -r requirements.txt; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Main requirements failed, trying conservative versions...${NC}"
    if pip install -r requirements-conservative.txt; then
        echo -e "${GREEN}✓ Conservative dependencies installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        echo -e "${YELLOW}Try running the dependency fix script:${NC}"
        echo "cd /opt/nagprom/api && ./fix-dependencies.sh"
        echo -e "${YELLOW}Or install system-level dependencies first:${NC}"
        echo "apt-get update && apt-get install -y python3-dev build-essential"
        exit 1
    fi
fi

# Enable and start service
echo -e "${GREEN}Starting API service...${NC}"
systemctl daemon-reload
systemctl enable nagprom-api
systemctl start nagprom-api

# Wait a moment for service to start
sleep 3

# Check status
echo -e "${GREEN}Checking service status...${NC}"
if systemctl is-active --quiet nagprom-api; then
    echo -e "${GREEN}✅ API service is running${NC}"
    systemctl status nagprom-api --no-pager
else
    echo -e "${RED}❌ API service failed to start${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    journalctl -u nagprom-api --no-pager -n 20
    exit 1
fi

echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo -e "${YELLOW}API is now accessible at:${NC}"
echo "• Direct API: http://localhost:5000/api/v1/health"
echo "• Via Apache: http://localhost/nagprom/api/v1/health"
echo ""
echo -e "${YELLOW}New SRE Analytics Features:${NC}"
echo "• Service Reliability: /api/v1/sre/service/{service}/reliability"
echo "• Host Reliability: /api/v1/sre/host/{host}/reliability"
echo "• Anomaly Detection: /api/v1/sre/anomalies"
echo "• SLO Management: /api/v1/sre/slo"
echo ""
echo -e "${YELLOW}Test the installation:${NC}"
echo "curl http://localhost/nagprom/api/v1/health"
echo "curl http://localhost/nagprom/api/v1/summary"
echo "curl http://localhost/nagprom/api/v1/sre/slo"
echo "curl http://localhost/nagprom/api/v1/sre/anomalies"
echo ""
echo -e "${YELLOW}If you need to modify Apache config:${NC}"
echo "Edit: /etc/apache2/sites-available/nagprom-api.conf"
echo "Reload: systemctl reload apache2"
