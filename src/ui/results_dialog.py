from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
import datetime

class ResultsDialog(QDialog):
    def __init__(self, experiment_results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Deney Sonuçları ve İstatistikler")
        self.resize(1000, 600)
        self.results = experiment_results
        
        layout = QVBoxLayout(self)
        
        # Header
        lbl_info = QLabel(f"Toplam {len(experiment_results)} deney durumu tamamlandı.")
        layout.addWidget(lbl_info)
        
        # Table
        self.table = QTableWidget()
        columns = [
            "Durum ID", "Kaynak -> Hedef", "Bant Gen.", "Algoritma", 
            "Durum", "Ort. Maliyet", "Ort. Süre (s)", "Std. Sapma", "Min/Max Süre"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Resize some columns to content
        
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
        row_count = 0
        for res in self.results:
            row_count += len(res.results)
        
        self.table.setRowCount(row_count)
        
        row_idx = 0
        for res in self.results:
            case_str = f"{res.case.source} -> {res.case.target}"
            bw_str = f"{res.case.bandwidth:.1f}"
            
            for stat in res.results:
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(res.case.case_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(case_str))
                self.table.setItem(row_idx, 2, QTableWidgetItem(bw_str))
                self.table.setItem(row_idx, 3, QTableWidgetItem(stat.algorithm_name))
                
                item_status = QTableWidgetItem(stat.status)
                if stat.status == "FAIL":
                     item_status.setForeground(Qt.GlobalColor.red)
                elif stat.status == "OK":
                     item_status.setForeground(Qt.GlobalColor.green)
                self.table.setItem(row_idx, 4, item_status)
                
                self.table.setItem(row_idx, 5, QTableWidgetItem(f"{stat.avg_cost:.4f}"))
                self.table.setItem(row_idx, 6, QTableWidgetItem(f"{stat.avg_time:.6f}"))
                self.table.setItem(row_idx, 7, QTableWidgetItem(f"{stat.std_dev_time:.6f}"))
                self.table.setItem(row_idx, 8, QTableWidgetItem(f"{stat.min_time:.5f} / {stat.max_time:.5f}"))
                
                row_idx += 1

    def export_results(self):
        path, _ = QFileDialog.getSaveFileName(self, "Sonuçları Kaydet", f"deney_sonuclari_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt", "Text Files (*.txt);;CSV Files (*.csv)")
        
        if not path:
            return
            
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Deney Raporu - {datetime.datetime.now()}\n")
                f.write("="*100 + "\n")
                # Header
                f.write(f"{'ID':<5} | {'Case':<15} | {'BW':<10} | {'Algorithm':<20} | {'Status':<10} | {'Cost':<10} | {'Time(s)':<12} | {'StdDev':<12} | {'Min/Max'}\n")
                f.write("-" * 120 + "\n")
                
                for res in self.results:
                    case_str = f"{res.case.source}->{res.case.target}"
                    
                    for stat in res.results:
                        line = (
                            f"{res.case.case_id:<5} | "
                            f"{case_str:<15} | "
                            f"{res.case.bandwidth:<10.2f} | "
                            f"{stat.algorithm_name:<20} | "
                            f"{stat.status:<10} | "
                            f"{stat.avg_cost:<10.4f} | "
                            f"{stat.avg_time:<12.6f} | "
                            f"{stat.std_dev_time:<12.6f} | "
                            f"{stat.min_time:.5f}/{stat.max_time:.5f}"
                        )
                        f.write(line + "\n")
            
            QMessageBox.information(self, "Başarılı", "Sonuçlar dosyaya kaydedildi.")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya hatası: {str(e)}")
