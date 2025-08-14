#!/usr/bin/env python3
"""
NagProm Custom Metrics Engine

Extensible system for defining, collecting, and processing custom metrics.
Supports dynamic metric registration, custom collection methods, and 
complex metric calculations.

Features:
- Dynamic metric definition and registration
- Custom collection functions
- Metric aggregation and transformation
- Time-series data management
- Metric validation and sanitization
- Performance optimization
- Plugin-based metric sources
- Advanced metric types (histograms, gauges, counters, summaries)
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import json
import uuid
import re
import statistics
import numpy as np
from abc import ABC, abstractmethod
import importlib
import inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of custom metrics"""
    GAUGE = "gauge"              # Current value (CPU usage, memory)
    COUNTER = "counter"          # Monotonically increasing (requests, errors)
    HISTOGRAM = "histogram"      # Distribution of values
    SUMMARY = "summary"          # Percentiles and count
    RATE = "rate"               # Rate of change over time
    RATIO = "ratio"             # Ratio between two metrics
    COMPOSITE = "composite"      # Computed from multiple metrics
    BOOLEAN = "boolean"         # True/false metrics
    CUSTOM = "custom"           # User-defined calculation


class MetricStatus(Enum):
    """Status of metric collection"""
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    PENDING = "pending"


class AggregationMethod(Enum):
    """Methods for aggregating metric values"""
    SUM = "sum"
    AVERAGE = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"
    MEDIAN = "median"
    STDDEV = "stddev"
    RATE = "rate"
    FIRST = "first"
    LAST = "last"


@dataclass
class MetricValue:
    """Single metric measurement"""
    timestamp: datetime
    value: Union[float, int, bool, str]
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'labels': self.labels,
            'metadata': self.metadata
        }


@dataclass
class MetricDefinition:
    """Definition of a custom metric"""
    id: str
    name: str
    description: str
    metric_type: MetricType
    unit: str = ""
    labels: List[str] = field(default_factory=list)
    collection_interval: int = 60  # seconds
    retention_period: int = 86400  # seconds (24 hours)
    aggregation_methods: List[AggregationMethod] = field(default_factory=lambda: [AggregationMethod.AVERAGE])
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    collection_function: Optional[str] = None  # Function name or code
    dependencies: List[str] = field(default_factory=list)  # Metric IDs this depends on
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'metric_type': self.metric_type.value,
            'unit': self.unit,
            'labels': self.labels,
            'collection_interval': self.collection_interval,
            'retention_period': self.retention_period,
            'aggregation_methods': [m.value for m in self.aggregation_methods],
            'validation_rules': self.validation_rules,
            'collection_function': self.collection_function,
            'dependencies': self.dependencies,
            'tags': self.tags,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class MetricCollector(ABC):
    """Abstract base class for metric collectors"""
    
    @abstractmethod
    async def collect(self, metric_def: MetricDefinition, context: Dict[str, Any]) -> List[MetricValue]:
        """Collect metric values"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate collector configuration"""
        pass


class CustomMetricsEngine:
    """Main engine for custom metrics management"""
    
    def __init__(self, storage_backend=None):
        self.metrics: Dict[str, MetricDefinition] = {}
        self.collectors: Dict[str, MetricCollector] = {}
        self.metric_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.collection_tasks: Dict[str, asyncio.Task] = {}
        self.storage_backend = storage_backend
        
        # Built-in collectors
        self._register_builtin_collectors()
        
        # Metric functions registry
        self.metric_functions: Dict[str, Callable] = {}
        self._register_builtin_functions()
        
        # Statistics and monitoring
        self.collection_stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'average_collection_time': 0
        }
        
        # Validation patterns
        self.validation_patterns = {
            'percentage': r'^([0-9]|[1-9][0-9]|100)(\.[0-9]+)?$',
            'ip_address': r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
            'hostname': r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        }
    
    def register_metric(self, metric_def: MetricDefinition) -> bool:
        """Register a new custom metric"""
        try:
            # Validate metric definition
            if not self._validate_metric_definition(metric_def):
                return False
            
            # Check dependencies
            if not self._validate_dependencies(metric_def):
                logger.error(f"Invalid dependencies for metric {metric_def.id}")
                return False
            
            # Store metric definition
            self.metrics[metric_def.id] = metric_def
            
            # Start collection if enabled
            if metric_def.enabled:
                self._start_metric_collection(metric_def)
            
            logger.info(f"Registered custom metric: {metric_def.name} ({metric_def.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register metric {metric_def.id}: {e}")
            return False
    
    def unregister_metric(self, metric_id: str) -> bool:
        """Unregister a custom metric"""
        try:
            if metric_id not in self.metrics:
                return False
            
            # Stop collection task
            if metric_id in self.collection_tasks:
                self.collection_tasks[metric_id].cancel()
                del self.collection_tasks[metric_id]
            
            # Remove metric data
            if metric_id in self.metric_data:
                del self.metric_data[metric_id]
            
            # Remove metric definition
            del self.metrics[metric_id]
            
            logger.info(f"Unregistered metric: {metric_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister metric {metric_id}: {e}")
            return False
    
    def update_metric(self, metric_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing metric definition"""
        try:
            if metric_id not in self.metrics:
                return False
            
            metric_def = self.metrics[metric_id]
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(metric_def, key):
                    setattr(metric_def, key, value)
            
            metric_def.updated_at = datetime.now()
            
            # Restart collection if interval changed
            if 'collection_interval' in updates or 'enabled' in updates:
                if metric_id in self.collection_tasks:
                    self.collection_tasks[metric_id].cancel()
                
                if metric_def.enabled:
                    self._start_metric_collection(metric_def)
            
            logger.info(f"Updated metric: {metric_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metric {metric_id}: {e}")
            return False
    
    def get_metric(self, metric_id: str) -> Optional[MetricDefinition]:
        """Get metric definition"""
        return self.metrics.get(metric_id)
    
    def list_metrics(self, tags: Optional[List[str]] = None, 
                    metric_type: Optional[MetricType] = None) -> List[MetricDefinition]:
        """List metrics with optional filtering"""
        result = list(self.metrics.values())
        
        if tags:
            result = [m for m in result if any(tag in m.tags for tag in tags)]
        
        if metric_type:
            result = [m for m in result if m.metric_type == metric_type]
        
        return result
    
    def register_collector(self, name: str, collector: MetricCollector):
        """Register a custom metric collector"""
        self.collectors[name] = collector
        logger.info(f"Registered collector: {name}")
    
    def register_function(self, name: str, func: Callable):
        """Register a custom metric function"""
        self.metric_functions[name] = func
        logger.info(f"Registered metric function: {name}")
    
    async def collect_metric(self, metric_id: str, context: Dict[str, Any] = None) -> List[MetricValue]:
        """Manually trigger metric collection"""
        if metric_id not in self.metrics:
            raise ValueError(f"Metric {metric_id} not found")
        
        metric_def = self.metrics[metric_id]
        context = context or {}
        
        return await self._collect_metric_values(metric_def, context)
    
    def get_metric_data(self, metric_id: str, 
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       aggregation: Optional[AggregationMethod] = None) -> List[Dict[str, Any]]:
        """Get metric data with optional time range and aggregation"""
        if metric_id not in self.metric_data:
            return []
        
        data = list(self.metric_data[metric_id])
        
        # Filter by time range
        if start_time:
            data = [d for d in data if d.timestamp >= start_time]
        if end_time:
            data = [d for d in data if d.timestamp <= end_time]
        
        # Apply aggregation if requested
        if aggregation and data:
            data = self._aggregate_metric_data(data, aggregation)
        
        return [d.to_dict() if hasattr(d, 'to_dict') else d for d in data]
    
    def calculate_metric_statistics(self, metric_id: str, 
                                  time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Calculate statistics for a metric"""
        end_time = datetime.now()
        start_time = end_time - time_window
        
        data = self.get_metric_data(metric_id, start_time, end_time)
        
        if not data:
            return {'error': 'No data available'}
        
        values = []
        for point in data:
            value = point.get('value') if isinstance(point, dict) else point.value
            if isinstance(value, (int, float)):
                values.append(value)
        
        if not values:
            return {'error': 'No numeric values found'}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
            'p95': np.percentile(values, 95),
            'p99': np.percentile(values, 99),
            'sum': sum(values),
            'time_window': time_window.total_seconds(),
            'rate': len(values) / time_window.total_seconds() if time_window.total_seconds() > 0 else 0
        }
    
    # Private methods
    
    def _validate_metric_definition(self, metric_def: MetricDefinition) -> bool:
        """Validate metric definition"""
        # Check required fields
        if not metric_def.id or not metric_def.name:
            logger.error("Metric ID and name are required")
            return False
        
        # Check ID format
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_.-]*$', metric_def.id):
            logger.error(f"Invalid metric ID format: {metric_def.id}")
            return False
        
        # Check collection interval
        if metric_def.collection_interval <= 0:
            logger.error("Collection interval must be positive")
            return False
        
        # Validate collection function if provided
        if metric_def.collection_function:
            if not self._validate_collection_function(metric_def.collection_function):
                return False
        
        return True
    
    def _validate_dependencies(self, metric_def: MetricDefinition) -> bool:
        """Validate metric dependencies"""
        for dep_id in metric_def.dependencies:
            if dep_id not in self.metrics:
                logger.warning(f"Dependency {dep_id} not found for metric {metric_def.id}")
                # Don't fail validation - dependency might be registered later
        
        # Check for circular dependencies
        if self._has_circular_dependency(metric_def.id, metric_def.dependencies):
            logger.error(f"Circular dependency detected for metric {metric_def.id}")
            return False
        
        return True
    
    def _has_circular_dependency(self, metric_id: str, dependencies: List[str], 
                                visited: Optional[set] = None) -> bool:
        """Check for circular dependencies"""
        if visited is None:
            visited = set()
        
        if metric_id in visited:
            return True
        
        visited.add(metric_id)
        
        for dep_id in dependencies:
            if dep_id in self.metrics:
                dep_metric = self.metrics[dep_id]
                if self._has_circular_dependency(dep_id, dep_metric.dependencies, visited.copy()):
                    return True
        
        return False
    
    def _validate_collection_function(self, function_code: str) -> bool:
        """Validate custom collection function"""
        try:
            # Check if it's a registered function name
            if function_code in self.metric_functions:
                return True
            
            # Try to compile as Python code
            compile(function_code, '<metric_function>', 'eval')
            return True
            
        except SyntaxError as e:
            logger.error(f"Invalid collection function syntax: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating collection function: {e}")
            return False
    
    def _start_metric_collection(self, metric_def: MetricDefinition):
        """Start background collection task for a metric"""
        if metric_def.id in self.collection_tasks:
            self.collection_tasks[metric_def.id].cancel()
        
        task = asyncio.create_task(self._collection_loop(metric_def))
        self.collection_tasks[metric_def.id] = task
    
    async def _collection_loop(self, metric_def: MetricDefinition):
        """Background collection loop for a metric"""
        logger.info(f"Started collection for metric: {metric_def.id}")
        
        while True:
            try:
                start_time = time.time()
                
                # Collect metric values
                values = await self._collect_metric_values(metric_def)
                
                # Store values
                for value in values:
                    self.metric_data[metric_def.id].append(value)
                
                # Update statistics
                collection_time = time.time() - start_time
                self.collection_stats['total_collections'] += 1
                self.collection_stats['successful_collections'] += 1
                self.collection_stats['average_collection_time'] = (
                    (self.collection_stats['average_collection_time'] * 
                     (self.collection_stats['successful_collections'] - 1) + collection_time) /
                    self.collection_stats['successful_collections']
                )
                
                # Clean up old data
                self._cleanup_metric_data(metric_def)
                
                # Store to backend if configured
                if self.storage_backend:
                    await self.storage_backend.store_metric_values(metric_def.id, values)
                
                logger.debug(f"Collected {len(values)} values for metric {metric_def.id}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.collection_stats['failed_collections'] += 1
                logger.error(f"Collection failed for metric {metric_def.id}: {e}")
            
            # Wait for next collection
            await asyncio.sleep(metric_def.collection_interval)
        
        logger.info(f"Stopped collection for metric: {metric_def.id}")
    
    async def _collect_metric_values(self, metric_def: MetricDefinition, 
                                   context: Dict[str, Any] = None) -> List[MetricValue]:
        """Collect values for a specific metric"""
        context = context or {}
        
        try:
            if metric_def.collection_function:
                # Use custom collection function
                return await self._execute_collection_function(metric_def, context)
            else:
                # Use default collection based on metric type
                return await self._default_collection(metric_def, context)
                
        except Exception as e:
            logger.error(f"Failed to collect metric {metric_def.id}: {e}")
            return []
    
    async def _execute_collection_function(self, metric_def: MetricDefinition, 
                                         context: Dict[str, Any]) -> List[MetricValue]:
        """Execute custom collection function"""
        function_code = metric_def.collection_function
        
        # Check if it's a registered function
        if function_code in self.metric_functions:
            func = self.metric_functions[function_code]
            
            # Prepare function arguments
            sig = inspect.signature(func)
            kwargs = {}
            
            if 'metric_def' in sig.parameters:
                kwargs['metric_def'] = metric_def
            if 'context' in sig.parameters:
                kwargs['context'] = context
            if 'engine' in sig.parameters:
                kwargs['engine'] = self
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
            
            # Convert result to MetricValue objects
            if isinstance(result, list):
                return [self._ensure_metric_value(v, metric_def) for v in result]
            else:
                return [self._ensure_metric_value(result, metric_def)]
        
        else:
            # Execute as Python code
            namespace = {
                'metric_def': metric_def,
                'context': context,
                'engine': self,
                'datetime': datetime,
                'time': time
            }
            
            result = eval(function_code, namespace)
            
            if isinstance(result, list):
                return [self._ensure_metric_value(v, metric_def) for v in result]
            else:
                return [self._ensure_metric_value(result, metric_def)]
    
    async def _default_collection(self, metric_def: MetricDefinition, 
                                context: Dict[str, Any]) -> List[MetricValue]:
        """Default collection implementation based on metric type"""
        now = datetime.now()
        
        if metric_def.metric_type == MetricType.GAUGE:
            # For gauges, return a random value (placeholder)
            value = MetricValue(
                timestamp=now,
                value=np.random.normal(50, 10),  # Random normal distribution
                labels={'type': 'gauge'}
            )
            return [value]
        
        elif metric_def.metric_type == MetricType.COUNTER:
            # For counters, increment from previous value
            previous_data = list(self.metric_data[metric_def.id])
            previous_value = previous_data[-1].value if previous_data else 0
            
            value = MetricValue(
                timestamp=now,
                value=previous_value + np.random.poisson(5),  # Random increment
                labels={'type': 'counter'}
            )
            return [value]
        
        elif metric_def.metric_type == MetricType.COMPOSITE:
            # For composite metrics, calculate from dependencies
            return await self._calculate_composite_metric(metric_def, context)
        
        else:
            # Default implementation
            value = MetricValue(
                timestamp=now,
                value=np.random.random() * 100,
                labels={'type': metric_def.metric_type.value}
            )
            return [value]
    
    async def _calculate_composite_metric(self, metric_def: MetricDefinition, 
                                        context: Dict[str, Any]) -> List[MetricValue]:
        """Calculate composite metric from dependencies"""
        dependency_values = {}
        
        # Get latest values from dependencies
        for dep_id in metric_def.dependencies:
            if dep_id in self.metric_data:
                dep_data = list(self.metric_data[dep_id])
                if dep_data:
                    dependency_values[dep_id] = dep_data[-1].value
        
        if not dependency_values:
            return []
        
        # Calculate composite value (example: average of dependencies)
        composite_value = sum(dependency_values.values()) / len(dependency_values)
        
        return [MetricValue(
            timestamp=datetime.now(),
            value=composite_value,
            labels={'type': 'composite', 'dependencies': ','.join(metric_def.dependencies)},
            metadata={'dependency_values': dependency_values}
        )]
    
    def _ensure_metric_value(self, value: Any, metric_def: MetricDefinition) -> MetricValue:
        """Convert various value types to MetricValue"""
        if isinstance(value, MetricValue):
            return value
        elif isinstance(value, (int, float, bool, str)):
            return MetricValue(
                timestamp=datetime.now(),
                value=value,
                labels={'metric_id': metric_def.id}
            )
        elif isinstance(value, dict):
            return MetricValue(
                timestamp=value.get('timestamp', datetime.now()),
                value=value.get('value', 0),
                labels=value.get('labels', {}),
                metadata=value.get('metadata', {})
            )
        else:
            return MetricValue(
                timestamp=datetime.now(),
                value=str(value),
                labels={'metric_id': metric_def.id}
            )
    
    def _cleanup_metric_data(self, metric_def: MetricDefinition):
        """Clean up old metric data based on retention period"""
        if metric_def.id not in self.metric_data:
            return
        
        cutoff_time = datetime.now() - timedelta(seconds=metric_def.retention_period)
        
        # Remove old data points
        metric_data = self.metric_data[metric_def.id]
        while metric_data and metric_data[0].timestamp < cutoff_time:
            metric_data.popleft()
    
    def _aggregate_metric_data(self, data: List[MetricValue], 
                              aggregation: AggregationMethod) -> List[Dict[str, Any]]:
        """Aggregate metric data using specified method"""
        if not data:
            return []
        
        numeric_values = []
        for point in data:
            value = point.value if hasattr(point, 'value') else point
            if isinstance(value, (int, float)):
                numeric_values.append(value)
        
        if not numeric_values:
            return [{'error': 'No numeric values to aggregate'}]
        
        timestamp = datetime.now()
        
        if aggregation == AggregationMethod.SUM:
            result = sum(numeric_values)
        elif aggregation == AggregationMethod.AVERAGE:
            result = statistics.mean(numeric_values)
        elif aggregation == AggregationMethod.MIN:
            result = min(numeric_values)
        elif aggregation == AggregationMethod.MAX:
            result = max(numeric_values)
        elif aggregation == AggregationMethod.COUNT:
            result = len(numeric_values)
        elif aggregation == AggregationMethod.MEDIAN:
            result = statistics.median(numeric_values)
        elif aggregation == AggregationMethod.PERCENTILE_95:
            result = np.percentile(numeric_values, 95)
        elif aggregation == AggregationMethod.PERCENTILE_99:
            result = np.percentile(numeric_values, 99)
        elif aggregation == AggregationMethod.STDDEV:
            result = statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
        elif aggregation == AggregationMethod.FIRST:
            result = numeric_values[0]
        elif aggregation == AggregationMethod.LAST:
            result = numeric_values[-1]
        else:
            result = statistics.mean(numeric_values)  # Default to average
        
        return [{
            'timestamp': timestamp.isoformat(),
            'value': result,
            'aggregation': aggregation.value,
            'sample_count': len(numeric_values)
        }]
    
    def _register_builtin_collectors(self):
        """Register built-in metric collectors"""
        # System metrics collector
        self.register_collector('system', SystemMetricsCollector())
        
        # HTTP metrics collector
        self.register_collector('http', HTTPMetricsCollector())
        
        # Database metrics collector
        self.register_collector('database', DatabaseMetricsCollector())
    
    def _register_builtin_functions(self):
        """Register built-in metric functions"""
        
        @self.register_function('cpu_usage_percentage')
        async def cpu_usage_percentage(context=None):
            """Get CPU usage percentage"""
            import psutil
            return psutil.cpu_percent(interval=1)
        
        @self.register_function('memory_usage_percentage')
        async def memory_usage_percentage(context=None):
            """Get memory usage percentage"""
            import psutil
            return psutil.virtual_memory().percent
        
        @self.register_function('disk_usage_percentage')
        async def disk_usage_percentage(context=None):
            """Get disk usage percentage"""
            import psutil
            path = context.get('path', '/') if context else '/'
            return psutil.disk_usage(path).percent
        
        @self.register_function('network_bytes_sent')
        async def network_bytes_sent(context=None):
            """Get network bytes sent"""
            import psutil
            return psutil.net_io_counters().bytes_sent
        
        @self.register_function('process_count')
        async def process_count(context=None):
            """Get number of running processes"""
            import psutil
            return len(psutil.pids())
    
    # Analytics and monitoring
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'registered_metrics': len(self.metrics),
            'active_collections': len(self.collection_tasks),
            'total_data_points': sum(len(data) for data in self.metric_data.values()),
            'collection_stats': self.collection_stats.copy(),
            'registered_collectors': list(self.collectors.keys()),
            'registered_functions': list(self.metric_functions.keys())
        }
    
    def export_metric_definitions(self) -> Dict[str, Any]:
        """Export all metric definitions"""
        return {
            'metrics': {
                metric_id: metric_def.to_dict() 
                for metric_id, metric_def in self.metrics.items()
            },
            'exported_at': datetime.now().isoformat()
        }
    
    def import_metric_definitions(self, definitions: Dict[str, Any]) -> Dict[str, bool]:
        """Import metric definitions"""
        results = {}
        
        for metric_id, metric_data in definitions.get('metrics', {}).items():
            try:
                metric_def = MetricDefinition(
                    id=metric_data['id'],
                    name=metric_data['name'],
                    description=metric_data['description'],
                    metric_type=MetricType(metric_data['metric_type']),
                    unit=metric_data.get('unit', ''),
                    labels=metric_data.get('labels', []),
                    collection_interval=metric_data.get('collection_interval', 60),
                    retention_period=metric_data.get('retention_period', 86400),
                    aggregation_methods=[
                        AggregationMethod(m) for m in metric_data.get('aggregation_methods', ['avg'])
                    ],
                    validation_rules=metric_data.get('validation_rules', {}),
                    collection_function=metric_data.get('collection_function'),
                    dependencies=metric_data.get('dependencies', []),
                    tags=metric_data.get('tags', []),
                    enabled=metric_data.get('enabled', True)
                )
                
                results[metric_id] = self.register_metric(metric_def)
                
            except Exception as e:
                logger.error(f"Failed to import metric {metric_id}: {e}")
                results[metric_id] = False
        
        return results


# Built-in collector implementations

class SystemMetricsCollector(MetricCollector):
    """Collector for system metrics"""
    
    async def collect(self, metric_def: MetricDefinition, context: Dict[str, Any]) -> List[MetricValue]:
        """Collect system metrics"""
        try:
            import psutil
            
            values = []
            now = datetime.now()
            
            if 'cpu' in metric_def.name.lower():
                values.append(MetricValue(
                    timestamp=now,
                    value=psutil.cpu_percent(interval=0.1),
                    labels={'type': 'cpu', 'unit': 'percent'}
                ))
            
            if 'memory' in metric_def.name.lower():
                mem = psutil.virtual_memory()
                values.append(MetricValue(
                    timestamp=now,
                    value=mem.percent,
                    labels={'type': 'memory', 'unit': 'percent'},
                    metadata={'total': mem.total, 'available': mem.available}
                ))
            
            return values
            
        except ImportError:
            logger.warning("psutil not available for system metrics")
            return []
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            return []
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate system metrics configuration"""
        return True  # System metrics don't need special config


class HTTPMetricsCollector(MetricCollector):
    """Collector for HTTP endpoint metrics"""
    
    async def collect(self, metric_def: MetricDefinition, context: Dict[str, Any]) -> List[MetricValue]:
        """Collect HTTP metrics"""
        import aiohttp
        
        url = context.get('url', 'http://localhost')
        timeout = context.get('timeout', 10)
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000  # milliseconds
                    
                    return [
                        MetricValue(
                            timestamp=datetime.now(),
                            value=response_time,
                            labels={
                                'url': url,
                                'status_code': str(response.status),
                                'method': 'GET'
                            },
                            metadata={
                                'response_size': len(await response.text()),
                                'headers': dict(response.headers)
                            }
                        )
                    ]
        
        except Exception as e:
            logger.error(f"HTTP metrics collection failed for {url}: {e}")
            return []
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate HTTP metrics configuration"""
        return 'url' in config


class DatabaseMetricsCollector(MetricCollector):
    """Collector for database metrics"""
    
    async def collect(self, metric_def: MetricDefinition, context: Dict[str, Any]) -> List[MetricValue]:
        """Collect database metrics"""
        # Placeholder implementation
        # In practice, this would connect to various databases
        return [
            MetricValue(
                timestamp=datetime.now(),
                value=np.random.uniform(0.1, 2.0),  # Query time in seconds
                labels={'type': 'query_time', 'database': context.get('database', 'default')}
            )
        ]
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate database metrics configuration"""
        return True


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize metrics engine
        engine = CustomMetricsEngine()
        
        # Define a custom metric
        cpu_metric = MetricDefinition(
            id="custom_cpu_usage",
            name="Custom CPU Usage",
            description="CPU usage percentage with custom collection",
            metric_type=MetricType.GAUGE,
            unit="percent",
            collection_interval=10,
            aggregation_methods=[AggregationMethod.AVERAGE, AggregationMethod.MAX],
            collection_function="cpu_usage_percentage",
            tags=["system", "performance"]
        )
        
        # Register the metric
        engine.register_metric(cpu_metric)
        
        # Define a composite metric
        composite_metric = MetricDefinition(
            id="system_health_score",
            name="System Health Score",
            description="Composite score based on CPU and memory usage",
            metric_type=MetricType.COMPOSITE,
            dependencies=["custom_cpu_usage"],
            collection_interval=30,
            collection_function="lambda metric_def, context, engine: 100 - ((engine.get_metric_data('custom_cpu_usage')[-1]['value'] if engine.get_metric_data('custom_cpu_usage') else 0) * 0.5)",
            tags=["system", "health"]
        )
        
        engine.register_metric(composite_metric)
        
        # Start collection
        await asyncio.sleep(5)
        
        # Get statistics
        print("Engine Stats:", json.dumps(engine.get_engine_stats(), indent=2))
        
        # Get metric data
        cpu_data = engine.get_metric_data("custom_cpu_usage")
        print(f"CPU Data Points: {len(cpu_data)}")
        
        # Calculate statistics
        stats = engine.calculate_metric_statistics("custom_cpu_usage")
        print("CPU Statistics:", json.dumps(stats, indent=2, default=str))
    
    asyncio.run(main())
