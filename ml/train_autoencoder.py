"""
Minimal Autoencoder trainer using Keras.

Usage:
  python train_autoencoder.py --input data/metrics.csv --out ml/models/autoencoder

The autoencoder complements Isolation Forest as an alternative unsupervised
detector in the T-Helper layer.
"""
import argparse
import os
import pandas as pd
from tensorflow.keras import layers, models

def build_autoencoder(input_dim, latent_dim=8):
    inputs = layers.Input(shape=(input_dim,))
    x = layers.Dense(64, activation='relu')(inputs)
    x = layers.Dense(32, activation='relu')(x)
    z = layers.Dense(latent_dim, activation='relu')(x)
    x = layers.Dense(32, activation='relu')(z)
    x = layers.Dense(64, activation='relu')(x)
    outputs = layers.Dense(input_dim, activation='linear')(x)
    model = models.Model(inputs, outputs)
    model.compile(optimizer='adam', loss='mse')
    return model

def main(input_csv, out_dir):
    df = pd.read_csv(input_csv)
    X = df.select_dtypes(include=['number']).fillna(0).values
    model = build_autoencoder(X.shape[1])
    model.fit(X, X, epochs=20, batch_size=64, validation_split=0.1)
    os.makedirs(out_dir, exist_ok=True)
    model.save(os.path.join(out_dir, 'autoencoder'))
    print('Saved autoencoder to', out_dir)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    main(args.input, args.out)
