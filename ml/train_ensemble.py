"""
Train a weighted ensemble combining IsolationForest, Autoencoder, and One-Class SVM.

The ensemble uses learned weights based on model performance on a validation set.

Usage:
  python ml/train_ensemble.py --input data/metrics.csv --out ml/models/ensemble.joblib
"""
import argparse
import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import f1_score, precision_recall_curve

ROOT = Path(__file__).resolve().parents[1]

# Standard feature columns for 100K dataset
FEATURE_COLS = ['cpu_percent', 'mem_percent', 'net_tx', 'net_rx',
                'disk_read', 'disk_write', 'http_req_rate', 'response_ms']


def normalize_scores(scores):
    """Normalize scores to [0, 1] range."""
    min_s, max_s = scores.min(), scores.max()
    if max_s - min_s < 1e-10:
        return np.zeros_like(scores)
    return (scores - min_s) / (max_s - min_s)


def compute_model_scores(model_dict, X, model_type):
    """Compute anomaly scores for a model."""
    model = model_dict.get('model')
    scaler = model_dict.get('scaler')
    
    X_scaled = scaler.transform(X) if scaler is not None else X
    
    if model_type == 'iforest':
        # Higher score = more anomalous (inverted)
        scores = -model.score_samples(X_scaled)
    elif model_type == 'ocsvm':
        # decision_function: positive = normal, negative = anomaly
        scores = -model.decision_function(X_scaled)
    elif model_type == 'ae':
        # Reconstruction error: higher = more anomalous
        recon = model.predict(X_scaled)
        scores = np.mean((X_scaled - recon) ** 2, axis=1)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return scores


def find_optimal_weights(scores_dict, y_true, n_iterations=500):
    """
    Find optimal ensemble weights using random search.
    Optimizes for F1 score using a sample for efficiency.
    """
    model_names = list(scores_dict.keys())
    n_models = len(model_names)
    
    # Normalize all scores
    normalized = {name: normalize_scores(scores) for name, scores in scores_dict.items()}
    
    # Subsample for speed (10k samples is enough for weight optimization)
    n_samples = min(10000, len(y_true))
    np.random.seed(42)
    indices = np.random.choice(len(y_true), n_samples, replace=False)
    y_sample = y_true[indices]
    norm_sample = {name: scores[indices] for name, scores in normalized.items()}
    
    best_f1 = 0
    best_weights = np.ones(n_models) / n_models  # Start with equal weights
    
    for _ in range(n_iterations):
        # Random weights (Dirichlet distribution ensures sum to 1)
        weights = np.random.dirichlet(np.ones(n_models))
        
        # Compute weighted ensemble score
        ensemble_scores = np.zeros(n_samples)
        for i, name in enumerate(model_names):
            ensemble_scores += weights[i] * norm_sample[name]
        
        # Find optimal threshold for this weight combination
        precision, recall, thresholds = precision_recall_curve(y_sample, ensemble_scores)
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
        best_idx = np.argmax(f1_scores)
        
        if f1_scores[best_idx] > best_f1:
            best_f1 = f1_scores[best_idx]
            best_weights = weights.copy()
    
    return {name: weight for name, weight in zip(model_names, best_weights)}, best_f1


def main(input_csv, out_path):
    df = pd.read_csv(input_csv)
    
    # Use standard feature columns
    available_cols = [c for c in FEATURE_COLS if c in df.columns]
    
    # Get labels
    if 'is_anomaly' in df.columns:
        y = df['is_anomaly'].values
    elif 'label' in df.columns:
        y = df['label'].values
    else:
        raise ValueError("Data must contain 'is_anomaly' or 'label' column")
    
    X = df[available_cols].fillna(0).values
    
    # Load individual models
    models = {}
    model_paths = {
        'iforest': [ROOT / 'ml' / 'models' / 'iforest.joblib', ROOT / 'results' / 'iforest.joblib'],
        'ocsvm': [ROOT / 'ml' / 'models' / 'ocsvm.joblib', ROOT / 'results' / 'ocsvm.joblib'],
        'ae': [ROOT / 'ml' / 'models' / 'ae_sklearn.joblib', ROOT / 'results' / 'ae_sklearn.joblib'],
    }
    
    for model_type, paths in model_paths.items():
        for p in paths:
            if p.exists():
                models[model_type] = joblib.load(p)
                print(f'Loaded {model_type} from {p}')
                break
    
    if len(models) < 2:
        raise ValueError(f"Need at least 2 models for ensemble, found {len(models)}")
    
    print(f'\nComputing scores for {len(models)} models...')
    
    # Compute scores for all models
    scores_dict = {}
    for model_type, model_dict in models.items():
        scores_dict[model_type] = compute_model_scores(model_dict, X, model_type)
        print(f'  {model_type}: score range [{scores_dict[model_type].min():.3f}, {scores_dict[model_type].max():.3f}]')
    
    # Find optimal weights
    print('\nOptimizing ensemble weights (this may take a minute)...')
    weights, best_f1 = find_optimal_weights(scores_dict, y, n_iterations=2000)
    
    print(f'\nOptimal weights (F1 = {best_f1:.4f}):')
    for name, weight in sorted(weights.items(), key=lambda x: -x[1]):
        print(f'  {name}: {weight:.4f}')
    
    # Save ensemble configuration
    ensemble_config = {
        'weights': weights,
        'model_paths': {k: str(v[0]) for k, v in model_paths.items() if k in models},
        'feature_cols': available_cols,
        'best_f1': best_f1
    }
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump(ensemble_config, out_path)
    print(f'\nSaved ensemble config to {out_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/metrics.csv', help='Input CSV file')
    parser.add_argument('--out', default='ml/models/ensemble.joblib', help='Output model file')
    args = parser.parse_args()
    main(args.input, args.out)
