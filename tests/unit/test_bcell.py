"""
Unit tests for B-Cell memory layer
"""

import pytest
import time
from dis_k8s.bcell import BCellMemoryLayer, MemoryCell


class TestMemoryCell:
    """Test MemoryCell data class"""
    
    def test_memory_cell_creation(self):
        """Test creating a memory cell"""
        cell = MemoryCell(
            threat_signature='test-threat-123',
            pod_name='test-pod',
            namespace='default',
            timestamp=time.time(),
            response_action='isolate',
            success=True
        )
        
        assert cell.threat_signature == 'test-threat-123'
        assert cell.pod_name == 'test-pod'
        assert cell.response_action == 'isolate'
        assert cell.success == True
    
    def test_memory_cell_to_dict(self):
        """Test converting memory cell to dictionary"""
        cell = MemoryCell(
            threat_signature='test-threat',
            pod_name='test-pod',
            namespace='default',
            timestamp=time.time(),
            response_action='restart',
            success=False
        )
        
        data = cell.to_dict()
        assert isinstance(data, dict)
        assert data['threat_signature'] == 'test-threat'
        assert data['response_action'] == 'restart'


class TestBCellMemoryLayer:
    """Test B-Cell memory layer"""
    
    def test_initialization(self):
        """Test B-Cell initialization"""
        bcell = BCellMemoryLayer(memory_retention_hours=24)
        
        assert bcell.memory_retention_hours == 24
        assert len(bcell.memory_cells) == 0
        assert len(bcell.quarantined_pods) == 0
    
    def test_add_memory(self):
        """Test adding memory"""
        bcell = BCellMemoryLayer()
        
        bcell.add_memory(
            threat_signature='threat-1',
            pod_name='pod-1',
            namespace='default',
            response_action='isolate',
            success=True
        )
        
        assert len(bcell.memory_cells) == 1
        assert bcell.memory_cells[0].threat_signature == 'threat-1'
    
    def test_recall_memory(self):
        """Test recalling memory"""
        bcell = BCellMemoryLayer()
        
        # Add some memories
        bcell.add_memory('threat-1', 'pod-1', 'default', 'isolate', True)
        bcell.add_memory('threat-1', 'pod-2', 'default', 'restart', True)
        bcell.add_memory('threat-2', 'pod-3', 'default', 'none', False)
        
        # Recall specific threat
        memories = bcell.recall_memory('threat-1')
        assert len(memories) == 2
        
        memories = bcell.recall_memory('threat-2')
        assert len(memories) == 1
    
    def test_determine_action(self):
        """Test action determination"""
        bcell = BCellMemoryLayer()
        
        assert bcell._determine_action('high') == 'isolate'
        assert bcell._determine_action('medium') == 'restart'
        assert bcell._determine_action('low') == 'none'
    
    def test_get_memory_stats(self):
        """Test getting memory statistics"""
        bcell = BCellMemoryLayer()
        
        # Add some memories
        bcell.add_memory('threat-1', 'pod-1', 'default', 'isolate', True)
        bcell.add_memory('threat-2', 'pod-2', 'default', 'restart', False)
        
        stats = bcell.get_memory_stats()
        
        assert stats['total_memories'] == 2
        assert stats['successful_responses'] == 1
        assert stats['failed_responses'] == 1
    
    def test_get_quarantined_pods(self):
        """Test getting quarantined pods list"""
        bcell = BCellMemoryLayer()
        
        # Manually add to quarantine (in real scenario, isolate_pod does this)
        bcell.quarantined_pods.add('default/pod-1')
        bcell.quarantined_pods.add('default/pod-2')
        
        quarantined = bcell.get_quarantined_pods()
        assert len(quarantined) == 2
        assert 'default/pod-1' in quarantined


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
