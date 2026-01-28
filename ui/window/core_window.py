"""
Core Configuration Window
Interactive robot frame for selecting models and components
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                                QFileDialog, QMessageBox, QGraphicsView, 
                                QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFont, QPainterPath
from PySide6.QtSvg import QSvgRenderer
from loguru import logger
import os


class ClickableRegion(QGraphicsEllipseItem):
    """Clickable region on the robot frame"""
    
    def __init__(self, x, y, width, height, component_type, tooltip_text, parent_window):
        super().__init__(x, y, width, height)
        
        self.component_type = component_type
        self.tooltip_text = tooltip_text
        self.parent_window = parent_window
        self.is_hovered = False
        
        # Make it invisible by default
        self.setPen(QPen(Qt.transparent))
        self.setBrush(QBrush(Qt.transparent))
        
        # Enable hover events
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter - glow effect"""
        self.is_hovered = True
        
        # Show glow effect
        glow_color = QColor(100, 200, 255, 100)
        self.setPen(QPen(glow_color, 3))
        self.setBrush(QBrush(glow_color))
        
        # Show tooltip
        self.setToolTip(self.tooltip_text)
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave - remove glow"""
        self.is_hovered = False
        
        # Remove glow
        self.setPen(QPen(Qt.transparent))
        self.setBrush(QBrush(Qt.transparent))
        
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle click - open file picker"""
        if event.button() == Qt.LeftButton:
            self.parent_window.select_component(self.component_type)
        super().mousePressEvent(event)


class CoreWindow(QMainWindow):
    """
    Core configuration window with interactive robot frame
    """
    
    # Component definitions: (x, y, width, height, type, tooltip, folder)
    COMPONENTS = {
        "skull": {
            "rect": (210, 50, 80, 80),
            "tooltip": "🧠 Brain / LLM\nClick to select the AI model that powers responses and reasoning",
            "folder": "models/llm",
            "filter": "GGUF Models (*.gguf);;All Files (*.*)"
        },
        "throat": {
            "rect": (230, 140, 40, 50),
            "tooltip": "🗣️ Voice / TTS\nClick to select the text-to-speech voice model",
            "folder": "models/voice",
            "filter": "Voice Models (*.onnx *.pth *.bin);;All Files (*.*)"
        },
        "ears": {
            "rect": (160, 70, 30, 40),
            "tooltip": "👂 Ears / STT\nClick to select the speech-to-text listening model",
            "folder": "models/speech",
            "filter": "Speech Models (*.onnx *.pth *.bin);;All Files (*.*)"
        },
        "heart": {
            "rect": (215, 210, 70, 60),
            "tooltip": "❤️ Heart / Personality\nClick to select the personality/character profile",
            "folder": "models/character",
            "filter": "Character Models (*.vrm *.glb *.gltf *.yaml);;All Files (*.*)"
        },
        "eyes": {
            "rect": (340, 70, 30, 40),
            "tooltip": "👁️ Eyes / Vision\nClick to select the computer vision model",
            "folder": "models/vision",
            "filter": "Vision Models (*.onnx *.pth *.bin);;All Files (*.*)"
        },
        "chest": {
            "rect": (200, 280, 100, 80),
            "tooltip": "💾 Core / Settings\nClick to configure core system settings",
            "folder": "config",
            "filter": "Config Files (*.yaml *.json);;All Files (*.*)"
        }
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("E.V3 Core Configuration")
        self.setFixedSize(600, 700)
        
        # Setup UI
        self._setup_ui()
        
        # Center window
        self._center_window()
        
        logger.info("Core window initialized")
    
    def _setup_ui(self):
        """Setup the UI"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("E.V3 Core Configuration")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #64B5F6;
                padding: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Click on different parts of the robot to configure components")
        desc.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #888;
                padding: 5px;
            }
        """)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Graphics view for robot frame
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet("background: #2b2b2b; border: 2px solid #444;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.view)
        
        # Draw robot frame
        self._draw_robot_frame()
        
        # Add clickable regions
        self._add_clickable_regions()
        
        # Status label
        self.status_label = QLabel("Ready to configure")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #aaa;
                padding: 5px;
                background: #1e1e1e;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.status_label)
    
    def _center_window(self):
        """Center window on screen"""
        from PySide6.QtGui import QScreen
        screen = QScreen.availableGeometry(self.screen())
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _draw_robot_frame(self):
        """Draw the robot frame - simplified version until image is uploaded"""
        # Try to load various image formats (check multiple case variations)
        image_paths = [
            # PNG (easiest, no dependencies)
            os.path.join("assets", "Core_Frame.png"),
            os.path.join("assets", "core_frame.png"),
            # SVG
            os.path.join("assets", "Core_Frame.svg"),
            os.path.join("assets", "core_frame.svg"),
            # EPS (requires Ghostscript)
            os.path.join("assets", "Core_Frame.eps"),
            os.path.join("assets", "core_frame.eps"),
        ]
        
        pixmap = None
        
        # Try each path
        for img_path in image_paths:
            if not os.path.exists(img_path):
                continue
                
            try:
                if img_path.endswith('.png'):
                    # Load PNG directly
                    pixmap = QPixmap(img_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(500, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        logger.info(f"Loaded PNG core frame from {img_path}")
                        break
                
                elif img_path.endswith('.svg'):
                    # Load SVG
                    renderer = QSvgRenderer(img_path)
                    pixmap = QPixmap(500, 550)
                    pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    
                    logger.info(f"Loaded SVG core frame from {img_path}")
                    break
                
                elif img_path.endswith('.eps'):
                    # Try to load EPS using Pillow (requires Ghostscript)
                    from PIL import Image
                    img = Image.open(img_path)
                    img = img.convert("RGBA")
                    
                    # Convert PIL Image to QPixmap
                    from io import BytesIO
                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    pixmap = QPixmap()
                    pixmap.loadFromData(buffer.read())
                    pixmap = pixmap.scaled(500, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    logger.info(f"Loaded EPS core frame from {img_path}")
                    break
                    
            except ImportError as e:
                logger.warning(f"Missing library for {img_path}: {e}")
            except Exception as e:
                logger.error(f"Failed to load {img_path}: {e}")
        
        if pixmap:
            self.scene.addPixmap(pixmap)
        else:
            # Draw placeholder robot frame
            logger.info("SVG not found, drawing placeholder robot")
            
            # Colors
            frame_color = QColor(100, 150, 200, 180)
            pen = QPen(frame_color, 3)
            brush = QBrush(QColor(50, 80, 120, 50))
            
            # Head (circle)
            head = self.scene.addEllipse(200, 40, 100, 100, pen, brush)
            
            # Neck
            neck = self.scene.addRect(240, 140, 20, 50, pen, brush)
            
            # Torso (rounded rectangle)
            torso = self.scene.addRect(180, 190, 140, 180, pen, brush)
            
            # Shoulders
            left_shoulder = self.scene.addEllipse(150, 200, 40, 40, pen, brush)
            right_shoulder = self.scene.addEllipse(310, 200, 40, 40, pen, brush)
            
            # Arms
            left_arm = self.scene.addRect(130, 240, 30, 120, pen, brush)
            right_arm = self.scene.addRect(340, 240, 30, 120, pen, brush)
            
            # Legs
            left_leg = self.scene.addRect(200, 370, 35, 150, pen, brush)
            right_leg = self.scene.addRect(265, 370, 35, 150, pen, brush)
            
            # Add labels
            font = QFont("Arial", 10)
            
            # Component labels with icons
            labels = [
                (230, 20, "🧠 LLM"),
                (230, 155, "🗣️ Voice"),
                (140, 75, "👂"),
                (340, 75, "👁️"),
                (230, 240, "❤️"),
                (230, 300, "💾")
            ]
            
            for x, y, text in labels:
                label = self.scene.addText(text, font)
                label.setDefaultTextColor(QColor(150, 200, 255))
                label.setPos(x, y)
    
    def _add_clickable_regions(self):
        """Add clickable regions for each component"""
        for component_id, component_data in self.COMPONENTS.items():
            x, y, w, h = component_data["rect"]
            tooltip = component_data["tooltip"]
            
            # Create clickable region
            region = ClickableRegion(x, y, w, h, component_id, tooltip, self)
            self.scene.addItem(region)
    
    def select_component(self, component_type: str):
        """Open file picker for component selection"""
        if component_type not in self.COMPONENTS:
            logger.error(f"Unknown component type: {component_type}")
            return
        
        component = self.COMPONENTS[component_type]
        folder = component["folder"]
        file_filter = component["filter"]
        
        logger.info(f"Selecting {component_type} from {folder}")
        
        # Ensure folder exists
        os.makedirs(folder, exist_ok=True)
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {component_type.title()} Model",
            folder,
            file_filter
        )
        
        if file_path:
            self._apply_component_selection(component_type, file_path)
    
    def _apply_component_selection(self, component_type: str, file_path: str):
        """Apply the selected component"""
        import yaml
        
        logger.info(f"Selected {component_type}: {file_path}")
        
        # Update status
        self.status_label.setText(f"✓ {component_type.title()} configured: {os.path.basename(file_path)}")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #4CAF50;
                padding: 5px;
                background: #1e1e1e;
                border-radius: 3px;
            }
        """)
        
        # Save to configuration
        config_file = os.path.join("config", "core_components.yaml")
        
        # Load existing config
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # Update component
        config[component_type] = {
            "path": file_path,
            "enabled": True
        }
        
        # Save config
        os.makedirs("config", exist_ok=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Show confirmation
        QMessageBox.information(
            self,
            "Component Updated",
            f"{component_type.title()} has been configured.\n\nFile: {os.path.basename(file_path)}\n\nRestart the daemon to apply changes."
        )
        
        logger.info(f"Component {component_type} saved to config")
