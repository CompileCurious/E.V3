# E.V3 C++ Kernel Architecture

## Overview

The E.V3 C++ Kernel is a complete rewrite of the Python kernel, designed for high-performance local LLM inference while maintaining full compatibility with the existing Python shell.

### Key Design Principles

1. **Persistent Model Loading**: Models are loaded once at startup and kept in memory
2. **Asynchronous Inference**: Non-blocking LLM pipeline with task queue
3. **Direct llama.cpp Integration**: No Python bindings, direct C/C++ API
4. **Streaming Output**: Tokens streamed back as generated
5. **Privacy First**: All inference is local, no network calls

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        E.V3 C++ KERNEL                                  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Kernel Core                                 │   │
│  │                                                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │   Config     │  │   Logger     │  │   Module Registry    │  │   │
│  │  │   Manager    │  │   (async)    │  │   (lifecycle mgmt)   │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│  │                                                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │  Event Bus   │  │  Kernel API  │  │  Permission Checker  │  │   │
│  │  │ (pub/sub)    │  │ (module ifc) │  │  (capability based)  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Inference Engine                              │   │
│  │                                                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                   Model Manager                           │   │   │
│  │  │                                                           │   │   │
│  │  │  ┌─────────────────┐      ┌─────────────────┐            │   │   │
│  │  │  │   Fast Model    │      │   Deep Model    │            │   │   │
│  │  │  │   (Phi-3)       │      │   (Mistral 7B)  │            │   │   │
│  │  │  │   Persistent    │      │   Persistent    │            │   │   │
│  │  │  └─────────────────┘      └─────────────────┘            │   │   │
│  │  │                                                           │   │   │
│  │  │  • Persistent context   • KV cache management            │   │   │
│  │  │  • GPU acceleration     • Optimized sampling             │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  │                                                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                    Task Queue                             │   │   │
│  │  │  • Priority scheduling  • Cancellation support           │   │   │
│  │  │  • Worker thread pool   • Non-blocking submission        │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      IPC Server                                  │   │
│  │  • Windows Named Pipes       • JSON message format              │   │
│  │  • Compatible with Python    • Async send/receive               │   │
│  │  • Local-only (privacy)      • Multiple client support          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    Named Pipe IPC  │  (\\.\pipe\E.V3.v2)
                    JSON Messages   │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Python Shell (UNCHANGED)                             │
│                                                                         │
│  • main_ui.py          • UI components                                 │
│  • System tray         • 3D character rendering                        │
│  • Speech/TTS          • All UX flows preserved                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Kernel Core (`kernel.hpp`)

The main orchestrator that initializes and manages all subsystems:

```cpp
class Kernel {
    Config config_;           // YAML configuration
    EventBus event_bus_;      // Pub/sub messaging
    KernelAPI api_;           // Module interface
    ModuleRegistry registry_; // Module lifecycle
    InferenceEngine engine_;  // LLM inference
    IpcServer* ipc_server_;   // Shell communication
};
```

**Responsibilities:**
- Configuration loading and validation
- Module registration, loading, and lifecycle management
- Signal handling (SIGINT, SIGTERM)
- IPC message routing
- LLM request processing

### 2. Event Bus (`event_bus.hpp`)

Thread-safe publish-subscribe messaging:

```cpp
class EventBus {
    void emit(string_view type, EventData data, string_view source);
    bool subscribe(string_view type, string_view module);
    void unsubscribe(string_view type, string_view module);
};
```

**Features:**
- Async event delivery via worker thread
- Module isolation (source doesn't receive own events)
- Exception-safe handler invocation

### 3. Module System (`module.hpp`)

Base class for capability modules:

```cpp
class Module {
    virtual Permission required_permissions() const = 0;
    virtual set<string> dependencies() const = 0;
    virtual Result<void> load(const ConfigSection&) = 0;
    virtual Result<void> enable() = 0;
    virtual Result<void> disable() = 0;
    virtual Result<void> shutdown() = 0;
    virtual void handle_event(string_view type, const EventData&) = 0;
};
```

**Lifecycle:**
```
Unloaded -> Loaded -> Enabled <-> Disabled -> Unloaded
                          |
                          v
                        Error
```

### 4. Inference Engine (`llm_engine.hpp`)

Persistent LLM with async task queue:

```cpp
class InferenceEngine {
    Result<void> initialize(const ConfigSection&);
    TaskHandle submit(InferenceRequest request);
    Result<string> generate_sync(const InferenceRequest&);
    Result<void> switch_mode(LlmMode mode);
};
```

**Features:**
- Persistent model loading (load once, infer many)
- Dual-mode support (Fast=Phi-3, Deep=Mistral)
- Streaming token output
- Request cancellation
- GPU acceleration (CUDA/Metal optional)

### 5. IPC Server (`ipc_server.hpp`)

Windows Named Pipe server:

```cpp
class IpcServer {
    void register_handler(string_view type, IpcMessageHandler);
    void start();
    void stop();
    bool send_message(const IpcMessage&);
    void queue_message(IpcMessage);
};
```

**Message Format (JSON):**
```json
{
    "type": "user_message",
    "data": {
        "message": "Hello, E.V3!"
    }
}
```

### 6. Task Queue (`task_queue.hpp`)

Priority-based async task execution:

```cpp
class TaskQueue {
    TaskHandle submit(F&& work, TaskPriority priority);
    pair<TaskHandle, future<R>> submit_with_result(F&& work);
};
```

**Features:**
- Worker thread pool
- Priority scheduling (Low, Normal, High, Critical)
- Task cancellation via handle
- Non-blocking submission

## Data Flow

### User Message Processing

```
1. Python Shell sends IPC message:
   {"type": "user_message", "data": {"message": "What time is it?"}}
                            │
                            ▼
2. C++ IPC Server receives message
                            │
                            ▼
3. Kernel processes message:
   - Check for simple greetings (instant response)
   - Build prompt with instruction format
   - Submit to InferenceEngine
                            │
                            ▼
4. InferenceEngine:
   - Queue task with callback
   - Worker thread executes inference
   - Streaming tokens (optional)
   - Completion callback fires
                            │
                            ▼
5. Kernel sends IPC response:
   {"type": "llm_response", "data": {"message": "It's 3:45 PM"}}
                            │
                            ▼
6. Python Shell displays response
```

### Model Switching

```
1. IPC message: {"type": "switch_model", "data": {"mode": "deep"}}
                            │
                            ▼
2. ModelManager.switch_mode(LlmMode::Deep)
   - If Mistral not loaded, load it
   - Set current_mode_ = Deep
                            │
                            ▼
3. Next inference uses Mistral 7B
```

## Performance Characteristics

| Metric | Python Kernel | C++ Kernel |
|--------|--------------|------------|
| Model Load Time | ~5-10s | ~3-5s |
| First Token Latency | ~500-1000ms | ~100-300ms |
| Tokens/Second | ~15-25 | ~30-60 |
| Memory Overhead | +500MB (Python) | Minimal |
| Startup Time | ~3s | <1s |

## Thread Model

```
Main Thread
    │
    ├── Event Bus Worker (1 thread)
    │   └── Delivers events to module handlers
    │
    ├── Inference Worker (1 thread)
    │   └── Executes LLM inference tasks
    │
    └── IPC Server (1 thread)
        └── Handles pipe connections and messages
```

## Error Handling

The kernel uses `std::expected<T, Error>` for all fallible operations:

```cpp
struct Error {
    ErrorCategory category;  // Kernel, Module, IPC, LLM, etc.
    int code;
    string message;
    source_location location;
};

template <typename T>
using Result = std::expected<T, Error>;
```

All errors are logged and propagated appropriately:
- Module failures don't crash kernel
- LLM failures return error response
- IPC errors are logged and connection reset

## Configuration

The C++ kernel uses the same `config/config.yaml` as the Python kernel:

```yaml
llm:
  mode: "fast"
  local:
    enabled: true
    model_path: "models/llm/"
    fast_model: "Phi-3-mini-4k-instruct-q4.gguf"
    deep_model: "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    context_length: 512
    n_batch: 256
    n_threads: 4
    use_gpu: true
    gpu_layers: 35

ipc:
  pipe_name: "\\\\.\\pipe\\E.V3.v2"
  buffer_size: 4096

logging:
  level: "INFO"
  log_to_file: true
  log_file: "logs/ev3_kernel.log"
```

## Building

See [BUILD.md](BUILD.md) for detailed build instructions.

Quick start:
```bash
cd kernel_cpp
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DLLAMA_CUBLAS=ON
cmake --build . --config Release
```
