# NagProm API Clients

This directory contains PHP-based client dashboards for the NagProm API integration with Nagios Core.

## Overview

The NagProm API clients provide web-based dashboards for monitoring and testing the NagProm REST API. These dashboards are designed to work without the `curl` extension, using `file_get_contents()` for HTTP requests instead.

## Files

### Core Dashboards

- **`index.php`** - Main dashboard hub
  - Overview of all monitoring data
  - Quick access to all dashboards
  - Clean, modern interface
  - Links back to Nagios

- **`metrics.php`** - Performance metrics dashboard
  - Shows detailed performance data for all services
  - Displays metrics with values and units
  - Organized by service and host
  - Includes gauge displays for warning/critical thresholds
  - Links to time-series graphing interface
  - Auto-refreshes every 30 seconds

- **`debug.php`** - Debug information dashboard
  - System configuration information
  - API connection status
  - Available Prometheus metrics
  - Sample data from API endpoints
  - Thresholds debug information
  - Auto-refreshes every 60 seconds

- **`graph.php`** - Time-series graphing interface
  - Historical performance data visualization
  - Configurable time ranges
  - Warning and critical threshold lines
  - Metric filtering capabilities
  - Chart.js integration for responsive graphs

### Installation

- **`install.sh`** - Automated installer script
  - Copies files to `/usr/local/nagios/share/nagprom/` directory
  - Sets proper permissions
  - Prompts for file overwrites
  - Creates navigation structure

## Installation

### Prerequisites

1. **Nagios Core** installed and running
2. **NagProm API** installed and running
3. **Apache** configured for PHP execution
4. **Root access** for installation

### Quick Install

```bash
# Navigate to the clients directory
cd nagprom-api/clients/nagios

# Run the installer
sudo ./install.sh
```

### Manual Installation

If you prefer to install manually:

```bash
# Create directory
sudo mkdir -p /usr/local/nagios/share/nagprom

# Copy files to Nagios share directory
sudo cp index.php /usr/local/nagios/share/nagprom/
sudo cp metrics.php /usr/local/nagios/share/nagprom/
sudo cp debug.php /usr/local/nagios/share/nagprom/
sudo cp graph.php /usr/local/nagios/share/nagprom/

# Set proper permissions
sudo chown nagios:nagios /usr/local/nagios/share/nagprom/
sudo chown nagios:nagios /usr/local/nagios/share/nagprom/*.php
sudo chmod 644 /usr/local/nagios/share/nagprom/*.php
```

## Configuration

### API Base URL

All dashboards use the following API base URL:
```php
$API_BASE = "http://127.0.0.1/nagprom/api/v1";
```

To change this, edit the `$API_BASE` variable in each PHP file.

### Timeout Settings

Default timeout is 10 seconds:
```php
$TIMEOUT = 10; // seconds
```

## Usage

### Access URLs

After installation, access the dashboards at:

- **Main Dashboard**: `http://your-server/nagios/nagprom/`
- **Performance Metrics**: `http://your-server/nagios/nagprom/metrics.php`
- **Debug Information**: `http://your-server/nagios/nagprom/debug.php`
- **Time-Series Graphs**: `http://your-server/nagios/nagprom/graph.php`

### Features

#### Main Dashboard Hub
- ✅ Overview of all monitoring data
- ✅ Quick access to all dashboards
- ✅ Clean, modern interface
- ✅ Links back to Nagios

#### Performance Metrics
- ✅ Shows all metrics per service
- ✅ Displays values with units
- ✅ Organized by host and service
- ✅ Real-time data updates
- ✅ Clean metric cards
- ✅ Gauge displays for warning/critical thresholds
- ✅ Links to time-series graphing interface

#### Debug Dashboard
- ✅ System configuration info
- ✅ PHP extension status
- ✅ API connection status
- ✅ Available Prometheus metrics
- ✅ Sample data display
- ✅ Thresholds debug information

#### Time-Series Graphing
- ✅ Historical performance data visualization
- ✅ Configurable time ranges (30min, 1h, 6h, 24h)
- ✅ Warning and critical threshold lines
- ✅ Metric filtering capabilities
- ✅ Chart.js integration for responsive graphs

## API Endpoints Used

The dashboards use these API endpoints:

1. **`/health`** - API health status
2. **`/summary`** - Monitoring summary
3. **`/hosts`** - All monitored hosts
4. **`/services`** - All monitored services
5. **`/metrics`** - Performance metrics data
6. **`/thresholds`** - Performance thresholds data
7. **`/timeseries/performance`** - Time-series performance data
8. **`/sre/dashboard`** - SRE analytics dashboard
9. **`/sre/capacity`** - Capacity planning data

## Troubleshooting

### Common Issues

#### "Connection Failed" Errors
- Check that the NagProm API is running: `systemctl status nagprom-api`
- Verify API is accessible: `curl http://127.0.0.1/nagprom/api/v1/health`
- Check Apache reverse proxy configuration

#### "No Data Available" Messages
- Ensure Prometheus is running and accessible
- Check that Nagios metrics are being exported to Prometheus
- Verify the API can query Prometheus successfully

#### Permission Errors
- Ensure files are owned by `nagios:nagios`
- Check file permissions are 644
- Verify Apache can read the files
- Check directory permissions for `/usr/local/nagios/share/nagprom/`

#### PHP Errors
- Check PHP error logs: `tail -f /var/log/apache2/error.log`
- Verify `file_get_contents()` is available
- Ensure `allow_url_fopen` is enabled

### Debug Steps

1. **Check API Status**:
   ```bash
   systemctl status nagprom-api
   journalctl -u nagprom-api -f
   ```

2. **Test API Directly**:
   ```bash
   curl http://127.0.0.1/nagprom/api/v1/health
   curl http://127.0.0.1/nagprom/api/v1/debug/metrics
   ```

3. **Check Apache Configuration**:
   ```bash
   apache2ctl configtest
   systemctl status apache2
   ```

4. **Verify File Permissions**:
   ```bash
   ls -la /usr/local/nagios/share/nagprom/
   ```

## Customization

### Styling

All dashboards use modern CSS with:
- Responsive design
- Clean, professional appearance
- Color-coded status indicators
- Hover effects and transitions

### Adding New Endpoints

To add new API endpoints to the dashboards:

1. Edit the appropriate PHP file (`index.php`, `metrics.php`, `debug.php`, or `graph.php`)
2. Add new API calls using `file_get_contents()`
3. Include proper error handling and data processing

### Modifying Auto-refresh

Change the refresh interval by modifying the JavaScript timeout:
```javascript
// Auto-refresh every 30 seconds
setTimeout(function() {
    location.reload();
}, 30000); // Change this value
```

## Security Considerations

- Dashboards are designed for internal monitoring use
- No authentication is implemented (rely on network security)
- Consider adding IP restrictions in Apache configuration
- API endpoints may require API keys (configure in API)

## Support

For issues with the NagProm API clients:

1. Check the debug dashboard for system information
2. Review Apache and PHP error logs
3. Verify API connectivity and configuration
4. Test API endpoints directly with curl

## Version History

- **v1.1.0** - Complete dashboard suite with time-series graphing
  - Added `graph.php` for historical data visualization
  - Enhanced `metrics.php` with threshold gauge displays
  - Updated `index.php` as main dashboard hub
  - Improved `debug.php` with thresholds information
  - All dashboards use consistent navigation and styling
  - Chart.js integration for responsive graphs
  - Time-series API integration with configurable ranges
