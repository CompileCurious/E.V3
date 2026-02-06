/**
 * @file common.hpp
 * @brief Common types, constants, and utilities for E.V3 C++ Kernel
 * 
 * E.V3 Microkernel - High-Performance C++ Implementation
 * Copyright (C) 2024-2026
 * 
 * Privacy-first design: All inference is local, no network calls.
 */

#pragma once

#include <string>
#include <string_view>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <optional>
#include <memory>
#include <functional>
#include <chrono>
#include <atomic>
#include <mutex>
#include <shared_mutex>
#include <condition_variable>
#include <variant>
#include <expected>
#include <format>
#include <span>
#include <source_location>

namespace ev3 {

// ============================================================================
// Version Information
// ============================================================================

inline constexpr std::string_view VERSION = "2.0.0";
inline constexpr std::string_view VERSION_CODENAME = "CppKernel";
inline constexpr int VERSION_MAJOR = 2;
inline constexpr int VERSION_MINOR = 0;
inline constexpr int VERSION_PATCH = 0;

// ============================================================================
// Error Handling
// ============================================================================

/**
 * @brief Error categories for kernel operations
 */
enum class ErrorCategory {
    None,
    Kernel,
    Module,
    IPC,
    LLM,
    Config,
    Permission,
    IO,
    System
};

/**
 * @brief Kernel error with category and message
 */
struct Error {
    ErrorCategory category = ErrorCategory::None;
    int code = 0;
    std::string message;
    std::source_location location;

    Error() = default;
    
    Error(ErrorCategory cat, int c, std::string_view msg,
          std::source_location loc = std::source_location::current())
        : category(cat), code(c), message(msg), location(loc) {}
    
    [[nodiscard]] bool ok() const noexcept { return category == ErrorCategory::None; }
    [[nodiscard]] explicit operator bool() const noexcept { return !ok(); }
    
    [[nodiscard]] std::string to_string() const {
        return std::format("[{}:{}] {} (at {}:{})", 
            static_cast<int>(category), code, message,
            location.file_name(), location.line());
    }
};

template <typename T>
using Result = std::expected<T, Error>;

inline Error make_error(ErrorCategory cat, int code, std::string_view msg,
                        std::source_location loc = std::source_location::current()) {
    return Error{cat, code, std::string(msg), loc};
}

// ============================================================================
// Event Data Types
// ============================================================================

/**
 * @brief Variant type for event payload values
 */
using EventValue = std::variant<
    std::nullptr_t,
    bool,
    int64_t,
    double,
    std::string,
    std::vector<std::string>,
    std::unordered_map<std::string, std::string>
>;

/**
 * @brief Event payload map
 */
using EventData = std::unordered_map<std::string, EventValue>;

/**
 * @brief Get a typed value from event data
 */
template <typename T>
std::optional<T> get_event_value(const EventData& data, std::string_view key) {
    auto it = data.find(std::string(key));
    if (it == data.end()) return std::nullopt;
    
    if (auto* val = std::get_if<T>(&it->second)) {
        return *val;
    }
    return std::nullopt;
}

// ============================================================================
// Module State
// ============================================================================

/**
 * @brief Module lifecycle states
 */
enum class ModuleState {
    Unloaded,
    Loaded,
    Enabled,
    Disabled,
    Error
};

[[nodiscard]] constexpr std::string_view to_string(ModuleState state) noexcept {
    switch (state) {
        case ModuleState::Unloaded: return "unloaded";
        case ModuleState::Loaded: return "loaded";
        case ModuleState::Enabled: return "enabled";
        case ModuleState::Disabled: return "disabled";
        case ModuleState::Error: return "error";
    }
    return "unknown";
}

// ============================================================================
// Permissions
// ============================================================================

/**
 * @brief System permissions that modules can request
 */
enum class Permission : uint32_t {
    None            = 0,
    
    // IPC permissions
    IpcSend         = 1 << 0,
    IpcReceive      = 1 << 1,
    
    // Event permissions
    EventEmit       = 1 << 2,
    EventSubscribe  = 1 << 3,
    
    // Storage permissions
    StorageRead     = 1 << 4,
    StorageWrite    = 1 << 5,
    
    // System permissions
    SystemEvents    = 1 << 6,
    SecurityEvents  = 1 << 7,
    CalendarRead    = 1 << 8,
    
    // LLM permissions
    LlmLocal        = 1 << 9,
    LlmExternal     = 1 << 10,
    
    // Composite permissions
    AllIpc          = IpcSend | IpcReceive,
    AllEvents       = EventEmit | EventSubscribe,
    AllStorage      = StorageRead | StorageWrite,
    AllLlm          = LlmLocal | LlmExternal,
    All             = 0xFFFFFFFF
};

[[nodiscard]] constexpr Permission operator|(Permission a, Permission b) noexcept {
    return static_cast<Permission>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b));
}

[[nodiscard]] constexpr Permission operator&(Permission a, Permission b) noexcept {
    return static_cast<Permission>(static_cast<uint32_t>(a) & static_cast<uint32_t>(b));
}

[[nodiscard]] constexpr bool has_permission(Permission set, Permission check) noexcept {
    return (static_cast<uint32_t>(set) & static_cast<uint32_t>(check)) == static_cast<uint32_t>(check);
}

// ============================================================================
// Task Types
// ============================================================================

/**
 * @brief Priority levels for task queue
 */
enum class TaskPriority {
    Low = 0,
    Normal = 1,
    High = 2,
    Critical = 3
};

/**
 * @brief Task status
 */
enum class TaskStatus {
    Pending,
    Running,
    Completed,
    Cancelled,
    Failed
};

// ============================================================================
// LLM Types
// ============================================================================

/**
 * @brief LLM inference mode
 */
enum class LlmMode {
    Fast,   // Phi-3 for quick responses
    Deep    // Mistral 7B for complex reasoning
};

[[nodiscard]] constexpr std::string_view to_string(LlmMode mode) noexcept {
    switch (mode) {
        case LlmMode::Fast: return "fast";
        case LlmMode::Deep: return "deep";
    }
    return "unknown";
}

/**
 * @brief Token callback for streaming output
 */
using TokenCallback = std::function<bool(std::string_view token)>;

/**
 * @brief Completion callback
 */
using CompletionCallback = std::function<void(Result<std::string>)>;

// ============================================================================
// Utility Types
// ============================================================================

/**
 * @brief Scoped lock that automatically releases on scope exit
 */
template <typename Mutex>
class ScopedLock {
public:
    explicit ScopedLock(Mutex& m) : mutex_(m) { mutex_.lock(); }
    ~ScopedLock() { mutex_.unlock(); }
    
    ScopedLock(const ScopedLock&) = delete;
    ScopedLock& operator=(const ScopedLock&) = delete;
    
private:
    Mutex& mutex_;
};

/**
 * @brief RAII scope guard
 */
template <typename F>
class ScopeGuard {
public:
    explicit ScopeGuard(F&& f) : func_(std::forward<F>(f)), active_(true) {}
    ~ScopeGuard() { if (active_) func_(); }
    
    void dismiss() noexcept { active_ = false; }
    
    ScopeGuard(const ScopeGuard&) = delete;
    ScopeGuard& operator=(const ScopeGuard&) = delete;
    ScopeGuard(ScopeGuard&& other) noexcept : func_(std::move(other.func_)), active_(other.active_) {
        other.active_ = false;
    }
    
private:
    F func_;
    bool active_;
};

template <typename F>
ScopeGuard<F> make_scope_guard(F&& f) {
    return ScopeGuard<F>(std::forward<F>(f));
}

// ============================================================================
// Time Utilities
// ============================================================================

using Clock = std::chrono::steady_clock;
using TimePoint = Clock::time_point;
using Duration = Clock::duration;

using SystemClock = std::chrono::system_clock;
using SystemTimePoint = SystemClock::time_point;

[[nodiscard]] inline TimePoint now() noexcept {
    return Clock::now();
}

[[nodiscard]] inline int64_t elapsed_ms(TimePoint start) noexcept {
    return std::chrono::duration_cast<std::chrono::milliseconds>(now() - start).count();
}

// ============================================================================
// String Utilities
// ============================================================================

/**
 * @brief Trim whitespace from string
 */
[[nodiscard]] inline std::string trim(std::string_view s) {
    auto start = s.find_first_not_of(" \t\n\r\f\v");
    if (start == std::string_view::npos) return "";
    auto end = s.find_last_not_of(" \t\n\r\f\v");
    return std::string(s.substr(start, end - start + 1));
}

/**
 * @brief Convert string to lowercase
 */
[[nodiscard]] inline std::string to_lower(std::string_view s) {
    std::string result(s);
    for (char& c : result) {
        if (c >= 'A' && c <= 'Z') c += 32;
    }
    return result;
}

/**
 * @brief Check if string contains substring (case-insensitive)
 */
[[nodiscard]] inline bool contains_ci(std::string_view haystack, std::string_view needle) {
    auto lower_haystack = to_lower(haystack);
    auto lower_needle = to_lower(needle);
    return lower_haystack.find(lower_needle) != std::string::npos;
}

} // namespace ev3
