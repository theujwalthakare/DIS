"""
Unit tests for aDC (Artificial Dendritic Cell) agent
"""

import pytest
import time
from dis_k8s.adc import ArtificialDendriticCell, Antigen


class TestAntigen:
    """Test Antigen data class"""
    
    def test_antigen_creation(self):
        """Test creating an antigen"""
        antigen = Antigen(
            timestamp=time.time(),
            node_name='test-node',
            metric_type='cpu',
            value=50.0,
            metadata={'cores': 4}
        )
        
        assert antigen.node_name == 'test-node'
        assert antigen.metric_type == 'cpu'
        assert antigen.value == 50.0
        assert antigen.metadata['cores'] == 4
    
    def test_antigen_to_dict(self):
        """Test converting antigen to dictionary"""
        antigen = Antigen(
            timestamp=time.time(),
            node_name='test-node',
            metric_type='memory',
            value=75.0
        )
        
        data = antigen.to_dict()
        assert isinstance(data, dict)
        assert data['node_name'] == 'test-node'
        assert data['metric_type'] == 'memory'


class TestArtificialDendriticCell:
    """Test aDC agent"""
    
    def test_initialization(self):
        """Test aDC initialization"""
        adc = ArtificialDendriticCell(node_name='test-node', collect_interval=5)
        
        assert adc.node_name == 'test-node'
        assert adc.collect_interval == 5
        assert len(adc.antigens) == 0
    
    def test_collect_cpu_metrics(self):
        """Test CPU metrics collection"""
        adc = ArtificialDendriticCell(node_name='test-node')
        antigen = adc.collect_cpu_metrics()
        
        assert antigen.metric_type == 'cpu'
        assert antigen.node_name == 'test-node'
        assert 0 <= antigen.value <= 100
        assert 'cores' in antigen.metadata
    
    def test_collect_memory_metrics(self):
        """Test memory metrics collection"""
        adc = ArtificialDendriticCell(node_name='test-node')
        antigen = adc.collect_memory_metrics()
        
        assert antigen.metric_type == 'memory'
        assert antigen.node_name == 'test-node'
        assert 0 <= antigen.value <= 100
        assert 'total' in antigen.metadata
        assert 'used' in antigen.metadata
    
    def test_collect_network_metrics(self):
        """Test network metrics collection"""
        adc = ArtificialDendriticCell(node_name='test-node')
        antigen = adc.collect_network_metrics()
        
        assert antigen.metric_type == 'network'
        assert antigen.node_name == 'test-node'
        assert antigen.value >= 0
        assert 'bytes_sent' in antigen.metadata
        assert 'bytes_recv' in antigen.metadata
    
    def test_collect_all_metrics(self):
        """Test collecting all metrics"""
        adc = ArtificialDendriticCell(node_name='test-node')
        antigens = adc.collect_all_metrics()
        
        assert len(antigens) == 3  # CPU, memory, network
        metric_types = [a.metric_type for a in antigens]
        assert 'cpu' in metric_types
        assert 'memory' in metric_types
        assert 'network' in metric_types
    
    def test_get_recent_antigens(self):
        """Test getting recent antigens"""
        adc = ArtificialDendriticCell(node_name='test-node')
        
        # Collect some antigens
        for _ in range(5):
            adc.collect_all_metrics()
        
        recent = adc.get_recent_antigens(count=20)
        # Should have collected multiple metrics (at least 10)
        assert len(recent) >= 10
    
    def test_clear_antigens(self):
        """Test clearing antigens"""
        adc = ArtificialDendriticCell(node_name='test-node')
        adc.collect_all_metrics()
        
        assert len(adc.antigens) > 0
        
        adc.clear_antigens()
        assert len(adc.antigens) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
