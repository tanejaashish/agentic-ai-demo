"""
Metrics collection utility for monitoring
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import defaultdict, deque
import threading
import json

class MetricsCollector:
    """
    Collect and export metrics for monitoring
    """
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.metrics = defaultdict(lambda: deque(maxlen=window_size))
        self.counters = defaultdict(int)
        self.gauges = {}
        self.histograms = defaultdict(list)
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def record_request(self, endpoint: str, method: str = "POST"):
        """
        Record an API request
        """
        with self.lock:
            self.counters["total_requests"] += 1
            self.counters[f"requests_{method}_{endpoint}"] += 1
            self.metrics["request_times"].append(time.time())
    
    def record_response(
        self,
        response: Dict[str, Any],
        duration: Optional[float] = None
    ):
        """
        Record an API response
        """
        with self.lock:
            self.counters["total_responses"] += 1
            
            if duration:
                self.histograms["response_duration"].append(duration)
            
            if "confidence" in response:
                self.metrics["confidence_scores"].append(response["confidence"])
            
            if "cag_applied" in response:
                if response["cag_applied"]:
                    self.counters["cag_applications"] += 1
    
    def record_error(self, error_type: str):
        """
        Record an error
        """
        with self.lock:
            self.counters["total_errors"] += 1
            self.counters[f"error_{error_type}"] += 1
    
    def set_gauge(self, name: str, value: float):
        """
        Set a gauge metric
        """
        with self.lock:
            self.gauges[name] = value
    
    def increment_counter(self, name: str, value: int = 1):
        """
        Increment a counter
        """
        with self.lock:
            self.counters[name] += value
    
    def record_histogram(self, name: str, value: float):
        """
        Record a value in histogram
        """
        with self.lock:
            self.histograms[name].append(value)
    
    def get_processing_time(self) -> float:
        """
        Get current processing time (mock for demo)
        """
        import random
        return round(random.uniform(1.5, 3.5), 2)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot
        """
        with self.lock:
            # Calculate rates
            uptime = time.time() - self.start_time
            request_rate = self.counters["total_requests"] / max(uptime, 1)
            
            # Calculate averages
            avg_confidence = 0
            if self.metrics["confidence_scores"]:
                avg_confidence = sum(self.metrics["confidence_scores"]) / len(
                    self.metrics["confidence_scores"]
                )
            
            avg_duration = 0
            if self.histograms["response_duration"]:
                avg_duration = sum(self.histograms["response_duration"]) / len(
                    self.histograms["response_duration"]
                )
            
            return {
                "uptime_seconds": uptime,
                "total_requests": self.counters["total_requests"],
                "total_responses": self.counters["total_responses"],
                "total_errors": self.counters["total_errors"],
                "request_rate": request_rate,
                "average_confidence": avg_confidence,
                "average_duration": avg_duration,
                "cag_applications": self.counters["cag_applications"],
                "cag_rate": self.counters["cag_applications"] / max(
                    self.counters["total_responses"], 1
                ),
                "gauges": dict(self.gauges),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format
        """
        lines = []
        metrics = self.get_current_metrics()
        
        # Add comments
        lines.append("# HELP requests_total Total number of requests")
        lines.append("# TYPE requests_total counter")
        lines.append(f"requests_total {metrics['total_requests']}")
        
        lines.append("# HELP responses_total Total number of responses")
        lines.append("# TYPE responses_total counter")
        lines.append(f"responses_total {metrics['total_responses']}")
        
        lines.append("# HELP errors_total Total number of errors")
        lines.append("# TYPE errors_total counter")
        lines.append(f"errors_total {metrics['total_errors']}")
        
        lines.append("# HELP average_confidence Average confidence score")
        lines.append("# TYPE average_confidence gauge")
        lines.append(f"average_confidence {metrics['average_confidence']}")
        
        lines.append("# HELP average_duration_seconds Average response duration")
        lines.append("# TYPE average_duration_seconds gauge")
        lines.append(f"average_duration_seconds {metrics['average_duration']}")
        
        lines.append("# HELP cag_applications_total Number of CAG applications")
        lines.append("# TYPE cag_applications_total counter")
        lines.append(f"cag_applications_total {metrics['cag_applications']}")
        
        # Add all counters
        for name, value in self.counters.items():
            if name not in ["total_requests", "total_responses", "total_errors", "cag_applications"]:
                lines.append(f"# HELP {name} Custom counter")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")
        
        # Add all gauges
        for name, value in self.gauges.items():
            lines.append(f"# HELP {name} Custom gauge")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        return "\n".join(lines)
    
    def reset_metrics(self):
        """
        Reset all metrics
        """
        with self.lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.start_time = time.time()


class PerformanceTracker:
    """
    Track performance of specific operations
    """
    
    def __init__(self):
        self.timings = defaultdict(list)
    
    def track(self, operation: str):
        """
        Context manager to track operation timing
        """
        return TimingContext(self, operation)
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """
        Get statistics for an operation
        """
        if operation not in self.timings or not self.timings[operation]:
            return {"count": 0, "mean": 0, "min": 0, "max": 0}
        
        times = self.timings[operation]
        return {
            "count": len(times),
            "mean": sum(times) / len(times),
            "min": min(times),
            "max": max(times)
        }
    
    def clear(self):
        """
        Clear all timings
        """
        self.timings.clear()


class TimingContext:
    """
    Context manager for timing operations
    """
    
    def __init__(self, tracker: PerformanceTracker, operation: str):
        self.tracker = tracker
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.tracker.timings[self.operation].append(duration)