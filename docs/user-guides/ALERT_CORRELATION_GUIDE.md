# Alert Correlation Guide

## Overview

NagProm's Alert Correlation Engine uses machine learning to automatically group related alerts, reducing noise and helping identify root causes faster.

## Features

- **Real-time Processing**: Alerts are analyzed immediately upon receipt
- **Multi-dimensional Correlation**: Temporal, spatial, similarity, and dependency-based
- **ML-powered Clustering**: Uses DBSCAN and TF-IDF for intelligent grouping
- **Root Cause Analysis**: Automatically identifies likely root causes
- **Noise Reduction**: Filters out false positives and duplicate alerts

## Quick Start

### 1. Send Alerts to NagProm

Configure your monitoring system to send alerts to the webhook endpoint:

```bash
# Example alert payload
curl -X POST http://localhost:8080/api/v1/sre/alerts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "id": "alert-001",
    "timestamp": "2024-01-15T10:30:00Z",
    "service": "web-service",
    "host": "web01",
    "severity": "critical",
    "title": "High Response Time",
    "description": "Response time exceeds 500ms threshold"
  }'
```

### 2. View Correlations

Access the correlation dashboard or API:

```bash
# Get correlations via API
curl "http://localhost:8080/api/v1/sre/alerts/correlation?time_window=900"

# Or visit the dashboard
http://localhost:8080/clients/nagios/correlation.php
```

### 3. Monitor Metrics

Track correlation effectiveness:

```bash
curl "http://localhost:8080/api/v1/sre/alerts/metrics"
```

## API Endpoints

### POST /api/v1/sre/alerts
**Webhook endpoint for receiving alerts**

**Required Fields:**
- `id`: Unique alert identifier
- `service`: Service name
- `host`: Host name
- `severity`: Alert severity (critical, warning, info)
- `title`: Alert title

**Optional Fields:**
- `timestamp`: Alert timestamp (ISO format)
- `description`: Alert description
- `status`: Alert status (firing, resolved)
- `fingerprint`: Alert fingerprint for deduplication

### GET /api/v1/sre/alerts/correlation
**Get current alert correlations**

**Query Parameters:**
- `time_window`: Time window in seconds (60-86400, default: 900)
- `service`: Filter by service name
- `host`: Filter by host name
- `type`: Filter by correlation type (temporal, spatial, similarity, dependency)

### GET /api/v1/sre/alerts/metrics
**Get correlation engine metrics**

Returns statistics about correlation effectiveness.

## Correlation Types

### Temporal Correlation
Groups alerts that occur within a short time window, indicating potential cascading failures.

### Spatial Correlation
Groups alerts from the same service or host, identifying localized issues.

### Similarity Correlation
Uses ML to group alerts with similar titles/descriptions, catching related issues.

### Dependency Correlation
Groups alerts based on service dependencies, identifying root causes in upstream services.

## Dashboard Features

The correlation dashboard provides:

- **Real-time Metrics**: Total alerts, correlation rate, clusters created
- **Filtering**: By time window, service, host, and correlation type
- **Cluster Details**: Root cause candidates, impact assessment, individual alerts
- **Auto-refresh**: Updates every 30 seconds

## Configuration

### Service Dependencies

Configure service dependencies for better correlation:

```python
from analytics.alert_correlation import AlertCorrelationEngine

engine = AlertCorrelationEngine()
dependencies = {
    'web-service': ['api-service', 'database'],
    'api-service': ['database', 'cache'],
    'database': [],
    'cache': []
}
engine.set_service_dependencies(dependencies)
```

### Custom Correlation Rules

Create custom correlation rules:

```python
from analytics.alert_correlation import CorrelationRule, CorrelationType

rule = CorrelationRule(
    id="database_cascade",
    name="Database Cascade Alerts",
    description="Correlate alerts when database issues cascade",
    correlation_type=CorrelationType.DEPENDENCY,
    conditions={
        "source_services": ["database"],
        "max_propagation_time": 300
    },
    time_window=timedelta(minutes=10),
    confidence_threshold=0.85
)
engine.register_correlation_rule(rule)
```

## Best Practices

### 1. Alert Quality
- Use descriptive titles and descriptions
- Include relevant metadata (service, host, severity)
- Provide consistent alert formats

### 2. Service Dependencies
- Define accurate service dependency maps
- Update dependencies when architecture changes
- Include both direct and indirect dependencies

### 3. Monitoring
- Track correlation metrics regularly
- Adjust time windows based on your environment
- Review and tune correlation rules

### 4. Integration
- Send alerts immediately when they fire
- Include resolution status updates
- Use consistent alert IDs for tracking

## Troubleshooting

### No Correlations Found
- Check if alerts are being received
- Verify alert format and required fields
- Increase time window if needed
- Check service dependency configuration

### Low Correlation Rate
- Review alert titles and descriptions
- Ensure service dependencies are accurate
- Consider adjusting correlation thresholds
- Check for alert format inconsistencies

### High False Positives
- Tune correlation confidence thresholds
- Review and update correlation rules
- Adjust time windows for your environment
- Consider adding noise patterns

## Performance Considerations

- **Memory Usage**: Engine stores up to 10,000 alerts in memory
- **Processing Time**: Correlation analysis runs asynchronously
- **API Limits**: 50 correlation requests per hour, 1000 alert ingestions per hour
- **Storage**: Clusters are stored in memory, not persisted

## Integration Examples

### Nagios Integration
```bash
# In Nagios command definition
define command {
    command_name notify_nagprom
    command_line curl -X POST http://localhost:8080/api/v1/sre/alerts \
        -H "Content-Type: application/json" \
        -d '{"id":"$HOSTNAME-$SERVICENAME-$TIMET","service":"$SERVICENAME","host":"$HOSTNAME","severity":"$SERVICESTATE","title":"$SERVICEOUTPUT"}'
}
```

### Prometheus Alertmanager
```yaml
# In alertmanager.yml
receivers:
  - name: 'nagprom'
    webhook_configs:
      - url: 'http://localhost:8080/api/v1/sre/alerts'
        send_resolved: true
```

### Custom Script
```python
import requests
import json
from datetime import datetime

def send_alert(alert_id, service, host, severity, title, description=""):
    payload = {
        "id": alert_id,
        "timestamp": datetime.now().isoformat(),
        "service": service,
        "host": host,
        "severity": severity,
        "title": title,
        "description": description
    }
    
    response = requests.post(
        "http://localhost:8080/api/v1/sre/alerts",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    return response.json()
```
