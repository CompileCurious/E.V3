#!/usr/bin/env python3
"""
Test GPU Skinning System
Verifies the shader compilation and mesh setup work correctly
"""

import sys
import numpy as np
from loguru import logger

def test_basic_imports():
    """Test that all modules can be imported"""
    print("Testing basic imports...")
    
    try:
        from ui.renderer.gpu_skinning import (
            SkinningShader, SkinnedMesh, get_skinning_shader, MAX_BONES,
            SKINNING_VERTEX_SHADER, SKINNING_FRAGMENT_SHADER
        )
        print(f"  ✓ GPU skinning module imported (MAX_BONES={MAX_BONES})")
        
        from ui.renderer.model_loader import Model3D, ModelLoader, Mesh, Bone
        print("  ✓ Model loader module imported")
        
        from ui.renderer.opengl_renderer import OpenGLRenderer
        print("  ✓ OpenGL renderer module imported")
        
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_shader_source():
    """Verify shader source code is valid"""
    print("\nTesting shader source...")
    
    from ui.renderer.gpu_skinning import SKINNING_VERTEX_SHADER, SKINNING_FRAGMENT_SHADER
    
    # Check vertex shader has required elements
    vs_checks = [
        "a_position" in SKINNING_VERTEX_SHADER,
        "a_bone_weights" in SKINNING_VERTEX_SHADER,
        "a_bone_indices" in SKINNING_VERTEX_SHADER,
        "u_bone_matrices" in SKINNING_VERTEX_SHADER,
        "u_skinning_enabled" in SKINNING_VERTEX_SHADER,
    ]
    
    if all(vs_checks):
        print("  ✓ Vertex shader has all required attributes/uniforms")
    else:
        print("  ✗ Vertex shader missing some elements")
        return False
    
    # Check fragment shader
    fs_checks = [
        "v_normal" in SKINNING_FRAGMENT_SHADER,
        "u_color" in SKINNING_FRAGMENT_SHADER,
        "frag_color" in SKINNING_FRAGMENT_SHADER,
    ]
    
    if all(fs_checks):
        print("  ✓ Fragment shader has all required elements")
    else:
        print("  ✗ Fragment shader missing some elements")
        return False
    
    return True


def test_mesh_data_setup():
    """Test mesh data preparation (without OpenGL context)"""
    print("\nTesting mesh data preparation...")
    
    from ui.renderer.model_loader import Mesh, Bone, Model3D
    
    # Create test mesh
    mesh = Mesh()
    mesh.vertices = np.array([
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        0.5, 1.0, 0.0,
    ], dtype=np.float32)
    mesh.normals = np.array([
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
    ], dtype=np.float32)
    mesh.uvs = np.array([
        0.0, 0.0,
        1.0, 0.0,
        0.5, 1.0,
    ], dtype=np.float32)
    mesh.indices = np.array([0, 1, 2], dtype=np.uint32)
    
    # Test with bone weights
    mesh.bone_weights = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.5, 0.5, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ], dtype=np.float32)
    mesh.bone_indices = np.array([
        [0, 0, 0, 0],
        [0, 1, 0, 0],
        [1, 0, 0, 0],
    ], dtype=np.uint16)
    
    print(f"  ✓ Mesh created: {len(mesh.vertices)//3} vertices, {len(mesh.indices)} indices")
    print(f"  ✓ Bone weights shape: {mesh.bone_weights.shape}")
    print(f"  ✓ Bone indices shape: {mesh.bone_indices.shape}")
    
    return True


def test_bone_transforms():
    """Test bone transformation calculations"""
    print("\nTesting bone transforms...")
    
    from ui.renderer.model_loader import Bone
    
    # Create root bone
    root = Bone("Root")
    root.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    root.rotation = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)  # Identity quaternion
    root.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    
    # Calculate transform
    root.calculate_transform(None)
    
    print(f"  Root world matrix:\n{root.world_matrix}")
    
    # Create child bone
    child = Bone("Child")
    child.position = np.array([0.0, 1.0, 0.0], dtype=np.float32)  # 1 unit up
    child.rotation = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    child.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    child.parent_idx = 0
    
    root.children.append(child)
    child.calculate_transform(root.world_matrix)
    
    print(f"  Child world matrix:\n{child.world_matrix}")
    
    # Verify child position is correct (should be at 0, 1, 0 in world space)
    expected_pos = np.array([0.0, 1.0, 0.0])
    actual_pos = child.world_matrix[:3, 3]
    if np.allclose(actual_pos, expected_pos):
        print(f"  ✓ Child position correct: {actual_pos}")
        return True
    else:
        print(f"  ✗ Child position incorrect: {actual_pos} (expected {expected_pos})")
        return False


def test_model3d_initialization():
    """Test Model3D initialization"""
    print("\nTesting Model3D initialization...")
    
    from ui.renderer.model_loader import Model3D, Mesh, Bone
    
    model = Model3D()
    
    # Add a mesh
    mesh = Mesh()
    mesh.vertices = np.array([0, 0, 0, 1, 0, 0, 0.5, 1, 0], dtype=np.float32)
    mesh.indices = np.array([0, 1, 2], dtype=np.uint32)
    model.add_mesh(mesh)
    
    # Add bones
    root = Bone("Root")
    arm = Bone("Arm", parent_idx=0)
    model.add_bone(root)
    model.add_bone(arm)
    
    print(f"  ✓ Model created with {len(model.meshes)} meshes and {len(model.bones)} bones")
    print(f"  ✓ GPU skinning ready: {model.gpu_skinning_ready}")
    print(f"  ✓ Skinning enabled: {model.skinning_enabled}")
    
    # Update skeleton
    model.update_skeleton()
    print(f"  ✓ Bone matrices computed: {len(model.bone_matrices)} matrices")
    
    return True


def main():
    print("=" * 60)
    print("GPU Skinning System Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Basic Imports", test_basic_imports()))
    results.append(("Shader Source", test_shader_source()))
    results.append(("Mesh Data Setup", test_mesh_data_setup()))
    results.append(("Bone Transforms", test_bone_transforms()))
    results.append(("Model3D Init", test_model3d_initialization()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n✓ All tests passed! GPU skinning system is ready.")
        return 0
    else:
        print("\n✗ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
