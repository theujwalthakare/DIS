"""
B-Cell Memory Layer: Adaptive Immune Response
==============================================

Implements adaptive responses to detected anomalies:
- Pod isolation (quarantine)
- Pod restart
- Memory of past threats
"""

import logging
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from kubernetes import client
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class MemoryCell:
    """Represents immune memory of a past threat"""
    threat_signature: str  # Hash or identifier of the threat pattern
    pod_name: str
    namespace: str
    timestamp: float
    response_action: str  # 'isolate', 'restart', 'none'
    success: bool
    
    def to_dict(self):
        return asdict(self)


class BCellMemoryLayer:
    """
    B-Cell memory layer that stores and recalls immune responses.
    Implements adaptive immunity with memory of past threats.
    """

    def __init__(self, memory_retention_hours: int = 24):
        """
        Initialize B-Cell memory layer.

        Args:
            memory_retention_hours: How long to retain memory (hours)
        """
        self.memory_cells: List[MemoryCell] = []
        self.memory_retention_hours = memory_retention_hours
        self.quarantined_pods: Set[str] = set()
        
        # Initialize Kubernetes client
        try:
            from kubernetes import config
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
        except Exception as e:
            logger.warning(f"Could not load Kubernetes config: {e}")
            
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        logger.info("B-Cell memory layer initialized")

    def add_memory(self, threat_signature: str, pod_name: str, namespace: str,
                   response_action: str, success: bool):
        """
        Add a memory cell for a past threat.

        Args:
            threat_signature: Identifier of the threat pattern
            pod_name: Name of the affected pod
            namespace: Kubernetes namespace
            response_action: Action taken ('isolate', 'restart', 'none')
            success: Whether the response was successful
        """
        memory = MemoryCell(
            threat_signature=threat_signature,
            pod_name=pod_name,
            namespace=namespace,
            timestamp=time.time(),
            response_action=response_action,
            success=success
        )
        self.memory_cells.append(memory)
        logger.info(f"Memory added: {threat_signature} -> {response_action}")

    def recall_memory(self, threat_signature: str) -> List[MemoryCell]:
        """
        Recall past responses to similar threats.

        Args:
            threat_signature: Identifier to search for

        Returns:
            List of matching memory cells
        """
        self._cleanup_old_memories()
        matches = [m for m in self.memory_cells if m.threat_signature == threat_signature]
        return matches

    def _cleanup_old_memories(self):
        """Remove memories older than retention period"""
        cutoff_time = time.time() - (self.memory_retention_hours * 3600)
        self.memory_cells = [m for m in self.memory_cells if m.timestamp > cutoff_time]

    def isolate_pod(self, pod_name: str, namespace: str = 'default') -> bool:
        """
        Isolate a pod by adding network policy (quarantine).

        Args:
            pod_name: Name of the pod to isolate
            namespace: Kubernetes namespace

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get pod details
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            
            # Add quarantine label
            if pod.metadata.labels is None:
                pod.metadata.labels = {}
            pod.metadata.labels['dis-quarantine'] = 'true'
            
            self.v1.patch_namespaced_pod(
                name=pod_name,
                namespace=namespace,
                body=pod
            )
            
            self.quarantined_pods.add(f"{namespace}/{pod_name}")
            logger.info(f"Pod isolated: {namespace}/{pod_name}")
            
            # Create network policy to block traffic
            self._create_isolation_network_policy(pod_name, namespace)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to isolate pod {pod_name}: {e}")
            return False

    def _create_isolation_network_policy(self, pod_name: str, namespace: str):
        """Create a network policy to isolate the pod"""
        try:
            networking_v1 = client.NetworkingV1Api()
            
            # Network policy that denies all traffic
            network_policy = client.V1NetworkPolicy(
                api_version="networking.k8s.io/v1",
                kind="NetworkPolicy",
                metadata=client.V1ObjectMeta(
                    name=f"isolate-{pod_name}",
                    namespace=namespace
                ),
                spec=client.V1NetworkPolicySpec(
                    pod_selector=client.V1LabelSelector(
                        match_labels={'dis-quarantine': 'true'}
                    ),
                    policy_types=["Ingress", "Egress"],
                    ingress=[],  # Empty list denies all ingress
                    egress=[]    # Empty list denies all egress
                )
            )
            
            networking_v1.create_namespaced_network_policy(
                namespace=namespace,
                body=network_policy
            )
            
            logger.info(f"Network policy created for {namespace}/{pod_name}")
            
        except Exception as e:
            logger.warning(f"Could not create network policy: {e}")

    def restart_pod(self, pod_name: str, namespace: str = 'default') -> bool:
        """
        Restart a pod by deleting it (will be recreated by controller).

        Args:
            pod_name: Name of the pod to restart
            namespace: Kubernetes namespace

        Returns:
            True if successful, False otherwise
        """
        try:
            self.v1.delete_namespaced_pod(
                name=pod_name,
                namespace=namespace,
                grace_period_seconds=0
            )
            
            logger.info(f"Pod deleted for restart: {namespace}/{pod_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart pod {pod_name}: {e}")
            return False

    def release_pod(self, pod_name: str, namespace: str = 'default') -> bool:
        """
        Release a pod from quarantine.

        Args:
            pod_name: Name of the pod to release
            namespace: Kubernetes namespace

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get pod details
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            
            # Remove quarantine label
            if pod.metadata.labels and 'dis-quarantine' in pod.metadata.labels:
                del pod.metadata.labels['dis-quarantine']
                
                self.v1.patch_namespaced_pod(
                    name=pod_name,
                    namespace=namespace,
                    body=pod
                )
            
            self.quarantined_pods.discard(f"{namespace}/{pod_name}")
            logger.info(f"Pod released from quarantine: {namespace}/{pod_name}")
            
            # Delete network policy
            self._delete_isolation_network_policy(pod_name, namespace)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to release pod {pod_name}: {e}")
            return False

    def _delete_isolation_network_policy(self, pod_name: str, namespace: str):
        """Delete the isolation network policy"""
        try:
            networking_v1 = client.NetworkingV1Api()
            networking_v1.delete_namespaced_network_policy(
                name=f"isolate-{pod_name}",
                namespace=namespace
            )
            logger.info(f"Network policy deleted for {namespace}/{pod_name}")
        except Exception as e:
            logger.debug(f"Network policy not found or already deleted: {e}")

    def respond_to_anomaly(self, pod_name: str, namespace: str, 
                          threat_signature: str, severity: str = 'medium') -> str:
        """
        Execute adaptive response to an anomaly.

        Args:
            pod_name: Name of the affected pod
            namespace: Kubernetes namespace
            threat_signature: Identifier of the threat
            severity: Severity level ('low', 'medium', 'high')

        Returns:
            Action taken ('isolate', 'restart', 'none')
        """
        # Check if we've seen this threat before
        memories = self.recall_memory(threat_signature)
        
        if memories:
            # Use adaptive response based on past success
            successful_responses = [m for m in memories if m.success]
            if successful_responses:
                action = successful_responses[-1].response_action
                logger.info(f"Using learned response for {threat_signature}: {action}")
            else:
                action = self._determine_action(severity)
        else:
            action = self._determine_action(severity)
        
        success = False
        if action == 'isolate':
            success = self.isolate_pod(pod_name, namespace)
        elif action == 'restart':
            success = self.restart_pod(pod_name, namespace)
        else:
            success = True  # 'none' action is always successful
            logger.info(f"No action taken for {namespace}/{pod_name}")
        
        # Store in memory
        self.add_memory(threat_signature, pod_name, namespace, action, success)
        
        return action

    def _determine_action(self, severity: str) -> str:
        """
        Determine appropriate action based on severity.

        Args:
            severity: Severity level

        Returns:
            Action to take
        """
        if severity == 'high':
            return 'isolate'
        elif severity == 'medium':
            return 'restart'
        else:
            return 'none'

    def get_quarantined_pods(self) -> List[str]:
        """Get list of currently quarantined pods"""
        return list(self.quarantined_pods)

    def get_memory_stats(self) -> Dict:
        """Get statistics about immune memory"""
        self._cleanup_old_memories()
        return {
            'total_memories': len(self.memory_cells),
            'quarantined_pods': len(self.quarantined_pods),
            'successful_responses': sum(1 for m in self.memory_cells if m.success),
            'failed_responses': sum(1 for m in self.memory_cells if not m.success)
        }
