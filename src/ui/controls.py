from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDoubleSpinBox, QPushButton, QGroupBox, QFormLayout, QSpinBox,
    QTabWidget, QListWidget, QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt

class SingleAnalysisPanel(QWidget):
    """
    Control Panel for Single Routing Analysis (Old Interface).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # 1. Network Generation
        gen_group = QGroupBox("Ağ (Network)")
        gen_layout = QVBoxLayout()
        self.lbl_stats = QLabel("Düğümler: - | Kenarlar: -")
        gen_layout.addWidget(self.lbl_stats)
        
        self.btn_generate = QPushButton("Yeni Topoloji Oluştur")
        gen_layout.addWidget(self.btn_generate)
        
        gen_group.setLayout(gen_layout)
        self.layout.addWidget(gen_group)
        
        # 2. Path Selection
        sel_group = QGroupBox("Düğüm Seçimi")
        sel_layout = QFormLayout()
        
        self.spin_source = QSpinBox()
        self.spin_source.setRange(-1, 9999)
        self.spin_source.setValue(-1)
        self.spin_source.setSpecialValueText("Kaynak Seçiniz") 
        
        self.spin_target = QSpinBox()
        self.spin_target.setRange(-1, 9999)
        self.spin_target.setValue(-1)
        self.spin_target.setSpecialValueText("Hedef Seçiniz") 

        
        sel_layout.addRow("Kaynak (S):", self.spin_source)
        sel_layout.addRow("Hedef (D):", self.spin_target)
        sel_group.setLayout(sel_layout)
        self.layout.addWidget(sel_group)
        
        # 3. Algorithms & Weights
        algo_group = QGroupBox("Optimizasyon")
        algo_layout = QVBoxLayout()
        
        self.combo_algo = QComboBox()
        self.combo_algo.addItems(["Algoritma Seçiniz...", "ACO Algoritma", "Genetik Algoritma", "Q-Learning Algoritma"])




        algo_layout.addWidget(QLabel("Algoritma:"))
        algo_layout.addWidget(self.combo_algo)
        
        # Weights
        weight_layout = QFormLayout()
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setRange(0, 1); self.spin_delay.setSingleStep(0.01); self.spin_delay.setValue(0.00)
        self.spin_reliability = QDoubleSpinBox()
        self.spin_reliability.setRange(0, 1); self.spin_reliability.setSingleStep(0.01); self.spin_reliability.setValue(0.00)
        self.spin_resource = QDoubleSpinBox()
        self.spin_resource.setRange(0, 1); self.spin_resource.setSingleStep(0.01); self.spin_resource.setValue(0.00)




        
        weight_layout.addRow("Gecikme Ağ.:", self.spin_delay)
        weight_layout.addRow("Güvenilirlik Ağ.:", self.spin_reliability)
        weight_layout.addRow("Kaynak Ağ.:", self.spin_resource)


        algo_layout.addLayout(weight_layout)
        
        self.btn_calculate = QPushButton("En İyi Yolu Hesapla")
        algo_layout.addWidget(self.btn_calculate)
        
        algo_group.setLayout(algo_layout)
        self.layout.addWidget(algo_group)
        
        # 4. Results
        res_group = QGroupBox("Metrikler")
        res_layout = QFormLayout()
        self.lbl_res_delay = QLabel("-")
        self.lbl_res_rel = QLabel("-")
        self.lbl_res_bw = QLabel("-")
        self.lbl_res_cost = QLabel("-")
        self.lbl_res_time = QLabel("-")
        self.lbl_res_path = QLabel("-")
        self.lbl_res_path.setWordWrap(True) # Allow long paths to wrap
        
        res_layout.addRow("Toplam Gecikme:", self.lbl_res_delay)
        res_layout.addRow("Toplam Güven.:", self.lbl_res_rel)
        res_layout.addRow("Kaynak Maliyeti:", self.lbl_res_bw)
        res_layout.addRow("Toplam Maliyet:", self.lbl_res_cost)
        res_layout.addRow("Çalışma Süresi:", self.lbl_res_time)
        res_layout.addRow("Bulunan Yol:", self.lbl_res_path) # Changed label distinctness
        res_group.setLayout(res_layout)
        self.layout.addWidget(res_group)
        
        self.layout.addStretch()

class ExperimentPanel(QWidget):
    """
    Control Panel for Experimental Setup (New Interface).
    """
    run_custom_experiment_signal = pyqtSignal()
    request_random_cases_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # 1. Experiment Cases Configuration
        case_group = QGroupBox("Deney (S, D, B)")
        case_layout = QVBoxLayout()
        
        # Add Input Area
        input_layout = QHBoxLayout()
        self.combo_source = QComboBox() 
        self.combo_target = QComboBox()
        self.spin_bw = QDoubleSpinBox()
        self.spin_bw.setRange(0.0, 10000.0)
        self.spin_bw.setValue(0.0)
        self.spin_bw.setSuffix(" Mbps")
        
        self.btn_add_case = QPushButton("Ekle")
        self.btn_add_case.clicked.connect(self.add_case)
        
        input_layout.addWidget(QLabel("K:"))
        input_layout.addWidget(self.combo_source)
        input_layout.addWidget(QLabel("H:"))
        input_layout.addWidget(self.combo_target)
        input_layout.addWidget(QLabel("B:"))
        input_layout.addWidget(self.spin_bw)
        input_layout.addWidget(self.btn_add_case)
        
        case_layout.addLayout(input_layout)
        
        # List/Table of Cases
        self.table_cases = QTableWidget()
        self.table_cases.setColumnCount(3)
        self.table_cases.setHorizontalHeaderLabels(["Kaynak", "Hedef", "Bant Genişliği"])
        self.table_cases.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        case_layout.addWidget(self.table_cases)
        
        # Presets
        btn_layout = QHBoxLayout()
        self.btn_load_preset = QPushButton("Rastgele Doldur")
        self.btn_load_preset.clicked.connect(self.request_random_cases_signal.emit)
        self.btn_clear_cases = QPushButton("Temizle")
        self.btn_clear_cases.clicked.connect(self.clear_cases)
        btn_layout.addWidget(self.btn_load_preset)
        btn_layout.addWidget(self.btn_clear_cases)
        case_layout.addLayout(btn_layout)
        
        case_group.setLayout(case_layout)
        layout.addWidget(case_group)
        
        # 2. Algorithm Selection
        algo_group = QGroupBox("Algoritma")
        algo_layout = QVBoxLayout()
        
        self.list_algos = QListWidget()
        self.list_algos.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Add items
        item_aco = QListWidgetItem("ACO Algoritma")
        item_aco.setCheckState(Qt.CheckState.Unchecked)

        self.list_algos.addItem(item_aco)
        
        item_ga = QListWidgetItem("Genetik Algoritma")
        item_ga.setCheckState(Qt.CheckState.Unchecked)
        self.list_algos.addItem(item_ga)
        
        item_ql = QListWidgetItem("Q-Learning Algoritma")
        item_ql.setCheckState(Qt.CheckState.Unchecked)
        self.list_algos.addItem(item_ql)




        algo_layout.addWidget(self.list_algos)
        
        algo_group.setLayout(algo_layout)
        layout.addWidget(algo_group)
        
        # 3. Settings
        set_group = QGroupBox("Ayarlar")
        set_layout = QFormLayout()
        
        self.spin_reps = QSpinBox()
        self.spin_reps.setRange(1, 100)
        self.spin_reps.setValue(1)
        set_layout.addRow("Tekrar Sayısı:", self.spin_reps)
        
        set_group.setLayout(set_layout)
        layout.addWidget(set_group)
        
        # 4. Run
        self.btn_run_exp = QPushButton("Deneyi Başlat")
        self.btn_run_exp.clicked.connect(self.run_custom_experiment_signal.emit)
        # Use same blue style as other primary buttons (or default/theme specific)
        self.btn_run_exp.setStyleSheet("font-weight: bold; background-color: #007bff; color: white; padding: 5px;")
        layout.addWidget(self.btn_run_exp)
        
        layout.addStretch()

    def add_case(self):
        s = self.combo_source.currentText()
        d = self.combo_target.currentText()
        if not s or not d: 
            return
        
        # Just add row
        row = self.table_cases.rowCount()
        self.table_cases.insertRow(row)
        self.table_cases.setItem(row, 0, QTableWidgetItem(s))
        self.table_cases.setItem(row, 1, QTableWidgetItem(d))
        self.table_cases.setItem(row, 2, QTableWidgetItem(str(self.spin_bw.value())))

    def clear_cases(self):
        self.table_cases.setRowCount(0)

    def update_node_lists(self, num_nodes):
        self.combo_source.clear()
        self.combo_target.clear()
        items = [str(i) for i in range(num_nodes)]
        self.combo_source.addItems(items)
        self.combo_target.addItems(items)


class ControlPanel(QWidget):
    """
    Main Control Panel Wrapper with Tabs.
    """
    generate_signal = pyqtSignal()
    calculate_signal = pyqtSignal()
    algorithm_changed_signal = pyqtSignal(str)
    source_changed_signal = pyqtSignal(int)
    target_changed_signal = pyqtSignal(int)
    run_experiment_signal = pyqtSignal() # Kept for compatibility if used, but we prefer new one
    
    # New Signal
    request_random_cases_signal = pyqtSignal()
    run_custom_experiment_signal = pyqtSignal() # Forwarded from ExperimentPanel

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.tabs = QTabWidget()
        
        self.pnl_single = SingleAnalysisPanel()
        self.pnl_experiment = ExperimentPanel()
        
        self.tabs.addTab(self.pnl_single, "Tekil Analiz")
        self.tabs.addTab(self.pnl_experiment, "Deneysel Analiz")
        
        self.layout.addWidget(self.tabs)
        
        # Connect Signals from Single Panel
        self.pnl_single.btn_generate.clicked.connect(self.generate_signal.emit)
        self.pnl_single.btn_calculate.clicked.connect(self.calculate_signal.emit)
        self.pnl_single.combo_algo.currentTextChanged.connect(self.algorithm_changed_signal.emit)
        self.pnl_single.spin_source.valueChanged.connect(self.source_changed_signal.emit)
        self.pnl_single.spin_target.valueChanged.connect(self.target_changed_signal.emit)
        
        # Connect Experiment Panel
        # New: Use direct signal proxy, no disconnect hacks
        self.pnl_experiment.request_random_cases_signal.connect(self.request_random_cases_signal.emit)
        self.pnl_experiment.run_custom_experiment_signal.connect(self.run_custom_experiment_signal.emit)

    # --- Delegated Methods (Single Analysis) ---

    def get_weights(self):
        return (self.pnl_single.spin_delay.value(), 
                self.pnl_single.spin_reliability.value(), 
                self.pnl_single.spin_resource.value())

    def get_selected_algorithm(self):
        return self.pnl_single.combo_algo.currentText()

    def set_selection_values(self, s, t):
        self.pnl_single.spin_source.blockSignals(True)
        self.pnl_single.spin_target.blockSignals(True)
        self.pnl_single.spin_source.setValue(s if s is not None else -1)
        self.pnl_single.spin_target.setValue(t if t is not None else -1)
        self.pnl_single.spin_source.blockSignals(False)
        self.pnl_single.spin_target.blockSignals(False)

    def show_results(self, result):
        if result:
            self.pnl_single.lbl_res_delay.setText(f"{result.total_delay:.2f} ms")
            self.pnl_single.lbl_res_rel.setText(f"{result.total_reliability:.4f}")
            self.pnl_single.lbl_res_bw.setText(f"{result.resource_cost:.2f}")
            self.pnl_single.lbl_res_cost.setText(f"{result.total_cost:.4f}")
            self.pnl_single.lbl_res_time.setText(f"{result.execution_time:.4f} s")
            
            # Format path
            if result.path_nodes:
                path_str = " -> ".join(map(str, result.path_nodes))
                self.pnl_single.lbl_res_path.setText(path_str)
            else:
                 self.pnl_single.lbl_res_path.setText("Yol Yok")
        else:
            self.pnl_single.lbl_res_delay.setText("-")
            self.pnl_single.lbl_res_rel.setText("-")
            self.pnl_single.lbl_res_bw.setText("-")
            self.pnl_single.lbl_res_cost.setText("-")
            self.pnl_single.lbl_res_time.setText("-")
            self.pnl_single.lbl_res_path.setText("-")

    def set_stats(self, num_nodes, num_edges):
        self.pnl_single.lbl_stats.setText(f"Düğümler: {num_nodes} | Kenarlar: {num_edges}")
        self.pnl_single.spin_source.setMaximum(num_nodes - 1)
        self.pnl_single.spin_target.setMaximum(num_nodes - 1)
        
        # Also update Experiment Panel combos
        self.pnl_experiment.update_node_lists(num_nodes)
        
    # --- New Methods (Experiment) ---
    def get_experiment_config(self):
        # Return dict or tuple with config
        cases = []
        rows = self.pnl_experiment.table_cases.rowCount()
        for r in range(rows):
            s = int(self.pnl_experiment.table_cases.item(r, 0).text())
            d = int(self.pnl_experiment.table_cases.item(r, 1).text())
            b = float(self.pnl_experiment.table_cases.item(r, 2).text())
            cases.append((s, d, b))
            
        algos = []
        # Get checked items from list
        for i in range(self.pnl_experiment.list_algos.count()):
            item = self.pnl_experiment.list_algos.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                algos.append(item.text())
        
        reps = self.pnl_experiment.spin_reps.value()
        
        return {
            "cases": cases,
            "algorithms": algos,
            "repetitions": reps
        }
    
    def add_cases_batch(self, cases_list):
        for (s, d, b) in cases_list:
             row = self.pnl_experiment.table_cases.rowCount()
             self.pnl_experiment.table_cases.insertRow(row)
             self.pnl_experiment.table_cases.setItem(row, 0, QTableWidgetItem(str(s)))
             self.pnl_experiment.table_cases.setItem(row, 1, QTableWidgetItem(str(d)))
             self.pnl_experiment.table_cases.setItem(row, 2, QTableWidgetItem(f"{b:.1f}"))
