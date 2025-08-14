import argparse, os, prometheus_client, sys, re, json, time
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, Info, write_to_textfile
from datetime import datetime

#NAGIOS(CORE) PROMETHEUS PERFDATA EXPORTOR - SERVICE (CUSTOMIZED EXAMPLE)
#PARSES NAGIOS CORE PERFORMANCE DATA AND EXPORTS THE DATA TO A PROMETHEUS
#PROM FILE TO BE READ BY THE PROMETHEUS NODE_EXPORTER.   
#
# This is an EXAMPLE of how you can customize the Prometheus interface
# Key customizations shown:
# 1. Environment labels for all metrics
# 2. Configurable metric prefixes
# 3. Custom file naming with environment
# 4. Extended command-line options

#SCRIPT DEFINITION
cname = "nagprom-service-custom"
cversion = "1.0.0-custom"
appPath = os.path.dirname(os.path.realpath(__file__))

def parse_nagios_perfdata(perfdata_string):
    """Parse Nagios performance data string into structured format"""
    metrics = []
    
    if not perfdata_string or perfdata_string.strip() == "":
        return metrics
    
    # Split by space to get individual metrics
    raw_metrics = perfdata_string.split(" ")
    
    for metric in raw_metrics:
        if "=" not in metric:
            continue
            
        try:
            # Split metric name and value
            name, value_part = metric.split("=", 1)
            
            # Parse the value part (format: value;warn;crit;min;max)
            parts = value_part.split(";")
            
            # Extract components
            value = parts[0] if len(parts) > 0 else "0"
            warn = parts[1] if len(parts) > 1 else ""
            crit = parts[2] if len(parts) > 2 else ""
            min_val = parts[3] if len(parts) > 3 else ""
            max_val = parts[4] if len(parts) > 4 else ""
            
            # Extract unit of measurement
            unit_match = re.search(r"([a-zA-Z%]+)$", value)
            unit = unit_match.group(1) if unit_match else ""
            
            # Clean numeric value
            numeric_value = re.sub(r"[a-zA-Z%]+$", "", value)
            
            # Try to convert to float, default to 0 if conversion fails
            try:
                float_value = float(numeric_value) if numeric_value else 0.0
            except ValueError:
                float_value = 0.0
            
            metrics.append({
                'name': name,
                'value': float_value,
                'unit': unit,
                'warn': warn,
                'crit': crit,
                'min': min_val,
                'max': max_val,
                'raw_value': value
            })
            
        except Exception as e:
            # Log parsing errors but continue
            print(f"Warning: Could not parse metric '{metric}': {e}", file=sys.stderr)
            continue
    
    return metrics

def get_service_state_info(state, state_id):
    """Convert Nagios state to standardized format"""
    state_mapping = {
        '0': 'OK',
        '1': 'WARNING', 
        '2': 'CRITICAL',
        '3': 'UNKNOWN'
    }
    
    # If state_id is provided, use it to determine state
    if state_id in state_mapping:
        return state_mapping[state_id], int(state_id)
    else:
        # Try to map state string to ID
        reverse_mapping = {v: k for k, v in state_mapping.items()}
        if state.upper() in reverse_mapping:
            return state.upper(), int(reverse_mapping[state.upper()])
        else:
            return state.upper(), 3  # Default to UNKNOWN

if __name__ == "__main__":

    #INPUT FROM NAGIOS
    args = argparse.ArgumentParser(prog=cname+" v:"+cversion, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    #STANDARD ARGS (same as original)
    args.add_argument(
        "-H","--host",
        required=True,
        default=None,
        help="String(hostname/hostaddress): The target host for the plugin to execute against."
    ),
    args.add_argument(
        "-s","--servicedesc",
        required=True,
        default=None,
        help="String(servicedesc): The nagios service description generating performance data."
    ),
    args.add_argument(
        "-e","--servicestate",
        required=True,
        default="OK",
        help="String(servicestate): The nagios service exit state for the service generating performance data."
    ),
    args.add_argument(
        "-i","--servicestateid",
        required=True,
        default=None,
        help="String(servicestateid): The nagios service exit state ID for the service generating performance data."
    ),
    args.add_argument(
        "-p","--perfdata",
        required=True,
        default=None,
        help="String(service perfdata): Nagios formatted service performance data."
    ),
    args.add_argument(
        "-m","--pmtype",
        required=False,
        default="g",
        help="String(prommetrictype): The prometheus metric type to be generated."
    ),
    args.add_argument(
        "-o","--output-dir",
        required=False,
        default="/var/lib/prometheus/node-exporter",
        help="String(outputdir): Directory to write prometheus metric files."
    ),
    
    # CUSTOMIZATION OPTIONS - These are the new features you can add
    args.add_argument(
        "--environment",
        required=False,
        default="production",
        help="String(environment): Environment label for metrics (e.g., production, staging, development)."
    ),
    args.add_argument(
        "--metric-prefix",
        required=False,
        default="nagios",
        help="String(prefix): Prefix for metric names (default: nagios)."
    ),
    args.add_argument(
        "--datacenter",
        required=False,
        default="",
        help="String(datacenter): Datacenter label for metrics."
    ),
    args.add_argument(
        "--team",
        required=False,
        default="",
        help="String(team): Team responsible for the service."
    )

    #COLLECT ARGS
    meta = args.parse_args()
    
    #SANITY CHECKS
    if not meta.perfdata or meta.perfdata.strip() == "":
        print("PERFDATA IS BLANK")
        sys.exit(1)
    
    #PROMETHEUS REGISTRY
    nagmetrics = CollectorRegistry()

    #SAFE FORMAT NAGIOS SERVICE DESCRIPTION
    svc = meta.servicedesc.replace(" ","_").replace("-","_")
    host_safe = meta.host.replace(" ","_").replace("-","_")
    
    # Get standardized state information
    state_name, state_id = get_service_state_info(meta.servicestate, meta.servicestateid)
    
    # BUILD DYNAMIC LABEL NAMES AND VALUES
    # This shows how you can make labels conditional and configurable
    base_labels = ['host', 'service', 'state', 'state_id', 'environment']
    base_values = {
        'host': host_safe,
        'service': svc,
        'state': state_name,
        'state_id': str(state_id),
        'environment': meta.environment
    }
    
    # Add optional labels if provided
    if meta.datacenter:
        base_labels.append('datacenter')
        base_values['datacenter'] = meta.datacenter
    
    if meta.team:
        base_labels.append('team')
        base_values['team'] = meta.team
    
    #CREATE COMPREHENSIVE METRICS WITH CUSTOMIZABLE STRUCTURE
    
    # Service state metric with dynamic labels
    service_state = Gauge(
        f'{meta.metric_prefix}_service_state',  # Configurable prefix
        'Nagios Service State', 
        labelnames=base_labels,  # Dynamic label list
        registry=nagmetrics
    )
    service_state.labels(**base_values).set(state_id)
    
    # Service check timestamp with dynamic labels
    timestamp_labels = ['host', 'service', 'environment']
    timestamp_values = {
        'host': host_safe,
        'service': svc,
        'environment': meta.environment
    }
    
    if meta.datacenter:
        timestamp_labels.append('datacenter')
        timestamp_values['datacenter'] = meta.datacenter
    
    if meta.team:
        timestamp_labels.append('team')
        timestamp_values['team'] = meta.team
    
    service_check_time = Gauge(
        f'{meta.metric_prefix}_service_check_timestamp',
        'Timestamp of last service check',
        labelnames=timestamp_labels,
        registry=nagmetrics
    )
    service_check_time.labels(**timestamp_values).set(time.time())
    
    # Service info metric with extended metadata
    info_values = base_values.copy()
    service_info = Info(
        f'{meta.metric_prefix}_service_info',
        'Information about Nagios service',
        labelnames=base_labels,
        registry=nagmetrics
    )
    service_info.labels(**info_values).info({
        'state_id': str(state_id),
        'check_time': datetime.now().isoformat(),
        'script_version': cversion,
        'metric_prefix': meta.metric_prefix
    })
    
    #PARSE PERFORMANCE DATA
    parsed_metrics = parse_nagios_perfdata(meta.perfdata)
    
    #CREATE PERFORMANCE METRICS WITH CUSTOM STRUCTURE
    if parsed_metrics:
        # Performance data labels
        perf_labels = ['host', 'service', 'metric', 'unit', 'environment']
        threshold_labels = ['host', 'service', 'metric', 'threshold_type', 'environment']
        
        # Add optional labels
        if meta.datacenter:
            perf_labels.append('datacenter')
            threshold_labels.append('datacenter')
        
        if meta.team:
            perf_labels.append('team')
            threshold_labels.append('team')
        
        # Main performance data gauge
        perf_gauge = Gauge(
            f'{meta.metric_prefix}_performance_data',
            'Nagios Performance Data',
            labelnames=perf_labels,
            registry=nagmetrics
        )
        
        # Threshold metrics
        threshold_gauge = Gauge(
            f'{meta.metric_prefix}_performance_thresholds',
            'Nagios Performance Thresholds',
            labelnames=threshold_labels,
            registry=nagmetrics
        )
        
        # Process each parsed metric
        for metric in parsed_metrics:
            # Build performance metric labels
            perf_values = {
                'host': host_safe,
                'service': svc,
                'metric': metric['name'],
                'unit': metric['unit'],
                'environment': meta.environment
            }
            
            if meta.datacenter:
                perf_values['datacenter'] = meta.datacenter
            if meta.team:
                perf_values['team'] = meta.team
            
            # Set main performance value
            perf_gauge.labels(**perf_values).set(metric['value'])
            
            # Set threshold values if they exist
            for threshold_type, threshold_value in [('warning', metric['warn']), ('critical', metric['crit']), ('min', metric['min']), ('max', metric['max'])]:
                if threshold_value:
                    try:
                        thresh_val = float(re.sub(r"[a-zA-Z%]+$", "", threshold_value))
                        
                        threshold_values = {
                            'host': host_safe,
                            'service': svc,
                            'metric': metric['name'],
                            'threshold_type': threshold_type,
                            'environment': meta.environment
                        }
                        
                        if meta.datacenter:
                            threshold_values['datacenter'] = meta.datacenter
                        if meta.team:
                            threshold_values['team'] = meta.team
                        
                        threshold_gauge.labels(**threshold_values).set(thresh_val)
                    except ValueError:
                        pass
    
    #WRITE THE METRICS REGISTRY TO FILE WITH CUSTOM NAMING
    try:
        # Ensure output directory exists
        os.makedirs(meta.output_dir, exist_ok=True)
        
        # Build custom filename with environment and optional datacenter
        filename_parts = [meta.environment, host_safe, svc.lower()]
        if meta.datacenter:
            filename_parts.insert(1, meta.datacenter)
        
        filename = "_".join(filename_parts) + f"_{meta.metric_prefix}.prom"
        promfile = os.path.join(meta.output_dir, filename)
        
        write_to_textfile(promfile, nagmetrics)
        
        # Print success message with details
        print(f"Successfully wrote metrics to {promfile}")
        print(f"Metric prefix: {meta.metric_prefix}")
        print(f"Environment: {meta.environment}")
        if meta.datacenter:
            print(f"Datacenter: {meta.datacenter}")
        if meta.team:
            print(f"Team: {meta.team}")
        
    except Exception as e:
        print(f"Error writing metrics file: {e}", file=sys.stderr)
        sys.exit(1)
