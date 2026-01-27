"""
Transparent Shell Window
Frameless, always-on-top window with 3D character and system tray control
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QSystemTrayIcon, QMenu, QApplication
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QScreen, QIcon, QAction
from typing import Dict, Any, Optional
from loguru import logger
import sys

from ui.renderer import OpenGLRenderer
from ui.animations import AnimationController


class CompanionWindow(QMainWindow):
    """
    Main shell window
    - Transparent background
    - Frameless
    - Always on top
    - System tray control
    - Anchored to bottom-right above taskbar
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        self.config = config
        self.is_click_through = False  # Start non-click-through so it's controllable
        self.current_state = "idle"
        
        # Setup window properties
        self._setup_window()
        
        # Create UI
        self._create_ui()
        
        # Setup system tray
        self._setup_tray_icon()
        
        # Position window
        self._position_window()
        
        logger.info("Shell window initialized")
    
    def _setup_window(self):
        """Setup window flags and properties"""
        # Frameless window
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # Don't show in taskbar
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
        
        self.setWindowTitle("E.V3 Shell")
    
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
    
    def _setup_tray_icon(self):
        """Setup system tray icon with menu"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create icon (use default for now)
        from PySide6.QtWidgets import QStyle
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        # Create menu
        tray_menu = QMenu()
        
        # Show/Hide action
        self.show_hide_action = QAction("Hide Shell", self)
        self.show_hide_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(self.show_hide_action)
        
        tray_menu.addSeparator()
        
        # Stop Daemon action
        stop_daemon_action = QAction("Stop Daemon", self)
        stop_daemon_action.triggered.connect(self.stop_daemon)
        tray_menu.addAction(stop_daemon_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("E.V3 Shell")
        
        # Double-click to show/hide
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        self.tray_icon.show()
        logger.info("System tray icon created")
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_visibility()
    
    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
            self.show_hide_action.setText("Show Shell")
            logger.info("Shell hidden")
        else:
            self.show()
            self.show_hide_action.setText("Hide Shell")
            logger.info("Shell shown")
    
    def stop_daemon(self):
        """Stop the daemon service"""
        import subprocess
        try:
            # Try to stop EV3Service.exe
            subprocess.run(["taskkill", "/F", "/IM", "EV3Daemon.exe"], 
                          capture_output=True)
            self.tray_icon.showMessage(
                "E.V3",
                "Daemon stopped",
                QSystemTrayIcon.Information,
                2000
            )
            logger.info("Daemon stop requested")
        except Exception as e:
            logger.error(f"Failed to stop daemon: {e}")
    
    def quit_application(self):
        """Quit the application"""
        logger.info("Quitting application")
        self.tray_icon.hide()
        QApplication.instance().quit()
    
    def closeEvent(self, event):
        """Handle window close - hide to tray instead"""
        event.ignore()
        self.hide()
        self.show_hide_action.setText("Show Shell")
        self.tray_icon.showMessage(
            "E.V3",
            "Shell hidden to system tray",
            QSystemTrayIcon.Information,
            2000
        )
    
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
