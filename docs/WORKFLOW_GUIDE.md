# DIS Experimental Workflow Guide

## Table of Contents
1. [Overview](#overview)
2. [Data Flow Architecture](#data-flow-architecture)
3. [Technologies Used](#technologies-used)
4. [Experimental Workflow](#experimental-workflow)
5. [Step-by-Step Manual](#step-by-step-manual)
6. [File Structure](#file-structure)

---

## Overview

This repository implements a **Cognitive Overlay Digital Immune System (DIS)** for Kubernetes-based microservices, inspired by biological immune system principles. The experiment validates anomaly detection and automated response capabilities using unsupervised machine learning.

### Research Objectives
- Design and implement immune-inspired anomaly detection for cloud-native applications
- Evaluate detection accuracy using synthetic metrics with labeled anomalies
- Demonstrate automated response mechanisms (pod isolation, restart, rollout)
- Provide reproducible experimental framework for research publication

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA GENERATION PHASE                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    scripts/generate_metrics.py
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  data/metrics.csv        │
                    │  (970 samples, 9 features)│
                    │  - Normal: 700 samples   │
                    │  - Anomalies: 270 samples│
                    │  - Ground truth labels   │
                    └──────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────┐
│                    TRAINING PHASE (T-Helper Layer)                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
    ┌───────────────────────────┐   ┌──────────────────────────┐
    │ Isolation Forest          │   │ Sklearn Autoencoder      │
    │ ml/train_isolation_forest │   │ ml/train_autoencoder_skl │
    └───────────────────────────┘   └──────────────────────────┘
                    │                           │
                    ▼                           ▼
         ml/models/iforest.joblib    ml/models/ae_sklearn.joblib
                    │                           │
┌───────────────────┴───────────────────────────┴───────────────────┐
│              DEPLOYMENT PHASE (Kubernetes Cluster)                │
└───────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
    ┌───────────────────────────┐   ┌──────────────────────────┐
    │ ADC Agent (DaemonSet)     │   │ Example Application      │
    │ agents/adc_agent.py       │   │ cluster/example-deploy   │
    │ Collects node metrics     │   │ nginx workload           │
    └───────────────────────────┘   └──────────────────────────┘
                    │                           │
                    ▼                           │
    ┌───────────────────────────┐               │
    │ Metrics Endpoint          │               │
    │ :8000/metrics (JSON)      │               │
    └───────────────────────────┘               │
                    │                           │
┌───────────────────┴───────────────────────────┴───────────────────┐
│           DETECTION PHASE (T-Helper Decision Layer)               │
└───────────────────────────────────────────────────────────────────┘
                                  │
                    scripts/simulate_detection.py
                    (Runs as Kubernetes Job)
                                  │
                    ┌─────────────┴─────────────┐
                    │ Load trained models       │
                    │ Fetch metrics from agent  │
                    │ Score with IF & AE        │
                    │ Aggregate anomaly scores  │
                    └───────────────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Anomaly Score >= Threshold│
                    │ controller/controller.py  │
                    └───────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────┐
│              RESPONSE PHASE (B-Cell Effector Layer)                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
    ┌───────────────────────────┐   ┌──────────────────────────┐
    │ bcell_isolate()           │   │ bcell_restart()          │
    │ Adds quarantine label     │   │ Deletes anomalous pod    │
    └───────────────────────────┘   └──────────────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ bcell_rollout_restart()   │
                    │ Triggers deployment update│
                    └───────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────┐
│                  ANALYSIS PHASE (Evaluation)                        │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    analysis/plot_detection.py
                                  │
                    ┌─────────────┴─────────────┐
                    │ Load metrics & models     │
                    │ Compute anomaly scores    │
                    │ Generate visualizations   │
                    └───────────────────────────┘
                                  │
                                  ▼
                    results/figures/
                    ├── timeseries_scores.png
                    ├── iforest_histogram.png
                    └── ae_sklearn_histogram.png
```

---

## Technologies Used

### Core Technologies

| Technology | Version | Purpose | Component |
|------------|---------|---------|-----------|
| **Python** | 3.11/3.14 | Primary language | All modules |
| **Kubernetes** | 1.28+ | Orchestration platform | Deployment runtime |
| **Docker** | 24.0+ | Containerization | Image builds |
| **scikit-learn** | 1.8.0 | Machine learning | Isolation Forest, Autoencoder |
| **TensorFlow** | 2.12.0 | Deep learning (optional) | Keras Autoencoder |
| **Chaos Mesh** | 2.6+ | Fault injection | Chaos experiments |

### Python Libraries

**Machine Learning & Data Processing:**
- `scikit-learn`: Isolation Forest, MLPRegressor autoencoder, preprocessing
- `pandas`: Data loading, CSV manipulation
- `numpy`: Numerical operations, array processing
- `joblib`: Model serialization

**Kubernetes Integration:**
- `kubernetes`: Python client for K8s API operations
- Pod management, deployment manipulation, label patching

**Monitoring & Metrics:**
- `psutil`: System metrics collection (CPU, memory, disk, network)
- `prometheus-client`: Metrics exposition (optional)

**Visualization:**
- `matplotlib`: Figure generation, histograms, timeseries plots

**Container Base Images:**
- `tensorflow/tensorflow:2.12.0`: TensorFlow-enabled trainer image
- `python:3.11-slim`: Lightweight production images

### Infrastructure Components

**Kubernetes Resources:**
- **DaemonSet**: ADC agent on every node
- **Deployment**: Example application workload
- **Job**: In-cluster detection simulator
- **Service**: Exposes example application
- **ServiceAccount + RBAC**: Permissions for agents and controllers

**Chaos Engineering:**
- **PodChaos**: Pod kill injection
- **StressChaos**: CPU stress injection

---

## Experimental Workflow

### Phase 1: Data Generation
```bash
# Generate synthetic metrics with labeled anomalies
.venv\Scripts\python.exe scripts\generate_metrics.py
```

**Output:** `data/metrics.csv` (970 samples, 9 features, ground truth labels)

**Features Generated:**
- `cpu_percent`: CPU utilization (0-100%)
- `mem_percent`: Memory utilization (0-100%)
- `net_tx`, `net_rx`: Network transmit/receive (MB/s)
- `disk_read`, `disk_write`: Disk I/O (MB/s)
- `http_req_rate`: HTTP requests per second
- `response_ms`: Response latency (milliseconds)
- `pod_restarts`: Number of pod restarts
- `label`: Ground truth (0=normal, 1=anomaly)

**Anomaly Patterns:**
1. **CPU Spike** (50 samples): 80-98% CPU
2. **Memory Leak** (80 samples): Gradual ramp to 92%
3. **Network Congestion** (60 samples): 2000-8000 MB/s
4. **Pod Crashes** (40 samples): High restarts, low metrics
5. **Disk I/O Saturation** (40 samples): 500-2000 MB/s

---

### Phase 2: Model Training
```bash
# Train Isolation Forest (unsupervised anomaly detection)
.venv\Scripts\python.exe ml\train_isolation_forest.py \
  --input data\metrics.csv \
  --out ml\models\iforest.joblib

# Train sklearn autoencoder (reconstruction-based detection)
.venv\Scripts\python.exe ml\train_autoencoder_sklearn.py \
  --input data\metrics.csv \
  --out ml\models\ae_sklearn.joblib
```

**Models:**
- **Isolation Forest**: Tree-based outlier detection (889KB)
- **Sklearn Autoencoder**: Neural network reconstruction error (49KB)

**Training Configuration:**
- Contamination: `auto` (automatically estimate anomaly ratio)
- Features: 9 (label column excluded)
- Samples: 970

---

### Phase 3: Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f cluster/adc-agent-sa.yaml
kubectl apply -f cluster/agent-daemonset.yaml
kubectl apply -f cluster/example-deployment.yaml
kubectl apply -f cluster/simulate-rbac.yaml
```

**Deployed Components:**
- **ADC Agent**: Runs on each node, exposes metrics at `:8000/metrics`
- **Example App**: nginx-based workload for monitoring
- **ServiceAccounts**: RBAC permissions for agents and simulators

---

### Phase 4: Detection Simulation
```bash
# Build detection container
docker build -f Dockerfile.tfbase -t dis-autoencoder:tfbase .

# Run detection job
kubectl apply -f cluster/simulate-detection-job.yaml

# View logs
kubectl logs job/simulate-detection
```

**Detection Logic:**
1. Load trained models from container image
2. Find target pod by label selector
3. Fetch metrics from ADC agent
4. Score with Isolation Forest and Autoencoder
5. Aggregate scores and compare to threshold
6. Call B-Cell response if anomaly detected

---

### Phase 5: Chaos Injection (Optional)
```bash
# Apply chaos experiments
kubectl apply -f chaos/pod-kill.yaml
kubectl apply -f chaos/cpu-stress.yaml
```

**Chaos Types:**
- **Pod Kill**: Randomly kill pods matching `app=example-app`
- **CPU Stress**: Inject 2 CPU stressors into target pods

---

### Phase 6: Response Actions
**B-Cell Effector Functions (in `controller/controller.py`):**

```python
# Isolate: Add quarantine label
bcell_isolate(pod_name, namespace)
# Result: Pod labeled "dis-status=quarantine"

# Restart: Delete pod (K8s recreates)
bcell_restart(pod_name, namespace)
# Result: Pod deleted, ReplicaSet creates new pod

# Rollout Restart: Trigger deployment update
bcell_rollout_restart(pod_name, namespace)
# Result: Deployment rolling restart initiated
```

---

### Phase 7: Analysis & Visualization
```bash
# Generate evaluation figures
.venv\Scripts\python.exe analysis\plot_detection.py
```

**Output Figures (in `results/figures/`):**
- **timeseries_scores.png**: Anomaly scores over time
- **iforest_histogram.png**: Isolation Forest score distribution
- **ae_sklearn_histogram.png**: Autoencoder reconstruction error distribution

---

## Step-by-Step Manual

### Prerequisites
1. **Python 3.11+** with virtual environment
2. **Docker Desktop** with Kubernetes enabled (or minikube/kind)
3. **kubectl** configured with cluster access
4. **Git** for repository cloning

### Setup Instructions

#### 1. Clone Repository
```bash
git clone <repo-url>
cd DIS
```

#### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Generate Synthetic Data
```bash
python scripts/generate_metrics.py
```
✅ **Verify:** `data/metrics.csv` created with 971 lines

#### 5. Train Models
```bash
# Option A: Train individually
python ml/train_isolation_forest.py --input data/metrics.csv --out ml/models/iforest.joblib
python ml/train_autoencoder_sklearn.py --input data/metrics.csv --out ml/models/ae_sklearn.joblib

# Option B: Use automation script (trains + deploys)
.\scripts\run_experiment.ps1
```
✅ **Verify:** Models in `ml/models/` directory

#### 6. Build Docker Image
```bash
docker build -f Dockerfile.tfbase -t dis-autoencoder:tfbase .
```
✅ **Verify:** `docker images | grep dis-autoencoder`

#### 7. Deploy to Kubernetes
```bash
# Apply manifests in order
kubectl apply -f cluster/adc-agent-sa.yaml
kubectl apply -f cluster/agent-daemonset.yaml
kubectl apply -f cluster/example-deployment.yaml
kubectl apply -f cluster/simulate-rbac.yaml

# Verify deployments
kubectl get pods
kubectl get daemonset
```
✅ **Expected:** All pods in `Running` state

#### 8. Run Detection Job
```bash
kubectl apply -f cluster/simulate-detection-job.yaml
kubectl wait --for=condition=complete job/simulate-detection --timeout=120s
kubectl logs job/simulate-detection
```
✅ **Expected:** Detection logs showing anomaly scores

#### 9. Generate Analysis Figures
```bash
python analysis/plot_detection.py
```
✅ **Verify:** Three PNG files in `results/figures/`

#### 10. View Results
```bash
# Open figures
start results\figures\timeseries_scores.png  # Windows
open results/figures/timeseries_scores.png   # Mac
xdg-open results/figures/timeseries_scores.png  # Linux
```

---

## File Structure

### Essential Files

```
DIS/
├── agents/
│   ├── adc_agent.py          # Artificial Dendritic Cell (metrics collector)
│   └── requirements.txt      # Agent dependencies
├── analysis/
│   └── plot_detection.py     # Visualization script
├── chaos/
│   ├── cpu-stress.yaml       # CPU stress chaos experiment
│   └── pod-kill.yaml         # Pod kill chaos experiment
├── cluster/
│   ├── adc-agent-sa.yaml     # ServiceAccount for ADC agent
│   ├── agent-daemonset.yaml  # DaemonSet for ADC deployment
│   ├── example-deployment.yaml  # Example workload
│   ├── simulate-detection-job.yaml  # Detection job
│   ├── simulate-rbac.yaml    # RBAC for simulator
│   └── prometheus/
│       └── prometheus.yml    # Example Prometheus config
├── controller/
│   └── controller.py         # T-Helper decision + B-Cell response
├── data/
│   └── metrics.csv           # Training/evaluation dataset (970 samples)
├── docs/
│   ├── architecture.md       # Immune system mapping
│   ├── results.md            # Experimental results
│   ├── runbook.md            # Operational guide
│   └── WORKFLOW_GUIDE.md     # This file
├── ml/
│   ├── models/
│   │   ├── iforest.joblib    # Trained Isolation Forest
│   │   └── ae_sklearn.joblib # Trained sklearn autoencoder
│   ├── train_isolation_forest.py
│   ├── train_autoencoder_sklearn.py
│   └── requirements.txt      # ML dependencies
├── scripts/
│   ├── generate_metrics.py   # Synthetic data generator
│   ├── run_experiment.ps1    # End-to-end automation
│   ├── simulate_detection.py # In-cluster detection logic
│   └── create_repro_bundle.ps1  # Reproducibility bundle
├── docker-compose.yml        # Container orchestration
├── Dockerfile.tfbase         # TensorFlow-enabled image
├── README.md                 # Project overview
└── requirements.txt          # Root dependencies
```

---

## Troubleshooting

### Common Issues

**1. TensorFlow not available on Python 3.14**
- **Solution:** Use Python 3.11 in container or use sklearn autoencoder

**2. ImagePullBackOff in Kubernetes**
- **Solution:** Set `imagePullPolicy: Never` and ensure image built locally
- For kind/minikube: `kind load docker-image dis-autoencoder:tfbase`

**3. Model file not found in container**
- **Solution:** Rebuild image with `docker build -f Dockerfile.tfbase -t dis-autoencoder:tfbase .`
- Models are copied at build time via `COPY ml/models/ /app/ml/models/`

**4. ServiceAccount missing errors**
- **Solution:** Apply `cluster/adc-agent-sa.yaml` and `cluster/simulate-rbac.yaml` first

**5. Feature count mismatch during scoring**
- **Solution:** Ensure label column is excluded when training and scoring
- Models expect 9 features (excluding 'label')

---

## Automation Script

For complete end-to-end execution:

```powershell
.\scripts\run_experiment.ps1
```

**What it does:**
1. ✅ Checks prerequisites (docker, kubectl)
2. ✅ Builds TensorFlow base image
3. ✅ Trains models (in venv or container)
4. ✅ Applies Kubernetes manifests
5. ✅ Runs detection job
6. ✅ Optionally applies chaos experiments
7. ✅ Collects logs and artifacts to `results/`
8. ✅ Teardown and cleanup

---

## Next Steps

### For Research Publication:
1. ✅ Generate larger synthetic datasets (1000+ samples)
2. ✅ Train models on labeled data
3. ⚠️ Compute precision-recall curves using ground truth labels
4. ⚠️ Calculate AUPRC (Area Under Precision-Recall Curve)
5. ⚠️ Measure detection latency (time-to-detect after anomaly onset)
6. ⚠️ Compare with baseline approaches

### For Production Deployment:
1. Replace synthetic data with real Prometheus metrics
2. Implement continuous model retraining pipeline
3. Add alert notification system (Slack, PagerDuty)
4. Implement model versioning and A/B testing
5. Add comprehensive logging and observability

---

## References

- **Kubernetes Python Client:** https://github.com/kubernetes-client/python
- **scikit-learn Isolation Forest:** https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
- **Chaos Mesh Documentation:** https://chaos-mesh.org/docs/
- **Biological Immune System Mapping:** See `docs/architecture.md`

---

**Document Version:** 1.0  
**Last Updated:** February 4, 2026  
**Maintained By:** DIS Research Team Lead - Ujwal Thakare
