# NagProm REST API

Simple, working REST API for Nagios monitoring data with integrated SRE (Site Reliability Engineering) analytics.

## Overview

The NagProm REST API provides:
- REST API endpoints for Nagios monitoring data
- Prometheus integration for metrics collection
- Optional API key authentication
- Time-series data support
- SRE analytics including reliability tracking and anomaly detection
- Clean, maintainable codebase

## Quick Start

### 1. Install API
```bash
cd nagprom-api/api
sudo ./install.sh
```

### 2. Configure Apache
The installer automatically configures Apache reverse proxy. The configuration is in `apache-nagprom.conf`.

### 3. Test API
```bash
# Direct access
curl http://localhost:5000/api/v1/health

# Via Apache proxy
curl http://localhost/nagprom/api/v1/health
```

## Installation Details

### Directory Structure
```
/opt/nagprom/
├── api/                    # API server files
│   ├── nagprom_rest_api.py
│   ├── requirements.txt
│   └── fix-dependencies.sh
├── analytics/              # SRE analytics modules
│   ├── sre_analytics_engine.py
│   ├── alert_correlation.py
│   └── README.md
└── venv/                   # Python virtual environment
```

### New SRE Features
- **Service Reliability Analysis**: `/api/v1/sre/service/reliability?service={service}`
- **Host Reliability Analysis**: `/api/v1/sre/host/reliability?host={host}`
- **Anomaly Detection**: `/api/v1/sre/anomalies`
- **SLO Management**: `/api/v1/sre/slo` (POST/GET)
- **Capacity Insights**: `/api/v1/sre/capacity`

### Dependencies
The installer automatically installs:
- Core Flask dependencies (Flask, Flask-CORS, Flask-Limiter, requests)
- SRE analytics dependencies (numpy, pandas)
- Build tools (setuptools, wheel)

### Permissions
- All files owned by `nagios:nagios`
- SRE analytics files have executable permissions
- Maintains existing security model

## API Endpoints

### Core Endpoints
- `GET /api/v1/health` - Health check (no auth)
- `GET /api/v1/summary` - Monitoring summary
- `GET /api/v1/hosts` - All monitored hosts
- `GET /api/v1/services` - All monitored services
- `GET /api/v1/metrics` - Performance metrics data
- `GET /api/v1/thresholds` - Performance thresholds data

### Time-Series Endpoints
- `GET /api/v1/timeseries/hosts` - Host status over time
- `GET /api/v1/timeseries/services` - Service status over time
- `GET /api/v1/timeseries/performance` - Performance metrics over time

### SRE Analytics
- `GET /api/v1/sre/dashboard` - SRE analytics dashboard
- `GET /api/v1/sre/capacity` - Capacity planning data
- `GET /api/v1/sre/service/reliability?service={service}` - Service reliability metrics
- `GET /api/v1/sre/host/reliability?host={host}` - Host reliability metrics
- `GET /api/v1/sre/anomalies` - Performance anomaly detection
- `POST /api/v1/sre/slo` - Create SLO target
- `GET /api/v1/sre/slo` - List all SLOs

### Debug Endpoints
- `GET /api/v1/debug/metrics` - Debug available metrics
- `GET /api/v1/debug/thresholds` - Debug thresholds functionality

### Query Parameters
Most endpoints support filtering and pagination:
- `?host=hostname` - Filter by specific host
- `?service=servicename` - Filter by specific service
- `?metric=metricname` - Filter performance data by metric name
- `?limit=100` - Maximum results to return (default: 100, max: 1000)
- `?offset=0` - Number of results to skip for pagination (default: 0)
- `?api_key=your_key` - API key authentication (if enabled)

### Time-Series Parameters
Time-series endpoints require additional parameters:
- `?start=2025-08-13T00:00:00Z` - Start time (RFC3339 or Unix timestamp)
- `?end=2025-08-13T01:00:00Z` - End time (RFC3339 or Unix timestamp)
- `?step=1m` - Step interval (15s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 6h, 12h, 1d)

### SRE Parameters
SRE endpoints support additional parameters:
- `?hours=24` - Time window for reliability calculations (default: 24)
- `?threshold_std=2.0` - Standard deviation threshold for anomaly detection (default: 2.0)
- `?service=servicename` - Filter by specific service
- `?host=hostname` - Filter by specific host

### Rate Limiting
- **Default**: 1000 requests per day, 200 requests per hour
- **Hosts/Services/Metrics/Thresholds**: 200 requests per hour
- **Time-Series**: 100 requests per hour (lower limit for performance)
- **SRE Reliability**: 100 requests per hour
- **SRE Anomalies**: 50 requests per hour (lower limit for performance)
- **SRE SLO Management**: 50 requests per hour
- Rate limits are applied per client IP address

## Data Structures

### Thresholds Response (Paginated)
```json
{
  "success": true,
  "data": {
    "thresholds": {
      "hostname:servicename": {
        "host": "hostname",
        "service": "servicename",
        "thresholds": {
          "metric_name": {
            "warning": 80.0,
            "critical": 95.0,
            "min": 0.0,
            "max": 100.0
          }
        }
      }
    },
    "pagination": {
      "limit": 100,
      "offset": 0,
      "total": 150,
      "returned": 100
    }
  }
}
```

### Metrics Response (Paginated)
```json
{
  "success": true,
  "data": {
    "metrics": {
      "hostname:servicename": {
        "host": "hostname",
        "service": "servicename",
        "timestamp": 1234567890,
        "metrics": {
          "cpu_usage": {
            "value": "75.5",
            "unit": "%"
          }
        }
      }
    },
    "pagination": {
      "limit": 100,
      "offset": 0,
      "total": 150,
      "returned": 100
    }
  }
}
```

### Time-Series Response
```json
{
  "success": true,
  "data": {
    "timeseries": {
      "resultType": "matrix",
      "result": [
        {
          "metric": {
            "host": "hostname",
            "service": "servicename",
            "metric": "cpu_usage"
          },
          "values": [
            [1640995200, "75.5"],
            [1640995260, "76.2"],
            [1640995320, "74.8"]
          ]
        }
      ]
    },
    "query_params": {
      "host": "hostname",
      "service": "servicename",
      "metric": "cpu_usage",
      "start": "2025-08-13T00:00:00Z",
      "end": "2025-08-13T01:00:00Z",
      "step": "1m"
    }
  }
}
```

### SRE Reliability Response
```json
{
  "success": true,
  "data": {
    "service": "cpu.utilization",
    "host_filter": "ncpa_host",
    "time_window": 86400,
    "measurement_period": {
      "start": "2025-08-12T20:45:51.573332",
      "end": "2025-08-13T20:45:51.573332"
    },
    "availability_percentage": 100.0,
    "total_instances": 1,
    "healthy_instances": 1,
    "unhealthy_instances": 0,
    "service_breakdown": {
      "ok": 1,
      "warning": 0,
      "critical": 0,
      "unknown": 0
    },
    "performance_metrics": [],
    "recommendations": []
  }
}
```

## Usage Examples

### Core API Examples

#### Get Host Status Over Time
```bash
curl "http://localhost/nagprom/api/v1/timeseries/hosts?host=webserver&start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=1m"
```

#### Get Service Performance Over Time
```bash
curl "http://localhost/nagprom/api/v1/timeseries/performance?host=webserver&service=apache&metric=cpu_usage&start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=5m"
```

#### Get All Services for a Host Over Time
```bash
curl "http://localhost/nagprom/api/v1/timeseries/services?host=webserver&start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=1m"
```

### SRE Analytics Examples

#### Create an SLO
```bash
curl -X POST "http://localhost/nagprom/api/v1/sre/slo" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "service": "web-service",
    "name": "Web Service Availability",
    "sli_type": "availability",
    "target_percentage": 99.9,
    "measurement_window_days": 30
  }'
```

#### Get Service Reliability
```bash
curl "http://localhost/nagprom/api/v1/sre/service/reliability?service=cpu.utilization&hours=24"
```

#### Get Host Reliability
```bash
curl "http://localhost/nagprom/api/v1/sre/host/reliability?host=localhost&hours=24"
```

#### Get Performance Anomalies
```bash
# All anomalies
curl "http://localhost/nagprom/api/v1/sre/anomalies?threshold_std=2.0"

# Anomalies for specific service
curl "http://localhost/nagprom/api/v1/sre/anomalies?threshold_std=2.0&service=cpu.utilization"

# Anomalies for specific host
curl "http://localhost/nagprom/api/v1/sre/anomalies?threshold_std=2.0&host=localhost"

# Anomalies for specific service on specific host
curl "http://localhost/nagprom/api/v1/sre/anomalies?threshold_std=2.0&service=cpu.utilization&host=localhost"
```

#### List All SLOs
```bash
curl "http://localhost/nagprom/api/v1/sre/slo"
```

## Configuration

### Environment Variables
- `PROMETHEUS_URL` - Prometheus server URL (default: http://localhost:9090)
- `NAGPROM_API_KEY` - API key for authentication (optional)

### Command Line Options
```bash
python3 nagprom_rest_api.py --host 127.0.0.1 --port 5000 --prometheus-url http://localhost:9090
```

## Post-Installation Verification

### Automatic Testing
The installer includes verification steps that test:
1. Basic API health
2. SRE endpoint availability
3. Service reliability calculations
4. Host reliability calculations

### Manual Testing Commands
```bash
# Test basic endpoints
curl http://localhost/nagprom/api/v1/health
curl http://localhost/nagprom/api/v1/sre/slo
curl http://localhost/nagprom/api/v1/sre/anomalies

# Test SRE features
curl "http://localhost/nagprom/api/v1/sre/service/reliability?service=cpu.utilization"
curl "http://localhost/nagprom/api/v1/sre/host/reliability?host=localhost"
```

## Files

- `nagprom_rest_api.py` - Main API server
- `requirements.txt` - Python dependencies
- `requirements-conservative.txt` - Fallback dependencies
- `install.sh` - Installation script
- `fix-dependencies.sh` - Dependency troubleshooting script
- `nagprom-api.service` - Systemd service
- `apache-nagprom.conf` - Apache configuration
- `README.md` - This file

## Troubleshooting

### API not starting
- Check logs: `journalctl -u nagprom-api`
- Verify Python dependencies: `pip3 install -r requirements.txt`
- Try conservative dependencies: `pip3 install -r requirements-conservative.txt`
- Run dependency fix script: `./fix-dependencies.sh`
- Check permissions: `chown nagios:nagios /opt/nagprom`

### Apache proxy not working
- Enable modules: `sudo a2enmod proxy proxy_http headers`
- Restart Apache: `sudo systemctl restart apache2`
- Check config: `apache2ctl configtest`

### Prometheus connection fails
- Verify Prometheus is running: `systemctl status prometheus`
- Check URL in configuration
- Test connectivity: `curl http://localhost:9090/api/v1/query?query=up`

### SRE features not working
- Check analytics directory exists: `ls -la /opt/nagprom/analytics/`
- Verify numpy/pandas installation: `pip3 list | grep -E "(numpy|pandas)"`
- Check API logs for import errors: `journalctl -u nagprom-api | grep -i error`

### Common Issues
1. **Import Errors**: Ensure analytics directory is properly created
2. **Dependency Issues**: Verify numpy and pandas are installed
3. **Permission Errors**: Check file ownership and permissions
4. **Rate Limiting**: Monitor for 429 errors in logs

### Logs
- API logs: `journalctl -u nagprom-api`
- Apache logs: `/var/log/apache2/error.log`

## Backward Compatibility

- All existing API endpoints remain unchanged
- Existing client applications continue to work
- No breaking changes to existing functionality
- Existing installations can be upgraded by running the installer again

## Support

For issues with the API:
1. Check API logs for error messages
2. Verify Prometheus connectivity
3. Test basic endpoints first
4. Check Python dependency installation
5. Review rate limiting configuration
