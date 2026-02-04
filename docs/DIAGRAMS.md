# E.V3 System Diagrams

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Transparent Companion Window                 │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │                                                       │  │ │
│  │  │         OpenGL 3D Renderer                           │  │ │
│  │  │         - VRM/GLB Model                              │  │ │
│  │  │         - Bone Animations                            │  │ │
│  │  │         - Blendshapes                                │  │ │
│  │  │         - Real-time Updates                          │  │ │
│  │  │                                                       │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │         Animation Controller                         │  │ │
│  │  │         - Breathing, Blinking                        │  │ │
│  │  │         - State Poses                                │  │ │
│  │  │         - Expressions                                │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │         Message Overlay                              │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ IPC (Named Pipes)
                               │ JSON Messages
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKGROUND SERVICE                         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    State Machine                          │ │
│  │  ┌─────┐  ┌──────────┐  ┌───────┐  ┌──────────┐         │ │
│  │  │IDLE │─▶│SCANNING  │─▶│ALERT  │  │REMINDER  │         │ │
│  │  └─────┘  └──────────┘  └───────┘  └──────────┘         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   Event Listeners                         │ │
│  │  ┌──────────────┐  ┌──────────┐  ┌─────────────────┐    │ │
│  │  │   Defender   │  │ Firewall │  │  System Events  │    │ │
│  │  └──────────────┘  └──────────┘  └─────────────────┘    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    LLM Manager                            │ │
│  │  ┌──────────────────┐         ┌──────────────────┐       │ │
│  │  │  Local Mistral   │         │  External GPT    │       │ │
│  │  │  (Default)       │         │  (On "find out") │       │ │
│  │  └──────────────────┘         └──────────────────┘       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                 Calendar Integration                      │ │
│  │  ┌──────────────┐              ┌──────────────┐          │ │
│  │  │   Outlook    │              │    Google    │          │ │
│  │  └──────────────┘              └──────────────┘          │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────────┐
│Windows Event │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Anonymize &     │ ◀─── Privacy Control
│  Filter          │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Event Manager   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  State Machine   │──────┐
└──────┬───────────┘      │
       │                   │
       ▼                   ▼
┌──────────────────┐  ┌────────────┐
│   LLM Manager    │  │ IPC Server │
│                  │  └─────┬──────┘
│  ┌────────────┐  │        │
│  │Local Model │  │        │ Named Pipe
│  └────────────┘  │        │
│                  │        ▼
│  ┌────────────┐  │  ┌────────────┐
│  │External API│◀─┼──│ IPC Client │
│  │("find out")│  │  └─────┬──────┘
│  └────────────┘  │        │
└──────┬───────────┘        │
       │                    │
       ▼                    ▼
┌──────────────────┐  ┌────────────┐
│   Interpreted    │  │  UI Update │
│   Response       │  └─────┬──────┘
└──────┬───────────┘        │
       │                    │
       └────────────────────┤
                            ▼
                    ┌────────────────┐
                    │ 3D Character   │
                    │ Animation      │
                    └────────────────┘
```

## Privacy Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Privacy Layers                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Layer 1: Data Collection                             │
│  ┌──────────────────────────────────────────────┐     │
│  │ • Windows Events (Anonymized)                │     │
│  │ • System Status (Non-PII)                    │     │
│  │ • Calendar Events (Local OAuth)              │     │
│  └──────────────────────────────────────────────┘     │
│                       │                               │
│                       ▼                               │
│  Layer 2: Local Processing (DEFAULT)                  │
│  ┌──────────────────────────────────────────────┐     │
│  │ • All AI processing on local machine         │     │
│  │ • No external network calls                  │     │
│  │ • Data never leaves computer                 │     │
│  └──────────────────────────────────────────────┘     │
│                       │                               │
│                       ▼                               │
│  Layer 3: Optional External (USER TRIGGERED)          │
│  ┌──────────────────────────────────────────────┐     │
│  │ • Only on "find out" phrase                  │     │
│  │ • Context anonymized before sending          │     │
│  │ • Single-shot query only                     │     │
│  │ • User must explicitly enable                │     │
│  └──────────────────────────────────────────────┘     │
│                       │                               │
│                       ▼                               │
│  Layer 4: Storage                                     │
│  ┌──────────────────────────────────────────────┐     │
│  │ • All data stored locally                    │     │
│  │ • Logs sanitized (no PII)                    │     │
│  │ • Credentials in system keyring              │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## State Machine Flow

```
                    ┌──────────┐
              ┌─────│  START   │─────┐
              │     └──────────┘     │
              ▼                      ▼
       ┌────────────┐         ┌────────────┐
       │   IDLE     │◀────────│  REMINDER  │
       │            │         │            │
       │ • Breathing│         │ • Message  │
       │ • Blinking │         │ • Glow     │
       │ • Click-   │         │ • Alert    │
       │   through  │         │   Pose     │
       └─────┬──────┘         └────────────┘
             │ ▲                     ▲
             │ │                     │
start_scan   │ │ finish_scan    show_reminder
             │ │                     │
             ▼ │                     │
       ┌────────────┐                │
       │ SCANNING   │                │
       │            │                │
       │ • Active   │                │
       │   Monitor  │                │
       │ • Look     │                │
       │   Around   │                │
       └─────┬──────┘                │
             │                       │
       trigger_alert                 │
             │                       │
             ▼                       │
       ┌────────────┐                │
       │   ALERT    │                │
       │            │────────────────┘
       │ • Glow     │   dismiss
       │ • Alert    │
       │   Pose     │
       │ • Inter-   │
       │   active   │
       └────────────┘
```

## Animation System

```
┌───────────────────────────────────────────────────┐
│            Animation Controller                   │
├───────────────────────────────────────────────────┤
│                                                   │
│  Idle Animations (Always Active)                 │
│  ┌─────────────────────────────────────────┐     │
│  │                                         │     │
│  │  Breathing:                             │     │
│  │  ┌──┐    ┌──┐    ┌──┐                  │     │
│  │ ─┘  └────┘  └────┘  └─  (Sine Wave)    │     │
│  │                                         │     │
│  │  Blinking:                              │     │
│  │  ──┐  ┌─────────┐  ┌────  (Random)     │     │
│  │    └──┘         └──┘                    │     │
│  │                                         │     │
│  └─────────────────────────────────────────┘     │
│                                                   │
│  State-Based Animations                          │
│  ┌─────────────────────────────────────────┐     │
│  │                                         │     │
│  │  Idle:    Relaxed pose                 │     │
│  │  Scanning: Head rotation               │     │
│  │  Alert:   Lean forward, eyes wide      │     │
│  │  Reminder: Gentle head tilt            │     │
│  │                                         │     │
│  └─────────────────────────────────────────┘     │
│                                                   │
│  Blendshapes (Facial Expressions)                │
│  ┌─────────────────────────────────────────┐     │
│  │                                         │     │
│  │  • eye_blink_left/right                │     │
│  │  • mouth_smile/frown/o                 │     │
│  │  • brow_angry/surprised                │     │
│  │  • eye_happy/sad/wide                  │     │
│  │                                         │     │
│  └─────────────────────────────────────────┘     │
│                                                   │
│  Effects                                         │
│  ┌─────────────────────────────────────────┐     │
│  │                                         │     │
│  │  Glow: State-dependent lighting         │     │
│  │  • Alert: Blue/Red (by priority)        │     │
│  │  • Reminder: Green                      │     │
│  │  • Idle: Subtle ambient                 │     │
│  │                                         │     │
│  └─────────────────────────────────────────┘     │
└───────────────────────────────────────────────────┘
```

## IPC Communication Protocol

```
Service → UI
─────────────
{
  "type": "state_update",
  "data": {
    "state": "alert",
    "message": "Security event detected",
    "priority": 2,
    "timestamp": 1706371200.0
  }
}

{
  "type": "llm_response",
  "data": {
    "message": "Response text from AI"
  }
}


UI → Service
────────────
{
  "type": "user_message",
  "data": {
    "message": "User query text"
  }
}

{
  "type": "dismiss",
  "data": {}
}
```

## File Structure

```
E.V3/
│
├── service/              ◀── Background Service
│   ├── modules/         │   Main logic (renamed from core)
│   ├── state/           │   State machine
│   ├── events/          │   Event monitoring
│   ├── llm/             │   AI integration
│   └── calendar/        │   Calendar sync
│
├── ui/                   ◀── User Interface
│   ├── window/          │   Main window
│   ├── renderer/        │   3D rendering
│   └── animations/      │   Animation system
│
├── ipc/                  ◀── Communication
│   └── native_pipe.py   │   Named pipes
│
├── models/               ◀── Assets
│   ├── character/       │   3D models
│   └── llm/             │   AI models
│
├── config/               ◀── Configuration
│   ├── config.yaml      │   Settings
│   └── credentials/     │   API keys
│
└── tests/                ◀── Testing
    └── test_*.py
```

## Deployment Options

```
┌────────────────────────────────────────────────┐
│              Development Mode                  │
│  python main_service.py                        │
│  python main_ui.py                             │
│  • Easy debugging                              │
│  • Quick iteration                             │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│           Windows Service Mode                 │
│  python install_service.py install             │
│  net start EV3CompanionService                 │
│  python main_ui.py                             │
│  • Auto-start with Windows                     │
│  • Runs in background                          │
│  • System-level service                        │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│              Portable Mode                     │
│  PyInstaller build                             │
│  • Single executable                           │
│  • No Python required                          │
│  • Easy distribution                           │
└────────────────────────────────────────────────┘
```
