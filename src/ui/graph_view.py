from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, 
                            QGraphicsLineItem, QGraphicsSimpleTextItem, QMenu, 
                            QWidgetAction, QWidget, QHBoxLayout, QVBoxLayout, 
                            QSlider, QLabel, QToolButton, QGraphicsItemGroup, QPushButton)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPointF, QTimer, QSize
from PyQt6.QtGui import (QPen, QBrush, QColor, QPainter, QFont, QAction, 
                        QRadialGradient, QGradient, QIcon, QPixmap)
from typing import Dict, Optional, Tuple, List
import networkx as nx
import random
from ..core.model import NetworkTopology, Node

# Constants for drawing
NODE_RADIUS = 25
NODE_DIAMETER = NODE_RADIUS * 2
SCENE_WIDTH = 2000
SCENE_HEIGHT = 2000
DEFAULT_EDGE_WIDTH = 1

class NodeItem(QGraphicsEllipseItem):
    """
    Sürüklenebilir düğüm öğesi. Hareket ettiğinde bağlı kenarları günceller.
    (Draggable node item. Updates connected edges when moved.)
    """
    def __init__(self, node_id, x, y, graph_view, show_label=False):
        super().__init__(x - NODE_RADIUS, y - NODE_RADIUS, NODE_DIAMETER, NODE_DIAMETER)
        self.node_id = node_id
        self.graph_view = graph_view
        self.edges: List[QGraphicsLineItem] = [] # (line, is_source)
        
        # Etkinleştir: Seçilebilir, Hareket Ettirilebilir, Pozisyon Değişikliği Gönderir
        self.setFlags(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        # Enable caching for better performance
        # Use ItemCoordinateCache to avoid "CreateDIBSection failed" on deep zoom
        self.setCacheMode(QGraphicsEllipseItem.CacheMode.ItemCoordinateCache)

        # Slate Grey for normal nodes (restored)
        self.setBrush(QBrush(QColor("#78909c")))
        self.setPen(QPen(Qt.PenStyle.NoPen)) # Remove border

        self.setPen(QPen(Qt.PenStyle.NoPen)) # Remove border

        # Wave Animation State
        self.waves: List[QGraphicsEllipseItem] = []
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.is_pulsing = False
        self.pulse_color = None
        self.tick_count = 0
        self.glow_radius_base = 0 # Will be set on first pulse

        # Add text item for node ID
        self.text_item = QGraphicsSimpleTextItem(str(node_id), self)
        # Increase font size to fill the node (approx half diameter)
        font = QFont("Arial", 23) 
        font.setBold(True)
        self.text_item.setFont(font)
        self.text_item.setBrush(QBrush(Qt.GlobalColor.white))
        self.text_item.setVisible(show_label)
        
        # Center text
        r = self.text_item.boundingRect()
        
        # If we simply center it in the rect:
        rect = self.rect()
        txt_x = rect.center().x() - r.width() / 2
        txt_y = rect.center().y() - r.height() / 2
        self.text_item.setPos(txt_x, txt_y) # type: ignore

        # Animation state
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_scale = 1.0
        self.text_item.setPos(txt_x, txt_y) # type: ignore
        
    def _create_wave_item(self, color: QColor) -> QGraphicsEllipseItem:
        wave = QGraphicsEllipseItem(self)
        wave.setPen(QPen(Qt.PenStyle.NoPen))
        wave.setZValue(1) # On top of node
        
        radius = self.rect().width() / 2
        glow_radius = radius * 1.0 
        
        # Donut Gradient
        gradient = QRadialGradient(glow_radius, glow_radius, glow_radius)
        c_color = QColor(color)
        c_color.setAlpha(150)
        c_trans = QColor(color)
        c_trans.setAlpha(0)
        
        gradient.setColorAt(0.0, c_trans)
        gradient.setColorAt(0.7, c_trans) # Hollow center
        gradient.setColorAt(0.85, c_color) # Peak color
        gradient.setColorAt(1.0, c_trans) # Fade out
        
        wave.setBrush(QBrush(gradient))
        wave.setRect(0, 0, glow_radius * 2, glow_radius * 2)
        wave.setPos(-glow_radius, -glow_radius)
        wave.setTransformOriginPoint(glow_radius, glow_radius)
        
        # Initial State
        wave.setScale(1.4)
        wave.setOpacity(1.0)
        
        return wave

    def start_pulsing(self, color: QColor):
        # Clear old waves first
        self.stop_pulsing()
        
        self.pulse_color = color
        self.is_pulsing = True
        self.tick_count = 0
        
        # Spawn first wave immediately
        self._spawn_wave()
        
        if not self.pulse_timer.isActive():
            self.pulse_timer.start(50) # 20 FPS

    def stop_pulsing(self):
        self.is_pulsing = False
        self.pulse_timer.stop()
        
        # Clear all active waves
        for wave in self.waves:
            if wave.scene():
                self.scene().removeItem(wave)
        self.waves.clear()
        
    def _spawn_wave(self):
        if not self.pulse_color:
            return
        wave = self._create_wave_item(self.pulse_color)
        self.waves.append(wave)

    def _update_pulse(self):
        if not self.is_pulsing:
            return
            
        self.tick_count += 1
        
        # Spawn new wave periodically (approx every 0.6 seconds = 12 ticks)
        if self.tick_count % 12 == 0:
            self._spawn_wave()
            
        # Update existing waves
        dead_waves = []
        for wave in self.waves:
            current_scale = wave.scale()
            new_scale = current_scale + 0.05
            
            if new_scale > 3.0: # Max size
                dead_waves.append(wave)
                continue
                
            # Fade out
            # 1.4 -> 3.0 range
            progress = (new_scale - 1.4) / 1.6
            opacity = max(0.0, 1.0 - progress)
            
            wave.setScale(new_scale)
            wave.setOpacity(opacity)
            
        # Cleanup
        for wave in dead_waves:
            if wave.scene():
                self.scene().removeItem(wave)
            self.waves.remove(wave)

    def set_label_text(self, text: str, force_visible: bool = False, default_visible: bool = False, font_size: int = 23):
        self.text_item.setText(text)
        
        # Update Font
        font = self.text_item.font()
        font.setPointSize(font_size)
        font.setBold(True)
        self.text_item.setFont(font)
        
        # Re-center
        r = self.text_item.boundingRect()
        rect = self.rect()
        txt_x = rect.center().x() - r.width() / 2
        txt_y = rect.center().y() - r.height() / 2
        self.text_item.setPos(txt_x, txt_y)
        
        if force_visible:
            self.text_item.setVisible(True)
        else:
            self.text_item.setVisible(default_visible)

    # Removed old helper methods that are no longer needed
    def remove_glow(self):
        self.stop_pulsing()


    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.update_edges()
        return super().itemChange(change, value)

    def update_edges(self):
        # Düğümün yeni merkezi
        center = self.scenePos() + QPointF(NODE_RADIUS, NODE_RADIUS) # local rect offset
        # Aslında scenePos() item'ın (0,0) noktasını verir (o da rect.topLeft değil, item'ın local koordinat sistemidir).
        # Ellipse rect'imiz (x-R, y-R) ile tanımlı olduğu için, item'ın orijini merkez değil.
        # Ancak spring_layout'dan gelen x,y'yi setPos ile değil rect ile set ettik.
        # Daha temiz yöntem: rect'i (-R, -R, D, D) yapıp setPos(x, y) kullanmak.
        
        # Hack: mevcut rect mantığına göre hareket:
        # scenePos, sürüklemeden kaynaklı ofsettir.
        # Orijinal rect (x-R, y-R).
        # Güncel merkez = scenePos() + OrijinalMerkez
        
        # Basitlik için: tüm kenarları yeniden çizmek yerine uç noktalarını güncelle.
        # Ama QGraphicsLineItem'ın setLine'ı var.
        pass # Bu mantığı graph_view içinde yönetmek daha kolay olabilir veya burada.
        
        if self.graph_view:
            self.graph_view.update_connected_edges(self.node_id)

class GraphView(QGraphicsView):
    """
    Ağ topolojisini görselleştirmek için araç.
    Renkler:
    - Normal Düğüm: #3498db (Mavi)
    - Kaynak Düğüm: #2ecc71 (Yeşil)
    - Hedef Düğüm: #e74c3c (Kırmızı)
    - Yol Kenarları: #f1c40f (Sarı/Altın)
    - Normal Kenarlar: #95a5a6 (Gri)
    """
    node_selected = pyqtSignal(int)  # Tıklandığında düğüm kimliğini yayan sinyal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, SCENE_WIDTH, SCENE_HEIGHT)
        self.setScene(self.scene)
        
        # Set Black Background for the space look
        self.setBackgroundBrush(QBrush(QColor("#0b0e14")))
        
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Performance optimizations
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        
        self.show_node_labels = False
        self.edge_alpha = 150 
        self.edge_width = DEFAULT_EDGE_WIDTH
        
        # Blinking Effect Removed
        # self.blink_timer = QTimer(self)
        # self.blink_timer.timeout.connect(self.toggle_glow)
        # self.blink_timer.start(100) # 100ms = 10Hz
        self.glow_visible = True



        
        self.topology: Optional[NetworkTopology] = None
        self.node_positions: Dict[int, Tuple[float, float]] = {}
        self.node_items: Dict[int, NodeItem] = {}
        self.edge_items: Dict[Tuple[int, int], QGraphicsLineItem] = {}
        self.edge_group: Optional[QGraphicsItemGroup] = None
        
        self.source_id: Optional[int] = None
        self.target_id: Optional[int] = None
        self.path_nodes: Optional[List[int]] = None
        self.source_target_line: Optional[QGraphicsLineItem] = None

        self.source_target_line: Optional[QGraphicsLineItem] = None

        # Packet Animation
        self.active_packets: List[Dict] = [] # List of dicts: {'item': QGraphicsItem, 'segment': int, 'progress': float}
        self.packet_timer = QTimer(self)
        self.packet_timer.timeout.connect(self._update_packet_animation)
        self.packet_path_indices: List[int] = [] # List of node IDs in order
        self.packet_speed = 0.15 # Faster speed
        self.packet_spawn_tick = 0

        # Debounce timer for style updates
        self.style_update_timer = QTimer(self)
        self.style_update_timer.setSingleShot(True)
        self.style_update_timer.timeout.connect(self._apply_edge_style)

        # Setup Floating Controls
        self.setup_floating_controls()

    def setup_floating_controls(self):
        # Common Style
        # Dark Circular Style matching the image
        btn_style = """
            QPushButton {
                background-color: #1a1e24; 
                border: 1px solid #2c323c;
                border-radius: 20px;
                font-weight: bold;
                font-size: 20px;
                color: #ecf0f1;
            }
            QPushButton:hover {
                background-color: #2c323c;
            }
            QPushButton:pressed {
                background-color: #0b0e14;
            }
        """
        
        # Zoom In (+)
        self.btn_zoom_in = QPushButton("+", self)
        self.btn_zoom_in.setFixedSize(40, 40)
        self.btn_zoom_in.setStyleSheet(btn_style)
        self.btn_zoom_in.setToolTip("Yakınlaş")
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        
        # Zoom Out (-)
        self.btn_zoom_out = QPushButton("-", self)
        self.btn_zoom_out.setFixedSize(40, 40)
        self.btn_zoom_out.setStyleSheet(btn_style)
        self.btn_zoom_out.setToolTip("Uzaklaş")
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        
        # Toggle Labels (Eye)
        self.btn_labels = QPushButton("", self) # No text, icon only
        self.btn_labels.setFixedSize(40, 40)
        self.btn_labels.setStyleSheet(btn_style)
        self.btn_labels.setToolTip("Etiketleri Göster/Gizle")
        self.btn_labels.setCheckable(True)
        # Default is Hidden -> Show Slashed Eye (Closed)
        self.btn_labels.setIcon(self._create_eye_icon(slashed=True))
        self.btn_labels.setIconSize(QSize(24, 24))
        self.btn_labels.clicked.connect(self.toggle_node_labels_click)

    def _create_eye_icon(self, slashed: bool) -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Eye Shape
        pen = QPen(QColor("#eeeeee"))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Outer Eye
        # (x, y, w, h)
        # Eye almond shape: usually two arcs
        path = QPainter.Qt.QPainterPath() if hasattr(QPainter, 'Qt') else None # Type hint workaround, logic below
        
        # Draw pupil
        brush = QBrush(QColor("#eeeeee"))
        painter.setBrush(brush)
        painter.drawEllipse(13, 13, 6, 6)
        
        # Draw outline (Simple ellipse implementation for robustness)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(4, 8, 24, 16)
        
        if slashed:
            pen.setWidth(3)
            # pen.setColor(QColor("#e74c3c")) # Red slash or just dark?
            painter.setPen(pen)
            painter.drawLine(6, 6, 26, 26)
            
        painter.end()
        return QIcon(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position buttons at bottom right
        pad = 20
        btn_s = 40
        gap = 10
        
        x = self.width() - btn_s - pad
        y_start = self.height() - btn_s - pad
        
        # Stack: Eye (Bottom), Zoom Out (Above), Zoom In (Top)
        self.btn_labels.move(x, y_start)
        self.btn_zoom_out.move(x, y_start - btn_s - gap)
        self.btn_zoom_in.move(x, y_start - 2*btn_s - 2*gap)

    def zoom_in(self):
        self.scale(1.15, 1.15)
        
    def zoom_out(self):
        self.scale(1/1.15, 1/1.15)
        
    def toggle_node_labels_click(self):
        # Toggle text visibility
        is_visible = self.btn_labels.isChecked()
        self.toggle_node_labels(is_visible)
        
        # Update Icon: 
        # Visible -> Show Open Eye (Watching)
        # Hidden -> Show Slashed Eye (Closed)
        
        if is_visible:
            self.btn_labels.setIcon(self._create_eye_icon(slashed=False))
        else:
            self.btn_labels.setIcon(self._create_eye_icon(slashed=True))

    def set_topology(self, topology: NetworkTopology):
        # 1. Disable logic callbacks
        self.topology = None
        
        # 2. Clear references to items to prevent access during deletion
        # Clear dictionaries holding references to items
        self.node_items.clear()
        self.edge_items.clear()
        
        # Clear single item references
        self.source_target_line = None
        self.edge_group = None
        
        if hasattr(self, 'path_overlay_items'):
             self.path_overlay_items = []
        
        self.path_nodes = None
        self.source_id = None
        self.target_id = None
        
        # 3. Stop animations (removes packet items safely)
        if hasattr(self, 'stop_packet_animation'):
             self.stop_packet_animation()
             
        # 4. Now safe to clear scene
        self.scene.clear()
        
        # 5. Set new topology
        self.topology = topology
        
        # Generate Starfield
        self._generate_starfield()
        
        # Kümelerin daha iyi görselleştirilmesi için yay (spring) düzenini kullanarak pozisyonları hesapla
        # k: Optimal distance between nodes. Increase to spread nodes out.
        # iterations: Number of iterations simulations.
        try:
             # Calculate optimal k based on node count to prevent clustering
             num_nodes = len(topology.graph.nodes())
             k_value = 12.0 / (num_nodes ** 0.5) if num_nodes > 0 else None
             
             pos = nx.spring_layout(
                 topology.graph, 
                  scale=950, 
                  center=(SCENE_WIDTH/2, SCENE_HEIGHT/2), 
                 seed=42,
                 k=k_value,
                 iterations=20
             )
        except:
             # Fallback if something goes wrong
             pos = nx.spring_layout(topology.graph, scale=800, center=(SCENE_WIDTH/2, SCENE_HEIGHT/2), seed=42)
             
        self.node_positions = {n: (p[0], p[1]) for n, p in pos.items()}
        
        self.draw_graph()

    def toggle_node_labels(self, visible: bool):
        self.show_node_labels = visible
        for item in self.node_items.values():
            item.text_item.setVisible(visible)

    def draw_graph(self):
        if not self.topology:
            return

        # Düğümleri Çiz (Node Items)
        # Önce düğümleri oluştur ki kenarlar referans alabilsin mi? 
        # Hayır, Z-order ile kenarlar arkada kalsın.
        
        # Ancak dinamik güncelleme için düğümlerin nesnelerine ihtiyacımız var.
        
        # 1. Düğümleri oluştur
        for node_id, (x, y) in self.node_positions.items():
            # Rect'i merkeze göre ayarla (-R, -R) böylece setPos(x,y) tam merkez olur
            item = NodeItem(node_id, 0, 0, self, self.show_node_labels) 
            item.setRect(-NODE_RADIUS, -NODE_RADIUS, NODE_DIAMETER, NODE_DIAMETER)
            item.setPos(x, y)
            item.setZValue(10) # Düğümler üstte
            self.scene.addItem(item)
            self.node_items[node_id] = item

        # 2. Kenarları Çiz
        # 2. Kenarları Çiz
        # Gruplama ile performans optimizasyonu
        self.edge_group = QGraphicsItemGroup()
        self.scene.addItem(self.edge_group)
        self.edge_group.setZValue(0) # Kenarlar altta
        self.edge_group.setOpacity(self.edge_alpha / 255.0) # Apply current opacity

        color = QColor("#4A4A4A") # User requested darker grey
        color.setAlpha(120) # Slightly more opaque for visibility
        pen_normal = QPen(color) 
        pen_normal.setWidth(self.edge_width) # Apply current width
        pen_normal.setCosmetic(True) # Performance optimization

        
        for u, v in self.topology.graph.edges:
             pos_u = self.node_items[u].scenePos()
             pos_v = self.node_items[v].scenePos()
             
             line = QGraphicsLineItem(pos_u.x(), pos_u.y(), pos_v.x(), pos_v.y())
             line.setPen(pen_normal)
             self.edge_group.addToGroup(line)
             # line.setZValue(0) # ZValue handled by group
             
             self.edge_items[(u, v)] = line
             self.edge_items[(v, u)] = line # Çift yönlü erişim için

        # Auto-fit to show the whole graph
        self.fit_to_view()

    def fit_to_view(self):
        """Auto-zoom to fit the graph with padding"""
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)



    def _generate_starfield(self):
        """Generate random 'stars' in the background"""
        num_stars = 200
        for _ in range(num_stars):
            x = random.randint(0, SCENE_WIDTH)
            y = random.randint(0, SCENE_HEIGHT)
            size = random.choice([1, 2, 2, 3])
            
            star = QGraphicsEllipseItem(x, y, size, size)
            
            # Random brightness/color
            brightness = random.randint(100, 255)
            color = QColor(brightness, brightness, brightness)
            color.setAlpha(random.randint(50, 200)) # Random transparency
            
            star.setBrush(QBrush(color))
            star.setPen(QPen(Qt.PenStyle.NoPen))
            star.setZValue(-100) # Behind everything
            
            self.scene.addItem(star)
            
    def update_connected_edges(self, node_id):
        """NodeItem hareket ettiğinde çağrılır."""
        if not self.topology:
            return
            
        # Update source-target line if applicable
        if self.source_target_line and (node_id == self.source_id or node_id == self.target_id):
             self.draw_source_target_line() # Redraw or update line
            
        item = self.node_items[node_id]
        new_pos = item.scenePos()
        
        # Bu düğüme bağlı tüm kenarları bul ve güncelle
        for neighbor in self.topology.graph.neighbors(node_id):
            edge_key = (node_id, neighbor)
            if edge_key in self.edge_items:
                line_item = self.edge_items[edge_key]
                other_item = self.node_items[neighbor]
                other_pos = other_item.scenePos()
                
                line_item.setLine(new_pos.x(), new_pos.y(), other_pos.x(), other_pos.y())
                
        # Eğer yol vurgusu varsa onu güncelle (overlay'i yeniden çiz)
        if self.path_nodes and node_id in self.path_nodes:
            self.draw_path_overlay()

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        # Tıklanan NodeItem ise sinyal gönder
        # (NodeItem, QGraphicsItem'dan türetildiği için bu çalışır, ancak scenePos ve parent yapısı farklı olabilir)
        # itemAt en üsttekini verir.
        
        # NodeItem sürüklemeyi engellememesi için, sadece tıklama (basıp bırakma) mı yoksa sürükleme mi ayırt edilmeli?
        # QGraphicsView varsayılan davranışı: ItemIsMovable varsa sürükler.
        # Biz sadece seçim yapmak istiyoruz. Sürükleme başladığında seçim değişmemeli mi?
        # Basitçe: her tıklamada seç.
        
        # Not: itemAt bazen line veya scene döner.
        if isinstance(item, NodeItem):
            self.node_selected.emit(item.node_id)
        
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)


    def set_source(self, node_id: int):
        self.source_id = node_id
        self.update_colors()
        self.draw_source_target_line()

    def set_target(self, node_id: int):
        self.target_id = node_id
        self.update_colors()
        self.draw_source_target_line()

    def highlight_path(self, path_nodes: List[int]):
        self.path_nodes = path_nodes
        self.update_colors()

    def update_colors(self):
        # Reset all nodes
        for nid, item in self.node_items.items():
            radius = NODE_RADIUS
            
            # Reset glow/pulse first - explicitly stop any active pulsing
            item.stop_pulsing()
            item.setZValue(10) # Reset Z-Value to default
            
            if nid == self.source_id:
                item.setBrush(QBrush(QColor("#39ff14"))) # Neon Green
                # Source Node Style
                pen = QPen(Qt.GlobalColor.white)
                pen.setWidth(2)
                item.setPen(pen)
                
                radius = NODE_RADIUS * 2.5 
                item.setRect(-radius, -radius, radius*2, radius*2)
                item.start_pulsing(QColor("#39ff14")) # Neon Green Pulse
                item.setZValue(100) # Bring to top
                
                item.set_label_text("S", force_visible=True, font_size=40)
                
            elif nid == self.target_id:
                item.setBrush(QBrush(QColor("#ff073a"))) # Neon Red
                # Target Node Style
                pen = QPen(Qt.GlobalColor.white)
                pen.setWidth(2)
                item.setPen(pen)

                radius = NODE_RADIUS * 2.5 
                item.setRect(-radius, -radius, radius*2, radius*2)
                item.start_pulsing(QColor("#ff073a")) # Neon Red Pulse
                item.setZValue(100) # Bring to top
                
                item.set_label_text("D", force_visible=True, font_size=40)
                
            elif self.path_nodes and nid in self.path_nodes:
                 item.setBrush(QBrush(QColor("#ffd700"))) # Gold/Yellow for path
                 
                 # Increase size for path nodes
                 radius = NODE_RADIUS * 1.4
                 item.setRect(-radius, -radius, radius*2, radius*2)
                 item.setZValue(20) # Slightly above normal nodes
                 
                 item.set_label_text(str(nid), force_visible=True, font_size=30)
            else:
                item.setBrush(QBrush(QColor("#78909c"))) # Slate Grey for normal nodes
                item.setPen(QPen(Qt.PenStyle.NoPen)) # Ensure no border for others
                
                # Boyut güncelleme (Reset size)
                diameter = NODE_RADIUS * 2
                item.setRect(-NODE_RADIUS, -NODE_RADIUS, diameter, diameter)
                
                item.set_label_text(str(nid), default_visible=self.show_node_labels, font_size=23)

        self.draw_path_overlay()
        


    def get_boundary_point(self, node_item: QGraphicsEllipseItem, target_pos: QPointF) -> QPointF:
        """Calculate the point on the node's boundary towards the target."""
        center = node_item.scenePos()
        # Vector from center to target
        dx = target_pos.x() - center.x()
        dy = target_pos.y() - center.y()
        length = (dx**2 + dy**2)**0.5
        
        if length == 0:
            return center
            
        # Normalize and scale by radius
        # Note: boundingRect is (-R, -R, 2R, 2R), so width/2 is radius
        radius = node_item.rect().width() / 2
        
        # Add a small padding so it doesn't touch exactly (optional)
        radius += 2 
        
        bx = center.x() + (dx / length) * radius
        by = center.y() + (dy / length) * radius
        
        return QPointF(bx, by)

    def draw_path_overlay(self):
        # 1. Eski kaplamayı kaldır
        if hasattr(self, 'path_overlay_items'):
            for item in self.path_overlay_items:
                if item.scene():
                    self.scene.removeItem(item)
        self.path_overlay_items = []
        
        if not self.path_nodes or len(self.path_nodes) < 2:
            return

        pen_path = QPen(QColor("#ffd700"))
        pen_path.setWidth(3)
        
        for i in range(len(self.path_nodes) - 1):
            u = self.path_nodes[i]
            v = self.path_nodes[i+1]
            if u in self.node_items and v in self.node_items:
                node_u = self.node_items[u]
                node_v = self.node_items[v]
                
                pos_u = node_u.scenePos()
                pos_v = node_v.scenePos()
                
                # Calculate boundary points
                start_point = self.get_boundary_point(node_u, pos_v)
                end_point = self.get_boundary_point(node_v, pos_u)
                
                line = self.scene.addLine(start_point.x(), start_point.y(), end_point.x(), end_point.y(), pen_path)
                line.setZValue(200) # Nodes are 10, path overlay 5, edges 0
                self.path_overlay_items.append(line)
        
        # Start Animation
        self.start_packet_animation()

    def start_packet_animation(self):
        self.stop_packet_animation()
        
        if not self.path_nodes or len(self.path_nodes) < 2:
            return
            
        self.packet_path_indices = self.path_nodes
        self.packet_spawn_tick = 0
             
        self.packet_timer.start(30) # 30ms interval

    def stop_packet_animation(self):
        self.packet_timer.stop()
        
        # Clear all packets
        for packet in self.active_packets:
            if packet['item'].scene():
                self.scene.removeItem(packet['item'])
        self.active_packets.clear()
        
        # Also clear legacy single packet if exists
        if hasattr(self, 'packet_item') and self.packet_item:
             if self.packet_item and self.packet_item.scene():
                 self.scene.removeItem(self.packet_item)
             self.packet_item = None

    def _spawn_new_packet(self):
         # Create Packet Item
        item = QGraphicsEllipseItem(-14, -14, 28, 28)
        item.setBrush(QBrush(QColor("#FFFFFF"))) # White
        item.setPen(QPen(Qt.GlobalColor.black, 1))
        item.setZValue(300) 
        self.scene.addItem(item)
        
        # Start at beginning
        start_node = self.packet_path_indices[0]
        if start_node in self.node_items:
             pos = self.node_items[start_node].scenePos()
             item.setPos(pos)
             
        self.active_packets.append({
            'item': item,
            'segment': 0,
            'progress': 0.0
        })

    def _update_packet_animation(self):
        if not self.packet_path_indices:
            self.stop_packet_animation()
            return

        # 1. Spawn new packets periodically
        self.packet_spawn_tick += 1
        if self.packet_spawn_tick % 5 == 0: # Every 5 ticks (~150ms)
            self._spawn_new_packet()

        # 2. Update all active packets
        packets_to_remove = []
        
        for packet in self.active_packets:
            # Move progress
            packet['progress'] += self.packet_speed
            
            if packet['progress'] >= 1.0:
                packet['progress'] = 0.0
                packet['segment'] += 1
                
                # Check if reached end
                if packet['segment'] >= len(self.packet_path_indices) - 1:
                    packets_to_remove.append(packet)
                    continue
            
            # Update Position
            u_id = self.packet_path_indices[packet['segment']]
            v_id = self.packet_path_indices[packet['segment'] + 1]
            
            if u_id in self.node_items and v_id in self.node_items:
                pos_u = self.node_items[u_id].scenePos()
                pos_v = self.node_items[v_id].scenePos()
                
                # Linear Interpolation
                new_x = pos_u.x() + (pos_v.x() - pos_u.x()) * packet['progress']
                new_y = pos_u.y() + (pos_v.y() - pos_u.y()) * packet['progress']
                
                packet['item'].setPos(new_x, new_y)
                
        # 3. Cleanup finished packets
        for packet in packets_to_remove:
            if packet['item'].scene():
                self.scene.removeItem(packet['item'])
            self.active_packets.remove(packet)

    def draw_source_target_line(self):
        # Remove existing line
        if self.source_target_line:
            self.scene.removeItem(self.source_target_line)
            self.source_target_line = None
            
        if self.source_id is None or self.target_id is None:
            return
            
        # Check validity
        # if self.source_id not in self.node_items or self.target_id not in self.node_items:
        #    return
            
        # pos_s = self.node_items[self.source_id].scenePos()
        # pos_t = self.node_items[self.target_id].scenePos()
        
        # Style: Dashed Yellow Line indicating direct logical link
        # pen = QPen(QColor("#f1c40f"))
        # pen.setWidth(2)
        # pen.setStyle(Qt.PenStyle.DashLine)
        
        # self.source_target_line = self.scene.addLine(pos_s.x(), pos_s.y(), pos_t.x(), pos_t.y(), pen)
        # self.source_target_line.setZValue(5) # Nodes are 10, path overlay 5 (same), edges 0
        pass

    # Remove old increase/decrease methods as we'll use a direct setter from the slider
    # Remove old increase/decrease methods as we'll use a direct setter from the slider
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2b2b2b; color: white; border: 1px solid #3d3d3d; }
            QWidget { background-color: transparent; color: white; }
            QSlider::groove:horizontal { border: 1px solid #3d3d3d; height: 8px; background: #1e1e1e; margin: 2px 0; border-radius: 4px; }
            QSlider::handle:horizontal { background: #3498db; border: 1px solid #3498db; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px; }
            QToolButton { background-color: #3d3d3d; border: none; border-radius: 3px; padding: 4px; font-weight: bold; }
            QToolButton:hover { background-color: #4d4d4d; }
            QToolButton:pressed { background-color: #2d2d2d; }
        """)
        
        # --- Opacity Control ---
        opacity_action = QWidgetAction(menu)
        opacity_widget = QWidget()
        op_layout = QHBoxLayout(opacity_widget)
        op_layout.setContentsMargins(10, 5, 10, 5)
        
        lbl_op = QLabel("Opaklık:")
        lbl_op.setFixedWidth(60)
        
        slider_op = QSlider(Qt.Orientation.Horizontal)
        slider_op.setRange(10, 255)
        slider_op.setValue(self.edge_alpha)
        slider_op.setFixedWidth(100)
        
        # Helper to update value but defer redraw if dragging
        def on_alpha_change(val):
            self.edge_alpha = val
            # Optimize: Update group opacity directly (Instant, no redraw needed)
            if self.edge_group:
                self.edge_group.setOpacity(val / 255.0)

        slider_op.valueChanged.connect(on_alpha_change)
        # slider_op.sliderReleased.connect(self.update_edge_style) # Not needed for opacity anymore
        
        btn_minus_op = QToolButton()
        btn_minus_op.setText("-")
        btn_minus_op.clicked.connect(lambda: slider_op.setValue(max(slider_op.minimum(), slider_op.value() - 25)))
        
        btn_plus_op = QToolButton()
        btn_plus_op.setText("+")
        btn_plus_op.clicked.connect(lambda: slider_op.setValue(min(slider_op.maximum(), slider_op.value() + 25)))
        
        op_layout.addWidget(lbl_op)
        op_layout.addWidget(btn_minus_op)
        op_layout.addWidget(slider_op)
        op_layout.addWidget(btn_plus_op)
        
        opacity_action.setDefaultWidget(opacity_widget)
        menu.addAction(opacity_action)

        # --- Width Control ---
        width_action = QWidgetAction(menu)
        width_widget = QWidget()
        w_layout = QHBoxLayout(width_widget)
        w_layout.setContentsMargins(10, 5, 10, 5)
        
        lbl_w = QLabel("Kalınlık:")
        lbl_w.setFixedWidth(60)
        
        slider_w = QSlider(Qt.Orientation.Horizontal)
        slider_w.setRange(1, 10)
        slider_w.setValue(self.edge_width)
        slider_w.setFixedWidth(100)
        
        def on_width_change(val):
            self.edge_width = val
            # Debounced update for width (requires iterating items)
            self.update_edge_style()
                
        slider_op.valueChanged.connect(on_alpha_change)
        slider_w.valueChanged.connect(on_width_change)
        # slider_w.sliderReleased.connect(self.update_edge_style) # Covered by debounced call
        
        btn_minus_w = QToolButton()
        btn_minus_w.setText("-")
        btn_minus_w.clicked.connect(lambda: slider_w.setValue(max(slider_w.minimum(), slider_w.value() - 1)))
        
        btn_plus_w = QToolButton()
        btn_plus_w.setText("+")
        btn_plus_w.clicked.connect(lambda: slider_w.setValue(min(slider_w.maximum(), slider_w.value() + 1)))
        
        w_layout.addWidget(lbl_w)
        w_layout.addWidget(btn_minus_w)
        w_layout.addWidget(slider_w)
        w_layout.addWidget(btn_plus_w)
        
        width_action.setDefaultWidget(width_widget)
        menu.addAction(width_action)
        
        menu.exec(event.globalPos())

    def set_edge_alpha(self, value):
        # Used by programmatic calls if any, otherwise local helpers used
        if self.edge_alpha == value:
            return
        self.edge_alpha = value
        self.update_edge_style()

    def set_edge_width(self, value):
        if self.edge_width == value:
            return
        self.edge_width = value
        self.update_edge_style()

    def update_edge_style(self):
        """
        Debounced call to apply edge styles.
        Prevents UI freezing during rapid slider changes.
        """
        self.style_update_timer.start(50)  # Wait 50ms before applying changes

    def _apply_edge_style(self):
        if not self.topology:
            return
            
        color = QColor("#555555")
        color.setAlpha(255) # Alpha handled by group opacity
        
        pen = QPen(color)
        pen.setWidth(self.edge_width)
        pen.setCosmetic(True)
        
        # Optimize: Iterate over unique lines only
        unique_lines = set(self.edge_items.values())
        
        self.scene.blockSignals(True)
        try:
            for line_item in unique_lines:
                # Safety check for C++ deleted objects
                try:
                    line_item.setPen(pen)
                except RuntimeError:
                    pass
        except Exception as e:
            print(f"Error updating edge style: {e}")
        finally:
            self.scene.blockSignals(False)
            self.scene.update()
