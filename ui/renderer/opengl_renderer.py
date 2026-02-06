"""
OpenGL 3D Renderer Widget with GPU Skinning
Renders 3D character model with skeletal animations using GLSL shaders
"""

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QSurfaceFormat, QCursor
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from typing import Optional, Dict, Any
from loguru import logger

from .model_loader import Model3D, ModelLoader


class OpenGLRenderer(QOpenGLWidget):
    """
    OpenGL widget for rendering 3D character with GPU skeletal animation
    Supports both modern shader-based rendering and legacy fallback
    """
    
    def __init__(self, parent=None, config: Dict[str, Any] = None):
        super().__init__(parent)
        
        self.config = config or {}
        self.model: Optional[Model3D] = None
        
        # Camera
        self.camera_distance = 3.0
        self.camera_angle_x = 0.0
        self.camera_angle_y = 0.0
        self.camera_pan_x = 0.0
        self.camera_pan_y = 0.0
        
        # Mouse interaction (Blender-style)
        self.last_mouse_pos = None
        self.mouse_button = None
        
        # Animation
        self.animation_time = 0.0
        self.animation_speed = 1.0
        self.last_anim_update = 0.0  # Track last animation update time
        self.anim_update_interval = 1.0 / 30.0  # Update animation at 30fps
        self.last_mouse_x = 0.5
        self.last_mouse_y = 0.5
        
        # Setup format - use OpenGL 2.1 Compatibility for maximum compatibility
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)  # OpenGL 2.1 for broad compatibility
        fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
        fmt.setSamples(4)  # Antialiasing
        fmt.setAlphaBufferSize(8)  # Enable alpha channel
        fmt.setDepthBufferSize(24)
        self.setFormat(fmt)
        
        # Make widget transparent but accept mouse input
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Idle animation state
        self.idle_animation_enabled = True
        self.breathing_phase = 0.0
        
        # Ensure we capture all mouse events - don't make transparent for input
        self.setMouseTracking(True)  # Track mouse even without button pressed
        
        # Mouse tracking for head
        self.mouse_x = 0.5  # Normalized 0-1
        self.mouse_y = 0.5  # Normalized 0-1
        
        # GPU skinning flag - disabled for now, use legacy rendering
        self.gpu_skinning_initialized = False
        self.supports_modern_gl = False
        
        # Setup timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        fps = self.config.get("rendering", {}).get("fps", 60)
        # Start with idle animation enabled
        self.timer.start(1000 // fps)
        
        print(f">>> OpenGLRenderer __init__ complete, format version: {self.format().version()}", flush=True)
        logger.info("OpenGL renderer initialized")
    
    def initializeGL(self):
        """Initialize OpenGL"""
        print(">>> initializeGL() called - starting OpenGL setup", flush=True)
        logger.info("initializeGL() called - starting OpenGL setup")
        
        # Log OpenGL version info
        try:
            version = glGetString(GL_VERSION)
            vendor = glGetString(GL_VENDOR)
            renderer_str = glGetString(GL_RENDERER)
            if version:
                print(f">>> OpenGL Version: {version.decode()}", flush=True)
                logger.info(f"OpenGL Version: {version.decode()}")
            if vendor:
                logger.info(f"OpenGL Vendor: {vendor.decode()}")
            if renderer_str:
                logger.info(f"OpenGL Renderer: {renderer_str.decode()}")
        except Exception as e:
            print(f">>> OpenGL error: {e}", flush=True)
            logger.warning(f"Could not get OpenGL info: {e}")
        
        # Set clear color - transparent for desktop overlay
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Transparent background
        
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Setup legacy lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        ambient = self.config.get("rendering", {}).get("ambient_light", 0.6)
        directional = self.config.get("rendering", {}).get("directional_light", 0.8)
        
        glLightfv(GL_LIGHT0, GL_AMBIENT, [ambient, ambient, ambient, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [directional, directional, directional, 1.0])
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Load model
        logger.info("Loading model...")
        self.load_model()
        
        # Try to initialize GPU skinning for proper bone animation
        if self.model:
            try:
                # Check OpenGL version for GPU skinning support
                gl_version = glGetString(GL_VERSION)
                if gl_version:
                    version_str = gl_version.decode()
                    major = int(version_str.split('.')[0])
                    if major >= 3:
                        self.supports_modern_gl = True
                        logger.info(f"OpenGL {major}.x supports GPU skinning")
                        
                        if self.model.initialize_gpu_skinning():
                            self.gpu_skinning_initialized = True
                            logger.info("GPU skinning enabled - arm poses will work!")
                        else:
                            logger.warning("GPU skinning init failed, bones won't animate")
            except Exception as e:
                logger.warning(f"GPU skinning setup error: {e}")
        
        logger.info("OpenGL initialization complete")
    
    def resizeGL(self, w, h):
        """Handle resize"""
        glViewport(0, 0, w, h)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        aspect = w / h if h > 0 else 1.0
        gluPerspective(45.0, aspect, 0.1, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Use legacy OpenGL rendering
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width() / self.height() if self.height() > 0 else 1.0
        gluPerspective(45.0, aspect, 0.1, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Setup camera with pan support
        glTranslatef(self.camera_pan_x, self.camera_pan_y, -self.camera_distance)
        glRotatef(self.camera_angle_x, 1.0, 0.0, 0.0)
        glRotatef(self.camera_angle_y, 0.0, 1.0, 0.0)
        
        # Render model with idle animation
        if self.model:
            glPushMatrix()
            
            # Apply model position
            glTranslatef(self.model.position[0], self.model.position[1], self.model.position[2])
            glRotatef(self.model.rotation[1], 0.0, 1.0, 0.0)
            glRotatef(self.model.rotation[0], 1.0, 0.0, 0.0)
            glRotatef(self.model.rotation[2], 0.0, 0.0, 1.0)
            
            # Apply idle animation (gentle breathing/sway)
            if self.idle_animation_enabled:
                breath_scale = 1.0 + 0.03 * np.sin(self.breathing_phase)
                sway_angle = 3.0 * np.sin(self.breathing_phase * 0.7)
                
                glRotatef(sway_angle, 0.0, 1.0, 0.0)
                glScalef(
                    self.model.scale * breath_scale,
                    self.model.scale * breath_scale,
                    self.model.scale * breath_scale
                )
            else:
                glScalef(self.model.scale, self.model.scale, self.model.scale)
            
            # Get current matrices for GPU skinning
            if self.gpu_skinning_initialized:
                view = np.array(glGetFloatv(GL_MODELVIEW_MATRIX), dtype=np.float32).reshape(4, 4)
                proj = np.array(glGetFloatv(GL_PROJECTION_MATRIX), dtype=np.float32).reshape(4, 4)
                self.model.render(view, proj)
            else:
                self.model.render()
            
            glPopMatrix()
        
        glFlush()
    
    def load_model(self):
        """Load 3D character model"""
        import sys
        import os
        
        # Helper for PyInstaller compatibility
        def get_resource_path(relative_path: str) -> str:
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        model_path = self.config.get("ui", {}).get("model", {}).get("model_path", "")
        
        logger.info(f"Loading model with path: '{model_path}'")
        
        if not model_path:
            logger.warning("No model path specified, using simple character")
            self.model = ModelLoader.create_simple_character()
            return
        
        # Resolve path for PyInstaller
        full_model_path = get_resource_path(model_path)
        
        # Try to load model
        logger.info(f"Attempting to load model from: {full_model_path}")
        if full_model_path.endswith('.vrm'):
            logger.info("Detected VRM format")
            self.model = ModelLoader.load_vrm(full_model_path)
        elif full_model_path.endswith(('.gltf', '.glb')):
            logger.info("Detected GLTF/GLB format")
            self.model = ModelLoader.load_gltf(full_model_path)
        else:
            logger.warning(f"Unsupported model format: {full_model_path}")
            self.model = ModelLoader.create_simple_character()
        
        if not self.model:
            logger.warning("Failed to load model, using simple character")
            self.model = ModelLoader.create_simple_character()
        
        # Apply initial transformations
        scale = self.config.get("ui", {}).get("model", {}).get("scale", 1.0)
        self.model.scale = scale
        
        rotation = self.config.get("ui", {}).get("model", {}).get("rotation", [0, 0, 0])
        self.model.rotation = np.array(rotation, dtype=np.float32)
        
        position = self.config.get("ui", {}).get("model", {}).get("position", [0, 0, 0])
        self.model.position = np.array(position, dtype=np.float32)
    
    def update_animation(self):
        """Update animation state"""
        # Increment animation time
        dt = 1.0 / self.config.get("rendering", {}).get("fps", 60)
        self.animation_time += dt * self.animation_speed
        
        # Get global mouse cursor position and convert to widget coordinates
        global_pos = QCursor.pos()
        widget_pos = self.mapFromGlobal(global_pos)
        
        # Update mouse position for head tracking
        if 0 <= widget_pos.x() <= self.width() and 0 <= widget_pos.y() <= self.height():
            self.mouse_x = widget_pos.x() / self.width() if self.width() > 0 else 0.5
            self.mouse_y = widget_pos.y() / self.height() if self.height() > 0 else 0.5
        
        # Only update animation (which triggers expensive CPU skinning) at 30fps
        mouse_moved = abs(self.mouse_x - self.last_mouse_x) > 0.01 or abs(self.mouse_y - self.last_mouse_y) > 0.01
        time_for_update = self.animation_time - self.last_anim_update >= self.anim_update_interval
        
        if time_for_update:
            # Update idle animation on model with mouse position
            if self.model and self.idle_animation_enabled:
                import time
                start = time.perf_counter()
                self.model.update_idle_animation(dt * self.animation_speed, self.mouse_x, self.mouse_y)
                elapsed = time.perf_counter() - start
                if elapsed > 0.05:  # Log if update takes more than 50ms
                    print(f"[PERF] Animation update took {elapsed*1000:.1f}ms", flush=True)
            
            self.last_anim_update = self.animation_time
            self.last_mouse_x = self.mouse_x
            self.last_mouse_y = self.mouse_y
        
        # Update model skeleton
        if self.model:
            self.model.update_skeleton()
        
        # Trigger repaint
        self.update()
    
    def set_camera_angle(self, x: float, y: float):
        """Set camera angles"""
        self.camera_angle_x = x
        self.camera_angle_y = y
    
    def set_camera_distance(self, distance: float):
        """Set camera distance"""
        self.camera_distance = max(1.0, min(10.0, distance))
    
    def apply_glow_effect(self, intensity: float = 0.5, color: tuple = (0.3, 0.6, 1.0)):
        """
        Apply glow effect to character
        Used for alerts and special states
        """
        # This is simplified - proper glow would use shaders
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        
        # Increase ambient light temporarily
        glow_ambient = [color[0] * intensity, color[1] * intensity, color[2] * intensity, 1.0]
        glLightfv(GL_LIGHT0, GL_AMBIENT, glow_ambient)
    
    def set_model_scale(self, scale: float):
        """Set model scale"""
        if self.model:
            self.model.scale = scale
            logger.debug(f"Model scale set to: {scale}")
    
    def set_model_position(self, x: float, y: float, z: float):
        """Set model position"""
        if self.model:
            self.model.position = np.array([x, y, z], dtype=np.float32)
            logger.debug(f"Model position set to: ({x}, {y}, {z})")
    
    def mousePressEvent(self, event):
        """Handle mouse press for Blender-style controls"""
        self.last_mouse_pos = event.position().toPoint()
        self.mouse_button = event.button()
        event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for camera control and head tracking"""
        # Update normalized mouse position for head tracking (always)
        current_pos = event.position().toPoint()
        self.mouse_x = current_pos.x() / self.width() if self.width() > 0 else 0.5
        self.mouse_y = current_pos.y() / self.height() if self.height() > 0 else 0.5
        
        # Camera control (only when button is pressed)
        if self.last_mouse_pos is not None:
            delta = current_pos - self.last_mouse_pos
            
            if self.mouse_button == Qt.LeftButton:
                # Rotate camera (Blender style)
                self.camera_angle_y += delta.x() * 0.5
                self.camera_angle_x += delta.y() * 0.5
                self.camera_angle_x = max(-89, min(89, self.camera_angle_x))
                
            elif self.mouse_button == Qt.MiddleButton:
                # Pan camera (Blender style)
                sensitivity = 0.01
                self.camera_pan_x += delta.x() * sensitivity
                self.camera_pan_y -= delta.y() * sensitivity
            
            self.last_mouse_pos = current_pos
        
        self.update()
        event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.last_mouse_pos = None
        self.mouse_button = None
        event.accept()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom (Blender style)"""
        delta = event.angleDelta().y()
        zoom_speed = 0.001
        self.camera_distance -= delta * zoom_speed
        self.camera_distance = max(1.0, min(10.0, self.camera_distance))
        self.update()
        event.accept()
