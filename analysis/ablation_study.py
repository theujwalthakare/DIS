"""
Ablation Study for DIS Publication.

Systematically evaluates design choices to justify the ensemble approach:
- Individual model performance vs. ensemble combination strategy
- Feature importance analysis  
- Operating point analysis

Usage:
  python analysis/ablation_study.py

Output:
  - results/ablation_study.csv
  - results/figures/ablation_**.png

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

def evaluate_model(scores, y_true, model_name):
    """Evaluate single model performance."""
    # Convert scores to binary predictions using optimal threshold
    fpr, tpr, thresholds = roc_curve(y_true, scores)
    roc_auc = auc(fpr, tpr)
    
    # Find optimal threshold (maximize F1)
    precision, recall, pr_thresholds = precision_recall_curve(y_true, scores)
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = pr_thresholds[optimal_idx] if optimal_idx < len(pr_thresholds) else np.median(scores)
    
    y_pred = (scores >= optimal_threshold).astype(int)
    
    metrics = {
        'model': model_name,
        'roc_auc': roc_auc,
        'precision': precision_score(y_true, y_pred),
        'recall': recall_score(y_true, y_pred),
        'f1_score': f1_score(y_true, y_pred),
        'optimal_threshold': optimal_threshold
    }
    
    return metrics, (fpr, tpr), (precision, recall)

def ensemble_combination_study(iforest_scores, ae_scores, y_true):
    """Study different ensemble combination strategies."""
    results = []
    
    # Strategy 1: Simple average
    if iforest_scores is not None and ae_scores is not None:
        # Normalize scores to [0,1] range
        if_norm = (iforest_scores - np.min(iforest_scores)) / (np.ptp(iforest_scores) + 1e-8)
        ae_norm = (ae_scores - np.min(ae_scores)) / (np.ptp(ae_scores) + 1e-8)
        
        avg_scores = (if_norm + ae_norm) / 2
        metrics, _, _ = evaluate_model(avg_scores, y_true, 'Ensemble_Average')
        results.append(metrics)
        
        # Strategy 2: Weighted average (favor IsolationForest)
        weighted_scores = 0.7 * if_norm + 0.3 * ae_norm
        metrics, _, _ = evaluate_model(weighted_scores, y_true, 'Ensemble_Weighted')
        results.append(metrics)
        
        # Strategy 3: Max (union - either model flags anomaly)
        max_scores = np.maximum(if_norm, ae_norm)
        metrics, _, _ = evaluate_model(max_scores, y_true, 'Ensemble_Max')
        results.append(metrics)
    
    return results

def feature_importance_analysis(X, y, feature_names, iforest_model):
    """Analyze feature importance for anomaly detection."""
    if iforest_model is None:
        return None
        
    # Compute baseline performance
    baseline_scores = compute_iforest_scores(iforest_model, X)
    baseline_metrics, _, _ = evaluate_model(baseline_scores, y, 'Baseline')
    baseline_f1 = baseline_metrics['f1_score']
    
    importance_results = []
    
    # Feature removal analysis
    for i, feature_name in enumerate(feature_names):
        # Create dataset with this feature masked (set to mean/median)
        X_masked = X.copy()
        # Replace feature with mean value to mask its effect
        X_masked[:, i] = np.mean(X_masked[:, i])
        
        try:
            masked_scores = compute_iforest_scores(iforest_model, X_masked)
            masked_metrics, _, _ = evaluate_model(masked_scores, y, f'Without_{feature_name}')
            
            importance = baseline_f1 - masked_metrics['f1_score']
            importance_results.append({
                'feature': feature_name,
                'importance': importance,
                'f1_without': masked_metrics['f1_score'],
                'f1_baseline': baseline_f1
            })
        except Exception as e:
            print(f"Failed to evaluate without {feature_name}: {e}")
    
    return sorted(importance_results, key=lambda x: x['importance'], reverse=True)

def plot_roc_curves(results_data):
    """Plot ROC curves for comparison."""
    plt.figure(figsize=(10, 8))
    
    for model_name, (fpr, tpr) in results_data:
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f'{model_name} (AUC = {roc_auc:.3f})')
    
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves - Model Comparison')
    plt.legend()
    plt.grid(True)
    
    output_path = FIG_DIR / 'ablation_roc_curves.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved ROC curves to: {output_path}")
    plt.close()

def plot_feature_importance(importance_results):
    """Plot feature importance analysis."""
    if not importance_results:
        return
        
    features = [r['feature'] for r in importance_results]
    importances = [r['importance'] for r in importance_results]
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(range(len(features)), importances)
    plt.xlabel('Features')
    plt.ylabel('F1 Score Drop (Importance)')
    plt.title('Feature Importance Analysis')
    plt.xticks(range(len(features)), features, rotation=45, ha='right')
    
    # Color bars by importance
    max_importance = max(importances) if importances else 1
    for bar, importance in zip(bars, importances):
        normalized = importance / max_importance if max_importance > 0 else 0
        bar.set_color(plt.cm.RdYlBu_r(normalized))
    
    plt.grid(True, alpha=0.3)
    
    output_path = FIG_DIR / 'ablation_feature_importance.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved feature importance to: {output_path}")
    plt.close()

def main():
    """Run complete ablation study."""
    print("Starting Ablation Study...")
    
    # Load data and models
    X, y, feature_names, df = load_data()
    models = load_models()
    
    if not models:
        print("No trained models found. Please train models first.")
        return
    
    print(f"Loaded data: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Ground truth distribution: {np.bincount(y)}")
    print(f"Available models: {list(models.keys())}")
    
    # Evaluate individual models
    all_results = []
    roc_data = []
    
    iforest_scores = None
    ae_scores = None
    
    if 'iforest' in models:
        iforest_scores = compute_iforest_scores(models['iforest'], X)
        metrics, roc_data_if, _ = evaluate_model(iforest_scores, y, 'IsolationForest')
        all_results.append(metrics)
        roc_data.append(('IsolationForest', roc_data_if))
        print(f"IsolationForest - F1: {metrics['f1_score']:.3f}, AUC: {metrics['roc_auc']:.3f}")
    
    if 'ae_sklearn' in models:
        ae_scores = compute_ae_scores(models['ae_sklearn'], X)
        metrics, roc_data_ae, _ = evaluate_model(ae_scores, y, 'Autoencoder')
        all_results.append(metrics)
        roc_data.append(('Autoencoder', roc_data_ae))
        print(f"Autoencoder - F1: {metrics['f1_score']:.3f}, AUC: {metrics['roc_auc']:.3f}")
    
    # Ensemble combination study
    ensemble_results = ensemble_combination_study(iforest_scores, ae_scores, y)
    all_results.extend(ensemble_results)
    
    for result in ensemble_results:
        print(f"{result['model']} - F1: {result['f1_score']:.3f}, AUC: {result['roc_auc']:.3f}")
    
    # Feature importance analysis
    if 'iforest' in models:
        print("\nPerforming feature importance analysis...")
        importance_results = feature_importance_analysis(X, y, feature_names, models['iforest'])
        
        if importance_results:
            print("Top 3 most important features:")
            for i, result in enumerate(importance_results[:3]):
                print(f"  {i+1}. {result['feature']}: {result['importance']:.4f}")
            
            plot_feature_importance(importance_results)
    
    # Save results
    results_df = pd.DataFrame(all_results)
    results_path = RESULTS / 'ablation_study.csv'
    results_df.to_csv(results_path, index=False)
    print(f"Saved results to: {results_path}")
    
    # Plot comparisons
    if roc_data:
        plot_roc_curves(roc_data)
    
    print("Ablation study complete!")

if __name__ == '__main__':
    main()