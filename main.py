import sys
import os

# Add src to path if needed, though implementing as package
# Assuming we run from qos_project/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Optional: Set Stylesheet for dark mode/modern look
    app.setStyle("Fusion")
    
    from src.ui.styles import DARK_THEME_QSS
    app.setStyleSheet(DARK_THEME_QSS)
    
    print("Creating MainWindow...")
    window = MainWindow()
    print("Showing MainWindow...")
    window.show()
    
    sys.exit(app.exec())




if __name__ == "__main__":
    main()
