# Cognitive Overlay Digital Immune System (DIS)

**A Hybrid Autonomous Cybersecurity Architecture with Human-in-the-Loop Control for Adaptive Threat Detection and Response**

This repository provides a complete, research-grade implementation of a Cognitive Overlay Digital Immune System (DIS) for Kubernetes-based cloud-native microservices. It includes:

- **Artificial Dendritic Cell (aDC) Agents**: Metrics collection from Kubernetes nodes
- **T-Helper Detection Layer**: Unsupervised anomaly detection (Isolation Forest, Autoencoder)
- **B-Cell Response Layer**: Automated pod isolation, restart, and rollout mechanisms
- **Synthetic Dataset**: 970 labeled samples with 5 anomaly patterns
- **Chaos Engineering**: Pod kill and CPU stress experiments
- **Complete Workflow**: End-to-end automation and reproducibility

## 📚 Documentation

- **[WORKFLOW_GUIDE.md](docs/WORKFLOW_GUIDE.md)** - **START HERE**: Complete workflow, data flow architecture, technologies used, and step-by-step manual
- [architecture.md](docs/architecture.md) - Biological immune system mapping to system components
- [runbook.md](docs/runbook.md) - Operational procedures and troubleshooting
- [results.md](docs/results.md) - Experimental results and analysis

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Generate synthetic data
python scripts/generate_metrics.py

# 3. Train models
python ml/train_isolation_forest.py --input data/metrics.csv --out ml/models/iforest.joblib
python ml/train_autoencoder_sklearn.py --input data/metrics.csv --out ml/models/ae_sklearn.joblib

# 4. Run complete experiment (optional)
.\scripts\run_experiment.ps1

# 5. Generate analysis figures
python analysis/plot_detection.py
```

## 📊 Dataset

**Synthetic Metrics (970 samples, 9 features):**
- **Normal baseline**: 700 samples (72%)
- **Anomalies**: 270 samples (28%)
  - CPU spike (50 samples)
  - Memory leak (80 samples)
  - Network congestion (60 samples)
  - Pod crashes (40 samples)
  - Disk I/O saturation (40 samples)

**Features**: cpu_percent, mem_percent, net_tx, net_rx, disk_read, disk_write, http_req_rate, response_ms, pod_restarts, label

## 🏗️ Repository Structure

- `cluster/` — Kubernetes manifests and monitoring config
- `agents/` — aDC agent skeleton (Python)
- `ml/` — Training scripts and trained models
- `controller/` — T-Helper decision logic and B-Cell response engine
- `chaos/` — Chaos Mesh experiment templates
- `scripts/` — Automation and utility scripts
- `data/` — Training/evaluation datasets
- `results/figures/` — Generated visualizations
- `docs/` — architecture and experiment notes

## 🧪 Technologies Used

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.11/3.14 |
| **ML Framework** | scikit-learn 1.8.0, TensorFlow 2.12.0 (optional) |
| **Orchestration** | Kubernetes 1.28+ |
| **Containerization** | Docker 24.0+ |
| **Chaos Engineering** | Chaos Mesh 2.6+ |
| **Monitoring** | Prometheus (config provided) |

## 📈 Models

- **Isolation Forest**: Tree-based outlier detection (889KB, 9 features)
- **Sklearn Autoencoder**: Neural network reconstruction error (49KB, 9 features)

## 🎯 Key Features

✅ **Production-Ready**: Complete Kubernetes integration with RBAC  
✅ **Reproducible**: Automated workflow with synthetic data generation  
✅ **Extensible**: Modular architecture for easy customization  
✅ **Research-Grade**: Labeled dataset for precision-recall analysis  
✅ **Well-Documented**: Comprehensive guides and inline comments  

## 📝 Active Files (Cleaned Repository)

**Container Images:**
- `Dockerfile.tfbase` - **ACTIVE**: TensorFlow-enabled image for detection jobs
- `Dockerfile` - Alternative/reference (not used in automation)

**Models:**
- `ml/models/iforest.joblib` - **ACTIVE**: Trained Isolation Forest
- `ml/models/ae_sklearn.joblib` - **ACTIVE**: Trained sklearn autoencoder

**Trainers:**
- `ml/train_isolation_forest.py` - **ACTIVE**
- `ml/train_autoencoder_sklearn.py` - **ACTIVE**
- `ml/train_autoencoder.py` - TensorFlow/Keras version (requires TF, alternative)

## 🧹 Repository Cleanup

**Removed unnecessary files:**
- ❌ Old experiment artifacts in `results/` (logs, pod lists, events)
- ❌ Duplicate model files (kept only in `ml/models/`)
- ❌ TensorFlow autoencoder models (using sklearn version)

## 🔬 For Researchers

**Next steps for publication:**
1. Compute precision-recall curves using ground truth labels
2. Calculate AUPRC (Area Under Precision-Recall Curve)
3. Measure detection latency (time-to-detect after anomaly onset)
4. Compare with baseline approaches

**For production deployment:**
1. Replace synthetic data with real Prometheus metrics
2. Implement continuous model retraining pipeline
3. Add alert notification system
4. Implement model versioning and A/B testing

## 📧 Citation

If you use this repository in your research, please cite:

```bibtex
@misc{dis2026,
  title={Cognitive Overlay Digital Immune System for Kubernetes},
  author={DIS Research Team},
  year={2026},
  howpublished={\url{https://github.com/theujwalthakare/DIS}}
}
```

## 📄 License

[Specify your license here]

---

**For complete workflow and data flow architecture, see [docs/WORKFLOW_GUIDE.md](docs/WORKFLOW_GUIDE.md)**
