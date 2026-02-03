"""
T-Helper Layer: ML-based Anomaly Detection
===========================================

Implements unsupervised ML models for anomaly detection:
- Isolation Forest
- Autoencoder
"""

import logging
import numpy as np
import pickle
from typing import List, Tuple, Optional
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow import keras

logger = logging.getLogger(__name__)


class IsolationForestDetector:
    """
    Isolation Forest-based anomaly detector.
    Effective for detecting outliers in high-dimensional data.
    """

    def __init__(self, contamination: float = 0.1, n_estimators: int = 100):
        """
        Initialize Isolation Forest detector.

        Args:
            contamination: Expected proportion of outliers
            n_estimators: Number of trees in the forest
        """
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        logger.info("Isolation Forest detector initialized")

    def train(self, features: np.ndarray):
        """
        Train the Isolation Forest model.

        Args:
            features: Training data (n_samples, n_features)
        """
        features_scaled = self.scaler.fit_transform(features)
        self.model.fit(features_scaled)
        self.is_fitted = True
        logger.info(f"Isolation Forest trained on {len(features)} samples")

    def predict(self, features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies.

        Args:
            features: Data to predict (n_samples, n_features)

        Returns:
            Tuple of (predictions, scores)
            predictions: -1 for anomaly, 1 for normal
            scores: Anomaly scores (lower is more anomalous)
        """
        if not self.is_fitted:
            raise ValueError("Model not trained yet")

        features_scaled = self.scaler.transform(features)
        predictions = self.model.predict(features_scaled)
        scores = self.model.decision_function(features_scaled)
        
        n_anomalies = np.sum(predictions == -1)
        logger.debug(f"Detected {n_anomalies} anomalies out of {len(features)} samples")
        
        return predictions, scores

    def save(self, path: str):
        """Save model to disk"""
        with open(path, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_fitted = True
        logger.info(f"Model loaded from {path}")


class AutoencoderDetector:
    """
    Autoencoder-based anomaly detector.
    Detects anomalies based on reconstruction error.
    """

    def __init__(self, input_dim: int, encoding_dim: int = 8, threshold_percentile: float = 95):
        """
        Initialize Autoencoder detector.

        Args:
            input_dim: Input feature dimension
            encoding_dim: Encoding dimension (bottleneck)
            threshold_percentile: Percentile for anomaly threshold
        """
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.threshold_percentile = threshold_percentile
        self.scaler = StandardScaler()
        self.threshold = None
        self.model = self._build_model()
        logger.info(f"Autoencoder detector initialized (input_dim={input_dim}, encoding_dim={encoding_dim})")

    def _build_model(self) -> keras.Model:
        """Build autoencoder architecture"""
        # Encoder
        input_layer = keras.layers.Input(shape=(self.input_dim,))
        encoded = keras.layers.Dense(self.encoding_dim * 2, activation='relu')(input_layer)
        encoded = keras.layers.Dense(self.encoding_dim, activation='relu')(encoded)
        
        # Decoder
        decoded = keras.layers.Dense(self.encoding_dim * 2, activation='relu')(encoded)
        decoded = keras.layers.Dense(self.input_dim, activation='sigmoid')(decoded)
        
        # Autoencoder
        autoencoder = keras.Model(input_layer, decoded)
        autoencoder.compile(optimizer='adam', loss='mse')
        
        return autoencoder

    def train(self, features: np.ndarray, epochs: int = 50, batch_size: int = 32, validation_split: float = 0.1):
        """
        Train the autoencoder model.

        Args:
            features: Training data (n_samples, n_features)
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Validation data split ratio
        """
        features_scaled = self.scaler.fit_transform(features)
        
        history = self.model.fit(
            features_scaled, features_scaled,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=0
        )
        
        # Calculate reconstruction error threshold
        reconstructions = self.model.predict(features_scaled)
        mse = np.mean(np.power(features_scaled - reconstructions, 2), axis=1)
        self.threshold = np.percentile(mse, self.threshold_percentile)
        
        logger.info(f"Autoencoder trained for {epochs} epochs, threshold={self.threshold:.4f}")

    def predict(self, features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies based on reconstruction error.

        Args:
            features: Data to predict (n_samples, n_features)

        Returns:
            Tuple of (predictions, scores)
            predictions: -1 for anomaly, 1 for normal
            scores: Reconstruction errors
        """
        if self.threshold is None:
            raise ValueError("Model not trained yet")

        features_scaled = self.scaler.transform(features)
        reconstructions = self.model.predict(features_scaled)
        mse = np.mean(np.power(features_scaled - reconstructions, 2), axis=1)
        
        predictions = np.where(mse > self.threshold, -1, 1)
        n_anomalies = np.sum(predictions == -1)
        logger.debug(f"Detected {n_anomalies} anomalies out of {len(features)} samples")
        
        return predictions, mse

    def save(self, model_path: str, config_path: str):
        """Save model to disk"""
        self.model.save(model_path)
        with open(config_path, 'wb') as f:
            pickle.dump({
                'scaler': self.scaler,
                'threshold': self.threshold,
                'input_dim': self.input_dim,
                'encoding_dim': self.encoding_dim
            }, f)
        logger.info(f"Model saved to {model_path}")

    def load(self, model_path: str, config_path: str):
        """Load model from disk"""
        self.model = keras.models.load_model(model_path)
        with open(config_path, 'rb') as f:
            config = pickle.load(f)
            self.scaler = config['scaler']
            self.threshold = config['threshold']
            self.input_dim = config['input_dim']
            self.encoding_dim = config['encoding_dim']
        logger.info(f"Model loaded from {model_path}")


class THelperLayer:
    """
    T-Helper layer that coordinates multiple anomaly detectors.
    Acts as the decision-making component of the immune system.
    """

    def __init__(self, use_isolation_forest: bool = True, use_autoencoder: bool = True,
                 input_dim: int = 4):
        """
        Initialize T-Helper layer.

        Args:
            use_isolation_forest: Enable Isolation Forest detector
            use_autoencoder: Enable Autoencoder detector
            input_dim: Input feature dimension
        """
        self.detectors = {}
        
        if use_isolation_forest:
            self.detectors['isolation_forest'] = IsolationForestDetector()
            
        if use_autoencoder:
            self.detectors['autoencoder'] = AutoencoderDetector(input_dim=input_dim)
            
        logger.info(f"T-Helper layer initialized with {len(self.detectors)} detectors")

    def train(self, features: np.ndarray):
        """
        Train all detectors.

        Args:
            features: Training data (n_samples, n_features)
        """
        for name, detector in self.detectors.items():
            logger.info(f"Training {name}...")
            detector.train(features)

    def detect_anomalies(self, features: np.ndarray, consensus: bool = True) -> np.ndarray:
        """
        Detect anomalies using ensemble of detectors.

        Args:
            features: Data to analyze (n_samples, n_features)
            consensus: If True, require consensus from multiple detectors

        Returns:
            Boolean array indicating anomalies
        """
        predictions = []
        
        for name, detector in self.detectors.items():
            pred, _ = detector.predict(features)
            predictions.append(pred)
            
        predictions = np.array(predictions)
        
        if consensus and len(predictions) > 1:
            # Majority vote
            anomalies = np.sum(predictions == -1, axis=0) > len(predictions) / 2
        else:
            # Any detector flags as anomaly
            anomalies = np.any(predictions == -1, axis=0)
            
        return anomalies

    def save_models(self, base_path: str):
        """Save all models"""
        Path(base_path).mkdir(parents=True, exist_ok=True)
        
        if 'isolation_forest' in self.detectors:
            self.detectors['isolation_forest'].save(f"{base_path}/isolation_forest.pkl")
            
        if 'autoencoder' in self.detectors:
            self.detectors['autoencoder'].save(
                f"{base_path}/autoencoder.h5",
                f"{base_path}/autoencoder_config.pkl"
            )

    def load_models(self, base_path: str):
        """Load all models"""
        if 'isolation_forest' in self.detectors:
            self.detectors['isolation_forest'].load(f"{base_path}/isolation_forest.pkl")
            
        if 'autoencoder' in self.detectors:
            self.detectors['autoencoder'].load(
                f"{base_path}/autoencoder.h5",
                f"{base_path}/autoencoder_config.pkl"
            )
