# NagProm Core Services

This directory contains the core NagProm service exporters that convert Nagios states into Prometheus metrics.

## Core Components

### Service State Exporter
- **`nagprom-service.py`** - Main service performance and state exporter
- Converts Nagios service check results to Prometheus metrics
- Supports custom performance data parsing
- Generates service-specific `.prom` files

### Host State Exporter  
- **`nagprom-host.py`** - Host state and availability exporter
- Converts Nagios host states to Prometheus metrics
- Tracks host availability and state transitions
- Generates host-specific `.prom` files

### Custom Implementation Example
- **`nagprom-service-custom-example.py`** - Example of custom service exporter
- Demonstrates how to extend the base functionality
- Shows custom metric definitions and labels
- Template for service-specific implementations

## Test Scripts

### Service Tests
- **`test_nagprom.py`** - Comprehensive test suite for service exporter
- Tests various service states and performance data formats
- Validates Prometheus output format
- Includes edge case and error handling tests

### Host Tests
- **`test_nagprom_host.py`** - Test suite for host state exporter
- Tests different host states (UP, DOWN, UNREACHABLE)
- Validates host metric generation
- Checks file output and format compliance

## Usage

### Direct Execution
```bash
# Export service metrics
python3 nagprom-service.py -H hostname -s servicename -e OK -i 0 -p "response_time=0.123ms;0.5;1.0"

# Export host metrics  
python3 nagprom-host.py -H hostname -e UP -i 0

# Run tests
python3 test_nagprom.py
python3 test_nagprom_host.py
```

### Integration with Nagios
Add to Nagios command definitions:
```bash
# commands.cfg
define command {
    command_name    nagprom_service_handler
    command_line    /opt/nagprom/core/nagprom-service.py -H $HOSTNAME$ -s "$SERVICEDESC$" -e $SERVICESTATE$ -i $SERVICESTATEID$ -p "$SERVICEPERFDATA$"
}

define command {
    command_name    nagprom_host_handler  
    command_line    /opt/nagprom/core/nagprom-host.py -H $HOSTNAME$ -e $HOSTSTATE$ -i $HOSTSTATEID$
}
```

## Command Line Arguments

### nagprom-service.py
- `-H, --hostname` - Target hostname
- `-s, --service` - Service name
- `-e, --state` - Service state (OK, WARNING, CRITICAL, UNKNOWN)
- `-i, --state-id` - Numeric state ID (0-3)
- `-p, --perfdata` - Performance data string
- `-o, --output-dir` - Output directory for .prom files (default: current directory)
- `--prometheus-url` - Prometheus server URL for validation
- `--debug` - Enable debug output

### nagprom-host.py
- `-H, --hostname` - Target hostname
- `-e, --state` - Host state (UP, DOWN, UNREACHABLE)
- `-i, --state-id` - Numeric state ID (0-2)
- `-o, --output-dir` - Output directory for .prom files
- `--debug` - Enable debug output

## Output Format

### Service Metrics
```prometheus
# HELP nagios_service_state Current state of Nagios service
# TYPE nagios_service_state gauge
nagios_service_state{hostname="web01",service="http",state="OK"} 0

# HELP nagios_service_response_time Service response time in seconds
# TYPE nagios_service_response_time gauge  
nagios_service_response_time{hostname="web01",service="http"} 0.123
```

### Host Metrics
```prometheus
# HELP nagios_host_state Current state of Nagios host
# TYPE nagios_host_state gauge
nagios_host_state{hostname="web01",state="UP"} 0

# HELP nagios_host_last_check_timestamp Unix timestamp of last host check
# TYPE nagios_host_last_check_timestamp gauge
nagios_host_last_check_timestamp{hostname="web01"} 1640995200
```

## Configuration

### Environment Variables
- `NAGPROM_OUTPUT_DIR` - Default output directory
- `NAGPROM_DEBUG` - Enable debug mode
- `PROMETHEUS_URL` - Default Prometheus server URL

### Prometheus Discovery
Configure Prometheus to discover generated files:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'nagios-services'
    file_sd_configs:
      - files: ['/opt/nagprom/output/*.prom']
        refresh_interval: 30s
```

## Error Handling

The exporters include comprehensive error handling for:
- Invalid command line arguments
- Malformed performance data
- File system permission issues
- Network connectivity problems
- Prometheus validation errors

## Performance Considerations

- Use `-o` to specify SSD-backed output directory for high-frequency updates
- Consider file rotation for large environments
- Monitor disk space usage in output directory
- Tune Prometheus scrape interval based on check frequency

## Troubleshooting

### Common Issues
1. **Permission Denied**: Ensure write access to output directory
2. **Invalid Perfdata**: Check performance data format compliance
3. **File Not Found**: Verify all dependencies are installed
4. **Prometheus Errors**: Validate metric names and label formats

### Debug Mode
Enable debug output to troubleshoot issues:
```bash
python3 nagprom-service.py --debug -H test -s test -e OK -i 0 -p "test=1"
```

## Related Documentation

- [API Documentation](../docs/api/REST_API_GUIDE.md)
- [Integration Guide](../docs/integration/)
- [Deployment Guide](../docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)
