# Building the E.V3 C++ Kernel

## Prerequisites

### Windows

- **CMake** 3.21 or later
- **Visual Studio 2022** with C++ workload (for MSVC compiler)
- **Git** (for fetching llama.cpp)
- **CUDA Toolkit** 12.x (optional, for GPU acceleration)

### Linux

- **CMake** 3.21 or later
- **GCC 12+** or **Clang 14+**
- **Git**
- **CUDA Toolkit** (optional)

## Quick Build

### Windows (Command Prompt)

```batch
cd kernel_cpp
mkdir build
cd build

:: CPU only
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release

:: With CUDA GPU support
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release -DLLAMA_CUBLAS=ON

:: Build
cmake --build . --config Release

:: Output: build/bin/EV3Kernel.exe
```

### Windows (PowerShell)

```powershell
cd kernel_cpp
New-Item -ItemType Directory -Force -Path build
Set-Location build

# CPU only
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release

# With CUDA
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release -DLLAMA_CUBLAS=ON

cmake --build . --config Release
```

### Linux

```bash
cd kernel_cpp
mkdir -p build && cd build

# CPU only
cmake .. -DCMAKE_BUILD_TYPE=Release

# With CUDA
cmake .. -DCMAKE_BUILD_TYPE=Release -DLLAMA_CUBLAS=ON

# Build
make -j$(nproc)
```

## Build Options

| Option | Default | Description |
|--------|---------|-------------|
| `CMAKE_BUILD_TYPE` | `Release` | Build type (Debug, Release, RelWithDebInfo) |
| `LLAMA_CUBLAS` | `OFF` | Enable CUDA GPU acceleration |
| `LLAMA_METAL` | `OFF` | Enable Metal GPU acceleration (macOS) |
| `LLAMA_CPP_DIR` | (empty) | Path to existing llama.cpp (skips fetch) |
| `BUILD_SHARED_LIBS` | `OFF` | Build as shared library |
| `EV3_BUILD_TESTS` | `OFF` | Build unit tests |

## Using Pre-built llama.cpp

If you have llama.cpp already built:

```bash
cmake .. -DLLAMA_CPP_DIR=/path/to/llama.cpp
```

## GPU Acceleration

### CUDA (NVIDIA)

1. Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
2. Ensure `nvcc` is in PATH
3. Build with `-DLLAMA_CUBLAS=ON`

```bash
cmake .. -DCMAKE_BUILD_TYPE=Release -DLLAMA_CUBLAS=ON
```

### Metal (Apple Silicon)

```bash
cmake .. -DCMAKE_BUILD_TYPE=Release -DLLAMA_METAL=ON
```

## Python Extension

To build the Python C extension module:

1. Ensure Python development files are installed:
   ```bash
   # Windows
   pip install pybind11
   
   # Linux
   sudo apt install python3-dev
   ```

2. CMake will automatically detect Python and build `ev3_kernel_cpp.pyd`

3. Copy to your Python environment:
   ```bash
   cp build/ev3_kernel_cpp.pyd path/to/your/project/
   ```

## Output Files

After building:

```
build/
├── bin/
│   ├── EV3Kernel.exe          # Main kernel executable
│   └── config/                 # Copied config files
├── libev3kernel.a              # Static library (Linux)
├── ev3kernel.lib               # Static library (Windows)
└── ev3_kernel_cpp.pyd          # Python extension (if built)
```

## Running

```bash
# From build directory
./bin/EV3Kernel.exe

# With custom config
./bin/EV3Kernel.exe -c /path/to/config.yaml
```

## Troubleshooting

### CMake can't find CUDA

Ensure CUDA Toolkit is installed and `nvcc` is in PATH:
```bash
nvcc --version
```

Set `CUDA_TOOLKIT_ROOT_DIR` if needed:
```bash
cmake .. -DCUDA_TOOLKIT_ROOT_DIR="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.0"
```

### llama.cpp fetch fails

If the automatic fetch fails, manually clone:
```bash
git clone https://github.com/ggerganov/llama.cpp.git ../llama.cpp
cmake .. -DLLAMA_CPP_DIR=../llama.cpp
```

### Missing Visual Studio components

Ensure you have the "Desktop development with C++" workload installed in Visual Studio Installer.

### Python extension not building

Check that Python development files are found:
```
-- Python found: C:/Python313/python.exe
-- Building Python extension module...
```

If not shown, install Python development files or set `Python3_ROOT_DIR`:
```bash
cmake .. -DPython3_ROOT_DIR="C:/Python313"
```
