# Results (Draft)

This draft summarizes the initial experimental outputs from the DIS scaffold. It
is intended for inclusion in a research paper — replace placeholder numbers
with full evaluation tables once experiments are scaled.

Key artifacts:

- Detection models: `ml/models/iforest.joblib`, `ml/models/ae_sklearn.joblib`.
- Saved Keras autoencoder: `results/autoencoder` (SavedModel format).
- Collected events and logs: `results/events.yaml`, `results/pods.txt`, `results/example-app.logs`.
- Analysis figures: `results/figures/timeseries_scores.png`, `results/figures/iforest_histogram.png`.

Summary (initial run):

- Models trained successfully and persisted. The IsolationForest and
  scikit-learn autoencoder produce measurable anomaly scores over the test
  metric stream (see time series and score distribution figures).
- The in-cluster simulator job executed and invoked the Controller B-Cell
  response. Some cluster-level issues (image pull and service account) were
  encountered during the first deployment; these were resolved by providing a
  local image and the missing service account.

Representative figure descriptions (place these captions under figures):

- Figure X — Time series of CPU and memory with normalized anomaly scores from
  the Isolation Forest and the scikit-learn autoencoder. Vertical markers
  indicate injected faults (Chaos Mesh) and the timing of B-Cell responses.
- Figure Y — Distribution of anomaly scores produced by the two detectors.

Next steps for full evaluation

- Build labeled test datasets by aligning Chaos Mesh injection timestamps with
  metrics windows to obtain ground-truth anomalies.
- Compute precision-recall curves and detection latency statistics for each
  detector and for the combined decision logic. Include AUPRC, median time-to-detect,
  and recovery success rate per fault type.
