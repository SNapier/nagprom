# NagProm Grafana Dashboards

This directory contains pre-configured Grafana dashboard definitions for visualizing NagProm metrics.

## Available Dashboards

### Host Monitoring Dashboards
- **`host-status-overview.json`** - High-level overview of all host states with status distribution and problem host identification

### Service Monitoring Dashboards  
- **`service-status-overview.json`** - Service status summary across all hosts with critical/warning service panels
- **`services-monitoring-detail.json`** - Detailed service performance metrics with threshold visualization and state history

## Dashboard Status

**Note**: These are the current, actively maintained dashboards. Previous experimental dashboards have been removed to focus on quality and maintainability. The current dashboards provide comprehensive monitoring coverage for both hosts and services.

## Import Instructions

### Via Grafana UI
1. Open Grafana web interface
2. Navigate to **Dashboards** → **Import**
3. Click **Upload JSON file** or paste the JSON content
4. Configure data source settings (point to your Prometheus instance)
5. Click **Import**

### Via Grafana API
```bash
# Replace GRAFANA_URL and API_KEY with your values
curl -X POST \
  http://GRAFANA_URL/api/dashboards/db \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d @host-status-overview.json
```

### Via Provisioning
1. Copy dashboard files to your Grafana provisioning directory:
   ```bash
   cp *.json /etc/grafana/provisioning/dashboards/
   ```
2. Create or update dashboard provisioning config:
   ```yaml
   # /etc/grafana/provisioning/dashboards/dashboards.yml
   apiVersion: 1
   providers:
     - name: 'nagprom'
       orgId: 1
       folder: 'NagProm'
       folderUid: 'nagprom'
       type: file
       disableDeletion: false
       updateIntervalSeconds: 30
       allowUiUpdates: true
       options:
         path: /etc/grafana/provisioning/dashboards
   ```
3. Restart Grafana service

## Data Source Configuration

These dashboards expect a Prometheus data source configured with:
- **Name**: `Prometheus` (or update dashboard data source references)
- **URL**: Your Prometheus server URL (e.g., `http://localhost:9090`)
- **Access**: `Server` (default) or `Browser` depending on your setup

## Dashboard Features

### Host Status Overview
- Real-time host state visualization
- State distribution charts
- Alert correlation
- Trend analysis

### Service Monitoring Detail
- Service performance metrics
- Response time graphs
- Error rate tracking
- Capacity utilization

## Integration with NagProm Web Interfaces

These Grafana dashboards complement the NagProm PHP dashboards:

### PHP Dashboard Features
- **Main Dashboard**: API endpoint testing and system overview
- **Metrics Dashboard**: Performance metrics with gauge displays
- **Debug Dashboard**: System information and troubleshooting
- **Graph Dashboard**: Time-series visualization with thresholds
- **Correlation Dashboard**: Alert correlation and pattern analysis

### Access URLs
```bash
# NagProm PHP Dashboards (self-contained)
http://your-server/nagprom/clients/nagios/index.php
http://your-server/nagprom/clients/nagios/metrics.php
http://your-server/nagprom/clients/nagios/debug.php
http://your-server/nagprom/clients/nagios/graph.php
http://your-server/nagprom/clients/nagios/correlation.php

# Grafana dashboards (after import)
http://your-grafana-server/d/nagprom-hosts/host-status-overview
http://your-grafana-server/d/nagprom-services/service-status-overview
http://your-grafana-server/d/nagprom-services/services-monitoring-detail
```

## Customization

You can customize these dashboards by:
1. Importing them into Grafana
2. Making modifications via the Grafana UI
3. Exporting the updated JSON
4. Committing changes back to this repository

## Troubleshooting

### No Data Displayed
- Verify Prometheus data source is configured correctly
- Check that NagProm services are running and exporting metrics
- Confirm metric names match those in the dashboard queries

### Dashboard Import Errors
- Ensure Grafana version compatibility
- Check for missing plugins or panels
- Verify JSON syntax is valid

### Performance Issues
- Adjust query time ranges if dashboards are slow
- Consider using recording rules for complex queries
- Optimize Prometheus retention and storage

## Migration from Previous Structure

If you were using the old `dashboards/` directory structure:

1. The directory has been renamed to `grafana-dashboards/` for clarity
2. All dashboard files remain the same
3. Update any scripts or documentation that reference the old path
4. The PHP dashboards are now in `clients/nagios/` and are self-contained
5. Removed experimental dashboards to focus on quality and maintainability

## Related Documentation

- [NagProm API Documentation](../docs/api/REST_API_GUIDE.md)
- [Production Deployment Guide](../docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Alert Correlation Guide](../docs/user-guides/ALERT_CORRELATION_GUIDE.md)
- [SRE Analytics Guide](../docs/user-guides/SRE_ANALYTICS_GUIDE.md)