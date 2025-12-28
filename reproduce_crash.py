import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from src.algorithms.ACO_Algorithm import AntColonyOptimizer
    from src.generation import generate_graf as gg
    from src.core import Metrics as mt
except ImportError as e:
    print(f"Import Error: {e}")
    # try adjusting path if src is not a package
    sys.path.append(os.getcwd())
    try:
        from src.algorithms.ACO_Algorithm import AntColonyOptimizer
        from src.generation import generate_graf as gg
        from src.core import Metrics as mt
    except ImportError as e2:
        print(f"Import Error 2: {e2}")
        sys.exit(1)

def reproducing_crash():
    print("Generating Graph...")
    G = gg.graf_uret()
    
    # Force some edge cases
    # Case 2: Bandwidth 0
    for u, v in G.edges():
        G.edges[u, v]['bandwidth_mbps'] = 0 # Should crash Metrics.Total_Bandwidth
        G.edges[u, v]['link_delay_ms'] = 10
        G.edges[u, v]['link_reliability'] = 0.99
    
    for n in G.nodes():
        G.nodes[n]['processing_delay_ms'] = 1
        G.nodes[n]['node_reliability'] = 0.99

    # Define Source and Destination
    # Try to ensure a path exists
    S = list(G.nodes())[0]
    D = list(G.nodes())[-1]
    
    print(f"Running ACO for S={S}, D={D}...")
    
    # All weights non-zero but costs will be 0 ?
    # delay cost = 0+0 = 0
    # rel cost = -0 + -0 = 0
    # bw cost = 1000/1000 = 1. (Not 0)
    
    # If bandwidth weight is 0...
    weights = {'delay': 1.0, 'reliability': 1.0, 'bandwidth': 0.0}
    # Then total cost = 1*0 + 1*0 + 0*1 = 0
    
    try:
        # Pass demand=0 to bypass heuristic check
        optimizer = AntColonyOptimizer(G, S, D, 0.0, weights, num_ants=5, max_iter=5)
        best_path, cost, metrics = optimizer.run()
        print(f"Success. Cost: {cost}")
        print(f"Metrics: {metrics}")
    except ZeroDivisionError:
        print("Caught ZeroDivisionError!")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Other Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproducing_crash()
