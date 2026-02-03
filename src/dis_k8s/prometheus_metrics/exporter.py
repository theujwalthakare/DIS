"""
Prometheus Metrics Integration
===============================

Exposes DIS metrics to Prometheus for monitoring and alerting.
"""

import logging
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)


class DISMetrics:
    """
    Prometheus metrics for Digital Immune System.
    """

    def __init__(self):
        """Initialize Prometheus metrics"""
        
        # aDC metrics
        self.antigens_collected = Counter(
            'dis_antigens_collected_total',
            'Total number of antigens collected',
            ['node', 'metric_type']
        )
        
        self.cpu_usage = Gauge(
            'dis_node_cpu_usage_percent',
            'Current CPU usage percentage',
            ['node']
        )
        
        self.memory_usage = Gauge(
            'dis_node_memory_usage_percent',
            'Current memory usage percentage',
            ['node']
        )
        
        self.network_bytes = Gauge(
            'dis_node_network_bytes_total',
            'Total network bytes (sent + received)',
            ['node']
        )
        
        # T-Helper metrics
        self.anomalies_detected = Counter(
            'dis_anomalies_detected_total',
            'Total number of anomalies detected',
            ['detector', 'node']
        )
        
        self.detection_latency = Histogram(
            'dis_detection_latency_seconds',
            'Time taken for anomaly detection',
            ['detector']
        )
        
        # B-Cell metrics
        self.responses_executed = Counter(
            'dis_responses_executed_total',
            'Total number of immune responses executed',
            ['action', 'success']
        )
        
        self.quarantined_pods = Gauge(
            'dis_quarantined_pods_current',
            'Current number of quarantined pods'
        )
        
        self.memory_cells = Gauge(
            'dis_memory_cells_total',
            'Total number of immune memory cells'
        )
        
        logger.info("Prometheus metrics initialized")

    def record_antigen(self, node: str, metric_type: str):
        """Record collection of an antigen"""
        self.antigens_collected.labels(node=node, metric_type=metric_type).inc()

    def update_cpu_usage(self, node: str, value: float):
        """Update CPU usage metric"""
        self.cpu_usage.labels(node=node).set(value)

    def update_memory_usage(self, node: str, value: float):
        """Update memory usage metric"""
        self.memory_usage.labels(node=node).set(value)

    def update_network_bytes(self, node: str, value: float):
        """Update network bytes metric"""
        self.network_bytes.labels(node=node).set(value)

    def record_anomaly(self, detector: str, node: str):
        """Record detection of an anomaly"""
        self.anomalies_detected.labels(detector=detector, node=node).inc()

    def record_detection_time(self, detector: str, duration: float):
        """Record time taken for detection"""
        self.detection_latency.labels(detector=detector).observe(duration)

    def record_response(self, action: str, success: bool):
        """Record execution of an immune response"""
        self.responses_executed.labels(
            action=action,
            success='true' if success else 'false'
        ).inc()

    def update_quarantined_pods(self, count: int):
        """Update number of quarantined pods"""
        self.quarantined_pods.set(count)

    def update_memory_cells(self, count: int):
        """Update number of memory cells"""
        self.memory_cells.set(count)

    def start_server(self, port: int = 8000):
        """
        Start Prometheus metrics HTTP server.

        Args:
            port: Port to serve metrics on
        """
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
