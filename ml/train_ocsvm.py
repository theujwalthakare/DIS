"""
Train a One-Class SVM for anomaly detection.

One-Class SVM showed the best performance in baseline comparisons,
so we add it to the DIS ensemble to improve overall detection.

Usage:
  python ml/train_ocsvm.py --input data/metrics.csv --out ml/models/ocsvm.joblib
"""
import argparse
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.svm import OneClassSVM
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
    
    # Sample for training if dataset is large (OCSVM is O(n²) memory)
    max_train_samples = 15000
    if len(Xs) > max_train_samples:
        print(f'Sampling {max_train_samples} samples for training (OCSVM memory constraint)')
        indices = np.random.RandomState(42).choice(len(Xs), max_train_samples, replace=False)
        Xs_train = Xs[indices]
    else:
        Xs_train = Xs
    
    # One-Class SVM with RBF kernel - optimized parameters
    print('Training One-Class SVM (this may take a few minutes)...')
    model = OneClassSVM(
        kernel='rbf',
        gamma='scale',  # 1/(n_features * X.var())
        nu=0.05,        # Upper bound on fraction of outliers
        cache_size=1000  # MB of cache for faster training
    )
    model.fit(Xs_train)
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # Save model with scaler for consistent evaluation
    joblib.dump({'model': model, 'scaler': scaler, 'feature_cols': available_cols}, out_path)
    print(f'Saved One-Class SVM to {out_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/metrics.csv', help='Input CSV file')
    parser.add_argument('--out', default='ml/models/ocsvm.joblib', help='Output model file')
    args = parser.parse_args()
    main(args.input, args.out)
