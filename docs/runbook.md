# DIS Experiment Runbook

This runbook documents a reproducible, end-to-end in-cluster experiment to
exercise the Cognitive Overlay Digital Immune System (DIS). It
assumes you have a Kubernetes cluster (minikube/Docker Desktop), `kubectl` access, and the repo
cloned locally.

**Dataset:** 100,000 synthetic metrics (96,311 normal, 3,689 anomalies)
**Models:** IsolationForest (AUPRC 0.536) + sklearn Autoencoder (AUPRC 0.178)
**Detection latency:** 15.8ms mean, 26.5ms P99

## 1) Verify Kubernetes Cluster

```powershell
kubectl cluster-info
kubectl get nodes
```

## 2) Prepare models and data

Models are pre-trained and available in `ml/models/`:
- `ml/models/iforest_100k.joblib` — IsolationForest (100k dataset)
- `ml/models/autoencoder_100k.joblib` — sklearn Autoencoder (100k dataset)
- `data/public_dataset_100k_ml_ready.csv` — 100k metric samples (already in repo)

No additional training required for standard deployment.

## 3) Deploy to Kubernetes

The cluster manifests use **hostPath volumes** to mount application code. First, copy the repo to minikube:

```powershell
minikube cp . /mnt/dis-app
```

Then deploy all cluster resources:

```powershell
kubectl apply -f cluster/
```

This deploys:
- **ServiceAccounts** — RBAC permissions for agents and jobs
- **DaemonSet (adc-agent)** — Metrics collection on all nodes (port 8000)
- **Deployment (example-app)** — 2x nginx replicas as detection target
- **Service** — ClusterIP service for example-app (port 80)
- **Job (simulate-detection)** — Detection simulation and anomaly scoring
- **Prometheus** — Scrape config for metrics collection

## 4) Verify Deployment

```powershell
# Check all pods running
kubectl get pods

# View ADC agent metrics
kubectl logs -l app=adc-agent

# Check detection job status
kubectl get jobs
kubectl logs job/simulate-detection

# Access example-app service
kubectl port-forward svc/example-app 8080:80  # Then visit http://localhost:8080
```

**Expected Status:**
- example-app: 2/2 Running ✓
- adc-agent: 1/1 Running ✓
- simulate-detection: 1/1 Running ✓

## 5) Run Full Analysis Pipeline

Optional: Re-train models or run comprehensive analysis locally:

```powershell
# Activate Python environment
. .venv\Scripts\Activate.ps1

# Train models
python ml/train_isolation_forest.py --input data/public_dataset_100k_ml_ready.csv --out ml/models/iforest_100k.joblib
python ml/train_autoencoder_sklearn.py --input data/public_dataset_100k_ml_ready.csv --out ml/models/autoencoder_100k.joblib

# Run all analysis scripts
python analysis/evaluate_models.py
python analysis/compare_baselines.py
python analysis/ablation_study.py
python analysis/measure_latency.py
```

Outputs saved to `results/` with CSV metrics and PNG visualizations.

## 6) Orchestrate Full Pipeline

Run the complete end-to-end pipeline (data prep, training, analysis, deployment):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_experiment.ps1
```

This script:
1. Prepares 100k dataset
2. Trains both models with cross-validation
3. Runs comprehensive analysis (6 scripts, 14 visualizations)
4. Generates metrics CSVs and publication-ready figures
5. Optionally deploys to Kubernetes

## Troubleshooting

**Pods stuck in ContainerCreating:**
- Verify code is copied to minikube: `minikube ssh "ls -la /mnt/dis-app/agents/"`
- Check pod events: `kubectl describe pod <pod-name>`

**Image pull errors:**
- Ensure minikube Docker environment is active: `minikube docker-env | Invoke-Expression`
- Base images (python:3.11-slim, nginx:1.25) should pull automatically

**Model not found errors:**
- Verify models in `ml/models/`: `ls -la ml/models/`
- Models are included in hostPath mount to `/mnt/dis-app`
- Image pull errors: either push to a registry or set `imagePullPolicy` to
  `Never` and make the image available on the node (e.g., `kind load docker-image`).
- RBAC denied: confirm `simulate-sa` Role has permissions and the Job uses
  `serviceAccountName: simulate-sa`.

Experiment notes

- Parameters to vary in experiments: model contamination, feature sets,
  length of observation window, Chaos Mesh fault intensity and frequency.
- Record all random seeds, model hyperparameters, and cluster topology in
  `results/metadata.json` for reproducibility.

References

- See `docs/architecture.md` for mapping to immune system concepts.
