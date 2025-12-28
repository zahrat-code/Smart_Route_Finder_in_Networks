import networkx as nx
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

@dataclass
class Node:
    """Ağdaki bir düğümü temsil eder."""
    id: int
    processing_delay: float  # ms (işleme gecikmesi)
    reliability: float       # olasılık [0, 1] (güvenilirlik)

    def to_dict(self):
        return {
            'id': self.id,
            'processing_delay': self.processing_delay,
            'reliability': self.reliability
        }

@dataclass
class Link:
    """İki düğüm arasındaki bağlantıyı (kenar) temsil eder."""
    source: int
    target: int
    bandwidth: float         # Mbps (bant genişliği)
    delay: float             # ms (gecikme)
    reliability: float       # olasılık [0, 1] (güvenilirlik)

    def to_dict(self):
        return {
            'source': self.source,
            'target': self.target,
            'bandwidth': self.bandwidth,
            'delay': self.delay,
            'reliability': self.reliability
        }

class NetworkTopology:
    """
    QoS özelliklerini yönetmek için networkx.Graph etrafında bir sarmalayıcı.
    """
    def __init__(self):
        self.graph = nx.Graph()

    def add_node(self, node: Node):
        self.graph.add_node(node.id, data=node)

    def add_link(self, link: Link):
        self.graph.add_edge(link.source, link.target, data=link)

    def get_nodes(self) -> List[Node]:
        return [self.graph.nodes[n]['data'] for n in self.graph.nodes]

    def get_links(self) -> List[Link]:
        return [self.graph.edges[u, v]['data'] for u, v in self.graph.edges]
    
    def get_link(self, u: int, v: int) -> Link:
        if self.graph.has_edge(u, v):
            return self.graph.edges[u, v]['data']
        return None

    def get_node(self, u: int) -> Node:
        if self.graph.has_node(u):
            return self.graph.nodes[u]['data']
        return None

    def clear(self):
        self.graph.clear()

    @staticmethod
    def from_nx_graph(G: nx.Graph) -> 'NetworkTopology':
        """
        Dışarıdan (generate_graf.py) gelen ham NetworkX grafını
        NetworkTopology yapısına dönüştürür.
        """
        topology = NetworkTopology()
        
        # Nodes
        for node_id, data in G.nodes(data=True):
            # generate_graf.py'den gelen veriler: 'processing_delay_ms', 'node_reliability'
            # Node sınıfı beklentisi: id, processing_delay, reliability
            node = Node(
                id=node_id,
                processing_delay=data.get('processing_delay_ms', 0.0),
                reliability=data.get('node_reliability', 1.0)
            )
            topology.add_node(node)
            
        # Links
        for u, v, data in G.edges(data=True):
            # generate_graf.py: 'bandwidth_mbps', 'link_delay_ms', 'link_reliability'
            # Link sınıfı: source, target, bandwidth, delay, reliability
            link = Link(
                source=u,
                target=v,
                bandwidth=data.get('bandwidth_mbps', 100.0),
                delay=data.get('link_delay_ms', 5.0),
                reliability=data.get('link_reliability', 1.0)
            )
            topology.add_link(link)
            
        return topology

