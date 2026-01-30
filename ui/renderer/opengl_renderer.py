"""
OpenGL 3D Renderer Widget with GPU Skinning
Renders 3D character model with skeletal animations using GLSL shaders
"""

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QSurfaceFormat
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
        
        # Setup format - request OpenGL 3.3 Compatibility for GPU skinning with legacy fallback
        # Compatibility profile allows both shader-based and legacy rendering
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)  # OpenGL 3.3 for shader support
        fmt.setProfile(QSurfaceFormat.CompatibilityProfile)  # Allows legacy fallback
        fmt.setSamples(4)  # Antialiasing
        fmt.setAlphaBufferSize(8)  # Enable alpha channel
        fmt.setDepthBufferSize(24)
        self.setFormat(fmt)
        
        # Make widget transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Idle animation state
        self.idle_animation_enabled = True
        self.breathing_phase = 0.0
        
        # GPU skinning flag
        self.gpu_skinning_initialized = False
        
        # Setup timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        fps = self.config.get("rendering", {}).get("fps", 60)
        # Start with idle animation enabled
        self.timer.start(1000 // fps)
        
        logger.info("OpenGL renderer initialized (GPU skinning enabled)")
    
    def initializeGL(self):
        """Initialize OpenGL and GPU skinning"""
        # Log OpenGL version info
        version = glGetString(GL_VERSION)
        vendor = glGetString(GL_VENDOR)
        renderer_str = glGetString(GL_RENDERER)
        if version:
            logger.info(f"OpenGL Version: {version.decode()}")
        if vendor:
            logger.info(f"OpenGL Vendor: {vendor.decode()}")
        if renderer_str:
            logger.info(f"OpenGL Renderer: {renderer_str.decode()}")
        
        # Set clear color (transparent or background color)
        glClearColor(0.0, 0.0, 0.0, 0.0)  # Transparent
        
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Check if we can use modern OpenGL
        try:
            gl_major = glGetIntegerv(GL_MAJOR_VERSION)
            gl_minor = glGetIntegerv(GL_MINOR_VERSION)
            self.supports_modern_gl = (gl_major > 3) or (gl_major == 3 and gl_minor >= 3)
            logger.info(f"OpenGL {gl_major}.{gl_minor} detected, modern GL support: {self.supports_modern_gl}")
        except:
            self.supports_modern_gl = False
            logger.warning("Could not detect OpenGL version, assuming legacy")
        
        # ALWAYS setup legacy lighting (needed for fallback and compatibility)
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
        self.load_model()
        
        # Try GPU skinning if modern GL is available
        self.gpu_skinning_initialized = False
        if self.model and self.supports_modern_gl:
            try:
                if self.model.initialize_gpu_skinning():
                    self.gpu_skinning_initialized = True
                    logger.info("GPU skinning initialized successfully")
                else:
                    logger.warning("GPU skinning initialization failed, using legacy rendering")
            except Exception as e:
                logger.error(f"GPU skinning init error: {e}, using legacy rendering")
        
        logger.info("OpenGL initialized")
    
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
        
        # Use legacy OpenGL rendering (stable and working)
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
            
            # Render the model
            self.model.render()
            
            glPopMatrix()
        
        glFlush()
    
    def load_model(self):
        """Load 3D character model"""
        model_path = self.config.get("ui", {}).get("model", {}).get("model_path", "")
        
        logger.info(f"Loading model with path: '{model_path}'")
        
        if not model_path:
            logger.warning("No model path specified, using simple character")
            self.model = ModelLoader.create_simple_character()
            return
        
        # Try to load model
        logger.info(f"Attempting to load model from: {model_path}")
        if model_path.endswith('.vrm'):
            logger.info("Detected VRM format")
            self.model = ModelLoader.load_vrm(model_path)
        elif model_path.endswith(('.gltf', '.glb')):
            logger.info("Detected GLTF/GLB format")
            self.model = ModelLoader.load_gltf(model_path)
        else:
            logger.warning(f"Unsupported model format: {model_path}")
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
        
        # Update idle breathing animation (slow, gentle)
        if self.idle_animation_enabled:
            self.breathing_phase += dt * 2.0  # 2 radians per second = ~0.3 breaths/sec
            # Log occasionally to verify animation is running
            if int(self.breathing_phase) % 5 == 0 and int(self.breathing_phase * 10) % 10 == 0:
                logger.debug(f"Idle animation: phase={self.breathing_phase:.2f}")
        
        # Update model animations
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
        """Handle mouse move for camera control"""
        if self.last_mouse_pos is None:
            return
        
        current_pos = event.position().toPoint()
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
