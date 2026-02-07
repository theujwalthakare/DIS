"""
Baseline Comparison for DIS Publication.

Compares the DIS anomaly detection approach against standard baseline methods:
- Local Outlier Factor (LOF)
- Elliptic Envelope (robust covariance)
- One-Class SVM
- Simple threshold-based detection (statistical)

Usage:
  python analysis/compare_baselines.py

Output:
  - results/figures/baseline_comparison.png
  - results/baseline_comparison.csv
  - Console output with comparison table
"""
from pathlib import Path
import time
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_recall_curve, auc, f1_score, precision_score, recall_score

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
    return pd.read_csv(DATA_CSV)


def load_dis_models():
    """Load trained DIS models (Isolation Forest, Autoencoder, OCSVM)."""
    models = {}
    
    iforest_paths = [RESULTS / 'iforest.joblib', ROOT / 'ml' / 'models' / 'iforest.joblib']
    for p in iforest_paths:
        if p.exists():
            models['DIS: Isolation Forest'] = ('iforest', joblib.load(p))
            break
    
    ae_paths = [RESULTS / 'ae_sklearn.joblib', ROOT / 'ml' / 'models' / 'ae_sklearn.joblib']
    for p in ae_paths:
        if p.exists():
            models['DIS: Autoencoder'] = ('ae', joblib.load(p))
            break
    
    ocsvm_paths = [RESULTS / 'ocsvm.joblib', ROOT / 'ml' / 'models' / 'ocsvm.joblib']
    for p in ocsvm_paths:
        if p.exists():
            models['DIS: One-Class SVM'] = ('ocsvm', joblib.load(p))
            break
    
    return models


def create_baseline_models(X_train, contamination_ratio, max_samples=10000):
    """Create and train baseline anomaly detection models.
    
    For slow baselines, samples data if n_samples > max_samples.
    """
    baselines = {}
    
    # Sample if dataset is too large for slow algorithms
    if len(X_train) > max_samples:
        print(f"  Sampling {max_samples} samples for slow baselines (from {len(X_train)})")
        indices = np.random.choice(len(X_train), max_samples, replace=False)
        X_sample = X_train[indices]
    else:
        X_sample = X_train
    
    # Local Outlier Factor
    print("  Training Local Outlier Factor...")
    lof = LocalOutlierFactor(n_neighbors=20, contamination=contamination_ratio, novelty=True)
    lof.fit(X_sample)
    baselines['Baseline: LOF'] = ('lof', lof)
    
    # Elliptic Envelope (robust covariance)
    print("  Training Elliptic Envelope...")
    try:
        ee = EllipticEnvelope(contamination=contamination_ratio, random_state=42)
        ee.fit(X_sample)
        baselines['Baseline: Elliptic Envelope'] = ('ee', ee)
    except Exception as e:
        print(f"    Warning: Elliptic Envelope failed - {e}")
    
    # One-Class SVM
    print("  Training One-Class SVM...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_sample)
    ocsvm = OneClassSVM(kernel='rbf', gamma='auto', nu=contamination_ratio)
    ocsvm.fit(X_scaled)
    baselines['Baseline: One-Class SVM'] = ('ocsvm', (ocsvm, scaler))
    
    # Statistical threshold (Z-score based)
    print("  Computing Statistical Baseline...")
    mean = np.mean(X_train, axis=0)
    std = np.std(X_train, axis=0) + 1e-10
    baselines['Baseline: Z-Score'] = ('zscore', (mean, std))
    
    return baselines


def compute_scores(models, X, model_type, model_obj):
    """Compute anomaly scores for a model."""
    if model_type == 'iforest':
        # Handle dict format with scaler
        if isinstance(model_obj, dict):
            model = model_obj.get('model')
            scaler = model_obj.get('scaler')
            Xs = scaler.transform(X) if scaler is not None else X
        else:
            model = model_obj
            Xs = X
        return -model.score_samples(Xs)  # Negate so higher = anomalous
    
    elif model_type == 'ae':
        ae = model_obj
        model = ae.get('model') if isinstance(ae, dict) else ae
        scaler = ae.get('scaler') if isinstance(ae, dict) else None
        Xs = scaler.transform(X) if scaler is not None else X
        recon = model.predict(Xs)
        return np.mean((Xs - recon) ** 2, axis=1)
    
    elif model_type == 'lof':
        return -model_obj.score_samples(X)  # Negate so higher = anomalous
    
    elif model_type == 'ee':
        return -model_obj.score_samples(X)  # Negate so higher = anomalous
    
    elif model_type == 'ocsvm':
        # Handle both dict format (DIS) and tuple format (baseline)
        if isinstance(model_obj, dict):
            model = model_obj.get('model')
            scaler = model_obj.get('scaler')
            Xs = scaler.transform(X) if scaler is not None else X
            return -model.decision_function(Xs)  # Negate so higher = anomalous
        else:
            ocsvm, scaler = model_obj
            X_scaled = scaler.transform(X)
            return -ocsvm.decision_function(X_scaled)  # Negate so higher = anomalous
    
    elif model_type == 'ensemble':
        # Weighted ensemble - compute component scores and combine
        config = model_obj
        weights = config.get('weights', {})
        
        # Compute scores for each component model
        scores_dict = {}
        for name in weights.keys():
            if name == 'iforest' and 'DIS: Isolation Forest' in models:
                _, m = models['DIS: Isolation Forest']
                scores_dict[name] = compute_scores(models, X, 'iforest', m)
            elif name == 'ocsvm' and 'DIS: One-Class SVM' in models:
                _, m = models['DIS: One-Class SVM']
                scores_dict[name] = compute_scores(models, X, 'ocsvm', m)
            elif name == 'ae' and 'DIS: Autoencoder' in models:
                _, m = models['DIS: Autoencoder']
                scores_dict[name] = compute_scores(models, X, 'ae', m)
        
        if not scores_dict:
            return None
        
        # Normalize and combine
        normalized = {}
        for name, s in scores_dict.items():
            s_norm = (s - s.min()) / (s.max() - s.min() + 1e-10)
            normalized[name] = s_norm
        
        ensemble_scores = np.zeros(len(X))
        for name, s_norm in normalized.items():
            w = weights.get(name, 1.0 / len(normalized))
            ensemble_scores += w * s_norm
        
        return ensemble_scores
    
    elif model_type == 'zscore':
        mean, std = model_obj
        z_scores = np.abs((X - mean) / std)
        return np.max(z_scores, axis=1)  # Max z-score across features
    
    return None


def evaluate_model(y_true, scores, model_name):
    """Compute evaluation metrics for a model."""
    # Normalize scores to [0, 1]
    scores_norm = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    
    # Precision-Recall curve
    precision, recall, thresholds = precision_recall_curve(y_true, scores_norm)
    auprc = auc(recall, precision)
    
    # Find optimal threshold (maximize F1)
    f1_scores = 2 * (precision[:-1] * recall[:-1]) / (precision[:-1] + recall[:-1] + 1e-10)
    optimal_idx = np.argmax(f1_scores) if len(f1_scores) > 0 else 0
    optimal_threshold = thresholds[optimal_idx] if len(thresholds) > 0 else 0.5
    
    # Binary predictions
    y_pred = (scores_norm >= optimal_threshold).astype(int)
    
    return {
        'model': model_name,
        'auprc': auprc,
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1': f1_score(y_true, y_pred, zero_division=0),
        'precision_curve': precision,
        'recall_curve': recall,
        'scores': scores_norm
    }


def plot_comparison_curves(results, y_true):
    """Plot comparison precision-recall curves."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # DIS models in solid lines, baselines in dashed
    dis_colors = ['#2563eb', '#16a34a']  # Blue, Green
    baseline_colors = ['#dc2626', '#f97316', '#8b5cf6', '#64748b']  # Red, Orange, Purple, Gray
    
    dis_idx = 0
    baseline_idx = 0
    
    for name, metrics in results.items():
        if 'DIS' in name:
            color = dis_colors[dis_idx % len(dis_colors)]
            linestyle = '-'
            linewidth = 2.5
            dis_idx += 1
        else:
            color = baseline_colors[baseline_idx % len(baseline_colors)]
            linestyle = '--'
            linewidth = 1.8
            baseline_idx += 1
        
        ax.plot(
            metrics['recall_curve'],
            metrics['precision_curve'],
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            label=f"{name} (AUPRC={metrics['auprc']:.4f})"
        )
    
    # Random baseline
    baseline = np.sum(y_true) / len(y_true)
    ax.axhline(y=baseline, color='gray', linestyle=':', linewidth=1.5,
               label=f'Random ({baseline:.3f})')
    
    ax.set_xlabel('Recall', fontsize=12)
    ax.set_ylabel('Precision', fontsize=12)
    ax.set_title('DIS vs. Baseline Methods: Precision-Recall Comparison', fontsize=14)
    ax.legend(loc='lower left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    
    fig.tight_layout()
    out_path = FIG_DIR / 'baseline_comparison.png'
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved baseline comparison to {out_path}")
    plt.close(fig)


def plot_metric_bars(results):
    """Plot bar chart comparing key metrics."""
    models = list(results.keys())
    metrics = ['auprc', 'precision', 'recall', 'f1']
    metric_labels = ['AUPRC', 'Precision', 'Recall', 'F1-Score']
    
    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    
    # Separate DIS and baseline models
    dis_models = [m for m in models if 'DIS' in m]
    baseline_models = [m for m in models if 'Baseline' in m]
    all_models = dis_models + baseline_models
    
    colors = ['#2563eb', '#16a34a'] + ['#dc2626', '#f97316', '#8b5cf6', '#64748b']
    
    for ax, metric, label in zip(axes, metrics, metric_labels):
        values = [results[m][metric] for m in all_models]
        bars = ax.bar(range(len(all_models)), values, color=colors[:len(all_models)])
        
        ax.set_ylabel(label)
        ax.set_xticks(range(len(all_models)))
        ax.set_xticklabels([m.split(': ')[1] for m in all_models], rotation=45, ha='right', fontsize=9)
        ax.set_ylim([0, 1.05])
        ax.grid(True, axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                   f'{val:.3f}', ha='center', va='bottom', fontsize=8)
    
    fig.suptitle('Performance Comparison: DIS vs. Baseline Methods', fontsize=14, y=1.02)
    fig.tight_layout()
    
    out_path = FIG_DIR / 'baseline_metrics_comparison.png'
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved metrics comparison to {out_path}")
    plt.close(fig)


def save_comparison_csv(results):
    """Save comparison results to CSV."""
    rows = []
    for name, metrics in results.items():
        rows.append({
            'Model': name,
            'Category': 'DIS' if 'DIS' in name else 'Baseline',
            'AUPRC': metrics['auprc'],
            'Precision': metrics['precision'],
            'Recall': metrics['recall'],
            'F1-Score': metrics['f1']
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values('AUPRC', ascending=False)
    
    out_path = RESULTS / 'baseline_comparison.csv'
    df.to_csv(out_path, index=False)
    print(f"✓ Saved comparison to {out_path}")
    return df


def print_comparison_table(df):
    """Print formatted comparison table."""
    print("\n" + "="*80)
    print("DIS vs. BASELINE METHODS - PUBLICATION COMPARISON")
    print("="*80)
    
    print(f"\n{'Rank':<5} {'Model':<30} {'AUPRC':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-"*80)
    
    for i, (_, row) in enumerate(df.iterrows(), 1):
        marker = "★" if row['Category'] == 'DIS' else " "
        print(f"{i:<5} {marker}{row['Model']:<29} {row['AUPRC']:>10.4f} "
              f"{row['Precision']:>10.4f} {row['Recall']:>10.4f} {row['F1-Score']:>10.4f}")
    
    print("-"*80)
    
    # Summary statistics
    dis_df = df[df['Category'] == 'DIS']
    baseline_df = df[df['Category'] == 'Baseline']
    
    print(f"\nSummary:")
    print(f"  DIS Average AUPRC:      {dis_df['AUPRC'].mean():.4f}")
    print(f"  Baseline Average AUPRC: {baseline_df['AUPRC'].mean():.4f}")
    print(f"  Improvement:            {(dis_df['AUPRC'].mean() - baseline_df['AUPRC'].mean())*100:.1f}%")
    
    best_model = df.iloc[0]['Model']
    print(f"\n✓ Best Overall: {best_model} (AUPRC = {df.iloc[0]['AUPRC']:.4f})")
    print("="*80)


def main():
    print("="*80)
    print("DIS Baseline Comparison - Evaluating Against Standard Methods")
    print("="*80 + "\n")
    
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
    contamination_ratio = n_anomalies / n_samples
    
    print(f"Dataset: {n_samples} samples ({n_anomalies} anomalies, {contamination_ratio*100:.1f}%)")
    
    # Load DIS models
    print("\nLoading DIS models...")
    dis_models = load_dis_models()
    for name in dis_models:
        print(f"  [OK] {name}")
    
    # Train on normal data only for novelty detection
    X_normal = X[y_true == 0]
    print(f"\nTraining baseline models on {len(X_normal)} normal samples...")
    
    baseline_models = create_baseline_models(X_normal, contamination_ratio)
    
    # Combine all models
    all_models = {**dis_models, **baseline_models}
    
    # Evaluate all models
    print("\nEvaluating models...")
    results = {}
    
    # For very slow methods (OCSVM), sample the evaluation data
    MAX_EVAL_SAMPLES = 20000
    if len(X) > MAX_EVAL_SAMPLES:
        np.random.seed(42)
        eval_idx = np.random.choice(len(X), MAX_EVAL_SAMPLES, replace=False)
        X_eval = X.iloc[eval_idx] if hasattr(X, 'iloc') else X[eval_idx]
        y_eval = y_true.iloc[eval_idx] if hasattr(y_true, 'iloc') else y_true[eval_idx]
        print(f"  (Using {MAX_EVAL_SAMPLES} samples for slow methods)")
    else:
        X_eval = X
        y_eval = y_true
    
    for name, (model_type, model_obj) in all_models.items():
        try:
            # Use sampled data for OCSVM which is very slow
            if model_type == 'ocsvm':
                scores = compute_scores(all_models, X_eval, model_type, model_obj)
                results[name] = evaluate_model(y_eval, scores, name)
            else:
                scores = compute_scores(all_models, X, model_type, model_obj)
                results[name] = evaluate_model(y_true, scores, name)
            print(f"  ✓ {name}: AUPRC = {results[name]['auprc']:.4f}")
        except Exception as e:
            print(f"  ✗ {name}: Failed - {e}")
    
    # Generate visualizations
    print("\nGenerating comparison visualizations...")
    plot_comparison_curves(results, y_true)
    plot_metric_bars(results)
    
    # Save results
    comparison_df = save_comparison_csv(results)
    
    # Print summary
    print_comparison_table(comparison_df)


if __name__ == '__main__':
    main()
