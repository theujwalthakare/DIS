"""
Unit tests for T-Helper layer
"""

import pytest
import numpy as np
from dis_k8s.thelper import THelperLayer, IsolationForestDetector, AutoencoderDetector


class TestIsolationForestDetector:
    """Test Isolation Forest detector"""
    
    def test_initialization(self):
        """Test detector initialization"""
        detector = IsolationForestDetector(contamination=0.1, n_estimators=50)
        
        assert detector.is_fitted == False
        assert detector.model.contamination == 0.1
        assert detector.model.n_estimators == 50
    
    def test_train_and_predict(self):
        """Test training and prediction"""
        detector = IsolationForestDetector(contamination=0.1)
        
        # Generate training data
        np.random.seed(42)
        normal_data = np.random.randn(100, 4) * 10 + 50
        detector.train(normal_data)
        
        assert detector.is_fitted == True
        
        # Test on normal data
        predictions, scores = detector.predict(normal_data[:10])
        assert len(predictions) == 10
        assert len(scores) == 10
        
        # Test on anomalous data
        anomaly_data = np.array([[200, 200, 200, 200]])
        predictions, scores = detector.predict(anomaly_data)
        assert predictions[0] == -1  # Should detect as anomaly


class TestAutoencoderDetector:
    """Test Autoencoder detector"""
    
    def test_initialization(self):
        """Test detector initialization"""
        detector = AutoencoderDetector(input_dim=4, encoding_dim=8)
        
        assert detector.input_dim == 4
        assert detector.encoding_dim == 8
        assert detector.threshold is None
    
    def test_train_and_predict(self):
        """Test training and prediction"""
        detector = AutoencoderDetector(input_dim=4, encoding_dim=2)
        
        # Generate training data
        np.random.seed(42)
        normal_data = np.random.randn(100, 4) * 10 + 50
        detector.train(normal_data, epochs=5, batch_size=32)
        
        assert detector.threshold is not None
        
        # Test on normal data
        predictions, scores = detector.predict(normal_data[:10])
        assert len(predictions) == 10
        assert len(scores) == 10


class TestTHelperLayer:
    """Test T-Helper layer"""
    
    def test_initialization(self):
        """Test T-Helper initialization"""
        thelper = THelperLayer(
            use_isolation_forest=True,
            use_autoencoder=True,
            input_dim=4
        )
        
        assert 'isolation_forest' in thelper.detectors
        assert 'autoencoder' in thelper.detectors
        assert len(thelper.detectors) == 2
    
    def test_train(self):
        """Test training all detectors"""
        thelper = THelperLayer(input_dim=4)
        
        # Generate training data
        np.random.seed(42)
        normal_data = np.random.randn(100, 4) * 10 + 50
        thelper.train(normal_data)
        
        # Check that models are trained
        assert thelper.detectors['isolation_forest'].is_fitted == True
        assert thelper.detectors['autoencoder'].threshold is not None
    
    def test_detect_anomalies(self):
        """Test anomaly detection"""
        thelper = THelperLayer(input_dim=4)
        
        # Generate and train on normal data
        np.random.seed(42)
        normal_data = np.random.randn(100, 4) * 10 + 50
        thelper.train(normal_data)
        
        # Test on normal data
        test_normal = normal_data[:5]
        anomalies = thelper.detect_anomalies(test_normal, consensus=True)
        
        assert len(anomalies) == 5
        assert isinstance(anomalies, np.ndarray)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
