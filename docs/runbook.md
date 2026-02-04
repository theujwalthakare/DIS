# DIS Experiment Runbook

This runbook documents a reproducible, end-to-end in-cluster experiment to
exercise the Cognitive Overlay Digital Immune System (DIS) scaffold. It
assumes you have a Kubernetes cluster, `kubectl` access, Docker, and the repo
cloned locally.

1) Prepare local artifacts

- Ensure models and data are present:
  - `data/metrics.csv` — example metrics (already in repo)
  - `ml/models/iforest.joblib` — train locally or build into image
  - `ml/models/autoencoder` — trained Keras model (optional)

- Build the TensorFlow test image (contains Keras trainer and simulator):

```powershell
# from repo root
docker build -f Dockerfile.tfbase -t dis-autoencoder:tfbase .
```

If your cluster cannot pull local images, push the image to a registry or load
the image into your cluster nodes (e.g., `kind load docker-image ...`).

2) Deploy example workload and monitoring config

```powershell
kubectl apply -f cluster/example-deployment.yaml
# (Optional) Apply Prometheus scrape config if you run a Prometheus instance
# kubectl apply -f cluster/prometheus/prometheus.yml
```

Verify pods:

```powershell
kubectl get pods -l app=example-app -o wide
```

3) Deploy aDC agent (optional local DaemonSet)

Edit `cluster/agent-daemonset.yaml` to point to your agent image, then:

```powershell
kubectl apply -f cluster/agent-daemonset.yaml
```

The aDC agent exposes local node metrics on port 8000. Configure Prometheus to
scrape this port to collect antigens.

4) Apply RBAC and run the in-cluster simulator job

This job uses `simulate_detection.py` to demonstrate detection->response.

```powershell
kubectl apply -f cluster/simulate-rbac.yaml
kubectl apply -f cluster/simulate-detection-job.yaml
kubectl get jobs
kubectl logs -l job=simulate-detection --tail=200
```

Notes about models:
- The Job image needs access to `ml/models/iforest.joblib` for deterministic
  scoring. You can either:
  - Bake the model into the image at build-time (COPY), or
  - Mount a PersistentVolume to `/app/ml/models` and write the file there.

5) Run trainers (alternatives)

- Local venv (no container):
```powershell
. .venv\Scripts\Activate.ps1
python ml/train_isolation_forest.py --input data/metrics.csv --out ml/models/iforest.joblib
python ml/train_autoencoder_sklearn.py --input data/metrics.csv --out ml/models/ae_sklearn.joblib
```

- Container (reproducible):
```powershell
docker compose build
docker compose run --rm autoencoder
```

6) Verify controller actions

- Check pod labels and lifecycle after simulator runs:
```powershell
kubectl get pods -l app=example-app -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.labels}{"\n"}{end}'
kubectl describe pod <pod-name>
```

7) Collect results

- Save Prometheus metrics (if configured) and Kubernetes events/logs to `results/`.
- Record model artifacts in `ml/models` and zip `data/` and `results/` for paper
  reproducibility.

Troubleshooting

- pandas / numpy errors in containers: ensure `numpy` and `pandas` are
  installed with compatible versions. The `Dockerfile.tfbase` uses the
  `tensorflow/tensorflow:2.12.0` base image which bundles compatible wheels.
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
