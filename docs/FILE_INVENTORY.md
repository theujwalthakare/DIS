# DIS Repository File Inventory

**Generated:** February 4, 2026  
**Status:** Cleaned and Production-Ready

## 📊 Repository Statistics

- **Total Python Files:** 8
- **Total Kubernetes Manifests:** 7
- **Total Documentation:** 5 markdown files
- **Total Scripts:** 4 automation scripts
- **Trained Models:** 2 (.joblib files, 916 KB total)

---

## 🗂️ Complete File Inventory

### 📁 Core Configuration (Root)
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `README.md` | 5 KB | Main documentation entry point | ✅ Active |
| `requirements.txt` | <1 KB | Python dependencies | ✅ Active |
| `docker-compose.yml` | <1 KB | Container orchestration | ✅ Active |
| `Dockerfile.tfbase` | 1 KB | **PRIMARY**: TensorFlow image | ✅ Active |
| `Dockerfile` | 1 KB | Alternative/reference | ⚠️ Optional |

### 📁 agents/ - Metrics Collection
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `adc_agent.py` | 2 KB | Artificial Dendritic Cell agent | ✅ Active |
| `requirements.txt` | <1 KB | Agent-specific dependencies | ✅ Active |

### 📁 ml/ - Machine Learning
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `train_isolation_forest.py` | 1 KB | **PRIMARY**: IF trainer | ✅ Active |
| `train_autoencoder_sklearn.py` | 2 KB | **PRIMARY**: sklearn AE trainer | ✅ Active |
| `train_autoencoder.py` | 1 KB | TensorFlow/Keras variant | ⚠️ Alternative |
| `requirements.txt` | <1 KB | ML dependencies | ✅ Active |
| `models/iforest.joblib` | 868 KB | Trained Isolation Forest | ✅ Active |
| `models/ae_sklearn.joblib` | 48 KB | Trained sklearn autoencoder | ✅ Active |

### 📁 controller/ - Decision & Response
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `controller.py` | 6 KB | T-Helper + B-Cell logic | ✅ Active |

### 📁 cluster/ - Kubernetes Manifests
| File | Size | Purpose | Status |
|------|------|---------|--------|
| `adc-agent-sa.yaml` | <1 KB | ServiceAccount for agents | ✅ Active |
| `agent-daemonset.yaml` | 1 KB | ADC agent deployment | ✅ Active |
| `example-deployment.yaml` | 1 KB | Test workload (nginx) | ✅ Active |
| `simulate-rbac.yaml` | 1 KB | RBAC for detection job | ✅ Active |
| `simulate-detection-job.yaml` | 1 KB | Detection job definition | ✅ Active |
| `prometheus/prometheus.yml` | <1 KB | Example Prometheus config | 📚 Reference |
| `README.md` | <1 KB | Cluster deployment guide | 📚 Documentation |

### 📁 chaos/ - Fault Injection
| File | Size | Purpose | Status |
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
