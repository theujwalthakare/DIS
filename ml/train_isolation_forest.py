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

def main(input_csv, out_path):
    df = pd.read_csv(input_csv)
    # Select numeric columns, exclude 'label' if present
    feature_cols = [c for c in df.columns if c != 'label']
    X = df[feature_cols].select_dtypes(include=['number']).fillna(0)
    model = IsolationForest(n_estimators=100, contamination='auto', random_state=42)
    model.fit(X)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump(model, out_path)
    print('Saved Isolation Forest to', out_path)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    main(args.input, args.out)
