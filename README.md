# nagprom
Enhanced Nagios Core plugins that write all performance data for services and host status to prom files to be processed by Prometheus.

## Overview

This project provides three main components:

1. **nagprom-service.py**: Enhanced service performance data exporter
2. **nagprom-host.py**: Host state monitoring exporter
3. **Grafana Dashboards**: Ready-to-use dashboards for monitoring

### Dashboards Included

- **Service Status Overview** (`service-status-overview.json`): High-level overview of all service states
- **Service Monitoring Detail** (`services-monitoring-detail.json`): Detailed service monitoring with performance metrics
- **Host Status Overview** (`host-status-overview.json`): Host state monitoring for large-scale environments

## Features

### Enhanced Metrics
- **Standardized Metric Names**: Uses consistent Prometheus metric naming conventions
- **Comprehensive Labels**: Rich labeling for better querying and filtering
- **Threshold Support**: Exports warning, critical, min, and max thresholds as separate metrics
- **Service State Tracking**: Detailed service state information with timestamps
- **Host State Tracking**: Detailed host state information with timestamps
- **Error Handling**: Robust parsing with graceful error handling
- **Metadata**: Service information metrics for better observability

### Metric Types Generated

#### Service Metrics
- `nagios_service_state`: Current service state (0=OK, 1=WARNING, 2=CRITICAL, 3=UNKNOWN)
  - Labels: host, service, state, state_id
- `nagios_service_check_timestamp`: Unix timestamp of last service check
  - Labels: host, service
- `nagios_service_info`: Service metadata
  - Labels: host, service, state
  - Info: state_id, check_time
- `nagios_performance_data`: Performance metric values
  - Labels: host, service, metric, unit
- `nagios_performance_thresholds`: Warning/critical/min/max thresholds
  - Labels: host, service, metric, threshold_type

#### Host Metrics
- `nagios_host_state`: Current host state (0=UP, 1=DOWN, 2=UNREACHABLE)
  - Labels: host, state, state_id
- `nagios_host_check_timestamp`: Unix timestamp of last host check
  - Labels: host
- `nagios_host_info`: Host metadata
  - Labels: host, state

Note: Service output text (plugin output) is not currently stored in the time series database.

## Prerequisites
1. Clean install of Nagios
2. Functioning Prometheus Node_Exporter
3. Python3 Prometheus_Collector
4. Grafana (for dashboard visualization)

## Installation

### Upload the Scripts
Upload both scripts to the `/usr/local/nagios/libexec/` directory.
Set the permissions as needed for your instance of Nagios.

```bash
cp nagprom-service.py /usr/local/nagios/libexec/
cp nagprom-host.py /usr/local/nagios/libexec/
chmod +x /usr/local/nagios/libexec/nagprom-service.py
chmod +x /usr/local/nagios/libexec/nagprom-host.py
```

### Create Commands
Edit the file `/usr/local/nagios/etc/objects/commands.cfg` to include the following:

```cfg
# Service performance data command
define command{
     command_name     nagprom-service
     command_line     python3 /usr/local/nagios/libexec/nagprom-service.py -H $HOSTNAME$ -s "$SERVICEDESC$" -e "$SERVICESTATE$" -i $SERVICESTATEID$ -p "$SERVICEPERFDATA$"
}

# Host state command
define command{
     command_name     nagprom-host
     command_line     python3 /usr/local/nagios/libexec/nagprom-host.py -H $HOSTNAME$ -e "$HOSTSTATE$" -i $HOSTSTATEID$
}
```

### Configure Nagios for Performance Data Processing
Modify `nagios.cfg` to enable metric export:

```cfg
# PROCESS PERFORMANCE DATA OPTION
# This determines whether or not Nagios will process performance
# data returned from service and host checks.  If this option is
# enabled, host performance data will be processed using the
# host_perfdata_command (defined below) and service performance
# data will be processed using the service_perfdata_command (also
# defined below).  Read the HTML docs for more information on
# performance data.
# Values: 1 = process performance data, 0 = do not process performance data

process_performance_data=1

# HOST AND SERVICE PERFORMANCE DATA PROCESSING COMMANDS
# These commands are run after every host and service check is
# performed.  These commands are executed only if the
# enable_performance_data option (above) is set to 1.  The command
# argument is the short name of a command definition that you
# define in your host configuration file.  Read the HTML docs for
# more information on performance data.

host_perfdata_command=nagprom-host
service_perfdata_command=nagprom-service
```

### Set Up Permissions
Add Nagios user to Prometheus group and set directory permissions:

```bash
# Add Nagios user to Prometheus group
usermod -a -G prometheus nagios

# Set Node_Exporter Directory Permissions
chown -R prometheus:prometheus /var/lib/prometheus/node-exporter
chmod 775 /var/lib/prometheus/node-exporter
```

### Restart Nagios
```bash
systemctl restart nagios
```

## Usage Examples

### Basic Usage
The plugin automatically processes performance data from Nagios service checks.

### Custom Output Directory
You can specify a custom output directory:

```bash
# Service performance data
python3 nagprom-service.py -H "webserver01" -s "HTTP" -e "OK" -i "0" -p "time=0.123s;1.000;2.000;0.000;10.000" -o "/custom/metrics/path"

# Host state data
python3 nagprom-host.py -H "webserver01" -e "UP" -i "0" -o "/custom/metrics/path"
```

## Generated Metrics

### Example Metrics Output

#### Service Metrics
```
# Service State
# HELP nagios_service_state Nagios Service State
# TYPE nagios_service_state gauge
nagios_service_state{host="webserver01",service="HTTP",state="OK",state_id="0"} 0
nagios_service_state{host="dbserver01",service="MySQL",state="WARNING",state_id="1"} 1
nagios_service_state{host="appserver01",service="Tomcat",state="CRITICAL",state_id="2"} 2

# Service Check Timestamp
# HELP nagios_service_check_timestamp Timestamp of last service check
# TYPE nagios_service_check_timestamp gauge
nagios_service_check_timestamp{host="webserver01",service="HTTP"} 1709913600

# Service Info
# HELP nagios_service_info Information about Nagios service
# TYPE nagios_service_info info
nagios_service_info{host="webserver01",service="HTTP",state="OK",state_id="0",check_time="2024-03-08T12:00:00"} 1
```

#### Host Metrics
```
# Host State
# HELP nagios_host_state Nagios Host State
# TYPE nagios_host_state gauge
nagios_host_state{host="webserver01",state="UP",state_id="0"} 0
nagios_host_state{host="dbserver01",state="DOWN",state_id="1"} 1
nagios_host_state{host="appserver01",state="UNREACHABLE",state_id="2"} 2

# Host Check Timestamp
# HELP nagios_host_check_timestamp Timestamp of last host check
# TYPE nagios_host_check_timestamp gauge
nagios_host_check_timestamp{host="webserver01"} 1709913600

# Host Info
# HELP nagios_host_info Information about Nagios host
# TYPE nagios_host_info info
nagios_host_info{host="webserver01",state="UP"} 1
```

#### Performance Data Metrics
```
# Performance Values
# HELP nagios_performance_data Nagios Performance Data
# TYPE nagios_performance_data gauge
# HTTP Response Time
nagios_performance_data{host="webserver01",service="HTTP",metric="time",unit="s"} 0.123
# MySQL Connections
nagios_performance_data{host="dbserver01",service="MySQL",metric="connections",unit=""} 42
# Memory Usage
nagios_performance_data{host="appserver01",service="Memory",metric="used",unit="%"} 85.5

# Performance Thresholds
# HELP nagios_performance_thresholds Nagios Performance Thresholds
# TYPE nagios_performance_thresholds gauge
# HTTP Response Time Thresholds
nagios_performance_thresholds{host="webserver01",service="HTTP",metric="time",threshold_type="warning"} 1.0
nagios_performance_thresholds{host="webserver01",service="HTTP",metric="time",threshold_type="critical"} 2.0
nagios_performance_thresholds{host="webserver01",service="HTTP",metric="time",threshold_type="min"} 0.0
nagios_performance_thresholds{host="webserver01",service="HTTP",metric="time",threshold_type="max"} 10.0
# Memory Usage Thresholds
nagios_performance_thresholds{host="appserver01",service="Memory",metric="used",threshold_type="warning"} 80.0
nagios_performance_thresholds{host="appserver01",service="Memory",metric="used",threshold_type="critical"} 90.0
```

## Prometheus Queries

### Service State Overview
```promql
# All services by state
nagios_service_state

# Services in critical state
nagios_service_state{state="CRITICAL"}

# Service count by state
count by (state) (nagios_service_state)
```

### Host State Overview
```promql
# All hosts by state
nagios_host_state

# Hosts that are down
nagios_host_state{state="DOWN"}

# Host count by state
count by (state) (nagios_host_state)
```

### Performance Data Analysis
```promql
# All performance metrics
nagios_performance_data

# Specific metric across all hosts
nagios_performance_data{metric="time"}

# Metrics exceeding warning threshold
nagios_performance_data > on(host,service,metric) group_left(threshold_type) 
  nagios_performance_thresholds{threshold_type="warning"}
```

### Service Information
```promql
# Service check frequency
rate(nagios_service_check_timestamp[5m])

# Services by host
nagios_service_info
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure Nagios user has write permissions to the output directory
   - Verify Nagios user is in the Prometheus group: `groups nagios`
   - Check directory permissions: `ls -la /var/lib/prometheus/node-exporter`
   - Fix with: `chown -R prometheus:prometheus /var/lib/prometheus/node-exporter && chmod 775 /var/lib/prometheus/node-exporter`

2. **No Metrics Generated**
   - Verify performance data is enabled in nagios.cfg: `process_performance_data=1`
   - Check service definitions include performance data commands
   - Verify Nagios checks are actually producing performance data
   - Look for performance data in Nagios web interface
   - Check Nagios logs for command execution errors

3. **Invalid Performance Data**
   - The plugin logs warnings for unparseable metrics but continues processing
   - Common format issues:
     - Missing equals sign in key-value pairs
     - Invalid characters in metric names
     - Malformed threshold values
   - Check service plugin output format matches: `metric=value[UOM];[warn];[crit];[min];[max]`

4. **Prometheus Not Seeing Metrics**
   - Verify .prom files exist: `ls -la /var/lib/prometheus/node-exporter/*.prom`
   - Check node_exporter configuration includes textfile directory
   - Ensure node_exporter has read permissions on .prom files
   - Verify metrics in Prometheus: `curl localhost:9090/api/v1/targets`

5. **Dashboard Issues**
   - No data showing:
     - Check Prometheus data source configuration in Grafana
     - Verify metrics exist in Prometheus
     - Check time range selection
   - Host/service selection not working:
     - Clear browser cache
     - Check URL parameters format
     - Verify label values match exactly
   - Performance problems:
     - Avoid selecting "All" in large environments
     - Use time range constraints
     - Check Prometheus query optimization

### Debug Mode

1. **Enable Verbose Logging**
   Add debug output by modifying the command definition:

   ```cfg
   define command{
        command_name     nagprom-service-debug
        command_line     python3 /usr/local/nagios/libexec/nagprom-service.py -H $HOSTNAME$ -s "$SERVICEDESC$" -e "$SERVICESTATE$" -i $SERVICESTATEID$ -p "$SERVICEPERFDATA$" 2>&1 | logger -t nagprom-service
   }
   ```

2. **Check Logs**
   - View Nagios logs: `tail -f /usr/local/nagios/var/nagios.log`
   - View system logs: `journalctl -t nagprom-service`
   - Check node_exporter logs: `journalctl -u prometheus-node-exporter`

3. **Verify Metric Files**
   ```bash
   # List all metric files
   ls -la /var/lib/prometheus/node-exporter/*.prom

   # View metric file contents
   cat /var/lib/prometheus/node-exporter/hostname_service.prom

   # Monitor file updates
   watch -n 1 'ls -la /var/lib/prometheus/node-exporter/*.prom'
   ```

4. **Test Metric Generation**
   ```bash
   # Test service metric generation
   python3 /usr/local/nagios/libexec/nagprom-service.py -H "testhost" -s "testservice" -e "OK" -i "0" -p "response_time=0.1s;1;2;0;5"

   # Test host metric generation
   python3 /usr/local/nagios/libexec/nagprom-host.py -H "testhost" -e "UP" -i "0"
   ```

### Grafana Dashboard Troubleshooting

1. **Host/Service Selection Issues**
   - **Empty Dropdowns**
     ```promql
     # Verify hosts are being collected
     count(nagios_host_state) by (host)
     
     # Verify services are being collected
     count(nagios_service_state) by (host, service)
     ```
   - **Default Selection Not Working**
     - Check URL parameters format: `...?var-host=hostname&var-service=servicename`
     - Verify exact label matches (case-sensitive)
     - Clear browser cache and refresh
   
   - **"Choose Host" Stuck**
     - Verify Prometheus data source is working
     - Check time range selection (top-right)
     - Test direct PromQL query in Explore view

2. **Missing or Zero Metrics**
   - **Stat Panels Show "No Data"**
     ```promql
     # Test basic metrics existence
     nagios_service_state{host="your_host",service="your_service"}
     
     # Check if any data in time range
     rate(nagios_service_check_timestamp{host="your_host"}[5m])
     ```
   - **Performance Data Missing**
     - Verify service is producing performance data in Nagios
     - Check metric names match exactly
     - Verify thresholds are being collected:
     ```promql
     nagios_performance_thresholds{host="your_host",service="your_service"}
     ```

3. **Visual Issues**
   - **Status Colors Wrong**
     - Check state mapping in transformations
     - Verify state values: 0=OK/UP, 1=WARNING/DOWN, 2=CRITICAL/UNREACHABLE
     - Test with override rules:
     ```promql
     # Should match dashboard colors
     nagios_service_state == 0  # Green (OK)
     nagios_service_state == 1  # Yellow (Warning)
     nagios_service_state == 2  # Red (Critical)
     ```
   
   - **Timeline Gaps**
     - Adjust "Min step" in query options
     - Check for missing data points:
     ```promql
     # Look for gaps in checks
     rate(nagios_service_check_timestamp{host="your_host"}[5m])
     ```

4. **Performance Issues**
   - **Slow Loading**
     ```promql
     # Count total metrics (if very high, use filters)
     count(nagios_service_state)
     
     # Check metric cardinality
     count(count by(host, service) (nagios_service_state))
     ```
   - **Browser Freezing**
     - Reduce time range
     - Add metric filters
     - Use query optimization:
     ```promql
     # Instead of
     nagios_service_state
     
     # Use
     nagios_service_state != 0  # Show only problems
     ```

5. **Common Fixes**
   - **Reset Dashboard**
     - Clear URL parameters
     - Set time range to last 6 hours
     - Refresh page with browser cache cleared
   
   - **Fix Variable Dependencies**
     ```promql
     # Test host variable query
     label_values(nagios_service_state, host)
     
     # Test service variable query (for specific host)
     label_values(nagios_service_state{host="$host"}, service)
     ```

### Quick Fixes

1. **Reset Permissions**
   ```bash
   # Fix directory permissions
   chown -R prometheus:prometheus /var/lib/prometheus/node-exporter
   chmod 775 /var/lib/prometheus/node-exporter
   
   # Add Nagios user to Prometheus group
   usermod -a -G prometheus nagios
   ```

2. **Clear Old Metrics**
   ```bash
   # Remove stale metric files
   rm /var/lib/prometheus/node-exporter/*.prom
   
   # Restart services
   systemctl restart nagios
   systemctl restart prometheus-node-exporter
   systemctl restart prometheus
   ```

3. **Verify Configuration**
   ```bash
   # Check Nagios config
   /usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg
   
   # Test node_exporter
   curl http://localhost:9100/metrics
   
   # Test Prometheus targets
   curl -s localhost:9090/api/v1/targets | jq .
   ```

## Grafana Dashboards

### Service Status Overview
Import `service-status-overview.json` into Grafana for a high-level view:
- Global service state overview
- Service state distribution
- Quick filtering by host and service
- Optimized for large-scale environments

### Service Monitoring Detail
Import `services-monitoring-detail.json` for detailed service analysis:
- Explicit host/service selection to prevent performance issues
- Detailed performance metrics with thresholds
- Service state tracking over time
- Performance optimization features:
  - No automatic loading of all hosts/services
  - Efficient query optimization for large environments
  - Selective data loading based on user choices

### Host Status Overview
Import `host-status-overview.json` for host monitoring:
- Host state heatmap (supports thousands of hosts)
- Host status summary cards
- Host status table
- Mouse-over tooltips showing hostnames

### Dashboard Navigation and Usage

The monitoring system consists of three interconnected dashboards, each optimized for different scales and use cases:

1. **Host Status Overview** (`host-status-overview.json`):
   - **Quick Stats (Top)**
     - Total host count
     - UP, DOWN, and UNREACHABLE counts
     - Zero displayed when no data (no blank panels)
   
   - **Status History (Timeline)**
     - Temporal view of host state changes
     - Color-coded status indicators
     - Hover for detailed state information
     - Perfect for identifying patterns
   
   - **Problem Hosts (Left Panel)**
     - Focused view of DOWN/UNREACHABLE hosts
     - Clickable hostnames linking to services
     - Instant visibility of critical issues
     - Sortable by state and duration
   
   - **Status Distribution (Right Panel)**
     - Donut chart visualization
     - At-a-glance health overview
     - Interactive legend with counts
     - Perfect for presentations/reports
   
   - **All Hosts Status (Bottom)**
     - Hierarchical view of all hosts
     - Grouping and filtering capabilities
     - Direct links to service details
     - Scales to thousands of hosts

2. **Service Status Overview** (`service-status-overview.json`):
   - **Summary Statistics**
     - Total, OK, Warning, Critical counts
     - Zero displayed for no data states
     - Real-time metric updates
   
   - **Service Status History**
     - Timeline of service state changes
     - Pattern and trend identification
     - Interactive time range selection
     - Historical state analysis
   
   - **Critical & Warning Services**
     - Immediate problem visibility
     - Clickable service names
     - Contextual host information
     - Prioritized by severity
   
   - **Service Distribution**
     - Visual status breakdown
     - Interactive filtering
     - Percentage distributions
     - Quick health assessment
   
   - **Hierarchical Service View**
     - Grouped by host
     - Nested service relationships
     - Advanced filtering options
     - Efficient large-scale handling

3. **Service Monitoring Detail** (`services-monitoring-detail.json`):
   - **Access Methods**
     - From host overview (click hostname)
     - From service overview (click service)
     - Direct URL with parameters
   
   - **Key Features**
     - Performance metrics over time
     - State history tracking
     - Warning/critical thresholds
     - Detailed service metrics
   
   - **Performance Optimizations**
     - Explicit host/service selection
     - No automatic data loading
     - Efficient query handling
     - Scalable for large environments

### Navigation Best Practices
1. **Start Point Selection**
   - Host Overview: For infrastructure focus
   - Service Overview: For application focus
   - Detail View: For specific investigations

2. **Drill-Down Workflow**
   - Overview → Problem Identification → Detail Investigation
   - Use browser tabs for multiple views
   - Maintain context through linked navigation
   - Bookmark common views

3. **Large-Scale Usage**
   - Use filters before detailed views
   - Leverage grouping for organization
   - Focus on problem states first
   - Utilize temporal views for patterns

### Performance Optimization Tips
1. **Query Management**
   - Filter before drilling down
   - Avoid selecting "All" in large environments
   - Use time range constraints
   - Leverage grouped views

2. **Resource Considerations**
   - Overview dashboards handle scale
   - Detail views require selection
   - Use browser tabs efficiently
   - Regular view refreshes (10s default)

3. **Enterprise Scale**
   - Supports thousands of hosts
   - Tens of thousands of services
   - Efficient state tracking
   - Optimized visualizations

## Changelog

### v1.0.0 - Breaking Changes Release

#### Breaking Changes
- Standardized metric names (old format no longer supported)
  - Old: `{host}_{service}_state` → New: `nagios_service_state`
  - Old: `{host}_{service}` → New: `nagios_performance_data`
- Restructured label format for all metrics

#### Major Features
1. **Enhanced Metric Structure**
   - Standardized Prometheus metrics with comprehensive labeling
   - Added service state tracking with detailed labels
   - Implemented performance threshold metrics
   - Added timestamp tracking for all checks

2. **New Grafana Dashboards**
   - Added three new dashboards for monitoring:
     - Host Status Overview
     - Service Status Overview
     - Service Monitoring Detail
   - Features include:
     - Hierarchical status panels
     - Status history timelines
     - Status distribution charts
     - Inter-dashboard linking
     - Zero-value display for empty metrics
     - Large-scale environment optimizations

3. **Performance Data Processing**
   - Robust parsing for complex performance data
   - Support for multiple metrics per check
   - Threshold extraction and tracking
   - Unit validation and standardization

4. **Error Handling & Reliability**
   - Graceful parsing of malformed data
   - Improved error reporting
   - Directory creation checks
   - Permission validation

5. **Monitoring Enhancements**
   - Comprehensive service state tracking
   - Performance trend analysis
   - Threshold-based monitoring
   - Check frequency tracking

#### Documentation
- Added detailed troubleshooting guide
- Added comprehensive dashboard documentation
- Added PromQL query examples
- Improved installation instructions

### Previous Versions

- **v0.0.5**: Basic metric formatting and threshold support
  - Enhanced performance data parsing
  - Added threshold extraction
  - Improved error handling
- **v0.0.4**: Initial release with basic functionality
  - Basic service state monitoring
  - Simple performance data collection
- **v0.0.1**: Host state monitoring plugin added
  - Basic host state tracking only

## Migration Guide

### Required Actions
1. **Before Upgrade**
   - Backup existing configuration
   - Export any custom dashboards
   - Document current metric names

2. **During Upgrade**
   ```bash
   # Stop services
   systemctl stop nagios
   systemctl stop prometheus

   # Backup files
   cp /usr/local/nagios/libexec/nagprom-service.py /usr/local/nagios/libexec/nagprom-service.py.bak
   cp /usr/local/nagios/libexec/nagprom-host.py /usr/local/nagios/libexec/nagprom-host.py.bak

   # Install new version
   cp nagprom-service.py /usr/local/nagios/libexec/
   cp nagprom-host.py /usr/local/nagios/libexec/
   chmod +x /usr/local/nagios/libexec/nagprom-service.py
   chmod +x /usr/local/nagios/libexec/nagprom-host.py

   # Clear old metrics
   rm /var/lib/prometheus/node-exporter/*.prom

   # Start services
   systemctl start nagios
   systemctl start prometheus
   ```

3. **After Upgrade**
   - Update Prometheus queries
   - Import new dashboards
   - Verify metrics collection
   - Update any custom dashboards

## Contributing


Feel free to submit issues and enhancement requests! 
