from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox, QApplication, QDialog, QTextEdit, QVBoxLayout, QTableWidgetItem
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import Optional, List, Tuple
import random
import statistics

from ..core.model import NetworkTopology

from ..generation import generate_graf
from ..algorithms.ACO_Algorithm import AntColonyOptimizer
from ..algorithms.GeneticAlgorithm import genetic_algorithm
from ..algorithms.QLearning import QLearningAgent
from ..algorithms import path_utilities

from ..experiment import runner as experiment_runner
from .results_dialog import ResultsDialog

from .graph_view import GraphView
from .controls import ControlPanel

class RoutingResult:
    """Helper struct to match the expected result interface for show_results"""
    def __init__(self, path_nodes, total_delay, total_reliability, resource_cost, total_cost, execution_time=0.0):
        self.path_nodes = path_nodes
        self.total_delay = total_delay
        self.total_reliability = total_reliability
        self.resource_cost = resource_cost
        self.total_cost = total_cost
        self.execution_time = execution_time


class ComparisonWorker(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, G, cases, algorithms, weights, repetitions):
        super().__init__()
        self.G = G
        self.cases = cases
        self.algorithms = algorithms
        self.weights = weights
        self.repetitions = repetitions
        
    def run(self):
        try:
            import time
            from ..core import Metrics as mt
            
            # metrics = {algo: {'costs': [], 'times': []}}
            data = {algo: {'costs': [], 'times': []} for algo in self.algorithms}
            
            # Weights
            w_d = self.weights[0]
            w_r = self.weights[1]
            w_b = self.weights[2]
            
            for rep in range(self.repetitions):
                for (src, dst, demand) in self.cases:
                    for algo_name in self.algorithms:
                        
                        start_time = time.time()
                        path = None
                        
                        try:
                            if algo_name == "ACO Algoritma":
                                weights_dict = {'delay': w_d, 'reliability': w_r, 'bandwidth': w_b}
                                # Create new instance for fairness
                                aco = AntColonyOptimizer(self.G, src, dst, demand, weights_dict, num_ants=10, max_iter=5)
                                path, _, _ = aco.run()
                                
                            elif algo_name == "Genetik Algoritma":
                                path = genetic_algorithm(self.G, src, dst, demand_mbps=demand, 
                                                         w_delay=w_d, w_rel=w_r, w_band=w_b)
                                
                            elif algo_name == "Q-Learning Algoritma":
                                params = {'alpha': 0.1, 'gamma': 0.9, 'epsilon': 0.1, 'episodes': 2000}
                                agent = QLearningAgent(src, dst, self.G, alpha=params['alpha'], gamma=params['gamma'], epsilon=params['epsilon'], episodes=params['episodes'])
                                agent.train()
                                path = agent.get_best_path()
                        except Exception:
                            path = None # Fail safely
                            
                        duration = time.time() - start_time
                        
                        # Calculate Cost
                        if path:
                            d = mt.Total_Delay(self.G, path)
                            r = mt.Total_Reliability(self.G, path)
                            b = mt.Total_Bandwidth(self.G, path)
                            
                            # Penalty if bandwidth not met
                            penalty = 500 if b < demand else 0
                            
                            cost = (w_d * d) + (w_r * r) + (w_b * (1000/(b+0.1))) + penalty
                            
                            data[algo_name]['costs'].append(cost)
                            data[algo_name]['times'].append(duration)
                        else:
                            pass 

            self.finished_signal.emit(data)
            
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Akilli-Rota-Bulucu")
        self.resize(1200, 800)
        
        # Central Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Components
        self.controls = ControlPanel()
        self.graph_view = GraphView()
        
        # Layout: Graph takes 70%, Controls takes 30%
        layout.addWidget(self.controls, 1)
        layout.addWidget(self.graph_view, 3)
        
        # State
        self.G = None # NetworkX Graph Container
        self.topology: Optional[NetworkTopology] = None
        self.source_id: Optional[int] = None
        self.target_id: Optional[int] = None
        self.worker = None # For Threading
        
        # Connect Signals
        self.controls.generate_signal.connect(self.generate_network)
        self.controls.calculate_signal.connect(self.calculate_path)
        self.graph_view.node_selected.connect(self.on_node_selected)
        
        # Connect Manual Selection Signals
        self.controls.source_changed_signal.connect(self.on_manual_source_changed)
        self.controls.target_changed_signal.connect(self.on_manual_target_changed)
        
        # Connect Experiment Signals
        self.controls.request_random_cases_signal.connect(self.generate_random_cases)
        self.controls.run_custom_experiment_signal.connect(self.run_custom_experiment)
        
        # Initial Generation
        self.generate_network()

    def generate_network(self):
        try:
            # Use the new generation logic from graf_uret
            G = generate_graf.graf_uret()
            # Store Raw Graph
            self.G = G
            
            # Convert to our UI model
            self.topology = NetworkTopology.from_nx_graph(G)
            
            self.graph_view.set_topology(self.topology)
            
            # Update Stats
            self.controls.set_stats(len(self.topology.get_nodes()), len(self.topology.get_links()))
            
            # Reset Selection
            self.source_id = None
            self.target_id = None
            self.update_selection_ui()
            self.controls.show_results(None)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ağ oluşturulamadı: {str(e)}")

    def on_node_selected(self, node_id: int):
        if self.source_id is None:
            self.source_id = node_id
        elif self.target_id is None:
            # Prevent same node selection
            if node_id != self.source_id:
                self.target_id = node_id
            else:
                return # Ignore click on same node
        else:
            # Reset and start over
            self.source_id = node_id
            self.target_id = None
            
        self.update_selection_ui()

    def on_manual_source_changed(self, val: int):
        if val == -1:
            self.source_id = None
        else:
            self.source_id = val
        self.update_selection_ui()

    def on_manual_target_changed(self, val: int):
        if val == -1:
            self.target_id = None
        else:
            self.target_id = val
        self.update_selection_ui()

    def update_selection_ui(self):
        self.graph_view.set_source(self.source_id)
        self.graph_view.set_target(self.target_id)
        # Use new method that handles spinboxes
        self.controls.set_selection_values(self.source_id, self.target_id)
        self.controls.show_results(None) # Clear results on new selection

    def calculate_path(self):
        if not self.topology or not self.G:
            QMessageBox.warning(self, "Uyarı", "Ağ oluşturulmadı.")
            return
        if self.source_id is None or self.target_id is None:
            QMessageBox.warning(self, "Uyarı", "Lütfen Kaynak ve Hedef düğümleri seçin.")
            return

        algo_name = self.controls.get_selected_algorithm()
        
        # Validation for Explicit Selection
        if algo_name == "Algoritma Seçiniz...":
            QMessageBox.warning(self, "Uyarı", "Lütfen bir algoritma seçiniz.")
            return

        weights_tuple = self.controls.get_weights() 
        # Validate Weights
        # New Validation: Sum must be exactly 1.0 (with small epsilon for float)
        total_weight = sum(weights_tuple)
        if abs(total_weight - 1.0) > 1e-5:
            QMessageBox.warning(self, "Uyarı", f"Ağırlıkların toplamı 1 olmalıdır. (Şu anki toplam: {total_weight:.2f})")
            return

        weights_dict = {
            'delay': weights_tuple[0], 
            'reliability': weights_tuple[1], 
            'bandwidth': weights_tuple[2]
        }
        
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            import time
            start_time = time.time()
            final_path = None
            
            # Use stored graph
            G_algo = self.G
            
            if algo_name == "ACO Algoritma":
                aco = AntColonyOptimizer(
                    G_algo, 
                    self.source_id, 
                    self.target_id, 
                    demand=0.1, 
                    weights=weights_dict,
                    num_ants=10, 
                    max_iter=5 
                )
                best_path, cost, metrics = aco.run()
                final_path = best_path
                
            elif algo_name == "Genetik Algoritma":
                best_path = genetic_algorithm(
                    G_algo,
                    self.source_id, 
                    self.target_id,
                    demand_mbps=0.1,
                    w_delay=weights_dict['delay'],
                    w_rel=weights_dict['reliability'],
                    w_band=weights_dict['bandwidth']
                )
                final_path = best_path
 
            elif algo_name == "Q-Learning Algoritma":
                agent = QLearningAgent(self.source_id, self.target_id, G=G_algo)
                agent.train() 
                final_path = agent.get_best_path()


            else:
                 QMessageBox.information(self, "Bilgi", f"{algo_name} henüz bağlanmadı.")
                 QApplication.restoreOverrideCursor()
                 return

            end_time = time.time()
            duration = end_time - start_time
            
            if final_path:
                # Calculate metrics for display
                final_path = [int(n) for n in final_path]
                
                # Re-calculate metrics using raw graph to match algorithm logic
                from ..core import Metrics as mt
                d = mt.Total_Delay(G_algo, final_path)
                r = mt.Total_Reliability(G_algo, final_path)
                b = mt.Total_Bandwidth(G_algo, final_path)
                
                # Total cost based on weights
                total_cost = (weights_dict['delay'] * d) + \
                             (weights_dict['reliability'] * r) + \
                             (weights_dict['bandwidth'] * b)
                             
                result_obj = RoutingResult(
                    path_nodes=final_path,
                    total_delay=d,
                    total_reliability=r,
                    resource_cost=b,
                    total_cost=total_cost,
                    execution_time=duration
                )
                
                self.graph_view.highlight_path(final_path)
                self.controls.show_results(result_obj)
            else:
                self.controls.show_results(None)
                QMessageBox.information(self, "Sonuç", "Yol bulunamadı.")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Hata", f"Algoritma hatası: {str(e)}")
        finally:
            QApplication.restoreOverrideCursor()

    # --- Experiment Logic ---

    def generate_random_cases(self):
        if not self.topology:
             QMessageBox.warning(self, "Uyarı", "Önce topoloji oluşturun.")
             return
             
        nodes = [n.id for n in self.topology.get_nodes()]
        cases = []
        count = 0
        while count < 20:
            s = random.choice(nodes)
            d = random.choice(nodes)
            if s != d:
                # Reduced demand range to increase probability of finding valid paths
                b = random.uniform(10.0, 80.0)
                cases.append((s, d, b))
                count += 1
                
        self.controls.add_cases_batch(cases)

    def run_custom_experiment(self):
        if not self.topology or not self.G:
             QMessageBox.warning(self, "Uyarı", "Önce topoloji oluşturun.")
             return
        
        config = self.controls.get_experiment_config()
        cases = config['cases']
        algo_names = config['algorithms']
        reps = config['repetitions']
        
        if not cases:
            QMessageBox.warning(self, "Uyarı", "Lütfen deney durumları ekleyin.")
            return
        if not algo_names:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir algoritma seçin.")
            return

        weights = self.controls.get_weights() 
        
        # Validate Weights for Experiment
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > 1e-5:
            QMessageBox.warning(self, "Uyarı", f"Ağırlıkların toplamı 1 olmalıdır. (Şu anki toplam: {total_weight:.2f})")
            return
        
        # Start Worker
        # Use CORRECT G
        self.worker = ComparisonWorker(self.G, cases, algo_names, weights, reps)
        self.worker.finished_signal.connect(self.on_experiment_finished)
        self.worker.error_signal.connect(self.on_experiment_error)
        
        self.statusBar().showMessage("Karşılaştırma yapılıyor, lütfen bekleyin...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.controls.setEnabled(False) 
        
        self.worker.start()

    def on_experiment_finished(self, results):
        self.statusBar().showMessage("Deney Tamamlandı")
        QApplication.restoreOverrideCursor()
        self.controls.setEnabled(True)
        
        # Show Results Dialog
        dlg = ResultsDialog(results, self)
        dlg.exec()

        # Show Results Dialog
        dlg = ResultsDialog(results, self)
        dlg.exec()

    def on_experiment_error(self, err):
        self.statusBar().showMessage("Hata")
        QApplication.restoreOverrideCursor()
        self.controls.setEnabled(True)
        QMessageBox.critical(self, "Deney Hatası", str(err))
