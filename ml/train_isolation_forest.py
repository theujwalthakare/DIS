"""
Train an Isolation Forest on pre-collected metrics CSV.

Usage:
  python train_isolation_forest.py --input data/metrics.csv --out ml/models/iforest.joblib

This represents the unsupervised T-Helper detection layer in simplified form.
"""
import argparse
import os
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Standard feature columns for 100K dataset
FEATURE_COLS = ['cpu_percent', 'mem_percent', 'net_tx', 'net_rx',
                'disk_read', 'disk_write', 'http_req_rate', 'response_ms']

def main(input_csv, out_path):
    df = pd.read_csv(input_csv)
    
    # Use standard feature columns
    available_cols = [c for c in FEATURE_COLS if c in df.columns]
    if len(available_cols) < len(FEATURE_COLS):
        print(f'Warning: Only {len(available_cols)}/{len(FEATURE_COLS)} features available')
    
    # Train only on normal data if anomaly column exists
    anomaly_col = None
    if 'is_anomaly' in df.columns:
        anomaly_col = 'is_anomaly'
    elif 'label' in df.columns:
        anomaly_col = 'label'
    
    if anomaly_col:
        df_normal = df[df[anomaly_col] == 0]
        print(f'Training on {len(df_normal)} normal samples (excluded {len(df) - len(df_normal)} anomalies)')
    else:
        df_normal = df
        print(f'Training on {len(df_normal)} samples (no anomaly labels found)')
    
    X = df_normal[available_cols].fillna(0).values
    
    # Apply StandardScaler for consistent evaluation
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    
    # Improved hyperparameters for better recall
    # - More estimators for better generalization
    # - Larger max_samples to capture more patterns
    # - Lower contamination estimate for tighter boundary
    model = IsolationForest(
        n_estimators=300,           # Increased from 200
        max_samples=min(20000, len(Xs)),  # Increased from 10000
        contamination=0.01,         # Explicit low contamination for tighter boundary
        max_features=1.0,           # Use all features
        bootstrap=True,             # Bootstrap sampling for diversity
        random_state=42,
        n_jobs=-1
    )
    model.fit(Xs)
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # Save model with scaler for consistent evaluation
    joblib.dump({'model': model, 'scaler': scaler, 'feature_cols': available_cols}, out_path)
    print(f'Saved Isolation Forest to {out_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/metrics.csv', help='Input CSV file')
    parser.add_argument('--out', default='ml/models/iforest.joblib', help='Output model file')
    args = parser.parse_args()
    main(args.input, args.out)
