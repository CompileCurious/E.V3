"""
Modules Configuration Window
Interactive robot frame for selecting models and components
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QFileDialog, QMessageBox, QGraphicsView, 
                                QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem, QLineEdit)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QTimer
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
        
        # Start invisible
        self.setPen(QPen(QColor(0, 0, 0, 0), 0))
        self.setBrush(QBrush(QColor(0, 0, 0, 0)))
        
        # Set tooltip
        self.setToolTip(tooltip_text)
        
        # Enable hover events
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter - blue glow effect"""
        self.is_hovered = True
        
        # Show blue glow effect
        glow_color = QColor(100, 180, 255, 180)
        self.setPen(QPen(glow_color, 4))
        self.setBrush(QBrush(QColor(100, 180, 255, 100)))
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave - return to invisible"""
        self.is_hovered = False
        
        # Return to invisible
        self.setPen(QPen(QColor(0, 0, 0, 0), 0))
        self.setBrush(QBrush(QColor(0, 0, 0, 0)))
        
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle click - open file picker"""
        if event.button() == Qt.LeftButton:
            self.parent_window.select_component(self.component_type)
        super().mousePressEvent(event)


class ModulesWindow(QMainWindow):
    """
    Modules configuration window with interactive robot frame
    """
    
    # Component definitions: (x, y, width, height, type, tooltip, folder)
    COMPONENTS = {
        "skull": {
            "rect": (420, 140, 90, 100),
            "tooltip": "🧠 Brain / LLM\nClick to select the AI model that powers responses and reasoning",
            "folder": "models/llm",
            "filter": "GGUF Models (*.gguf);;All Files (*.*)"
        },
        "throat": {
            "rect": (435, 240, 60, 50),
            "tooltip": "🗣️ Voice / TTS\nClick to select the text-to-speech voice model",
            "folder": "models/voice",
            "filter": "Voice Models (*.onnx *.pth *.bin);;All Files (*.*)"
        },
        "ears": {
            "rect": (390, 160, 50, 60),
            "tooltip": "👂 Ears / STT\nClick to select the speech-to-text listening model",
            "folder": "models/speech",
            "filter": "Speech Models (*.onnx *.pth *.bin);;All Files (*.*)"
        },
        "heart": {
            "rect": (420, 340, 80, 70),
            "tooltip": "❤️ Heart / Personality\nClick to select the personality/character profile",
            "folder": "models/character",
            "filter": "Character Models (*.vrm *.glb *.gltf *.yaml);;All Files (*.*)"
        },
        "eyes": {
            "rect": (490, 160, 50, 60),
            "tooltip": "👁️ Eyes / Vision\nClick to select the computer vision model",
            "folder": "models/vision",
            "filter": "Vision Models (*.onnx *.pth *.bin);;All Files (*.*)"
        },
        "chest": {
            "rect": (410, 430, 100, 90),
            "tooltip": "💾 Modules / Settings\nClick to configure modules system settings",
            "folder": "config",
            "filter": "Config Files (*.yaml *.json);;All Files (*.*)"
        }
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("E.V3 Modules Configuration")
        self.setFixedSize(500, 650)
        
        # Setup UI
        self._setup_ui()
        
        # Center window
        self._center_window()
        
        logger.info("Modules window initialized")
    
    def _setup_ui(self):
        """Setup the UI"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("E.V3 Modules Configuration")
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
        desc = QLabel("Click on components of E.V3's frame to select modules")
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
        
        # Terminal-style commit widget
        terminal_widget = QWidget()
        terminal_layout = QHBoxLayout(terminal_widget)
        terminal_layout.setContentsMargins(10, 5, 10, 5)
        
        self.commit_label = QLabel("commit_to_modules? (Y/N)")
        self.commit_label.setStyleSheet("""
            QLabel {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                color: #64B5F6;
                padding: 5px;
                background: #1a1a1a;
            }
        """)
        
        self.commit_input = QLineEdit()
        self.commit_input.setMaxLength(1)
        self.commit_input.setFixedWidth(30)
        self.commit_input.setStyleSheet("""
            QLineEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                color: #64B5F6;
                background: #1a1a1a;
                border: 1px solid #444;
                padding: 3px;
            }
        """)
        self.commit_input.returnPressed.connect(self._handle_commit)
        
        terminal_layout.addWidget(self.commit_label)
        terminal_layout.addWidget(self.commit_input)
        terminal_layout.addStretch()
        
        terminal_widget.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 3px;
            }
        """)
        
        layout.addWidget(terminal_widget)
        
        # Track pending changes
        self.pending_changes = {}
    
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
                        # Scale to a reasonable size
                        pixmap = pixmap.scaled(480, 580, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        logger.info(f"Loaded PNG modules frame from {img_path}")
                        break
                
                elif img_path.endswith('.svg'):
                    # Load SVG
                    renderer = QSvgRenderer(img_path)
                    pixmap = QPixmap(480, 580)
                    pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    
                    logger.info(f"Loaded SVG modules frame from {img_path}")
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
                    # Scale to reasonable size
                    pixmap = pixmap.scaled(480, 580, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    logger.info(f"Loaded EPS modules frame from {img_path}")
                    break
                    
            except ImportError as e:
                logger.warning(f"Missing library for {img_path}: {e}")
            except Exception as e:
                logger.error(f"Failed to load {img_path}: {e}")
        
        if pixmap:
            # Add pixmap and center it in the scene
            pixmap_item = self.scene.addPixmap(pixmap)
            
            # Set scene rect to match the pixmap size
            self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
            
            # Fit the view to show the entire scene
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
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
            logger.debug(f"Added clickable region for {component_id} at ({x}, {y}, {w}, {h})")
    
    def _handle_commit(self):
        """Handle Y/N commit input"""
        response = self.commit_input.text().upper()
        self.commit_input.clear()
        
        if response == 'Y':
            if self.pending_changes:
                # Save all pending changes
                import yaml
                config_file = os.path.join("config", "core_components.yaml")
                
                # Load existing config
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f) or {}
                else:
                    config = {}
                
                # Update with pending changes
                config.update(self.pending_changes)
                
                # Save configuration
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                
                self.commit_label.setText(f"✓ Committed {len(self.pending_changes)} module(s)")
                self.commit_label.setStyleSheet("""
                    QLabel {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        color: #4CAF50;
                        padding: 5px;
                        background: #1a1a1a;
                    }
                """)
                self.pending_changes = {}
                
                # Reset after 2 seconds
                from PySide6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: self.commit_label.setText("commit_to_modules? (Y/N)"))
                QTimer.singleShot(2000, lambda: self.commit_label.setStyleSheet("""
                    QLabel {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        color: #64B5F6;
                        padding: 5px;
                        background: #1a1a1a;
                    }
                """))
            else:
                self.commit_label.setText("⚠ No pending changes")
                self.commit_label.setStyleSheet("""
                    QLabel {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        color: #FFA726;
                        padding: 5px;
                        background: #1a1a1a;
                    }
                """)
                from PySide6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: self.commit_label.setText("commit_to_modules? (Y/N)"))
                QTimer.singleShot(2000, lambda: self.commit_label.setStyleSheet("""
                    QLabel {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        color: #64B5F6;
                        padding: 5px;
                        background: #1a1a1a;
                    }
                """))
        elif response == 'N':
            if self.pending_changes:
                count = len(self.pending_changes)
                self.pending_changes = {}
                self.commit_label.setText(f"✗ Discarded {count} change(s)")
                self.commit_label.setStyleSheet("""
                    QLabel {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        color: #EF5350;
                        padding: 5px;
                        background: #1a1a1a;
                    }
                """)
                from PySide6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: self.commit_label.setText("commit_to_modules? (Y/N)"))
                QTimer.singleShot(2000, lambda: self.commit_label.setStyleSheet("""
                    QLabel {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        color: #64B5F6;
                        padding: 5px;
                        background: #1a1a1a;
                    }
                """))
            else:
                self.commit_label.setText("⚠ No pending changes")
                self.commit_label.setStyleSheet("""
                    QLabel {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        color: #FFA726;
                        padding: 5px;
                        background: #1a1a1a;
                    }
                """)
                from PySide6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: self.commit_label.setText("commit_to_modules? (Y/N)"))
                QTimer.singleShot(2000, lambda: self.commit_label.setStyleSheet("""
                    QLabel {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        color: #64B5F6;
                        padding: 5px;
                        background: #1a1a1a;
                    }
                """))
    
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
        logger.info(f"Selected {component_type}: {file_path}")
        
        # Add to pending changes
        self.pending_changes[component_type] = {
            "path": file_path,
            "enabled": True
        }
        
        # Update commit prompt
        self.commit_label.setText(f"commit_to_modules? (Y/N) [{len(self.pending_changes)} pending]")
        self.commit_label.setStyleSheet("""
            QLabel {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                color: #FFA726;
                padding: 5px;
                background: #1a1a1a;
            }
        """)
