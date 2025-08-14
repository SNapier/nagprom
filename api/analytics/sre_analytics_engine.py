#!/usr/bin/env python3
"""
NagProm SRE Analytics Engine

Advanced analytics engine for SRE/DevOps teams providing:
- Service reliability metrics (SLI/SLO)
- Performance trend analysis
- Alert correlation and pattern recognition
- Capacity planning insights
- Error budget tracking
- Incident impact analysis
- MTTR/MTBF calculations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import statistics
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional alert correlation integration
ALERT_CORRELATION_AVAILABLE = False
class SLIType(Enum):
    """Service Level Indicator types"""
    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    SATURATION = "saturation"


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    UNKNOWN = "unknown"


@dataclass
class SLOTarget:
    """Service Level Objective target definition"""
    name: str
    sli_type: SLIType
    target_percentage: float  # e.g., 99.9
    measurement_window: timedelta  # e.g., 30 days
    error_budget_policy: str = "burn_rate"
    
    @property
    def error_budget_percentage(self) -> float:
        return 100.0 - self.target_percentage


@dataclass
class SLIMetric:
    """Service Level Indicator measurement"""
    timestamp: datetime
    service: str
    sli_type: SLIType
    value: float
    success_count: int = 0
    total_count: int = 0
    metadata: Dict[str, Any] = None


@dataclass
class AlertEvent:
    """Alert event data structure"""
    timestamp: datetime
    service: str
    host: str
    severity: AlertSeverity
    status: str  # firing, resolved
    description: str
    duration: Optional[timedelta] = None
    metadata: Dict[str, Any] = None


@dataclass
class IncidentImpact:
    """Incident impact analysis"""
    incident_id: str
    start_time: datetime
    end_time: Optional[datetime]
    affected_services: List[str]
    severity: AlertSeverity
    users_affected: int
    revenue_impact: float
    mttr: Optional[timedelta] = None


class SREAnalyticsEngine:
    """Main analytics engine for SRE metrics"""
    
    def __init__(self, prometheus_client=None):
        self.prometheus_client = prometheus_client
        self.slo_targets: Dict[str, List[SLOTarget]] = {}
        self.sli_data: deque = deque(maxlen=10000)  # Ring buffer for SLI data
        self.alert_history: deque = deque(maxlen=5000)  # Alert event history
        self.incident_data: List[IncidentImpact] = []
        
        # Analytics caches
        self._reliability_cache: Dict[str, Any] = {}
        self._cache_timestamp = None
        self._cache_ttl = timedelta(minutes=5)
        
        # Trend analysis data
        self.trend_window = timedelta(days=7)
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        
        # Optional alert correlation integration
        self.alert_correlation_engine = None
        if ALERT_CORRELATION_AVAILABLE:
            try:
                from alert_correlation import AlertCorrelationEngine
                self.alert_correlation_engine = AlertCorrelationEngine()
                logger.info("Alert correlation engine integrated with SRE analytics")
            except Exception as e:
                logger.warning(f"Failed to initialize alert correlation engine: {e}")
                self.alert_correlation_engine = None
        
    def register_slo(self, service: str, slo_target: SLOTarget):
        """Register an SLO target for a service"""
        if service not in self.slo_targets:
            self.slo_targets[service] = []
        
        self.slo_targets[service].append(slo_target)
        logger.info(f"Registered SLO {slo_target.name} for service {service}")
    
    def record_sli_metric(self, metric: SLIMetric):
        """Record a Service Level Indicator measurement"""
        self.sli_data.append(metric)
        
        # Update performance baselines
        self._update_performance_baseline(metric)
    
    def record_alert_event(self, alert: AlertEvent):
        """Record an alert event"""
        self.alert_history.append(alert)
        
        # Calculate duration for resolved alerts
        if alert.status == "resolved":
            self._calculate_alert_duration(alert)
    
    def calculate_service_reliability(self, service: str, time_window: timedelta = None) -> Dict[str, Any]:
        """Calculate comprehensive service reliability metrics"""
        if time_window is None:
            time_window = timedelta(days=30)
        
        # Check cache
        cache_key = f"{service}_{time_window.total_seconds()}"
        if self._is_cache_valid() and cache_key in self._reliability_cache:
            return self._reliability_cache[cache_key]
        
        end_time = datetime.now()
        start_time = end_time - time_window
        
        # Get SLI data for the service in the time window
        service_slis = [
            sli for sli in self.sli_data
            if sli.service == service and start_time <= sli.timestamp <= end_time
        ]
        
        if not service_slis:
            return {"error": "No SLI data available for service"}
        
        # Calculate reliability metrics
        reliability_metrics = {
            "service": service,
            "time_window": time_window.total_seconds(),
            "measurement_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "sli_metrics": {},
            "slo_compliance": {},
            "error_budgets": {},
            "trend_analysis": {},
            "incidents": self._get_service_incidents(service, start_time, end_time)
        }
        
        # Group SLIs by type
        slis_by_type = defaultdict(list)
        for sli in service_slis:
            slis_by_type[sli.sli_type].append(sli)
        
        # Calculate metrics for each SLI type
        for sli_type, slis in slis_by_type.items():
            reliability_metrics["sli_metrics"][sli_type.value] = self._calculate_sli_metrics(slis)
        
        # Calculate SLO compliance
        if service in self.slo_targets:
            for slo_target in self.slo_targets[service]:
                compliance = self._calculate_slo_compliance(service, slo_target, start_time, end_time)
                reliability_metrics["slo_compliance"][slo_target.name] = compliance
                
                # Calculate error budget
                error_budget = self._calculate_error_budget(service, slo_target, start_time, end_time)
                reliability_metrics["error_budgets"][slo_target.name] = error_budget
        
        # Add trend analysis
        reliability_metrics["trend_analysis"] = self._analyze_service_trends(service, time_window)
        
        # Cache results
        self._reliability_cache[cache_key] = reliability_metrics
        self._cache_timestamp = datetime.now()
        
        return reliability_metrics
    
    def get_alert_correlation_insights(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Get alert correlation insights if correlation engine is available"""
        if not self.alert_correlation_engine:
            return {
                "available": False,
                "message": "Alert correlation engine not available"
            }
        
        try:
            if time_window is None:
                time_window = timedelta(minutes=15)
            
            # Get correlation metrics
            metrics = self.alert_correlation_engine.get_correlation_metrics()
            
            # Get recent correlations
            import asyncio
            clusters = asyncio.run(self.alert_correlation_engine.correlate_alerts(time_window))
            
            return {
                "available": True,
                "metrics": metrics,
                "recent_correlations": len(clusters),
                "time_window": time_window.total_seconds(),
                "engine_status": "active"
            }
        except Exception as e:
            logger.error(f"Failed to get correlation insights: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def analyze_alert_patterns(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Analyze alert patterns and correlations"""
        if time_window is None:
            time_window = timedelta(days=7)
        
        end_time = datetime.now()
        start_time = end_time - time_window
        
        # Filter alerts in time window
        recent_alerts = [
            alert for alert in self.alert_history
            if start_time <= alert.timestamp <= end_time
        ]
        
        if not recent_alerts:
            return {"error": "No alerts in specified time window"}
        
        analysis = {
            "time_window": time_window.total_seconds(),
            "total_alerts": len(recent_alerts),
            "alert_distribution": self._analyze_alert_distribution(recent_alerts),
            "service_analysis": self._analyze_service_alerts(recent_alerts),
            "temporal_patterns": self._analyze_temporal_patterns(recent_alerts),
            "correlation_analysis": self._analyze_alert_correlations(recent_alerts),
            "mttr_analysis": self._calculate_mttr_metrics(recent_alerts),
            "alert_frequency": self._calculate_alert_frequencies(recent_alerts),
            "noise_analysis": self._analyze_alert_noise(recent_alerts)
        }
        
        return analysis
    
    def generate_capacity_insights(self, service: str = None) -> Dict[str, Any]:
        """Generate capacity planning insights"""
        insights = {
            "timestamp": datetime.now().isoformat(),
            "analysis_period": self.trend_window.total_seconds(),
            "services": {}
        }
        
        # Analyze specific service or all services
        services_to_analyze = [service] if service else self._get_monitored_services()
        
        for svc in services_to_analyze:
            service_insights = self._analyze_service_capacity(svc)
            if service_insights:
                insights["services"][svc] = service_insights
        
        # Global capacity insights
        insights["global_insights"] = self._analyze_global_capacity_trends()
        
        return insights
    
    def calculate_business_impact(self, incident_id: str = None) -> Dict[str, Any]:
        """Calculate business impact of incidents"""
        if incident_id:
            # Analyze specific incident
            incident = next((inc for inc in self.incident_data if inc.incident_id == incident_id), None)
            if not incident:
                return {"error": f"Incident {incident_id} not found"}
            
            return self._calculate_incident_impact(incident)
        else:
            # Analyze all recent incidents
            return self._calculate_aggregate_impact()
    
    def get_sre_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive SRE dashboard data"""
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "overview": self._get_sre_overview(),
            "service_health": self._get_service_health_summary(),
            "slo_status": self._get_slo_status_summary(),
            "error_budgets": self._get_error_budget_summary(),
            "alert_summary": self._get_alert_summary(),
            "capacity_status": self._get_capacity_status(),
            "incident_metrics": self._get_incident_metrics(),
            "recommendations": self._generate_sre_recommendations()
        }
        
        return dashboard_data
    
    # Private helper methods
    
    def _calculate_sli_metrics(self, slis: List[SLIMetric]) -> Dict[str, Any]:
        """Calculate metrics for a list of SLI measurements"""
        if not slis:
            return {}
        
        values = [sli.value for sli in slis]
        success_counts = [sli.success_count for sli in slis if sli.success_count > 0]
        total_counts = [sli.total_count for sli in slis if sli.total_count > 0]
        
        metrics = {
            "count": len(slis),
            "latest_value": slis[-1].value,
            "average": statistics.mean(values),
            "median": statistics.median(values),
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99),
            "min": min(values),
            "max": max(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0
        }
        
        if success_counts and total_counts:
            total_success = sum(success_counts)
            total_requests = sum(total_counts)
            metrics["success_rate"] = (total_success / total_requests) * 100 if total_requests > 0 else 0
        
        return metrics
    
    def _calculate_slo_compliance(self, service: str, slo_target: SLOTarget, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Calculate SLO compliance for a service"""
        # Get relevant SLI data
        relevant_slis = [
            sli for sli in self.sli_data
            if (sli.service == service and 
                sli.sli_type == slo_target.sli_type and
                start_time <= sli.timestamp <= end_time)
        ]
        
        if not relevant_slis:
            return {"compliance": 0, "status": "no_data"}
        
        # Calculate compliance based on SLI type
        if slo_target.sli_type == SLIType.AVAILABILITY:
            total_success = sum(sli.success_count for sli in relevant_slis if sli.success_count > 0)
            total_requests = sum(sli.total_count for sli in relevant_slis if sli.total_count > 0)
            
            if total_requests == 0:
                return {"compliance": 0, "status": "no_data"}
            
            actual_availability = (total_success / total_requests) * 100
            compliance = actual_availability >= slo_target.target_percentage
            
            return {
                "compliance": compliance,
                "actual_percentage": actual_availability,
                "target_percentage": slo_target.target_percentage,
                "status": "compliant" if compliance else "breach",
                "total_requests": total_requests,
                "successful_requests": total_success
            }
        
        # Add other SLI type calculations here
        return {"compliance": False, "status": "unsupported_sli_type"}
    
    def _calculate_error_budget(self, service: str, slo_target: SLOTarget, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Calculate error budget consumption"""
        compliance_data = self._calculate_slo_compliance(service, slo_target, start_time, end_time)
        
        if compliance_data.get("status") in ["no_data", "unsupported_sli_type"]:
            return {"error": "Cannot calculate error budget", "details": compliance_data}
        
        # Calculate error budget
        actual_percentage = compliance_data.get("actual_percentage", 0)
        target_percentage = slo_target.target_percentage
        error_budget_percentage = slo_target.error_budget_percentage
        
        if actual_percentage >= target_percentage:
            # SLO is being met
            budget_consumed = 0
            budget_remaining = 100
        else:
            # SLO is being breached
            actual_error_rate = 100 - actual_percentage
            budget_consumed = (actual_error_rate / error_budget_percentage) * 100
            budget_remaining = max(0, 100 - budget_consumed)
        
        # Calculate burn rate
        measurement_days = (end_time - start_time).days
        monthly_budget = error_budget_percentage
        daily_budget = monthly_budget / 30  # Assuming 30-day budget
        
        if measurement_days > 0:
            actual_daily_burn = (100 - budget_remaining) / measurement_days
            burn_rate = actual_daily_burn / daily_budget if daily_budget > 0 else 0
        else:
            burn_rate = 0
        
        return {
            "error_budget_percentage": error_budget_percentage,
            "budget_consumed_percentage": budget_consumed,
            "budget_remaining_percentage": budget_remaining,
            "burn_rate": burn_rate,
            "status": self._get_budget_status(budget_remaining, burn_rate),
            "projected_exhaustion_days": self._calculate_budget_exhaustion(budget_remaining, burn_rate)
        }
    
    def _analyze_service_trends(self, service: str, time_window: timedelta) -> Dict[str, Any]:
        """Analyze service performance trends"""
        end_time = datetime.now()
        start_time = end_time - time_window
        
        # Get service data
        service_data = [
            sli for sli in self.sli_data
            if sli.service == service and start_time <= sli.timestamp <= end_time
        ]
        
        if len(service_data) < 2:
            return {"status": "insufficient_data"}
        
        # Group by SLI type and analyze trends
        trends = {}
        for sli_type in SLIType:
            type_data = [sli for sli in service_data if sli.sli_type == sli_type]
            if len(type_data) >= 2:
                trends[sli_type.value] = self._calculate_trend_metrics(type_data)
        
        return trends
    
    def _calculate_trend_metrics(self, data: List[SLIMetric]) -> Dict[str, Any]:
        """Calculate trend metrics for a dataset"""
        # Sort by timestamp
        sorted_data = sorted(data, key=lambda x: x.timestamp)
        values = [item.value for item in sorted_data]
        
        # Calculate linear trend
        if len(values) >= 2:
            x = np.arange(len(values))
            coefficients = np.polyfit(x, values, 1)
            trend_slope = coefficients[0]
            
            # Determine trend direction
            if abs(trend_slope) < 0.01:  # Threshold for "stable"
                trend_direction = "stable"
            elif trend_slope > 0:
                trend_direction = "improving"
            else:
                trend_direction = "degrading"
            
            # Calculate trend strength
            correlation = np.corrcoef(x, values)[0, 1] if len(values) > 1 else 0
            
            return {
                "direction": trend_direction,
                "slope": trend_slope,
                "correlation": correlation,
                "strength": abs(correlation),
                "recent_average": statistics.mean(values[-5:]) if len(values) >= 5 else statistics.mean(values),
                "historical_average": statistics.mean(values),
                "volatility": statistics.stdev(values) if len(values) > 1 else 0
            }
        
        return {"status": "insufficient_data"}
    
    def _analyze_alert_distribution(self, alerts: List[AlertEvent]) -> Dict[str, Any]:
        """Analyze alert distribution by various dimensions"""
        severity_counts = defaultdict(int)
        service_counts = defaultdict(int)
        host_counts = defaultdict(int)
        
        for alert in alerts:
            severity_counts[alert.severity.value] += 1
            service_counts[alert.service] += 1
            host_counts[alert.host] += 1
        
        return {
            "by_severity": dict(severity_counts),
            "by_service": dict(sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_host": dict(sorted(host_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def _get_sre_overview(self) -> Dict[str, Any]:
        """Get high-level SRE overview metrics"""
        total_services = len(self._get_monitored_services())
        active_alerts = len([a for a in self.alert_history if a.status == "firing"])
        
        # Calculate overall health score
        health_scores = []
        for service in self._get_monitored_services():
            service_reliability = self.calculate_service_reliability(service, timedelta(hours=24))
            if "sli_metrics" in service_reliability:
                # Simple health score based on availability
                for sli_type, metrics in service_reliability["sli_metrics"].items():
                    if sli_type == "availability":
                        health_scores.append(metrics.get("success_rate", 0))
        
        overall_health = statistics.mean(health_scores) if health_scores else 0
        
        return {
            "total_services": total_services,
            "healthy_services": len([s for s in health_scores if s >= 95]),
            "active_alerts": active_alerts,
            "overall_health_score": round(overall_health, 2),
            "uptime_percentage": round(overall_health, 3)
        }
    
    def _get_monitored_services(self) -> List[str]:
        """Get list of all monitored services"""
        services = set()
        for sli in self.sli_data:
            services.add(sli.service)
        return list(services)
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self._cache_timestamp is None:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl
    
    def _update_performance_baseline(self, metric: SLIMetric):
        """Update performance baselines for anomaly detection"""
        service = metric.service
        sli_type = metric.sli_type.value
        
        if service not in self.performance_baselines:
            self.performance_baselines[service] = {}
        
        if sli_type not in self.performance_baselines[service]:
            self.performance_baselines[service][sli_type] = {
                "values": deque(maxlen=1000),
                "mean": 0,
                "std": 0,
                "last_updated": datetime.now()
            }
        
        baseline = self.performance_baselines[service][sli_type]
        baseline["values"].append(metric.value)
        
        # Update statistics periodically
        if len(baseline["values"]) >= 10:
            values = list(baseline["values"])
            baseline["mean"] = statistics.mean(values)
            baseline["std"] = statistics.stdev(values) if len(values) > 1 else 0
            baseline["last_updated"] = datetime.now()
    
    def detect_anomalies(self, service: str, threshold_std: float = 2.0) -> List[Dict[str, Any]]:
        """Detect performance anomalies using statistical methods"""
        anomalies = []
        
        if service not in self.performance_baselines:
            return anomalies
        
        recent_time = datetime.now() - timedelta(hours=1)
        recent_slis = [
            sli for sli in self.sli_data
            if sli.service == service and sli.timestamp >= recent_time
        ]
        
        for sli in recent_slis:
            sli_type = sli.sli_type.value
            if sli_type in self.performance_baselines[service]:
                baseline = self.performance_baselines[service][sli_type]
                
                if baseline["std"] > 0:
                    z_score = abs(sli.value - baseline["mean"]) / baseline["std"]
                    
                    if z_score > threshold_std:
                        anomalies.append({
                            "timestamp": sli.timestamp.isoformat(),
                            "service": service,
                            "sli_type": sli_type,
                            "value": sli.value,
                            "expected_range": [
                                baseline["mean"] - threshold_std * baseline["std"],
                                baseline["mean"] + threshold_std * baseline["std"]
                            ],
                            "z_score": z_score,
                            "severity": "high" if z_score > 3.0 else "medium"
                        })
        
        return anomalies
    
    def _get_budget_status(self, budget_remaining: float, burn_rate: float) -> str:
        """Determine error budget status"""
        if budget_remaining <= 10:
            return "critical"
        elif budget_remaining <= 25:
            return "warning"
        elif burn_rate > 2.0:
            return "high_burn_rate"
        else:
            return "healthy"
    
    def _calculate_budget_exhaustion(self, budget_remaining: float, burn_rate: float) -> Optional[float]:
        """Calculate projected days until budget exhaustion"""
        if burn_rate <= 0 or budget_remaining <= 0:
            return None
        
        # Simple linear projection
        days_remaining = budget_remaining / burn_rate
        return max(0, days_remaining)
    
    def _get_service_incidents(self, service: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get incidents for a specific service in time window"""
        incidents = [
            inc for inc in self.incident_data
            if inc.incident_id and service in inc.affected_services and 
            start_time <= inc.start_time <= end_time
        ]
        return [asdict(inc) for inc in incidents]
    
    def _analyze_service_alerts(self, alerts: List[AlertEvent]) -> Dict[str, Any]:
        """Analyze alerts by service"""
        service_analysis = defaultdict(lambda: {
            'total_alerts': 0,
            'by_severity': defaultdict(int),
            'by_host': defaultdict(int),
            'avg_duration': timedelta(0),
            'durations': []
        })
        
        for alert in alerts:
            service = alert.service
            service_analysis[service]['total_alerts'] += 1
            service_analysis[service]['by_severity'][alert.severity.value] += 1
            service_analysis[service]['by_host'][alert.host] += 1
            
            if alert.duration:
                service_analysis[service]['durations'].append(alert.duration)
        
        # Calculate averages
        for service in service_analysis:
            durations = service_analysis[service]['durations']
            if durations:
                avg_seconds = sum(d.total_seconds() for d in durations) / len(durations)
                service_analysis[service]['avg_duration'] = timedelta(seconds=avg_seconds)
            service_analysis[service]['by_severity'] = dict(service_analysis[service]['by_severity'])
            service_analysis[service]['by_host'] = dict(service_analysis[service]['by_host'])
        
        return dict(service_analysis)
    
    def _analyze_temporal_patterns(self, alerts: List[AlertEvent]) -> Dict[str, Any]:
        """Analyze temporal patterns in alerts"""
        if not alerts:
            return {}
        
        # Group by hour of day
        hourly_distribution = defaultdict(int)
        for alert in alerts:
            hour = alert.timestamp.hour
            hourly_distribution[hour] += 1
        
        # Group by day of week
        daily_distribution = defaultdict(int)
        for alert in alerts:
            day = alert.timestamp.strftime('%A')
            daily_distribution[day] += 1
        
        # Find peak alert times
        peak_hour = max(hourly_distribution.items(), key=lambda x: x[1])[0] if hourly_distribution else None
        peak_day = max(daily_distribution.items(), key=lambda x: x[1])[0] if daily_distribution else None
        
        return {
            'hourly_distribution': dict(hourly_distribution),
            'daily_distribution': dict(daily_distribution),
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'total_alerts': len(alerts)
        }
    
    def _analyze_alert_correlations(self, alerts: List[AlertEvent]) -> Dict[str, Any]:
        """Analyze correlations between alerts"""
        if len(alerts) < 2:
            return {}
        
        # Group alerts by time proximity (within 5 minutes)
        correlated_groups = []
        processed = set()
        
        for i, alert1 in enumerate(alerts):
            if i in processed:
                continue
            
            group = [alert1]
            processed.add(i)
            
            for j, alert2 in enumerate(alerts[i+1:], i+1):
                if j in processed:
                    continue
                
                time_diff = abs((alert1.timestamp - alert2.timestamp).total_seconds())
                if time_diff <= 300:  # 5 minutes
                    group.append(alert2)
                    processed.add(j)
            
            if len(group) > 1:
                correlated_groups.append(group)
        
        # Analyze service correlations
        service_correlations = defaultdict(int)
        for group in correlated_groups:
            services = [alert.service for alert in group]
            for i, service1 in enumerate(services):
                for service2 in services[i+1:]:
                    pair = tuple(sorted([service1, service2]))
                    service_correlations[pair] += 1
        
        return {
            'correlated_groups': len(correlated_groups),
            'total_correlated_alerts': sum(len(group) for group in correlated_groups),
            'service_correlations': dict(service_correlations),
            'avg_group_size': sum(len(group) for group in correlated_groups) / len(correlated_groups) if correlated_groups else 0
        }
    
    def _calculate_mttr_metrics(self, alerts: List[AlertEvent]) -> Dict[str, Any]:
        """Calculate MTTR (Mean Time To Recovery) metrics"""
        resolved_alerts = [alert for alert in alerts if alert.status == "resolved" and alert.duration]
        
        if not resolved_alerts:
            return {"mttr": None, "total_resolved": 0}
        
        total_duration = sum(alert.duration.total_seconds() for alert in resolved_alerts)
        avg_mttr_seconds = total_duration / len(resolved_alerts)
        
        # Calculate percentiles
        durations = [alert.duration.total_seconds() for alert in resolved_alerts]
        durations.sort()
        
        p50_idx = int(len(durations) * 0.5)
        p95_idx = int(len(durations) * 0.95)
        p99_idx = int(len(durations) * 0.99)
        
        return {
            "mttr_seconds": avg_mttr_seconds,
            "mttr_minutes": avg_mttr_seconds / 60,
            "mttr_hours": avg_mttr_seconds / 3600,
            "p50_seconds": durations[p50_idx] if p50_idx < len(durations) else None,
            "p95_seconds": durations[p95_idx] if p95_idx < len(durations) else None,
            "p99_seconds": durations[p99_idx] if p99_idx < len(durations) else None,
            "total_resolved": len(resolved_alerts),
            "min_resolution_time": min(durations),
            "max_resolution_time": max(durations)
        }
    
    def _analyze_alert_noise(self, alerts: List[AlertEvent]) -> Dict[str, Any]:
        """Analyze alert noise and identify potential issues"""
        if not alerts:
            return {}
        
        # Group by service and severity
        service_severity_counts = defaultdict(lambda: defaultdict(int))
        for alert in alerts:
            service_severity_counts[alert.service][alert.severity.value] += 1
        
        # Identify noisy services (high alert count)
        service_totals = {service: sum(counts.values()) for service, counts in service_severity_counts.items()}
        avg_alerts_per_service = sum(service_totals.values()) / len(service_totals) if service_totals else 0
        
        noisy_services = [
            service for service, count in service_totals.items()
            if count > avg_alerts_per_service * 2  # 2x average
        ]
        
        # Identify services with mostly low-severity alerts
        low_severity_services = []
        for service, counts in service_severity_counts.items():
            total = sum(counts.values())
            low_severity = counts.get('info', 0) + counts.get('warning', 0)
            if total > 0 and (low_severity / total) > 0.8:  # 80% low severity
                low_severity_services.append(service)
        
        return {
            "total_alerts": len(alerts),
            "unique_services": len(service_totals),
            "avg_alerts_per_service": avg_alerts_per_service,
            "noisy_services": noisy_services,
            "low_severity_services": low_severity_services,
            "service_breakdown": dict(service_totals)
        }
    
    def _analyze_service_capacity(self, service: str) -> Optional[Dict[str, Any]]:
        """Analyze capacity for a specific service"""
        # Get recent SLI data for the service
        end_time = datetime.now()
        start_time = end_time - self.trend_window
        
        service_slis = [
            sli for sli in self.sli_data
            if sli.service == service and start_time <= sli.timestamp <= end_time
        ]
        
        if not service_slis:
            return None
        
        # Analyze saturation metrics
        saturation_slis = [sli for sli in service_slis if sli.sli_type == SLIType.SATURATION]
        
        capacity_insights = {
            "service": service,
            "analysis_period": self.trend_window.total_seconds(),
            "data_points": len(service_slis),
            "current_utilization": None,
            "trend": "stable",
            "recommendations": []
        }
        
        if saturation_slis:
            recent_values = [sli.value for sli in saturation_slis[-10:]]  # Last 10 measurements
            current_utilization = statistics.mean(recent_values) if recent_values else 0
            capacity_insights["current_utilization"] = current_utilization
            
            # Determine trend
            if len(recent_values) >= 5:
                trend_slope = np.polyfit(range(len(recent_values)), recent_values, 1)[0]
                if trend_slope > 0.1:
                    capacity_insights["trend"] = "increasing"
                elif trend_slope < -0.1:
                    capacity_insights["trend"] = "decreasing"
            
            # Generate recommendations
            if current_utilization > 80:
                capacity_insights["recommendations"].append("High utilization detected - consider scaling")
            elif current_utilization > 60:
                capacity_insights["recommendations"].append("Moderate utilization - monitor trends")
            elif current_utilization < 20:
                capacity_insights["recommendations"].append("Low utilization - consider resource optimization")
        
        return capacity_insights
    
    def _analyze_global_capacity_trends(self) -> Dict[str, Any]:
        """Analyze global capacity trends across all services"""
        services = self._get_monitored_services()
        
        if not services:
            return {"status": "no_data"}
        
        total_services = len(services)
        high_utilization_services = 0
        increasing_trend_services = 0
        
        for service in services:
            capacity_data = self._analyze_service_capacity(service)
            if capacity_data:
                if capacity_data.get("current_utilization", 0) > 80:
                    high_utilization_services += 1
                if capacity_data.get("trend") == "increasing":
                    increasing_trend_services += 1
        
        return {
            "total_services": total_services,
            "high_utilization_services": high_utilization_services,
            "increasing_trend_services": increasing_trend_services,
            "capacity_health_score": ((total_services - high_utilization_services) / total_services) * 100 if total_services > 0 else 0,
            "recommendations": [
                "Monitor high-utilization services closely",
                "Plan capacity expansion for trending services",
                "Review resource allocation for underutilized services"
            ] if high_utilization_services > 0 or increasing_trend_services > 0 else ["Capacity utilization is healthy"]
        }
    
    def _calculate_incident_impact(self, incident: IncidentImpact) -> Dict[str, Any]:
        """Calculate detailed impact for a specific incident"""
        return {
            "incident_id": incident.incident_id,
            "duration": (incident.end_time - incident.start_time).total_seconds() if incident.end_time else None,
            "affected_services": incident.affected_services,
            "severity": incident.severity.value,
            "users_affected": incident.users_affected,
            "revenue_impact": incident.revenue_impact,
            "mttr": incident.mttr.total_seconds() if incident.mttr else None,
            "impact_score": self._calculate_impact_score(incident)
        }
    
    def _calculate_aggregate_impact(self) -> Dict[str, Any]:
        """Calculate aggregate impact across all incidents"""
        if not self.incident_data:
            return {"total_incidents": 0, "total_impact": 0}
        
        total_incidents = len(self.incident_data)
        total_users_affected = sum(inc.users_affected for inc in self.incident_data)
        total_revenue_impact = sum(inc.revenue_impact for inc in self.incident_data)
        
        # Calculate average MTTR
        resolved_incidents = [inc for inc in self.incident_data if inc.mttr]
        avg_mttr = statistics.mean([inc.mttr.total_seconds() for inc in resolved_incidents]) if resolved_incidents else 0
        
        return {
            "total_incidents": total_incidents,
            "total_users_affected": total_users_affected,
            "total_revenue_impact": total_revenue_impact,
            "avg_mttr_seconds": avg_mttr,
            "avg_impact_per_incident": total_revenue_impact / total_incidents if total_incidents > 0 else 0
        }
    
    def _get_service_health_summary(self) -> Dict[str, Any]:
        """Get summary of service health across all services"""
        services = self._get_monitored_services()
        
        if not services:
            return {"total_services": 0, "healthy_services": 0}
        
        healthy_services = 0
        service_health_scores = []
        
        for service in services:
            reliability = self.calculate_service_reliability(service, timedelta(hours=24))
            if "sli_metrics" in reliability:
                # Calculate health score based on availability
                for sli_type, metrics in reliability["sli_metrics"].items():
                    if sli_type == "availability":
                        health_score = metrics.get("success_rate", 0)
                        service_health_scores.append(health_score)
                        if health_score >= 95:  # 95% threshold for healthy
                            healthy_services += 1
                        break
        
        overall_health = statistics.mean(service_health_scores) if service_health_scores else 0
        
        return {
            "total_services": len(services),
            "healthy_services": healthy_services,
            "unhealthy_services": len(services) - healthy_services,
            "overall_health_score": round(overall_health, 2),
            "health_distribution": {
                "excellent": len([s for s in service_health_scores if s >= 99]),
                "good": len([s for s in service_health_scores if 95 <= s < 99]),
                "fair": len([s for s in service_health_scores if 90 <= s < 95]),
                "poor": len([s for s in service_health_scores if s < 90])
            }
        }
    
    def _get_slo_status_summary(self) -> Dict[str, Any]:
        """Get summary of SLO status across all services"""
        total_slos = 0
        compliant_slos = 0
        slo_details = []
        
        for service, slo_targets in self.slo_targets.items():
            for slo_target in slo_targets:
                total_slos += 1
                compliance = self._calculate_slo_compliance(service, slo_target, 
                                                          datetime.now() - timedelta(days=30), 
                                                          datetime.now())
                if compliance.get("compliance", False):
                    compliant_slos += 1
                
                slo_details.append({
                    "service": service,
                    "slo_name": slo_target.name,
                    "compliance": compliance.get("compliance", False),
                    "actual_percentage": compliance.get("actual_percentage", 0)
                })
        
        return {
            "total_slos": total_slos,
            "compliant_slos": compliant_slos,
            "non_compliant_slos": total_slos - compliant_slos,
            "compliance_rate": (compliant_slos / total_slos * 100) if total_slos > 0 else 0,
            "slo_details": slo_details
        }
    
    def _get_error_budget_summary(self) -> Dict[str, Any]:
        """Get summary of error budgets across all services"""
        total_budgets = 0
        healthy_budgets = 0
        budget_details = []
        
        for service, slo_targets in self.slo_targets.items():
            for slo_target in slo_targets:
                total_budgets += 1
                error_budget = self._calculate_error_budget(service, slo_target,
                                                          datetime.now() - timedelta(days=30),
                                                          datetime.now())
                
                status = error_budget.get("status", "unknown")
                if status == "healthy":
                    healthy_budgets += 1
                
                budget_details.append({
                    "service": service,
                    "slo_name": slo_target.name,
                    "budget_remaining": error_budget.get("budget_remaining_percentage", 0),
                    "burn_rate": error_budget.get("burn_rate", 0),
                    "status": status
                })
        
        return {
            "total_budgets": total_budgets,
            "healthy_budgets": healthy_budgets,
            "at_risk_budgets": total_budgets - healthy_budgets,
            "avg_budget_remaining": statistics.mean([b["budget_remaining"] for b in budget_details]) if budget_details else 0,
            "budget_details": budget_details
        }
    
    def _get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of recent alerts"""
        recent_time = datetime.now() - timedelta(hours=24)
        recent_alerts = [
            alert for alert in self.alert_history
            if alert.timestamp >= recent_time
        ]
        
        if not recent_alerts:
            return {"total_alerts": 0, "active_alerts": 0}
        
        active_alerts = len([alert for alert in recent_alerts if alert.status == "firing"])
        
        # Group by severity
        severity_counts = defaultdict(int)
        for alert in recent_alerts:
            severity_counts[alert.severity.value] += 1
        
        return {
            "total_alerts": len(recent_alerts),
            "active_alerts": active_alerts,
            "resolved_alerts": len(recent_alerts) - active_alerts,
            "by_severity": dict(severity_counts),
            "alert_trend": "stable"  # Could be enhanced with trend analysis
        }
    
    def _get_capacity_status(self) -> Dict[str, Any]:
        """Get current capacity status"""
        services = self._get_monitored_services()
        
        if not services:
            return {"status": "no_data"}
        
        high_utilization_count = 0
        total_utilization = 0
        utilization_count = 0
        
        for service in services:
            capacity_data = self._analyze_service_capacity(service)
            if capacity_data and capacity_data.get("current_utilization"):
                utilization = capacity_data["current_utilization"]
                total_utilization += utilization
                utilization_count += 1
                if utilization > 80:
                    high_utilization_count += 1
        
        avg_utilization = total_utilization / utilization_count if utilization_count > 0 else 0
        
        return {
            "total_services": len(services),
            "high_utilization_services": high_utilization_count,
            "avg_utilization": round(avg_utilization, 2),
            "capacity_health": "healthy" if high_utilization_count < len(services) * 0.2 else "at_risk"
        }
    
    def _get_incident_metrics(self) -> Dict[str, Any]:
        """Get incident-related metrics"""
        if not self.incident_data:
            return {"total_incidents": 0, "avg_mttr": 0}
        
        recent_incidents = [
            inc for inc in self.incident_data
            if inc.start_time >= datetime.now() - timedelta(days=30)
        ]
        
        resolved_incidents = [inc for inc in recent_incidents if inc.mttr]
        
        avg_mttr = statistics.mean([inc.mttr.total_seconds() for inc in resolved_incidents]) if resolved_incidents else 0
        
        return {
            "total_incidents": len(recent_incidents),
            "resolved_incidents": len(resolved_incidents),
            "avg_mttr_seconds": avg_mttr,
            "avg_mttr_minutes": avg_mttr / 60 if avg_mttr > 0 else 0,
            "incident_trend": "stable"  # Could be enhanced with trend analysis
        }
    
    def _generate_sre_recommendations(self) -> List[Dict[str, Any]]:
        """Generate SRE recommendations based on current state"""
        recommendations = []
        
        # Check service health
        health_summary = self._get_service_health_summary()
        if health_summary.get("unhealthy_services", 0) > 0:
            recommendations.append({
                "type": "service_health",
                "priority": "high",
                "title": "Unhealthy Services Detected",
                "description": f"{health_summary['unhealthy_services']} services are below health threshold",
                "action": "Review service configurations and dependencies"
            })
        
        # Check SLO compliance
        slo_summary = self._get_slo_status_summary()
        if slo_summary.get("non_compliant_slos", 0) > 0:
            recommendations.append({
                "type": "slo_compliance",
                "priority": "high",
                "title": "SLO Compliance Issues",
                "description": f"{slo_summary['non_compliant_slos']} SLOs are not being met",
                "action": "Investigate service performance and adjust SLOs if needed"
            })
        
        # Check error budgets
        budget_summary = self._get_error_budget_summary()
        at_risk_budgets = [b for b in budget_summary.get("budget_details", []) if b["status"] != "healthy"]
        if at_risk_budgets:
            recommendations.append({
                "type": "error_budget",
                "priority": "medium",
                "title": "Error Budgets at Risk",
                "description": f"{len(at_risk_budgets)} error budgets are being consumed rapidly",
                "action": "Review service reliability and consider reducing deployment frequency"
            })
        
        # Check capacity
        capacity_status = self._get_capacity_status()
        if capacity_status.get("capacity_health") == "at_risk":
            recommendations.append({
                "type": "capacity",
                "priority": "medium",
                "title": "Capacity Issues Detected",
                "description": "Multiple services showing high utilization",
                "action": "Plan capacity expansion and review resource allocation"
            })
        
        # Check alert patterns
        alert_summary = self._get_alert_summary()
        if alert_summary.get("active_alerts", 0) > 10:
            recommendations.append({
                "type": "alerts",
                "priority": "medium",
                "title": "High Alert Volume",
                "description": f"{alert_summary['active_alerts']} active alerts detected",
                "action": "Review alert thresholds and consider alert correlation"
            })
        
        return recommendations
    
    def _calculate_impact_score(self, incident: IncidentImpact) -> float:
        """Calculate impact score for an incident (0-100)"""
        score = 0
        
        # Severity weight
        severity_weights = {
            'critical': 40,
            'warning': 20,
            'info': 10,
            'unknown': 15
        }
        score += severity_weights.get(incident.severity.value, 15)
        
        # Duration weight (up to 30 points)
        if incident.end_time and incident.start_time:
            duration_hours = (incident.end_time - incident.start_time).total_seconds() / 3600
            score += min(30, duration_hours * 2)  # 2 points per hour, max 30
        
        # User impact weight (up to 20 points)
        if incident.users_affected > 0:
            score += min(20, incident.users_affected / 100)  # 1 point per 100 users, max 20
        
        # Revenue impact weight (up to 10 points)
        if incident.revenue_impact > 0:
            score += min(10, incident.revenue_impact / 1000)  # 1 point per $1000, max 10
        
        return min(100, score)


# Export the main class
__all__ = ['SREAnalyticsEngine', 'SLOTarget', 'SLIMetric', 'AlertEvent', 'IncidentImpact', 'SLIType', 'AlertSeverity']


# Example usage
if __name__ == "__main__":
    # Example usage of the SRE Analytics Engine
    engine = SREAnalyticsEngine()
    
    # Register SLOs
    availability_slo = SLOTarget(
        name="web_service_availability",
        sli_type=SLIType.AVAILABILITY,
        target_percentage=99.9,
        measurement_window=timedelta(days=30)
    )
    
    engine.register_slo("web-service", availability_slo)
    
    # Simulate some SLI data
    import random
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(100):
        timestamp = base_time + timedelta(minutes=i * 15)
        success_rate = random.uniform(0.95, 1.0)
        
        sli_metric = SLIMetric(
            timestamp=timestamp,
            service="web-service",
            sli_type=SLIType.AVAILABILITY,
            value=success_rate,
            success_count=int(1000 * success_rate),
            total_count=1000
        )
        
        engine.record_sli_metric(sli_metric)
    
    # Generate analytics
    reliability = engine.calculate_service_reliability("web-service")
    print("Service Reliability Analysis:")
    print(json.dumps(reliability, indent=2, default=str))
    
    # Get dashboard data
    dashboard = engine.get_sre_dashboard_data()
    print("\nSRE Dashboard Data:")
    print(json.dumps(dashboard, indent=2, default=str))
