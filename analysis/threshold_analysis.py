"""
Threshold Sensitivity Analysis for DIS Publication.

Provides statistical justification for anomaly detection thresholds:
- Threshold vs. F1/Precision/Recall curves
- Operating point analysis
- Statistical significance of threshold choices

Usage:
  python analysis/threshold_analysis.py

Output:
  - results/threshold_analysis.csv
  - results/threshold_sweep.csv  
  - results/figures/threshold_sensitivity.png
  - results/figures/threshold_sweep.png

Requires: pandas, matplotlib, joblib, numpy, scikit-learn
"""

import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, roc_curve, auc
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / 'data' / 'metrics.csv'
RESULTS = ROOT / 'results'
FIG_DIR = RESULTS / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Load metrics CSV with ground truth labels."""
    if not DATA_CSV.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_CSV}")
    df = pd.read_csv(DATA_CSV)
    
    # Use 'is_anomaly' or 'label' column
    if 'is_anomaly' in df.columns:
        feature_cols = [c for c in df.columns if c not in ['is_anomaly']]
        y = df['is_anomaly'].values
    elif 'label' in df.columns:
        feature_cols = [c for c in df.columns if c not in ['label']]
        y = df['label'].values
    else:
        raise ValueError("Data must contain 'is_anomaly' or 'label' column")
    
    X = df[feature_cols].select_dtypes(include=['number']).fillna(0).values
    
    return X, y, feature_cols, df

def load_models():
    """Load trained models."""
    models = {}
    
    # Try different locations for models
    iforest_paths = [
        RESULTS / 'iforest.joblib', 
        ROOT / 'ml' / 'models' / 'iforest.joblib',
        ROOT / 'models' / 'iforest.joblib'
    ]
    for p in iforest_paths:
        if p.exists():
            models['iforest'] = joblib.load(p)
            print(f"Loaded IsolationForest from: {p}")
            break
    
    ae_paths = [
        RESULTS / 'ae_sklearn.joblib', 
        ROOT / 'ml' / 'models' / 'ae_sklearn.joblib',
        ROOT / 'models' / 'ae_sklearn.joblib'
    ]
    for p in ae_paths:
        if p.exists():
            models['ae_sklearn'] = joblib.load(p)
            print(f"Loaded Autoencoder from: {p}")
            break
            
    return models

def compute_iforest_scores(model_obj, X):
    """Compute IsolationForest anomaly scores."""
    # Handle dict structure from saved model
    if isinstance(model_obj, dict):
        model = model_obj.get('model')
        scaler = model_obj.get('scaler')
    else:
        model = model_obj
        scaler = None
    
    # Apply scaling if available
    X_scaled = scaler.transform(X) if scaler is not None else X
    
    # IsolationForest.score_samples returns higher values for normal points
    # Invert to get anomaly scores (higher = more anomalous)
    scores = model.score_samples(X_scaled)
    return -scores

def compute_ae_scores(model_obj, X):
    """Compute Autoencoder reconstruction error scores."""
    if isinstance(model_obj, dict):
        model = model_obj.get('model')
        scaler = model_obj.get('scaler')
    else:
        model = model_obj
        scaler = None
    
    # Apply scaling if available
    X_scaled = scaler.transform(X) if scaler is not None else X
    
    # Compute reconstruction
    X_recon = model.predict(X_scaled)
    
    # Compute MSE per sample
    mse = np.mean((X_scaled - X_recon) ** 2, axis=1)
    return mse

def threshold_sweep_analysis(scores, y_true, model_name, n_thresholds=100):
    """
    Perform comprehensive threshold sweep analysis.
    
    Returns DataFrame with threshold performance metrics.
    """
    # Define threshold range
    min_score, max_score = np.min(scores), np.max(scores)
    thresholds = np.linspace(min_score, max_score, n_thresholds)
    
    results = []
    
    for threshold in thresholds:
        y_pred = (scores >= threshold).astype(int)
        
        # Compute confusion matrix elements
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        
        # Compute metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        
        results.append({
            'model': model_name,
            'threshold': threshold,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'specificity': specificity,
            'fpr': fpr,
            'fnr': fnr,
            'accuracy': accuracy,
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn
        })
    
    return pd.DataFrame(results)

def find_optimal_thresholds(threshold_df):
    """Find optimal operating points based on different criteria."""
    optimal_points = {}
    
    # Best F1 score
    best_f1_idx = threshold_df['f1_score'].idxmax()
    optimal_points['best_f1'] = {
        'threshold': threshold_df.loc[best_f1_idx, 'threshold'],
        'f1_score': threshold_df.loc[best_f1_idx, 'f1_score'],
        'precision': threshold_df.loc[best_f1_idx, 'precision'],
        'recall': threshold_df.loc[best_f1_idx, 'recall']
    }
    
    # Best precision (minimize false positives)
    best_precision_idx = threshold_df['precision'].idxmax()
    optimal_points['best_precision'] = {
        'threshold': threshold_df.loc[best_precision_idx, 'threshold'],
        'f1_score': threshold_df.loc[best_precision_idx, 'f1_score'],
        'precision': threshold_df.loc[best_precision_idx, 'precision'],
        'recall': threshold_df.loc[best_precision_idx, 'recall']
    }
    
    # Best recall (minimize false negatives)
    best_recall_idx = threshold_df['recall'].idxmax()
    optimal_points['best_recall'] = {
        'threshold': threshold_df.loc[best_recall_idx, 'threshold'],
        'f1_score': threshold_df.loc[best_recall_idx, 'f1_score'],
        'precision': threshold_df.loc[best_recall_idx, 'precision'],
        'recall': threshold_df.loc[best_recall_idx, 'recall']
    }
    
    # Balanced point (precision ≈ recall)
    threshold_df_valid = threshold_df[(threshold_df['precision'] > 0) & (threshold_df['recall'] > 0)]
    if len(threshold_df_valid) > 0:
        threshold_df_valid = threshold_df_valid.copy()
        threshold_df_valid['balance_diff'] = np.abs(threshold_df_valid['precision'] - threshold_df_valid['recall'])
        balanced_idx = threshold_df_valid['balance_diff'].idxmin()
        optimal_points['balanced'] = {
            'threshold': threshold_df.loc[balanced_idx, 'threshold'],
            'f1_score': threshold_df.loc[balanced_idx, 'f1_score'],
            'precision': threshold_df.loc[balanced_idx, 'precision'],
            'recall': threshold_df.loc[balanced_idx, 'recall']
        }
    
    return optimal_points

def plot_threshold_sensitivity(threshold_dfs, model_names):
    """Plot threshold sensitivity curves."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Threshold Sensitivity Analysis', fontsize=16)
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(model_names)))
    
    for i, (model_name, df) in enumerate(zip(model_names, threshold_dfs)):
        color = colors[i]
        
        # F1 Score vs Threshold
        axes[0, 0].plot(df['threshold'], df['f1_score'], label=model_name, color=color)
        axes[0, 0].set_xlabel('Threshold')
        axes[0, 0].set_ylabel('F1 Score')
        axes[0, 0].set_title('F1 Score vs Threshold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Precision vs Recall
        axes[0, 1].plot(df['recall'], df['precision'], label=model_name, color=color)
        axes[0, 1].set_xlabel('Recall')
        axes[0, 1].set_ylabel('Precision')
        axes[0, 1].set_title('Precision-Recall Curve')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Precision and Recall vs Threshold
        axes[1, 0].plot(df['threshold'], df['precision'], label=f'{model_name} Precision', 
                       color=color, linestyle='-')
        axes[1, 0].plot(df['threshold'], df['recall'], label=f'{model_name} Recall', 
                       color=color, linestyle='--')
        axes[1, 0].set_xlabel('Threshold')
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].set_title('Precision & Recall vs Threshold')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # ROC-style: FPR vs TPR (Recall)
        axes[1, 1].plot(df['fpr'], df['recall'], label=model_name, color=color)
        axes[1, 1].set_xlabel('False Positive Rate')
        axes[1, 1].set_ylabel('True Positive Rate (Recall)')
        axes[1, 1].set_title('ROC-style Curve')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_path = FIG_DIR / 'threshold_sensitivity.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved threshold sensitivity plot to: {output_path}")
    plt.close()

def plot_threshold_sweep(threshold_dfs, model_names):
    """Plot detailed threshold sweep analysis."""
    fig, axes = plt.subplots(1, len(model_names), figsize=(5*len(model_names), 6))
    
    if len(model_names) == 1:
        axes = [axes]
    
    fig.suptitle('Threshold Sweep Analysis', fontsize=16)
    
    for i, (model_name, df) in enumerate(zip(model_names, threshold_dfs)):
        ax = axes[i]
        
        # Plot multiple metrics
        ax.plot(df['threshold'], df['f1_score'], label='F1 Score', linewidth=2)
        ax.plot(df['threshold'], df['precision'], label='Precision', alpha=0.7)
        ax.plot(df['threshold'], df['recall'], label='Recall', alpha=0.7)
        ax.plot(df['threshold'], df['accuracy'], label='Accuracy', alpha=0.7)
        
        # Mark optimal F1 point
        best_f1_idx = df['f1_score'].idxmax()
        best_f1_threshold = df.loc[best_f1_idx, 'threshold']
        best_f1_score = df.loc[best_f1_idx, 'f1_score']
        
        ax.axvline(x=best_f1_threshold, color='red', linestyle=':', alpha=0.7, 
                  label=f'Optimal F1 ({best_f1_score:.3f})')
        ax.scatter([best_f1_threshold], [best_f1_score], color='red', s=50, zorder=10)
        
        ax.set_xlabel('Threshold')
        ax.set_ylabel('Metric Score')
        ax.set_title(f'{model_name}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.05)
    
    plt.tight_layout()
    
    output_path = FIG_DIR / 'threshold_sweep.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved threshold sweep plot to: {output_path}")
    plt.close()

def statistical_analysis(threshold_dfs, optimal_points_dict):
    """Perform statistical analysis of threshold choices."""
    analysis_results = []
    
    for model_name, threshold_df in zip(optimal_points_dict.keys(), threshold_dfs):
        optimal_points = optimal_points_dict[model_name]
        
        # Compute statistics around optimal F1 threshold
        best_f1_threshold = optimal_points['best_f1']['threshold']
        
        # Find thresholds within ±10% of optimal
        threshold_range = np.abs(threshold_df['threshold'].max() - threshold_df['threshold'].min())
        window = 0.1 * threshold_range
        
        nearby_thresholds = threshold_df[
            np.abs(threshold_df['threshold'] - best_f1_threshold) <= window
        ]
        
        if len(nearby_thresholds) > 0:
            f1_std = nearby_thresholds['f1_score'].std()
            f1_mean = nearby_thresholds['f1_score'].mean()
            
            analysis_results.append({
                'model': model_name,
                'optimal_threshold': best_f1_threshold,
                'optimal_f1': optimal_points['best_f1']['f1_score'],
                'f1_std_in_window': f1_std,
                'f1_mean_in_window': f1_mean,
                'threshold_sensitivity': f1_std / f1_mean if f1_mean > 0 else 0,
                'window_size': len(nearby_thresholds),
                'total_thresholds': len(threshold_df)
            })
    
    return pd.DataFrame(analysis_results)

def main():
    """Run complete threshold analysis."""
    print("Starting Threshold Sensitivity Analysis...")
    
    # Load data and models
    X, y, feature_names, df = load_data()
    models = load_models()
    
    if not models:
        print("No trained models found. Please train models first.")
        return
    
    print(f"Loaded data: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Ground truth distribution: {np.bincount(y)}")
    print(f"Available models: {list(models.keys())}")
    
    # Perform threshold sweep for each model
    all_threshold_dfs = []
    all_optimal_points = {}
    model_names = []
    
    if 'iforest' in models:
        print("Analyzing IsolationForest thresholds...")
        iforest_scores = compute_iforest_scores(models['iforest'], X)
        
        threshold_df = threshold_sweep_analysis(iforest_scores, y, 'IsolationForest')
        optimal_points = find_optimal_thresholds(threshold_df)
        
        all_threshold_dfs.append(threshold_df)
        all_optimal_points['IsolationForest'] = optimal_points
        model_names.append('IsolationForest')
        
        print(f"  Optimal F1 threshold: {optimal_points['best_f1']['threshold']:.4f}")
        print(f"  F1: {optimal_points['best_f1']['f1_score']:.3f}, "
              f"Precision: {optimal_points['best_f1']['precision']:.3f}, "
              f"Recall: {optimal_points['best_f1']['recall']:.3f}")
    
    if 'ae_sklearn' in models:
        print("Analyzing Autoencoder thresholds...")
        ae_scores = compute_ae_scores(models['ae_sklearn'], X)
        
        threshold_df = threshold_sweep_analysis(ae_scores, y, 'Autoencoder')
        optimal_points = find_optimal_thresholds(threshold_df)
        
        all_threshold_dfs.append(threshold_df)
        all_optimal_points['Autoencoder'] = optimal_points
        model_names.append('Autoencoder')
        
        print(f"  Optimal F1 threshold: {optimal_points['best_f1']['threshold']:.4f}")
        print(f"  F1: {optimal_points['best_f1']['f1_score']:.3f}, "
              f"Precision: {optimal_points['best_f1']['precision']:.3f}, "
              f"Recall: {optimal_points['best_f1']['recall']:.3f}")
    
    if not all_threshold_dfs:
        print("No models available for threshold analysis.")
        return
    
    # Combine all threshold data
    all_thresholds_df = pd.concat(all_threshold_dfs, ignore_index=True)
    
    # Save threshold sweep results
    threshold_sweep_path = RESULTS / 'threshold_sweep.csv'
    all_thresholds_df.to_csv(threshold_sweep_path, index=False)
    print(f"Saved threshold sweep results to: {threshold_sweep_path}")
    
    # Create summary of optimal points
    summary_results = []
    for model_name, optimal_points in all_optimal_points.items():
        for criterion, metrics in optimal_points.items():
            summary_results.append({
                'model': model_name,
                'criterion': criterion,
                **metrics
            })
    
    summary_df = pd.DataFrame(summary_results)
    threshold_analysis_path = RESULTS / 'threshold_analysis.csv'
    summary_df.to_csv(threshold_analysis_path, index=False)
    print(f"Saved threshold analysis summary to: {threshold_analysis_path}")
    
    # Statistical analysis
    stats_df = statistical_analysis(all_threshold_dfs, all_optimal_points)
    if len(stats_df) > 0:
        print("\nThreshold Sensitivity Statistics:")
        for _, row in stats_df.iterrows():
            sensitivity = row['threshold_sensitivity']
            if sensitivity < 0.05:
                stability = "Very Stable"
            elif sensitivity < 0.1:
                stability = "Stable"
            elif sensitivity < 0.2:
                stability = "Moderate"
            else:
                stability = "Sensitive"
            
            print(f"  {row['model']}: Sensitivity = {sensitivity:.4f} ({stability})")
    
    # Generate plots
    plot_threshold_sensitivity(all_threshold_dfs, model_names)
    plot_threshold_sweep(all_threshold_dfs, model_names)
    
    print("Threshold analysis complete!")

if __name__ == '__main__':
    main()