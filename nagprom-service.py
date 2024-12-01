import argparse, os, prometheus_client, sys, re
from prometheus_client import CollectorRegistry, Gauge, write_to_textfile

#NAGIOS(CORE) PROMETHEUS PERFDATA EXPORTOR - SERVICE
#PARSES NAGIOS CORE PERFORMANCE DATA AND EXPORTS THE DATA TO A PROMETHEUS
#PROM FILE TO BE READ BY THE PROMETHEUS NODE_EXPORTER.   

#SCRIPT DEFINITION
cname = "nagprom-service"
cversion = "0.0.2"
appPath = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__" :

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
        help="String(prommetrictype): The prometheus metric typre to be generated."
    )

    #COLLECT ARGS
    meta = args.parse_args()
    
    #SANITY CHECKS
    if meta.perfdata == "":
        print("PERFDATA IS BLANK")
        sys.exit()
    
    #PROMETHEUS REGISTRY
    nagmetrics = CollectorRegistry()

    #SAFE FORMAT NAGIOS SEVICE DESCRIPTION
    svc = meta.servicedesc.replace(" ","_")
    
    #FORMAT GAUGE NAME
    gname = "{}_{}".format(meta.host,svc.lower())
    
    #GAUGE DEFINITOIN
    g = Gauge(gname, meta.servicedesc, ['metric','unit'], registry=nagmetrics)
    
    #GET INDIVIDUAL METRICS IN THE PERFDATA STRING
    rawdata = meta.perfdata.split(" ")
    
    #PARSE EACH METRIC IN THE PERFDATA STRING
    for i in rawdata:
        
        #SPLIT NAME AND VALUE
        data = i.split("=")
        metric = data[0]

        #GET NAGIOS DATA
        #TAKE VALUE FROM FIRST POSITION AND DISCARD WARN,CRIT,MIN,MAX
        rpd = data[1]
        fv = rpd.split(";")
        ev = fv[0]
        
        #GET THE UNIT OF MEASURE FROM EXTRACTED VALUE IF PRESENT
        u = re.search("(\\D{1,3})$", ev)
        if u:
            uom = u[1]
        else:
            uom = ""

        #STRIP UNIT OF MEASURE FROM EXTRACTED VALUE IF PRESENT    
        value = re.sub("\\D{1,}$","",ev)

        #ADD LABEL FOR METRIC
        g.labels(metric,uom).set(value)
    
    #WRITE THE METRICS REGISRTY TO THE HOSTS PROM FILE    
    promfile = '/var/lib/prometheus/node-exporter/{}_{}.prom'.format(meta.host,svc.lower())    
    write_to_textfile(promfile, nagmetrics)
