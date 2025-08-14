# NagProm Advanced Analytics

This directory contains the advanced analytics components of NagProm Phase 3, providing sophisticated SRE/DevOps analytics, alert correlation, and predictive monitoring capabilities.

## 🧠 Components Overview

### 📊 SRE Analytics Engine (`sre_analytics_engine.py`)
Comprehensive Service Reliability Engineering analytics platform.

**Features:**
- **SLI/SLO Management**: Define and track Service Level Objectives
- **Error Budget Tracking**: Monitor error budget consumption and burn rates
- **Reliability Metrics**: Calculate MTTR, MTBF, and availability percentages
- **Trend Analysis**: Identify performance trends and degradation patterns
- **Capacity Planning**: Analyze resource utilization and predict capacity needs
- **Business Impact Analysis**: Calculate revenue impact of incidents
- **Anomaly Detection**: Statistical anomaly detection for performance metrics

**Key Classes:**
- `SREAnalyticsEngine`: Main analytics engine
- `SLOTarget`: SLO definition and tracking
- `SLIMetric`: Service Level Indicator measurements
- `AlertEvent`: Alert event data structure
- `IncidentImpact`: Incident impact analysis

### 🌐 Integrated SRE Analytics
SRE analytics are now **embedded within the main NagProm REST API** (`nagprom-api/api/nagprom_rest_api.py`) instead of running as a separate service.

**Features:**
- **Embedded Processing**: Background analytics within main API process
- **REST API Integration**: SRE endpoints added to existing API
- **PHP Dashboard**: Nagios-integrated dashboard (`clients/nagios/sre_analytics.php`)
- **Shared Infrastructure**: Uses existing Prometheus connections
- **Unified Service**: Single process, single port, unified management

**Integrated API Endpoints:**
```bash
GET  /api/v1/sre/dashboard                        # SRE dashboard data
GET  /api/v1/sre/service/{service}/reliability    # Service reliability
GET  /api/v1/sre/alerts/correlation               # Alert correlation
GET  /api/v1/sre/capacity                         # Capacity insights
POST /api/v1/sre/slo                              # Register SLO
GET  /api/v1/webhooks                             # List webhooks
POST /api/v1/webhooks                             # Register webhook
```

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                NagProm REST API                         │
│                   (Port 8080)                          │
├─────────────────────────────────────────────────────────┤
│  Original API     │  SRE Analytics  │  Alert Correlation │
│  - /api/v1/hosts  │  - /api/v1/sre  │  - Background      │
│  - /api/v1/services│  - Embedded     │  - Processing      │
│  - /api/v1/dashboard│  - Processing   │  - Webhooks        │
└─────────────────────────────────────────────────────────┘
```

### 🔍 Alert Correlation Engine (`alert_correlation.py`)
Advanced alert correlation and pattern recognition system.

**Features:**
- **Multi-dimensional Correlation**: Temporal, spatial, similarity, dependency-based
- **Pattern Recognition**: Identify recurring alert patterns
- **Alert Clustering**: Group related alerts intelligently
- **Root Cause Analysis**: Automated RCA suggestions
- **Noise Reduction**: Filter out alert noise and duplicates
- **Predictive Alerting**: Predict future alerts based on patterns
- **Incident Timeline**: Reconstruct incident progression
- **Machine Learning**: DBSCAN clustering and TF-IDF similarity

**Correlation Types:**
- **Temporal**: Time-based alert grouping
- **Spatial**: Location/service proximity correlation
- **Similarity**: Content similarity using NLP
- **Dependency**: Service dependency-based correlation
- **Pattern**: Historical pattern matching

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Additional ML dependencies
pip install scikit-learn pandas numpy networkx
```

### Basic Usage

#### SRE Analytics Engine

```python
from sre_analytics_engine import SREAnalyticsEngine, SLOTarget, SLIMetric, SLIType
from datetime import datetime, timedelta

# Initialize engine
engine = SREAnalyticsEngine()

# Register SLO
slo = SLOTarget(
    name="web_service_availability",
    sli_type=SLIType.AVAILABILITY,
    target_percentage=99.9,
    measurement_window=timedelta(days=30)
)
engine.register_slo("web-service", slo)

# Record SLI metric
sli = SLIMetric(
    timestamp=datetime.now(),
    service="web-service",
    sli_type=SLIType.AVAILABILITY,
    value=0.999,
    success_count=9990,
    total_count=10000
)
engine.record_sli_metric(sli)

# Get reliability metrics
reliability = engine.calculate_service_reliability("web-service")
print(f"Service reliability: {reliability}")
```

#### Integrated SRE Analytics

```bash
# Start the main NagProm API (includes SRE analytics)
python nagprom-api/api/nagprom_rest_api.py --host 0.0.0.0 --port 8080

# Access SRE dashboard (Nagios integration)
http://localhost/nagios/sre_analytics.php

# API usage (integrated endpoints)
curl http://localhost:8080/api/v1/sre/dashboard
curl http://localhost:8080/api/v1/sre/service/web-service/reliability
```

#### Alert Correlation

```python
from alert_correlation import AlertCorrelationEngine, Alert, AlertSeverity, AlertStatus
from datetime import datetime
import uuid

# Initialize engine
engine = AlertCorrelationEngine()

# Set service dependencies
dependencies = {
    'web-service': ['api-service', 'database'],
    'api-service': ['database', 'cache'],
    'database': [],
    'cache': []
}
engine.set_service_dependencies(dependencies)

# Add alerts
alert = Alert(
    id=str(uuid.uuid4()),
    timestamp=datetime.now(),
    service="web-service",
    host="web01",
    severity=AlertSeverity.CRITICAL,
    status=AlertStatus.FIRING,
    title="High Response Time",
    description="Response time exceeds threshold"
)
engine.add_alert(alert)

# Perform correlation
clusters = await engine.correlate_alerts()
for cluster in clusters:
    print(f"Cluster: {cluster.id}, Alerts: {len(cluster.alerts)}")
```

## 📈 Advanced Features

### SLO Management

```python
# Define complex SLOs
latency_slo = SLOTarget(
    name="api_latency_p99",
    sli_type=SLIType.LATENCY,
    target_percentage=99.0,
    measurement_window=timedelta(days=7),
    error_budget_policy="burn_rate"
)

# Calculate error budget
error_budget = engine.calculate_error_budget(service, slo, start_time, end_time)
print(f"Error budget remaining: {error_budget['budget_remaining_percentage']}%")
```

### Alert Pattern Recognition

```python
# Detect alert patterns
patterns = engine.detect_alert_patterns(lookback_period=timedelta(days=30))
print(f"Found {len(patterns['patterns'])} patterns")

# Predict future alerts
prediction = engine.predict_alerts("web-service", time_horizon=timedelta(hours=4))
print(f"Prediction score: {prediction['prediction_score']}")
```

### Anomaly Detection

```python
# Detect anomalies for a service
anomalies = engine.detect_anomalies("web-service", threshold_std=2.0)
for anomaly in anomalies:
    print(f"Anomaly detected: {anomaly['timestamp']}, value: {anomaly['value']}")
```

### Custom Correlation Rules

```python
from alert_correlation import CorrelationRule, CorrelationType

# Define custom correlation rule
custom_rule = CorrelationRule(
    id="database_cascade",
    name="Database Cascade Alerts",
    description="Correlate alerts when database issues cascade to dependent services",
    correlation_type=CorrelationType.DEPENDENCY,
    conditions={
        "source_services": ["database"],
        "max_propagation_time": 300  # 5 minutes
    },
    time_window=timedelta(minutes=10),
    confidence_threshold=0.85
)

engine.register_correlation_rule(custom_rule)
```

## 🔧 Configuration

### Environment Variables

```bash
# NagProm API Configuration (analytics embedded)
NAGPROM_API_PORT=8080
PROMETHEUS_URL=http://localhost:9090
NAGPROM_API_KEY=your-api-key

# Alert Correlation Configuration  
CORRELATION_WINDOW=900  # 15 minutes
MIN_CLUSTER_SIZE=2
CONFIDENCE_THRESHOLD=0.7

# Analytics Configuration
DATA_RETENTION_DAYS=90
ANOMALY_DETECTION_ENABLED=true
PATTERN_LEARNING_ENABLED=true
```

### Configuration Files

#### `sre_config.yaml`
```yaml
sre_analytics:
  default_slo_window: "30d"
  error_budget_policy: "burn_rate"
  anomaly_detection:
    enabled: true
    threshold_std: 2.0
    window_size: "1h"
  
  capacity_planning:
    prediction_horizon: "7d"
    growth_factor: 1.2
    utilization_threshold: 80
```

#### `correlation_config.yaml`
```yaml
alert_correlation:
  correlation_window: "15m"
  min_cluster_size: 2
  confidence_threshold: 0.7
  
  correlation_types:
    temporal:
      max_gap: "2m"
      enabled: true
    
    spatial:
      same_service_weight: 0.9
      same_host_weight: 0.8
      enabled: true
    
    similarity:
      text_similarity_threshold: 0.8
      enabled: true
    
    dependency:
      max_hop_distance: 3
      enabled: true
  
  noise_reduction:
    enabled: true
    frequency_threshold: 0.1
    pattern_learning: true
```

## 📊 Monitoring and Metrics

### SRE Engine Metrics

```python
# Get engine statistics
stats = engine.get_engine_stats()
print(f"SLI metrics processed: {stats['sli_metrics_processed']}")
print(f"SLOs tracked: {stats['slos_tracked']}")
print(f"Error budgets: {stats['error_budgets']}")
```

### Correlation Engine Metrics

```python
# Get correlation statistics
metrics = engine.get_correlation_metrics()
print(f"Correlation rate: {metrics['correlation_rate']}%")
print(f"Noise reduction: {metrics['noise_reduction_rate']}%")
print(f"Active clusters: {metrics['active_clusters']}")
```

### Performance Monitoring

Both engines include built-in performance monitoring:

- **Execution time tracking**
- **Memory usage monitoring**
- **API call statistics**
- **Error rate tracking**
- **Cache hit rates**

## 🤖 Machine Learning Features

### Alert Clustering

Uses DBSCAN clustering algorithm for grouping similar alerts:

```python
# Clustering parameters
clustering_params = {
    'eps': 0.3,           # Maximum distance between points
    'min_samples': 2,     # Minimum cluster size
    'metric': 'cosine'    # Distance metric
}
```

### Text Similarity

TF-IDF vectorization for alert content similarity:

```python
# TF-IDF parameters
tfidf_params = {
    'max_features': 1000,
    'stop_words': 'english',
    'ngram_range': (1, 2)
}
```

### Anomaly Detection

Statistical anomaly detection using z-score analysis:

```python
# Anomaly detection parameters
anomaly_params = {
    'threshold_std': 2.0,    # Z-score threshold
    'window_size': 100,      # Rolling window size
    'min_samples': 10        # Minimum samples for detection
}
```

## 🔌 Integration

### Prometheus Integration

```python
# Connect to Prometheus
from prometheus_api_client import PrometheusConnect

prom = PrometheusConnect(url="http://localhost:9090")
engine.set_prometheus_client(prom)

# Auto-import metrics
engine.import_prometheus_metrics(['up', 'http_requests_total'])
```

### Grafana Integration

```python
# Export SLO dashboard
dashboard_json = engine.export_grafana_dashboard("web-service")
# Import to Grafana via API
```

### Webhook Integration

```python
# Send alerts to correlation engine via webhook
@app.route('/webhook/alerts', methods=['POST'])
def webhook_alerts():
    alert_data = request.json
    alert = Alert.from_dict(alert_data)
    correlation_engine.add_alert(alert)
    return {'status': 'received'}
```

## 🧪 Testing

### Unit Tests

```bash
# Run SRE analytics tests
python -m pytest tests/test_sre_analytics.py

# Run correlation tests  
python -m pytest tests/test_alert_correlation.py

# Run integration tests
python -m pytest tests/test_integration.py
```

### Load Testing

```bash
# Simulate high alert volume
python tests/load_test_correlation.py --alerts-per-second 100 --duration 60

# SRE metrics load test
python tests/load_test_sre.py --metrics-per-second 50 --duration 120
```

### Sample Data Generation

```python
# Generate sample SRE data
python scripts/generate_sample_data.py --services 10 --days 30 --slos 5

# Generate sample alerts
python scripts/generate_sample_alerts.py --count 1000 --timespan 24h
```

## 📚 API Documentation

### SRE Analytics API

Comprehensive REST API for SRE analytics:

- **OpenAPI/Swagger documentation** available at `/docs`
- **Interactive API explorer** at `/swagger`
- **API versioning** with v1, v2 support
- **Rate limiting** and authentication
- **Response caching** for performance

### WebSocket Streaming

Real-time data streaming:

```javascript
// Connect to real-time metrics
const ws = new WebSocket('ws://localhost:8080/ws/metrics');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateDashboard(data);
};
```

## 🔒 Security

### Authentication

```python
# API key authentication
headers = {
    'X-API-Key': 'your-api-key',
    'Authorization': 'Bearer your-jwt-token'
}
```

### Data Privacy

- **PII scrubbing** from alert content
- **Data encryption** at rest and in transit
- **Audit logging** for all API access
- **Role-based access control** (RBAC)

## 🚀 Deployment

### Integrated Deployment (Recommended)

**SRE analytics are embedded within the main NagProm API** - no separate deployment needed!

```bash
# Start NagProm API with integrated analytics
python nagprom-api/api/nagprom_rest_api.py --host 0.0.0.0 --port 8080

# All analytics features available via:
# - API endpoints: http://localhost:8080/api/v1/sre/
# - PHP dashboard: http://localhost/nagios/sre_analytics.php
```

### Production Deployment

```bash
# Install NagProm with analytics
cd nagprom-api/clients/nagios/
sudo ./install.sh

# Start the integrated service
python nagprom-api/api/nagprom_rest_api.py --host 0.0.0.0 --port 8080
```

### Systemd Service

```ini
[Unit]
Description=NagProm REST API with Analytics
After=network.target prometheus.service

[Service]
Type=simple
User=nagprom
WorkingDirectory=/opt/nagprom/nagprom-api/api
ExecStart=/usr/bin/python3 nagprom_rest_api.py --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Production Considerations

- **Single Service**: No container orchestration needed - embedded analytics
- **Data Persistence**: Uses existing Prometheus/Nagios data storage
- **Monitoring**: Monitor the unified NagProm API process
- **Backup & Recovery**: Standard NagProm backup procedures apply
- **Performance Tuning**: Background analytics processing with configurable intervals

## 📝 Examples

See the `examples/` directory for:

- **Complete SRE setup** with sample services
- **Alert correlation scenarios** with test data
- **Dashboard customization** examples
- **Integration patterns** with popular tools
- **Performance optimization** techniques

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Happy Monitoring with NagProm Advanced Analytics! 🚀**
