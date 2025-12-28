import random
import time
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any
from ..core.model import NetworkTopology
# from ..generation.generator import NetworkGenerator
from ..generation import generate_graf
# from ..algorithms.base import RoutingAlgorithm, PathResult
# from ..algorithms.dummy import DummyAlgorithm
# from ..algorithms.dijkstra import DijkstraAlgorithm

@dataclass
class ExperimentCase:
    case_id: int
    source: int
    target: int
    bandwidth: float

@dataclass
class AlgorithmStats:
    algorithm_name: str
    success_rate: float
    avg_cost: float
    avg_time: float
    std_dev_time: float
    min_time: float
    max_time: float
    avg_path_len: float
    status: str # "OK", "FAIL", "PARTIAL"

@dataclass
class ExperimentResult:
    case: ExperimentCase
    results: List[AlgorithmStats]

def run_custom_experiment(
    topology: NetworkTopology,
    cases: List[Tuple[int, int, float]],
    algorithms: List[Any], # Changed from RoutingAlgorithm
    weights: Tuple[float, float, float],
    repetitions: int = 5
) -> List[ExperimentResult]:
    
    experiment_results = []
    w_delay, w_rel, w_res = weights
    
    # Optimize: Generate raw graph once for the entire experiment
    # This prevents regenerating it 100+ times inside loops
    # Assuming topology doesn't change during experiment
    G = experiment_graph_instance(topology) 
    
    for i, (s, d, b) in enumerate(cases):
        case_obj = ExperimentCase(i+1, s, d, b)
        algo_stats_list = []
        
        for algo in algorithms:
            times = []
            costs = []
            path_lens = []
            success_count = 0
            
            # Initialize Algorithm Object if needed based on 'algo' type (string vs object)
            # In MainWindow we passed STRINGS for new algos.
            # We need to instantiate here or handle it.
            
            # Logic adapted for new setup
            algo_instance = None
            algo_name = str(algo)
            
            # Since strict OOP interface is broken, we handle manually
            
            for _ in range(repetitions):
                res = None
                start_t = time.time()
                try:
                    # Using cached G from outside loop 
                    
                    if algo == "ACO Algoritma":
                        from ..algorithms.ACO_Algorithm import AntColonyOptimizer
                        # Weights dictionary
                        w_dict = {'delay': w_delay, 'reliability': w_rel, 'bandwidth': w_res}
                        # Optimized for speed/reliability balance
                        optimizer = AntColonyOptimizer(G, s, d, 0.1, w_dict, num_ants=10, max_iter=5)
                        best_path, cost, _ = optimizer.run()


                        if best_path:
                            # Mock existing result structure
                            # We can create a simple object
                            res = SimpleResult(best_path, cost, time.time() - start_t)
                            
                    elif algo == "Genetik Algoritma":
                        from ..algorithms.GeneticAlgorithm import genetic_algorithm
                        # Fix: Pass weights as keyword arguments, otherwise they override pop_size/generations
                        # Reduced pop/gen for UI responsiveness
                        best_path = genetic_algorithm(
                            G, s, d, 
                            demand_mbps=0.1, 
                            pop_size=20,
                            generations=20,
                            w_delay=w_delay, 
                            w_rel=w_rel, 
                            w_band=w_res
                        )
                        if best_path:
                            # GA returns only path. recalculate cost?

                            # For speed, assume cost=0 or calculate later.
                            # calculate cost
                            from ..core import Metrics as mt
                            d_val = mt.Total_Delay(G, best_path)
                            r_val = mt.Total_Reliability(G, best_path)
                            b_val = mt.Total_Bandwidth(G, best_path)
                            total = (w_delay * d_val) + (w_rel * r_val) + (w_res * b_val)
                            res = SimpleResult(best_path, total, time.time() - start_t)

                    elif algo == "Q-Learning Algoritma":
                        from ..algorithms.QLearning import QLearningAgent
                        # Use s and d from the loop
                        agent = QLearningAgent(s, d, G=G)
                        # QL takes time
                        agent.train()
                        path = agent.get_best_path()


                        if path:
                             res = SimpleResult(path, 0.0, time.time() - start_t)


                except Exception as e:
                    print(f"Error in experiment for {algo} case {i}: {e}")
                    import traceback
                    traceback.print_exc()

                
                if res:
                    times.append(res.execution_time)
                    costs.append(res.total_cost)
                    path_lens.append(len(res.path_nodes))
                    success_count += 1
            
            # Calculate Stats (Same as before)
            if success_count > 0:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                avg_cost = sum(costs) / len(costs)
                avg_len = sum(path_lens) / len(path_lens)
                
                if len(times) > 1:
                    std_dev = math.sqrt(sum((x - avg_time) ** 2 for x in times) / (len(times) - 1))
                else:
                    std_dev = 0.0
                status = "OK"
            else:
                avg_time = 0.0; min_time = 0.0; max_time = 0.0; avg_cost = 0.0; avg_len = 0.0; std_dev = 0.0
                status = "FAIL"
            
            stats = AlgorithmStats(
                algorithm_name=algo_name,
                success_rate=success_count / repetitions,
                avg_cost=avg_cost,
                avg_time=avg_time,
                std_dev_time=std_dev,
                min_time=min_time,
                max_time=max_time,
                avg_path_len=avg_len,
                status=status
            )
            algo_stats_list.append(stats)
            
        experiment_results.append(ExperimentResult(case=case_obj, results=algo_stats_list))
        
    return experiment_results

class SimpleResult:
    def __init__(self, path, cost, time):
        self.path_nodes = path
        self.total_cost = cost
        self.execution_time = time

def experiment_graph_instance(topology):
    """
    Returns a networkx graph. 
    If topology has .graph, use it. 
    Else generate new (less consistant but working).
    """
    if hasattr(topology, 'graph'):
        # We need to convert the topology graph (which has objects in 'data')
        # back to the raw dict format expected by the algorithms.
        import networkx as nx
        raw_G = nx.Graph()
        
        # Nodes
        for n in topology.get_nodes():
            raw_G.add_node(n.id, 
                           processing_delay_ms=n.processing_delay,
                           node_reliability=n.reliability,
                           id=n.id) # Some algos might use 'id' attribute
                           
        # Links
        for l in topology.get_links():
            raw_G.add_edge(l.source, l.target,
                           bandwidth_mbps=l.bandwidth,
                           link_delay_ms=l.delay,
                           link_reliability=l.reliability)
        return raw_G

    # Fallback
    return generate_graf.graf_uret()


# Keep the old function for backward compatibility if needed, or update it
def run_experiment() -> str:
    """Default demo experiment logic preserved but mapped to new structure."""
    # Placeholder implementation
    return "Legacy Experiment Wrapper is deprecated."




