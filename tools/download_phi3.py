"""
Download Phi-3 Mini model for faster LLM responses
Phi-3 is Microsoft's compact, efficient model similar to Copilot
"""
import urllib.request
import os
from pathlib import Path

MODEL_URL = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
MODEL_DIR = Path(__file__).parent.parent / "models" / "llm"
MODEL_PATH = MODEL_DIR / "Phi-3-mini-4k-instruct-q4.gguf"

def download_phi3():
    """Download Phi-3 model from HuggingFace"""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    if MODEL_PATH.exists():
        print(f"✓ Phi-3 model already exists at {MODEL_PATH}")
        return
    
    print(f"Downloading Phi-3 Mini model (~2.4GB)...")
    print(f"From: {MODEL_URL}")
    print(f"To: {MODEL_PATH}")
    print()
    
    def show_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 // total_size)
        bar_length = 50
        filled = int(bar_length * percent // 100)
        bar = '=' * filled + '-' * (bar_length - filled)
        print(f'\r[{bar}] {percent}% ({downloaded // 1024 // 1024}MB / {total_size // 1024 // 1024}MB)', end='')
    
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH, show_progress)
        print(f"\n\n✓ Phi-3 model downloaded successfully!")
        print(f"  Location: {MODEL_PATH}")
        print(f"\nTo use Phi-3, update config/config.yaml:")
        print('  model: "Phi-3-mini-4k-instruct-q4.gguf"')
    except Exception as e:
        print(f"\n✗ Error downloading model: {e}")
        print(f"\nManual download:")
        print(f"  1. Visit: {MODEL_URL}")
        print(f"  2. Save to: {MODEL_PATH}")

if __name__ == "__main__":
    download_phi3()
