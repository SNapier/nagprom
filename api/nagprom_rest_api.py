#!/usr/bin/env python3
"""
NagProm REST API Server
Simple, working API for Nagios monitoring data
"""

import os
import sys
import json
import logging
import argparse
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add SRE Analytics Engine
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'analytics'))
from sre_analytics_engine import SREAnalyticsEngine, SLOTarget, SLIMetric, SLIType
from alert_correlation import AlertCorrelationEngine, Alert, AlertSeverity, AlertStatus

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"]
)

# Configuration
PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://localhost:9090')
API_KEY = os.environ.get('NAGPROM_API_KEY', None)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrometheusClient:
    """Simple Prometheus client"""
    
    def __init__(self, prometheus_url):
        self.prometheus_url = prometheus_url.rstrip('/')
    
    def query(self, query):
        """Execute PromQL query"""
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            params = {'query': query}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Prometheus query failed: {e}")
            return None
    
    def query_range(self, query, start, end, step):
        """Execute PromQL range query for time-series data"""
        try:
            url = f"{self.prometheus_url}/api/v1/query_range"
            params = {
                'query': query,
                'start': start,
                'end': end,
                'step': step
            }
            response = requests.get(url, params=params, timeout=30)  # Longer timeout for range queries
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Prometheus range query failed: {e}")
            return None
    
    def get_hosts(self):
        """Get all monitored hosts"""
        # Use the correct metric name from Prometheus
        queries = [
            'nagios_host_state',
            'nagios_host_status',
            'nagios_host_up',
            'nagios_hosts',
            'up{job="nagios"}',
            'nagios_up'
        ]
        
        for query in queries:
            result = self.query(query)
            if result and 'data' in result and result['data']['result']:
                logger.info(f"Found hosts using query: {query}")
                break
        else:
            logger.warning("No Nagios host metrics found in Prometheus")
            return []
        
        hosts = []
        for metric in result['data']['result']:
            # Handle different metric label structures
            host_name = (metric['metric'].get('host') or 
                        metric['metric'].get('instance') or 
                        metric['metric'].get('name') or 
                        'unknown')
            
            # Get state - use state_id if available, otherwise state
            state = metric['metric'].get('state_id', metric['metric'].get('state', 'unknown'))
            
            # Only add if this is a host entry (not a service entry)
            if host_name and host_name != 'unknown':
                host = {
                    'name': host_name,
                    'state': str(state),
                    'state_type': 'hard',  # Default to hard state for hosts
                    'last_check': metric['value'][0] if len(metric['value']) > 0 else 0
                }
                hosts.append(host)
        
        return hosts
    
    def get_services(self):
        """Get all monitored services"""
        # Use the correct metric name from Prometheus
        queries = [
            'nagios_service_state',
            'nagios_service_status',
            'nagios_services',
            'nagios_service_up',
            'nagios_service_ok'
        ]
        
        for query in queries:
            result = self.query(query)
            if result and 'data' in result and result['data']['result']:
                logger.info(f"Found services using query: {query}")
                break
        else:
            logger.warning("No Nagios service metrics found in Prometheus")
            return []
        
        services = []
        for metric in result['data']['result']:
            # Handle different metric label structures
            host_name = (metric['metric'].get('host') or 
                        metric['metric'].get('instance') or 
                        'unknown')
            
            service_name = (metric['metric'].get('service') or 
                          metric['metric'].get('name') or 
                          'unknown')
            
            # Get state - use state_id if available, otherwise state
            state = metric['metric'].get('state_id', metric['metric'].get('state', 'unknown'))
            
            # Only add if this is a service entry (has both host and service names)
            if host_name and service_name and host_name != 'unknown' and service_name != 'unknown':
                service = {
                    'host': host_name,
                    'service': service_name,
                    'state': str(state),
                    'state_type': 'hard',  # Default to hard state for services
                    'last_check': metric['value'][0] if len(metric['value']) > 0 else 0
                }
                services.append(service)
        
        return services
    
    def get_performance_data(self):
        """Get performance data for services"""
        try:
            result = self.query('nagios_performance_data')
            if not result or 'data' not in result or not result['data']['result']:
                return {}
            
            performance = {}
            for metric in result['data']['result']:
                host_name = metric['metric'].get('host', 'unknown')
                service_name = metric['metric'].get('service', 'unknown')
                metric_name = metric['metric'].get('metric', 'value')  # Get the specific metric name
                unit = metric['metric'].get('unit', '')  # Get unit if available
                
                if host_name != 'unknown' and service_name != 'unknown':
                    key = f"{host_name}:{service_name}"
                    
                    # Initialize service entry if it doesn't exist
                    if key not in performance:
                        performance[key] = {
                            'host': host_name,
                            'service': service_name,
                            'timestamp': metric['value'][0] if len(metric['value']) > 0 else 0,
                            'metrics': {}
                        }
                    
                    # Add the specific metric
                    metric_value = metric['value'][1] if len(metric['value']) > 1 else 'unknown'
                    if unit:
                        performance[key]['metrics'][metric_name] = {
                            'value': metric_value,
                            'unit': unit
                        }
                    else:
                        performance[key]['metrics'][metric_name] = metric_value
            
            return performance
        except Exception as e:
            logger.error(f"Failed to get performance data: {e}")
            return {}

    def get_thresholds(self):
        """Get performance thresholds for services"""
        try:
            result = self.query('nagios_performance_thresholds')
            if not result or 'data' not in result or not result['data']['result']:
                return {}
            
            thresholds = {}
            for metric in result['data']['result']:
                host_name = metric['metric'].get('host', 'unknown')
                service_name = metric['metric'].get('service', 'unknown')
                metric_name = metric['metric'].get('metric', 'value')
                threshold_type = metric['metric'].get('threshold_type', 'warning')  # Get threshold type
                
                if host_name != 'unknown' and service_name != 'unknown':
                    key = f"{host_name}:{service_name}"
                    
                    # Initialize service entry if it doesn't exist
                    if key not in thresholds:
                        thresholds[key] = {
                            'host': host_name,
                            'service': service_name,
                            'thresholds': {}
                        }
                    
                    # Initialize metric entry if it doesn't exist
                    if metric_name not in thresholds[key]['thresholds']:
                        thresholds[key]['thresholds'][metric_name] = {
                            'warning': None,
                            'critical': None,
                            'min': None,
                            'max': None
                        }
                    
                    # Parse threshold value
                    threshold_value = metric['value'][1] if len(metric['value']) > 1 else None
                    if threshold_value is not None:
                        try:
                            # Store based on threshold type
                            if threshold_type == 'critical':
                                thresholds[key]['thresholds'][metric_name]['critical'] = float(threshold_value)
                            elif threshold_type == 'min':
                                thresholds[key]['thresholds'][metric_name]['min'] = float(threshold_value)
                            elif threshold_type == 'max':
                                thresholds[key]['thresholds'][metric_name]['max'] = float(threshold_value)
                            else:  # Default to warning
                                thresholds[key]['thresholds'][metric_name]['warning'] = float(threshold_value)
                        except (ValueError, TypeError):
                            # If parsing fails, store as string
                            if threshold_type == 'critical':
                                thresholds[key]['thresholds'][metric_name]['critical'] = threshold_value
                            elif threshold_type == 'min':
                                thresholds[key]['thresholds'][metric_name]['min'] = threshold_value
                            elif threshold_type == 'max':
                                thresholds[key]['thresholds'][metric_name]['max'] = threshold_value
                            else:
                                thresholds[key]['thresholds'][metric_name]['warning'] = threshold_value
            
            return thresholds
        except Exception as e:
            logger.error(f"Failed to get thresholds: {e}")
            return {}
    
    def get_hosts_timeseries(self, host=None, start=None, end=None, step='1m'):
        """Get time-series data for hosts"""
        try:
            # Build query based on available host metrics
            queries = [
                'nagios_host_state',
                'nagios_host_status',
                'nagios_host_up',
                'nagios_hosts',
                'up{job="nagios"}',
                'nagios_up'
            ]
            
            query = None
            for q in queries:
                if host:
                    # Add host filter to query
                    if 'nagios_host' in q:
                        query = f'{q}{{host="{host}"}}'
                    elif 'up{job="nagios"}' in q:
                        query = f'up{{job="nagios",instance="{host}"}}'
                    else:
                        query = f'{q}{{instance="{host}"}}'
                else:
                    query = q
                
                # Test if this query returns data
                test_result = self.query(query)
                if test_result and 'data' in test_result and test_result['data']['result']:
                    logger.info(f"Using query for host timeseries: {query}")
                    break
            else:
                logger.warning("No suitable host query found for timeseries")
                return {}
            
            # Execute range query
            result = self.query_range(query, start, end, step)
            if not result or 'data' not in result:
                return {}
            
            return result['data']
        except Exception as e:
            logger.error(f"Failed to get host timeseries: {e}")
            return {}
    
    def get_services_timeseries(self, host=None, service=None, start=None, end=None, step='1m'):
        """Get time-series data for services"""
        try:
            # Build query based on available service metrics
            queries = [
                'nagios_service_state',
                'nagios_service_status',
                'nagios_services',
                'nagios_service_up',
                'nagios_service_ok'
            ]
            
            query = None
            for q in queries:
                if host and service:
                    query = f'{q}{{host="{host}",service="{service}"}}'
                elif host:
                    query = f'{q}{{host="{host}"}}'
                else:
                    query = q
                
                # Test if this query returns data
                test_result = self.query(query)
                if test_result and 'data' in test_result and test_result['data']['result']:
                    logger.info(f"Using query for service timeseries: {query}")
                    break
            else:
                logger.warning("No suitable service query found for timeseries")
                return {}
            
            # Execute range query
            result = self.query_range(query, start, end, step)
            if not result or 'data' not in result:
                return {}
            
            return result['data']
        except Exception as e:
            logger.error(f"Failed to get service timeseries: {e}")
            return {}
    
    def get_performance_timeseries(self, host=None, service=None, metric=None, start=None, end=None, step='1m'):
        """Get time-series data for performance metrics"""
        try:
            # Build query for performance data
            if host and service and metric:
                query = f'nagios_performance_data{{host="{host}",service="{service}",metric="{metric}"}}'
            elif host and service:
                query = f'nagios_performance_data{{host="{host}",service="{service}"}}'
            elif host:
                query = f'nagios_performance_data{{host="{host}"}}'
            else:
                query = 'nagios_performance_data'
            
            # Execute range query
            result = self.query_range(query, start, end, step)
            if not result or 'data' not in result:
                return {}
            
            return result['data']
        except Exception as e:
            logger.error(f"Failed to get performance timeseries: {e}")
            return {}
    
    def get_sli_data(self, service, sli_type, start_time, end_time):
        """Get SLI data for SRE analytics"""
        try:
            # Map SLI types to Prometheus queries
            sli_queries = {
                'availability': f'nagios_service_state{{service="{service}"}}',
                'latency': f'nagios_performance_data{{service="{service}",metric=~".*time.*"}}',
                'error_rate': f'rate(nagios_service_state{{service="{service}",state="2"}}[5m])',
                'throughput': f'rate(nagios_performance_data{{service="{service}"}}[5m])',
                'saturation': f'nagios_performance_data{{service="{service}",metric=~".*util.*|.*usage.*"}}'
            }
            
            query = sli_queries.get(sli_type, f'nagios_service_state{{service="{service}"}}')
            result = self.query_range(query, start_time, end_time, '5m')
            return result
        except Exception as e:
            logger.error(f"SLI data query failed: {e}")
            return None
    
    def get_host_sli_data(self, host, start_time, end_time):
        """Get host-level SLI data for SRE analytics"""
        try:
            # Host availability query
            query = f'nagios_host_state{{host="{host}"}}'
            result = self.query_range(query, start_time, end_time, '5m')
            return result
        except Exception as e:
            logger.error(f"Host SLI data query failed: {e}")
            return None

# Initialize Prometheus client
prometheus = PrometheusClient(PROMETHEUS_URL)

# Initialize SRE Analytics Engine
sre_engine = SREAnalyticsEngine(prometheus_client=prometheus)

# Initialize Alert Correlation Engine
alert_correlation_engine = AlertCorrelationEngine()

def require_api_key(f):
    """Decorator to require API key authentication"""
    def decorated_function(*args, **kwargs):
        if not API_KEY:
            return f(*args, **kwargs)  # No auth required
        
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            # Check for API key in query parameter
            api_key = request.args.get('api_key')
        
        if api_key != API_KEY:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key',
                'timestamp': datetime.now().isoformat()
            }), 401
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__  # Fix Flask endpoint naming
    return decorated_function

def create_response(success=True, data=None, error=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat()
    }
    
    if success:
        response['data'] = data or {}
    else:
        response['error'] = error
    
    return jsonify(response)

def get_pagination_params():
    """Get pagination parameters from request"""
    limit = request.args.get('limit', type=int, default=100)
    offset = request.args.get('offset', type=int, default=0)
    
    # Enforce maximum limits to prevent large datasets
    max_limit = 1000
    if limit > max_limit:
        limit = max_limit
    if limit < 1:
        limit = 1
    
    # Ensure offset is not negative
    if offset < 0:
        offset = 0
    
    return limit, offset

def apply_pagination(data, limit, offset):
    """Apply pagination to data"""
    if isinstance(data, list):
        return data[offset:offset + limit]
    elif isinstance(data, dict):
        # For dict data, convert to list of items and paginate
        items = list(data.items())
        paginated_items = items[offset:offset + limit]
        return dict(paginated_items)
    return data

def _get_status_from_state(state):
    """Convert state value to status name"""
    state_mapping = {
        '0': 'OK',
        '1': 'WARNING', 
        '2': 'CRITICAL',
        '3': 'UNKNOWN'
    }
    return state_mapping.get(str(state), 'UNKNOWN')

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint - no auth required"""
    try:
        # Test Prometheus connectivity
        test_query = prometheus.query('up')
        
        health_data = {
            'status': 'healthy',
            'prometheus_connected': test_query is not None,
            'api_key_required': API_KEY is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        return create_response(True, health_data)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_response(False, error=f"Health check failed: {str(e)}")

@app.route('/api/v1/summary', methods=['GET'])
@require_api_key
def get_summary():
    """Get monitoring summary"""
    try:
        hosts = prometheus.get_hosts()
        services = prometheus.get_services()
        
        # Count states
        host_states = {}
        service_states = {}
        
        for host in hosts:
            state = host['state']
            host_states[state] = host_states.get(state, 0) + 1
        
        for service in services:
            state = service['state']
            service_states[state] = service_states.get(state, 0) + 1
        
        summary = {
            'total_hosts': len(hosts),
            'total_services': len(services),
            'host_states': host_states,
            'service_states': service_states,
            'up_hosts': host_states.get('0', 0),  # 0 = UP
            'down_hosts': host_states.get('1', 0),  # 1 = DOWN
            'ok_services': service_states.get('0', 0),  # 0 = OK
            'warning_services': service_states.get('1', 0),  # 1 = WARNING
            'critical_services': service_states.get('2', 0),  # 2 = CRITICAL
            'unknown_services': service_states.get('3', 0)  # 3 = UNKNOWN
        }
        
        return create_response(True, summary)
    except Exception as e:
        logger.error(f"Summary failed: {e}")
        return create_response(False, error=f"Failed to get summary: {str(e)}")

@app.route('/api/v1/hosts', methods=['GET'])
@limiter.limit("200 per hour")
@require_api_key
def get_hosts():
    """Get all monitored hosts"""
    try:
        hosts = prometheus.get_hosts()
        
        # Filter by host name if specified
        host_filter = request.args.get('host')
        if host_filter:
            hosts = [h for h in hosts if h['name'] == host_filter]
        
        # Apply pagination
        limit, offset = get_pagination_params()
        paginated_hosts = apply_pagination(hosts, limit, offset)
        
        response_data = {
            'hosts': paginated_hosts,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': len(hosts),
                'returned': len(paginated_hosts)
            }
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Hosts failed: {e}")
        return create_response(False, error=f"Failed to get hosts: {str(e)}")

@app.route('/api/v1/services', methods=['GET'])
@limiter.limit("200 per hour")
@require_api_key
def get_services():
    """Get all monitored services"""
    try:
        services = prometheus.get_services()
        
        # Filter by host name if specified
        host_filter = request.args.get('host')
        if host_filter:
            services = [s for s in services if s['host'] == host_filter]
        
        # Filter by service name if specified
        service_filter = request.args.get('service')
        if service_filter:
            services = [s for s in services if s['service'] == service_filter]
        
        # Apply pagination
        limit, offset = get_pagination_params()
        paginated_services = apply_pagination(services, limit, offset)
        
        response_data = {
            'services': paginated_services,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': len(services),
                'returned': len(paginated_services)
            }
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Services failed: {e}")
        return create_response(False, error=f"Failed to get services: {str(e)}")

@app.route('/api/v1/sre/dashboard', methods=['GET'])
@require_api_key
def get_sre_dashboard():
    """Get SRE dashboard data"""
    try:
        hosts = prometheus.get_hosts()
        services = prometheus.get_services()
        
        # Calculate basic SRE metrics
        total_hosts = len(hosts)
        up_hosts = len([h for h in hosts if h['state'] == '0'])  # 0 = UP
        down_hosts = len([h for h in hosts if h['state'] == '1'])  # 1 = DOWN
        total_services = len(services)
        ok_services = len([s for s in services if s['state'] == '0'])  # 0 = OK
        problem_services = len([s for s in services if s['state'] in ['1', '2', '3']])  # 1=WARNING, 2=CRITICAL, 3=UNKNOWN
        
        # Calculate uptime percentages
        host_uptime = (up_hosts / total_hosts * 100) if total_hosts > 0 else 0
        service_uptime = (ok_services / total_services * 100) if total_services > 0 else 0
        
        sre_data = {
            'host_uptime_percentage': round(host_uptime, 2),
            'service_uptime_percentage': round(service_uptime, 2),
            'total_hosts': total_hosts,
            'up_hosts': up_hosts,
            'down_hosts': down_hosts,
            'total_services': total_services,
            'ok_services': ok_services,
            'problem_services': problem_services,
            'last_updated': datetime.now().isoformat()
        }
        
        return create_response(True, sre_data)
    except Exception as e:
        logger.error(f"SRE dashboard failed: {e}")
        return create_response(False, error=f"Failed to get SRE dashboard: {str(e)}")

@app.route('/api/v1/sre/capacity', methods=['GET'])
@require_api_key
def get_capacity():
    """Get capacity planning data"""
    try:
        hosts = prometheus.get_hosts()
        services = prometheus.get_services()
        
        # Simple capacity analysis
        capacity_data = {
            'total_hosts': len(hosts),
            'total_services': len(services),
            'services_per_host': round(len(services) / len(hosts), 2) if len(hosts) > 0 else 0,
            'monitoring_load': 'low' if len(services) < 100 else 'medium' if len(services) < 500 else 'high',
            'recommendations': [
                'Monitor host resource usage',
                'Review service check intervals',
                'Consider load balancing for high-traffic services'
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        return create_response(True, capacity_data)
    except Exception as e:
        logger.error(f"Capacity failed: {e}")
        return create_response(False, error=f"Failed to get capacity data: {str(e)}")

@app.route('/api/v1/sre/service/reliability', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def get_service_reliability():
    """Get detailed reliability metrics for services using query parameters"""
    try:
        # Get query parameters
        service = request.args.get('service')
        host = request.args.get('host')
        hours = request.args.get('hours', type=int, default=24)
        
        if not service:
            return create_response(False, error="Service parameter is required")
        
        time_window = timedelta(hours=hours)
        
        # Get service data from Prometheus
        services = prometheus.get_services()
        
        # Filter by service and optionally by host
        if host:
            service_data = [s for s in services if s['service'] == service and s['host'] == host]
        else:
            service_data = [s for s in services if s['service'] == service]
        
        if not service_data:
            return create_response(False, error=f"Service '{service}' not found")
        
        # Calculate reliability metrics
        end_time = datetime.now()
        start_time = end_time - time_window
        
        # Calculate availability
        total_instances = len(service_data)
        healthy_instances = len([s for s in service_data if s['state'] == '0'])  # 0 = OK
        availability_percentage = (healthy_instances / total_instances * 100) if total_instances > 0 else 0
        
        # Get performance metrics for the service
        performance_data = []
        for service_instance in service_data:
            try:
                metrics = prometheus.get_performance_data(
                    service_instance['host'], 
                    service_instance['service']
                )
                if metrics:
                    performance_data.extend(metrics)
            except Exception as e:
                logger.warning(f"Failed to get metrics for {service_instance['host']}:{service_instance['service']}: {e}")
        
        # Calculate basic SRE metrics
        reliability_data = {
            'service': service,
            'host_filter': host,
            'time_window': time_window.total_seconds(),
            'measurement_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'availability_percentage': round(availability_percentage, 2),
            'total_instances': total_instances,
            'healthy_instances': healthy_instances,
            'unhealthy_instances': total_instances - healthy_instances,
            'service_breakdown': {
                'ok': healthy_instances,
                'warning': len([s for s in service_data if s['state'] == '1']),
                'critical': len([s for s in service_data if s['state'] == '2']),
                'unknown': len([s for s in service_data if s['state'] == '3'])
            },
            'performance_metrics': performance_data[:10],  # Limit to first 10 metrics
            'recommendations': []
        }
        
        # Generate recommendations
        if availability_percentage < 95:
            reliability_data['recommendations'].append("Service availability below 95% - investigate issues")
        if total_instances - healthy_instances > 0:
            reliability_data['recommendations'].append(f"{total_instances - healthy_instances} instances need attention")
        
        return create_response(True, reliability_data)
    except Exception as e:
        logger.error(f"Service reliability failed: {e}")
        return create_response(False, error=f"Failed to get service reliability: {str(e)}")

@app.route('/api/v1/sre/host/reliability', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def get_host_reliability():
    """Get detailed reliability metrics for hosts using query parameters"""
    try:
        # Get query parameters
        host = request.args.get('host')
        hours = request.args.get('hours', type=int, default=24)
        
        if not host:
            return create_response(False, error="Host parameter is required")
        
        time_window = timedelta(hours=hours)
        
        # Get host data from Prometheus
        hosts = prometheus.get_hosts()
        logger.info(f"Available hosts: {[h['name'] for h in hosts]}")
        host_data = next((h for h in hosts if h['name'] == host), None)
        
        if not host_data:
            return create_response(False, error=f"Host '{host}' not found")
        
        # Get services for this host
        services = prometheus.get_services()
        host_services = [s for s in services if s['host'] == host]
        logger.info(f"Found {len(host_services)} services for host {host}: {[s['service'] for s in host_services]}")
        
        # Calculate host-level reliability metrics
        end_time = datetime.now()
        start_time = end_time - time_window
        
        # Calculate availability
        total_checks = len(host_services)
        up_services = len([s for s in host_services if s['state'] == '0'])  # 0 = OK
        availability_percentage = (up_services / total_checks * 100) if total_checks > 0 else 0
        
        # Get performance metrics for the host
        performance_data = []
        try:
            # Get metrics for all services on this host
            for service in host_services:
                try:
                    metrics = prometheus.get_performance_data(host, service['service'])
                    if metrics:
                        performance_data.extend(metrics[:5])  # Limit to 5 metrics per service
                except Exception as e:
                    logger.warning(f"Failed to get metrics for {host}:{service['service']}: {e}")
        except Exception as e:
            logger.warning(f"Failed to get performance data for host {host}: {e}")
        
        # Calculate basic SRE metrics
        reliability_data = {
            'host': host,
            'time_window': time_window.total_seconds(),
            'measurement_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'availability_percentage': round(availability_percentage, 2),
            'total_services': total_checks,
            'healthy_services': up_services,
            'unhealthy_services': total_checks - up_services,
            'host_state': host_data['state'],
            'host_status': _get_status_from_state(host_data['state']),
            'service_breakdown': {
                'ok': up_services,
                'warning': len([s for s in host_services if s['state'] == '1']),
                'critical': len([s for s in host_services if s['state'] == '2']),
                'unknown': len([s for s in host_services if s['state'] == '3'])
            },
            'performance_metrics': performance_data,
            'service_details': [
                {
                    'service': s['service'],
                    'state': s['state'],
                    'status': _get_status_from_state(s['state']),
                    'last_check': s.get('last_check', 'unknown')
                }
                for s in host_services
            ],
            'recommendations': []
        }
        
        # Generate recommendations
        if availability_percentage < 95:
            reliability_data['recommendations'].append("Host availability below 95% - investigate service issues")
        if total_checks - up_services > 0:
            reliability_data['recommendations'].append(f"{total_checks - up_services} services need attention")
        
        return create_response(True, reliability_data)
    except Exception as e:
        logger.error(f"Host reliability failed: {e}")
        return create_response(False, error=f"Failed to get host reliability: {str(e)}")

@app.route('/api/v1/sre/anomalies', methods=['GET'])
@limiter.limit("50 per hour")  # Lower limit for anomaly detection
@require_api_key
def get_anomalies():
    """Get performance anomalies detected by SRE analytics"""
    try:
        # Get query parameters
        service = request.args.get('service')
        host = request.args.get('host')
        threshold_std = request.args.get('threshold_std', type=float, default=2.0)
        
        # Get services to analyze
        if service and host:
            # Specific service on specific host
            services_to_analyze = [f"{host}:{service}"]
        elif service:
            # Specific service across all hosts
            services_to_analyze = [service]
        elif host:
            # All services on specific host
            all_services = prometheus.get_services()
            services_to_analyze = [s['service'] for s in all_services if s['host'] == host]
        else:
            # All services
            services_to_analyze = sre_engine._get_monitored_services()
        
        # Get anomalies for the selected services
        all_anomalies = []
        for svc in services_to_analyze:
            try:
                service_anomalies = sre_engine.detect_anomalies(svc, threshold_std)
                all_anomalies.extend(service_anomalies)
            except Exception as e:
                logger.warning(f"Failed to detect anomalies for {svc}: {e}")
        
        anomalies = all_anomalies
        
        # Sort by severity and timestamp
        anomalies.sort(key=lambda x: (x.get('severity', 'low') == 'high', x.get('timestamp', '')), reverse=True)
        
        # Apply pagination
        limit, offset = get_pagination_params()
        paginated_anomalies = anomalies[offset:offset + limit]
        
        response_data = {
            'anomalies': paginated_anomalies,
            'total_anomalies': len(anomalies),
            'pagination': {
                'limit': limit,
                'offset': offset,
                'returned': len(paginated_anomalies)
            },
            'detection_params': {
                'threshold_std': threshold_std,
                'service_filter': service,
                'host_filter': host
            }
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        return create_response(False, error=f"Failed to get anomalies: {str(e)}")

@app.route('/api/v1/sre/slo', methods=['POST'])
@limiter.limit("50 per hour")
@require_api_key
def create_slo():
    """Create a new SLO target"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, error="No JSON data provided")
        
        # Validate required fields
        required_fields = ['service', 'name', 'sli_type', 'target_percentage']
        for field in required_fields:
            if field not in data:
                return create_response(False, error=f"Missing required field: {field}")
        
        # Validate SLI type
        try:
            sli_type = SLIType(data['sli_type'])
        except ValueError:
            return create_response(False, error=f"Invalid SLI type: {data['sli_type']}")
        
        # Create SLO target
        slo_target = SLOTarget(
            name=data['name'],
            sli_type=sli_type,
            target_percentage=float(data['target_percentage']),
            measurement_window=timedelta(days=data.get('measurement_window_days', 30)),
            error_budget_policy=data.get('error_budget_policy', 'burn_rate')
        )
        
        # Register SLO with engine
        sre_engine.register_slo(data['service'], slo_target)
        
        response_data = {
            'slo_created': True,
            'service': data['service'],
            'slo_name': data['name'],
            'target_percentage': data['target_percentage'],
            'error_budget_percentage': slo_target.error_budget_percentage
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"SLO creation failed: {e}")
        return create_response(False, error=f"Failed to create SLO: {str(e)}")

@app.route('/api/v1/sre/slo', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def list_slos():
    """List all registered SLOs"""
    try:
        slo_data = {}
        
        for service, slo_targets in sre_engine.slo_targets.items():
            slo_data[service] = []
            for slo_target in slo_targets:
                slo_data[service].append({
                    'name': slo_target.name,
                    'sli_type': slo_target.sli_type.value,
                    'target_percentage': slo_target.target_percentage,
                    'error_budget_percentage': slo_target.error_budget_percentage,
                    'measurement_window_days': slo_target.measurement_window.days,
                    'error_budget_policy': slo_target.error_budget_policy
                })
        
        return create_response(True, slo_data)
    except Exception as e:
        logger.error(f"SLO listing failed: {e}")
        return create_response(False, error=f"Failed to list SLOs: {str(e)}")

@app.route('/api/v1/performance', methods=['GET'])
@require_api_key
def get_performance():
    """Get performance metrics"""
    try:
        # Get actual performance data from Prometheus
        performance_data = prometheus.get_performance_data()
        
        # Filter by host name if specified
        host_filter = request.args.get('host')
        if host_filter:
            performance_data = {k: v for k, v in performance_data.items() 
                              if v['host'] == host_filter}
        
        # Filter by service name if specified
        service_filter = request.args.get('service')
        if service_filter:
            performance_data = {k: v for k, v in performance_data.items() 
                              if v['service'] == service_filter}
        
        # Add API performance info
        api_performance = {
            'api_response_time': 'fast',
            'prometheus_query_time': 'normal',
            'active_connections': 1,
            'uptime': '100%',
            'last_updated': datetime.now().isoformat(),
            'service_metrics': performance_data
        }
        
        return create_response(True, api_performance)
    except Exception as e:
        logger.error(f"Performance failed: {e}")
        return create_response(False, error=f"Failed to get performance data: {str(e)}")

@app.route('/api/v1/debug/metrics', methods=['GET'])
def debug_metrics():
    """Debug endpoint to see what metrics are available"""
    try:
        # Get all metrics from Prometheus
        url = f"{PROMETHEUS_URL}/api/v1/label/__name__/values"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get('status') == 'success':
            metrics = result.get('data', [])
            # Filter for Nagios-related metrics
            nagios_metrics = [m for m in metrics if 'nagios' in m.lower()]
            
            # Get sample data from actual Nagios metrics
            sample_host_data = prometheus.query('nagios_host_state')
            sample_service_data = prometheus.query('nagios_service_state')
            sample_performance_data = prometheus.query('nagios_performance_data')
            
            # Get processed data to see what the API returns
            processed_hosts = prometheus.get_hosts()
            processed_services = prometheus.get_services()
            processed_performance = prometheus.get_performance_data()
            
            debug_data = {
                'total_metrics': len(metrics),
                'nagios_metrics': nagios_metrics,
                'prometheus_url': PROMETHEUS_URL,
                'sample_metrics': metrics[:20],  # First 20 metrics as sample
                'sample_host_data': sample_host_data,
                'sample_service_data': sample_service_data,
                'sample_performance_data': sample_performance_data,
                'processed_hosts': processed_hosts,
                'processed_services': processed_services,
                'processed_performance': processed_performance
            }
            
            return create_response(True, debug_data)
        else:
            return create_response(False, error=f"Failed to get metrics: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Debug metrics failed: {e}")
        return create_response(False, error=f"Debug metrics failed: {str(e)}")

@app.route('/api/v1/debug/thresholds', methods=['GET'])
def debug_thresholds():
    """Debug endpoint to test thresholds functionality"""
    try:
        # Get raw threshold data from Prometheus
        raw_thresholds = prometheus.query('nagios_performance_thresholds')
        
        # Get processed thresholds (max 5 services)
        processed_thresholds = prometheus.get_thresholds()
        
        # Limit to first 5 services for debugging
        limited_thresholds = {}
        count = 0
        for key, data in processed_thresholds.items():
            if count >= 5:
                break
            limited_thresholds[key] = data
            count += 1
        
        # Get performance data for the same services (max 10 services)
        performance_data = prometheus.get_performance_data()
        limited_performance = {}
        count = 0
        for key, data in performance_data.items():
            if count >= 10:
                break
            limited_performance[key] = data
            count += 1
        
        debug_data = {
            'raw_thresholds_query': 'nagios_performance_thresholds',
            'raw_thresholds_data': raw_thresholds,
            'processed_thresholds': limited_thresholds,
            'performance_data': limited_performance,
            'thresholds_count': len(processed_thresholds),
            'performance_count': len(performance_data),
            'prometheus_url': PROMETHEUS_URL
        }
        
        return create_response(True, debug_data)
    except Exception as e:
        logger.error(f"Debug thresholds failed: {e}")
        return create_response(False, error=f"Debug thresholds failed: {str(e)}")

@app.route('/api/v1/metrics', methods=['GET'])
@limiter.limit("200 per hour")
@require_api_key
def get_service_metrics():
    """Get actual service metrics/performance data"""
    try:
        performance_data = prometheus.get_performance_data()
        
        # Filter by host name if specified
        host_filter = request.args.get('host')
        if host_filter:
            performance_data = {k: v for k, v in performance_data.items() 
                              if v['host'] == host_filter}
        
        # Filter by service name if specified
        service_filter = request.args.get('service')
        if service_filter:
            performance_data = {k: v for k, v in performance_data.items() 
                              if v['service'] == service_filter}
        
        # Apply pagination
        limit, offset = get_pagination_params()
        paginated_data = apply_pagination(performance_data, limit, offset)
        
        response_data = {
            'metrics': paginated_data,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': len(performance_data),
                'returned': len(paginated_data)
            }
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Service metrics failed: {e}")
        return create_response(False, error=f"Failed to get service metrics: {str(e)}")

@app.route('/api/v1/thresholds', methods=['GET'])
@limiter.limit("200 per hour")
@require_api_key
def get_thresholds():
    """Get performance thresholds for services"""
    try:
        thresholds_data = prometheus.get_thresholds()
        
        # Filter by host name if specified
        host_filter = request.args.get('host')
        if host_filter:
            thresholds_data = {k: v for k, v in thresholds_data.items() 
                             if v['host'] == host_filter}
        
        # Filter by service name if specified
        service_filter = request.args.get('service')
        if service_filter:
            thresholds_data = {k: v for k, v in thresholds_data.items() 
                             if v['service'] == service_filter}
        
        # Apply pagination
        limit, offset = get_pagination_params()
        paginated_data = apply_pagination(thresholds_data, limit, offset)
        
        response_data = {
            'thresholds': paginated_data,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': len(thresholds_data),
                'returned': len(paginated_data)
            }
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Thresholds failed: {e}")
        return create_response(False, error=f"Failed to get thresholds: {str(e)}")

@app.route('/api/v1/timeseries/hosts', methods=['GET'])
@limiter.limit("100 per hour")  # Lower limit for timeseries queries
@require_api_key
def get_hosts_timeseries():
    """Get time-series data for hosts"""
    try:
        # Get query parameters
        host = request.args.get('host')
        start = request.args.get('start')
        end = request.args.get('end')
        step = request.args.get('step', '1m')
        
        # Validate required parameters
        if not start or not end:
            return create_response(False, error="start and end parameters are required")
        
        # Validate step format
        valid_steps = ['15s', '30s', '1m', '5m', '15m', '30m', '1h', '2h', '6h', '12h', '1d']
        if step not in valid_steps:
            return create_response(False, error=f"Invalid step. Must be one of: {', '.join(valid_steps)}")
        
        # Get timeseries data
        timeseries_data = prometheus.get_hosts_timeseries(host, start, end, step)
        
        response_data = {
            'timeseries': timeseries_data,
            'query_params': {
                'host': host,
                'start': start,
                'end': end,
                'step': step
            }
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Host timeseries failed: {e}")
        return create_response(False, error=f"Failed to get host timeseries: {str(e)}")

@app.route('/api/v1/timeseries/services', methods=['GET'])
@limiter.limit("100 per hour")  # Lower limit for timeseries queries
@require_api_key
def get_services_timeseries():
    """Get time-series data for services"""
    try:
        # Get query parameters
        host = request.args.get('host')
        service = request.args.get('service')
        start = request.args.get('start')
        end = request.args.get('end')
        step = request.args.get('step', '1m')
        
        # Validate required parameters
        if not start or not end:
            return create_response(False, error="start and end parameters are required")
        
        # Validate step format
        valid_steps = ['15s', '30s', '1m', '5m', '15m', '30m', '1h', '2h', '6h', '12h', '1d']
        if step not in valid_steps:
            return create_response(False, error=f"Invalid step. Must be one of: {', '.join(valid_steps)}")
        
        # Get timeseries data
        timeseries_data = prometheus.get_services_timeseries(host, service, start, end, step)
        
        response_data = {
            'timeseries': timeseries_data,
            'query_params': {
                'host': host,
                'service': service,
                'start': start,
                'end': end,
                'step': step
            }
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Service timeseries failed: {e}")
        return create_response(False, error=f"Failed to get service timeseries: {str(e)}")

@app.route('/api/v1/timeseries/performance', methods=['GET'])
@limiter.limit("100 per hour")  # Lower limit for timeseries queries
@require_api_key
def get_performance_timeseries():
    """Get time-series data for performance metrics"""
    try:
        # Get query parameters
        host = request.args.get('host')
        service = request.args.get('service')
        metric = request.args.get('metric')
        start = request.args.get('start')
        end = request.args.get('end')
        step = request.args.get('step', '1m')
        
        # Validate required parameters
        if not start or not end:
            return create_response(False, error="start and end parameters are required")
        
        # Validate step format
        valid_steps = ['15s', '30s', '1m', '5m', '15m', '30m', '1h', '2h', '6h', '12h', '1d']
        if step not in valid_steps:
            return create_response(False, error=f"Invalid step. Must be one of: {', '.join(valid_steps)}")
        
        # Get timeseries data
        timeseries_data = prometheus.get_performance_timeseries(host, service, metric, start, end, step)
        
        response_data = {
            'timeseries': timeseries_data,
            'query_params': {
                'host': host,
                'service': service,
                'metric': metric,
                'start': start,
                'end': end,
                'step': step
            }
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Performance timeseries failed: {e}")
        return create_response(False, error=f"Failed to get performance timeseries: {str(e)}")

# Alert Correlation Endpoints
@app.route('/api/v1/sre/alerts/correlation', methods=['GET'])
@limiter.limit("50 per hour")  # Lower limit for correlation analysis
@require_api_key
def get_alert_correlations():
    """Get current alert correlations"""
    try:
        # Get query parameters
        time_window = request.args.get('time_window', type=int, default=900)  # 15 minutes default
        service = request.args.get('service')
        host = request.args.get('host')
        correlation_type = request.args.get('type')  # temporal, spatial, similarity, dependency
        
        # Validate time window
        if time_window < 60 or time_window > 86400:  # 1 minute to 24 hours
            return create_response(False, error="time_window must be between 60 and 86400 seconds")
        
        # Get correlations
        from datetime import timedelta
        import asyncio
        clusters = asyncio.run(alert_correlation_engine.correlate_alerts(timedelta(seconds=time_window)))
        
        # Filter by service/host if specified
        if service or host:
            filtered_clusters = []
            for cluster in clusters:
                cluster_alerts = cluster.alerts
                if service and not any(alert.service == service for alert in cluster_alerts):
                    continue
                if host and not any(alert.host == host for alert in cluster_alerts):
                    continue
                filtered_clusters.append(cluster)
            clusters = filtered_clusters
        
        # Filter by correlation type if specified
        if correlation_type:
            clusters = [c for c in clusters if c.correlation_type.value == correlation_type]
        
        # Convert clusters to JSON-serializable format
        correlation_data = []
        for cluster in clusters:
            cluster_data = {
                'id': cluster.id,
                'correlation_type': cluster.correlation_type.value,
                'confidence_score': cluster.confidence_score,
                'alert_count': len(cluster.alerts),
                'created_at': cluster.created_at.isoformat(),
                'root_cause_candidates': cluster.root_cause_candidates,
                'impact_assessment': cluster.impact_assessment,
                'alerts': [
                    {
                        'id': alert.id,
                        'service': alert.service,
                        'host': alert.host,
                        'severity': alert.severity.value,
                        'title': alert.title,
                        'timestamp': alert.timestamp.isoformat()
                    }
                    for alert in cluster.alerts
                ]
            }
            correlation_data.append(cluster_data)
        
        # Get correlation metrics
        metrics = alert_correlation_engine.get_correlation_metrics()
        
        response_data = {
            'correlations': correlation_data,
            'metrics': metrics,
            'query_params': {
                'time_window': time_window,
                'service': service,
                'host': host,
                'correlation_type': correlation_type
            }
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Alert correlation failed: {e}")
        return create_response(False, error=f"Failed to get alert correlations: {str(e)}")

@app.route('/api/v1/sre/alerts', methods=['POST'])
@limiter.limit("1000 per hour")  # Higher limit for alert ingestion
@require_api_key
def receive_alert():
    """Webhook endpoint for receiving alerts"""
    try:
        # Get alert data from request
        alert_data = request.get_json()
        
        if not alert_data:
            return create_response(False, error="No alert data provided")
        
        # Validate required fields
        required_fields = ['id', 'service', 'host', 'severity', 'title']
        for field in required_fields:
            if field not in alert_data:
                return create_response(False, error=f"Missing required field: {field}")
        
        # Create Alert object
        alert = Alert(
            id=alert_data['id'],
            timestamp=datetime.fromisoformat(alert_data.get('timestamp', datetime.now().isoformat())),
            service=alert_data['service'],
            host=alert_data['host'],
            severity=AlertSeverity(alert_data['severity']),
            status=AlertStatus(alert_data.get('status', 'firing')),
            title=alert_data['title'],
            description=alert_data.get('description', ''),
            fingerprint=alert_data.get('fingerprint')
        )
        
        # Add to correlation engine
        alert_correlation_engine.add_alert(alert)
        
        response_data = {
            'alert_id': alert.id,
            'status': 'received',
            'correlation_triggered': True
        }
        
        return create_response(True, response_data)
    except Exception as e:
        logger.error(f"Alert reception failed: {e}")
        return create_response(False, error=f"Failed to receive alert: {str(e)}")

@app.route('/api/v1/sre/alerts/metrics', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def get_alert_metrics():
    """Get alert correlation metrics"""
    try:
        metrics = alert_correlation_engine.get_correlation_metrics()
        
        # Add additional metrics
        metrics['engine_status'] = 'active'
        metrics['last_updated'] = datetime.now().isoformat()
        
        return create_response(True, metrics)
    except Exception as e:
        logger.error(f"Alert metrics failed: {e}")
        return create_response(False, error=f"Failed to get alert metrics: {str(e)}")

@app.route('/api/v1/', methods=['GET'])
def api_root():
    """API root with available endpoints"""
    endpoints = {
        'health': '/api/v1/health',
        'summary': '/api/v1/summary',
        'hosts': '/api/v1/hosts',
        'services': '/api/v1/services',
        'sre_dashboard': '/api/v1/sre/dashboard',
        'sre_capacity': '/api/v1/sre/capacity',
        'sre_service_reliability': '/api/v1/sre/service/reliability?service={service}',
        'sre_host_reliability': '/api/v1/sre/host/reliability?host={host}',
        'sre_anomalies': '/api/v1/sre/anomalies',
        'sre_slo_create': '/api/v1/sre/slo (POST)',
        'sre_slo_list': '/api/v1/sre/slo (GET)',
        'performance': '/api/v1/performance',
        'metrics': '/api/v1/metrics',
        'thresholds': '/api/v1/thresholds',
        'timeseries_hosts': '/api/v1/timeseries/hosts',
        'timeseries_services': '/api/v1/timeseries/services',
        'timeseries_performance': '/api/v1/timeseries/performance',
        'alert_correlation': '/api/v1/sre/alerts/correlation',
        'alert_ingestion': '/api/v1/sre/alerts (POST)',
        'alert_metrics': '/api/v1/sre/alerts/metrics',
        'debug_metrics': '/api/v1/debug/metrics',
        'debug_thresholds': '/api/v1/debug/thresholds'
    }
    
    # Query parameters documentation
    query_params = {
        'host': 'Filter results by host name',
        'service': 'Filter results by service name',
        'metric': 'Filter performance data by metric name',
        'start': 'Start time for timeseries queries (RFC3339 or Unix timestamp)',
        'end': 'End time for timeseries queries (RFC3339 or Unix timestamp)',
        'step': 'Step interval for timeseries queries (15s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 6h, 12h, 1d)',
        'limit': 'Maximum number of results to return (default: 100, max: 1000)',
        'offset': 'Number of results to skip for pagination (default: 0)',
        'api_key': 'API key for authentication (if required)'
    }
    
    # Rate limiting information
    rate_limits = {
        'default': '1000 requests per day, 200 requests per hour',
        'hosts': '200 requests per hour',
        'services': '200 requests per hour',
        'metrics': '200 requests per hour',
        'thresholds': '200 requests per hour',
        'timeseries': '100 requests per hour (lower limit for performance)',
        'sre_reliability': '100 requests per hour',
        'sre_anomalies': '50 requests per hour (lower limit for performance)',
        'sre_slo': '50 requests per hour',
        'alert_correlation': '50 requests per hour (lower limit for performance)',
        'alert_ingestion': '1000 requests per hour'
    }
    
    # Query parameters documentation
    query_params = {
        'host': 'Filter results by host name',
        'service': 'Filter results by service name',
        'metric': 'Filter performance data by metric name',
        'start': 'Start time for timeseries queries (RFC3339 or Unix timestamp)',
        'end': 'End time for timeseries queries (RFC3339 or Unix timestamp)',
        'step': 'Step interval for timeseries queries (15s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 6h, 12h, 1d)',
        'limit': 'Maximum number of results to return (default: 100, max: 1000)',
        'offset': 'Number of results to skip for pagination (default: 0)',
        'time_window': 'Time window for alert correlation in seconds (60-86400)',
        'type': 'Filter correlations by type (temporal, spatial, similarity, dependency)',
        'api_key': 'API key for authentication (if required)'
    }
    
    return create_response(True, {
        'endpoints': endpoints,
        'query_parameters': query_params,
        'rate_limits': rate_limits,
        'authentication_required': API_KEY is not None,
        'prometheus_url': PROMETHEUS_URL
    })

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NagProm REST API Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--prometheus-url', default=PROMETHEUS_URL, help='Prometheus URL')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Update configuration
    if args.prometheus_url:
        PROMETHEUS_URL = args.prometheus_url
        prometheus = PrometheusClient(PROMETHEUS_URL)
    
    if args.api_key:
        API_KEY = args.api_key
    
    logger.info(f"Starting NagProm API server on {args.host}:{args.port}")
    logger.info(f"Prometheus URL: {PROMETHEUS_URL}")
    logger.info(f"API Key required: {API_KEY is not None}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
