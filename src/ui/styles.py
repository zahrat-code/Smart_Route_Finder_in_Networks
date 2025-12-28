
# Modern Dark Theme Stylesheet matching the provided image (Cyberpunk/Sci-Fi Blue)

DARK_THEME_QSS = """
/* Global Application Style */
QWidget {
    background-color: #2b2b2b;
    color: #ecf0f1;
    font-family: "Segoe UI", sans-serif;
    font-size: 14px;
}

/* Main Window & Central Widget */
QMainWindow {
    background-color: #1e1e1e;
}

/* Group Box */
QGroupBox {
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    margin-top: 24px;
    font-weight: bold;
    color: #ecf0f1;
    background-color: #2b2b2b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #bdc3c7;
}

/* Labels */
QLabel {
    color: #bdc3c7;
}

/* Push Button - Cyber Blue Gradient */
QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9);
    color: white;
    border: 1px solid #2980b9;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5dade2, stop:1 #3498db);
    border: 1px solid #5dade2;
}

QPushButton:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2980b9, stop:1 #1f618d);
}

QPushButton:disabled {
    background-color: #7f8c8d;
    border: 1px solid #7f8c8d;
    color: #bdc3c7;
}

/* Input Fields (SpinBox, ComboBox) */
QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #3d3d3d;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px;
    color: #ffffff;
    selection-background-color: #3498db;
}

QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border: 1px solid #3498db;
}

/* SpinBox Buttons & Arrows */
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    background-color: #3d3d3d;
    border-left: 1px solid #555555;
    border-bottom: 1px solid #555555;
    border-top-right-radius: 4px;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    background-color: #3d3d3d;
    border-left: 1px solid #555555;
    border-bottom-right-radius: 4px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #4d4d4d;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: url(src/ui/resources/arrow_up.png);
    width: 10px;
    height: 10px;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: url(src/ui/resources/arrow_down.png);
    width: 10px;
    height: 10px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}

QComboBox::down-arrow {
    image: url(src/ui/resources/arrow_down.png);
    width: 12px;
    height: 12px;
}


/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #2b2b2b;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #555555;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
