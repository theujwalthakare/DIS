"""
Comprehensive Model Evaluation for DIS Publication.

Computes publication-ready metrics:
- Precision-Recall curves for each model
- AUPRC (Area Under Precision-Recall Curve)
- F1-Score, Precision, Recall at optimal threshold
- Confusion matrices and detection statistics

Usage:
  python analysis/evaluate_models.py

Output:
  - results/figures/precision_recall_curves.png
  - results/figures/confusion_matrices.png
  - results/evaluation_metrics.csv
  - Console output with all metrics
"""
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    precision_recall_curve, auc, f1_score, precision_score, 
    recall_score, confusion_matrix, classification_report
)

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / 'data' / 'metrics.csv'
RESULTS = ROOT / 'results'
FIG_DIR = RESULTS / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Standard feature columns for 100K dataset
FEATURE_COLS = ['cpu_percent', 'mem_percent', 'net_tx', 'net_rx',
                'disk_read', 'disk_write', 'http_req_rate', 'response_ms']


def load_data():
    """Load metrics CSV with ground truth labels."""
    if not DATA_CSV.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_CSV}")
    df = pd.read_csv(DATA_CSV)
    return df


def load_models():
    """Load trained Isolation Forest, Autoencoder, OCSVM, and Ensemble models."""
    models = {}
    
    # Load Isolation Forest
    iforest_paths = [RESULTS / 'iforest.joblib', ROOT / 'ml' / 'models' / 'iforest.joblib']
    for p in iforest_paths:
        if p.exists():
            models['iforest'] = joblib.load(p)
            print(f"✓ Loaded Isolation Forest from {p}")
            break
    
    # Load sklearn Autoencoder
    ae_paths = [RESULTS / 'ae_sklearn.joblib', ROOT / 'ml' / 'models' / 'ae_sklearn.joblib']
    for p in ae_paths:
        if p.exists():
            models['ae_sklearn'] = joblib.load(p)
            print(f"✓ Loaded sklearn Autoencoder from {p}")
            break
    
    # Load One-Class SVM
    ocsvm_paths = [RESULTS / 'ocsvm.joblib', ROOT / 'ml' / 'models' / 'ocsvm.joblib']
    for p in ocsvm_paths:
        if p.exists():
            models['ocsvm'] = joblib.load(p)
            print(f"✓ Loaded One-Class SVM from {p}")
            break
    
    # Load Ensemble config
    ensemble_paths = [RESULTS / 'ensemble.joblib', ROOT / 'ml' / 'models' / 'ensemble.joblib']
    for p in ensemble_paths:
        if p.exists():
            models['ensemble_config'] = joblib.load(p)
            print(f"✓ Loaded Ensemble config from {p}")
            break
    
    return models


def compute_anomaly_scores(models, X):
    """Compute anomaly scores for each model."""
    scores = {}
    raw_scores = {}  # For weighted ensemble
    
    # Isolation Forest scores (negate so higher = more anomalous)
    if 'iforest' in models:
        iforest_data = models['iforest']
        if isinstance(iforest_data, dict):
            model = iforest_data.get('model')
            scaler = iforest_data.get('scaler')
            Xs = scaler.transform(X) if scaler is not None else X
        else:
            model = iforest_data
            Xs = X
        raw_scores['iforest'] = -model.score_samples(Xs)
        scores['Isolation Forest'] = raw_scores['iforest']
    
    # Autoencoder reconstruction error
    if 'ae_sklearn' in models:
        ae = models['ae_sklearn']
        model = ae.get('model') if isinstance(ae, dict) else ae
        scaler = ae.get('scaler') if isinstance(ae, dict) else None
        Xs = scaler.transform(X) if scaler is not None else X
        recon = model.predict(Xs)
        mse = np.mean((Xs - recon) ** 2, axis=1)
        raw_scores['ae'] = mse
        scores['Autoencoder (sklearn)'] = mse
    
    # One-Class SVM scores
    if 'ocsvm' in models:
        ocsvm_data = models['ocsvm']
        if isinstance(ocsvm_data, dict):
            model = ocsvm_data.get('model')
            scaler = ocsvm_data.get('scaler')
            Xs = scaler.transform(X) if scaler is not None else X
        else:
            model = ocsvm_data
            Xs = X
        # decision_function: positive = normal, negative = anomaly, so negate
        raw_scores['ocsvm'] = -model.decision_function(Xs)
        scores['One-Class SVM'] = raw_scores['ocsvm']
    
    # Weighted Ensemble (if config available)
    if 'ensemble_config' in models and len(raw_scores) >= 2:
        config = models['ensemble_config']
        weights = config.get('weights', {})
        
        # Normalize scores
        normalized = {}
        for name, s in raw_scores.items():
            s_norm = (s - s.min()) / (s.max() - s.min() + 1e-10)
            normalized[name] = s_norm
        
        # Apply weights
        ensemble_scores = np.zeros(len(X))
        total_weight = 0
        for name, s_norm in normalized.items():
            w = weights.get(name, 1.0 / len(normalized))
            ensemble_scores += w * s_norm
            total_weight += w
        
        if total_weight > 0:
            ensemble_scores /= total_weight
        
        scores['Weighted Ensemble'] = ensemble_scores
    
    # Simple average ensemble as fallback
    if len(raw_scores) >= 2 and 'Weighted Ensemble' not in scores:
        normalized_scores = []
        for name, s in raw_scores.items():
            s_norm = (s - s.min()) / (s.max() - s.min() + 1e-10)
            normalized_scores.append(s_norm)
        scores['Ensemble (Average)'] = np.mean(normalized_scores, axis=0)
    
    return scores


def compute_metrics(y_true, y_scores, model_name):
    """Compute comprehensive metrics for a single model."""
    # Precision-Recall curve
    precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
    auprc = auc(recall, precision)
    
    # Find optimal threshold (maximize F1)
    f1_scores = 2 * (precision[:-1] * recall[:-1]) / (precision[:-1] + recall[:-1] + 1e-10)
    if len(f1_scores) > 0:
        optimal_idx = np.argmax(f1_scores)
        optimal_threshold = thresholds[optimal_idx]
    else:
        optimal_threshold = np.median(y_scores)
    
    # Binary predictions at optimal threshold
    y_pred = (y_scores >= optimal_threshold).astype(int)
    
    # Compute metrics
    metrics = {
        'model': model_name,
        'auprc': auprc,
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1': f1_score(y_true, y_pred, zero_division=0),
        'optimal_threshold': optimal_threshold,
        'true_positives': np.sum((y_pred == 1) & (y_true == 1)),
        'false_positives': np.sum((y_pred == 1) & (y_true == 0)),
        'true_negatives': np.sum((y_pred == 0) & (y_true == 0)),
        'false_negatives': np.sum((y_pred == 0) & (y_true == 1)),
        'precision_curve': precision,
        'recall_curve': recall,
        'thresholds': thresholds,
        'y_pred': y_pred
    }
    
    return metrics


def plot_precision_recall_curves(results, y_true):
    """Generate publication-quality precision-recall curves."""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    colors = ['#2563eb', '#dc2626', '#16a34a', '#9333ea']
    linestyles = ['-', '--', '-.', ':']
    
    for i, (name, metrics) in enumerate(results.items()):
        ax.plot(
            metrics['recall_curve'], 
            metrics['precision_curve'],
            color=colors[i % len(colors)],
            linestyle=linestyles[i % len(linestyles)],
            linewidth=2,
            label=f"{name} (AUPRC = {metrics['auprc']:.4f})"
        )
    
    # Add baseline (random classifier)
    baseline = np.sum(y_true) / len(y_true)
    ax.axhline(y=baseline, color='gray', linestyle=':', linewidth=1.5, 
               label=f'Random Baseline ({baseline:.3f})')
    
    ax.set_xlabel('Recall', fontsize=12)
    ax.set_ylabel('Precision', fontsize=12)
    ax.set_title('Precision-Recall Curves for DIS Anomaly Detection Models', fontsize=14)
    ax.legend(loc='lower left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    
    fig.tight_layout()
    out_path = FIG_DIR / 'precision_recall_curves.png'
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved precision-recall curves to {out_path}")
    plt.close(fig)


def plot_confusion_matrices(results, y_true):
    """Generate confusion matrix visualizations."""
    n_models = len(results)
    fig, axes = plt.subplots(1, n_models, figsize=(5 * n_models, 4))
    
    if n_models == 1:
        axes = [axes]
    
    for ax, (name, metrics) in zip(axes, results.items()):
        cm = confusion_matrix(y_true, metrics['y_pred'])
        
        # Plot confusion matrix
        im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
        ax.set_title(f'{name}\nF1={metrics["f1"]:.3f}', fontsize=11)
        
        # Add text annotations
        thresh = cm.max() / 2.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, format(cm[i, j], 'd'),
                       ha="center", va="center",
                       color="white" if cm[i, j] > thresh else "black",
                       fontsize=12)
        
        ax.set_ylabel('True Label')
        ax.set_xlabel('Predicted Label')
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(['Normal', 'Anomaly'])
        ax.set_yticklabels(['Normal', 'Anomaly'])
    
    fig.tight_layout()
    out_path = FIG_DIR / 'confusion_matrices.png'
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved confusion matrices to {out_path}")
    plt.close(fig)


def plot_score_distributions(scores, y_true):
    """Plot anomaly score distributions by class."""
    n_models = len(scores)
    fig, axes = plt.subplots(1, n_models, figsize=(5 * n_models, 4))
    
    if n_models == 1:
        axes = [axes]
    
    for ax, (name, score_values) in zip(axes, scores.items()):
        # Separate scores by class
        normal_scores = score_values[y_true == 0]
        anomaly_scores = score_values[y_true == 1]
        
        ax.hist(normal_scores, bins=30, alpha=0.6, label='Normal', color='#2563eb', density=True)
        ax.hist(anomaly_scores, bins=30, alpha=0.6, label='Anomaly', color='#dc2626', density=True)
        ax.set_title(f'{name}', fontsize=11)
        ax.set_xlabel('Anomaly Score')
        ax.set_ylabel('Density')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    out_path = FIG_DIR / 'score_distributions_by_class.png'
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved score distributions to {out_path}")
    plt.close(fig)


def save_metrics_csv(results):
    """Save evaluation metrics to CSV for publication."""
    rows = []
    for name, metrics in results.items():
        rows.append({
            'Model': name,
            'AUPRC': metrics['auprc'],
            'Precision': metrics['precision'],
            'Recall': metrics['recall'],
            'F1-Score': metrics['f1'],
            'Optimal_Threshold': metrics['optimal_threshold'],
            'True_Positives': metrics['true_positives'],
            'False_Positives': metrics['false_positives'],
            'True_Negatives': metrics['true_negatives'],
            'False_Negatives': metrics['false_negatives']
        })
    
    df = pd.DataFrame(rows)
    out_path = RESULTS / 'evaluation_metrics.csv'
    df.to_csv(out_path, index=False)
    print(f"✓ Saved metrics to {out_path}")
    return df


def print_publication_summary(results, df, n_samples, n_anomalies):
    """Print formatted summary for publication."""
    print("\n" + "="*70)
    print("DIS EVALUATION RESULTS - PUBLICATION SUMMARY")
    print("="*70)
    
    print(f"\nDataset Statistics:")
    print(f"  Total samples: {n_samples}")
    print(f"  Anomaly samples: {n_anomalies} ({100*n_anomalies/n_samples:.1f}%)")
    print(f"  Normal samples: {n_samples - n_anomalies} ({100*(n_samples-n_anomalies)/n_samples:.1f}%)")
    print(f"  Features: 9 (cpu_percent, mem_percent, net_tx, net_rx, disk_read,")
    print(f"            disk_write, http_req_rate, response_ms, pod_restarts)")
    
    print(f"\nModel Performance:")
    print("-"*70)
    print(f"{'Model':<25} {'AUPRC':>8} {'Precision':>10} {'Recall':>8} {'F1-Score':>10}")
    print("-"*70)
    
    for _, row in df.iterrows():
        print(f"{row['Model']:<25} {row['AUPRC']:>8.4f} {row['Precision']:>10.4f} "
              f"{row['Recall']:>8.4f} {row['F1-Score']:>10.4f}")
    
    print("-"*70)
    
    # Find best model
    best_idx = df['AUPRC'].idxmax()
    best_model = df.loc[best_idx, 'Model']
    best_auprc = df.loc[best_idx, 'AUPRC']
    
    print(f"\n✓ Best performing model: {best_model} (AUPRC = {best_auprc:.4f})")
    print("="*70)


def main():
    print("="*70)
    print("DIS Model Evaluation - Computing Publication Metrics")
    print("="*70 + "\n")
    
    # Load data
    df = load_data()
    
    # Support both 'is_anomaly' and 'label' columns
    if 'is_anomaly' in df.columns:
        y_true = df['is_anomaly'].values.astype(int)
    elif 'label' in df.columns:
        y_true = df['label'].values.astype(int)
    else:
        raise ValueError("Data must contain 'is_anomaly' or 'label' column")
    
    # Use standard feature columns
    available_cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available_cols].fillna(0).values
    
    n_samples = len(y_true)
    n_anomalies = np.sum(y_true)
    print(f"Loaded {n_samples} samples ({n_anomalies} anomalies, {n_samples - n_anomalies} normal)")
    
    # Load models
    print("\nLoading models...")
    models = load_models()
    
    if not models:
        raise RuntimeError("No models found. Run training scripts first.")
    
    # Compute anomaly scores
    print("\nComputing anomaly scores...")
    scores = compute_anomaly_scores(models, X)
    
    # Compute metrics for each model
    print("\nComputing evaluation metrics...")
    results = {}
    for name, score_values in scores.items():
        results[name] = compute_metrics(y_true, score_values, name)
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    plot_precision_recall_curves(results, y_true)
    plot_confusion_matrices(results, y_true)
    plot_score_distributions(scores, y_true)
    
    # Save metrics to CSV
    metrics_df = save_metrics_csv(results)
    
    # Print publication summary
    print_publication_summary(results, metrics_df, n_samples, n_anomalies)


if __name__ == '__main__':
    main()
