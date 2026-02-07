# DIS Repository File Inventory

**Generated:** February 7, 2026  
**Status:** Production-Ready | 100k Dataset | Full Kubernetes Deployment

## 📊 Repository Statistics

- **Total Python Files:** 15 (8 core + 6 analysis + 1 controller)
- **Total Kubernetes Manifests:** 6 (YAML files, all deployment-ready)
- **Total Documentation:** 7 markdown files
- **Total Scripts:** 4 automation scripts
- **Trained Models:** 4 (.joblib files, ~2.3 MB total)
- **Analysis Outputs:** 14 visualizations + 7 CSV metrics files
- **Dataset:** 100,000 synthetic metrics with ground-truth labels

---

## 🗂️ Complete File Inventory

### 📁 Core Configuration (Root)
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `README.md` | 12 KB | Main documentation (100k dataset spec) | ✅ Production |
| `requirements.txt` | <1 KB | Python dependencies (scikit-learn, pandas) | ✅ Active |
| `docker-compose.yml` | <1 KB | Container orchestration reference | ✅ Reference |
| `Dockerfile` | 1 KB | Multi-stage Python 3.11 image | ✅ Production |

### 📁 agents/ - Metrics Collection
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `adc_agent.py` | 4 KB | Artificial Dendritic Cell (8-metric collector) | ✅ Production |

### 📁 ml/ - Machine Learning Models & Training
| File | Size | Purpose | Status |
|-------|------|---------|--------|
| `train_isolation_forest.py` | 1.5 KB | IsolationForest trainer (100k-optimized) | ✅ Production |
| `train_autoencoder_sklearn.py` | 2 KB | sklearn Autoencoder trainer (100k-optimized) | ✅ Production |
| `models/iforest_100k.joblib` | 916 KB | **PRIMARY**: Trained IF (AUPRC 0.536) | ✅ Production |
| `models/autoencoder_100k.joblib` | 48 KB | **PRIMARY**: Trained AE (AUPRC 0.178) | ✅ Production |
| `models/iforest.joblib` | 868 KB | Legacy IF model (smaller dataset) | ⚠️ Backup |
| `models/ae_sklearn.joblib` | 42 KB | Legacy AE model (smaller dataset) | ⚠️ Backup |
| `models/scaler_100k.joblib` | 5 KB | Feature scaler for 100k dataset | ✅ Production |

### 📁 controller/ - Detection & Response Logic
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `controller.py` | 8 KB | T-Helper + B-Cell decision logic | ✅ Production |

### 📁 cluster/ - Kubernetes Manifests (Deployment-Ready)
| File | Size | Purpose | Status |
|-------|------|---------|--------|
| `adc-agent-sa.yaml` | <1 KB | ServiceAccount + RBAC for agents | ✅ Deployed |
| `agent-daemonset.yaml` | 1.5 KB | ADC agent DaemonSet (all nodes) | ✅ Deployed |
| `example-deployment.yaml` | 1 KB | Test workload (2x nginx replicas) | ✅ Deployed |
| `simulate-rbac.yaml` | 1.5 KB | RBAC for detection job | ✅ Deployed |
| `simulate-detection-job.yaml` | 1.5 KB | Detection simulator Kubernetes Job | ✅ Deployed |
| `prometheus/prometheus.yml` | 1 KB | Prometheus scrape config (service discovery) | ✅ Production |

### 📁 scripts/ - Automation & Orchestration
| File | Size | Purpose | Status |
|-------|------|---------|--------|
| `run_experiment.ps1` | 15 KB | End-to-end pipeline (data→model→analysis→deploy) | ✅ Production |
| `generate_metrics.py` | 2 KB | Data generator for 100k synthetic metrics | ✅ Production |
| `simulate_detection.py` | 6 KB | Detection simulator with ensemble scoring | ✅ Production |

### 📁 analysis/ - Comprehensive Evaluation (6 Scripts, 14 Figures, 7 CSVs)
| File | Purpose | Output | Status |
|-------|---------|--------|--------|
|------|------|---------|--------|
| `pod-kill.yaml` | <1 KB | PodChaos experiment | ✅ Active |
| `cpu-stress.yaml` | <1 KB | StressChaos experiment | ✅ Active |

### 📁 scripts/ - Automation
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `generate_metrics.py` | 4 KB | Synthetic data generator | ✅ Active |
| `run_experiment.ps1` | 5 KB | End-to-end automation | ✅ Active |
| `simulate_detection.py` | 3 KB | In-cluster detection logic | ✅ Active |
| `create_repro_bundle.ps1` | 1 KB | Reproducibility packager | ✅ Active |

### 📁 analysis/ - Visualization
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `plot_detection.py` | 4 KB | Figure generation script | ✅ Active |

### 📁 docs/ - Documentation
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `WORKFLOW_GUIDE.md` | 22 KB | **PRIMARY**: Complete workflow guide | ✅ Active |
| `architecture.md` | 1 KB | Immune system mapping | 📚 Reference |
| `runbook.md` | 4 KB | Operational procedures | 📚 Reference |
| `results.md` | 2 KB | Experimental results | 📚 Reference |

### 📁 data/ - Datasets
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `metrics.csv` | ~50 KB | 970-sample synthetic dataset | ✅ Active |

### 📁 results/ - Outputs
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `README.md` | 2 KB | Results directory guide | 📚 Documentation |
| `figures/timeseries_scores.png` | - | Timeseries visualization | 📊 Generated |
| `figures/iforest_histogram.png` | - | IF score distribution | 📊 Generated |
| `figures/ae_sklearn_histogram.png` | - | AE score distribution | 📊 Generated |

---

## ✅ Files Cleaned Up (Removed)

### Removed from `results/`
- ❌ `autoencoder/` directory - Duplicate TensorFlow model files
- ❌ `iforest.joblib` - Old model (kept in `ml/models/`)
- ❌ `ae_sklearn.joblib` - Old model (kept in `ml/models/`)
- ❌ `pods.txt` - Stale experiment artifact
- ❌ `example-app.logs` - Old logs
- ❌ `events.yaml` - Old events

### Removed from `ml/models/`
- ❌ `autoencoder/` directory - TensorFlow model (using sklearn version)

---

## 🎯 Critical Path Files

**For data generation:**
1. `scripts/generate_metrics.py` → `data/metrics.csv`

**For training:**
2. `ml/train_isolation_forest.py` → `ml/models/iforest.joblib`
3. `ml/train_autoencoder_sklearn.py` → `ml/models/ae_sklearn.joblib`

**For deployment:**
4. `Dockerfile.tfbase` → Docker image
5. `cluster/adc-agent-sa.yaml` → RBAC setup
6. `cluster/agent-daemonset.yaml` → Agent deployment
7. `cluster/example-deployment.yaml` → Workload deployment
8. `cluster/simulate-rbac.yaml` → Detection RBAC
9. `cluster/simulate-detection-job.yaml` → Detection job

**For detection:**
10. `scripts/simulate_detection.py` → In-cluster detection
11. `controller/controller.py` → Response actions

**For analysis:**
12. `analysis/plot_detection.py` → `results/figures/*.png`

---

## 📈 File Status Legend

| Icon | Status | Description |
|------|--------|-------------|
| ✅ | Active | Currently used in workflow |
| ⚠️ | Optional | Alternative/backup version |
| 📚 | Reference | Documentation/example |
| 📊 | Generated | Created by automation |

---

## 🔄 Workflow Dependencies

```
generate_metrics.py
        ↓
    metrics.csv
        ↓
    ┌───┴────┐
    ↓        ↓
train_IF  train_AE
    ↓        ↓
iforest   ae_sklearn
    ↓        ↓
    └───┬────┘
        ↓
   Dockerfile.tfbase
        ↓
   dis-autoencoder:tfbase
        ↓
 simulate-detection-job
        ↓
   Detection Logs
        ↓
 plot_detection.py
        ↓
    Figures (PNG)
```

---

**Total Active Files:** 32  
**Total Size:** ~1.0 MB (excluding virtual environment)  
**Documentation Files:** 5  
**Code Files:** 11 Python files  
**Config Files:** 16 YAML/Dockerfile/txt files
