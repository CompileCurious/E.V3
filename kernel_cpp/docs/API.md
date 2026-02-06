# E.V3 C++ Kernel API Reference

## Shell ↔ Kernel IPC Protocol

The Python shell communicates with the C++ kernel via Windows Named Pipes using JSON messages.

### Connection

- **Pipe Name**: `\\.\pipe\E.V3.v2` (configurable)
- **Mode**: Duplex, message-based
- **Encoding**: UTF-8 JSON

### Message Format

All messages follow this structure:

```json
{
    "type": "message_type",
    "data": {
        "key1": "value1",
        "key2": "value2"
    }
}
```

---

## Messages: Shell → Kernel

### `user_message`

Send a user query for LLM processing.

```json
{
    "type": "user_message",
    "data": {
        "message": "What is the weather like?"
    }
}
```

**Behavior:**
- Kernel checks for simple greetings (instant response)
- Otherwise, processes with LLM
- Response sent as `llm_response` message

---

### `dismiss`

Dismiss current alert/notification.

```json
{
    "type": "dismiss",
    "data": {}
}
```

**Behavior:**
- Kernel emits `state.transition.idle` event
- State machine transitions to idle

---

### `switch_model`

Switch between fast and deep LLM modes.

```json
{
    "type": "switch_model",
    "data": {
        "mode": "deep"
    }
}
```

**Parameters:**
- `mode`: `"fast"` (Phi-3) or `"deep"` (Mistral 7B)

**Behavior:**
- Loads target model if not already loaded
- Sets as active model for subsequent inference

---

### `get_status`

Query kernel status.

```json
{
    "type": "get_status",
    "data": {}
}
```

**Response:**
```json
{
    "type": "status",
    "data": {
        "running": "true",
        "llm_ready": "true",
        "llm_mode": "fast"
    }
}
```

---

## Messages: Kernel → Shell

### `llm_response`

LLM inference result.

```json
{
    "type": "llm_response",
    "data": {
        "message": "The weather is sunny and 72°F."
    }
}
```

---

### `state_update`

State machine state change.

```json
{
    "type": "state_update",
    "data": {
        "state": "alert",
        "message": "Windows Defender detected a threat",
        "priority": "2"
    }
}
```

**States:**
- `idle` - Default state
- `alert` - Security alert
- `reminder` - Calendar reminder
- `scanning` - System scan in progress

---

### `status`

Response to `get_status` request.

```json
{
    "type": "status",
    "data": {
        "running": "true",
        "llm_ready": "true",
        "llm_mode": "fast"
    }
}
```

---

### `token` (Streaming Mode)

Individual token during streaming generation.

```json
{
    "type": "token",
    "data": {
        "token": "Hello",
        "done": "false"
    }
}
```

When generation completes:
```json
{
    "type": "token",
    "data": {
        "token": "",
        "done": "true"
    }
}
```

---

## Python Integration

### Option 1: Native IPC (Recommended)

Use the existing `IPCClient` class unchanged:

```python
from ipc.native_pipe import IPCClient

client = IPCClient(pipe_name=r"\\.\pipe\E.V3.v2")
client.connect()

# Send message
client.send_message("user_message", {"message": "Hello!"})

# Register response handler
client.register_handler("llm_response", lambda data: print(data["message"]))
```

### Option 2: Python C Extension

If built with Python support, import the C++ kernel directly:

```python
import ev3_kernel_cpp as kernel

# Initialize
kernel.initialize("config/config.yaml")

# Start (non-blocking, runs in background)
kernel.start()

# Generate (blocking)
response = kernel.generate("What is 2+2?", max_tokens=50)
print(response)

# Switch mode
kernel.switch_mode("deep")

# Stop
kernel.stop()
```

### Option 3: Subprocess

Run the kernel as a separate process:

```python
import subprocess

kernel_proc = subprocess.Popen(
    ["bin/EV3Kernel.exe", "-c", "config/config.yaml"],
    creationflags=subprocess.CREATE_NO_WINDOW
)

# Connect via IPC
client = IPCClient()
client.connect()

# ... use client as normal ...

# Stop
kernel_proc.terminate()
```

---

## C++ API

### Kernel

```cpp
#include <ev3/ev3.hpp>

ev3::Kernel kernel;

// Initialize with config
auto result = kernel.initialize("config/config.yaml");
if (!result) {
    std::cerr << result.error().message << std::endl;
    return 1;
}

// Load and enable modules
kernel.load_modules();
kernel.enable_modules();

// Start (blocks)
kernel.start();
```

### Inference Engine

```cpp
// Direct inference
ev3::InferenceRequest request;
request.prompt = "[INST] Hello! [/INST]";
request.max_tokens = 100;
request.temperature = 0.7f;

auto result = kernel.inference_engine().generate_sync(request);
if (result) {
    std::cout << *result << std::endl;
}

// Async inference
request.on_complete = [](ev3::Result<std::string> result) {
    if (result) {
        std::cout << *result << std::endl;
    }
};

auto handle = kernel.inference_engine().submit(std::move(request));

// Cancel if needed
handle.cancel();
```

### Streaming

```cpp
request.on_token = [](std::string_view token) {
    std::cout << token << std::flush;
    return true;  // Continue generation
};

kernel.inference_engine().generate_sync(request);
```

### Custom Modules

```cpp
class MyModule : public ev3::Module {
public:
    MyModule(ev3::KernelAPI* api) : Module("mymodule", api) {}
    
    ev3::Permission required_permissions() const override {
        return ev3::Permission::EventEmit | ev3::Permission::EventSubscribe;
    }
    
    ev3::Result<void> load(const ev3::ConfigSection& config) override {
        // Initialize resources
        return {};
    }
    
    ev3::Result<void> enable() override {
        api()->subscribe_event(name(), "my.event");
        return {};
    }
    
    ev3::Result<void> disable() override {
        return {};
    }
    
    ev3::Result<void> shutdown() override {
        return {};
    }
    
    void handle_event(std::string_view type, const ev3::EventData& data) override {
        // Handle events
    }
};

// Register
kernel.register_module(std::make_unique<MyModule>(&kernel.api()));
```

---

## Error Codes

| Category | Code | Description |
|----------|------|-------------|
| Kernel | 1 | Initialization failed |
| Kernel | 2 | Already running |
| Module | 1 | Already registered |
| Module | 2 | Not found |
| Module | 3 | Dependency not registered |
| Module | 4 | Dependency not loaded |
| Module | 5 | Must be loaded first |
| LLM | 1 | Already loaded |
| LLM | 2 | Model file not found |
| LLM | 3 | Failed to load model |
| LLM | 4 | Failed to create context |
| LLM | 10 | Model not loaded |
| LLM | 11 | Tokenization failed |
| LLM | 12 | Prompt too long |
| LLM | 13 | Prompt evaluation failed |
| LLM | 14 | Token generation failed |
| Config | 1 | File not found |
| IPC | 1 | Connection failed |
| IPC | 2 | Send failed |
