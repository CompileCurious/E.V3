"""
Modules Configuration Window
Interactive robot frame for selecting models and components
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QFileDialog, QMessageBox, QGraphicsView, 
                                QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem, QLineEdit,
                                QGroupBox, QCheckBox, QPushButton, QComboBox)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFont, QPainterPath
from PySide6.QtSvg import QSvgRenderer
from loguru import logger
import os


class SlidingToggle(QWidget):
    """iOS-style sliding toggle switch"""
    toggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 24)
        self._checked = False
        self._circle_position = 2
        
        # Animation for smooth sliding
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(200)
        
        self.setCursor(Qt.PointingHandCursor)
    
    @Property(int)
    def circle_position(self):
        return self._circle_position
    
    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()
    
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._animate_toggle()
    
    def isChecked(self):
        return self._checked
    
    def _animate_toggle(self):
        start_pos = 2 if not self._checked else 28
        end_pos = 28 if self._checked else 2
        
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.start()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._animate_toggle()
            self.toggled.emit(self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background track
        if self._checked:
            track_color = QColor(100, 181, 246)  # Blue when on
        else:
            track_color = QColor(60, 60, 60)  # Dark gray when off
        
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 50, 24, 12, 12)
        
        # Draw sliding circle
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(self._circle_position, 2, 20, 20)


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
        self.setFixedSize(620, 700)
        
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
        
        # File picker buttons section
        self._add_file_pickers(layout)
        
        # Bottom section: robot image on left, extended toggles on right
        bottom_layout = QHBoxLayout()
        
        # Graphics view for robot frame (left side, smaller)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet("background: #2b2b2b; border: 2px solid #444;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setFixedSize(280, 350)  # Narrower to avoid overlapping toggles
        bottom_layout.addWidget(self.view)
        
        # Draw robot frame
        self._draw_robot_frame()
        
        # Right side spacer for future toggles extension
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)
        
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
    
    def _add_file_pickers(self, layout):
        """Add file picker buttons and module toggles in two-column layout"""
        
        # Create horizontal layout for two columns
        columns_layout = QHBoxLayout()
        
        # Left column - Model selection
        left_column = QVBoxLayout()
        
        # LLM Configuration Group
        llm_group = QGroupBox("🧠 AI Brain (LLM)")
        llm_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #64B5F6;
                border: 2px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        llm_layout = QVBoxLayout(llm_group)
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("color: #aaa; font-weight: normal;")
        self.llm_mode_combo = QComboBox()
        self.llm_mode_combo.addItems(["Fast (Phi-3)", "Deep Thinking (Mistral)"])
        self.llm_mode_combo.setStyleSheet("""
            QComboBox {
                background: #333;
                color: #64B5F6;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        self.llm_mode_combo.currentIndexChanged.connect(self._on_llm_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.llm_mode_combo)
        mode_layout.addStretch()
        llm_layout.addLayout(mode_layout)
        
        # Fast model picker
        fast_btn = QPushButton("📁 Select Fast Model (Phi-3)")
        fast_btn.setStyleSheet(self._button_style())
        fast_btn.clicked.connect(lambda: self._select_model("fast"))
        llm_layout.addWidget(fast_btn)
        
        # Deep model picker
        deep_btn = QPushButton("📁 Select Deep Model (Mistral)")
        deep_btn.setStyleSheet(self._button_style())
        deep_btn.clicked.connect(lambda: self._select_model("deep"))
        llm_layout.addWidget(deep_btn)
        
        left_column.addWidget(llm_group)
        
        # Character Model Group
        char_group = QGroupBox("💫 3D Character Model")
        char_group.setStyleSheet(llm_group.styleSheet())
        char_layout = QVBoxLayout(char_group)
        
        char_btn = QPushButton("📁 Select Character Model (.vrm/.glb)")
        char_btn.setStyleSheet(self._button_style())
        char_btn.clicked.connect(lambda: self._select_model("character"))
        char_layout.addWidget(char_btn)
        
        left_column.addWidget(char_group)
        left_column.addStretch()
        
        # Right column - Speech, Hearing, and Module toggles
        right_column = QVBoxLayout()
        
        # Speech Group
        speech_group = QGroupBox("🗣️ Speech (TTS)")
        speech_group.setStyleSheet(llm_group.styleSheet())
        speech_layout = QVBoxLayout(speech_group)
        
        speech_btn = QPushButton("📁 Select Voice Model")
        speech_btn.setStyleSheet(self._button_style())
        speech_btn.clicked.connect(lambda: self._select_model("speech"))
        speech_layout.addWidget(speech_btn)
        
        right_column.addWidget(speech_group)
        
        # Hearing Group
        hearing_group = QGroupBox("👂 Hearing (STT)")
        hearing_group.setStyleSheet(llm_group.styleSheet())
        hearing_layout = QVBoxLayout(hearing_group)
        
        hearing_btn = QPushButton("📁 Select Listening Model")
        hearing_btn.setStyleSheet(self._button_style())
        hearing_btn.clicked.connect(lambda: self._select_model("hearing"))
        hearing_layout.addWidget(hearing_btn)
        
        right_column.addWidget(hearing_group)
        
        # Module Toggles below
        self._add_module_toggles(right_column)
        right_column.addStretch()
        
        # Add columns to horizontal layout
        columns_layout.addLayout(left_column, 60)  # 60% width for left
        columns_layout.addLayout(right_column, 40)  # 40% width for right
        
        layout.addLayout(columns_layout)
    
    def _add_module_toggles(self, layout):
        """Add module enable/disable toggles"""
        
        modules_group = QGroupBox("⚙️ Module Toggles")
        modules_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #64B5F6;
                border: 2px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        modules_layout = QVBoxLayout(modules_group)
        
        # System Status Toggle with sliding switch
        toggle_row = QHBoxLayout()
        
        system_label = QLabel("📊 System Status (Time, CPU, RAM, Network)")
        system_label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-weight: normal;
            }
        """)
        
        self.system_status_toggle = SlidingToggle()
        self.system_status_toggle.setChecked(False)
        self.system_status_toggle.toggled.connect(self._on_system_status_changed)
        
        toggle_row.addWidget(system_label)
        toggle_row.addStretch()
        toggle_row.addWidget(self.system_status_toggle)
        
        modules_layout.addLayout(toggle_row)
        
        layout.addWidget(modules_group)
    
    def _on_system_status_changed(self, enabled):
        """Handle system status toggle"""
        self.pending_changes["system_module_enabled"] = enabled
        self.pending_changes["system_module_enabled"] = enabled
        logger.info(f"System module {'enabled' if enabled else 'disabled'}")
    
    def _button_style(self):
        """Return consistent button styling"""
        return """
            QPushButton {
                background: #2a2a2a;
                color: #64B5F6;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 3px;
                text-align: left;
            }
            QPushButton:hover {
                background: #3a3a3a;
                border: 1px solid #64B5F6;
            }
            QPushButton:pressed {
                background: #1a1a1a;
            }
        """
    
    def _on_llm_mode_changed(self, index):
        """Handle LLM mode change"""
        mode = "fast" if index == 0 else "deep"
        self.pending_changes["llm_mode"] = mode
        logger.info(f"LLM mode changed to: {mode}")
    
    def _select_model(self, model_type):
        """Open file picker for model selection"""
        if model_type == "fast":
            title = "Select Fast LLM Model (Phi-3)"
            folder = "models/llm"
            filter_str = "GGUF Models (*.gguf);;All Files (*.*)"
            config_key = "fast_model"
        elif model_type == "deep":
            title = "Select Deep LLM Model (Mistral)"
            folder = "models/llm"
            filter_str = "GGUF Models (*.gguf);;All Files (*.*)"
            config_key = "deep_model"
        elif model_type == "character":
            title = "Select 3D Character Model"
            folder = "models/character"
            filter_str = "3D Models (*.vrm *.glb *.gltf);;All Files (*.*)"
            config_key = "character_model"
        elif model_type == "speech":
            title = "Select Speech Voice Model (TTS)"
            folder = "models/speech"
            filter_str = "Voice Models (*.onnx *.pth *.bin);;All Files (*.*)"
            config_key = "speech_model"
        elif model_type == "hearing":
            title = "Select Listening Model (STT)"
            folder = "models/speech"
            filter_str = "Speech Models (*.onnx *.pth *.bin);;All Files (*.*)"
            config_key = "hearing_model"
        else:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            folder,
            filter_str
        )
        
        if file_path:
            # Store just the filename
            import os
            filename = os.path.basename(file_path)
            self.pending_changes[config_key] = filename
            logger.info(f"Selected {model_type} model: {filename}")
            QMessageBox.information(
                self,
                "Model Selected",
                f"{model_type.title()} model selected:\n{filename}\n\nType 'Y' in commit field to apply changes."
            )
    
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
            
            # Scale down to 75% and shift up to show head
            pixmap_item.setScale(0.75)
            pixmap_item.setPos(-30, -120)
            
            # Set scene rect to accommodate the scaled and shifted image
            scaled_width = pixmap.width() * 0.75
            scaled_height = pixmap.height() * 0.75
            self.scene.setSceneRect(-30, -120, scaled_width, scaled_height)
            
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
                # Save to main config.yaml
                import yaml
                config_file = "config/config.yaml"
                
                try:
                    # Load existing config
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    # Update LLM settings
                    if "llm_mode" in self.pending_changes:
                        config["llm"]["mode"] = self.pending_changes["llm_mode"]
                    
                    if "fast_model" in self.pending_changes:
                        config["llm"]["local"]["fast_model"] = self.pending_changes["fast_model"]
                    
                    if "deep_model" in self.pending_changes:
                        config["llm"]["local"]["deep_model"] = self.pending_changes["deep_model"]
                    
                    if "character_model" in self.pending_changes:
                        config["ui"]["model"]["model_path"] = f"models/character/{self.pending_changes['character_model']}"
                    
                    # Update module settings
                    if "system_module_enabled" in self.pending_changes:
                        if "modules" not in config:
                            config["modules"] = {}
                        config["modules"]["system_enabled"] = self.pending_changes["system_module_enabled"]
                    
                    # Save updated config
                    with open(config_file, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                    
                    self.commit_label.setText(f"✓ Committed {len(self.pending_changes)} change(s)")
                    self.commit_label.setStyleSheet("""
                        QLabel {
                            font-family: 'Consolas', 'Courier New', monospace;
                            font-size: 11px;
                            color: #4CAF50;
                            padding: 5px;
                            background: #1a1a1a;
                        }
                    """)
                    
                    # Show success message
                    QMessageBox.information(
                        self,
                        "Configuration Saved",
                        f"Changes saved to {config_file}\n\nRestart E.V3 to apply changes."
                    )
                    
                    # Clear pending changes
                    self.pending_changes = {}
                    
                    # Reset label after delay
                    QTimer.singleShot(3000, lambda: self.commit_label.setText("commit_to_modules? (Y/N)"))
                    QTimer.singleShot(3000, lambda: self.commit_label.setStyleSheet("""
                        QLabel {
                            font-family: 'Consolas', 'Courier New', monospace;
                            font-size: 11px;
                            color: #64B5F6;
                            padding: 5px;
                            background: #1a1a1a;
                        }
                    """))
                    
                    logger.info("Module configuration committed successfully")
                
                except Exception as e:
                    logger.error(f"Failed to save configuration: {e}")
                    QMessageBox.critical(
                        self,
                        "Save Failed",
                        f"Failed to save configuration:\n{str(e)}"
                    )
            else:
                self.commit_label.setText("⚠ No pending changes")
                QTimer.singleShot(2000, lambda: self.commit_label.setText("commit_to_modules? (Y/N)"))
        
        elif response == 'N':
            # Cancel pending changes
            if self.pending_changes:
                self.commit_label.setText(f"✗ Cancelled {len(self.pending_changes)} change(s)")
                self.commit_label.setStyleSheet("""
                    QLabel {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 11px;
                        color: #FF5252;
                        padding: 5px;
                        background: #1a1a1a;
                    }
                """)
                self.pending_changes = {}
                
                # Reset after 2 seconds
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
                QTimer.singleShot(2000, lambda: self.commit_label.setText("commit_to_modules? (Y/N)"))
    
    def _handle_component_click(self, component_type: str):
        """Handle click on robot frame component (not implemented yet)"""
        logger.info(f"Component clicked: {component_type}")
        # Will implement when clickable regions are working
    
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
