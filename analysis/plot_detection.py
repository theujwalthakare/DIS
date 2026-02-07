"""
Minimal analysis script to generate detection figures for the DIS experiment.

Produces:
- results/figures/timeseries_scores.png
- results/figures/score_histogram.png

Usage:
  python analysis/plot_detection.py

Requires: pandas, matplotlib, joblib, numpy, scikit-learn
"""
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / 'data' / 'metrics.csv'
RESULTS = ROOT / 'results'
FIG_DIR = RESULTS / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    if not DATA_CSV.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_CSV}")
    df = pd.read_csv(DATA_CSV)
    return df

def load_iforest():
    candidates = [RESULTS / 'iforest.joblib', ROOT / 'ml' / 'models' / 'iforest.joblib']
    for p in candidates:
        if p.exists():
            return joblib.load(p)
    return None

def load_ae_sklearn():
    candidates = [RESULTS / 'ae_sklearn.joblib', ROOT / 'ml' / 'models' / 'ae_sklearn.joblib']
    for p in candidates:
        if p.exists():
            return joblib.load(p)
    return None

def compute_iforest_scores(model_obj, X):
    # Handle dict structure from saved model
    if isinstance(model_obj, dict):
        model = model_obj.get('model')
        scaler = model_obj.get('scaler')
    else:
        model = model_obj
        scaler = None
    
    # Apply scaling if available
    X_scaled = scaler.transform(X) if scaler is not None else X
    
    # IsolationForest.score_samples -> higher is normal; invert to get anomaly score
    s = model.score_samples(X_scaled)
    return -s

def compute_ae_scores(obj, X):
    # obj is a dict {'model': MLPRegressor, 'scaler': StandardScaler}
    model = obj.get('model') if isinstance(obj, dict) else obj
    scaler = obj.get('scaler') if isinstance(obj, dict) else None
    Xs = scaler.transform(X) if scaler is not None else X
    recon = model.predict(Xs)
    # compute per-sample MSE
    mse = np.mean((Xs - recon) ** 2, axis=1)
    return mse

def plot_timeseries(df, if_scores=None, ae_scores=None):
    t = np.arange(len(df))
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax[0].plot(t, df['cpu_percent'], label='cpu_percent')
    ax[0].plot(t, df['mem_percent'], label='mem_percent')
    ax[0].set_ylabel('Percent')
    ax[0].legend()

    if if_scores is not None:
        ax[1].plot(t, (if_scores - np.min(if_scores)) / (np.ptp(if_scores)+1e-9), label='IF anomaly (norm)')
    if ae_scores is not None:
        ax[1].plot(t, (ae_scores - np.min(ae_scores)) / (np.ptp(ae_scores)+1e-9), label='AE anomaly (norm)')
    ax[1].set_ylabel('Normalized score')
    ax[1].set_xlabel('Sample index')
    ax[1].legend()
    fig.tight_layout()
    out = FIG_DIR / 'timeseries_scores.png'
    fig.savefig(out)
    print('Wrote', out)

def plot_hist(scores, name):
    fig, ax = plt.subplots(figsize=(6,3))
    ax.hist(scores, bins=30)
    ax.set_title(f'{name} score distribution')
    out = FIG_DIR / f'{name}_histogram.png'
    fig.savefig(out)
    print('Wrote', out)

def main():
    df = load_data()
    # Exclude 'is_anomaly' column if present for scoring
    feature_cols = [c for c in df.columns if c not in ['is_anomaly', 'label']]
    X = df[feature_cols].select_dtypes(include=['number']).fillna(0).values

    iforest = load_iforest()
    if iforest is not None:
        if_scores = compute_iforest_scores(iforest, X)
        plot_hist(if_scores, 'iforest')
    else:
        if_scores = None
        print('No Isolation Forest model found')

    ae = load_ae_sklearn()
    if ae is not None:
        try:
            ae_scores = compute_ae_scores(ae, X)
            plot_hist(ae_scores, 'ae_sklearn')
        except Exception as e:
            print('AE scoring failed:', e)
            ae_scores = None
    else:
        ae_scores = None
        print('No AE_sklearn model found')

    plot_timeseries(df, if_scores=if_scores, ae_scores=ae_scores)

if __name__ == '__main__':
    main()
