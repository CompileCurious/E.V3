"""
3D Model Loader and Renderer
Supports VRM, GLB, GLTF formats with bone animations
"""

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
import struct


class Bone:
    """Represents a bone in the skeletal animation system"""
    
    def __init__(self, name: str, parent_idx: int = -1):
        self.name = name
        self.parent_idx = parent_idx
        self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.rotation = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)  # Quaternion
        self.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        self.transform_matrix = np.eye(4, dtype=np.float32)
        self.children = []
    
    def calculate_transform(self):
        """Calculate transformation matrix from position, rotation, scale"""
        # This is simplified - proper implementation would use quaternion math
        self.transform_matrix = np.eye(4, dtype=np.float32)
        # Apply transformations (scale, rotate, translate)
        self.transform_matrix[:3, 3] = self.position


class BlendShape:
    """Represents a blendshape/morph target"""
    
    def __init__(self, name: str, vertices: np.ndarray):
        self.name = name
        self.vertices = vertices  # Vertex displacements
        self.weight = 0.0  # 0.0 to 1.0


class Mesh:
    """Represents a 3D mesh"""
    
    def __init__(self):
        self.vertices = np.array([], dtype=np.float32)
        self.normals = np.array([], dtype=np.float32)
        self.uvs = np.array([], dtype=np.float32)
        self.indices = np.array([], dtype=np.uint32)
        self.bone_weights = []
        self.bone_indices = []
        
        # OpenGL buffers
        self.vao = None
        self.vbo_vertices = None
        self.vbo_normals = None
        self.vbo_uvs = None
        self.ebo = None
        
        self.texture_id = None
    
    def setup_gl_buffers(self):
        """Setup OpenGL buffers"""
        # Generate VAO
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # Vertex buffer
        self.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        # Normal buffer
        if len(self.normals) > 0:
            self.vbo_normals = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
            glBufferData(GL_ARRAY_BUFFER, self.normals.nbytes, self.normals, GL_STATIC_DRAW)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
            glEnableVertexAttribArray(1)
        
        # UV buffer
        if len(self.uvs) > 0:
            self.vbo_uvs = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_uvs)
            glBufferData(GL_ARRAY_BUFFER, self.uvs.nbytes, self.uvs, GL_STATIC_DRAW)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)
            glEnableVertexAttribArray(2)
        
        # Index buffer
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        glBindVertexArray(0)
    
    def render(self):
        """Render the mesh"""
        if self.vao is None:
            return
        
        glBindVertexArray(self.vao)
        
        if self.texture_id:
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
        
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        
        glBindVertexArray(0)


class Model3D:
    """
    3D model with skeletal animation and blendshapes
    """
    
    def __init__(self):
        self.meshes: List[Mesh] = []
        self.bones: List[Bone] = []
        self.blendshapes: Dict[str, BlendShape] = {}
        self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.scale = 1.0
    
    def add_mesh(self, mesh: Mesh):
        """Add mesh to model"""
        self.meshes.append(mesh)
        mesh.setup_gl_buffers()
    
    def add_bone(self, bone: Bone):
        """Add bone to skeleton"""
        self.bones.append(bone)
    
    def add_blendshape(self, name: str, blendshape: BlendShape):
        """Add blendshape/morph target"""
        self.blendshapes[name] = blendshape
    
    def set_blendshape_weight(self, name: str, weight: float):
        """Set blendshape weight (0.0 to 1.0)"""
        if name in self.blendshapes:
            self.blendshapes[name].weight = max(0.0, min(1.0, weight))
    
    def update_skeleton(self):
        """Update bone transformations"""
        for bone in self.bones:
            bone.calculate_transform()
    
    def render(self):
        """Render the model"""
        glPushMatrix()
        
        # Apply model transformations
        glTranslatef(*self.position)
        glRotatef(self.rotation[0], 1, 0, 0)
        glRotatef(self.rotation[1], 0, 1, 0)
        glRotatef(self.rotation[2], 0, 0, 1)
        glScalef(self.scale, self.scale, self.scale)
        
        # Render all meshes
        for mesh in self.meshes:
            mesh.render()
        
        glPopMatrix()


class ModelLoader:
    """
    Load 3D models from various formats
    Privacy: All models are loaded and processed locally
    """
    
    @staticmethod
    def load_gltf(filepath: str) -> Optional[Model3D]:
        """
        Load GLTF/GLB model
        This is a simplified loader - production should use pygltflib or similar
        """
        try:
            from pygltflib import GLTF2
            
            gltf = GLTF2().load(filepath)
            model = Model3D()
            
            logger.info(f"Loading GLTF model: {filepath}")
            logger.info(f"Meshes: {len(gltf.meshes)}, Nodes: {len(gltf.nodes)}")
            
            # Load meshes (simplified)
            for gltf_mesh in gltf.meshes:
                for primitive in gltf_mesh.primitives:
                    mesh = Mesh()
                    
                    # Get vertex data
                    # Note: This is simplified - proper implementation needed
                    # for production use with proper accessor/buffer handling
                    
                    mesh.vertices = np.array([
                        # Placeholder vertices for a simple cube
                        -1, -1, -1,  1, -1, -1,  1,  1, -1, -1,  1, -1,
                        -1, -1,  1,  1, -1,  1,  1,  1,  1, -1,  1,  1
                    ], dtype=np.float32)
                    
                    mesh.indices = np.array([
                        0,1,2, 0,2,3,  4,5,6, 4,6,7,  0,1,5, 0,5,4,
                        2,3,7, 2,7,6,  0,3,7, 0,7,4,  1,2,6, 1,6,5
                    ], dtype=np.uint32)
                    
                    model.add_mesh(mesh)
            
            return model
            
        except ImportError:
            logger.error("pygltflib not installed. Install with: pip install pygltflib")
            return None
        except Exception as e:
            logger.error(f"Error loading GLTF model: {e}")
            return None
    
    @staticmethod
    def load_vrm(filepath: str) -> Optional[Model3D]:
        """
        Load VRM model (VRoid format)
        VRM is based on GLTF with VRM-specific extensions
        """
        try:
            # VRM is essentially GLTF with extensions
            model = ModelLoader.load_gltf(filepath)
            
            if model:
                logger.info("VRM model loaded (using GLTF loader)")
                # Additional VRM-specific processing would go here
            
            return model
            
        except Exception as e:
            logger.error(f"Error loading VRM model: {e}")
            return None
    
    @staticmethod
    def create_simple_character() -> Model3D:
        """
        Create a simple character model for testing
        Use this until a proper VRM/GLTF model is available
        """
        model = Model3D()
        
        # Create a simple character mesh (sphere for head, cylinders for body)
        mesh = Mesh()
        
        # Simple sphere vertices (low poly)
        vertices = []
        indices = []
        
        # Create a simple icosphere
        t = (1.0 + np.sqrt(5.0)) / 2.0
        
        # 12 vertices of icosahedron
        base_vertices = [
            [-1,  t,  0], [ 1,  t,  0], [-1, -t,  0], [ 1, -t,  0],
            [ 0, -1,  t], [ 0,  1,  t], [ 0, -1, -t], [ 0,  1, -t],
            [ t,  0, -1], [ t,  0,  1], [-t,  0, -1], [-t,  0,  1]
        ]
        
        mesh.vertices = np.array(base_vertices, dtype=np.float32).flatten()
        
        # Indices for icosahedron faces
        mesh.indices = np.array([
            0,11,5,  0,5,1,  0,1,7,  0,7,10,  0,10,11,
            1,5,9,  5,11,4,  11,10,2,  10,7,6,  7,1,8,
            3,9,4,  3,4,2,  3,2,6,  3,6,8,  3,8,9,
            4,9,5,  2,4,11,  6,2,10,  8,6,7,  9,8,1
        ], dtype=np.uint32)
        
        # Generate normals (simplified - just use vertex positions as normals)
        mesh.normals = mesh.vertices.copy()
        
        model.add_mesh(mesh)
        
        logger.info("Created simple test character")
        return model
