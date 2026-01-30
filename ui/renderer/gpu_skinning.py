"""
GPU Skinning Shader System for VRM/GLTF Models
Implements skeletal animation on the GPU using GLSL shaders
"""

import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
from typing import Optional, List
from loguru import logger

# Maximum number of bones supported by the shader
MAX_BONES = 128

# Vertex Shader with Skeletal Animation
SKINNING_VERTEX_SHADER = """
#version 330

// Vertex attributes
layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_normal;
layout(location = 2) in vec2 a_texcoord;
layout(location = 3) in vec4 a_bone_weights;
layout(location = 4) in ivec4 a_bone_indices;

// Uniforms
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform mat4 u_bone_matrices[128];  // Max 128 bones
uniform bool u_skinning_enabled;

// Outputs to fragment shader
out vec3 v_normal;
out vec2 v_texcoord;
out vec3 v_position;

void main() {
    vec4 skinned_position;
    vec3 skinned_normal;
    
    if (u_skinning_enabled && (a_bone_weights.x + a_bone_weights.y + a_bone_weights.z + a_bone_weights.w) > 0.0) {
        // Apply skeletal animation
        mat4 bone_transform = mat4(0.0);
        
        // Blend bone transforms based on weights
        if (a_bone_weights.x > 0.0 && a_bone_indices.x >= 0 && a_bone_indices.x < 128) {
            bone_transform += a_bone_weights.x * u_bone_matrices[a_bone_indices.x];
        }
        if (a_bone_weights.y > 0.0 && a_bone_indices.y >= 0 && a_bone_indices.y < 128) {
            bone_transform += a_bone_weights.y * u_bone_matrices[a_bone_indices.y];
        }
        if (a_bone_weights.z > 0.0 && a_bone_indices.z >= 0 && a_bone_indices.z < 128) {
            bone_transform += a_bone_weights.z * u_bone_matrices[a_bone_indices.z];
        }
        if (a_bone_weights.w > 0.0 && a_bone_indices.w >= 0 && a_bone_indices.w < 128) {
            bone_transform += a_bone_weights.w * u_bone_matrices[a_bone_indices.w];
        }
        
        // Transform position and normal
        skinned_position = bone_transform * vec4(a_position, 1.0);
        skinned_normal = mat3(bone_transform) * a_normal;
    } else {
        // No skinning - use original position
        skinned_position = vec4(a_position, 1.0);
        skinned_normal = a_normal;
    }
    
    // Apply model-view-projection
    vec4 world_position = u_model * skinned_position;
    gl_Position = u_projection * u_view * world_position;
    
    // Pass to fragment shader
    v_position = world_position.xyz;
    v_normal = normalize(mat3(u_model) * skinned_normal);
    v_texcoord = a_texcoord;
}
"""

# Fragment Shader with Lighting
SKINNING_FRAGMENT_SHADER = """
#version 330

// Inputs from vertex shader
in vec3 v_normal;
in vec2 v_texcoord;
in vec3 v_position;

// Uniforms
uniform sampler2D u_texture;
uniform bool u_use_texture;
uniform vec4 u_color;
uniform vec3 u_light_dir;
uniform vec3 u_light_color;
uniform vec3 u_ambient_color;

// Output
out vec4 frag_color;

void main() {
    // Base color from texture or uniform
    vec4 base_color;
    if (u_use_texture) {
        base_color = texture(u_texture, v_texcoord);
    } else {
        base_color = u_color;
    }
    
    // Simple diffuse lighting
    vec3 normal = normalize(v_normal);
    vec3 light_dir = normalize(u_light_dir);
    float diff = max(dot(normal, light_dir), 0.0);
    
    // Combine lighting
    vec3 ambient = u_ambient_color * base_color.rgb;
    vec3 diffuse = diff * u_light_color * base_color.rgb;
    vec3 result = ambient + diffuse;
    
    frag_color = vec4(result, base_color.a);
}
"""

# Fallback simple shader (no skinning, for compatibility)
SIMPLE_VERTEX_SHADER = """
#version 120

attribute vec3 a_position;
attribute vec3 a_normal;
attribute vec2 a_texcoord;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;

varying vec3 v_normal;
varying vec2 v_texcoord;

void main() {
    gl_Position = u_projection * u_view * u_model * vec4(a_position, 1.0);
    v_normal = mat3(u_model) * a_normal;
    v_texcoord = a_texcoord;
}
"""

SIMPLE_FRAGMENT_SHADER = """
#version 120

varying vec3 v_normal;
varying vec2 v_texcoord;

uniform sampler2D u_texture;
uniform bool u_use_texture;
uniform vec4 u_color;

void main() {
    vec4 base_color;
    if (u_use_texture) {
        base_color = texture2D(u_texture, v_texcoord);
    } else {
        base_color = u_color;
    }
    
    // Simple lighting
    vec3 light_dir = normalize(vec3(1.0, 1.0, 1.0));
    float diff = max(dot(normalize(v_normal), light_dir), 0.0);
    vec3 result = (0.4 + 0.6 * diff) * base_color.rgb;
    
    gl_FragColor = vec4(result, base_color.a);
}
"""


class SkinningShader:
    """Manages GPU skinning shaders"""
    
    def __init__(self):
        self.program = None
        self.simple_program = None
        self.use_skinning = False
        self.initialized = False
        
        # Uniform locations
        self.u_model = -1
        self.u_view = -1
        self.u_projection = -1
        self.u_bone_matrices = -1
        self.u_skinning_enabled = -1
        self.u_texture = -1
        self.u_use_texture = -1
        self.u_color = -1
        self.u_light_dir = -1
        self.u_light_color = -1
        self.u_ambient_color = -1
    
    def initialize(self) -> bool:
        """Initialize shaders - call after OpenGL context is ready"""
        if self.initialized:
            return True
        
        try:
            # Try to compile skinning shader (OpenGL 3.3)
            self.program = self._compile_shader(SKINNING_VERTEX_SHADER, SKINNING_FRAGMENT_SHADER)
            if self.program:
                self.use_skinning = True
                self._get_uniform_locations()
                logger.info("GPU skinning shader initialized (OpenGL 3.3)")
            else:
                # Fallback to simple shader
                self.program = self._compile_shader(SIMPLE_VERTEX_SHADER, SIMPLE_FRAGMENT_SHADER)
                if self.program:
                    self.use_skinning = False
                    logger.warning("Fallback to simple shader (no GPU skinning)")
                else:
                    logger.error("Failed to compile any shaders")
                    return False
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Shader initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _compile_shader(self, vertex_source: str, fragment_source: str) -> Optional[int]:
        """Compile vertex and fragment shaders into a program"""
        try:
            vertex_shader = shaders.compileShader(vertex_source, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_source, GL_FRAGMENT_SHADER)
            program = shaders.compileProgram(vertex_shader, fragment_shader)
            return program
        except Exception as e:
            logger.warning(f"Shader compilation failed: {e}")
            return None
    
    def _get_uniform_locations(self):
        """Get locations of all uniforms"""
        if not self.program:
            return
        
        self.u_model = glGetUniformLocation(self.program, "u_model")
        self.u_view = glGetUniformLocation(self.program, "u_view")
        self.u_projection = glGetUniformLocation(self.program, "u_projection")
        self.u_bone_matrices = glGetUniformLocation(self.program, "u_bone_matrices")
        self.u_skinning_enabled = glGetUniformLocation(self.program, "u_skinning_enabled")
        self.u_texture = glGetUniformLocation(self.program, "u_texture")
        self.u_use_texture = glGetUniformLocation(self.program, "u_use_texture")
        self.u_color = glGetUniformLocation(self.program, "u_color")
        self.u_light_dir = glGetUniformLocation(self.program, "u_light_dir")
        self.u_light_color = glGetUniformLocation(self.program, "u_light_color")
        self.u_ambient_color = glGetUniformLocation(self.program, "u_ambient_color")
    
    def use(self):
        """Activate the shader program"""
        if self.program:
            glUseProgram(self.program)
    
    def unuse(self):
        """Deactivate the shader program"""
        glUseProgram(0)
    
    def set_matrices(self, model: np.ndarray, view: np.ndarray, projection: np.ndarray):
        """Set MVP matrices"""
        if self.u_model >= 0:
            glUniformMatrix4fv(self.u_model, 1, GL_FALSE, model.flatten())
        if self.u_view >= 0:
            glUniformMatrix4fv(self.u_view, 1, GL_FALSE, view.flatten())
        if self.u_projection >= 0:
            glUniformMatrix4fv(self.u_projection, 1, GL_FALSE, projection.flatten())
    
    def set_bone_matrices(self, bone_matrices: List[np.ndarray]):
        """Upload bone matrices to GPU"""
        if not self.use_skinning or self.u_bone_matrices < 0:
            return
        
        # Pack matrices into single array
        num_bones = min(len(bone_matrices), MAX_BONES)
        matrices_flat = np.zeros((MAX_BONES, 4, 4), dtype=np.float32)
        
        for i in range(num_bones):
            matrices_flat[i] = bone_matrices[i]
        
        # Upload to GPU
        glUniformMatrix4fv(self.u_bone_matrices, MAX_BONES, GL_FALSE, matrices_flat.flatten())
    
    def set_skinning_enabled(self, enabled: bool):
        """Enable/disable skinning in shader"""
        if self.u_skinning_enabled >= 0:
            glUniform1i(self.u_skinning_enabled, 1 if enabled else 0)
    
    def set_texture(self, texture_id: int, use_texture: bool):
        """Set texture uniform"""
        if self.u_texture >= 0:
            glActiveTexture(GL_TEXTURE0)
            if use_texture and texture_id:
                glBindTexture(GL_TEXTURE_2D, texture_id)
            glUniform1i(self.u_texture, 0)
        if self.u_use_texture >= 0:
            glUniform1i(self.u_use_texture, 1 if (use_texture and texture_id) else 0)
    
    def set_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Set base color"""
        if self.u_color >= 0:
            glUniform4f(self.u_color, r, g, b, a)
    
    def set_lighting(self, light_dir: tuple = (1, 1, 1), 
                     light_color: tuple = (0.8, 0.8, 0.8),
                     ambient_color: tuple = (0.4, 0.4, 0.4)):
        """Set lighting parameters"""
        if self.u_light_dir >= 0:
            glUniform3f(self.u_light_dir, *light_dir)
        if self.u_light_color >= 0:
            glUniform3f(self.u_light_color, *light_color)
        if self.u_ambient_color >= 0:
            glUniform3f(self.u_ambient_color, *ambient_color)
    
    def cleanup(self):
        """Release shader resources"""
        if self.program:
            glDeleteProgram(self.program)
            self.program = None
        self.initialized = False


class SkinnedMesh:
    """GPU-accelerated skinned mesh with VAO/VBO"""
    
    def __init__(self):
        self.vao = None
        self.vbo_positions = None
        self.vbo_normals = None
        self.vbo_texcoords = None
        self.vbo_bone_weights = None
        self.vbo_bone_indices = None
        self.ebo = None
        
        self.num_indices = 0
        self.texture_id = None
        self.color = (0.8, 0.8, 0.8, 1.0)
        self.has_skinning = False
        self.initialized = False
    
    def setup(self, vertices: np.ndarray, normals: np.ndarray, uvs: np.ndarray,
              indices: np.ndarray, bone_weights: np.ndarray = None, 
              bone_indices: np.ndarray = None):
        """Setup GPU buffers for the mesh"""
        
        # Ensure correct dtypes
        vertices = vertices.astype(np.float32)
        normals = normals.astype(np.float32) if len(normals) > 0 else np.zeros_like(vertices)
        uvs = uvs.astype(np.float32) if len(uvs) > 0 else np.zeros((len(vertices) // 3, 2), dtype=np.float32).flatten()
        indices = indices.astype(np.uint32)
        
        num_verts = len(vertices) // 3
        
        # Generate VAO
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # Position buffer (location 0)
        self.vbo_positions = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_positions)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        # Normal buffer (location 1)
        self.vbo_normals = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        
        # Texcoord buffer (location 2)
        self.vbo_texcoords = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_texcoords)
        glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(2)
        
        # Bone weights buffer (location 3)
        if bone_weights is not None and len(bone_weights) > 0:
            bone_weights = bone_weights.astype(np.float32).reshape(-1)  # Flatten to 1D
            self.vbo_bone_weights = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_bone_weights)
            glBufferData(GL_ARRAY_BUFFER, bone_weights.nbytes, bone_weights, GL_STATIC_DRAW)
            glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 0, None)
            glEnableVertexAttribArray(3)
            self.has_skinning = True
        else:
            # Default zero weights
            default_weights = np.zeros((num_verts, 4), dtype=np.float32).flatten()
            self.vbo_bone_weights = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_bone_weights)
            glBufferData(GL_ARRAY_BUFFER, default_weights.nbytes, default_weights, GL_STATIC_DRAW)
            glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 0, None)
            glEnableVertexAttribArray(3)
        
        # Bone indices buffer (location 4)
        if bone_indices is not None and len(bone_indices) > 0:
            bone_indices = bone_indices.astype(np.int32).reshape(-1)  # Flatten to 1D
            self.vbo_bone_indices = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_bone_indices)
            glBufferData(GL_ARRAY_BUFFER, bone_indices.nbytes, bone_indices, GL_STATIC_DRAW)
            glVertexAttribIPointer(4, 4, GL_INT, 0, None)  # Use IPointer for integers
            glEnableVertexAttribArray(4)
        else:
            # Default zero indices
            default_indices = np.zeros((num_verts, 4), dtype=np.int32).flatten()
            self.vbo_bone_indices = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_bone_indices)
            glBufferData(GL_ARRAY_BUFFER, default_indices.nbytes, default_indices, GL_STATIC_DRAW)
            glVertexAttribIPointer(4, 4, GL_INT, 0, None)
            glEnableVertexAttribArray(4)
        
        # Index buffer
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        
        self.num_indices = len(indices)
        
        # Unbind
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        
        self.initialized = True
        logger.debug(f"SkinnedMesh setup: {num_verts} vertices, {self.num_indices} indices, skinning={self.has_skinning}")
    
    def render(self, shader: SkinningShader):
        """Render the mesh using the skinning shader"""
        if not self.initialized or not self.vao:
            return
        
        # Set texture/color
        shader.set_texture(self.texture_id, self.texture_id is not None)
        if not self.texture_id:
            shader.set_color(*self.color)
        else:
            shader.set_color(1.0, 1.0, 1.0, 1.0)
        
        # Enable skinning if mesh has bone data
        shader.set_skinning_enabled(self.has_skinning)
        
        # Draw
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.num_indices, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
    
    def cleanup(self):
        """Release GPU resources"""
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])
        buffers = [self.vbo_positions, self.vbo_normals, self.vbo_texcoords,
                   self.vbo_bone_weights, self.vbo_bone_indices, self.ebo]
        for buf in buffers:
            if buf:
                glDeleteBuffers(1, [buf])
        self.initialized = False


# Global shader instance
_skinning_shader: Optional[SkinningShader] = None

def get_skinning_shader() -> SkinningShader:
    """Get or create the global skinning shader instance"""
    global _skinning_shader
    if _skinning_shader is None:
        _skinning_shader = SkinningShader()
    return _skinning_shader
