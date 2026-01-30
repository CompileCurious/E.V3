"""Renderer package with GPU skeletal animation support"""
from .model_loader import Model3D, ModelLoader, Mesh, Bone, BlendShape
from .opengl_renderer import OpenGLRenderer

# GPU Skinning (optional - may not be available on all systems)
try:
    from .gpu_skinning import SkinningShader, SkinnedMesh, get_skinning_shader
    GPU_SKINNING_AVAILABLE = True
except ImportError:
    GPU_SKINNING_AVAILABLE = False

__all__ = [
    'Model3D', 'ModelLoader', 'Mesh', 'Bone', 'BlendShape', 
    'OpenGLRenderer', 'GPU_SKINNING_AVAILABLE'
]

if GPU_SKINNING_AVAILABLE:
    __all__.extend(['SkinningShader', 'SkinnedMesh', 'get_skinning_shader'])
