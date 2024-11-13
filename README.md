# nagprom-service
Nagios Core plugin that writes all performance data for services to prom files to be processed by Prometheus.

## Prerequisites
1. Clean install of Nagios
2. Functioning Prometheus Node_Exporter
3. Python3 Prometheus_Collector

## Upload the nagprom-service.py script to the the "/usr/local/nagios/libexec/" directory.
Set the permissions as needed for your instance of Nagios.

## Create nagprom-service Command
Edit the file "/usr/local/nagios/etc/objects/commands.cfg" to include the following.

    define command{
         command_name     nagprom-service
         command_line     python3 /usr/local/nagios/libexec/nagprom-service.py -H $HOSTNAME$ -s "$SERVICEDESC$" -p "$SERVICEPERFDATA$"
    }

## Modify nagios.cfg to enable metric export.

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
      
      #host_perfdata_command=process-host-perfdata
      service_perfdata_command=nagprom-service

## Add Nagios user to Prometheus group
      usermod -a -G Prometheus nagios

## Restart Nagios
      systemctl restart nagios
      
