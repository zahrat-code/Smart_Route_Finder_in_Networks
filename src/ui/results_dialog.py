from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
import datetime
import statistics

class ResultsDialog(QDialog):
    """
    Displays the comparison results (dictionary format) in a table.
    expected results format:
    {
       'AlgorithmName': {'costs': [c1, c2, ...], 'times': [t1, t2, ...]},
       ...
    }
    """
    def __init__(self, results_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Karşılaştırmalı Analiz Sonuçları")
        self.resize(1000, 500)
        self.results_data = results_data
        
        layout = QVBoxLayout(self)
        
        # Header
        lbl_info = QLabel("Algoritma Performans Karşılaştırması")
        font = lbl_info.font()
        font.setBold(True)
        font.setPointSize(12)
        lbl_info.setFont(font)
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)
        
        # Table
        self.table = QTableWidget()
        columns = [
            "Algoritma", "Ort. Maliyet", "En İyi Maliyet", "En Kötü Maliyet", 
            "Std. Sapma", "Ort. Süre (s)"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        
        # Populate
        self.populate_table()
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_export = QPushButton("Sonuçları Kaydet (TXT)")
        self.btn_export.clicked.connect(self.export_results)
        self.btn_close = QPushButton("Kapat")
        self.btn_close.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)

    def populate_table(self):
        self.table.setRowCount(0)
        
        for algo_name, metrics in self.results_data.items():
            costs = metrics['costs']
            times = metrics['times']
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Algorithm Name
            self.table.setItem(row, 0, QTableWidgetItem(algo_name))
            
            if not costs:
                # FAIL case
                item_fail = QTableWidgetItem("FAIL")
                item_fail.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 1, item_fail)
                # Fill rest with dashes
                for c in range(2, 6):
                    self.table.setItem(row, c, QTableWidgetItem("-"))
                continue
            
            # Calculations
            avg_cost = statistics.mean(costs)
            min_cost = min(costs)
            max_cost = max(costs)
            std_dev = statistics.stdev(costs) if len(costs) > 1 else 0.0
            avg_time = statistics.mean(times)
            
            # Set Items
            self.table.setItem(row, 1, QTableWidgetItem(f"{avg_cost:.4f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{min_cost:.4f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{max_cost:.4f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{std_dev:.4f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{avg_time:.4f}"))


    def export_results(self):
        path, _ = QFileDialog.getSaveFileName(self, "Sonuçları Kaydet", f"karsilastirma_sonuclari_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt", "Text Files (*.txt)")
        
        if not path:
            return
            
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Karşılaştırmalı Analiz Raporu - {datetime.datetime.now()}\n")
                f.write("="*100 + "\n")
                # Header
                f.write(f"{'Algoritma':<25} | {'Ort. Maliyet':<15} | {'En İyi':<12} | {'En Kötü':<12} | {'Std. Sapma':<12} | {'Süre (s)':<10}\n")
                f.write("-" * 100 + "\n")
                
                for algo_name, metrics in self.results_data.items():
                    costs = metrics['costs']
                    times = metrics['times']
                    
                    if not costs:
                        f.write(f"{algo_name:<25} | {'FAIL':<15} | {'-':<12} | {'-':<12} | {'-':<12} | {'-':<10}\n")
                        continue
                        
                    avg_cost = statistics.mean(costs)
                    min_cost = min(costs)
                    max_cost = max(costs)
                    std_dev = statistics.stdev(costs) if len(costs) > 1 else 0.0
                    avg_time = statistics.mean(times)
                    
                    line = (
                        f"{algo_name:<25} | "
                        f"{avg_cost:<15.4f} | "
                        f"{min_cost:<12.4f} | "
                        f"{max_cost:<12.4f} | "
                        f"{std_dev:<12.4f} | "
                        f"{avg_time:<10.4f}"
                    )
                    f.write(line + "\n")
            
            QMessageBox.information(self, "Başarılı", "Sonuçlar dosyaya kaydedildi.")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya hatası: {str(e)}")
