#!/usr/bin/env python3
"""
NagProm Alert Correlation and Analysis Engine

Advanced alert correlation system that identifies patterns, reduces noise,
and provides intelligent insights for incident management.

Features:
- Multi-dimensional alert correlation
- Pattern recognition and classification
- Alert clustering and deduplication
- Root cause analysis
- Anomaly detection for alerts
- Predictive alerting
- Alert fatigue reduction
- Incident timeline reconstruction
- Impact analysis
- Machine learning-based insights
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import numpy as np
import pandas as pd

# Optional ML imports with graceful fallbacks
try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. ML features will be disabled.")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("networkx not available. Dependency correlation will be disabled.")
import re
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    UNKNOWN = "unknown"


class AlertStatus(Enum):
    """Alert status"""
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class CorrelationType(Enum):
    """Types of alert correlation"""
    TEMPORAL = "temporal"          # Time-based correlation
    SPATIAL = "spatial"            # Location/service-based correlation
    CAUSAL = "causal"             # Cause-effect relationship
    SIMILARITY = "similarity"     # Similar alert patterns
    DEPENDENCY = "dependency"     # Service dependency correlation
    FREQUENCY = "frequency"       # Frequency pattern correlation


class IncidentSeverity(Enum):
    """Incident severity classification"""
    SEV1 = "sev1"  # Critical - service down
    SEV2 = "sev2"  # Major - significant impact
    SEV3 = "sev3"  # Minor - limited impact
    SEV4 = "sev4"  # Informational


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: datetime
    service: str
    host: str
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    fingerprint: str = ""
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'service': self.service,
            'host': self.host,
            'severity': self.severity.value,
            'status': self.status.value,
            'title': self.title,
            'description': self.description,
            'labels': self.labels,
            'annotations': self.annotations,
            'fingerprint': self.fingerprint,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'correlation_id': self.correlation_id
        }


@dataclass
class CorrelationRule:
    """Alert correlation rule"""
    id: str
    name: str
    description: str
    correlation_type: CorrelationType
    conditions: Dict[str, Any]
    time_window: timedelta
    confidence_threshold: float = 0.8
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AlertCluster:
    """Cluster of correlated alerts"""
    id: str
    alerts: List[Alert]
    correlation_type: CorrelationType
    confidence_score: float
    root_cause_candidates: List[str]
    impact_assessment: Dict[str, Any]
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    @property
    def severity(self) -> AlertSeverity:
        """Get cluster severity (highest severity among alerts)"""
        severities = [alert.severity for alert in self.alerts]
        if AlertSeverity.CRITICAL in severities:
            return AlertSeverity.CRITICAL
        elif AlertSeverity.WARNING in severities:
            return AlertSeverity.WARNING
        elif AlertSeverity.INFO in severities:
            return AlertSeverity.INFO
        else:
            return AlertSeverity.UNKNOWN
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'alert_count': len(self.alerts),
            'alerts': [alert.to_dict() for alert in self.alerts],
            'correlation_type': self.correlation_type.value,
            'confidence_score': self.confidence_score,
            'severity': self.severity.value,
            'root_cause_candidates': self.root_cause_candidates,
            'impact_assessment': self.impact_assessment,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class IncidentAnalysis:
    """Comprehensive incident analysis"""
    incident_id: str
    clusters: List[AlertCluster]
    timeline: List[Dict[str, Any]]
    root_cause_analysis: Dict[str, Any]
    impact_analysis: Dict[str, Any]
    recommendations: List[str]
    severity: IncidentSeverity
    estimated_duration: Optional[timedelta] = None
    affected_services: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)


class AlertCorrelationEngine:
    """Main alert correlation and analysis engine"""
    
    def __init__(self):
        self.alerts: deque = deque(maxlen=10000)
        self.clusters: Dict[str, AlertCluster] = {}
        self.correlation_rules: Dict[str, CorrelationRule] = {}
        self.service_dependencies: Dict[str, List[str]] = {}
        
        # Machine learning components
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        
        # Pattern recognition
        self.alert_patterns: Dict[str, Any] = {}
        self.noise_patterns: Set[str] = set()
        
        # Statistics and monitoring
        self.correlation_stats = {
            'total_alerts': 0,
            'correlated_alerts': 0,
            'clusters_created': 0,
            'false_positives': 0,
            'noise_suppressed': 0
        }
        
        # Register default correlation rules
        self._register_default_rules()
    
    def add_alert(self, alert: Alert):
        """Add a new alert for correlation analysis"""
        # Generate fingerprint if not provided
        if not alert.fingerprint:
            alert.fingerprint = self._generate_fingerprint(alert)
        
        # Add to alerts collection
        self.alerts.append(alert)
        self.correlation_stats['total_alerts'] += 1
        
        # Trigger correlation analysis
        asyncio.create_task(self._analyze_alert(alert))
        
        logger.debug(f"Added alert: {alert.id} from {alert.service}")
    
    def update_alert_status(self, alert_id: str, status: AlertStatus, 
                           resolved_at: Optional[datetime] = None,
                           acknowledged_by: Optional[str] = None):
        """Update alert status"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.status = status
                if status == AlertStatus.RESOLVED and resolved_at:
                    alert.resolved_at = resolved_at
                elif status == AlertStatus.ACKNOWLEDGED:
                    alert.acknowledged_at = datetime.now()
                    alert.acknowledged_by = acknowledged_by
                break
    
    def register_correlation_rule(self, rule: CorrelationRule):
        """Register a new correlation rule"""
        self.correlation_rules[rule.id] = rule
        logger.info(f"Registered correlation rule: {rule.name}")
    
    def set_service_dependencies(self, dependencies: Dict[str, List[str]]):
        """Set service dependency graph"""
        self.service_dependencies = dependencies
        logger.info(f"Updated service dependencies for {len(dependencies)} services")
    
    async def correlate_alerts(self, time_window: timedelta = timedelta(minutes=15)) -> List[AlertCluster]:
        """Perform comprehensive alert correlation"""
        end_time = datetime.now()
        start_time = end_time - time_window
        
        # Get recent alerts
        recent_alerts = [
            alert for alert in self.alerts
            if start_time <= alert.timestamp <= end_time and alert.status == AlertStatus.FIRING
        ]
        
        if len(recent_alerts) < 2:
            return []
        
        clusters = []
        
        # Apply different correlation strategies
        clusters.extend(await self._temporal_correlation(recent_alerts))
        clusters.extend(await self._spatial_correlation(recent_alerts))
        clusters.extend(await self._similarity_correlation(recent_alerts))
        clusters.extend(await self._dependency_correlation(recent_alerts))
        clusters.extend(await self._pattern_correlation(recent_alerts))
        
        # Merge overlapping clusters
        merged_clusters = self._merge_overlapping_clusters(clusters)
        
        # Update cluster storage
        for cluster in merged_clusters:
            self.clusters[cluster.id] = cluster
            self.correlation_stats['clusters_created'] += 1
        
        return merged_clusters
    
    async def analyze_incident(self, cluster_id: str) -> IncidentAnalysis:
        """Perform comprehensive incident analysis"""
        if cluster_id not in self.clusters:
            raise ValueError(f"Cluster {cluster_id} not found")
        
        cluster = self.clusters[cluster_id]
        
        # Create incident analysis
        incident_id = str(uuid.uuid4())
        
        # Build timeline
        timeline = self._build_incident_timeline([cluster])
        
        # Perform root cause analysis
        root_cause_analysis = await self._perform_root_cause_analysis(cluster)
        
        # Assess impact
        impact_analysis = self._assess_incident_impact(cluster)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(cluster, root_cause_analysis)
        
        # Determine severity
        severity = self._classify_incident_severity(cluster, impact_analysis)
        
        # Estimate duration
        estimated_duration = self._estimate_incident_duration(cluster)
        
        # Get affected services
        affected_services = {alert.service for alert in cluster.alerts}
        
        return IncidentAnalysis(
            incident_id=incident_id,
            clusters=[cluster],
            timeline=timeline,
            root_cause_analysis=root_cause_analysis,
            impact_analysis=impact_analysis,
            recommendations=recommendations,
            severity=severity,
            estimated_duration=estimated_duration,
            affected_services=affected_services
        )
    
    def detect_alert_patterns(self, lookback_period: timedelta = timedelta(days=7)) -> Dict[str, Any]:
        """Detect recurring alert patterns"""
        end_time = datetime.now()
        start_time = end_time - lookback_period
        
        # Get historical alerts
        historical_alerts = [
            alert for alert in self.alerts
            if start_time <= alert.timestamp <= end_time
        ]
        
        if not historical_alerts:
            return {'patterns': [], 'noise_patterns': []}
        
        # Pattern detection
        patterns = self._detect_patterns(historical_alerts)
        noise_patterns = self._detect_noise_patterns(historical_alerts)
        
        return {
            'patterns': patterns,
            'noise_patterns': noise_patterns,
            'analysis_period': lookback_period.total_seconds(),
            'total_alerts_analyzed': len(historical_alerts)
        }
    
    def predict_alerts(self, service: str, time_horizon: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Predict future alerts based on patterns"""
        # Get historical data for service
        service_alerts = [
            alert for alert in self.alerts
            if alert.service == service and alert.timestamp >= datetime.now() - timedelta(days=30)
        ]
        
        if len(service_alerts) < 10:
            return {'prediction': 'insufficient_data'}
        
        # Analyze patterns
        time_patterns = self._analyze_temporal_patterns(service_alerts)
        frequency_patterns = self._analyze_frequency_patterns(service_alerts)
        
        # Calculate prediction
        prediction_score = self._calculate_prediction_score(time_patterns, frequency_patterns)
        
        return {
            'service': service,
            'time_horizon': time_horizon.total_seconds(),
            'prediction_score': prediction_score,
            'confidence': self._calculate_prediction_confidence(service_alerts),
            'expected_alert_types': self._predict_alert_types(service_alerts),
            'risk_factors': self._identify_risk_factors(service_alerts)
        }
    
    def reduce_alert_noise(self, alerts: List[Alert]) -> List[Alert]:
        """Reduce alert noise using pattern recognition"""
        if not alerts:
            return alerts
        
        filtered_alerts = []
        
        for alert in alerts:
            if not self._is_noise_alert(alert):
                filtered_alerts.append(alert)
            else:
                self.correlation_stats['noise_suppressed'] += 1
        
        return filtered_alerts
    
    def get_correlation_metrics(self) -> Dict[str, Any]:
        """Get correlation engine metrics"""
        total_alerts = self.correlation_stats['total_alerts']
        correlated_alerts = self.correlation_stats['correlated_alerts']
        
        correlation_rate = (correlated_alerts / total_alerts * 100) if total_alerts > 0 else 0
        noise_reduction_rate = (self.correlation_stats['noise_suppressed'] / total_alerts * 100) if total_alerts > 0 else 0
        
        return {
            'total_alerts': total_alerts,
            'correlated_alerts': correlated_alerts,
            'correlation_rate': correlation_rate,
            'clusters_created': self.correlation_stats['clusters_created'],
            'noise_suppressed': self.correlation_stats['noise_suppressed'],
            'noise_reduction_rate': noise_reduction_rate,
            'active_clusters': len([c for c in self.clusters.values() if c.resolved_at is None]),
            'correlation_rules': len(self.correlation_rules)
        }
    
    # Private correlation methods
    
    async def _analyze_alert(self, alert: Alert):
        """Analyze a single alert for immediate correlation"""
        # Check for immediate patterns
        similar_alerts = self._find_similar_alerts(alert, timedelta(minutes=5))
        
        if similar_alerts:
            # Create or update cluster
            await self._update_or_create_cluster(alert, similar_alerts)
            self.correlation_stats['correlated_alerts'] += 1
    
    async def _temporal_correlation(self, alerts: List[Alert]) -> List[AlertCluster]:
        """Correlate alerts based on temporal proximity"""
        clusters = []
        
        # Sort alerts by timestamp
        sorted_alerts = sorted(alerts, key=lambda x: x.timestamp)
        
        # Group alerts within time windows
        current_group = []
        current_time = None
        
        for alert in sorted_alerts:
            if (current_time is None or 
                alert.timestamp - current_time <= timedelta(minutes=2)):
                current_group.append(alert)
                current_time = alert.timestamp
            else:
                if len(current_group) > 1:
                    cluster = self._create_cluster(
                        current_group, 
                        CorrelationType.TEMPORAL,
                        self._calculate_temporal_confidence(current_group)
                    )
                    clusters.append(cluster)
                
                current_group = [alert]
                current_time = alert.timestamp
        
        # Handle last group
        if len(current_group) > 1:
            cluster = self._create_cluster(
                current_group,
                CorrelationType.TEMPORAL,
                self._calculate_temporal_confidence(current_group)
            )
            clusters.append(cluster)
        
        return clusters
    
    async def _spatial_correlation(self, alerts: List[Alert]) -> List[AlertCluster]:
        """Correlate alerts based on spatial/service proximity"""
        clusters = []
        
        # Group by service and host
        service_groups = defaultdict(list)
        for alert in alerts:
            service_groups[alert.service].append(alert)
        
        for service, service_alerts in service_groups.items():
            if len(service_alerts) > 1:
                # Further group by host
                host_groups = defaultdict(list)
                for alert in service_alerts:
                    host_groups[alert.host].append(alert)
                
                for host, host_alerts in host_groups.items():
                    if len(host_alerts) > 1:
                        cluster = self._create_cluster(
                            host_alerts,
                            CorrelationType.SPATIAL,
                            self._calculate_spatial_confidence(host_alerts)
                        )
                        clusters.append(cluster)
        
        return clusters
    
    async def _similarity_correlation(self, alerts: List[Alert]) -> List[AlertCluster]:
        """Correlate alerts based on content similarity"""
        if not SKLEARN_AVAILABLE:
            logger.warning("Similarity correlation disabled - scikit-learn not available")
            return []
            
        if len(alerts) < 2:
            return []
        
        # Extract text features
        texts = [f"{alert.title} {alert.description}" for alert in alerts]
        
        try:
            # Compute TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Compute similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Apply clustering
            clustering = DBSCAN(eps=0.3, min_samples=2, metric='precomputed')
            distance_matrix = 1 - similarity_matrix
            cluster_labels = clustering.fit_predict(distance_matrix)
            
            # Create clusters
            clusters = []
            cluster_groups = defaultdict(list)
            
            for i, label in enumerate(cluster_labels):
                if label != -1:  # -1 indicates noise/outlier
                    cluster_groups[label].append(alerts[i])
            
            for group_alerts in cluster_groups.values():
                if len(group_alerts) > 1:
                    cluster = self._create_cluster(
                        group_alerts,
                        CorrelationType.SIMILARITY,
                        self._calculate_similarity_confidence(group_alerts, similarity_matrix)
                    )
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Similarity correlation failed: {e}")
            return []
    
    async def _dependency_correlation(self, alerts: List[Alert]) -> List[AlertCluster]:
        """Correlate alerts based on service dependencies"""
        if not NETWORKX_AVAILABLE:
            logger.warning("Dependency correlation disabled - networkx not available")
            return []
            
        if not self.service_dependencies:
            return []
        
        clusters = []
        
        # Build dependency graph
        graph = nx.DiGraph()
        for service, deps in self.service_dependencies.items():
            for dep in deps:
                graph.add_edge(dep, service)
        
        # Group alerts by service
        service_alerts = defaultdict(list)
        for alert in alerts:
            service_alerts[alert.service].append(alert)
        
        # Find dependency chains
        for service in service_alerts:
            if service in graph:
                # Get upstream and downstream services
                upstream = set(graph.predecessors(service))
                downstream = set(graph.successors(service))
                
                related_services = upstream.union(downstream)
                related_alerts = []
                
                for related_service in related_services:
                    if related_service in service_alerts:
                        related_alerts.extend(service_alerts[related_service])
                
                if len(related_alerts) > 1:
                    cluster = self._create_cluster(
                        related_alerts,
                        CorrelationType.DEPENDENCY,
                        self._calculate_dependency_confidence(related_alerts, graph)
                    )
                    clusters.append(cluster)
        
        return clusters
    
    async def _pattern_correlation(self, alerts: List[Alert]) -> List[AlertCluster]:
        """Correlate alerts based on learned patterns"""
        clusters = []
        
        # Apply learned patterns
        for pattern_id, pattern in self.alert_patterns.items():
            matching_alerts = []
            
            for alert in alerts:
                if self._matches_pattern(alert, pattern):
                    matching_alerts.append(alert)
            
            if len(matching_alerts) > 1:
                cluster = self._create_cluster(
                    matching_alerts,
                    CorrelationType.FREQUENCY,
                    pattern.get('confidence', 0.5)
                )
                clusters.append(cluster)
        
        return clusters
    
    def _create_cluster(self, alerts: List[Alert], correlation_type: CorrelationType, 
                       confidence: float) -> AlertCluster:
        """Create an alert cluster"""
        cluster_id = str(uuid.uuid4())
        
        # Identify root cause candidates
        root_cause_candidates = self._identify_root_causes(alerts, correlation_type)
        
        # Assess impact
        impact_assessment = self._assess_cluster_impact(alerts)
        
        cluster = AlertCluster(
            id=cluster_id,
            alerts=alerts,
            correlation_type=correlation_type,
            confidence_score=confidence,
            root_cause_candidates=root_cause_candidates,
            impact_assessment=impact_assessment,
            created_at=datetime.now()
        )
        
        # Update correlation IDs for alerts
        for alert in alerts:
            alert.correlation_id = cluster_id
        
        return cluster
    
    def _find_similar_alerts(self, alert: Alert, time_window: timedelta) -> List[Alert]:
        """Find alerts similar to the given alert"""
        cutoff_time = alert.timestamp - time_window
        
        similar_alerts = []
        for existing_alert in self.alerts:
            if (existing_alert.timestamp >= cutoff_time and
                existing_alert.id != alert.id and
                self._are_alerts_similar(alert, existing_alert)):
                similar_alerts.append(existing_alert)
        
        return similar_alerts
    
    def _are_alerts_similar(self, alert1: Alert, alert2: Alert) -> bool:
        """Check if two alerts are similar"""
        # Same service and host
        if alert1.service == alert2.service and alert1.host == alert2.host:
            return True
        
        # Similar fingerprints
        if alert1.fingerprint == alert2.fingerprint:
            return True
        
        # Similar titles (fuzzy matching)
        title_similarity = self._calculate_text_similarity(alert1.title, alert2.title)
        if title_similarity > 0.8:
            return True
        
        return False
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Simple Jaccard similarity for demonstration
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _generate_fingerprint(self, alert: Alert) -> str:
        """Generate a fingerprint for an alert"""
        # Create fingerprint from service, host, and normalized title
        normalized_title = re.sub(r'\d+', 'X', alert.title.lower())
        fingerprint_string = f"{alert.service}:{alert.host}:{normalized_title}"
        
        import hashlib
        return hashlib.md5(fingerprint_string.encode()).hexdigest()[:16]
    
    def _calculate_temporal_confidence(self, alerts: List[Alert]) -> float:
        """Calculate confidence for temporal correlation"""
        if len(alerts) < 2:
            return 0.0
        
        # Calculate time gaps between alerts
        sorted_alerts = sorted(alerts, key=lambda x: x.timestamp)
        gaps = []
        
        for i in range(1, len(sorted_alerts)):
            gap = sorted_alerts[i].timestamp - sorted_alerts[i-1].timestamp
            gaps.append(gap.total_seconds())
        
        # Higher confidence for smaller, more consistent gaps
        avg_gap = statistics.mean(gaps)
        std_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
        
        # Normalize confidence (smaller gaps = higher confidence)
        confidence = max(0.1, 1.0 - (avg_gap / 300))  # 300 seconds = 5 minutes
        
        # Penalize for high variation
        if std_gap > 0:
            confidence *= max(0.1, 1.0 - (std_gap / avg_gap))
        
        return min(1.0, confidence)
    
    def _calculate_spatial_confidence(self, alerts: List[Alert]) -> float:
        """Calculate confidence for spatial correlation"""
        # High confidence for same service/host
        return 0.9 if len(alerts) > 1 else 0.0
    
    def _calculate_similarity_confidence(self, alerts: List[Alert], similarity_matrix: np.ndarray) -> float:
        """Calculate confidence for similarity correlation"""
        # Average similarity score
        return float(np.mean(similarity_matrix))
    
    def _calculate_dependency_confidence(self, alerts: List[Alert], graph: nx.DiGraph) -> float:
        """Calculate confidence for dependency correlation"""
        # Base confidence on dependency distance
        services = [alert.service for alert in alerts]
        
        min_distance = float('inf')
        for i in range(len(services)):
            for j in range(i+1, len(services)):
                try:
                    distance = nx.shortest_path_length(graph, services[i], services[j])
                    min_distance = min(min_distance, distance)
                except nx.NetworkXNoPath:
                    continue
        
        if min_distance == float('inf'):
            return 0.1
        
        # Closer dependencies = higher confidence
        return max(0.1, 1.0 - (min_distance / 5))
    
    def _identify_root_causes(self, alerts: List[Alert], correlation_type: CorrelationType) -> List[str]:
        """Identify potential root causes for a cluster"""
        root_causes = []
        
        if correlation_type == CorrelationType.DEPENDENCY:
            # For dependency correlations, upstream services are likely root causes
            services = [alert.service for alert in alerts]
            
            if self.service_dependencies:
                for service in services:
                    if service in self.service_dependencies:
                        # Services with no dependencies might be root causes
                        if not self.service_dependencies[service]:
                            root_causes.append(service)
        
        elif correlation_type == CorrelationType.TEMPORAL:
            # For temporal correlations, earliest alert might indicate root cause
            earliest_alert = min(alerts, key=lambda x: x.timestamp)
            root_causes.append(f"{earliest_alert.service}:{earliest_alert.host}")
        
        elif correlation_type == CorrelationType.SPATIAL:
            # For spatial correlations, infrastructure issues are common root causes
            root_causes.extend(["network", "infrastructure", "hardware"])
        
        return root_causes or ["unknown"]
    
    def _assess_cluster_impact(self, alerts: List[Alert]) -> Dict[str, Any]:
        """Assess the impact of an alert cluster"""
        services = {alert.service for alert in alerts}
        hosts = {alert.host for alert in alerts}
        
        # Count by severity
        severity_counts = defaultdict(int)
        for alert in alerts:
            severity_counts[alert.severity.value] += 1
        
        return {
            'affected_services': len(services),
            'affected_hosts': len(hosts),
            'total_alerts': len(alerts),
            'severity_breakdown': dict(severity_counts),
            'services': list(services),
            'hosts': list(hosts)
        }
    
    def _merge_overlapping_clusters(self, clusters: List[AlertCluster]) -> List[AlertCluster]:
        """Merge clusters that have overlapping alerts"""
        if not clusters:
            return []
        
        merged = []
        used_clusters = set()
        
        for i, cluster1 in enumerate(clusters):
            if i in used_clusters:
                continue
            
            merged_alerts = set(cluster1.alerts)
            overlapping_clusters = [cluster1]
            
            for j, cluster2 in enumerate(clusters[i+1:], i+1):
                if j in used_clusters:
                    continue
                
                # Check for overlap
                cluster2_alerts = set(cluster2.alerts)
                if merged_alerts.intersection(cluster2_alerts):
                    merged_alerts.update(cluster2_alerts)
                    overlapping_clusters.append(cluster2)
                    used_clusters.add(j)
            
            if len(overlapping_clusters) > 1:
                # Create merged cluster
                merged_cluster = self._create_merged_cluster(overlapping_clusters)
                merged.append(merged_cluster)
            else:
                merged.append(cluster1)
            
            used_clusters.add(i)
        
        return merged
    
    def _create_merged_cluster(self, clusters: List[AlertCluster]) -> AlertCluster:
        """Create a merged cluster from multiple clusters"""
        all_alerts = []
        for cluster in clusters:
            all_alerts.extend(cluster.alerts)
        
        # Remove duplicates
        unique_alerts = []
        seen_ids = set()
        for alert in all_alerts:
            if alert.id not in seen_ids:
                unique_alerts.append(alert)
                seen_ids.add(alert.id)
        
        # Determine best correlation type and confidence
        correlation_types = [cluster.correlation_type for cluster in clusters]
        confidence_scores = [cluster.confidence_score for cluster in clusters]
        
        best_correlation_type = max(set(correlation_types), key=correlation_types.count)
        avg_confidence = statistics.mean(confidence_scores)
        
        return self._create_cluster(unique_alerts, best_correlation_type, avg_confidence)
    
    def _register_default_rules(self):
        """Register default correlation rules"""
        # Service cascade rule
        cascade_rule = CorrelationRule(
            id="service_cascade",
            name="Service Cascade Correlation",
            description="Correlate alerts when they cascade through service dependencies",
            correlation_type=CorrelationType.DEPENDENCY,
            conditions={
                "max_time_gap": 300,  # 5 minutes
                "min_services": 2
            },
            time_window=timedelta(minutes=10),
            confidence_threshold=0.7
        )
        self.register_correlation_rule(cascade_rule)
        
        # Burst alert rule
        burst_rule = CorrelationRule(
            id="alert_burst",
            name="Alert Burst Correlation",
            description="Correlate rapid succession of similar alerts",
            correlation_type=CorrelationType.TEMPORAL,
            conditions={
                "max_time_gap": 60,   # 1 minute
                "min_alerts": 3,
                "similarity_threshold": 0.8
            },
            time_window=timedelta(minutes=5),
            confidence_threshold=0.8
        )
        self.register_correlation_rule(burst_rule)
    
    # Pattern detection methods
    
    def _detect_patterns(self, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Detect recurring patterns in alerts"""
        patterns = []
        
        # Group by service and analyze patterns
        service_groups = defaultdict(list)
        for alert in alerts:
            service_groups[alert.service].append(alert)
        
        for service, service_alerts in service_groups.items():
            if len(service_alerts) >= 5:  # Minimum for pattern detection
                pattern = self._analyze_service_pattern(service, service_alerts)
                if pattern:
                    patterns.append(pattern)
        
        return patterns
    
    def _analyze_service_pattern(self, service: str, alerts: List[Alert]) -> Optional[Dict[str, Any]]:
        """Analyze alert patterns for a specific service"""
        # Analyze temporal patterns
        timestamps = [alert.timestamp for alert in alerts]
        timestamps.sort()
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return None
        
        # Detect recurring intervals
        avg_interval = statistics.mean(intervals)
        std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
        
        # Check for periodicity
        is_periodic = std_interval < (avg_interval * 0.3)  # Low variation indicates periodicity
        
        if is_periodic and avg_interval < 86400:  # Less than 24 hours
            return {
                'service': service,
                'type': 'periodic',
                'average_interval': avg_interval,
                'standard_deviation': std_interval,
                'occurrences': len(alerts),
                'confidence': 1.0 - (std_interval / avg_interval) if avg_interval > 0 else 0
            }
        
        return None
    
    def _detect_noise_patterns(self, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Detect noise patterns in alerts"""
        noise_patterns = []
        
        # Detect high-frequency, low-impact alerts
        alert_frequencies = defaultdict(int)
        
        for alert in alerts:
            key = f"{alert.service}:{alert.title}"
            alert_frequencies[key] += 1
        
        # Identify potential noise
        for key, frequency in alert_frequencies.items():
            if frequency > len(alerts) * 0.1:  # More than 10% of all alerts
                service, title = key.split(':', 1)
                noise_patterns.append({
                    'service': service,
                    'title': title,
                    'frequency': frequency,
                    'percentage': (frequency / len(alerts)) * 100,
                    'type': 'high_frequency'
                })
                
                # Add to noise patterns set
                self.noise_patterns.add(key)
        
        return noise_patterns
    
    def _is_noise_alert(self, alert: Alert) -> bool:
        """Check if an alert is considered noise"""
        key = f"{alert.service}:{alert.title}"
        return key in self.noise_patterns
    
    # Analysis and prediction methods
    
    def _build_incident_timeline(self, clusters: List[AlertCluster]) -> List[Dict[str, Any]]:
        """Build incident timeline from clusters"""
        timeline = []
        
        for cluster in clusters:
            for alert in cluster.alerts:
                timeline.append({
                    'timestamp': alert.timestamp.isoformat(),
                    'type': 'alert',
                    'service': alert.service,
                    'host': alert.host,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'cluster_id': cluster.id
                })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline
    
    async def _perform_root_cause_analysis(self, cluster: AlertCluster) -> Dict[str, Any]:
        """Perform root cause analysis for a cluster"""
        analysis = {
            'method': 'heuristic',
            'candidates': cluster.root_cause_candidates,
            'confidence': cluster.confidence_score,
            'evidence': []
        }
        
        # Analyze timing
        if cluster.correlation_type == CorrelationType.TEMPORAL:
            earliest_alert = min(cluster.alerts, key=lambda x: x.timestamp)
            analysis['evidence'].append({
                'type': 'temporal',
                'description': f"First alert from {earliest_alert.service} at {earliest_alert.timestamp}",
                'weight': 0.8
            })
        
        # Analyze dependencies
        if cluster.correlation_type == CorrelationType.DEPENDENCY:
            services = [alert.service for alert in cluster.alerts]
            upstream_services = []
            
            for service in services:
                if service in self.service_dependencies:
                    deps = self.service_dependencies[service]
                    upstream_services.extend([dep for dep in deps if dep in services])
            
            if upstream_services:
                analysis['evidence'].append({
                    'type': 'dependency',
                    'description': f"Upstream services affected: {', '.join(set(upstream_services))}",
                    'weight': 0.9
                })
        
        return analysis
    
    def _assess_incident_impact(self, cluster: AlertCluster) -> Dict[str, Any]:
        """Assess incident impact"""
        services = {alert.service for alert in cluster.alerts}
        hosts = {alert.host for alert in cluster.alerts}
        
        # Calculate severity score
        severity_weights = {
            AlertSeverity.CRITICAL: 4,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 1,
            AlertSeverity.UNKNOWN: 0
        }
        
        total_severity = sum(severity_weights.get(alert.severity, 0) for alert in cluster.alerts)
        
        return {
            'affected_services': len(services),
            'affected_hosts': len(hosts),
            'severity_score': total_severity,
            'estimated_users_affected': len(services) * 1000,  # Rough estimate
            'business_impact': 'high' if total_severity > 10 else 'medium' if total_severity > 5 else 'low'
        }
    
    def _generate_recommendations(self, cluster: AlertCluster, root_cause: Dict[str, Any]) -> List[str]:
        """Generate incident response recommendations"""
        recommendations = []
        
        # General recommendations based on cluster type
        if cluster.correlation_type == CorrelationType.DEPENDENCY:
            recommendations.append("Check service dependencies and upstream components")
            recommendations.append("Verify network connectivity between services")
        
        elif cluster.correlation_type == CorrelationType.SPATIAL:
            recommendations.append("Investigate infrastructure issues on affected hosts")
            recommendations.append("Check system resources (CPU, memory, disk)")
        
        elif cluster.correlation_type == CorrelationType.TEMPORAL:
            recommendations.append("Review recent deployments or configuration changes")
            recommendations.append("Check for scheduled maintenance or batch jobs")
        
        # Severity-specific recommendations
        if cluster.severity == AlertSeverity.CRITICAL:
            recommendations.append("Escalate to on-call engineer immediately")
            recommendations.append("Consider activating incident response team")
        
        # Service-specific recommendations
        services = {alert.service for alert in cluster.alerts}
        if 'database' in services:
            recommendations.append("Check database connections and query performance")
        
        if 'api' in str(services).lower():
            recommendations.append("Monitor API response times and error rates")
        
        return recommendations
    
    def _classify_incident_severity(self, cluster: AlertCluster, impact: Dict[str, Any]) -> IncidentSeverity:
        """Classify incident severity"""
        severity_score = impact.get('severity_score', 0)
        affected_services = impact.get('affected_services', 0)
        
        if severity_score >= 15 or affected_services >= 5:
            return IncidentSeverity.SEV1
        elif severity_score >= 10 or affected_services >= 3:
            return IncidentSeverity.SEV2
        elif severity_score >= 5 or affected_services >= 1:
            return IncidentSeverity.SEV3
        else:
            return IncidentSeverity.SEV4
    
    def _estimate_incident_duration(self, cluster: AlertCluster) -> Optional[timedelta]:
        """Estimate incident duration based on historical data"""
        # Simplified estimation based on cluster size and severity
        base_duration = timedelta(minutes=30)
        
        # Adjust based on cluster size
        size_factor = len(cluster.alerts) / 10
        severity_factor = 2 if cluster.severity == AlertSeverity.CRITICAL else 1
        
        estimated_minutes = base_duration.total_seconds() / 60 * size_factor * severity_factor
        
        return timedelta(minutes=estimated_minutes)
    
    def _analyze_temporal_patterns(self, alerts: List[Alert]) -> Dict[str, Any]:
        """Analyze temporal patterns in alerts"""
        if not alerts:
            return {}
        
        # Extract hour of day and day of week
        hours = [alert.timestamp.hour for alert in alerts]
        days = [alert.timestamp.weekday() for alert in alerts]
        
        # Find peak hours and days
        hour_counts = defaultdict(int)
        day_counts = defaultdict(int)
        
        for hour in hours:
            hour_counts[hour] += 1
        
        for day in days:
            day_counts[day] += 1
        
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
        peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
        
        return {
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'hourly_distribution': dict(hour_counts),
            'daily_distribution': dict(day_counts)
        }
    
    def _analyze_frequency_patterns(self, alerts: List[Alert]) -> Dict[str, Any]:
        """Analyze frequency patterns in alerts"""
        if not alerts:
            return {}
        
        # Calculate intervals between alerts
        sorted_alerts = sorted(alerts, key=lambda x: x.timestamp)
        intervals = []
        
        for i in range(1, len(sorted_alerts)):
            interval = (sorted_alerts[i].timestamp - sorted_alerts[i-1].timestamp).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return {}
        
        avg_interval = statistics.mean(intervals)
        std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
        
        return {
            'average_interval': avg_interval,
            'interval_std_dev': std_interval,
            'frequency_per_hour': 3600 / avg_interval if avg_interval > 0 else 0,
            'is_regular': std_interval < (avg_interval * 0.3)
        }
    
    def _calculate_prediction_score(self, time_patterns: Dict[str, Any], 
                                  frequency_patterns: Dict[str, Any]) -> float:
        """Calculate alert prediction score"""
        score = 0.0
        
        # Base score on frequency regularity
        if frequency_patterns.get('is_regular', False):
            score += 0.3
        
        # Add score for frequency
        freq_per_hour = frequency_patterns.get('frequency_per_hour', 0)
        if freq_per_hour > 0:
            score += min(0.4, freq_per_hour / 10)  # Cap at 0.4
        
        # Add score for temporal patterns
        if time_patterns.get('peak_hour') is not None:
            current_hour = datetime.now().hour
            peak_hour = time_patterns['peak_hour']
            
            # Higher score if current time is near peak hour
            hour_diff = min(abs(current_hour - peak_hour), 24 - abs(current_hour - peak_hour))
            if hour_diff <= 2:
                score += 0.3
        
        return min(1.0, score)
    
    def _calculate_prediction_confidence(self, alerts: List[Alert]) -> float:
        """Calculate prediction confidence"""
        # Base confidence on sample size
        base_confidence = min(0.9, len(alerts) / 100)
        
        # Adjust for recency
        recent_alerts = [
            alert for alert in alerts
            if alert.timestamp >= datetime.now() - timedelta(days=7)
        ]
        
        recency_factor = len(recent_alerts) / len(alerts) if alerts else 0
        
        return base_confidence * (0.5 + 0.5 * recency_factor)
    
    def _predict_alert_types(self, alerts: List[Alert]) -> List[str]:
        """Predict likely alert types"""
        # Count alert types
        type_counts = defaultdict(int)
        for alert in alerts:
            type_counts[alert.title] += 1
        
        # Return most common types
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        return [alert_type for alert_type, count in sorted_types[:5]]
    
    def _identify_risk_factors(self, alerts: List[Alert]) -> List[str]:
        """Identify risk factors for future alerts"""
        risk_factors = []
        
        # High frequency alerts
        if len(alerts) > 50:
            risk_factors.append("High alert frequency")
        
        # Critical alerts
        critical_count = sum(1 for alert in alerts if alert.severity == AlertSeverity.CRITICAL)
        if critical_count > 5:
            risk_factors.append("Frequent critical alerts")
        
        # Multiple hosts affected
        hosts = {alert.host for alert in alerts}
        if len(hosts) > 10:
            risk_factors.append("Multiple hosts affected")
        
        return risk_factors
    
    def _matches_pattern(self, alert: Alert, pattern: Dict[str, Any]) -> bool:
        """Check if alert matches a learned pattern"""
        # Simple pattern matching implementation
        if pattern.get('service') and pattern['service'] != alert.service:
            return False
        
        if pattern.get('title_pattern'):
            if pattern['title_pattern'] not in alert.title:
                return False
        
        return True
    
    async def _update_or_create_cluster(self, alert: Alert, similar_alerts: List[Alert]):
        """Update existing cluster or create new one"""
        # Check if any similar alert already has a correlation ID
        existing_cluster_id = None
        for similar_alert in similar_alerts:
            if similar_alert.correlation_id:
                existing_cluster_id = similar_alert.correlation_id
                break
        
        if existing_cluster_id and existing_cluster_id in self.clusters:
            # Update existing cluster
            cluster = self.clusters[existing_cluster_id]
            cluster.alerts.append(alert)
            alert.correlation_id = existing_cluster_id
        else:
            # Create new cluster
            all_alerts = [alert] + similar_alerts
            cluster = self._create_cluster(all_alerts, CorrelationType.SIMILARITY, 0.8)
            self.clusters[cluster.id] = cluster


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize correlation engine
        engine = AlertCorrelationEngine()
        
        # Set service dependencies
        dependencies = {
            'web-service': ['api-service', 'auth-service'],
            'api-service': ['database', 'cache'],
            'auth-service': ['ldap'],
            'database': [],
            'cache': [],
            'ldap': []
        }
        engine.set_service_dependencies(dependencies)
        
        # Add sample alerts
        import random
        base_time = datetime.now() - timedelta(hours=1)
        
        for i in range(20):
            alert = Alert(
                id=str(uuid.uuid4()),
                timestamp=base_time + timedelta(minutes=i * 3),
                service=random.choice(['web-service', 'api-service', 'database']),
                host=f"host-{random.randint(1, 5):02d}",
                severity=random.choice(list(AlertSeverity)),
                status=AlertStatus.FIRING,
                title=random.choice(['High CPU Usage', 'Memory Leak', 'Connection Timeout']),
                description=f"Sample alert {i+1}"
            )
            engine.add_alert(alert)
        
        # Wait for correlation
        await asyncio.sleep(1)
        
        # Perform correlation
        clusters = await engine.correlate_alerts()
        print(f"Found {len(clusters)} alert clusters")
        
        for cluster in clusters:
            print(f"Cluster {cluster.id}: {len(cluster.alerts)} alerts, "
                  f"type: {cluster.correlation_type.value}, "
                  f"confidence: {cluster.confidence_score:.2f}")
        
        # Get metrics
        metrics = engine.get_correlation_metrics()
        print("Correlation metrics:", json.dumps(metrics, indent=2))
        
        # Detect patterns
        patterns = engine.detect_alert_patterns()
        print("Alert patterns:", json.dumps(patterns, indent=2, default=str))
    
    asyncio.run(main())
