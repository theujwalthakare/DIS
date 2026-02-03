"""
DIS Orchestrator
================

Main orchestrator that coordinates all DIS components.
"""

import logging
import time
import numpy as np
import threading
from typing import Dict, List, Optional
import hashlib

from dis_k8s.adc import ArtificialDendriticCell, Antigen
from dis_k8s.thelper import THelperLayer
from dis_k8s.bcell import BCellMemoryLayer
from dis_k8s.prometheus_metrics import DISMetrics

logger = logging.getLogger(__name__)


class DISOrchestrator:
    """
    Main orchestrator for the Digital Immune System.
    Coordinates aDC agents, T-Helper layer, and B-Cell responses.
    """

    def __init__(self, node_name: str, config: Optional[Dict] = None):
        """
        Initialize DIS orchestrator.

        Args:
            node_name: Name of the Kubernetes node
            config: Configuration dictionary
        """
        self.node_name = node_name
        self.config = config or self._default_config()
        
        # Initialize components
        self.adc = ArtificialDendriticCell(
            node_name=node_name,
            collect_interval=self.config['adc']['collect_interval']
        )
        
        self.thelper = THelperLayer(
            use_isolation_forest=self.config['thelper']['use_isolation_forest'],
            use_autoencoder=self.config['thelper']['use_autoencoder'],
            input_dim=self.config['thelper']['input_dim']
        )
        
        self.bcell = BCellMemoryLayer(
            memory_retention_hours=self.config['bcell']['memory_retention_hours']
        )
        
        self.metrics = DISMetrics()
        
        self.is_trained = False
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        logger.info(f"DIS Orchestrator initialized for node: {node_name}")

    def _default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'adc': {
                'collect_interval': 10
            },
            'thelper': {
                'use_isolation_forest': True,
                'use_autoencoder': True,
                'input_dim': 4,
                'training_samples': 1000,
                'detection_interval': 30
            },
            'bcell': {
                'memory_retention_hours': 24
            },
            'prometheus': {
                'port': 8000
            }
        }

    def train_models(self, training_duration_seconds: int = 300):
        """
        Train ML models with collected baseline data.

        Args:
            training_duration_seconds: Duration to collect training data
        """
        logger.info("Starting training phase...")
        
        # Collect baseline data
        training_data = []
        start_time = time.time()
        
        while time.time() - start_time < training_duration_seconds:
            antigens = self.adc.collect_all_metrics()
            
            # Convert to feature vector
            features = self._antigens_to_features(antigens)
            if features is not None:
                training_data.append(features)
            
            # Update metrics
            for antigen in antigens:
                self.metrics.record_antigen(antigen.node_name, antigen.metric_type)
                self._update_metrics_from_antigen(antigen)
            
            time.sleep(self.config['adc']['collect_interval'])
        
        # Train T-Helper models
        if training_data:
            training_array = np.array(training_data)
            logger.info(f"Training models with {len(training_data)} samples...")
            self.thelper.train(training_array)
            self.is_trained = True
            logger.info("Training completed successfully")
        else:
            logger.error("No training data collected")

    def _antigens_to_features(self, antigens: List[Antigen]) -> Optional[np.ndarray]:
        """
        Convert antigens to feature vector for ML models.

        Args:
            antigens: List of antigens

        Returns:
            Feature vector [cpu, memory, network, pod_events]
        """
        if not antigens:
            return None
            
        features = {
            'cpu': 0.0,
            'memory': 0.0,
            'network': 0.0,
            'pod_event': 0.0
        }
        
        for antigen in antigens:
            if antigen.metric_type in features:
                features[antigen.metric_type] = antigen.value
        
        return np.array([
            features['cpu'],
            features['memory'],
            features['network'],
            features['pod_event']
        ])

    def _update_metrics_from_antigen(self, antigen: Antigen):
        """Update Prometheus metrics from antigen"""
        if antigen.metric_type == 'cpu':
            self.metrics.update_cpu_usage(antigen.node_name, antigen.value)
        elif antigen.metric_type == 'memory':
            self.metrics.update_memory_usage(antigen.node_name, antigen.value)
        elif antigen.metric_type == 'network':
            self.metrics.update_network_bytes(antigen.node_name, antigen.value)

    def _compute_threat_signature(self, features: np.ndarray) -> str:
        """
        Compute a hash signature for a threat pattern.

        Args:
            features: Feature vector

        Returns:
            Threat signature (hash)
        """
        # Round features to reduce noise
        rounded = np.round(features, decimals=1)
        signature = hashlib.md5(rounded.tobytes()).hexdigest()
        return signature

    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting monitoring loop...")
        
        while self.running:
            try:
                # Collect antigens
                antigens = self.adc.collect_all_metrics()
                
                # Update metrics
                for antigen in antigens:
                    self.metrics.record_antigen(antigen.node_name, antigen.metric_type)
                    self._update_metrics_from_antigen(antigen)
                
                # Detect anomalies if trained
                if self.is_trained:
                    features = self._antigens_to_features(antigens)
                    if features is not None:
                        features_reshaped = features.reshape(1, -1)
                        
                        # Detect anomalies
                        start_detect = time.time()
                        anomalies = self.thelper.detect_anomalies(features_reshaped)
                        detect_duration = time.time() - start_detect
                        
                        self.metrics.record_detection_time('ensemble', detect_duration)
                        
                        # If anomaly detected, trigger response
                        if anomalies[0]:
                            logger.warning("Anomaly detected!")
                            self.metrics.record_anomaly('ensemble', self.node_name)
                            
                            # Determine severity (simple heuristic)
                            severity = self._compute_severity(features)
                            
                            # Compute threat signature
                            threat_sig = self._compute_threat_signature(features)
                            
                            # Trigger B-Cell response
                            # Note: In real scenario, would identify specific pod
                            # For now, we log the anomaly
                            logger.info(f"Threat signature: {threat_sig}, severity: {severity}")
                            
                # Update B-Cell metrics
                stats = self.bcell.get_memory_stats()
                self.metrics.update_memory_cells(stats['total_memories'])
                self.metrics.update_quarantined_pods(stats['quarantined_pods'])
                
                time.sleep(self.config['thelper']['detection_interval'])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(5)

    def _compute_severity(self, features: np.ndarray) -> str:
        """
        Compute severity based on feature values.

        Args:
            features: Feature vector

        Returns:
            Severity level ('low', 'medium', 'high')
        """
        max_value = np.max(features)
        
        if max_value > 90:
            return 'high'
        elif max_value > 75:
            return 'medium'
        else:
            return 'low'

    def start(self, start_metrics_server: bool = True):
        """
        Start the DIS system.

        Args:
            start_metrics_server: Whether to start Prometheus metrics server
        """
        if not self.is_trained:
            logger.warning("Models not trained. Run train_models() first.")
            return
        
        # Start metrics server
        if start_metrics_server:
            self.metrics.start_server(self.config['prometheus']['port'])
        
        # Start monitoring loop
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("DIS system started successfully")

    def stop(self):
        """Stop the DIS system"""
        logger.info("Stopping DIS system...")
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        logger.info("DIS system stopped")

    def save_models(self, path: str):
        """Save trained models"""
        self.thelper.save_models(path)
        logger.info(f"Models saved to {path}")

    def load_models(self, path: str):
        """Load trained models"""
        self.thelper.load_models(path)
        self.is_trained = True
        logger.info(f"Models loaded from {path}")
