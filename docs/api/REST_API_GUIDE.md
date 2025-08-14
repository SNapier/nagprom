# NagProm REST API Technical Documentation

## Overview

The NagProm REST API provides programmatic access to Nagios monitoring data via Prometheus. The API exposes monitoring data, performance metrics, thresholds, and SRE analytics through a RESTful interface.

**Base URL:** `http://localhost:8080/api/v1/` (development) or `http://yourserver/nagprom/api/v1/` (production)

**Data Source:** Prometheus (default: `http://localhost:9090`)

## Authentication

### API Key Authentication

Authentication is optional and controlled by the `NAGPROM_API_KEY` environment variable.

**Configuration:**
```bash
# Enable authentication
export NAGPROM_API_KEY="your-secure-key-here"

# Disable authentication (default)
unset NAGPROM_API_KEY
```

**Usage:**
```bash
# Via HTTP header (recommended)
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/v1/summary

# Via query parameter
curl "http://localhost:5000/api/v1/summary?api_key=your-api-key"
```

**Public Endpoints (no authentication required):**
- `GET /api/v1/health`
- `GET /api/v1/`

## Rate Limiting

The API implements rate limiting to prevent abuse:

| Endpoint Category | Limit | Description |
|------------------|-------|-------------|
| Default | 1000/day, 200/hour | General endpoints |
| Hosts, Services, Metrics, Thresholds | 200/hour | Core monitoring data |
| Time-series | 100/hour | Historical data queries |
| SRE Reliability | 100/hour | Service/host reliability |
| SRE Anomalies | 50/hour | Anomaly detection |
| SRE SLO | 50/hour | SLO management |

## Response Format

All API responses follow a consistent format:

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2025-08-13T20:45:51.573567"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2025-08-13T20:45:51.573567"
}
```

## Core Endpoints

### Health Check

#### `GET /api/v1/health`

Returns API health status and configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "prometheus_connected": true,
    "api_key_required": false,
    "timestamp": "2025-08-13T20:45:51.573567"
  }
}
```

### API Documentation

#### `GET /api/v1/`

Returns available endpoints and configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "endpoints": {
      "health": "/api/v1/health",
      "summary": "/api/v1/summary",
      "hosts": "/api/v1/hosts",
      "services": "/api/v1/services",
      "metrics": "/api/v1/metrics",
      "thresholds": "/api/v1/thresholds",
      "timeseries_hosts": "/api/v1/timeseries/hosts",
      "timeseries_services": "/api/v1/timeseries/services",
      "timeseries_performance": "/api/v1/timeseries/performance",
      "sre_dashboard": "/api/v1/sre/dashboard",
      "sre_service_reliability": "/api/v1/sre/service/reliability?service={service}",
      "sre_host_reliability": "/api/v1/sre/host/reliability?host={host}",
      "sre_anomalies": "/api/v1/sre/anomalies",
      "sre_slo_create": "/api/v1/sre/slo (POST)",
      "sre_slo_list": "/api/v1/sre/slo (GET)"
    },
    "query_parameters": {
      "host": "Filter results by host name",
      "service": "Filter results by service name",
      "metric": "Filter performance data by metric name",
      "start": "Start time for timeseries queries (RFC3339 or Unix timestamp)",
      "end": "End time for timeseries queries (RFC3339 or Unix timestamp)",
      "step": "Step interval for timeseries queries (15s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 6h, 12h, 1d)",
      "limit": "Maximum number of results to return (default: 100, max: 1000)",
      "offset": "Number of results to skip for pagination (default: 0)",
      "api_key": "API key for authentication (if required)"
    },
    "rate_limits": {
      "default": "1000 requests per day, 200 requests per hour",
      "hosts": "200 requests per hour",
      "services": "200 requests per hour",
      "metrics": "200 requests per hour",
      "thresholds": "200 requests per hour",
      "timeseries": "100 requests per hour (lower limit for performance)",
      "sre_reliability": "100 requests per hour",
      "sre_anomalies": "50 requests per hour (lower limit for performance)",
      "sre_slo": "50 requests per hour"
    },
    "authentication_required": false,
    "prometheus_url": "http://localhost:9090"
  }
}
```

### Monitoring Summary

#### `GET /api/v1/summary`

Returns monitoring overview with host and service counts.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_hosts": 2,
    "total_services": 8,
    "host_states": {
      "0": 2
    },
    "service_states": {
      "0": 7,
      "1": 1
    },
    "up_hosts": 2,
    "down_hosts": 0,
    "ok_services": 7,
    "warning_services": 1,
    "critical_services": 0,
    "unknown_services": 0
  }
}
```

### Hosts

#### `GET /api/v1/hosts`

Returns all monitored hosts with pagination support.

**Query Parameters:**
- `host`: Filter by host name
- `limit`: Maximum results (default: 100, max: 1000)
- `offset`: Skip results (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "hosts": [
      {
        "name": "ncpa_host",
        "state": "0",
        "state_type": "hard",
        "last_check": 1734123456
      }
    ],
    "pagination": {
      "limit": 100,
      "offset": 0,
      "total": 1,
      "returned": 1
    }
  }
}
```

### Services

#### `GET /api/v1/services`

Returns all monitored services with pagination support.

**Query Parameters:**
- `host`: Filter by host name
- `service`: Filter by service name
- `limit`: Maximum results (default: 100, max: 1000)
- `offset`: Skip results (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "services": [
      {
        "host": "ncpa_host",
        "service": "cpu.utilization",
        "state": "0",
        "state_type": "hard",
        "last_check": 1734123456
      }
    ],
    "pagination": {
      "limit": 100,
      "offset": 0,
      "total": 8,
      "returned": 8
    }
  }
}
```

### Performance Metrics

#### `GET /api/v1/metrics`

Returns performance data with pagination support.

**Query Parameters:**
- `host`: Filter by host name
- `service`: Filter by service name
- `limit`: Maximum results (default: 100, max: 1000)
- `offset`: Skip results (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "metrics": {
      "ncpa_host:cpu.utilization": {
        "host": "ncpa_host",
        "service": "cpu.utilization",
        "timestamp": 1734123456,
        "metrics": {
          "cpu_usage": {
            "value": 15.2,
            "unit": "%"
          }
        }
      }
    },
    "pagination": {
      "limit": 100,
      "offset": 0,
      "total": 1,
      "returned": 1
    }
  }
}
```

### Performance Thresholds

#### `GET /api/v1/thresholds`

Returns performance thresholds with pagination support.

**Query Parameters:**
- `host`: Filter by host name
- `service`: Filter by service name
- `limit`: Maximum results (default: 100, max: 1000)
- `offset`: Skip results (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "thresholds": {
      "ncpa_host:cpu.utilization": {
        "host": "ncpa_host",
        "service": "cpu.utilization",
        "thresholds": {
          "cpu_usage": {
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
      "total": 1,
      "returned": 1
    }
  }
}
```

## Time-Series Endpoints

### Host Time-Series

#### `GET /api/v1/timeseries/hosts`

Returns time-series data for hosts.

**Query Parameters:**
- `host`: Filter by host name
- `start`: Start time (RFC3339 or Unix timestamp) - **required**
- `end`: End time (RFC3339 or Unix timestamp) - **required**
- `step`: Step interval (15s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 6h, 12h, 1d) - default: 1m

**Response:**
```json
{
  "success": true,
  "data": {
    "timeseries": {
      "resultType": "matrix",
      "result": [
        {
          "metric": {
            "host": "ncpa_host"
          },
          "values": [
            [1734123456, "0"],
            [1734123516, "0"]
          ]
        }
      ]
    },
    "query_params": {
      "host": "ncpa_host",
      "start": "2025-08-13T00:00:00Z",
      "end": "2025-08-13T01:00:00Z",
      "step": "1m"
    }
  }
}
```

### Service Time-Series

#### `GET /api/v1/timeseries/services`

Returns time-series data for services.

**Query Parameters:**
- `host`: Filter by host name
- `service`: Filter by service name
- `start`: Start time (RFC3339 or Unix timestamp) - **required**
- `end`: End time (RFC3339 or Unix timestamp) - **required**
- `step`: Step interval (15s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 6h, 12h, 1d) - default: 1m

**Response:**
```json
{
  "success": true,
  "data": {
    "timeseries": {
      "resultType": "matrix",
      "result": [
        {
          "metric": {
            "host": "ncpa_host",
            "service": "cpu.utilization"
          },
          "values": [
            [1734123456, "0"],
            [1734123516, "0"]
          ]
        }
      ]
    },
    "query_params": {
      "host": "ncpa_host",
      "service": "cpu.utilization",
      "start": "2025-08-13T00:00:00Z",
      "end": "2025-08-13T01:00:00Z",
      "step": "1m"
    }
  }
}
```

### Performance Time-Series

#### `GET /api/v1/timeseries/performance`

Returns time-series data for performance metrics.

**Query Parameters:**
- `host`: Filter by host name
- `service`: Filter by service name
- `metric`: Filter by metric name
- `start`: Start time (RFC3339 or Unix timestamp) - **required**
- `end`: End time (RFC3339 or Unix timestamp) - **required**
- `step`: Step interval (15s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 6h, 12h, 1d) - default: 1m

**Response:**
```json
{
  "success": true,
  "data": {
    "timeseries": {
      "resultType": "matrix",
      "result": [
        {
          "metric": {
            "host": "ncpa_host",
            "service": "cpu.utilization",
            "metric": "cpu_usage"
          },
          "values": [
            [1734123456, "15.2"],
            [1734123516, "16.1"]
          ]
        }
      ]
    },
    "query_params": {
      "host": "ncpa_host",
      "service": "cpu.utilization",
      "metric": "cpu_usage",
      "start": "2025-08-13T00:00:00Z",
      "end": "2025-08-13T01:00:00Z",
      "step": "1m"
    }
  }
}
```

## SRE Analytics Endpoints

### SRE Dashboard

#### `GET /api/v1/sre/dashboard`

Returns basic SRE dashboard data.

**Response:**
```json
{
  "success": true,
  "data": {
    "host_uptime_percentage": 100.0,
    "service_uptime_percentage": 87.5,
    "total_hosts": 2,
    "up_hosts": 2,
    "down_hosts": 0,
    "total_services": 8,
    "ok_services": 7,
    "problem_services": 1,
    "last_updated": "2025-08-13T20:45:51.573567"
  }
}
```

### Service Reliability

#### `GET /api/v1/sre/service/reliability`

Returns detailed reliability metrics for services.

**Query Parameters:**
- `service`: Service name - **required**
- `host`: Filter by host name
- `hours`: Time window in hours (default: 24)

**Response:**
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

### Host Reliability

#### `GET /api/v1/sre/host/reliability`

Returns detailed reliability metrics for hosts.

**Query Parameters:**
- `host`: Host name - **required**
- `hours`: Time window in hours (default: 24)

**Response:**
```json
{
  "success": true,
  "data": {
    "host": "ncpa_host",
    "time_window": 86400,
    "measurement_period": {
      "start": "2025-08-12T20:45:51.573332",
      "end": "2025-08-13T20:45:51.573332"
    },
    "availability_percentage": 87.5,
    "total_services": 8,
    "healthy_services": 7,
    "unhealthy_services": 1,
    "host_state": "0",
    "host_status": "OK",
    "service_breakdown": {
      "ok": 7,
      "warning": 1,
      "critical": 0,
      "unknown": 0
    },
    "performance_metrics": [],
    "service_details": [
      {
        "service": "cpu.utilization",
        "state": "0",
        "status": "OK",
        "last_check": "unknown"
      }
    ],
    "recommendations": []
  }
}
```

### Anomaly Detection

#### `GET /api/v1/sre/anomalies`

Returns detected performance anomalies.

**Query Parameters:**
- `service`: Filter by service name
- `host`: Filter by host name
- `threshold_std`: Standard deviation threshold (default: 2.0)
- `limit`: Maximum results (default: 100, max: 1000)
- `offset`: Skip results (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "anomalies": [
      {
        "service": "cpu.utilization",
        "metric": "cpu_usage",
        "value": 95.2,
        "baseline_mean": 15.3,
        "baseline_std": 5.2,
        "z_score": 15.4,
        "severity": "high",
        "timestamp": "2025-08-13T20:45:51.573567"
      }
    ],
    "total_anomalies": 1,
    "pagination": {
      "limit": 100,
      "offset": 0,
      "returned": 1
    },
    "detection_params": {
      "threshold_std": 2.0,
      "service_filter": null,
      "host_filter": null
    }
  }
}
```

### SLO Management

#### `GET /api/v1/sre/slo`

Returns all registered SLOs.

**Response:**
```json
{
  "success": true,
  "data": {
    "cpu.utilization": [
      {
        "name": "CPU Utilization SLO",
        "sli_type": "availability",
        "target_percentage": 99.5,
        "error_budget_percentage": 0.5,
        "measurement_window_days": 30,
        "error_budget_policy": "burn_rate"
      }
    ]
  }
}
```

#### `POST /api/v1/sre/slo`

Creates a new SLO target.

**Request Body:**
```json
{
  "service": "cpu.utilization",
  "name": "CPU Utilization SLO",
  "sli_type": "availability",
  "target_percentage": 99.5,
  "measurement_window_days": 30,
  "error_budget_policy": "burn_rate"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "slo_created": true,
    "service": "cpu.utilization",
    "slo_name": "CPU Utilization SLO",
    "target_percentage": 99.5,
    "error_budget_percentage": 0.5
  }
}
```

### Capacity Insights

#### `GET /api/v1/sre/capacity`

Returns capacity planning insights.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_hosts": 2,
    "total_services": 8,
    "services_per_host": 4.0,
    "monitoring_load": "low",
    "recommendations": [
      "Monitor host resource usage",
      "Review service check intervals",
      "Consider load balancing for high-traffic services"
    ],
    "last_updated": "2025-08-13T20:45:51.573567"
  }
}
```

## Debug Endpoints

### Debug Metrics

#### `GET /api/v1/debug/metrics`

Returns available metrics and sample data.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_metrics": 150,
    "nagios_metrics": [
      "nagios_host_state",
      "nagios_service_state",
      "nagios_performance_data"
    ],
    "prometheus_url": "http://localhost:9090",
    "sample_metrics": [...],
    "sample_host_data": {...},
    "sample_service_data": {...},
    "sample_performance_data": {...},
    "processed_hosts": [...],
    "processed_services": [...],
    "processed_performance": {...}
  }
}
```

### Debug Thresholds

#### `GET /api/v1/debug/thresholds`

Returns threshold debugging information.

**Response:**
```json
{
  "success": true,
  "data": {
    "raw_thresholds_query": "nagios_performance_thresholds",
    "raw_thresholds_data": {...},
    "processed_thresholds": {...},
    "performance_data": {...},
    "thresholds_count": 5,
    "performance_count": 10,
    "prometheus_url": "http://localhost:9090"
  }
}
```

## Data Structures

### Host State Values

| Value | Status | Description |
|-------|--------|-------------|
| 0 | UP | Host is up and responding |
| 1 | DOWN | Host is down or unreachable |
| 2 | UNREACHABLE | Host is unreachable through parent |

### Service State Values

| Value | Status | Description |
|-------|--------|-------------|
| 0 | OK | Service is working normally |
| 1 | WARNING | Service has a warning condition |
| 2 | CRITICAL | Service has a critical condition |
| 3 | UNKNOWN | Service state is unknown |

### Threshold Types

| Type | Description |
|------|-------------|
| warning | Warning threshold (orange alert) |
| critical | Critical threshold (red alert) |
| min | Minimum acceptable value |
| max | Maximum acceptable value |

### SLI Types

| Type | Description |
|------|-------------|
| availability | Service availability percentage |
| latency | Response time metrics |
| error_rate | Error rate percentage |
| throughput | Requests per second |

## Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid API key |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Usage Examples

### Basic Monitoring Check

```bash
# Check API health
curl http://localhost:5000/api/v1/health

# Get monitoring summary
curl -H "X-API-Key: your-key" http://localhost:5000/api/v1/summary

# Get critical services
curl -H "X-API-Key: your-key" "http://localhost:5000/api/v1/services?state=2"
```

### Performance Monitoring

```bash
# Get performance data for specific host
curl -H "X-API-Key: your-key" "http://localhost:5000/api/v1/metrics?host=ncpa_host"

# Get thresholds for specific service
curl -H "X-API-Key: your-key" "http://localhost:5000/api/v1/thresholds?host=ncpa_host&service=cpu.utilization"

# Get time-series data
curl -H "X-API-Key: your-key" "http://localhost:5000/api/v1/timeseries/performance?host=ncpa_host&service=cpu.utilization&start=2025-08-13T00:00:00Z&end=2025-08-13T01:00:00Z&step=5m"
```

### SRE Analytics

```bash
# Get service reliability
curl -H "X-API-Key: your-key" "http://localhost:5000/api/v1/sre/service/reliability?service=cpu.utilization&host=ncpa_host"

# Get host reliability
curl -H "X-API-Key: your-key" "http://localhost:5000/api/v1/sre/host/reliability?host=ncpa_host"

# Get anomalies
curl -H "X-API-Key: your-key" "http://localhost:5000/api/v1/sre/anomalies?service=cpu.utilization&threshold_std=2.0"

# Create SLO
curl -X POST -H "X-API-Key: your-key" -H "Content-Type: application/json" \
  -d '{"service":"cpu.utilization","name":"CPU SLO","sli_type":"availability","target_percentage":99.5}' \
  http://localhost:5000/api/v1/sre/slo
```

### Pagination

```bash
# Get first 10 services
curl -H "X-API-Key: your-key" "http://localhost:5000/api/v1/services?limit=10"

# Get next 10 services
curl -H "X-API-Key: your-key" "http://localhost:5000/api/v1/services?limit=10&offset=10"
```

## Integration Examples

### Python Client

```python
import requests
import json

class NagPromAPI:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.headers = {'X-API-Key': api_key} if api_key else {}
    
    def get_summary(self):
        response = requests.get(f"{self.base_url}/api/v1/summary", headers=self.headers)
        return response.json()
    
    def get_critical_services(self):
        response = requests.get(f"{self.base_url}/api/v1/services?state=2", headers=self.headers)
        return response.json()
    
    def get_service_reliability(self, service, host=None):
        params = {'service': service}
        if host:
            params['host'] = host
        response = requests.get(f"{self.base_url}/api/v1/sre/service/reliability", 
                              params=params, headers=self.headers)
        return response.json()

# Usage
api = NagPromAPI('http://localhost:5000', 'your-api-key')
summary = api.get_summary()
critical = api.get_critical_services()
reliability = api.get_service_reliability('cpu.utilization', 'ncpa_host')
```

### JavaScript Client

```javascript
class NagPromAPI {
    constructor(baseUrl, apiKey = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.headers = apiKey ? { 'X-API-Key': apiKey } : {};
    }
    
    async getSummary() {
        const response = await fetch(`${this.baseUrl}/api/v1/summary`, {
            headers: this.headers
        });
        return response.json();
    }
    
    async getCriticalServices() {
        const response = await fetch(`${this.baseUrl}/api/v1/services?state=2`, {
            headers: this.headers
        });
        return response.json();
    }
    
    async getServiceReliability(service, host = null) {
        const params = new URLSearchParams({ service });
        if (host) params.append('host', host);
        
        const response = await fetch(`${this.baseUrl}/api/v1/sre/service/reliability?${params}`, {
            headers: this.headers
        });
        return response.json();
    }
}

// Usage
const api = new NagPromAPI('http://localhost:5000', 'your-api-key');
const summary = await api.getSummary();
const critical = await api.getCriticalServices();
const reliability = await api.getServiceReliability('cpu.utilization', 'ncpa_host');
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROMETHEUS_URL` | Prometheus server URL | `http://localhost:9090` |
| `NAGPROM_API_KEY` | API key for authentication | `None` (disabled) |

### Command Line Options

```bash
python3 nagprom_rest_api.py [options]

Options:
  --host HOST           Host to bind to (default: 127.0.0.1)
  --port PORT           Port to bind to (default: 5000)
  --prometheus-url URL  Prometheus URL (default: http://localhost:9090)
  --api-key KEY         API key for authentication
  --debug               Enable debug mode
```

## Performance Considerations

1. **Use pagination** for large datasets (`limit` and `offset` parameters)
2. **Filter results** using query parameters to reduce data transfer
3. **Cache responses** for frequently accessed data
4. **Monitor rate limits** to avoid 429 errors
5. **Use appropriate time ranges** for time-series queries

## Security Best Practices

1. **Enable API key authentication** in production
2. **Use HTTPS** for external access
3. **Implement proper CORS** configuration
4. **Monitor API usage** and set appropriate rate limits
5. **Regularly rotate API keys**
6. **Validate all input parameters**
