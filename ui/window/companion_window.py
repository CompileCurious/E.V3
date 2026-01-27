"""
Transparent Companion Window
Frameless, always-on-top, click-through window with 3D character
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QScreen
from typing import Dict, Any, Optional
from loguru import logger

from ui.renderer import OpenGLRenderer
from ui.animations import AnimationController


class CompanionWindow(QMainWindow):
    """
    Main companion window
    - Transparent background
    - Frameless
    - Always on top
    - Click-through when idle
    - Anchored to bottom-right above taskbar
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        self.config = config
        self.is_click_through = True
        self.current_state = "idle"
        
        # Setup window properties
        self._setup_window()
        
        # Create UI
        self._create_ui()
        
        # Position window
        self._position_window()
        
        logger.info("Companion window initialized")
    
    def _setup_window(self):
        """Setup window flags and properties"""
        # Frameless window
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |  # Don't show in taskbar
            Qt.WindowTransparentForInput  # Click-through initially
        )
        
        # Transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        # Window size
        ui_config = self.config.get("ui", {}).get("window", {})
        width = ui_config.get("width", 400)
        height = ui_config.get("height", 600)
        self.setFixedSize(width, height)
        
        # Window opacity
        opacity = ui_config.get("opacity", 0.95)
        self.setWindowOpacity(opacity)
        
        self.setWindowTitle("E.V3 Companion")
    
    def _create_ui(self):
        """Create UI elements"""
        # Central widget
        central = QWidget()
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 3D Renderer
        self.renderer = OpenGLRenderer(config=self.config)
        layout.addWidget(self.renderer, stretch=1)
        
        # Text overlay (for messages)
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("""
            QLabel {
                color: white;
                background: rgba(0, 0, 0, 150);
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.hide()
        layout.addWidget(self.message_label)
        
        # Animation controller
        if self.renderer.model:
            self.animation_controller = AnimationController(
                self.renderer.model,
                self.config
            )
            
            # Update animations
            self.anim_timer = QTimer(self)
            self.anim_timer.timeout.connect(self._update_animations)
            self.anim_timer.start(16)  # ~60 FPS
    
    def _position_window(self):
        """Position window at bottom-right above taskbar"""
        ui_config = self.config.get("ui", {}).get("window", {})
        
        # Get screen geometry
        screen = QScreen.availableGeometry(self.screen())
        
        # Calculate position
        offset_x = ui_config.get("offset_x", 20)
        offset_y = ui_config.get("offset_y", 20)
        
        x = screen.right() - self.width() - offset_x
        y = screen.bottom() - self.height() - offset_y
        
        self.move(x, y)
        logger.info(f"Window positioned at ({x}, {y})")
    
    def _update_animations(self):
        """Update character animations"""
        if hasattr(self, 'animation_controller'):
            self.animation_controller.update(0.016)  # ~60 FPS
    
    def set_state(self, state: str, message: str = "", priority: int = 0):
        """
        Update companion state
        
        States: idle, scanning, alert, reminder
        """
        self.current_state = state
        
        # Update animation state
        if hasattr(self, 'animation_controller'):
            self.animation_controller.set_state(state)
        
        # Update message
        if message:
            self.show_message(message)
        else:
            self.hide_message()
        
        # Update click-through based on state
        if state in ["alert", "reminder"]:
            self.enable_interaction()
        else:
            click_through = self.config.get("ui", {}).get("window", {}).get("click_through_when_idle", True)
            if click_through:
                self.disable_interaction()
        
        # Apply visual effects
        self._apply_state_effects(state, priority)
        
        logger.info(f"State changed to: {state}")
    
    def _apply_state_effects(self, state: str, priority: int):
        """Apply visual effects based on state"""
        if state == "alert":
            # Glow effect for alerts
            glow_config = self.config.get("ui", {}).get("animations", {}).get("glow", {})
            if glow_config.get("enabled", True):
                color = glow_config.get("color", [0.3, 0.6, 1.0])
                intensity = glow_config.get("intensity", 0.5)
                
                # Higher priority = more intense glow
                intensity *= (priority + 1) * 0.3
                
                self.renderer.apply_glow_effect(intensity, tuple(color))
        
        elif state == "reminder":
            # Gentle glow for reminders
            self.renderer.apply_glow_effect(0.3, (0.5, 0.8, 0.3))
    
    def show_message(self, message: str):
        """Show text message"""
        self.message_label.setText(message)
        self.message_label.show()
        
        # Auto-hide after some time (for non-critical messages)
        if self.current_state not in ["alert", "reminder"]:
            QTimer.singleShot(5000, self.hide_message)
    
    def hide_message(self):
        """Hide text message"""
        self.message_label.hide()
    
    def enable_interaction(self):
        """Enable window interaction (disable click-through)"""
        if self.is_click_through:
            self.is_click_through = False
            flags = self.windowFlags()
            flags &= ~Qt.WindowTransparentForInput
            self.setWindowFlags(flags)
            self.show()  # Need to show again after changing flags
            logger.debug("Interaction enabled")
    
    def disable_interaction(self):
        """Disable interaction (enable click-through)"""
        if not self.is_click_through:
            self.is_click_through = True
            flags = self.windowFlags()
            flags |= Qt.WindowTransparentForInput
            self.setWindowFlags(flags)
            self.show()
            logger.debug("Click-through enabled")
    
    def mousePressEvent(self, event):
        """Handle mouse press (for dragging window)"""
        if event.button() == Qt.LeftButton and not self.is_click_through:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move (drag window)"""
        if event.buttons() == Qt.LeftButton and not self.is_click_through:
            if hasattr(self, 'drag_position'):
                self.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click (dismiss or interact)"""
        if not self.is_click_through:
            if self.current_state in ["alert", "reminder"]:
                # Dismiss notification
                self.set_state("idle")
                # Notify service (would send IPC message)
                logger.info("Notification dismissed by user")
