/**
 * @file logger.hpp
 * @brief Thread-safe logging system for E.V3 C++ Kernel
 */

#pragma once

#include "common.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <filesystem>

namespace ev3 {

/**
 * @brief Log levels
 */
enum class LogLevel {
    Trace = 0,
    Debug = 1,
    Info = 2,
    Warning = 3,
    Error = 4,
    Critical = 5
};

[[nodiscard]] constexpr std::string_view to_string(LogLevel level) noexcept {
    switch (level) {
        case LogLevel::Trace: return "TRACE";
        case LogLevel::Debug: return "DEBUG";
        case LogLevel::Info: return "INFO";
        case LogLevel::Warning: return "WARN";
        case LogLevel::Error: return "ERROR";
        case LogLevel::Critical: return "CRIT";
    }
    return "?????";
}

/**
 * @brief Thread-safe logger with file and console output
 */
class Logger {
public:
    static Logger& instance() {
        static Logger logger;
        return logger;
    }

    void set_level(LogLevel level) noexcept {
        level_.store(level, std::memory_order_relaxed);
    }
    
    [[nodiscard]] LogLevel level() const noexcept {
        return level_.load(std::memory_order_relaxed);
    }
    
    void set_console_enabled(bool enabled) noexcept {
        console_enabled_.store(enabled, std::memory_order_relaxed);
    }
    
    bool open_file(const std::filesystem::path& path) {
        std::lock_guard lock(mutex_);
        
        // Create parent directories if needed
        auto parent = path.parent_path();
        if (!parent.empty() && !std::filesystem::exists(parent)) {
            std::filesystem::create_directories(parent);
        }
        
        file_.open(path, std::ios::app);
        return file_.is_open();
    }
    
    void close_file() {
        std::lock_guard lock(mutex_);
        if (file_.is_open()) {
            file_.close();
        }
    }
    
    template <typename... Args>
    void log(LogLevel level, std::source_location loc, std::format_string<Args...> fmt, Args&&... args) {
        if (level < level_.load(std::memory_order_relaxed)) {
            return;
        }
        
        auto now = SystemClock::now();
        auto time = SystemClock::to_time_t(now);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()) % 1000;
        
        std::string message = std::format(fmt, std::forward<Args>(args)...);
        
        std::ostringstream oss;
        oss << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S")
            << '.' << std::setfill('0') << std::setw(3) << ms.count()
            << " | " << to_string(level)
            << " | " << extract_filename(loc.file_name()) << ":" << loc.line()
            << " | " << message << '\n';
        
        std::string line = oss.str();
        
        std::lock_guard lock(mutex_);
        
        if (console_enabled_.load(std::memory_order_relaxed)) {
            std::cerr << line;
        }
        
        if (file_.is_open()) {
            file_ << line;
            file_.flush();
        }
    }
    
private:
    Logger() = default;
    
    [[nodiscard]] static std::string_view extract_filename(const char* path) noexcept {
        std::string_view sv(path);
        auto pos = sv.find_last_of("/\\");
        return pos == std::string_view::npos ? sv : sv.substr(pos + 1);
    }
    
    std::mutex mutex_;
    std::ofstream file_;
    std::atomic<LogLevel> level_{LogLevel::Info};
    std::atomic<bool> console_enabled_{true};
};

} // namespace ev3

// Logging macros
#define EV3_LOG(level, ...) \
    ::ev3::Logger::instance().log(level, std::source_location::current(), __VA_ARGS__)

#define EV3_TRACE(...) EV3_LOG(::ev3::LogLevel::Trace, __VA_ARGS__)
#define EV3_DEBUG(...) EV3_LOG(::ev3::LogLevel::Debug, __VA_ARGS__)
#define EV3_INFO(...)  EV3_LOG(::ev3::LogLevel::Info, __VA_ARGS__)
#define EV3_WARN(...)  EV3_LOG(::ev3::LogLevel::Warning, __VA_ARGS__)
#define EV3_ERROR(...) EV3_LOG(::ev3::LogLevel::Error, __VA_ARGS__)
#define EV3_CRIT(...)  EV3_LOG(::ev3::LogLevel::Critical, __VA_ARGS__)
