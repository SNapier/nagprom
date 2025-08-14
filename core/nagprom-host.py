import argparse, os, prometheus_client, sys, time
from prometheus_client import CollectorRegistry, Gauge, Info, write_to_textfile
from datetime import datetime

#NAGIOS(CORE) PROMETHEUS HOST STATE EXPORTOR
#EXPORTS NAGIOS CORE HOST STATE DATA TO PROMETHEUS FORMAT

#SCRIPT DEFINITION
cname = "nagprom-host"
cversion = "1.0.0"
appPath = os.path.dirname(os.path.realpath(__file__))

def get_host_state_info(state, state_id):
    """Convert Nagios host state to standardized format"""
    state_mapping = {
        '0': 'UP',
        '1': 'DOWN', 
        '2': 'UNREACHABLE'
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
            return state.upper(), 1  # Default to DOWN

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
    #NAGIOS HOST STATE
    args.add_argument(
        "-e","--hoststate",
        required=True,
        default="UP",
        help="String(hoststate): The nagios host exit state."
    ),
    #NAGIOS HOST STATE ID
    args.add_argument(
        "-i","--hoststateid",
        required=True,
        default=None,
        help="String(hoststateid): The nagios host exit state ID."
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
    if not meta.host or meta.host.strip() == "":
        print("HOST IS BLANK")
        sys.exit(1)
    
    #PROMETHEUS REGISTRY
    nagmetrics = CollectorRegistry()

    #SAFE FORMAT NAGIOS HOST NAME
    host_safe = meta.host.replace(" ","_").replace("-","_")

    # Get standardized state information
    state_name, state_id = get_host_state_info(meta.hoststate, meta.hoststateid)
    
    #CREATE HOST STATE METRICS
    
    # Host state metric with detailed labels
    host_state = Gauge(
        'nagios_host_state', 
        'Nagios Host State', 
        labelnames=['host', 'state', 'state_id'], 
        registry=nagmetrics
    )
    host_state.labels(
        host=host_safe, 
        state=state_name, 
        state_id=str(state_id)
    ).set(state_id)
    
    # Host check timestamp
    host_check_time = Gauge(
        'nagios_host_check_timestamp',
        'Timestamp of last host check',
        labelnames=['host'],
        registry=nagmetrics
    )
    host_check_time.labels(host=host_safe).set(time.time())
    
    # Host info metric
    host_info = Info(
        'nagios_host_info',
        'Information about Nagios host',
        labelnames=['host', 'state'],
        registry=nagmetrics
    )
    host_info.labels(host=host_safe, state=state_name).info({
        'state_id': str(state_id),
        'check_time': datetime.now().isoformat()
    })
    
    #WRITE THE METRICS REGISTRY TO THE HOSTS PROM FILE
    try:
        # Ensure output directory exists
        os.makedirs(meta.output_dir, exist_ok=True)
        
        promfile = os.path.join(meta.output_dir, '{}_host_state.prom'.format(host_safe))
        write_to_textfile(promfile, nagmetrics)
        
        # Print success message
        print(f"Successfully wrote host state metrics to {promfile}")
        
    except Exception as e:
        print(f"Error writing metrics file: {e}", file=sys.stderr)
        sys.exit(1) 