"""
3D Model Loader and Renderer with GPU Skeletal Animation
Supports VRM, GLB, GLTF formats with bone animations and GPU skinning
All model processing happens locally - no external services
"""

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
import struct
import base64

# GPU Skinning System
try:
    from .gpu_skinning import SkinningShader, SkinnedMesh, get_skinning_shader, MAX_BONES
    GPU_SKINNING_AVAILABLE = True
    logger.info("GPU skinning module loaded successfully")
except ImportError as e:
    GPU_SKINNING_AVAILABLE = False
    logger.warning(f"GPU skinning module not available: {e}")


class Bone:
    """Represents a bone in the skeletal animation system"""
    
    def __init__(self, name: str, parent_idx: int = -1):
        self.name = name
        self.parent_idx = parent_idx
        self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.rotation = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)  # Quaternion (x,y,z,w)
        self.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        self.local_matrix = np.eye(4, dtype=np.float32)
        self.world_matrix = np.eye(4, dtype=np.float32)
        self.inverse_bind_matrix = np.eye(4, dtype=np.float32)
        self.children = []
        # Animation rotation - applied relative to bind pose
        self.animation_rotation = None  # Quaternion or None for no animation
    
    def calculate_transform(self, parent_matrix=None):
        """Calculate transformation matrix from position, rotation, scale"""
        # Use animation rotation if set, otherwise use bind pose rotation
        # Animation rotations are absolute, not deltas to add to bind pose
        rotation_to_use = self.animation_rotation if self.animation_rotation is not None else self.rotation
        
        # Build local transform matrix from TRS
        self.local_matrix = self._trs_to_matrix(self.position, rotation_to_use, self.scale)
        
        # Calculate world matrix
        if parent_matrix is not None:
            self.world_matrix = parent_matrix @ self.local_matrix
        else:
            self.world_matrix = self.local_matrix.copy()
    
    @staticmethod
    def _trs_to_matrix(translation, rotation, scale):
        """Convert translation, rotation (quaternion), scale to 4x4 matrix"""
        # Quaternion to rotation matrix
        x, y, z, w = rotation
        matrix = np.eye(4, dtype=np.float32)
        
        # Rotation matrix from quaternion
        matrix[0, 0] = 1 - 2*(y*y + z*z)
        matrix[0, 1] = 2*(x*y - w*z)
        matrix[0, 2] = 2*(x*z + w*y)
        
        matrix[1, 0] = 2*(x*y + w*z)
        matrix[1, 1] = 1 - 2*(x*x + z*z)
        matrix[1, 2] = 2*(y*z - w*x)
        
        matrix[2, 0] = 2*(x*z - w*y)
        matrix[2, 1] = 2*(y*z + w*x)
        matrix[2, 2] = 1 - 2*(x*x + y*y)
        
        # Apply scale
        matrix[0, :3] *= scale[0]
        matrix[1, :3] *= scale[1]
        matrix[2, :3] *= scale[2]
        
        # Apply translation
        matrix[0, 3] = translation[0]
        matrix[1, 3] = translation[1]
        matrix[2, 3] = translation[2]
        
        return matrix


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
        self.bone_weights = np.array([], dtype=np.float32)  # Shape: (num_verts, 4)
        self.bone_indices = np.array([], dtype=np.uint16)  # Shape: (num_verts, 4)
        self.skinned_vertices = None  # Transformed vertices after skinning
        
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
    
    def render(self, bone_matrices=None):
        """Render the mesh with optional skeletal animation"""
        # Use skinned vertices if available (CPU skinning already applied)
        if self.skinned_vertices is not None:
            vertices_to_render = self.skinned_vertices
        else:
            vertices_to_render = self.vertices
        
        # Debug: Log first render
        if not hasattr(self, '_first_render_logged'):
            self._first_render_logged = True
            has_skinning = self.skinned_vertices is not None
            logger.info(f"Mesh first render: {len(vertices_to_render)} vertex components, {len(self.indices)} indices, immediate_mode={self.use_immediate_mode}, texture={self.texture_id}, skinned={has_skinning}")
        
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
                    # Apply vertex (skinned or original)
                    if len(vertices_to_render) > idx * 3:
                        glVertex3f(vertices_to_render[idx*3], vertices_to_render[idx*3+1], vertices_to_render[idx*3+2])
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
    3D model with GPU skeletal animation and blendshapes
    Uses GLSL shaders for efficient vertex skinning on GPU
    """
    
    def __init__(self):
        self.meshes: List[Mesh] = []
        self.bones: List[Bone] = []
        self.blendshapes: Dict[str, BlendShape] = {}
        self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.scale = 1.0
        self.joint_indices = []  # Maps joint index -> node index (from skin.joints)
        self.inverse_bind_matrices = None  # IBMs indexed by joint index
        self.skinning_enabled = True  # Enable GPU skinning by default
        self.bones_initialized = False
        
        # Animation state
        self.animation_time = 0.0  # Elapsed time for animations
        self.base_pose_rotations = {}  # Store base rotations before animation
        
        # GPU Skinning components
        self.gpu_skinning_ready = False
        self.skinned_meshes: List[SkinnedMesh] = [] if GPU_SKINNING_AVAILABLE else []
        self.shader: Optional[SkinningShader] = None
        self.bone_matrices: List[np.ndarray] = []  # Final bone matrices for GPU
        
        # Cached matrices for efficiency
        self._model_matrix = np.eye(4, dtype=np.float32)
        self._view_matrix = np.eye(4, dtype=np.float32)
        self._projection_matrix = np.eye(4, dtype=np.float32)
    
    def add_mesh(self, mesh: Mesh):
        """Add mesh to model"""
        self.meshes.append(mesh)
        # GPU mesh will be created during initialize_gpu_skinning()
    
    def initialize_gpu_skinning(self):
        """
        Initialize GPU skinning - call after OpenGL context is ready
        This sets up shaders and GPU buffers for all meshes
        """
        if not GPU_SKINNING_AVAILABLE:
            logger.warning("GPU skinning not available, using legacy rendering")
            return False
        
        try:
            # Get or create shader
            self.shader = get_skinning_shader()
            if not self.shader.initialize():
                logger.error("Failed to initialize GPU skinning shader")
                return False
            
            # Update skeleton to compute bone matrices before creating GPU meshes
            self.update_skeleton()
            logger.info(f"Updated skeleton - computed {len(self.bone_matrices)} bone matrices")
            
            # Create GPU meshes for all loaded meshes
            self.skinned_meshes = []
            for i, mesh in enumerate(self.meshes):
                skinned_mesh = SkinnedMesh()
                skinned_mesh.setup(
                    vertices=mesh.vertices,
                    normals=mesh.normals,
                    uvs=mesh.uvs,
                    indices=mesh.indices,
                    bone_weights=mesh.bone_weights if len(mesh.bone_weights) > 0 else None,
                    bone_indices=mesh.bone_indices if len(mesh.bone_indices) > 0 else None
                )
                skinned_mesh.texture_id = mesh.texture_id
                skinned_mesh.color = mesh.color
                self.skinned_meshes.append(skinned_mesh)
                logger.debug(f"Created GPU skinned mesh {i}: {len(mesh.vertices)//3} verts, skinning={skinned_mesh.has_skinning}")
            
            self.gpu_skinning_ready = True
            logger.info(f"GPU skinning initialized with {len(self.skinned_meshes)} meshes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPU skinning: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
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
        """Update bone transformations and compute final matrices for GPU"""
        if not self.bones:
            return
        
        # Update bone transforms in hierarchy order
        self._update_bone_hierarchy()
        
        # Compute final bone matrices ordered by JOINT INDEX (not node index)
        # Mesh bone_indices reference joint indices from skin.joints array
        self.bone_matrices = []
        
        if hasattr(self, 'joint_indices') and len(self.joint_indices) > 0:
            # GPU skinning: Build matrices ordered by joint index
            # Match CPU skinning: transpose IBM for NumPy, then transpose result for OpenGL
            for joint_idx, node_idx in enumerate(self.joint_indices):
                if node_idx < len(self.bones):
                    bone = self.bones[node_idx]
                    # Transpose IBM from GLTF column-major to NumPy row-major
                    ibm_transposed = self.inverse_bind_matrices[joint_idx].T
                    # Compute skin matrix in row-major
                    skin_matrix = bone.world_matrix @ ibm_transposed
                    # Transpose to column-major for OpenGL
                    final_matrix = skin_matrix.T.astype(np.float32)
                    self.bone_matrices.append(final_matrix)
                else:
                    # Missing bone - use identity
                    self.bone_matrices.append(np.eye(4, dtype=np.float32))
        else:
            # Legacy CPU skinning: Use node order
            for bone in self.bones:
                final_matrix = bone.world_matrix @ bone.inverse_bind_matrix
                self.bone_matrices.append(final_matrix.astype(np.float32))
    
    def update_idle_animation(self, delta_time: float, mouse_x: float = 0.5, mouse_y: float = 0.5):
        """Update idle animation with mouse tracking
        
        Args:
            delta_time: Time since last frame in seconds
            mouse_x: Mouse X position normalized 0-1 (0=left, 1=right)
            mouse_y: Mouse Y position normalized 0-1 (0=top, 1=bottom)
        """
        import math
        
        self.animation_time += delta_time
        t = self.animation_time
        
        animation_changed = False
        
        try:
            for bone in self.bones:
                bone_lower = bone.name.lower()
                base_rotation = self.base_pose_rotations.get(bone.name)
                
                if base_rotation is None:
                    continue  # Skip bones without base pose
                
                # Head - follows mouse cursor subtly
                if "j_bip_c_head" in bone_lower:
                    # Convert mouse position to angles
                    # Head should LOOK AT cursor position:
                    # X: 0 = left edge (look left), 0.5 = center, 1 = right edge (look right)
                    # Y: 0 = top edge (look up), 0.5 = center, 1 = bottom edge (look down)
                    max_yaw = 0.52  # ±30 degrees in radians
                    max_pitch = 0.35  # ±20 degrees in radians
                    
                    # Calculate target angles
                    # When cursor moves right, head looks right (positive yaw)
                    target_yaw = (mouse_x - 0.5) * 2.0 * max_yaw
                    # When cursor moves down, head looks down (negative pitch)
                    target_pitch = (mouse_y - 0.5) * 2.0 * max_pitch
                    
                    # Smooth damping for natural movement
                    if not hasattr(bone, 'current_yaw'):
                        bone.current_yaw = 0.0
                        bone.current_pitch = 0.0
                    
                    smoothing = 0.8  # Lower = smoother, higher = more responsive
                    bone.current_yaw += (target_yaw - bone.current_yaw) * smoothing
                    bone.current_pitch += (target_pitch - bone.current_pitch) * smoothing
                    
                    # Create rotation quaternions
                    qx = np.array([math.sin(bone.current_pitch/2), 0.0, 0.0, math.cos(bone.current_pitch/2)], dtype=np.float32)
                    qy = np.array([0.0, math.sin(bone.current_yaw/2), 0.0, math.cos(bone.current_yaw/2)], dtype=np.float32)
                    bone.animation_rotation = self._quaternion_multiply(qy, qx)
                    animation_changed = True
                
                # Skip hips - it rotates the entire body
                # elif "j_bip_c_hips" in bone_lower:
                #     pass
                
                # Skip shoulders for performance - CPU skinning is too slow
                # elif "j_bip_l_shoulder" in bone_lower or "j_bip_r_shoulder" in bone_lower:
                #     pass
        
        except Exception as e:
            logger.warning(f"Idle animation update error: {e}")
        
        # Update bone matrices for GPU or CPU rendering
        if animation_changed:
            self.update_skeleton()
            
            # Only apply CPU skinning if GPU skinning is not available
            if not (self.gpu_skinning_ready and GPU_SKINNING_AVAILABLE):
                # Apply CPU skinning only to head and descendants for performance
                if hasattr(self, 'inverse_bind_matrices') and self.inverse_bind_matrices is not None:
                    head_bones = []
                    for bone in self.bones:
                        if 'head' in bone.name.lower():
                            head_bones.append(bone.name)
                            self._add_bone_descendants(bone, head_bones)
                            break
                    self._apply_skinning(only_bones=head_bones if head_bones else None)
    
    def _add_bone_descendants(self, bone, bone_list):
        """Recursively add all descendant bones to the list"""
        for child in bone.children:
            bone_list.append(child.name)
            self._add_bone_descendants(child, bone_list)
    
    @staticmethod
    def _quaternion_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """Multiply two quaternions (q1 * q2)"""
        x1, y1, z1, w1 = q1
        x2, y2, z2, w2 = q2
        
        return np.array([
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2,
            w1*w2 - x1*x2 - y1*y2 - z1*z2
        ], dtype=np.float32)
    
    def _update_bone_hierarchy(self, bone_idx=None, parent_matrix=None):
        """Recursively update bone transforms in hierarchy"""
        if bone_idx is None:
            # Create bone-to-index lookup for O(1) access
            if not hasattr(self, '_bone_to_idx'):
                self._bone_to_idx = {bone: idx for idx, bone in enumerate(self.bones)}
            
            # Start from root bones (those with no parent)
            for idx, bone in enumerate(self.bones):
                if bone.parent_idx == -1:
                    self._update_bone_hierarchy(idx, None)
        else:
            bone = self.bones[bone_idx]
            bone.calculate_transform(parent_matrix)
            
            # Update children
            for child in bone.children:
                child_idx = self._bone_to_idx.get(child, -1)
                if child_idx >= 0:
                    self._update_bone_hierarchy(child_idx, bone.world_matrix)
    
    def _apply_skinning(self, only_bones=None):
        """Apply bone transforms to mesh vertices (CPU skinning)
        
        glTF skinning formula: skinned = sum(weight * jointMatrix * IBM * vertex)
        Where jointMatrix is the CURRENT world transform of the joint.
        
        For proper hierarchical skinning:
        1. Compute animated world transform for each joint (respecting hierarchy)
        2. Skin matrix = animated_world @ IBM
        """
        if not self.bones or not self.joint_indices:
            logger.warning("Cannot apply skinning: no bones or joint mapping")
            return
        
        if not hasattr(self, 'inverse_bind_matrices') or self.inverse_bind_matrices is None:
            logger.warning("Cannot apply skinning: no inverse bind matrices")
            return
        
        # Step 1: Compute animated world transforms for all joints (hierarchically)
        # Start from bind pose (identity) and apply animation rotations
        animated_world_transforms = {}  # joint_idx -> 4x4 matrix
        
        # Build joint hierarchy map
        joint_to_node = {j: self.joint_indices[j] for j in range(len(self.joint_indices))}
        node_to_joint = {v: k for k, v in joint_to_node.items()}
        
        # Get bind pose transforms from IBM
        bind_transforms = {}  # joint_idx -> bind world transform
        for j in range(len(self.joint_indices)):
            ibm = self.inverse_bind_matrices[j].T  # Transpose for numpy
            bind_transforms[j] = np.linalg.inv(ibm)
        
        def get_parent_joint(joint_idx):
            """Get parent joint index, or -1 if no parent"""
            node_idx = self.joint_indices[joint_idx]
            if node_idx < len(self.bones):
                parent_node = self.bones[node_idx].parent_idx
                if parent_node in node_to_joint:
                    return node_to_joint[parent_node]
            return -1
        
        def compute_animated_world(joint_idx, visited=None):
            """Recursively compute animated world transform"""
            if visited is None:
                visited = set()
            if joint_idx in visited:
                return np.eye(4, dtype=np.float32)
            visited.add(joint_idx)
            
            if joint_idx in animated_world_transforms:
                return animated_world_transforms[joint_idx]
            
            node_idx = self.joint_indices[joint_idx]
            bone = self.bones[node_idx] if node_idx < len(self.bones) else None
            
            # Get this joint's local animation rotation (if any)
            local_anim = np.eye(4, dtype=np.float32)
            if bone and hasattr(bone, 'animation_rotation') and bone.animation_rotation is not None:
                local_anim = Bone._trs_to_matrix(
                    np.zeros(3, dtype=np.float32),
                    bone.animation_rotation,
                    np.ones(3, dtype=np.float32)
                )
            
            # Get parent's animated world transform
            parent_joint = get_parent_joint(joint_idx)
            if parent_joint >= 0:
                parent_world = compute_animated_world(parent_joint, visited)
                # Get bind pose local transform (relative to parent)
                parent_bind = bind_transforms.get(parent_joint, np.eye(4))
                this_bind = bind_transforms.get(joint_idx, np.eye(4))
                
                # Local bind = inv(parent_bind) @ this_bind
                local_bind = np.linalg.inv(parent_bind) @ this_bind
                
                # Animated world = parent_world @ local_bind @ local_anim
                animated_world = parent_world @ local_bind @ local_anim
            else:
                # Root joint - world = bind @ local_anim
                animated_world = bind_transforms.get(joint_idx, np.eye(4)) @ local_anim
            
            animated_world_transforms[joint_idx] = animated_world.astype(np.float32)
            return animated_world_transforms[joint_idx]
        
        # Compute animated world transforms for all joints
        for j in range(len(self.joint_indices)):
            compute_animated_world(j)
        
        # Step 2: Compute skin matrices
        skin_matrices = []
        animated_count = 0
        for j in range(len(self.joint_indices)):
            ibm = self.inverse_bind_matrices[j].T
            animated_world = animated_world_transforms.get(j, bind_transforms[j])
            
            # Skin matrix = animated_world @ IBM
            skin_matrix = animated_world @ ibm
            
            # Check if this joint is animated
            node_idx = self.joint_indices[j]
            if node_idx < len(self.bones):
                bone = self.bones[node_idx]
                if hasattr(bone, 'animation_rotation') and bone.animation_rotation is not None:
                    animated_count += 1
            
            skin_matrices.append(skin_matrix.astype(np.float32))
        
        # Build set of joint indices to update (if only_bones specified)
        update_joints = None
        if only_bones:
            update_joints = set()
            for bone_name in only_bones:
                for j, joint_idx in enumerate(self.joint_indices):
                    if joint_idx < len(self.bones) and self.bones[joint_idx].name == bone_name:
                        update_joints.add(j)
        
        # Apply skinning to all meshes
        for mesh_idx, mesh in enumerate(self.meshes):
            if len(mesh.bone_weights) == 0 or len(mesh.bone_indices) == 0:
                mesh.skinned_vertices = None
                continue
            
            num_verts = len(mesh.vertices) // 3
            explosion_count = 0
            skinned_verts = np.zeros_like(mesh.vertices, dtype=np.float32)
            explosion_count = 0
            
            try:
                for v_idx in range(num_verts):
                    # Skip this vertex if we're only updating specific bones and this vertex isn't influenced by them
                    if update_joints is not None:
                        vertex_affected = False
                        for influence in range(4):
                            weight = mesh.bone_weights[v_idx, influence]
                            if weight > 0.001:
                                joint_idx = int(mesh.bone_indices[v_idx, influence])
                                if joint_idx in update_joints:
                                    vertex_affected = True
                                    break
                        if not vertex_affected:
                            # Copy existing vertex position
                            if mesh.skinned_vertices is not None:
                                skinned_verts[v_idx*3:v_idx*3+3] = mesh.skinned_vertices[v_idx*3:v_idx*3+3]
                            else:
                                skinned_verts[v_idx*3:v_idx*3+3] = mesh.vertices[v_idx*3:v_idx*3+3]
                            continue
                    
                    orig_vert = np.array([mesh.vertices[v_idx*3], 
                                          mesh.vertices[v_idx*3+1], 
                                          mesh.vertices[v_idx*3+2]], dtype=np.float32)
                    vert4 = np.array([orig_vert[0], orig_vert[1], orig_vert[2], 1.0], dtype=np.float32)
                    
                    skinned_vert = np.zeros(3, dtype=np.float32)
                    total_weight = 0.0
                    
                    for influence in range(4):
                        weight = mesh.bone_weights[v_idx, influence]
                        if weight <= 0.001:
                            continue
                        
                        joint_idx = int(mesh.bone_indices[v_idx, influence])
                        if joint_idx >= len(skin_matrices):
                            continue
                        
                        transformed = skin_matrices[joint_idx] @ vert4
                        skinned_vert += weight * transformed[:3]
                        total_weight += weight
                    
                    if total_weight > 0.001:
                        result = skinned_vert / total_weight
                        
                        # Check for explosion
                        diff = np.abs(result - orig_vert)
                        if np.any(diff > 5.0):  # More sensitive threshold
                            explosion_count += 1
                            if explosion_count <= 3:
                                logger.warning(f"Vertex {v_idx}: orig={orig_vert}, result={result}, diff max={diff.max():.2f}")
                            result = orig_vert  # Fallback
                        skinned_verts[v_idx*3:v_idx*3+3] = result
                    else:
                        skinned_verts[v_idx*3:v_idx*3+3] = orig_vert
                
                if explosion_count > 0:
                    logger.warning(f"Mesh {mesh_idx}: {explosion_count}/{num_verts} vertices exploded")
                    mesh.skinned_vertices = None
                else:
                    mesh.skinned_vertices = skinned_verts
                
            except Exception as e:
                logger.error(f"Error skinning mesh {mesh_idx}: {e}")
                mesh.skinned_vertices = None
    
    def render(self, view_matrix: np.ndarray = None, projection_matrix: np.ndarray = None):
        """Render the model using GPU skinning or legacy fallback"""
        
        # Use GPU skinning with fixed bone index mapping
        if self.gpu_skinning_ready and self.shader and GPU_SKINNING_AVAILABLE:
            self._render_gpu(view_matrix, projection_matrix)
        else:
            self._render_legacy()
    
    def _render_gpu(self, view_matrix: np.ndarray = None, projection_matrix: np.ndarray = None):
        """Render with GPU skinning shaders"""
        try:
            # Activate shader
            self.shader.use()
            
            # Get matrices from OpenGL if not provided
            if view_matrix is None:
                view_matrix = np.array(glGetFloatv(GL_MODELVIEW_MATRIX), dtype=np.float32).reshape(4, 4)
            if projection_matrix is None:
                projection_matrix = np.array(glGetFloatv(GL_PROJECTION_MATRIX), dtype=np.float32).reshape(4, 4)
            
            # Model matrix is identity (transformations already in modelview)
            model_matrix = np.eye(4, dtype=np.float32)
            
            # Set MVP matrices
            self.shader.set_matrices(model_matrix, view_matrix, projection_matrix)
            
            # Set lighting
            self.shader.set_lighting(
                light_dir=(1.0, 1.0, 1.0),
                light_color=(0.8, 0.8, 0.8),
                ambient_color=(0.4, 0.4, 0.4)
            )
            
            # Upload bone matrices
            if self.bone_matrices and self.skinning_enabled:
                self.shader.set_bone_matrices(self.bone_matrices)
                # Debug: log once
                if not hasattr(self, '_logged_bone_upload'):
                    self._logged_bone_upload = True
                    logger.info(f"GPU: Uploading {len(self.bone_matrices)} bone matrices to shader")
                    # Check if arm bones have rotation
                    for i, bone in enumerate(self.bones):
                        if 'UpperArm' in bone.name:
                            logger.info(f"  Arm bone {bone.name}: rotation={bone.rotation}, matrix[0,0:3]={self.bone_matrices[i][0,:3]}")
            
            # Render all skinned meshes
            for skinned_mesh in self.skinned_meshes:
                skinned_mesh.render(self.shader)
            
            # Deactivate shader
            self.shader.unuse()
            
        except Exception as e:
            logger.error(f"GPU render error: {e}")
            # Fallback to legacy
            self._render_legacy()
    
    def _render_legacy(self):
        """Legacy immediate mode rendering (fallback)"""
        from OpenGL.GL import glColor4f
        
        # Debug: count frames
        if not hasattr(self, '_frame_count'):
            self._frame_count = 0
        self._frame_count += 1
        if self._frame_count % 300 == 1:  # Log every ~5 seconds at 60fps
            logger.info(f"_render_legacy: rendering {len(self.meshes)} meshes")
        
        # Render all meshes with legacy path
        bone_matrices = [bone.world_matrix @ bone.inverse_bind_matrix for bone in self.bones] if self.bones else None
        for mesh in self.meshes:
            mesh.render(bone_matrices)


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
                        
                        # Get bone weights and indices for skinning
                        if 'JOINTS_0' in primitive.attributes.__dict__ and 'WEIGHTS_0' in primitive.attributes.__dict__:
                            joints_accessor_idx = primitive.attributes.JOINTS_0
                            joints_data = ModelLoader._get_accessor_data(gltf, joints_accessor_idx)
                            
                            weights_accessor_idx = primitive.attributes.WEIGHTS_0
                            weights_data = ModelLoader._get_accessor_data(gltf, weights_accessor_idx)
                            
                            if joints_data is not None and weights_data is not None:
                                # Ensure shape is (num_verts, 4)
                                num_verts = len(mesh.vertices) // 3
                                mesh.bone_indices = joints_data.reshape(num_verts, 4).astype(np.uint16)
                                mesh.bone_weights = weights_data.reshape(num_verts, 4).astype(np.float32)
                                logger.debug(f"Loaded skinning data: {num_verts} vertices with 4 bone influences each")
                        
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
            
            # Load bones/nodes for skeletal animation
            if gltf.nodes:
                ModelLoader._load_bones(gltf, model)
            
            # Load skin data (inverse bind matrices)
            if gltf.skins:
                ModelLoader._load_skins(gltf, model)
            
            # Initialize skeleton but DON'T apply CPU skinning
            # GPU skinning needs bind-pose vertices, not pre-skinned ones
            if model.bones and model.joint_indices:
                model.update_skeleton()
                logger.info("Skeleton initialized - vertices remain in bind pose for GPU skinning")
            
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
    def _load_bones(gltf, model: Model3D):
        """Load bone hierarchy from GLTF nodes"""
        try:
            bone_map = {}
            
            # Parse all nodes as potential bones
            for idx, node in enumerate(gltf.nodes):
                bone = Bone(node.name if node.name else f"Bone_{idx}")
                
                # Set position if available
                if node.translation:
                    bone.position = np.array(node.translation, dtype=np.float32)
                
                # Set rotation if available (quaternion)
                if node.rotation:
                    bone.rotation = np.array(node.rotation, dtype=np.float32)
                
                # Set scale if available
                if node.scale:
                    bone.scale = np.array(node.scale, dtype=np.float32)
                
                bone_map[idx] = bone
                model.add_bone(bone)
            
            # Set up parent-child relationships
            for idx, node in enumerate(gltf.nodes):
                if node.children:
                    bone = bone_map[idx]
                    for child_idx in node.children:
                        if child_idx in bone_map:
                            bone.children.append(bone_map[child_idx])
                            bone_map[child_idx].parent_idx = idx
            
            # Apply natural pose to transition from T-pose
            ModelLoader._apply_natural_pose(model)
            
            # Mark bones as initialized
            model.bones_initialized = True
            
            logger.info(f"Loaded {len(model.bones)} bones from VRM")
            
        except Exception as e:
            logger.warning(f"Could not load bones: {e}")
    
    @staticmethod
    @staticmethod
    @staticmethod
    def _apply_natural_pose(model: Model3D):
        """Apply natural idle pose to the model
        
        Transforms character from T-pose to a relaxed standing position.
        This sets the BASE pose - idle animation is added on top via update_idle_animation().
        
        VRM coordinate system: Y-up (height), Z-forward (front), X-right (side)
        """
        import math
        try:
            # Arms - need separate handling for left vs right due to mirroring
            arm_angle = math.radians(-75)  # Lower arms 75° from T-pose
            
            for bone in model.bones:
                bone_lower = bone.name.lower()
                
                # Left upper arm - positive Z rotation lowers left arm
                if "j_bip_l_upperarm" in bone_lower or "leftupperarm" in bone_lower:
                    bone.animation_rotation = np.array([
                        0.0, 0.0, 
                        math.sin(arm_angle/2), 
                        math.cos(arm_angle/2)
                    ], dtype=np.float32)
                    model.base_pose_rotations[bone.name] = bone.animation_rotation.copy()
                    logger.info(f"Set left arm pose for {bone.name}: {math.degrees(arm_angle):.1f}°")
                
                # Right upper arm - negative Z rotation lowers right arm (mirrored)
                elif "j_bip_r_upperarm" in bone_lower or "rightupperarm" in bone_lower:
                    bone.animation_rotation = np.array([
                        0.0, 0.0, 
                        -math.sin(arm_angle/2),  # Negated for right side
                        math.cos(arm_angle/2)
                    ], dtype=np.float32)
                    model.base_pose_rotations[bone.name] = bone.animation_rotation.copy()
                    logger.info(f"Set right arm pose for {bone.name}: {math.degrees(arm_angle):.1f}° (mirrored)")
                
                # Head - neutral base pose (animation will add tilt)
                elif "j_bip_c_head" in bone_lower or "head" == bone_lower:
                    bone.animation_rotation = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
                    model.base_pose_rotations[bone.name] = bone.animation_rotation.copy()
                
                # Hips - identity base pose (animation will override)
                elif "j_bip_c_hips" in bone_lower:
                    bone.animation_rotation = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
                    model.base_pose_rotations[bone.name] = bone.animation_rotation.copy()
                
                # Shoulders - identity base pose (animation will override)
                elif "j_bip_l_shoulder" in bone_lower or "j_bip_r_shoulder" in bone_lower:
                    bone.animation_rotation = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
                    model.base_pose_rotations[bone.name] = bone.animation_rotation.copy()
                
                # Hand curl
                elif ("j_bip_l_hand" in bone_lower or "j_bip_r_hand" in bone_lower or 
                      "lefthand" in bone_lower or "righthand" in bone_lower):
                    hand_angle = math.radians(10)
                    bone.animation_rotation = np.array([
                        0.0, 0.0, 
                        math.sin(hand_angle/2), 
                        math.cos(hand_angle/2)
                    ], dtype=np.float32)
                    model.base_pose_rotations[bone.name] = bone.animation_rotation.copy()
                    logger.info(f"Set hand curl for {bone.name}")
                
                # Finger curl
                elif any(finger in bone_lower for finger in ["index1", "middle1", "ring1", "little1", "thumb1"]):
                    finger_angle = math.radians(15)
                    bone.animation_rotation = np.array([
                        math.sin(finger_angle/2), 0.0, 0.0, 
                        math.cos(finger_angle/2)
                    ], dtype=np.float32)
                    model.base_pose_rotations[bone.name] = bone.animation_rotation.copy()
            
        except Exception as e:
            logger.warning(f"Could not apply natural pose: {e}")
            import traceback
            logger.warning(traceback.format_exc())
    
    @staticmethod
    def _load_skins(gltf, model: Model3D):
        """Load skin data - inverse bind matrices for skeletal animation"""
        try:
            for skin in gltf.skins:
                # Store joint-to-node mapping (CRITICAL for skinning!)
                # skin.joints[joint_idx] = node_idx
                # mesh bone_indices contain joint_idx, not node_idx
                model.joint_indices = list(skin.joints)
                logger.info(f"Skin has {len(skin.joints)} joints")
                
                # Get inverse bind matrices
                if skin.inverseBindMatrices is not None:
                    ibm_data = ModelLoader._get_accessor_data(gltf, skin.inverseBindMatrices)
                    if ibm_data is not None:
                        # Reshape to (num_joints, 4, 4) matrices
                        num_joints = len(skin.joints)
                        ibm_matrices = ibm_data.reshape(num_joints, 4, 4)
                        
                        # GLTF stores matrices in column-major order (OpenGL format)
                        # Keep them as-is - no transpose needed!
                        
                        # Store IBM per joint index (not per bone)
                        model.inverse_bind_matrices = ibm_matrices.astype(np.float32)
                        
                        # Also assign to bones for compatibility
                        for joint_idx, node_idx in enumerate(skin.joints):
                            if node_idx < len(model.bones):
                                model.bones[node_idx].inverse_bind_matrix = ibm_matrices[joint_idx]
                        
                        logger.info(f"Loaded {num_joints} inverse bind matrices from skin")
                
                # Only use first skin
                break
                
        except Exception as e:
            logger.warning(f"Could not load skin data: {e}")
    
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
