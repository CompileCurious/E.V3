"""
Test script for VRM model loading
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.renderer.model_loader import ModelLoader
from loguru import logger

def test_vrm_loading():
    """Test loading the VRM file"""
    vrm_path = "models/character/E.V3.vrm"
    
    logger.info(f"Testing VRM loading from: {vrm_path}")
    
    # Check if file exists
    if not Path(vrm_path).exists():
        logger.error(f"VRM file not found: {vrm_path}")
        return False
    
    # Try to load
    model = ModelLoader.load_vrm(vrm_path)
    
    if model is None:
        logger.error("Failed to load VRM model")
        return False
    
    # Check what we got
    logger.info(f"Model loaded successfully!")
    logger.info(f"  Meshes: {len(model.meshes)}")
    
    for i, mesh in enumerate(model.meshes):
        vertex_count = len(mesh.vertices) // 3 if len(mesh.vertices) > 0 else 0
        index_count = len(mesh.indices)
        normal_count = len(mesh.normals) // 3 if len(mesh.normals) > 0 else 0
        
        logger.info(f"  Mesh {i+1}:")
        logger.info(f"    Vertices: {vertex_count}")
        logger.info(f"    Indices: {index_count}")
        logger.info(f"    Normals: {normal_count}")
        
        if vertex_count > 0:
            logger.info(f"    Sample vertex: {mesh.vertices[0:9]}")
    
    return True

if __name__ == "__main__":
    success = test_vrm_loading()
    sys.exit(0 if success else 1)
