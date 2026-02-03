"""
Artificial Dendritic Cell (aDC) Agent
======================================

Monitors system antigens including:
- CPU usage
- Memory usage
- Network metrics
- Kubernetes pod events
"""

import time
import logging
import psutil
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from kubernetes import client, config, watch

logger = logging.getLogger(__name__)


@dataclass
class Antigen:
    """Represents a monitored system metric (antigen)"""
    timestamp: float
    node_name: str
    metric_type: str  # 'cpu', 'memory', 'network', 'pod_event'
    value: float
    metadata: Optional[Dict] = None

    def to_dict(self):
        return asdict(self)


class ArtificialDendriticCell:
    """
    aDC agent that monitors node-level metrics and Kubernetes pod events.
    Acts as the sensory component of the immune system.
    """

    def __init__(self, node_name: str, collect_interval: int = 10):
        """
        Initialize aDC agent.

        Args:
            node_name: Name of the Kubernetes node to monitor
            collect_interval: Interval in seconds between collections
        """
        self.node_name = node_name
        self.collect_interval = collect_interval
        self.antigens: List[Antigen] = []
        
        # Initialize Kubernetes client
        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except config.ConfigException:
                logger.warning("Could not load Kubernetes config, K8s features disabled")
        
        self.v1 = client.CoreV1Api()
        logger.info(f"aDC agent initialized for node: {node_name}")

    def collect_cpu_metrics(self) -> Antigen:
        """Collect CPU usage metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        return Antigen(
            timestamp=time.time(),
            node_name=self.node_name,
            metric_type='cpu',
            value=cpu_percent,
            metadata={'cores': psutil.cpu_count()}
        )

    def collect_memory_metrics(self) -> Antigen:
        """Collect memory usage metrics"""
        memory = psutil.virtual_memory()
        return Antigen(
            timestamp=time.time(),
            node_name=self.node_name,
            metric_type='memory',
            value=memory.percent,
            metadata={
                'total': memory.total,
                'available': memory.available,
                'used': memory.used
            }
        )

    def collect_network_metrics(self) -> Antigen:
        """Collect network I/O metrics"""
        net_io = psutil.net_io_counters()
        return Antigen(
            timestamp=time.time(),
            node_name=self.node_name,
            metric_type='network',
            value=net_io.bytes_sent + net_io.bytes_recv,
            metadata={
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        )

    def watch_pod_events(self, namespace: str = 'default', timeout: int = 60):
        """
        Watch for Kubernetes pod events.

        Args:
            namespace: Kubernetes namespace to watch
            timeout: Timeout in seconds for watching
        """
        try:
            w = watch.Watch()
            for event in w.stream(self.v1.list_namespaced_pod,
                                 namespace=namespace,
                                 timeout_seconds=timeout):
                pod = event['object']
                event_type = event['type']
                
                # Create antigen from pod event
                antigen = Antigen(
                    timestamp=time.time(),
                    node_name=self.node_name,
                    metric_type='pod_event',
                    value=1.0 if event_type in ['ADDED', 'MODIFIED'] else 0.0,
                    metadata={
                        'event_type': event_type,
                        'pod_name': pod.metadata.name,
                        'pod_phase': pod.status.phase,
                        'node': pod.spec.node_name
                    }
                )
                self.antigens.append(antigen)
                logger.debug(f"Pod event captured: {event_type} - {pod.metadata.name}")
                
        except Exception as e:
            logger.error(f"Error watching pod events: {e}")

    def collect_all_metrics(self) -> List[Antigen]:
        """Collect all metrics (CPU, memory, network)"""
        antigens = []
        
        try:
            antigens.append(self.collect_cpu_metrics())
        except Exception as e:
            logger.error(f"Error collecting CPU metrics: {e}")
            
        try:
            antigens.append(self.collect_memory_metrics())
        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")
            
        try:
            antigens.append(self.collect_network_metrics())
        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")
        
        self.antigens.extend(antigens)
        return antigens

    def get_recent_antigens(self, count: int = 100) -> List[Antigen]:
        """Get most recent antigens"""
        return self.antigens[-count:] if len(self.antigens) > count else self.antigens

    def clear_antigens(self):
        """Clear collected antigens"""
        self.antigens.clear()
