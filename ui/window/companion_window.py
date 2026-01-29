"""
Transparent Shell Window
Frameless, always-on-top window with 3D character and system tray control
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSystemTrayIcon, QMenu, QApplication, QLineEdit, QPushButton,
                               QFrame, QDialog)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QScreen, QIcon, QAction, QKeySequence, QShortcut
from typing import Dict, Any, Optional
from loguru import logger
import sys
import keyboard

from ui.renderer import OpenGLRenderer
from ui.animations import AnimationController
from ui.window.core_window import ModulesWindow


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
        self.chat_window = None
        self.hotkey_enabled = True
        self.hotkey_combination = "win+c"  # Default hotkey
        
        # Setup window properties
        self._setup_window()
        
        # Create UI
        self._create_ui()
        
        # Setup system tray
        self._setup_tray_icon()
        
        # Position window
        self._position_window()
        
        # Setup global hotkey
        self._setup_global_hotkey()
        
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
        
        # Don't set window opacity - we want full opacity for the window
        # Transparency is handled by OpenGL rendering
        
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
        
        # Create main menu
        tray_menu = QMenu()
        
        # === SHELL SUBMENU ===
        shell_menu = QMenu("Shell", tray_menu)
        
        # Show/Hide action
        self.show_hide_action = QAction("Hide Shell", self)
        self.show_hide_action.triggered.connect(self.toggle_visibility)
        shell_menu.addAction(self.show_hide_action)
        
        shell_menu.addSeparator()
        
        # 3D Model Controls submenu
        model_menu = QMenu("3D Model Controls", shell_menu)
        
        # Zoom controls
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        model_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        model_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.triggered.connect(self.reset_zoom)
        model_menu.addAction(reset_zoom_action)
        
        model_menu.addSeparator()
        
        # Position controls
        move_up_action = QAction("Move Up", self)
        move_up_action.triggered.connect(self.move_model_up)
        model_menu.addAction(move_up_action)
        
        move_down_action = QAction("Move Down", self)
        move_down_action.triggered.connect(self.move_model_down)
        model_menu.addAction(move_down_action)
        
        move_left_action = QAction("Move Left", self)
        move_left_action.triggered.connect(self.move_model_left)
        model_menu.addAction(move_left_action)
        
        move_right_action = QAction("Move Right", self)
        move_right_action.triggered.connect(self.move_model_right)
        model_menu.addAction(move_right_action)
        
        reset_position_action = QAction("Reset Position", self)
        reset_position_action.triggered.connect(self.reset_position)
        model_menu.addAction(reset_position_action)
        
        shell_menu.addMenu(model_menu)
        
        shell_menu.addSeparator()
        
        # Input Mode submenu
        input_menu = QMenu("Input Mode", shell_menu)
        
        self.input_text_action = QAction("Text", self, checkable=True)
        self.input_text_action.setChecked(True)
        self.input_text_action.triggered.connect(lambda: self.set_input_mode("text"))
        input_menu.addAction(self.input_text_action)
        
        self.input_voice_action = QAction("Voice (Coming Soon)", self, checkable=True)
        self.input_voice_action.setEnabled(False)
        self.input_voice_action.triggered.connect(lambda: self.set_input_mode("voice"))
        input_menu.addAction(self.input_voice_action)
        
        shell_menu.addMenu(input_menu)
        
        # Output Mode submenu
        output_menu = QMenu("Output Mode", shell_menu)
        
        self.output_text_action = QAction("Text", self, checkable=True)
        self.output_text_action.setChecked(True)
        self.output_text_action.triggered.connect(lambda: self.set_output_mode("text"))
        output_menu.addAction(self.output_text_action)
        
        self.output_voice_action = QAction("Voice (Coming Soon)", self, checkable=True)
        self.output_voice_action.setEnabled(False)
        self.output_voice_action.triggered.connect(lambda: self.set_output_mode("voice"))
        output_menu.addAction(self.output_voice_action)
        
        shell_menu.addMenu(output_menu)
        
        shell_menu.addSeparator()
        
        # Hotkey Configuration
        hotkey_menu = QMenu("Summon Hotkey", shell_menu)
        
        self.hotkey_enabled_action = QAction("Enable Hotkey", self, checkable=True)
        self.hotkey_enabled_action.setChecked(True)
        self.hotkey_enabled_action.triggered.connect(self.toggle_hotkey)
        hotkey_menu.addAction(self.hotkey_enabled_action)
        
        hotkey_menu.addSeparator()
        
        hotkey_info_action = QAction(f"Current: {self.hotkey_combination.upper()}", self)
        hotkey_info_action.setEnabled(False)
        hotkey_menu.addAction(hotkey_info_action)
        
        shell_menu.addMenu(hotkey_menu)
        
        shell_menu.addSeparator()
        
        # Open Chat action
        open_chat_action = QAction("Open Chat Window", self)
        open_chat_action.triggered.connect(self.open_chat_window)
        shell_menu.addAction(open_chat_action)
        
        tray_menu.addMenu(shell_menu)
        
        # === KERNEL SUBMENU ===
        daemon_menu = QMenu("Kernel", tray_menu)
        
        # Stop Kernel action
        stop_daemon_action = QAction("Stop Kernel", self)
        stop_daemon_action.triggered.connect(self.stop_kernel)
        daemon_menu.addAction(stop_daemon_action)
        
        # Restart Kernel action
        restart_daemon_action = QAction("Restart Kernel", self)
        restart_daemon_action.triggered.connect(self.restart_kernel)
        daemon_menu.addAction(restart_daemon_action)
        
        daemon_menu.addSeparator()
        
        # Permissions submenu
        permissions_menu = QMenu("Permissions", daemon_menu)
        
        # File System Access
        fs_menu = QMenu("File System Access", permissions_menu)
        
        self.fs_none_action = QAction("None (Read-Only Config)", self, checkable=True)
        self.fs_none_action.triggered.connect(lambda: self.set_filesystem_permission("none"))
        fs_menu.addAction(self.fs_none_action)
        
        self.fs_scoped_action = QAction("Scoped (Selected Folders)", self, checkable=True)
        self.fs_scoped_action.setChecked(True)
        self.fs_scoped_action.triggered.connect(lambda: self.set_filesystem_permission("scoped"))
        fs_menu.addAction(self.fs_scoped_action)
        
        self.fs_full_action = QAction("Full Access", self, checkable=True)
        self.fs_full_action.triggered.connect(lambda: self.set_filesystem_permission("full"))
        fs_menu.addAction(self.fs_full_action)
        
        fs_menu.addSeparator()
        
        manage_folders_action = QAction("Manage Allowed Folders...", self)
        manage_folders_action.triggered.connect(self.manage_allowed_folders)
        fs_menu.addAction(manage_folders_action)
        
        permissions_menu.addMenu(fs_menu)
        
        # Network Access
        network_menu = QMenu("Network Access", permissions_menu)
        
        self.net_none_action = QAction("Disabled", self, checkable=True)
        self.net_none_action.triggered.connect(lambda: self.set_network_permission("none"))
        network_menu.addAction(self.net_none_action)
        
        self.net_local_action = QAction("Local Only", self, checkable=True)
        self.net_local_action.setChecked(True)
        self.net_local_action.triggered.connect(lambda: self.set_network_permission("local"))
        network_menu.addAction(self.net_local_action)
        
        self.net_full_action = QAction("Full Internet", self, checkable=True)
        self.net_full_action.triggered.connect(lambda: self.set_network_permission("full"))
        network_menu.addAction(self.net_full_action)
        
        permissions_menu.addMenu(network_menu)
        
        # System Information
        sysinfo_menu = QMenu("System Information", permissions_menu)
        
        self.sysinfo_basic_action = QAction("Basic (CPU, Memory)", self, checkable=True)
        self.sysinfo_basic_action.setChecked(True)
        self.sysinfo_basic_action.triggered.connect(lambda: self.set_sysinfo_permission("basic"))
        sysinfo_menu.addAction(self.sysinfo_basic_action)
        
        self.sysinfo_extended_action = QAction("Extended (+ Processes)", self, checkable=True)
        self.sysinfo_extended_action.triggered.connect(lambda: self.set_sysinfo_permission("extended"))
        sysinfo_menu.addAction(self.sysinfo_extended_action)
        
        self.sysinfo_full_action = QAction("Full (+ Hardware IDs)", self, checkable=True)
        self.sysinfo_full_action.triggered.connect(lambda: self.set_sysinfo_permission("full"))
        sysinfo_menu.addAction(self.sysinfo_full_action)
        
        permissions_menu.addMenu(sysinfo_menu)
        
        # Calendar Access
        calendar_menu = QMenu("Calendar Access", permissions_menu)
        
        self.cal_none_action = QAction("Disabled", self, checkable=True)
        self.cal_none_action.triggered.connect(lambda: self.set_calendar_permission("none"))
        calendar_menu.addAction(self.cal_none_action)
        
        self.cal_read_action = QAction("Read-Only", self, checkable=True)
        self.cal_read_action.setChecked(True)
        self.cal_read_action.triggered.connect(lambda: self.set_calendar_permission("read"))
        calendar_menu.addAction(self.cal_read_action)
        
        self.cal_full_action = QAction("Read & Write", self, checkable=True)
        self.cal_full_action.triggered.connect(lambda: self.set_calendar_permission("full"))
        calendar_menu.addAction(self.cal_full_action)
        
        permissions_menu.addMenu(calendar_menu)
        
        # LLM Data Usage
        llm_menu = QMenu("LLM Data Usage", permissions_menu)
        
        self.llm_local_action = QAction("Local Only (No External API)", self, checkable=True)
        self.llm_local_action.setChecked(True)
        self.llm_local_action.triggered.connect(lambda: self.set_llm_permission("local"))
        llm_menu.addAction(self.llm_local_action)
        
        self.llm_external_action = QAction("Allow External API (Fallback)", self, checkable=True)
        self.llm_external_action.triggered.connect(lambda: self.set_llm_permission("external"))
        llm_menu.addAction(self.llm_external_action)
        
        llm_menu.addSeparator()
        
        self.llm_log_action = QAction("Log LLM Queries", self, checkable=True)
        self.llm_log_action.setChecked(False)
        self.llm_log_action.triggered.connect(self.toggle_llm_logging)
        llm_menu.addAction(self.llm_log_action)
        
        permissions_menu.addMenu(llm_menu)
        
        permissions_menu.addSeparator()
        
        # Reset to defaults
        reset_permissions_action = QAction("Reset to Defaults", self)
        reset_permissions_action.triggered.connect(self.reset_permissions)
        permissions_menu.addAction(reset_permissions_action)
        
        daemon_menu.addMenu(permissions_menu)
        
        tray_menu.addMenu(daemon_menu)
        
        # === MODULES MENU ===
        core_action = QAction("Modules", self)
        core_action.triggered.connect(self.open_modules_window)
        tray_menu.addAction(core_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("E.V3 Shell")
        
        # Double-click to show/hide
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Store current modes
        self.input_mode = "text"
        self.output_mode = "text"
        
        # Store model transform values
        self.model_scale = 1.0
        self.model_position = [0.0, 0.0, 0.0]
        
        # Store permission settings (default to secure)
        self.permissions = {
            "filesystem": "scoped",
            "network": "local",
            "sysinfo": "basic",
            "calendar": "read",
            "llm": "local",
            "llm_logging": False,
            "allowed_folders": []
        }
        
        self._load_permissions()
        
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
    
    def stop_kernel(self):
        """Stop the kernel service"""
        import subprocess
        try:
            # Try to stop EV3Kernel.exe
            subprocess.run(["taskkill", "/F", "/IM", "EV3Kernel.exe"], 
                          capture_output=True)
            self.tray_icon.showMessage(
                "E.V3",
                "Kernel stopped",
                QSystemTrayIcon.Information,
                2000
            )
            logger.info("Kernel stop requested")
        except Exception as e:
            logger.error(f"Failed to stop kernel: {e}")
    
    def restart_kernel(self):
        """Restart the kernel service"""
        logger.info("Kernel restart requested")
        self.tray_icon.showMessage(
            "E.V3",
            "Kernel restart not yet implemented",
            QSystemTrayIcon.Information,
            2000
        )
    
    def zoom_in(self):
        """Zoom in on 3D model"""
        self.model_scale *= 1.1
        if hasattr(self.renderer, 'set_model_scale'):
            self.renderer.set_model_scale(self.model_scale)
        logger.info(f"Model zoomed in: scale={self.model_scale:.2f}")
    
    def zoom_out(self):
        """Zoom out on 3D model"""
        self.model_scale *= 0.9
        if hasattr(self.renderer, 'set_model_scale'):
            self.renderer.set_model_scale(self.model_scale)
        logger.info(f"Model zoomed out: scale={self.model_scale:.2f}")
    
    def reset_zoom(self):
        """Reset model zoom"""
        self.model_scale = 1.0
        if hasattr(self.renderer, 'set_model_scale'):
            self.renderer.set_model_scale(self.model_scale)
        logger.info("Model zoom reset")
    
    def move_model_up(self):
        """Move model up"""
        self.model_position[1] += 0.1
        if hasattr(self.renderer, 'set_model_position'):
            self.renderer.set_model_position(*self.model_position)
        logger.info(f"Model moved up: position={self.model_position}")
    
    def move_model_down(self):
        """Move model down"""
        self.model_position[1] -= 0.1
        if hasattr(self.renderer, 'set_model_position'):
            self.renderer.set_model_position(*self.model_position)
        logger.info(f"Model moved down: position={self.model_position}")
    
    def move_model_left(self):
        """Move model left"""
        self.model_position[0] -= 0.1
        if hasattr(self.renderer, 'set_model_position'):
            self.renderer.set_model_position(*self.model_position)
        logger.info(f"Model moved left: position={self.model_position}")
    
    def move_model_right(self):
        """Move model right"""
        self.model_position[0] += 0.1
        if hasattr(self.renderer, 'set_model_position'):
            self.renderer.set_model_position(*self.model_position)
        logger.info(f"Model moved right: position={self.model_position}")
    
    def reset_position(self):
        """Reset model position"""
        self.model_position = [0.0, 0.0, 0.0]
        if hasattr(self.renderer, 'set_model_position'):
            self.renderer.set_model_position(*self.model_position)
        logger.info("Model position reset")
    
    def set_input_mode(self, mode: str):
        """Set input mode (text or voice)"""
        self.input_mode = mode
        
        # Update checkmarks
        self.input_text_action.setChecked(mode == "text")
        self.input_voice_action.setChecked(mode == "voice")
        
        logger.info(f"Input mode set to: {mode}")
        self.tray_icon.showMessage(
            "E.V3",
            f"Input mode: {mode}",
            QSystemTrayIcon.Information,
            2000
        )
    
    def set_output_mode(self, mode: str):
        """Set output mode (text or voice)"""
        self.output_mode = mode
        
        # Update checkmarks
        self.output_text_action.setChecked(mode == "text")
        self.output_voice_action.setChecked(mode == "voice")
        
        logger.info(f"Output mode set to: {mode}")
        self.tray_icon.showMessage(
            "E.V3",
            f"Output mode: {mode}",
            QSystemTrayIcon.Information,
            2000
        )
    
    # === PERMISSION MANAGEMENT METHODS ===
    
    def _load_permissions(self):
        """Load permissions from config file"""
        import os
        import yaml
        
        permissions_file = os.path.join("config", "permissions.yaml")
        if os.path.exists(permissions_file):
            try:
                with open(permissions_file, 'r') as f:
                    saved_perms = yaml.safe_load(f) or {}
                    self.permissions.update(saved_perms)
                logger.info("Permissions loaded from config")
            except Exception as e:
                logger.error(f"Failed to load permissions: {e}")
        
        # Update UI checkmarks based on loaded permissions
        self._update_permission_checkmarks()
    
    def _save_permissions(self):
        """Save permissions to config file"""
        import os
        import yaml
        
        os.makedirs("config", exist_ok=True)
        permissions_file = os.path.join("config", "permissions.yaml")
        
        try:
            with open(permissions_file, 'w') as f:
                yaml.dump(self.permissions, f, default_flow_style=False)
            logger.info("Permissions saved to config")
        except Exception as e:
            logger.error(f"Failed to save permissions: {e}")
    
    def _update_permission_checkmarks(self):
        """Update checkmarks in permission menus based on current settings"""
        # Filesystem
        self.fs_none_action.setChecked(self.permissions["filesystem"] == "none")
        self.fs_scoped_action.setChecked(self.permissions["filesystem"] == "scoped")
        self.fs_full_action.setChecked(self.permissions["filesystem"] == "full")
        
        # Network
        self.net_none_action.setChecked(self.permissions["network"] == "none")
        self.net_local_action.setChecked(self.permissions["network"] == "local")
        self.net_full_action.setChecked(self.permissions["network"] == "full")
        
        # System Info
        self.sysinfo_basic_action.setChecked(self.permissions["sysinfo"] == "basic")
        self.sysinfo_extended_action.setChecked(self.permissions["sysinfo"] == "extended")
        self.sysinfo_full_action.setChecked(self.permissions["sysinfo"] == "full")
        
        # Calendar
        self.cal_none_action.setChecked(self.permissions["calendar"] == "none")
        self.cal_read_action.setChecked(self.permissions["calendar"] == "read")
        self.cal_full_action.setChecked(self.permissions["calendar"] == "full")
        
        # LLM
        self.llm_local_action.setChecked(self.permissions["llm"] == "local")
        self.llm_external_action.setChecked(self.permissions["llm"] == "external")
        self.llm_log_action.setChecked(self.permissions.get("llm_logging", False))
    
    def set_filesystem_permission(self, level: str):
        """Set filesystem access level"""
        self.permissions["filesystem"] = level
        self._update_permission_checkmarks()
        self._save_permissions()
        
        logger.info(f"Filesystem permission set to: {level}")
        self.tray_icon.showMessage(
            "E.V3 Permissions",
            f"File system access: {level}",
            QSystemTrayIcon.Information,
            2000
        )
        
        # Notify kernel of permission change via IPC
        self._notify_kernel_permissions()
    
    def set_network_permission(self, level: str):
        """Set network access level"""
        self.permissions["network"] = level
        self._update_permission_checkmarks()
        self._save_permissions()
        
        logger.info(f"Network permission set to: {level}")
        self.tray_icon.showMessage(
            "E.V3 Permissions",
            f"Network access: {level}",
            QSystemTrayIcon.Information,
            2000
        )
        
        self._notify_kernel_permissions()
    
    def set_sysinfo_permission(self, level: str):
        """Set system information access level"""
        self.permissions["sysinfo"] = level
        self._update_permission_checkmarks()
        self._save_permissions()
        
        logger.info(f"System info permission set to: {level}")
        self.tray_icon.showMessage(
            "E.V3 Permissions",
            f"System info access: {level}",
            QSystemTrayIcon.Information,
            2000
        )
        
        self._notify_kernel_permissions()
    
    def set_calendar_permission(self, level: str):
        """Set calendar access level"""
        self.permissions["calendar"] = level
        self._update_permission_checkmarks()
        self._save_permissions()
        
        logger.info(f"Calendar permission set to: {level}")
        self.tray_icon.showMessage(
            "E.V3 Permissions",
            f"Calendar access: {level}",
            QSystemTrayIcon.Information,
            2000
        )
        
        self._notify_kernel_permissions()
    
    def set_llm_permission(self, level: str):
        """Set LLM data usage permission"""
        self.permissions["llm"] = level
        self._update_permission_checkmarks()
        self._save_permissions()
        
        logger.info(f"LLM permission set to: {level}")
        self.tray_icon.showMessage(
            "E.V3 Permissions",
            f"LLM mode: {level}",
            QSystemTrayIcon.Information,
            2000
        )
        
        self._notify_kernel_permissions()
    
    def toggle_llm_logging(self):
        """Toggle LLM query logging"""
        self.permissions["llm_logging"] = self.llm_log_action.isChecked()
        self._save_permissions()
        
        status = "enabled" if self.permissions["llm_logging"] else "disabled"
        logger.info(f"LLM logging {status}")
        self.tray_icon.showMessage(
            "E.V3 Permissions",
            f"LLM query logging: {status}",
            QSystemTrayIcon.Information,
            2000
        )
        
        self._notify_kernel_permissions()
    
    def manage_allowed_folders(self):
        """Open dialog to manage allowed folders for scoped access"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        
        if dialog.exec():
            selected = dialog.selectedFiles()
            if selected:
                folder = selected[0]
                if folder not in self.permissions["allowed_folders"]:
                    self.permissions["allowed_folders"].append(folder)
                    self._save_permissions()
                    
                    logger.info(f"Added allowed folder: {folder}")
                    self.tray_icon.showMessage(
                        "E.V3 Permissions",
                        f"Added folder: {folder}",
                        QSystemTrayIcon.Information,
                        2000
                    )
                    
                    self._notify_kernel_permissions()
                else:
                    QMessageBox.information(
                        self,
                        "E.V3 Permissions",
                        "This folder is already in the allowed list."
                    )
        
        # Show current allowed folders
        if self.permissions["allowed_folders"]:
            folders_list = "\n".join(self.permissions["allowed_folders"])
            QMessageBox.information(
                self,
                "Allowed Folders",
                f"Currently allowed folders:\n\n{folders_list}\n\nTo remove folders, edit config/permissions.yaml"
            )
        else:
            QMessageBox.information(
                self,
                "Allowed Folders",
                "No folders currently allowed.\nSelect folders to grant access."
            )
    
    def reset_permissions(self):
        """Reset all permissions to secure defaults"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Reset Permissions",
            "Reset all permissions to secure defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.permissions = {
                "filesystem": "scoped",
                "network": "local",
                "sysinfo": "basic",
                "calendar": "read",
                "llm": "local",
                "llm_logging": False,
                "allowed_folders": []
            }
            
            self._update_permission_checkmarks()
            self._save_permissions()
            
            logger.info("Permissions reset to defaults")
            self.tray_icon.showMessage(
                "E.V3 Permissions",
                "Permissions reset to secure defaults",
                QSystemTrayIcon.Information,
                2000
            )
            
            self._notify_kernel_permissions()
    
    def _notify_kernel_permissions(self):
        """Notify kernel of permission changes via IPC"""
        # This would send an IPC message to the kernel
        # For now, just log it
        logger.info("Kernel notified of permission changes")
        # TODO: Implement IPC message sending when kernel connection is available
        # Example: self.ipc_client.send_message("update_permissions", self.permissions)
    
    def open_modules_window(self):
        """Open the Modules configuration window"""
        logger.info("Opening Modules window")

        # Check if Modules window already exists
        if not hasattr(self, 'core_window') or not self.core_window:
            self.core_window = ModulesWindow(self)

        self.core_window.show()
        self.core_window.raise_()
        self.core_window.activateWindow()
    
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
    
    def _setup_global_hotkey(self):
        """Setup global keyboard shortcut to summon character and chat"""
        try:
            keyboard.add_hotkey(self.hotkey_combination, self._on_hotkey_pressed)
            logger.info(f"Global hotkey registered: {self.hotkey_combination}")
        except Exception as e:
            logger.error(f"Failed to register global hotkey: {e}")
    
    def _on_hotkey_pressed(self):
        """Handle hotkey press - show window and open chat"""
        if not self.hotkey_enabled:
            return
        
        logger.info("Hotkey pressed - summoning character and chat")
        
        # Show window if hidden
        if not self.isVisible():
            self.show()
        
        # Bring to front
        self.raise_()
        self.activateWindow()
        
        # Open chat window
        self.open_chat_window()
    
    def toggle_hotkey(self, checked: bool):
        """Toggle hotkey enabled/disabled"""
        self.hotkey_enabled = checked
        logger.info(f"Hotkey {'enabled' if checked else 'disabled'}")
    
    def open_chat_window(self):
        """Open the chat input window"""
        if self.chat_window is None:
            self.chat_window = ChatWindow(self)
            self.chat_window.message_sent.connect(self.send_chat_message)
        
        # Position chat window next to character
        chat_pos = self.pos()
        chat_pos.setX(chat_pos.x() - self.chat_window.width() - 10)
        self.chat_window.move(chat_pos)
        
        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.focus_input()
        
        logger.info("Chat window opened")
    
    def send_chat_message(self, message: str):
        """Send chat message to kernel via IPC"""
        logger.info(f"Sending chat message: {message[:50]}...")
        
        # This should be connected to IPC client in main_ui.py
        # For now, just log it
        # self.ipc_client.send_message("user_message", {"message": message})
    
    def display_chat_response(self, response: str):
        """Display LLM response in chat window"""
        if self.chat_window and self.chat_window.isVisible():
            self.chat_window.display_response(response)


class ChatWindow(QDialog):
    """
    Floating chat window for user input and LLM responses
    Can be closed independently of the character window
    """
    
    message_sent = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Chat with E.V3")
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint |
            Qt.WindowCloseButtonHint
        )
        
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2b2b2b, stop:1 #1a1a1a);
                border: 2px solid #3a7bd5;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
                padding: 5px;
            }
            QLineEdit {
                background: #3a3a3a;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #3a7bd5;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a7bd5, stop:1 #2563a8);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a8be5, stop:1 #3573b8);
            }
            QPushButton:pressed {
                background: #2563a8;
            }
            QFrame {
                background: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 5px;
            }
        """)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create chat UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("💬 Chat with E.V3")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #3a7bd5;")
        layout.addWidget(title)
        
        # Chat history display
        self.chat_history = QLabel("")
        self.chat_history.setWordWrap(True)
        self.chat_history.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.chat_history.setStyleSheet("""
            QLabel {
                background: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 10px;
                color: #e0e0e0;
                font-size: 12px;
            }
        """)
        
        # Scroll area for chat history
        history_frame = QFrame()
        history_frame.setFixedHeight(320)
        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.addWidget(self.chat_history)
        layout.addWidget(history_frame)
        
        # Input area
        input_label = QLabel("Your message:")
        layout.addWidget(input_label)
        
        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here... (add 'find out' for external LLM)")
        self.input_field.returnPressed.connect(self._send_message)
        layout.addWidget(self.input_field)
        
        # Send button
        send_button = QPushButton("Send")
        send_button.clicked.connect(self._send_message)
        layout.addWidget(send_button)
        
        # Info label
        info_label = QLabel("💡 Tip: Press Enter to send, close button (X) to hide chat window")
        info_label.setStyleSheet("font-size: 11px; color: #888888;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.chat_messages = []
    
    def _send_message(self):
        """Send message from input field"""
        message = self.input_field.text().strip()
        
        if not message:
            return
        
        # Add to history
        self.chat_messages.append(f"<b>You:</b> {message}")
        self._update_history()
        
        # Emit signal
        self.message_sent.emit(message)
        
        # Clear input
        self.input_field.clear()
        
        # Add "thinking" indicator
        self.chat_messages.append("<i style='color: #3a7bd5;'>E.V3 is thinking...</i>")
        self._update_history()
    
    def display_response(self, response: str):
        """Display LLM response"""
        # Remove "thinking" indicator
        if self.chat_messages and "thinking" in self.chat_messages[-1]:
            self.chat_messages.pop()
        
        # Add response
        self.chat_messages.append(f"<b style='color: #3a7bd5;'>E.V3:</b> {response}")
        self._update_history()
    
    def _update_history(self):
        """Update chat history display"""
        # Keep last 10 messages
        if len(self.chat_messages) > 10:
            self.chat_messages = self.chat_messages[-10:]
        
        history_text = "<br><br>".join(self.chat_messages)
        self.chat_history.setText(history_text)
    
    def focus_input(self):
        """Focus the input field"""
        self.input_field.setFocus()
    
    def closeEvent(self, event):
        """Handle window close - hide instead of destroy"""
        self.hide()
        event.accept()
