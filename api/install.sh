#!/bin/bash

# Simple NagProm API Installer
# Installs the working API server

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
CLEAN_INSTALL=false
SKIP_SSL=false
SERVER_NAME=""
ALLOWED_NETWORKS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_INSTALL=true
            shift
            ;;
        --skipssl)
            SKIP_SSL=true
            shift
            ;;
        --server-name)
            SERVER_NAME="$2"
            shift 2
            ;;
        --allowed-networks)
            ALLOWED_NETWORKS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --clean              Clean installation (remove old files)"
            echo "  --skipssl            Skip SSL configuration"
            echo "  --server-name NAME   Set server name for SSL certificate"
            echo "  --allowed-networks   Comma-separated list of allowed networks"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}NagProm API Installer${NC}"
echo "======================"
echo "Clean install: $CLEAN_INSTALL"
echo "Skip SSL: $SKIP_SSL"
echo "Server name: ${SERVER_NAME:-'not specified'}"
echo "Allowed networks: ${ALLOWED_NETWORKS:-'not specified'}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Clean up old installation if requested
if [[ "$CLEAN_INSTALL" == "true" ]]; then
    echo -e "${YELLOW}Performing clean installation...${NC}"
    systemctl stop nagprom-api 2>/dev/null || true
    systemctl disable nagprom-api 2>/dev/null || true
    rm -f /etc/systemd/system/nagprom-api.service
    rm -rf /opt/nagprom/bin
    rm -rf /opt/nagprom/venv
    rm -rf /opt/nagprom/api
    rm -rf /opt/nagprom/analytics
    rm -rf /opt/nagprom/config
    systemctl daemon-reload
    echo -e "${GREEN}Clean installation completed${NC}"
fi

# Create directories
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p /opt/nagprom/api
mkdir -p /opt/nagprom/config
mkdir -p /opt/nagprom/analytics

# Copy API files
echo -e "${GREEN}Installing API files...${NC}"
echo "Copying nagprom_rest_api.py..."
cp nagprom_rest_api.py /opt/nagprom/api/
echo "Copying requirements.txt..."
cp requirements.txt /opt/nagprom/api/
echo "Copying requirements-conservative.txt..."
cp requirements-conservative.txt /opt/nagprom/api/
echo "Copying nagprom-api.service..."
cp nagprom-api.service /etc/systemd/system/

# Copy SRE Analytics files
echo -e "${GREEN}Installing SRE Analytics files...${NC}"
echo "Copying sre_analytics_engine.py..."
cp analytics/sre_analytics_engine.py /opt/nagprom/analytics/
echo "Copying alert_correlation.py..."
cp analytics/alert_correlation.py /opt/nagprom/analytics/
echo "Copying analytics README.md..."
cp analytics/README.md /opt/nagprom/analytics/

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

# Copy the simple Apache configuration
cp apache-nagprom.conf /etc/apache2/sites-available/nagprom-api.conf

# Enable the site
a2ensite nagprom-api

# Configure SSL if not skipped and server name is provided
if [[ "$SKIP_SSL" == "false" && -n "$SERVER_NAME" ]]; then
    echo -e "${GREEN}Configuring SSL for server: $SERVER_NAME${NC}"
    
    # Check if certbot is available
    if command -v certbot &> /dev/null; then
        echo -e "${YELLOW}Attempting to obtain SSL certificate with Let's Encrypt...${NC}"
        certbot --apache -d "$SERVER_NAME" --non-interactive --agree-tos --email admin@"$SERVER_NAME" || {
            echo -e "${YELLOW}Let's Encrypt certificate failed, continuing without SSL${NC}"
        }
    else
        echo -e "${YELLOW}Certbot not found, creating self-signed certificate...${NC}"
        # Create self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/ssl/private/nagprom.key \
            -out /etc/ssl/certs/nagprom.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$SERVER_NAME" 2>/dev/null || {
            echo -e "${YELLOW}Self-signed certificate creation failed, continuing without SSL${NC}"
        }
    fi
elif [[ "$SKIP_SSL" == "true" ]]; then
    echo -e "${YELLOW}Skipping SSL configuration as requested${NC}"
else
    echo -e "${YELLOW}No server name provided, skipping SSL configuration${NC}"
fi

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
# Check if nagios user exists, if not use root
if id "nagios" &>/dev/null; then
    chown -R nagios:nagios /opt/nagprom
else
    echo -e "${YELLOW}Nagios user not found, setting ownership to root${NC}"
    chown -R root:root /opt/nagprom
fi
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

# Show SSL URLs if configured
if [[ "$SKIP_SSL" == "false" && -n "$SERVER_NAME" ]]; then
    echo "• Via HTTPS: https://$SERVER_NAME/nagprom/api/v1/health"
fi

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
