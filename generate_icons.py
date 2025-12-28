
import os
from PyQt6.QtGui import QImage, QPainter, QPen, QColor, QPolygonF
from PyQt6.QtCore import Qt, QPointF

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_arrow_icon(name, direction='up'):
    size = 16
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    pen = QPen(QColor("#ecf0f1")) # White-ish
    pen.setWidth(2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    
    # Draw Chevron ^
    if direction == 'up':
        points = [
            QPointF(3, 10),
            QPointF(8, 5),
            QPointF(13, 10)
        ]
    else:
        points = [
            QPointF(3, 6),
            QPointF(8, 11),
            QPointF(13, 6)
        ]
        
    painter.drawPolyline(points)
    painter.end()
    
    # Save
    path = f"src/ui/resources/{name}"
    image.save(path)
    print(f"Saved {path}")

if __name__ == "__main__":
    ensure_dir("src/ui/resources")
    create_arrow_icon("arrow_up.png", "up")
    create_arrow_icon("arrow_down.png", "down")
