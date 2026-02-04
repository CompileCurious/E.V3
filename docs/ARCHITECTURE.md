# E.V3 Microkernel Architecture

## Overview

E.V3 has been refactored into a **microkernel architecture** where a minimal core provides:

1. **Minimal event loop** - Simple main loop with signal handling
2. **Event bus** - Central message passing for module communication
3. **Permission checker** - Scoped storage and capability enforcement
4. **Module registry** - Lifecycle management (load/enable/disable/shutdown)

All functionality is implemented as **isolated capability modules** with explicit:
- Permission requirements
- Dependencies on other modules
- Lifecycle hooks
- Event subscriptions

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     E.V3 MICROKERNEL                        │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │  Event Bus (Central Communication)                │     │
│  │  - Event routing between modules                  │     │
│  │  - Subscription management                        │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │  Permission Checker                               │     │
│  │  - Grants/checks module permissions              │     │
│  │  - Scoped storage per module                     │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │  Module Registry                                  │     │
│  │  - Load/Enable/Disable/Shutdown lifecycle        │     │
│  │  - Dependency resolution                         │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │  Kernel API                                       │     │
│  │  - emit_event() / subscribe_event()              │     │
│  │  - read_config() / write_config()                │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Kernel API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  CAPABILITY MODULES                         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   State     │  │   Events    │  │    LLM      │        │
│  │   Module    │  │   Module    │  │   Module    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │  Calendar   │  │    IPC      │                          │
│  │   Module    │  │   Module    │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Module Interface

All modules implement the `Module` base class with:

### Lifecycle Methods

```python
def load(config: Dict[str, Any]) -> bool:
    """
    Initialize module with configuration
    - Parse config
    - Allocate resources
    - Prepare for enable
    """

def enable() -> bool:
    """
    Start active operations
    - Subscribe to events
    - Start background threads
    - Begin processing
    """

def disable() -> bool:
    """
    Pause operations
    - Stop processing
    - Pause threads
    - Keep resources allocated
    """

def shutdown() -> bool:
    """
    Release all resources
    - Stop threads
    - Close connections
    - Cleanup state
    """
```

### Capability Declaration

```python
def get_required_permissions() -> Set[Permission]:
    """Declare required permissions"""
    
def get_dependencies() -> Set[str]:
    """Declare module dependencies"""
```

### Event Handling

```python
def handle_event(event_type: str, event_data: Dict[str, Any]) -> None:
    """Handle events from event bus"""
```

## Permission Model

Modules must declare permissions. The kernel enforces these at runtime:

### Available Permissions

- **IPC_SEND** / **IPC_RECEIVE** - Inter-process communication
- **EVENT_EMIT** / **EVENT_SUBSCRIBE** - Event bus access
- **STORAGE_READ** / **STORAGE_WRITE** - Configuration storage
- **SYSTEM_EVENTS** / **SECURITY_EVENTS** - Windows event monitoring
- **CALENDAR_READ** - Calendar access
- **LLM_LOCAL** / **LLM_EXTERNAL** - LLM usage

### Scoped Storage

Each module has isolated configuration storage:

```python
kernel.read_config("module_name", "key")
kernel.write_config("module_name", "key", value)
```

## Capability Modules

### State Module

**Purpose**: Manages companion state machine (idle/scanning/alert/reminder)

**Permissions**:
- EVENT_EMIT - Emit state change events
- EVENT_SUBSCRIBE - Subscribe to transition requests
- STORAGE_READ/WRITE - Persist state data

**Dependencies**: None (fundamental module)

**Events Emitted**:
- `state.changed` - State transition occurred

**Events Subscribed**:
- `state.transition.alert` - Request alert state
- `state.transition.reminder` - Request reminder state
- `state.transition.scanning` - Request scanning state
- `state.transition.idle` - Request idle state

### Event Module

**Purpose**: Monitors Windows system events (Defender, Firewall)

**Permissions**:
- SYSTEM_EVENTS - Monitor system events
- SECURITY_EVENTS - Monitor security events
- EVENT_EMIT - Emit detected events
- STORAGE_READ - Read config

**Dependencies**: `state` (for triggering alerts)

**Events Emitted**:
- `system.defender` - Windows Defender event detected
- `system.firewall` - Firewall event detected

**Events Subscribed**: None

### LLM Module

**Purpose**: Local Mistral 7B and optional external LLM processing

**Permissions**:
- LLM_LOCAL - Use local LLM
- LLM_EXTERNAL - Use external LLM (when enabled)
- EVENT_EMIT - Emit responses
- EVENT_SUBSCRIBE - Subscribe to interpretation requests
- STORAGE_READ - Read config

**Dependencies**: `state` (for triggering alerts)

**Events Emitted**:
- `state.transition.alert` - Request alert with interpretation
- `ipc.send_message` - Send LLM response to UI

**Events Subscribed**:
- `system.defender` - Interpret defender event
- `system.firewall` - Interpret firewall event
- `ipc.user_message` - Process user query

### Calendar Module

**Purpose**: Monitor calendar for upcoming events and reminders

**Permissions**:
- CALENDAR_READ - Access calendar
- EVENT_EMIT - Emit reminders
- STORAGE_READ - Read config

**Dependencies**: `state` (for triggering reminders)

**Events Emitted**:
- `state.transition.reminder` - Calendar reminder

**Events Subscribed**: None

### IPC Module

**Purpose**: Inter-process communication with UI shell via named pipes

**Permissions**:
- IPC_SEND - Send messages to UI
- IPC_RECEIVE - Receive messages from UI
- EVENT_EMIT - Emit received messages
- EVENT_SUBSCRIBE - Subscribe to outbound messages
- STORAGE_READ - Read config

**Dependencies**: `state` (for relaying state to UI)

**Events Emitted**:
- `ipc.user_message` - User message received from UI
- `state.transition.idle` - User dismissed notification

**Events Subscribed**:
- `state.changed` - Forward state updates to UI
- `ipc.send_message` - Send message to UI

## Event Flow Examples

### Windows Defender Alert Flow

```
1. EventModule detects Windows Defender event
   └─> Emits: system.defender

2. LLMModule receives system.defender
   ├─> Interprets event with local LLM
   └─> Emits: state.transition.alert

3. StateModule receives state.transition.alert
   ├─> Transitions to ALERT state
   └─> Emits: state.changed

4. IPCModule receives state.changed
   └─> Sends state update to UI shell
```

### User Message Flow

```
1. User types message in UI shell
   └─> UI sends via named pipe

2. IPCModule receives message via pipe
   └─> Emits: ipc.user_message

3. LLMModule receives ipc.user_message
   ├─> Processes with LLM
   └─> Emits: ipc.send_message

4. IPCModule receives ipc.send_message
   └─> Sends response to UI via pipe
```

### Calendar Reminder Flow

```
1. CalendarModule checks upcoming events
   ├─> Finds event starting in 15 minutes
   └─> Emits: state.transition.reminder

2. StateModule receives state.transition.reminder
   ├─> Transitions to REMINDER state
   └─> Emits: state.changed

3. IPCModule receives state.changed
   └─> Sends reminder to UI shell
```

## Module Dependency Graph

```
         ┌──────────────┐
         │    State     │ ◄──── Fundamental module (no dependencies)
         │    Module    │
         └──────────────┘
                ▲
                │
    ┌───────────┼───────────┬───────────┬───────────┐
    │           │           │           │           │
┌───┴────┐  ┌──┴────┐  ┌───┴────┐  ┌──┴────┐  ┌───┴────┐
│ Events │  │  LLM  │  │Calendar│  │  IPC  │  │  (UI)  │
│ Module │  │Module │  │ Module │  │Module │  │        │
└────────┘  └───────┘  └────────┘  └───────┘  └────────┘
```

All modules depend on `state` except the state module itself.

## Configuration

Modules receive scoped configuration from global config file:

```yaml
# State module config
state_machine:
  initial_state: "idle"
  idle_timeout: 300

# Events module config  
events:
  windows_defender:
    enabled: true
    event_ids: [1116, 1117, 5001, 5010, 5012]
  firewall:
    enabled: true

# LLM module config
llm:
  local:
    enabled: true
    model: "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
  external:
    enabled: false

# Calendar module config
calendar:
  enabled: true
  provider: "outlook"
  check_interval: 300

# IPC module config
ipc:
  pipe_name: "\\\\.\\pipe\\E.V3.v2"
  buffer_size: 4096
```

## Privacy & Security Features

### Preserved from Original Design

1. **Local-first processing** - LLM runs locally by default
2. **No telemetry** - No data sent externally
3. **Event anonymization** - Personal data stripped from events
4. **Scoped storage** - Each module's data is isolated
5. **Permission boundaries** - Explicit capability grants

### Enhanced by Microkernel

1. **Module isolation** - Failures contained to individual modules
2. **Fine-grained permissions** - Each capability explicitly granted
3. **Event-based communication** - No direct module coupling
4. **Auditable interactions** - All inter-module communication logged

## Benefits of Microkernel Design

1. **Modularity** - Add/remove capabilities without kernel changes
2. **Testability** - Test modules in isolation
3. **Reliability** - Module failures don't crash kernel
4. **Security** - Permission boundaries enforced
5. **Maintainability** - Clear separation of concerns
6. **Extensibility** - New modules follow standard interface

## Adding New Modules

To add a new capability module:

1. **Inherit from Module base class**
   ```python
   from kernel.module import Module, Permission, KernelAPI
   
   class NewModule(Module):
       def __init__(self, kernel_api: KernelAPI):
           super().__init__("new_module", kernel_api)
   ```

2. **Implement required methods**
   - `get_required_permissions()`
   - `get_dependencies()`
   - `load()`, `enable()`, `disable()`, `shutdown()`
   - `handle_event()`

3. **Register in main_service.py**
   ```python
   new_module = NewModule(kernel_api)
   kernel.register_module(new_module)
   ```

4. **Add configuration**
   ```yaml
   new_module:
     enabled: true
     # module-specific config
   ```

## Directory Structure

```
E.V3/
├── kernel/                  # Microkernel core
│   ├── __init__.py
│   ├── kernel.py           # Kernel, EventBus, PermissionChecker
│   └── module.py           # Module interface, KernelAPI
│
├── modules/                 # Capability modules
│   ├── __init__.py
│   ├── state_module.py     # State machine
│   ├── event_module.py     # System event monitoring
│   ├── llm_module.py       # LLM processing
│   ├── calendar_module.py  # Calendar integration
│   └── ipc_module.py       # Inter-process communication
│
├── service/                 # Legacy implementations (used by modules)
│   ├── state/              # State machine implementation
│   ├── events/             # Event listeners
│   ├── llm/                # LLM providers
│   └── calendar/           # Calendar providers
│
├── ipc/                     # IPC implementation
├── ui/                      # UI shell (separate process)
├── config/                  # Configuration
├── models/                  # LLM and 3D models
└── main_service.py          # Service entrypoint
```

## Backwards Compatibility

The microkernel architecture **preserves all existing functionality**:

- Same configuration file format
- Same IPC protocol with UI
- Same event monitoring capabilities
- Same state machine behavior
- Same LLM and calendar features

**No features were invented or removed** - only reorganized into modular, permission-checked components.
