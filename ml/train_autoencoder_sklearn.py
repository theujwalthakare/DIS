"""
Train a simple autoencoder using scikit-learn's MLPRegressor.

This provides a TensorFlow-free alternative for environments where TensorFlow
is unavailable (e.g., Python 3.14). It trains a model to reconstruct inputs
and saves the trained regressor and a scaler.

Usage:
  python ml/train_autoencoder_sklearn.py --input data/metrics.csv --out ml/models/ae_sklearn.joblib
"""
import argparse
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

def main(input_csv, out_path):
    df = pd.read_csv(input_csv)
    # Exclude 'label' column if present
    feature_cols = [c for c in df.columns if c != 'label']
    X = df[feature_cols].select_dtypes(include=['number']).fillna(0).values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    # MLPRegressor as an autoencoder: input->hidden->input reconstruction
    # hidden_layer_sizes controls the bottleneck size; adjust for experiments
    model = MLPRegressor(hidden_layer_sizes=(32, 8, 32), activation='relu',
                         max_iter=500, random_state=42)
    model.fit(Xs, Xs)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump({'model': model, 'scaler': scaler}, out_path)
    print('Saved sklearn autoencoder to', out_path)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    main(args.input, args.out)
