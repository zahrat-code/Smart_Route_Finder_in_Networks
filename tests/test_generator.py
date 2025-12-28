import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qos_project.src.generation.generator import NetworkGenerator
from qos_project.src.core.model import NetworkTopology

def test_generator_structure():
    """Verify 250 nodes and basic connectivity."""
    gen = NetworkGenerator(num_nodes=250, connection_prob=0.4)
    topology = gen.generate()
     
    # Check Node Count
    assert len(topology.get_nodes()) == 250
    
    # Check Connectivity
    # Fast check: number of edges should be roughly p * n * (n-1) / 2
    # 0.4 * 250 * 249 / 2 = 12450. Allow some variance.
    num_edges = len(topology.get_links())
    assert num_edges > 10000 
    
    # Check if networkx graph is connected
    import networkx as nx
    assert nx.is_connected(topology.graph)

def test_node_properties():
    """Verify Node property ranges."""
    gen = NetworkGenerator(num_nodes=10, connection_prob=0.5)
    topology = gen.generate()
    
    for node in topology.get_nodes():
        assert 0.5 <= node.processing_delay <= 2.0
        assert 0.95 <= node.reliability <= 0.999

def test_link_properties():
    """Verify Link property ranges."""
    gen = NetworkGenerator(num_nodes=10, connection_prob=0.5)
    topology = gen.generate()
    
    for link in topology.get_links():
        assert 100.0 <= link.bandwidth <= 1000.0
        assert 3.0 <= link.delay <= 15.0
        assert 0.95 <= link.reliability <= 0.999
