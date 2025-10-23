"""
Advanced Metrics and Observability System
Comprehensive monitoring with OpenTelemetry integration
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import logging
import json
import numpy as np
from contextlib import asynccontextmanager
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanContext:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    status: str = "in_progress"  # in_progress, success, error


class AdvancedMetricsCollector:
    """
    Comprehensive metrics collection and observability
    Supports Prometheus, Grafana, and OpenTelemetry patterns
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)

        # Metric storage
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.summaries: Dict[str, List[MetricPoint]] = defaultdict(list)

        # Tracing
        self.traces: Dict[str, SpanContext] = {}
        self.completed_traces: deque = deque(maxlen=10000)

        # Performance tracking
        self.operation_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_counts: Dict[str, int] = defaultdict(int)

        # Agent-specific metrics
        self.agent_metrics = {
            'rag': {
                'requests': 0,
                'total_time': 0.0,
                'confidence_scores': deque(maxlen=1000),
                'errors': 0
            },
            'cag': {
                'refinements': 0,
                'total_iterations': 0,
                'improvements': deque(maxlen=1000),
                'errors': 0
            },
            'predictor': {
                'predictions': 0,
                'accuracy_scores': deque(maxlen=1000),
                'errors': 0
            }
        }

        # System health
        self.health_checks: Dict[str, Dict] = {}
        self.alerts: List[Dict] = []

        logger.info("Advanced Metrics Collector initialized")

    # ============================================================================
    # BASIC METRICS
    # ============================================================================

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        if not self.enabled:
            return

        key = self._make_key(name, labels)
        self.counters[key] += value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        if not self.enabled:
            return

        key = self._make_key(name, labels)
        self.gauges[key] = value

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value for histogram"""
        if not self.enabled:
            return

        key = self._make_key(name, labels)
        self.histograms[key].append(value)

    def record_summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None,
                      metadata: Optional[Dict[str, Any]] = None):
        """Record a summary metric with metadata"""
        if not self.enabled:
            return

        key = self._make_key(name, labels)
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {},
            metadata=metadata or {}
        )
        self.summaries[key].append(point)

        # Trim old data
        if len(self.summaries[key]) > 1000:
            self.summaries[key] = self.summaries[key][-1000:]

    # ============================================================================
    # DISTRIBUTED TRACING
    # ============================================================================

    def start_span(self, operation_name: str, parent_id: Optional[str] = None,
                   tags: Optional[Dict[str, Any]] = None) -> str:
        """Start a new tracing span"""
        if not self.enabled:
            return "disabled"

        import uuid
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        span = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_id,
            operation_name=operation_name,
            start_time=datetime.now(),
            tags=tags or {}
        )

        self.traces[span_id] = span
        return span_id

    def end_span(self, span_id: str, error: Optional[str] = None):
        """End a tracing span"""
        if not self.enabled or span_id not in self.traces:
            return

        span = self.traces[span_id]
        span.end_time = datetime.now()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000

        if error:
            span.error = error
            span.status = "error"
        else:
            span.status = "success"

        # Move to completed traces
        self.completed_traces.append(span)
        del self.traces[span_id]

    def add_span_log(self, span_id: str, message: str, level: str = "info",
                     metadata: Optional[Dict] = None):
        """Add a log entry to a span"""
        if not self.enabled or span_id not in self.traces:
            return

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "metadata": metadata or {}
        }

        self.traces[span_id].logs.append(log_entry)

    @asynccontextmanager
    async def trace_operation(self, operation_name: str, tags: Optional[Dict[str, Any]] = None):
        """Context manager for tracing operations"""
        span_id = self.start_span(operation_name, tags=tags)
        error = None

        try:
            yield span_id
        except Exception as e:
            error = str(e)
            raise
        finally:
            self.end_span(span_id, error=error)

    # ============================================================================
    # AGENT-SPECIFIC METRICS
    # ============================================================================

    def record_rag_request(self, processing_time: float, confidence: float, error: bool = False):
        """Record RAG agent metrics"""
        metrics = self.agent_metrics['rag']
        metrics['requests'] += 1
        metrics['total_time'] += processing_time
        metrics['confidence_scores'].append(confidence)
        if error:
            metrics['errors'] += 1

        self.observe_histogram('rag_processing_time', processing_time, {'agent': 'rag'})
        self.observe_histogram('rag_confidence', confidence, {'agent': 'rag'})

    def record_cag_refinement(self, iterations: int, improvement: float, processing_time: float,
                            error: bool = False):
        """Record CAG agent metrics"""
        metrics = self.agent_metrics['cag']
        metrics['refinements'] += 1
        metrics['total_iterations'] += iterations
        metrics['improvements'].append(improvement)
        if error:
            metrics['errors'] += 1

        self.observe_histogram('cag_iterations', iterations, {'agent': 'cag'})
        self.observe_histogram('cag_improvement', improvement, {'agent': 'cag'})
        self.observe_histogram('cag_processing_time', processing_time, {'agent': 'cag'})

    def record_prediction(self, processing_time: float, accuracy: float = None, error: bool = False):
        """Record predictor metrics"""
        metrics = self.agent_metrics['predictor']
        metrics['predictions'] += 1
        if accuracy is not None:
            metrics['accuracy_scores'].append(accuracy)
        if error:
            metrics['errors'] += 1

        self.observe_histogram('predictor_processing_time', processing_time, {'agent': 'predictor'})
        if accuracy is not None:
            self.observe_histogram('predictor_accuracy', accuracy, {'agent': 'predictor'})

    # ============================================================================
    # PERCENTILE CALCULATIONS
    # ============================================================================

    def calculate_percentile(self, metric_name: str, percentile: int,
                            labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Calculate percentile for histogram metric"""
        key = self._make_key(metric_name, labels)

        if key not in self.histograms or not self.histograms[key]:
            return None

        values = list(self.histograms[key])
        return float(np.percentile(values, percentile))

    def calculate_percentiles(self, metric_name: str,
                             percentiles: List[int] = [50, 90, 95, 99],
                             labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Calculate multiple percentiles"""
        key = self._make_key(metric_name, labels)

        if key not in self.histograms or not self.histograms[key]:
            return {f"p{p}": None for p in percentiles}

        values = list(self.histograms[key])
        return {
            f"p{p}": float(np.percentile(values, p))
            for p in percentiles
        }

    # ============================================================================
    # AGGREGATION & STATISTICS
    # ============================================================================

    def get_counter_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0.0)

    def get_gauge_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get gauge value"""
        key = self._make_key(name, labels)
        return self.gauges.get(key)

    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, labels)

        if key not in self.histograms or not self.histograms[key]:
            return {}

        values = list(self.histograms[key])
        return {
            "count": len(values),
            "sum": float(np.sum(values)),
            "mean": float(np.mean(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "stddev": float(np.std(values)),
            **self.calculate_percentiles(name, labels=labels)
        }

    def get_error_rate(self, window_seconds: int = 300) -> float:
        """Calculate error rate in given time window"""
        total_errors = sum(self.error_counts.values())
        total_requests = sum(
            metrics['requests']
            for metrics in self.agent_metrics.values()
        )

        if total_requests == 0:
            return 0.0

        return total_errors / total_requests

    # ============================================================================
    # AGENT PERFORMANCE SUMMARY
    # ============================================================================

    def get_agent_performance(self) -> Dict[str, Any]:
        """Get comprehensive agent performance metrics"""
        performance = {}

        for agent_name, metrics in self.agent_metrics.items():
            requests = metrics.get('requests', 0)

            agent_perf = {
                "total_requests": requests,
                "error_count": metrics.get('errors', 0),
                "error_rate": metrics.get('errors', 0) / max(requests, 1)
            }

            # Agent-specific metrics
            if agent_name == 'rag':
                if metrics['confidence_scores']:
                    agent_perf.update({
                        "average_confidence": float(np.mean(metrics['confidence_scores'])),
                        "min_confidence": float(np.min(metrics['confidence_scores'])),
                        "max_confidence": float(np.max(metrics['confidence_scores']))
                    })
                if requests > 0:
                    agent_perf["average_processing_time"] = metrics['total_time'] / requests

            elif agent_name == 'cag':
                refinements = metrics.get('refinements', 0)
                if refinements > 0:
                    agent_perf["average_iterations"] = metrics['total_iterations'] / refinements
                if metrics['improvements']:
                    agent_perf["average_improvement"] = float(np.mean(metrics['improvements']))

            elif agent_name == 'predictor':
                if metrics['accuracy_scores']:
                    agent_perf["average_accuracy"] = float(np.mean(metrics['accuracy_scores']))

            performance[agent_name] = agent_perf

        return performance

    # ============================================================================
    # SYSTEM HEALTH
    # ============================================================================

    def register_health_check(self, component: str, check_func: Callable, interval: int = 60):
        """Register a health check for a component"""
        self.health_checks[component] = {
            "check_func": check_func,
            "interval": interval,
            "last_check": None,
            "status": "unknown",
            "message": ""
        }

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}

        for component, check_info in self.health_checks.items():
            try:
                check_func = check_info["check_func"]
                if asyncio.iscoroutinefunction(check_func):
                    status, message = await check_func()
                else:
                    status, message = check_func()

                check_info["last_check"] = datetime.now()
                check_info["status"] = status
                check_info["message"] = message

                results[component] = {
                    "status": status,
                    "message": message,
                    "last_check": check_info["last_check"].isoformat()
                }

            except Exception as e:
                logger.error(f"Health check failed for {component}: {e}")
                results[component] = {
                    "status": "error",
                    "message": str(e),
                    "last_check": datetime.now().isoformat()
                }

        return results

    def create_alert(self, severity: str, component: str, message: str, metadata: Optional[Dict] = None):
        """Create an alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,  # info, warning, error, critical
            "component": component,
            "message": message,
            "metadata": metadata or {}
        }

        self.alerts.append(alert)

        # Trim old alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

        logger.warning(f"Alert created: [{severity}] {component}: {message}")

    # ============================================================================
    # EXPORT & REPORTING
    # ============================================================================

    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format"""
        lines = []

        # Counters
        for key, value in self.counters.items():
            metric_name, labels = self._parse_key(key)
            label_str = self._format_labels(labels)
            lines.append(f'{metric_name}{label_str} {value}')

        # Gauges
        for key, value in self.gauges.items():
            metric_name, labels = self._parse_key(key)
            label_str = self._format_labels(labels)
            lines.append(f'{metric_name}{label_str} {value}')

        # Histograms
        for key, values in self.histograms.items():
            if values:
                metric_name, labels = self._parse_key(key)
                stats = self.get_histogram_stats(metric_name, labels)
                label_str = self._format_labels(labels)

                lines.append(f'{metric_name}_count{label_str} {stats["count"]}')
                lines.append(f'{metric_name}_sum{label_str} {stats["sum"]}')
                for p in [50, 90, 95, 99]:
                    if f"p{p}" in stats:
                        lines.append(f'{metric_name}_p{p}{label_str} {stats[f"p{p}"]}')

        return "\n".join(lines)

    def export_json(self) -> str:
        """Export all metrics as JSON"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                k: self.get_histogram_stats(k)
                for k in self.histograms.keys()
            },
            "agent_performance": self.get_agent_performance(),
            "system_health": {
                comp: {
                    "status": info["status"],
                    "message": info["message"],
                    "last_check": info["last_check"].isoformat() if info["last_check"] else None
                }
                for comp, info in self.health_checks.items()
            },
            "recent_alerts": self.alerts[-100:],
            "trace_summary": {
                "active_traces": len(self.traces),
                "completed_traces": len(self.completed_traces),
                "recent_traces": [
                    {
                        "operation": t.operation_name,
                        "duration_ms": t.duration_ms,
                        "status": t.status,
                        "timestamp": t.start_time.isoformat()
                    }
                    for t in list(self.completed_traces)[-20:]
                ]
            }
        }

        return json.dumps(export_data, indent=2, default=str)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create metric key from name and labels"""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _parse_key(self, key: str) -> Tuple[str, Dict[str, str]]:
        """Parse metric key back into name and labels"""
        if '{' not in key:
            return key, {}

        name, label_part = key.split('{', 1)
        label_part = label_part.rstrip('}')

        labels = {}
        if label_part:
            for pair in label_part.split(','):
                k, v = pair.split('=', 1)
                labels[k] = v

        return name, labels

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus"""
        if not labels:
            return ""

        label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(label_pairs) + "}"

    def reset(self):
        """Reset all metrics (useful for testing)"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.summaries.clear()
        self.traces.clear()
        self.completed_traces.clear()
        self.operation_times.clear()
        self.error_counts.clear()
        self.alerts.clear()

        # Reset agent metrics
        for agent in self.agent_metrics.values():
            agent['requests'] = 0
            agent['errors'] = 0
            agent['total_time'] = 0.0
            if 'confidence_scores' in agent:
                agent['confidence_scores'].clear()
            if 'improvements' in agent:
                agent['improvements'].clear()
            if 'accuracy_scores' in agent:
                agent['accuracy_scores'].clear()

        logger.info("All metrics reset")


# Global metrics collector instance
_global_collector: Optional[AdvancedMetricsCollector] = None


def get_metrics_collector() -> AdvancedMetricsCollector:
    """Get or create global metrics collector"""
    global _global_collector
    if _global_collector is None:
        _global_collector = AdvancedMetricsCollector()
    return _global_collector
