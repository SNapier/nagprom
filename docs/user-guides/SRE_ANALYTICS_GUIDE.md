# NagProm SRE Analytics Guide

## Overview

NagProm SRE Analytics provides advanced Site Reliability Engineering (SRE) metrics and insights integrated directly into your Nagios Core monitoring environment. This feature set enables you to track service reliability, manage SLOs/SLIs, detect anomalies, and gain operational insights.

## Features

### 🎯 SLO/SLI Management
- **Service Level Objectives (SLOs)**: Define and track reliability targets for your services
- **Service Level Indicators (SLIs)**: Monitor key metrics like availability, latency, and error rates
- **Error Budget Tracking**: Monitor how much error budget remains and burn rates

### 📊 Reliability Metrics
- **Service Reliability**: Real-time service availability tracking with detailed breakdowns
- **Host Reliability**: Host-level reliability metrics including service health
- **Availability Percentage**: Current availability calculations based on service states

### 🚨 Anomaly Detection
- **Performance Anomalies**: Statistical detection of unusual performance patterns using Z-score analysis
- **Configurable Thresholds**: Adjustable sensitivity for anomaly detection
- **Service and Host Filtering**: Focus on specific services or hosts

### 📈 Capacity Planning
- **Resource Utilization**: Monitor current resource usage
- **Service Distribution**: Track services per host and monitoring load
- **Basic Recommendations**: Get insights for capacity planning

## API Endpoints

### SRE Dashboard
```http
GET /api/v1/sre/dashboard
```
Returns basic SRE dashboard data including:
- Host and service uptime percentages
- Total counts of hosts and services
- Service breakdown by status

### Service Reliability
```http
GET /api/v1/sre/service/reliability?service={service_name}&host={host_name}&hours=24
```
Returns detailed reliability metrics for a specific service:
- Availability percentage
- Total and healthy instances
- Service breakdown by status (OK, WARNING, CRITICAL, UNKNOWN)
- Performance metrics
- Recommendations

### Host Reliability
```http
GET /api/v1/sre/host/reliability?host={host_name}&hours=24
```
Returns detailed reliability metrics for a specific host:
- Host availability percentage
- Total and healthy services
- Host status and service breakdown
- Service details with status
- Performance metrics
- Recommendations

### Anomaly Detection
```http
GET /api/v1/sre/anomalies?service={service_name}&host={host_name}&threshold_std=2.0
```
Returns detected performance anomalies:
- Anomaly details with severity
- Detection parameters
- Service and host filtering
- Pagination support

### Capacity Insights
```http
GET /api/v1/sre/capacity
```
Returns capacity planning insights:
- Total hosts and services
- Services per host ratio
- Monitoring load assessment
- Basic recommendations

### SLO Management
```http
POST /api/v1/sre/slo
Content-Type: application/json

{
  "service": "web-service",
  "name": "Web Service Availability",
  "sli_type": "availability",
  "target_percentage": 99.9,
  "measurement_window_days": 30,
  "error_budget_policy": "burn_rate"
}
```

```http
GET /api/v1/sre/slo
```
Returns all registered SLOs with their configurations.

## Rate Limiting

The SRE endpoints have specific rate limits to ensure system stability:
- **Service/Host Reliability**: 100 requests per hour
- **Anomaly Detection**: 50 requests per hour (lower limit for performance)
- **SLO Management**: 50 requests per hour
- **General SRE endpoints**: 1000 requests per day, 200 requests per hour

## Query Parameters

### Common Parameters
- `host`: Filter results by host name
- `service`: Filter results by service name
- `hours`: Time window for reliability calculations (default: 24)
- `threshold_std`: Standard deviation threshold for anomaly detection (default: 2.0)
- `limit`: Maximum number of results (default: 100, max: 1000)
- `offset`: Number of results to skip for pagination (default: 0)

### Time-Series Parameters
- `start`: Start time for timeseries queries (RFC3339 or Unix timestamp)
- `end`: End time for timeseries queries (RFC3339 or Unix timestamp)
- `step`: Step interval for timeseries queries (15s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 6h, 12h, 1d)

## SLI Types

### Availability
- **Description**: Percentage of time service is available
- **Calculation**: Healthy instances / Total instances
- **Target Range**: 99.0% - 99.99%

### Latency
- **Description**: Response time metrics
- **Calculation**: Based on performance data
- **Target Range**: Varies by service

### Error Rate
- **Description**: Percentage of failed requests
- **Calculation**: Failed requests / Total requests
- **Target Range**: < 0.1%

### Throughput
- **Description**: Requests per second
- **Calculation**: Total requests / Time period
- **Target Range**: Varies by service

## Error Budget Management

### Understanding Error Budgets
Error budgets represent the acceptable amount of unreliability for a service. For example:
- 99.9% SLO = 0.1% error budget
- 99.99% SLO = 0.01% error budget

### Burn Rate
Burn rate indicates how quickly the error budget is being consumed:
- **Low burn rate**: < 1% per day
- **Medium burn rate**: 1-5% per day
- **High burn rate**: > 5% per day

## Usage Examples

### Check Service Reliability
```bash
# Get reliability for a specific service
curl "http://localhost/nagprom/api/v1/sre/service/reliability?service=cpu.utilization&host=ncpa_host" \
  -H "X-API-Key: your-api-key"

# Get reliability for a service across all hosts
curl "http://localhost/nagprom/api/v1/sre/service/reliability?service=cpu.utilization" \
  -H "X-API-Key: your-api-key"
```

### Check Host Reliability
```bash
# Get reliability for a specific host
curl "http://localhost/nagprom/api/v1/sre/host/reliability?host=ncpa_host" \
  -H "X-API-Key: your-api-key"
```

### Detect Anomalies
```bash
# Get anomalies for a specific service
curl "http://localhost/nagprom/api/v1/sre/anomalies?service=cpu.utilization" \
  -H "X-API-Key: your-api-key"

# Get anomalies with custom threshold
curl "http://localhost/nagprom/api/v1/sre/anomalies?service=cpu.utilization&threshold_std=1.5" \
  -H "X-API-Key: your-api-key"
```

### Create SLO
```bash
curl -X POST "http://localhost/nagprom/api/v1/sre/slo" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "service": "cpu.utilization",
    "name": "CPU Utilization SLO",
    "sli_type": "availability",
    "target_percentage": 99.5,
    "measurement_window_days": 30
  }'
```

### List SLOs
```bash
curl "http://localhost/nagprom/api/v1/sre/slo" \
  -H "X-API-Key: your-api-key"
```

## Configuration

### API Configuration
The SRE Analytics features are integrated into the main NagProm API. Configure the API URL and authentication:

```bash
# Set API key as environment variable
export NAGPROM_API_KEY="your-api-key-here"
```

### Prometheus Integration
SRE Analytics relies on Prometheus for data collection. Ensure your Prometheus instance is:
- Collecting Nagios metrics
- Accessible to the NagProm API
- Configured with appropriate retention policies

## Best Practices

### SLO Definition
1. **Start Simple**: Begin with availability SLOs
2. **User-Centric**: Focus on user-facing metrics
3. **Measurable**: Ensure metrics can be reliably measured
4. **Achievable**: Set realistic targets based on current performance

### Anomaly Detection
1. **Start Conservative**: Begin with higher threshold_std values (2.0-3.0)
2. **Monitor Results**: Adjust thresholds based on detection accuracy
3. **Filter Appropriately**: Use service and host filters to focus on relevant data
4. **Review Regularly**: Periodically review and adjust detection parameters

### Reliability Monitoring
1. **Set Baselines**: Establish baseline reliability metrics
2. **Monitor Trends**: Track reliability over time
3. **Set Alerts**: Configure alerts for reliability thresholds
4. **Document Procedures**: Document response procedures for reliability issues

## Troubleshooting

### Common Issues

#### API Connection Errors
- Verify NagProm API is running: `systemctl status nagprom-api`
- Check API URL configuration
- Ensure API key is valid
- Check network connectivity

#### Missing Data
- Verify Prometheus is collecting metrics
- Check service names match between systems
- Ensure SLOs are properly registered
- Review API response for errors

#### Performance Issues
- Monitor API response times
- Check Prometheus query performance
- Optimize time range queries
- Consider data retention policies

### Debug Mode
Enable debug logging in the API:
```bash
curl "http://localhost/nagprom/api/v1/health?debug=true"
```

### Log Analysis
Check API logs for errors:
```bash
journalctl -u nagprom-api -f
```

## Integration Examples

### Grafana Integration
Use the SRE Analytics API to create Grafana dashboards:

```javascript
// Grafana data source configuration
{
  "url": "http://localhost/nagprom/api/v1",
  "headers": {
    "X-API-Key": "your-api-key"
  }
}
```

### Custom Dashboards
Create custom SRE dashboards using the API:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Custom SRE Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div id="sre-data"></div>
    
    <script>
        async function loadSREData() {
            const response = await fetch('/api/v1/sre/dashboard', {
                headers: {
                    'X-API-Key': 'your-api-key'
                }
            });
            const data = await response.json();
            
            // Update dashboard with data
            document.getElementById('sre-data').innerHTML = 
                `<h2>Host Uptime: ${data.data.host_uptime_percentage}%</h2>
                 <h2>Service Uptime: ${data.data.service_uptime_percentage}%</h2>`;
        }
        
        loadSREData();
        setInterval(loadSREData, 60000); // Refresh every minute
    </script>
</body>
</html>
```

## Support

For additional support and documentation:
- Check the main NagProm documentation
- Review API documentation at `/api/v1/`
- Submit issues to the project repository
- Join the community discussions

## Version History

### v1.0.0
- Initial SRE Analytics implementation
- Service and host reliability tracking
- Anomaly detection with configurable thresholds
- SLO/SLI management
- Basic capacity insights
- Rate limiting and pagination support
