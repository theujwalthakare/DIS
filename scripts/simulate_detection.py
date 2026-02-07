"""
DIS (Distributed Intrusion System) - Real-time Detection Simulator

This script simulates the end-to-end detection and response pipeline:
1. Loads trained ML models (IsolationForest, Autoencoder)
2. Processes streaming metrics data from Kubernetes pods
3. Computes anomaly scores using ensemble detection
4. Triggers B-Cell responses based on detection confidence
5. Integrates with controller for automated remediation

Usage examples:
  # Basic detection simulation with default models
  python scripts/simulate_detection.py --label app=example-app
  
  # Use specific models and custom threshold
  python scripts/simulate_detection.py --label app=example-app --iforest ml/models/iforest.joblib --autoencoder ml/models/ae_sklearn.joblib --threshold 0.6
  
  # High-frequency monitoring mode
  python scripts/simulate_detection.py --label app=example-app --interval 1 --continuous

Features:
- Multi-model ensemble detection (IsolationForest + Autoencoder)
- Real-time metrics processing from 100k-trained models
- Kubernetes integration for pod monitoring and response
- Configurable detection thresholds and response actions
- Comprehensive logging and performance metrics
"""
import argparse
import csv
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import joblib
    import numpy as np
    import pandas as pd
except ImportError as e:
    print(f"ERROR: Required packages not available: {e}")
    print("Install with: pip install scikit-learn pandas numpy")
    sys.exit(1)

try:
    from kubernetes import client, config
    KUBERNETES_AVAILABLE = True
except ImportError:
    client = None
    config = None
    KUBERNETES_AVAILABLE = False
    print("WARNING: Kubernetes client not available - using simulation mode")

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from controller.controller import DecisionEngine, bcell_apply
    CONTROLLER_AVAILABLE = True
except ImportError:
    CONTROLLER_AVAILABLE = False
    print("WARNING: Controller module not available - using fallback mode")
    
    class DecisionEngine:
        def __init__(self, *args, **kwargs):
            self.models = {}
            
        def score(self, features):
            return {'fallback': 0.5}
            
        def decide_response(self, scores):
            return 'monitor'
    
    def bcell_apply(action, pod_name, namespace='default'):
        print(f"[B-Cell Fallback] Action: {action} -> Pod: {pod_name} (Namespace: {namespace})")

# Standard feature columns matching the 100k dataset
FEATURE_COLUMNS = [
    'cpu_percent', 'mem_percent', 'net_tx', 'net_rx',
    'disk_read', 'disk_write', 'http_req_rate', 'response_ms'
]

class DISDetectionEngine:
    """Enhanced detection engine supporting multiple models and ensemble scoring."""
    
    def __init__(self, iforest_path=None, autoencoder_path=None, threshold=0.5):
        self.models = {}
        self.threshold = threshold
        self.feature_columns = FEATURE_COLUMNS
        
        # Load models
        self._load_models(iforest_path, autoencoder_path)
        
    def _load_models(self, iforest_path, autoencoder_path):
        """Load trained ML models with fallback paths."""
        # IsolationForest
        if iforest_path and os.path.exists(iforest_path):
            try:
                self.models['iforest'] = joblib.load(iforest_path)
                print(f"✓ Loaded IsolationForest from {iforest_path}")
            except Exception as e:
                print(f"WARNING: Failed to load IsolationForest: {e}")
        else:
            # Try fallback paths
            fallback_paths = ['ml/models/iforest.joblib', 'models/iforest.joblib']
            for path in fallback_paths:
                if os.path.exists(path):
                    try:
                        self.models['iforest'] = joblib.load(path)
                        print(f"✓ Loaded IsolationForest from {path}")
                        break
                    except Exception as e:
                        continue
        
        # Autoencoder
        if autoencoder_path and os.path.exists(autoencoder_path):
            try:
                self.models['autoencoder'] = joblib.load(autoencoder_path)
                print(f"✓ Loaded Autoencoder from {autoencoder_path}")
            except Exception as e:
                print(f"WARNING: Failed to load Autoencoder: {e}")
        else:
            # Try fallback paths
            fallback_paths = ['ml/models/ae_sklearn.joblib', 'models/ae_sklearn.joblib']
            for path in fallback_paths:
                if os.path.exists(path):
                    try:
                        self.models['autoencoder'] = joblib.load(path)
                        print(f"✓ Loaded Autoencoder from {path}")
                        break
                    except Exception as e:
                        continue
        
        if not self.models:
            print("WARNING: No models loaded - detection will use fallback scoring")
    
    def extract_features(self, data_row: Dict) -> Optional[np.ndarray]:
        """Extract feature vector from metrics data row."""
        try:
            features = []
            for col in self.feature_columns:
                if col in data_row:
                    features.append(float(data_row[col]))
                else:
                    # Use reasonable defaults for missing features
                    defaults = {
                        'cpu_percent': 5.0, 'mem_percent': 20.0,
                        'net_tx': 50.0, 'net_rx': 60.0,
                        'disk_read': 10.0, 'disk_write': 8.0,
                        'http_req_rate': 30.0, 'response_ms': 100.0
                    }
                    features.append(defaults.get(col, 0.0))
            
            return np.array(features).reshape(1, -1)
        except Exception as e:
            print(f"ERROR: Feature extraction failed: {e}")
            return None
    
    def compute_anomaly_scores(self, features: np.ndarray) -> Dict[str, float]:
        """Compute anomaly scores using available models."""
        scores = {}
        
        # IsolationForest scoring (lower = more anomalous)
        if 'iforest' in self.models:
            try:
                if_score = self.models['iforest'].decision_function(features)[0]
                # Convert to 0-1 scale (higher = more anomalous)
                scores['iforest'] = max(0, -if_score / 2 + 0.5)
            except Exception as e:
                print(f"WARNING: IsolationForest scoring failed: {e}")
        
        # Autoencoder scoring (reconstruction error)
        if 'autoencoder' in self.models:
            try:
                # For sklearn MLPRegressor autoencoder
                reconstruction = self.models['autoencoder'].predict(features)
                mse = np.mean((features - reconstruction) ** 2)
                # Normalize to 0-1 scale
                scores['autoencoder'] = min(1.0, mse / 100.0)
            except Exception as e:
                print(f"WARNING: Autoencoder scoring failed: {e}")
        
        # Ensemble score (weighted average)
        if len(scores) > 1:
            # Weight IsolationForest higher based on evaluation results
            ensemble_score = (0.7 * scores.get('iforest', 0)) + (0.3 * scores.get('autoencoder', 0))
            scores['ensemble'] = ensemble_score
        elif len(scores) == 1:
            scores['ensemble'] = list(scores.values())[0]
        else:
            # Fallback random scoring for demonstration
            scores['fallback'] = random.uniform(0, 1)
            scores['ensemble'] = scores['fallback']
        
        return scores
    
    def decide_action(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """Decide response action based on ensemble score."""
        ensemble_score = scores.get('ensemble', 0.0)
        
        if ensemble_score >= 0.8:
            return 'isolate', ensemble_score
        elif ensemble_score >= 0.6:
            return 'restart', ensemble_score
        elif ensemble_score >= self.threshold:
            return 'investigate', ensemble_score
        else:
            return 'monitor', ensemble_score


def load_latest_metrics(data_path='data/metrics.csv', sample_random=False) -> Optional[Dict]:
    """Load the latest metrics from the dataset."""
    if not os.path.exists(data_path):
        print(f"WARNING: Metrics file not found: {data_path}")
        return None
    
    try:
        df = pd.read_csv(data_path)
        if df.empty:
            print("WARNING: Metrics file is empty")
            return None
            
        # Get latest sample or random sample for simulation
        if sample_random:
            idx = random.randint(0, len(df) - 1)
            sample = df.iloc[idx]
            print(f"Using random sample #{idx} for simulation")
        else:
            sample = df.iloc[-1]
            print(f"Using latest sample from dataset")
        
        return sample.to_dict()
        
    except Exception as e:
        print(f"ERROR: Failed to load metrics: {e}")
        return None


def find_kubernetes_pods(label_selector: str, namespace: str = 'default') -> List[str]:
    """Find Kubernetes pods matching the label selector."""
    if not KUBERNETES_AVAILABLE:
        print('[Simulation] Kubernetes not available - returning mock pods')
        return ['example-pod-1', 'example-pod-2']
    
    try:
        # Try to load cluster config first, then kube config
        try:
            config.load_incluster_config()
            print("✓ Loaded in-cluster Kubernetes config")
        except:
            config.load_kube_config()
            print("✓ Loaded local Kubernetes config")
    
    except Exception as e:
        print(f'WARNING: Could not load Kubernetes config: {e}')
        return ['mock-pod']

    try:
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        pod_names = [pod.metadata.name for pod in pods.items if pod.status.phase == 'Running']
        
        if not pod_names:
            print(f'WARNING: No running pods found for label {label_selector} in {namespace}')
            return ['mock-pod']
            
        print(f"✓ Found {len(pod_names)} running pods")
        return pod_names
        
    except Exception as e:
        print(f'ERROR: Failed to query pods: {e}')
        return ['mock-pod']


def execute_detection_simulation(args):
    """Main detection simulation logic."""
    print("="*80)
    print("DIS DETECTION SIMULATION")
    print("="*80)
    
    # Initialize detection engine
    detection_engine = DISDetectionEngine(
        iforest_path=args.iforest,
        autoencoder_path=args.autoencoder,
        threshold=args.threshold
    )
    
    # Load metrics data
    metrics = load_latest_metrics(args.data, sample_random=args.random_sample)
    if metrics is None:
        print("ERROR: Cannot proceed without metrics data")
        sys.exit(1)
    
    # Extract features
    features = detection_engine.extract_features(metrics)
    if features is None:
        print("ERROR: Feature extraction failed")
        sys.exit(1)
        
    print(f"✓ Extracted {len(FEATURE_COLUMNS)} features from metrics")
    
    # Compute anomaly scores
    scores = detection_engine.compute_anomaly_scores(features)
    print(f"Anomaly Scores: {scores}")
    
    # Decide action
    action, confidence = detection_engine.decide_action(scores)
    print(f"Decision: {action.upper()} (confidence: {confidence:.3f})")
    
    # Find target pods
    pods = find_kubernetes_pods(args.label, args.namespace)
    target_pod = pods[0] if pods else 'mock-pod'
    
    # Execute response action
    print(f"\nExecuting response on pod: {target_pod}")
    if CONTROLLER_AVAILABLE:
        bcell_apply(action, target_pod, namespace=args.namespace)
    else:
        print(f"[Simulation] B-Cell Action: {action} -> {target_pod} (namespace: {args.namespace})")
    
    # Log detection event
    log_detection_event(target_pod, metrics, scores, action, confidence)
    
    print("\n" + "="*80)
    print("DETECTION SIMULATION COMPLETE")
    print("="*80)
    
    return scores, action, confidence


def log_detection_event(pod_name: str, metrics: Dict, scores: Dict, action: str, confidence: float):
    """Log detection event for analysis and debugging."""
    log_entry = {
        'timestamp': time.time(),
        'pod_name': pod_name,
        'action': action,
        'confidence': confidence,
        'scores': scores,
        'metrics_sample': {k: v for k, v in metrics.items() if k in FEATURE_COLUMNS}
    }
    
    # Append to detection log
    log_file = 'results/detection_events.json'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    try:
        # Load existing logs
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        # Keep only last 1000 events
        logs = logs[-1000:]
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
        print(f"✓ Detection event logged to {log_file}")
        
    except Exception as e:
        print(f"WARNING: Failed to log detection event: {e}")


def continuous_monitoring(args):
    """Run continuous detection monitoring."""
    print(f"Starting continuous monitoring (interval: {args.interval}s)")
    print("Press Ctrl+C to stop")
    
    detection_count = 0
    anomaly_count = 0
    
    try:
        while True:
            print(f"\n--- Detection Cycle #{detection_count + 1} ---")
            
            scores, action, confidence = execute_detection_simulation(args)
            detection_count += 1
            
            if action != 'monitor':
                anomaly_count += 1
                
            print(f"Summary: {detection_count} detections, {anomaly_count} anomalies")
            
            if not args.continuous:
                break
                
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print(f"\nMonitoring stopped. Final stats: {detection_count} detections, {anomaly_count} anomalies")


def main():
    """Main entry point for detection simulation."""
    parser = argparse.ArgumentParser(
        description='DIS Detection Simulation - Real-time anomaly detection and response',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic single detection
  python scripts/simulate_detection.py
  
  # Target specific pods with custom threshold
  python scripts/simulate_detection.py --label app=web-server --threshold 0.7
  
  # Continuous monitoring mode
  python scripts/simulate_detection.py --continuous --interval 5
  
  # Use specific models
  python scripts/simulate_detection.py --iforest ml/models/iforest.joblib --autoencoder ml/models/ae_sklearn.joblib
        """
    )
    
    # Model configuration
    parser.add_argument('--iforest', default='ml/models/iforest.joblib',
                       help='Path to IsolationForest model file')
    parser.add_argument('--autoencoder', default='ml/models/ae_sklearn.joblib',
                       help='Path to Autoencoder model file')
    parser.add_argument('--threshold', type=float, default=0.5,
                       help='Anomaly detection threshold (0.0-1.0)')
    
    # Data configuration
    parser.add_argument('--data', default='data/metrics.csv',
                       help='Path to metrics data file')
    parser.add_argument('--random-sample', action='store_true',
                       help='Use random sample instead of latest metrics')
    
    # Kubernetes configuration
    parser.add_argument('--label', default='app=example-app',
                       help='Pod label selector for targeting')
    parser.add_argument('--namespace', default='default',
                       help='Kubernetes namespace')
    
    # Execution mode
    parser.add_argument('--continuous', action='store_true',
                       help='Run in continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=30,
                       help='Interval between detections (seconds)')
    
    args = parser.parse_args()
    
    # Validation
    if args.threshold < 0.0 or args.threshold > 1.0:
        print("ERROR: Threshold must be between 0.0 and 1.0")
        sys.exit(1)
    
    if args.interval < 1:
        print("ERROR: Interval must be at least 1 second")
        sys.exit(1)
    
    # Execute simulation
    if args.continuous:
        continuous_monitoring(args)
    else:
        execute_detection_simulation(args)


if __name__ == '__main__':
    main()
