/**
 * @file ev3.hpp
 * @brief E.V3 Kernel - Main include header
 * 
 * E.V3 Microkernel - High-Performance C++ Implementation
 * 
 * This is the main header file for the E.V3 kernel. Include this file
 * to get access to all kernel functionality.
 * 
 * @copyright Copyright (C) 2024-2026
 * @license MIT
 */

#pragma once

// Core types and utilities
#include "common.hpp"
#include "logger.hpp"
#include "config.hpp"

// Event system
#include "event_bus.hpp"

// Module system
#include "module.hpp"

// Task scheduling
#include "task_queue.hpp"

// LLM inference
#include "llm_engine.hpp"

// IPC communication
#include "ipc_server.hpp"

// Main kernel
#include "kernel.hpp"

/**
 * @mainpage E.V3 C++ Kernel
 * 
 * @section intro_sec Introduction
 * 
 * The E.V3 C++ Kernel is a high-performance microkernel for the E.V3
 * desktop companion application. It provides:
 * 
 * - **Persistent LLM Inference**: Models are loaded once and kept in memory
 * - **Async Task Queue**: Non-blocking inference with cancellation support
 * - **Event Bus**: Publish-subscribe messaging between modules
 * - **IPC Server**: Named pipe communication with the Python shell
 * - **Module System**: Plugin architecture with permissions and lifecycle
 * 
 * @section arch_sec Architecture
 * 
 * The kernel follows a microkernel design with capability-based modules:
 * 
 * ```
 * ┌─────────────────────────────────────────┐
 * │           E.V3 C++ KERNEL               │
 * │  ┌─────────────────────────────────┐    │
 * │  │  Kernel Core                    │    │
 * │  │  - Event Bus                    │    │
 * │  │  - Permission Checker           │    │
 * │  │  - Module Registry              │    │
 * │  │  - Inference Engine             │    │
 * │  │  - IPC Server                   │    │
 * │  └─────────────────────────────────┘    │
 * └─────────────────────────────────────────┘
 *                     │
 *         Named Pipes │ (JSON messages)
 *                     ▼
 * ┌─────────────────────────────────────────┐
 * │         Python Shell (unchanged)        │
 * └─────────────────────────────────────────┘
 * ```
 * 
 * @section usage_sec Basic Usage
 * 
 * ```cpp
 * #include <ev3/ev3.hpp>
 * 
 * int main() {
 *     ev3::Kernel kernel;
 *     
 *     if (auto result = kernel.initialize("config/config.yaml"); !result) {
 *         std::cerr << "Init failed: " << result.error().message << std::endl;
 *         return 1;
 *     }
 *     
 *     if (auto result = kernel.load_modules(); !result) {
 *         std::cerr << "Load failed: " << result.error().message << std::endl;
 *         return 1;
 *     }
 *     
 *     if (auto result = kernel.enable_modules(); !result) {
 *         std::cerr << "Enable failed: " << result.error().message << std::endl;
 *         return 1;
 *     }
 *     
 *     kernel.start();  // Blocks until stopped
 *     return 0;
 * }
 * ```
 */
