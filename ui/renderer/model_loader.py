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
import base64


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
        
        # Material properties
        self.color = (0.8, 0.8, 0.8, 1.0)  # Default light gray color
        
        # OpenGL buffers
        self.vao = None
        self.vbo_vertices = None
        self.vbo_normals = None
        self.vbo_uvs = None
        self.ebo = None
        
        self.texture_id = None
        self.use_immediate_mode = False  # For compatibility with older OpenGL
    
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
        # Enable texturing if we have a texture
        if self.texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            # Use white color with texture so texture colors show through
            glColor4f(1.0, 1.0, 1.0, 1.0)
        else:
            # Apply material color if no texture
            glDisable(GL_TEXTURE_2D)
            glColor4f(*self.color)
        
        if self.use_immediate_mode:
            # Use immediate mode for compatibility
            glBegin(GL_TRIANGLES)
            for i in range(0, len(self.indices), 3):
                for j in range(3):
                    idx = self.indices[i + j]
                    # Apply texture coordinates if available
                    if self.texture_id and len(self.uvs) > idx * 2:
                        glTexCoord2f(self.uvs[idx*2], self.uvs[idx*2+1])
                    # Apply normal
                    if len(self.normals) > idx * 3:
                        glNormal3f(self.normals[idx*3], self.normals[idx*3+1], self.normals[idx*3+2])
                    # Apply vertex
                    if len(self.vertices) > idx * 3:
                        glVertex3f(self.vertices[idx*3], self.vertices[idx*3+1], self.vertices[idx*3+2])
            glEnd()
            
            # Disable texture after rendering
            if self.texture_id:
                glBindTexture(GL_TEXTURE_2D, 0)
                glDisable(GL_TEXTURE_2D)
            return
        
        # Modern OpenGL path
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
        # Don't setup GL buffers here - that requires OpenGL context
        # Buffers will be set up during rendering initialization
    
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
        """Render the model - transformations should be handled by caller"""
        from OpenGL.GL import glColor4f
        
        # Set a visible color for the test character (light blue)
        glColor4f(0.3, 0.7, 1.0, 1.0)
        
        # Render all meshes
        for mesh in self.meshes:
            mesh.render()


class ModelLoader:
    """
    Load 3D models from various formats
    Privacy: All models are loaded and processed locally
    """
    
    @staticmethod
    def _get_accessor_data(gltf, accessor_idx: int) -> Optional[np.ndarray]:
        """
        Extract data from a GLTF accessor
        Handles buffer views and binary data parsing
        """
        try:
            accessor = gltf.accessors[accessor_idx]
            buffer_view = gltf.bufferViews[accessor.bufferView]
            buffer = gltf.buffers[buffer_view.buffer]
            
            # Get the buffer data
            if hasattr(gltf, '_glb_data') and gltf._glb_data:
                # GLB file with embedded binary data
                buffer_data = gltf._glb_data
            elif buffer.uri:
                if buffer.uri.startswith('data:'):
                    # Data URI format
                    data_uri = buffer.uri
                    # Extract base64 data after the comma
                    base64_data = data_uri.split(',', 1)[1]
                    buffer_data = base64.b64decode(base64_data)
                else:
                    logger.error("External buffer files not supported")
                    return None
            else:
                logger.error("No buffer data found")
                return None
            
            # Calculate byte offset
            byte_offset = (buffer_view.byteOffset or 0) + (accessor.byteOffset or 0)
            
            # Map GLTF component types to numpy dtypes
            component_type_map = {
                5120: np.int8,    # BYTE
                5121: np.uint8,   # UNSIGNED_BYTE
                5122: np.int16,   # SHORT
                5123: np.uint16,  # UNSIGNED_SHORT
                5125: np.uint32,  # UNSIGNED_INT
                5126: np.float32, # FLOAT
            }
            
            dtype = component_type_map.get(accessor.componentType)
            if dtype is None:
                logger.error(f"Unsupported component type: {accessor.componentType}")
                return None
            
            # Map GLTF types to component counts
            type_component_count = {
                'SCALAR': 1,
                'VEC2': 2,
                'VEC3': 3,
                'VEC4': 4,
                'MAT2': 4,
                'MAT3': 9,
                'MAT4': 16,
            }
            
            components = type_component_count.get(accessor.type, 1)
            
            # Extract the data
            element_size = np.dtype(dtype).itemsize * components
            total_size = element_size * accessor.count
            
            data_bytes = buffer_data[byte_offset:byte_offset + total_size]
            data = np.frombuffer(data_bytes, dtype=dtype)
            
            # Reshape to (count, components)
            if components > 1:
                data = data.reshape((accessor.count, components))
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting accessor data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def _load_texture(gltf, texture_idx: int) -> Optional[int]:
        """
        Load texture from GLTF and create OpenGL texture
        Returns OpenGL texture ID
        """
        try:
            from PIL import Image
            import io
            
            texture = gltf.textures[texture_idx]
            image_idx = texture.source
            image = gltf.images[image_idx]
            
            # Get image data
            if image.bufferView is not None:
                # Image data is embedded in buffer
                buffer_view = gltf.bufferViews[image.bufferView]
                buffer = gltf.buffers[buffer_view.buffer]
                
                # Get buffer data
                if hasattr(gltf, '_glb_data') and gltf._glb_data:
                    buffer_data = gltf._glb_data
                elif buffer.uri and buffer.uri.startswith('data:'):
                    data_uri = buffer.uri
                    base64_data = data_uri.split(',', 1)[1]
                    buffer_data = base64.b64decode(base64_data)
                else:
                    logger.error("Cannot access buffer data for texture")
                    return None
                
                # Extract image bytes
                byte_offset = buffer_view.byteOffset or 0
                byte_length = buffer_view.byteLength
                image_bytes = buffer_data[byte_offset:byte_offset + byte_length]
                
                # Load image with PIL
                img = Image.open(io.BytesIO(image_bytes))
            elif image.uri:
                # External image file (not common in GLB/VRM)
                logger.warning(f"External image URI not supported: {image.uri}")
                return None
            else:
                logger.error("No image data found")
                return None
            
            # Convert to RGBA
            img = img.convert('RGBA')
            img_data = img.tobytes()
            width, height = img.size
            
            # Create OpenGL texture
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            
            # Set texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            
            # Upload texture data
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            glGenerateMipmap(GL_TEXTURE_2D)
            
            glBindTexture(GL_TEXTURE_2D, 0)
            
            logger.info(f"Loaded texture: {width}x{height}")
            return tex_id
            
        except ImportError:
            logger.error("PIL/Pillow not installed. Install with: pip install Pillow")
            return None
        except Exception as e:
            logger.error(f"Error loading texture: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def load_gltf(filepath: str) -> Optional[Model3D]:
        """
        Load GLTF/GLB model
        Properly parses vertex data from GLTF buffers
        """
        try:
            import os
            if not os.path.exists(filepath):
                logger.error(f"Model file not found: {filepath}")
                return None
            
            from pygltflib import GLTF2
            
            logger.info(f"Loading GLTF/GLB/VRM model: {filepath}")
            
            # Load the GLTF file
            # For GLB/VRM files, we need to load binary data
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            # Check if it's a GLB file (binary GLTF)
            if file_data[:4] == b'glTF':
                logger.info("Loading as binary GLB/VRM format")
                gltf = GLTF2.load_from_bytes(file_data)
            else:
                logger.info("Loading as JSON GLTF format")
                gltf = GLTF2.load(filepath)
            
            logger.info("Successfully loaded GLTF model")
            
            model = Model3D()
            
            logger.info(f"Meshes: {len(gltf.meshes)}, Nodes: {len(gltf.nodes)}, Buffers: {len(gltf.buffers)}")
            
            # Parse each mesh
            mesh_count = 0
            for gltf_mesh in gltf.meshes:
                for primitive in gltf_mesh.primitives:
                    mesh = Mesh()
                    
                    try:
                        # Get vertex positions
                        if 'POSITION' in primitive.attributes.__dict__:
                            position_accessor_idx = primitive.attributes.POSITION
                            position_data = ModelLoader._get_accessor_data(gltf, position_accessor_idx)
                            if position_data is not None:
                                mesh.vertices = position_data.flatten().astype(np.float32)
                        
                        # Get normals
                        if 'NORMAL' in primitive.attributes.__dict__:
                            normal_accessor_idx = primitive.attributes.NORMAL
                            normal_data = ModelLoader._get_accessor_data(gltf, normal_accessor_idx)
                            if normal_data is not None:
                                mesh.normals = normal_data.flatten().astype(np.float32)
                        
                        # Get UVs
                        if 'TEXCOORD_0' in primitive.attributes.__dict__:
                            uv_accessor_idx = primitive.attributes.TEXCOORD_0
                            uv_data = ModelLoader._get_accessor_data(gltf, uv_accessor_idx)
                            if uv_data is not None:
                                mesh.uvs = uv_data.flatten().astype(np.float32)
                        
                        # Load material/texture if available
                        if primitive.material is not None:
                            try:
                                material = gltf.materials[primitive.material]
                                # Get base color from material
                                if material.pbrMetallicRoughness:
                                    if material.pbrMetallicRoughness.baseColorFactor:
                                        color = material.pbrMetallicRoughness.baseColorFactor
                                        mesh.color = tuple(color) if len(color) == 4 else (color[0], color[1], color[2], 1.0)
                                        logger.debug(f"Loaded material color: {mesh.color}")
                                    
                                    # Load texture
                                    if material.pbrMetallicRoughness.baseColorTexture:
                                        texture_idx = material.pbrMetallicRoughness.baseColorTexture.index
                                        mesh.texture_id = ModelLoader._load_texture(gltf, texture_idx)
                                        if mesh.texture_id:
                                            logger.info(f"Loaded texture {texture_idx} for mesh")
                            except Exception as e:
                                logger.debug(f"Could not load material: {e}")
                        
                        # Get indices
                        if primitive.indices is not None:
                            indices_data = ModelLoader._get_accessor_data(gltf, primitive.indices)
                            if indices_data is not None:
                                mesh.indices = indices_data.flatten().astype(np.uint32)
                        
                        # If no indices, generate them
                        if len(mesh.indices) == 0 and len(mesh.vertices) > 0:
                            vertex_count = len(mesh.vertices) // 3
                            mesh.indices = np.arange(vertex_count, dtype=np.uint32)
                        
                        # Only add mesh if it has vertices
                        if len(mesh.vertices) > 0:
                            mesh.use_immediate_mode = True  # Use immediate mode for compatibility
                            model.add_mesh(mesh)
                            mesh_count += 1
                            logger.info(f"Loaded mesh {mesh_count}: {len(mesh.vertices)//3} vertices, {len(mesh.indices)} indices")
                    
                    except Exception as e:
                        logger.error(f"Error parsing mesh primitive: {e}")
                        continue
            
            if mesh_count > 0:
                logger.info(f"Successfully loaded VRM with {mesh_count} meshes")
                return model
            else:
                logger.warning("No valid meshes found in GLTF file, falling back to simple character")
                return ModelLoader.create_simple_character()
            
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
        
        # Create a simple character mesh (sphere)
        mesh = Mesh()
        
        # Create sphere using latitude/longitude method
        from OpenGL.GL import glBegin, glEnd, glVertex3f, glNormal3f, GL_TRIANGLES
        import math
        
        # Store vertices for a sphere (20 segments)
        segments = 20
        rings = 20
        vertices = []
        indices = []
        
        for ring in range(rings + 1):
            theta = ring * math.pi / rings
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)
            
            for seg in range(segments + 1):
                phi = seg * 2 * math.pi / segments
                sin_phi = math.sin(phi)
                cos_phi = math.cos(phi)
                
                x = cos_phi * sin_theta
                y = cos_theta
                z = sin_phi * sin_theta
                
                vertices.extend([x, y, z])
        
        # Generate indices for triangle strips
        for ring in range(rings):
            for seg in range(segments):
                first = ring * (segments + 1) + seg
                second = first + segments + 1
                
                indices.extend([first, second, first + 1])
                indices.extend([second, second + 1, first + 1])
        
        mesh.vertices = np.array(vertices, dtype=np.float32)
        mesh.indices = np.array(indices, dtype=np.uint32)
        mesh.normals = mesh.vertices.copy()  # Sphere normals = positions
        
        # Use immediate mode rendering for compatibility
        mesh.use_immediate_mode = True
        
        model.add_mesh(mesh)
        
        logger.info("Created simple test character")
        return model
