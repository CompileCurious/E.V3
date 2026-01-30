# GPU Skeletal Animation System

## Overview

This document describes the GPU-based skeletal animation (skinning) system implemented for the E.V3 desktop companion.

## Architecture

### Components

1. **[gpu_skinning.py](ui/renderer/gpu_skinning.py)** - Core GPU skinning system
   - `SkinningShader` - GLSL shader program management
   - `SkinnedMesh` - GPU buffer management with VAO/VBO
   - Vertex shader performs weighted bone transformations
   - Fragment shader handles lighting and texturing

2. **[model_loader.py](ui/renderer/model_loader.py)** - Model loading with skinning support
   - `Bone` class - Quaternion-based TRS transforms
   - `Mesh` class - Vertex data with bone weights/indices
   - `Model3D` class - Full model with GPU skinning initialization

3. **[opengl_renderer.py](ui/renderer/opengl_renderer.py)** - OpenGL rendering widget
   - OpenGL 3.3 Compatibility profile
   - Automatic fallback to legacy rendering

## How It Works

### Vertex Shader Skinning

The vertex shader performs skeletal animation on the GPU:

```glsl
// For each vertex, blend up to 4 bone influences
mat4 bone_transform = mat4(0.0);
bone_transform += weight_0 * bone_matrices[bone_index_0];
bone_transform += weight_1 * bone_matrices[bone_index_1];
bone_transform += weight_2 * bone_matrices[bone_index_2];
bone_transform += weight_3 * bone_matrices[bone_index_3];

// Apply skinning
vec4 skinned_position = bone_transform * vec4(position, 1.0);
vec3 skinned_normal = mat3(bone_transform) * normal;
```

### Bone Matrix Computation

Each frame, the CPU computes final bone matrices:

```python
for bone in bones:
    final_matrix = bone.world_matrix @ bone.inverse_bind_matrix
    bone_matrices.append(final_matrix)
```

These matrices are uploaded to the GPU as uniforms.

### Data Flow

1. **Load VRM** → Parse vertices, normals, UVs, bone weights, indices
2. **Initialize GPU** → Create VAO/VBOs, compile shaders
3. **Each Frame**:
   - Update bone transforms (apply animations)
   - Compute final bone matrices
   - Upload matrices to GPU
   - Render with shader

## Performance

| Method | Performance | Quality |
|--------|-------------|---------|
| CPU Skinning | ~5 FPS | Slow, can explode |
| GPU Skinning | 60+ FPS | Smooth, stable |

## Usage

The system initializes automatically when the OpenGL context is ready:

```python
# In initializeGL()
if model.initialize_gpu_skinning():
    logger.info("GPU skinning ready")
```

Rendering happens automatically:

```python
# In paintGL()
model.render(view_matrix, projection_matrix)
```

## Compatibility

- **OpenGL 3.3+**: Full GPU skinning with GLSL shaders
- **OpenGL 2.1**: Falls back to legacy immediate mode rendering

## Files Modified

- `ui/renderer/gpu_skinning.py` - NEW: GPU skinning shader system
- `ui/renderer/model_loader.py` - Updated: GPU skinning integration
- `ui/renderer/opengl_renderer.py` - Updated: OpenGL 3.3 + initialization
- `ui/renderer/__init__.py` - Updated: Export new classes

## Testing

Run the test suite:

```bash
python test_gpu_skinning.py
```

## Future Improvements

1. **Morph Targets/Blendshapes**: For facial expressions
2. **Animation Clips**: Load and play VRM animations
3. **IK Solver**: Inverse kinematics for procedural animation
4. **Physics**: Hair/cloth simulation
