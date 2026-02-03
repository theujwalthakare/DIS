# Digital Immune System (DIS) for Kubernetes

A research-grade Cognitive Overlay Digital Immune System that provides bio-inspired adaptive threat detection and response for Kubernetes clusters.

## Overview

DIS implements an artificial immune system architecture inspired by biological immunity, featuring:

- **aDC (artificial Dendritic Cell) Agents**: Per-node monitoring of CPU, memory, network, and pod events
- **T-Helper Layer**: Unsupervised ML-based anomaly detection using Isolation Forest and Autoencoder
- **B-Cell Memory Layer**: Adaptive immune responses with memory of past threats
- **Prometheus Integration**: Comprehensive metrics exposure
- **Chaos Mesh Support**: Built-in failure injection for testing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Node 1     │      │   Node 2     │                    │
│  │              │      │              │                    │
│  │  ┌────────┐  │      │  ┌────────┐  │                    │
│  │  │  aDC   │◄─┼──────┼─►│  aDC   │  │  (Per-node agents)│
│  │  │ Agent  │  │      │  │ Agent  │  │                    │
│  │  └───┬────┘  │      │  └───┬────┘  │                    │
│  └──────┼───────┘      └──────┼───────┘                    │
│         │                     │                             │
│         │   Antigens (Metrics)│                             │
│         ▼                     ▼                             │
│  ┌─────────────────────────────────────┐                   │
│  │        T-Helper Layer               │                   │
│  │  ┌─────────────┐  ┌──────────────┐ │                   │
│  │  │ Isolation   │  │ Autoencoder  │ │ (Anomaly Detection)│
│  │  │   Forest    │  │              │ │                   │
│  │  └─────────────┘  └──────────────┘ │                   │
│  └──────────────┬──────────────────────┘                   │
│                 │ Anomaly Detection                         │
│                 ▼                                           │
│  ┌─────────────────────────────────────┐                   │
│  │       B-Cell Memory Layer           │                   │
│  │  • Isolate Pods (Network Policy)    │  (Adaptive Response)│
│  │  • Restart Pods                     │                   │
│  │  • Memory of Past Threats           │                   │
│  └─────────────────────────────────────┘                   │
│                 │                                           │
│                 ▼                                           │
│         ┌──────────────┐                                    │
│         │  Prometheus  │  (Metrics & Monitoring)            │
│         └──────────────┘                                    │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. aDC (Artificial Dendritic Cell) Agents

- **Per-node deployment** via DaemonSet
- **Antigen collection**:
  - CPU usage (via psutil)
  - Memory usage (via psutil)
  - Network I/O metrics
  - Kubernetes pod events (ADDED, MODIFIED, DELETED)
- **Configurable collection interval**

### 2. T-Helper Layer (Anomaly Detection)

- **Isolation Forest**: Tree-based anomaly detection
  - Fast training and inference
  - Effective for high-dimensional data
  - Configurable contamination rate
  
- **Autoencoder**: Neural network-based detection
  - Detects anomalies via reconstruction error
  - Adaptive threshold based on training data
  - TensorFlow/Keras implementation

- **Ensemble Detection**: Consensus voting between detectors

### 3. B-Cell Memory Layer (Adaptive Response)

- **Threat Memory**: Stores past threats and successful responses
- **Adaptive Actions**:
  - **Isolate**: Apply network policy to quarantine pod
  - **Restart**: Delete pod (controller recreates it)
  - **None**: Log only for low-severity threats
- **Severity-based decision making**
- **Configurable memory retention period**

### 4. Prometheus Metrics

All metrics exposed on port 8000:

- `dis_antigens_collected_total`: Total antigens collected
- `dis_node_cpu_usage_percent`: CPU usage per node
- `dis_node_memory_usage_percent`: Memory usage per node
- `dis_anomalies_detected_total`: Anomalies detected
- `dis_responses_executed_total`: Immune responses executed
- `dis_quarantined_pods_current`: Currently quarantined pods
- `dis_memory_cells_total`: Total immune memory cells

## Installation

### Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Docker for building images
- (Optional) Chaos Mesh for failure injection

### Quick Start

1. **Clone the repository**:
```bash
git clone https://github.com/theujwalthakare/DIS.git
cd DIS
```

2. **Build the Docker image**:
```bash
docker build -t dis-kubernetes:latest .
```

3. **Deploy to Kubernetes**:
```bash
# Apply manifests in order
kubectl apply -f k8s/manifests/00-namespace.yaml
kubectl apply -f k8s/manifests/01-rbac.yaml
kubectl apply -f k8s/manifests/02-configmap.yaml
kubectl apply -f k8s/manifests/03-daemonset.yaml
kubectl apply -f k8s/manifests/04-service.yaml
kubectl apply -f k8s/manifests/05-servicemonitor.yaml
```

4. **Verify deployment**:
```bash
kubectl get pods -n dis-system
kubectl logs -n dis-system -l app=dis-agent
```

5. **Access metrics**:
```bash
kubectl port-forward -n dis-system svc/dis-metrics 8000:8000
# Visit http://localhost:8000/metrics
```

## Configuration

Edit `config/dis-config.yaml` or the ConfigMap to customize:

```yaml
adc:
  collect_interval: 10  # seconds

thelper:
  use_isolation_forest: true
  use_autoencoder: true
  detection_interval: 30  # seconds
  
bcell:
  memory_retention_hours: 24
  
prometheus:
  port: 8000
```

## Testing with Chaos Mesh

1. **Install Chaos Mesh**:
```bash
curl -sSL https://mirrors.chaos-mesh.org/v2.5.0/install.sh | bash
```

2. **Deploy test application**:
```bash
kubectl apply -f k8s/examples/test-app.yaml
```

3. **Run chaos experiments**:
```bash
# CPU stress test
kubectl apply -f k8s/chaos-mesh/experiments.yaml
```

4. **Monitor DIS response**:
```bash
kubectl logs -n dis-system -l app=dis-agent -f
```

## Development

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=dis --cov-report=html
```

### Project Structure

```
DIS/
├── src/dis/                    # Source code
│   ├── adc/                    # aDC agent implementation
│   ├── thelper/                # T-Helper ML models
│   ├── bcell/                  # B-Cell memory layer
│   ├── prometheus_metrics/     # Metrics exporter
│   ├── orchestrator.py         # Main orchestrator
│   └── main.py                 # Entry point
├── k8s/                        # Kubernetes manifests
│   ├── manifests/              # DIS deployment
│   ├── chaos-mesh/             # Chaos experiments
│   └── examples/               # Example applications
├── config/                     # Configuration files
├── tests/                      # Unit tests
├── Dockerfile                  # Container image
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Research & Publications

This implementation is designed for research in:

- Autonomous cybersecurity systems
- Bio-inspired computing
- Adaptive threat detection
- Self-healing systems
- Chaos engineering

### Key Concepts

1. **Cognitive Overlay**: DIS operates as an overlay system, monitoring without modifying application code
2. **Artificial Immunity**: Inspired by biological immune systems (innate + adaptive)
3. **Unsupervised Learning**: No labeled training data required
4. **Adaptive Response**: System learns from past threats
5. **Reproducibility**: Deterministic behavior for research validation

## Performance Considerations

- **Resource Usage**: ~256MB RAM, 100m CPU per node (configurable)
- **Metric Collection**: Every 10 seconds (configurable)
- **Anomaly Detection**: Every 30 seconds (configurable)
- **Training Time**: ~5 minutes with 300 seconds of baseline data
- **Response Latency**: <1 second for pod isolation/restart

## Troubleshooting

### DIS agents not starting
```bash
kubectl describe pods -n dis-system
kubectl logs -n dis-system <pod-name>
```

### Metrics not appearing
- Check Prometheus ServiceMonitor configuration
- Verify port 8000 is accessible
- Check firewall rules

### Models not training
- Ensure sufficient baseline data collection period
- Check for metric collection errors in logs
- Verify psutil can access system metrics

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Citation

If you use this work in research, please cite:

```
@software{dis_kubernetes,
  author = {DIS Team},
  title = {Digital Immune System for Kubernetes},
  year = {2024},
  url = {https://github.com/theujwalthakare/DIS}
}
```

## Contact

For questions or collaboration: [GitHub Issues](https://github.com/theujwalthakare/DIS/issues)
