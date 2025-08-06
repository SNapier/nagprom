import argparse, os, prometheus_client, sys, re, json, time
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, Info, write_to_textfile
from datetime import datetime

#NAGIOS(CORE) PROMETHEUS PERFDATA EXPORTOR - SERVICE
#PARSES NAGIOS CORE PERFORMANCE DATA AND EXPORTS THE DATA TO A PROMETHEUS
#PROM FILE TO BE READ BY THE PROMETHEUS NODE_EXPORTER.   

#SCRIPT DEFINITION
cname = "nagprom-service"
cversion = "1.0.0"
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

    #ARGS
    #HOSTNAME/ADDRESS
    args.add_argument(
        "-H","--host",
        required=True,
        default=None,
        help="String(hostname/hostaddress): The target host for the plugin to execute against."
    ),
    #SERVICE DESCRIPTION
    args.add_argument(
        "-s","--servicedesc",
        required=True,
        default=None,
        help="String(servicedesc): The nagios service description generating performance data."
    ),
    #NAGIOS SERVICE STATE
    args.add_argument(
        "-e","--servicestate",
        required=True,
        default="OK",
        help="String(servicestate): The nagios service exit state for the service generating performance data."
    ),
    #NAGIOS SERVICE STATE ID
    args.add_argument(
        "-i","--servicestateid",
        required=True,
        default=None,
        help="String(servicestateid): The nagios service exit state ID for the service generating performance data."
    ),
    #NAGIOS PERFORMANCE DATA
    args.add_argument(
        "-p","--perfdata",
        required=True,
        default=None,
        help="String(service perfdata): Nagios formatted service performance data."
    ),
    #PROMETHEUS METRIC TYPE
    args.add_argument(
        "-m","--pmtype",
        required=False,
        default="g",
        help="String(prommetrictype): The prometheus metric type to be generated."
    ),
    #OUTPUT DIRECTORY
    args.add_argument(
        "-o","--output-dir",
        required=False,
        default="/var/lib/prometheus/node-exporter",
        help="String(outputdir): Directory to write prometheus metric files."
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

    #FORMAT GAUGE NAME
    gname = "{}_{}".format(host_safe, svc.lower())
    
    # Get standardized state information
    state_name, state_id = get_service_state_info(meta.servicestate, meta.servicestateid)
    
    #CREATE COMPREHENSIVE METRICS
    
    # Service state metric with detailed labels
    service_state = Gauge(
        'nagios_service_state', 
        'Nagios Service State', 
        labelnames=['host', 'service', 'state', 'state_id'], 
        registry=nagmetrics
    )
    service_state.labels(
        host=host_safe, 
        service=svc, 
        state=state_name, 
        state_id=str(state_id)
    ).set(state_id)
    
    # Service check timestamp
    service_check_time = Gauge(
        'nagios_service_check_timestamp',
        'Timestamp of last service check',
        labelnames=['host', 'service'],
        registry=nagmetrics
    )
    service_check_time.labels(host=host_safe, service=svc).set(time.time())
    
    # Service info metric
    service_info = Info(
        'nagios_service_info',
        'Information about Nagios service',
        labelnames=['host', 'service', 'state'],
        registry=nagmetrics
    )
    service_info.labels(host=host_safe, service=svc, state=state_name).info({
        'state_id': str(state_id),
        'check_time': datetime.now().isoformat()
    })
    
    #PARSE PERFORMANCE DATA
    parsed_metrics = parse_nagios_perfdata(meta.perfdata)
    
    #CREATE PERFORMANCE METRICS
    if parsed_metrics:
        # Main performance data gauge
        perf_gauge = Gauge(
            'nagios_performance_data',
            'Nagios Performance Data',
            labelnames=['host', 'service', 'metric', 'unit'],
            registry=nagmetrics
        )
        
        # Threshold metrics
        threshold_gauge = Gauge(
            'nagios_performance_thresholds',
            'Nagios Performance Thresholds',
            labelnames=['host', 'service', 'metric', 'threshold_type'],
            registry=nagmetrics
        )
        
        # Process each parsed metric
        for metric in parsed_metrics:
            # Set main performance value
            perf_gauge.labels(
                host=host_safe,
                service=svc,
                metric=metric['name'],
                unit=metric['unit']
            ).set(metric['value'])
            
            # Set threshold values if they exist
            if metric['warn']:
                try:
                    warn_val = float(re.sub(r"[a-zA-Z%]+$", "", metric['warn']))
                    threshold_gauge.labels(
                        host=host_safe,
                        service=svc,
                        metric=metric['name'],
                        threshold_type='warning'
                    ).set(warn_val)
                except ValueError:
                    pass
                    
            if metric['crit']:
                try:
                    crit_val = float(re.sub(r"[a-zA-Z%]+$", "", metric['crit']))
                    threshold_gauge.labels(
                        host=host_safe,
                        service=svc,
                        metric=metric['name'],
                        threshold_type='critical'
                    ).set(crit_val)
                except ValueError:
                    pass
                    
            if metric['min']:
                try:
                    min_val = float(re.sub(r"[a-zA-Z%]+$", "", metric['min']))
                    threshold_gauge.labels(
                        host=host_safe,
                        service=svc,
                        metric=metric['name'],
                        threshold_type='min'
                    ).set(min_val)
                except ValueError:
                    pass
                    
            if metric['max']:
                try:
                    max_val = float(re.sub(r"[a-zA-Z%]+$", "", metric['max']))
                    threshold_gauge.labels(
                        host=host_safe,
                        service=svc,
                        metric=metric['name'],
                        threshold_type='max'
                    ).set(max_val)
                except ValueError:
                    pass
    
    #WRITE THE METRICS REGISTRY TO THE HOSTS PROM FILE
    try:
        # Ensure output directory exists
        os.makedirs(meta.output_dir, exist_ok=True)
        
        promfile = os.path.join(meta.output_dir, '{}_{}.prom'.format(host_safe, svc.lower()))
        write_to_textfile(promfile, nagmetrics)
        
        # Print success message
        print(f"Successfully wrote metrics to {promfile}")
        
    except Exception as e:
        print(f"Error writing metrics file: {e}", file=sys.stderr)
        sys.exit(1) 