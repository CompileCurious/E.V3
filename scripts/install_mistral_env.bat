@echo off
REM Installer for Mistral 7B runtime dependencies

echo Updating pip...
python -m pip install --upgrade pip

echo Installing core packages (transformers, accelerate, bitsandbytes, safetensors, sentencepiece, vllm, psutil)...
python -m pip install transformers accelerate bitsandbytes safetensors sentencepiece vllm psutil

echo.
echo IMPORTANT: Install `torch` (PyTorch) separately to match your platform and CUDA.
echo If you have no NVIDIA GPU or want CPU-only builds, run:
echo   python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
echo
echo If you have an NVIDIA GPU (example for CUDA 11.8), run:
echo   python -m pip install torch --index-url https://download.pytorch.org/whl/cu118
echo
echo For other CUDA versions or platform-specific wheels, follow instructions at:
echo   https://pytorch.org/get-started/locally/

echo.
echo Installer finished. You may want to reboot your shell or activate your virtualenv again.
pause
