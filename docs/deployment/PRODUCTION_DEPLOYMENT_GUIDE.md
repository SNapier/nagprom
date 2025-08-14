# NagProm Production Deployment Guide
## Ubuntu 24.04 + Nagios Core 4.5.x + Apache2 + Prometheus Integration

This guide provides step-by-step instructions for integrating the NagProm REST API into your existing production Nagios environment. The API provides comprehensive monitoring data access, SRE analytics, and time-series capabilities.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Production Server                    │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │   Nagios    │  │  Prometheus  │  │   Node Exporter     │ │
│  │   :80/nagios│  │    :9090     │  │       :9100         │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
│           │              │                       │          │
│           │              └───────────────────────┘          │
│           │                       │                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Apache2 Reverse Proxy                     │ │
│  │  /nagios/* ──→ Nagios Web Interface                    │ │
│  │  /nagprom/api/* ──→ NagProm REST API (:5000)           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           NagProm REST API Service                     │ │
│  │  • Reads from Prometheus                               │ │
│  │  • Exposes REST endpoints                              │ │
│  │  • Embedded SRE Analytics                              │ │
│  │  • Runs as systemd service                             │ │
│  │  • Self-monitoring via Nagios                          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites Checklist

Before starting, ensure you have:

- ✅ **Ubuntu 24.04** server
- ✅ **Nagios Core 4.5.x** installed and running
- ✅ **Apache2** serving Nagios on port 80
- ✅ **Prometheus** running on localhost:9090
- ✅ **Node Exporter** running on localhost:9100
- ✅ **nagprom-service.py** and **nagprom-host.py** already configured
- ✅ **Root/sudo access** for installation

## Quick Installation (Automated)

### Option 1: Complete Installation

```bash
# Step 1: Install the REST API service
cd nagprom-api/api/
sudo bash install.sh

# Step 2: Install Nagios dashboard components
cd ../clients/nagios/
sudo ./install.sh

# Verification
curl http://localhost/nagprom/api/v1/health
```

### Option 2: API Service Only

```bash
# Basic installation
cd nagprom-api/api/
sudo bash install.sh

# Verification
curl http://localhost/nagprom/api/v1/health
```

The installer will:
- Install all dependencies
- Create dedicated directories
- Configure systemd service with embedded SRE analytics
- Set up Apache reverse proxy with security
- Start all services

**Note:** This installs the REST API service only. For Nagios PHP dashboard components, run the separate Nagios installer after this:
```bash
cd nagprom-api/clients/nagios/
sudo ./install.sh
```

## Manual Installation Steps

### 1. Install Dependencies

```bash
# Update system
sudo apt update

# Install Python dependencies
sudo apt install -y python3-venv python3-dev python3-pip build-essential

# Enable Apache modules
sudo a2enmod proxy proxy_http headers rewrite ssl
sudo systemctl reload apache2
```

### 2. Create Directories

```bash
# Create directory structure
sudo mkdir -p /opt/nagprom/{api,config,analytics}
sudo chown -R nagios:nagios /opt/nagprom
```

### 3. Install API Files

```bash
# Copy API files to installation directory
sudo cp nagprom_rest_api.py /opt/nagprom/api/
sudo cp requirements.txt /opt/nagprom/api/
sudo cp requirements-conservative.txt /opt/nagprom/api/
sudo cp nagprom-api.service /etc/systemd/system/

# Copy SRE Analytics files
sudo cp ../analytics/sre_analytics_engine.py /opt/nagprom/analytics/
sudo cp ../analytics/alert_correlation.py /opt/nagprom/analytics/
sudo cp ../analytics/README.md /opt/nagprom/analytics/

# Copy utility scripts
sudo cp fix-dependencies.sh /opt/nagprom/api/
sudo chmod +x /opt/nagprom/api/fix-dependencies.sh
sudo chmod +x /opt/nagprom/api/nagprom_rest_api.py
sudo chmod +x /opt/nagprom/analytics/sre_analytics_engine.py
```

### 4. Configure Apache Integration

```bash
# Create Apache configuration
sudo tee /etc/apache2/sites-available/nagprom-api.conf << 'EOF'
# NagProm API Apache Configuration

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
sudo a2ensite nagprom-api

# Test and reload Apache
if apache2ctl configtest; then
    sudo systemctl reload apache2
    echo "Apache configuration updated successfully"
else
    echo "Apache configuration test failed"
    exit 1
fi
```

### 5. Install Python Dependencies

```bash
# Create virtual environment
cd /opt/nagprom/api
sudo python3 -m venv /opt/nagprom/venv
sudo /opt/nagprom/venv/bin/pip install --upgrade pip
sudo /opt/nagprom/venv/bin/pip install --upgrade setuptools wheel

# Install dependencies
if sudo /opt/nagprom/venv/bin/pip install -r requirements.txt; then
    echo "✓ Dependencies installed successfully"
else
    echo "⚠ Main requirements failed, trying conservative versions..."
    if sudo /opt/nagprom/venv/bin/pip install -r requirements-conservative.txt; then
        echo "✓ Conservative dependencies installed successfully"
    else
        echo "❌ Failed to install dependencies"
        echo "Try running the dependency fix script:"
        echo "cd /opt/nagprom/api && ./fix-dependencies.sh"
        exit 1
    fi
fi
```

### 6. Start Services

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable nagprom-api
sudo systemctl start nagprom-api

# Wait a moment for service to start
sleep 3

# Check status
if systemctl is-active --quiet nagprom-api; then
    echo "✅ API service is running"
    systemctl status nagprom-api --no-pager
else
    echo "❌ API service failed to start"
    echo "Checking logs..."
    journalctl -u nagprom-api --no-pager -n 20
    exit 1
fi
```

## Testing Your Installation

### 1. Basic API Test

**Without API Key Authentication:**
```bash
# Test API health (always public)
curl http://localhost/nagprom/api/v1/health

# Test monitoring summary
curl http://localhost/nagprom/api/v1/summary

# Test service list
curl http://localhost/nagprom/api/v1/services

# Test performance metrics
curl http://localhost/nagprom/api/v1/metrics

# Test thresholds data
curl http://localhost/nagprom/api/v1/thresholds

# Test timeseries endpoints (last hour)
curl "http://localhost/nagprom/api/v1/timeseries/hosts?start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=1m"
curl "http://localhost/nagprom/api/v1/timeseries/services?start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=1m"
curl "http://localhost/nagprom/api/v1/timeseries/performance?start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=1m"

# Test debug endpoints
curl http://localhost/nagprom/api/v1/debug/metrics
curl http://localhost/nagprom/api/v1/debug/thresholds

# Test SRE Analytics endpoints
curl http://localhost/nagprom/api/v1/sre/dashboard
curl http://localhost/nagprom/api/v1/sre/capacity
curl "http://localhost/nagprom/api/v1/sre/service/reliability?service=cpu.utilization"
curl "http://localhost/nagprom/api/v1/sre/host/reliability?host=localhost"
curl http://localhost/nagprom/api/v1/sre/anomalies
curl http://localhost/nagprom/api/v1/sre/slo
```

**With API Key Authentication:**
```bash
# Set API key environment variable
export NAGPROM_API_KEY="your-api-key-here"

# Test monitoring summary with API key
curl -H "X-API-Key: $NAGPROM_API_KEY" http://localhost/nagprom/api/v1/summary

# Test service list with API key
curl -H "X-API-Key: $NAGPROM_API_KEY" http://localhost/nagprom/api/v1/services

# Test performance metrics with API key
curl -H "X-API-Key: $NAGPROM_API_KEY" http://localhost/nagprom/api/v1/metrics

# Test thresholds data with API key
curl -H "X-API-Key: $NAGPROM_API_KEY" http://localhost/nagprom/api/v1/thresholds

# Test timeseries endpoints with API key
curl -H "X-API-Key: $NAGPROM_API_KEY" "http://localhost/nagprom/api/v1/timeseries/hosts?start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=1m"
curl -H "X-API-Key: $NAGPROM_API_KEY" "http://localhost/nagprom/api/v1/timeseries/services?start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=1m"
curl -H "X-API-Key: $NAGPROM_API_KEY" "http://localhost/nagprom/api/v1/timeseries/performance?start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=1m"

# Test without API key (should return 401)
curl http://localhost/nagprom/api/v1/summary

# Test SRE Analytics with API key
curl -H "X-API-Key: $NAGPROM_API_KEY" http://localhost/nagprom/api/v1/sre/dashboard
curl -H "X-API-Key: $NAGPROM_API_KEY" http://localhost/nagprom/api/v1/sre/capacity
curl -H "X-API-Key: $NAGPROM_API_KEY" "http://localhost/nagprom/api/v1/sre/service/reliability?service=cpu.utilization"
curl -H "X-API-Key: $NAGPROM_API_KEY" "http://localhost/nagprom/api/v1/sre/host/reliability?host=localhost"
curl -H "X-API-Key: $NAGPROM_API_KEY" http://localhost/nagprom/api/v1/sre/anomalies
curl -H "X-API-Key: $NAGPROM_API_KEY" http://localhost/nagprom/api/v1/sre/slo
```

### 2. Integration Test

```bash
# Test from external machine (replace YOUR_SERVER_IP and YOUR_API_KEY)
curl http://YOUR_SERVER_IP/nagprom/api/v1/health

# Test with API key if authentication is enabled
curl -H "X-API-Key: YOUR_API_KEY" http://YOUR_SERVER_IP/nagprom/api/v1/summary
```

### 3. Performance Test

```bash
# Run load test (adjust for API key authentication)
if [[ -n "$NAGPROM_API_KEY" ]]; then
    for i in {1..10}; do
        curl -s -H "X-API-Key: $NAGPROM_API_KEY" http://localhost/nagprom/api/v1/summary > /dev/null &
    done
else
    for i in {1..10}; do
        curl -s http://localhost/nagprom/api/v1/summary > /dev/null &
    done
fi
wait

# Check response times
time curl -H "X-API-Key: YOUR_API_KEY" http://localhost/nagprom/api/v1/summary
```

## Production Configuration

### Security Configuration

#### 1. API Key Authentication

**Enable API Key Authentication:**
```bash
# Set environment variable for the service
sudo tee /etc/systemd/system/nagprom-api.service.d/override.conf << EOF
[Service]
Environment="NAGPROM_API_KEY=your-secure-key-here"
EOF

# Reload systemd and restart service
sudo systemctl daemon-reload
sudo systemctl restart nagprom-api
```

**Using API Keys:**
```bash
# Via X-API-Key header (recommended)
curl -H "X-API-Key: YOUR_KEY" http://your-server/nagprom/api/v1/summary

# Via query parameter (less secure, but convenient for testing)
curl http://your-server/nagprom/api/v1/summary?api_key=YOUR_KEY

# Health endpoint is always public (no key required)
curl http://your-server/nagprom/api/v1/health
```

#### 2. Configure SSL/TLS

```bash
# Install Let's Encrypt (recommended for production)
sudo apt install certbot python3-certbot-apache

# Get SSL certificate
sudo certbot --apache -d yourdomain.com

# Or use self-signed for testing
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nagprom.key \
    -out /etc/ssl/certs/nagprom.crt
```

#### 3. Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block direct API access (optional - API only listens on 127.0.0.1 by default)
sudo ufw deny 5000/tcp
```

### Performance Optimization

#### 1. Configure Log Rotation

```bash
sudo tee /etc/logrotate.d/nagprom-api << EOF
/opt/nagprom/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 nagios nagios
    postrotate
        systemctl reload nagprom-api > /dev/null 2>&1 || true
    endscript
}
EOF
```

#### 2. Resource Limits

Edit the systemd service to add:

```ini
[Service]
MemoryLimit=512M
CPUQuota=100%
TasksMax=100
```

## Monitoring and Maintenance

### Health Checks

```bash
# API health
curl http://localhost/nagprom/api/v1/health

# Service status
sudo systemctl status nagprom-api

# Check logs
sudo journalctl -u nagprom-api --since "1 hour ago"

# Check Apache logs
sudo tail -f /var/log/apache2/nagprom-api_access.log
```

### Management Commands

Create a management script:

```bash
sudo tee /usr/local/bin/nagprom-manage << 'EOF'
#!/bin/bash
case "$1" in
    start)   sudo systemctl start nagprom-api ;;
    stop)    sudo systemctl stop nagprom-api ;;
    restart) sudo systemctl restart nagprom-api ;;
    status)  sudo systemctl status nagprom-api ;;
    logs)    sudo journalctl -u nagprom-api -f ;;
    test)    curl -s http://localhost/nagprom/api/v1/health | python3 -m json.tool ;;
    *)       echo "Usage: $0 {start|stop|restart|status|logs|test}" ;;
esac
EOF

sudo chmod +x /usr/local/bin/nagprom-manage
```

Usage:
```bash
nagprom-manage status
nagprom-manage logs
nagprom-manage test
```

## Troubleshooting

### Common Issues

#### 1. API Not Responding

```bash
# Check if service is running
sudo systemctl status nagprom-api

# Check if port is listening
sudo netstat -tlnp | grep :5000

# Check logs
sudo journalctl -u nagprom-api
```

#### 2. Prometheus Connection Failed

```bash
# Test Prometheus directly
curl http://localhost:9090/api/v1/query?query=up

# Check if Prometheus is running
sudo systemctl status prometheus

# Verify network connectivity
telnet localhost 9090
```

#### 3. Apache Proxy Issues

```bash
# Test Apache configuration
sudo apache2ctl configtest

# Check Apache error logs
sudo tail -f /var/log/apache2/error.log

# Verify proxy modules are enabled
apache2ctl -M | grep proxy
```

#### 4. Permission Issues

```bash
# Check file permissions
ls -la /opt/nagprom/

# Fix ownership if needed
sudo chown -R nagios:nagios /opt/nagprom/

# Check SELinux (if enabled)
sudo setsebool -P httpd_can_network_connect 1
```

### Log Analysis

```bash
# API logs
sudo journalctl -u nagprom-api --since "1 day ago" | grep ERROR

# Apache access logs
sudo tail -f /var/log/apache2/nagprom-api_access.log

# Apache error logs
sudo tail -f /var/log/apache2/nagprom-api_error.log

# System logs
sudo journalctl --since "1 hour ago" | grep nagprom
```

## Integration Examples

### 1. Custom Dashboard Integration

Your API endpoints are now available at:
- `http://yourserver/nagprom/api/v1/health` - Health check (no auth)
- `http://yourserver/nagprom/api/v1/summary` - Monitoring summary
- `http://yourserver/nagprom/api/v1/hosts` - All monitored hosts
- `http://yourserver/nagprom/api/v1/services` - All monitored services
- `http://yourserver/nagprom/api/v1/metrics` - Performance metrics data
- `http://yourserver/nagprom/api/v1/thresholds` - Performance thresholds data
- `http://yourserver/nagprom/api/v1/sre/dashboard` - SRE analytics
- `http://yourserver/nagprom/api/v1/sre/capacity` - Capacity planning
- `http://yourserver/nagprom/api/v1/debug/metrics` - Debug available metrics
- `http://yourserver/nagprom/api/v1/debug/thresholds` - Debug thresholds functionality

### 2. Mobile App Integration

```javascript
// React Native example
const API_BASE = 'https://yourserver/nagprom/api/v1';

const fetchSummary = async () => {
    try {
        const response = await fetch(`${API_BASE}/summary`, {
            headers: {
                'X-API-Key': 'your-api-key' // if authentication enabled
            }
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API Error:', error);
    }
};
```

### 3. Automation Scripts

```python
import requests

API_BASE = 'http://yourserver/nagprom/api/v1'
API_KEY = 'your-api-key'

headers = {'X-API-Key': API_KEY}

# Get critical services
response = requests.get(f'{API_BASE}/services', headers=headers)
services = response.json()

# Get performance metrics for a specific host
response = requests.get(f'{API_BASE}/metrics?host=your-host', headers=headers)
metrics = response.json()

# Get thresholds for a specific host
response = requests.get(f'{API_BASE}/thresholds?host=your-host', headers=headers)
thresholds = response.json()

# Example: Check if any metrics exceed thresholds
for service_key, service_data in metrics.get('data', {}).items():
    host = service_data['host']
    service = service_data['service']
    
    # Get thresholds for this service
    service_thresholds = thresholds.get('data', {}).get(service_key, {}).get('thresholds', {})
    
    for metric_name, metric_value in service_data.get('metrics', {}).items():
        metric_thresholds = service_thresholds.get(metric_name, {})
        
        # Check if value exceeds thresholds
        if isinstance(metric_value, dict):
            value = float(metric_value.get('value', 0))
        else:
            value = float(metric_value)
            
        warning = metric_thresholds.get('warning')
        critical = metric_thresholds.get('critical')
        min_val = metric_thresholds.get('min')
        max_val = metric_thresholds.get('max')
        
        if critical and value >= critical:
            print(f"CRITICAL: {host}:{service}:{metric_name} = {value} (threshold: {critical})")
        elif warning and value >= warning:
            print(f"WARNING: {host}:{service}:{metric_name} = {value} (threshold: {warning})")
        elif min_val and value < min_val:
            print(f"MIN EXCEEDED: {host}:{service}:{metric_name} = {value} (min: {min_val})")
        elif max_val and value > max_val:
            print(f"MAX EXCEEDED: {host}:{service}:{metric_name} = {value} (max: {max_val})")

# Send alerts, generate reports, etc.
```

### 4. Thresholds Data Structure

The thresholds endpoint returns data in this format:

```json
{
  "success": true,
  "data": {
    "hostname:servicename": {
      "host": "hostname",
      "service": "servicename", 
      "thresholds": {
        "cpu_usage": {
          "warning": 80.0,
          "critical": 95.0,
          "min": 0.0,
          "max": 100.0
        },
        "memory_usage": {
          "warning": 85.0,
          "critical": 98.0,
          "min": null,
          "max": null
        }
      }
    }
  }
}
```

**Threshold Types:**
- `warning` - Warning threshold (orange alert)
- `critical` - Critical threshold (red alert) 
- `min` - Minimum acceptable value (red alert if below)
- `max` - Maximum acceptable value (red alert if above)

**Usage Examples:**
```bash
# Get all thresholds
curl -H "X-API-Key: YOUR_KEY" http://yourserver/nagprom/api/v1/thresholds

# Get thresholds for specific host
curl -H "X-API-Key: YOUR_KEY" http://yourserver/nagprom/api/v1/thresholds?host=web-server-01

# Get thresholds for specific service
curl -H "X-API-Key: YOUR_KEY" http://yourserver/nagprom/api/v1/thresholds?service=disk-usage
```

### Backup Configuration

```bash
# Create backup script
sudo tee /opt/nagprom/api/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/nagprom/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup configuration
tar -czf "$BACKUP_DIR/nagprom-config-$DATE.tar.gz" \
    /opt/nagprom/config/ \
    /etc/systemd/system/nagprom-api.service \
    /etc/apache2/sites-available/nagprom-api.conf

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "nagprom-config-*.tar.gz" -mtime +30 -delete
EOF

sudo chmod +x /opt/nagprom/api/backup.sh

# Add to cron
echo "0 2 * * * nagios /opt/nagprom/api/backup.sh" | sudo crontab -u nagios -
```

## 🎯 Final Result

After installation, you'll have:

- ✅ **NagProm REST API** running as a systemd service
- ✅ **Apache integration** with reverse proxy
- ✅ **SSL/TLS support** for secure access
- ✅ **SRE Analytics** with reliability tracking and anomaly detection

Your API will be accessible at:
- `http://yourserver/nagprom/api/v1/` (HTTP)
- `https://yourserver/nagprom/api/v1/` (HTTPS)

Alongside your existing Nagios interface at:
- `http://yourserver/nagios/` (Nagios Web Interface)
