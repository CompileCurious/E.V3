/**
 * @file main.cpp
 * @brief E.V3 C++ Kernel entry point
 */

#include "ev3/ev3.hpp"

#include <iostream>
#include <filesystem>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#endif

/**
 * @brief Get resource path (works for dev and packaged builds)
 */
std::filesystem::path get_resource_path(const std::filesystem::path& relative) {
    // Try current directory first
    if (std::filesystem::exists(relative)) {
        return relative;
    }
    
    // Try executable directory
    #ifdef _WIN32
    char path[MAX_PATH];
    GetModuleFileNameA(nullptr, path, MAX_PATH);
    auto exe_dir = std::filesystem::path(path).parent_path();
    auto exe_relative = exe_dir / relative;
    if (std::filesystem::exists(exe_relative)) {
        return exe_relative;
    }
    #endif
    
    return relative;
}

/**
 * @brief Check for single instance
 */
#ifdef _WIN32
HANDLE check_single_instance() {
    HANDLE mutex = CreateMutexA(nullptr, TRUE, "Global\\EV3CppKernelMutex");
    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        std::cerr << "E.V3 Kernel is already running." << std::endl;
        CloseHandle(mutex);
        return nullptr;
    }
    return mutex;
}
#else
void* check_single_instance() { return (void*)1; }
#endif

void print_banner() {
    std::cout << R"(
  ███████╗ ██╗   ██╗ ██████╗ 
  ██╔════╝ ██║   ██║ ╚════██╗
  █████╗   ██║   ██║  █████╔╝
  ██╔══╝   ╚██╗ ██╔╝  ╚═══██╗
  ███████╗  ╚████╔╝  ██████╔╝
  ╚══════╝   ╚═══╝   ╚═════╝ 
  
  E.V3 C++ Kernel v)" << ev3::VERSION << R"(
  High-Performance Privacy-First Companion
  
)" << std::endl;
}

int main(int argc, char* argv[]) {
    print_banner();
    
    // Single instance check
    auto mutex = check_single_instance();
    if (!mutex) {
        return 1;
    }
    
    #ifdef _WIN32
    auto mutex_guard = ev3::make_scope_guard([mutex] { 
        if (mutex) CloseHandle(mutex); 
    });
    #endif
    
    // Parse arguments
    std::filesystem::path config_path = "config/config.yaml";
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if ((arg == "-c" || arg == "--config") && i + 1 < argc) {
            config_path = argv[++i];
        } else if (arg == "-h" || arg == "--help") {
            std::cout << "Usage: " << argv[0] << " [options]\n"
                      << "Options:\n"
                      << "  -c, --config <path>  Configuration file path\n"
                      << "  -h, --help           Show this help\n"
                      << std::endl;
            return 0;
        }
    }
    
    // Resolve config path
    config_path = get_resource_path(config_path);
    
    EV3_INFO("E.V3 C++ Kernel starting...");
    EV3_INFO("Config: {}", config_path.string());
    
    // Create and initialize kernel
    ev3::Kernel kernel;
    
    if (auto result = kernel.initialize(config_path); !result) {
        EV3_CRIT("Initialization failed: {}", result.error().message);
        std::cerr << "Initialization failed: " << result.error().message << std::endl;
        return 1;
    }
    
    // Note: Built-in modules are handled by the kernel itself
    // Custom modules can be registered here if needed
    
    if (auto result = kernel.load_modules(); !result) {
        EV3_CRIT("Module loading failed: {}", result.error().message);
        std::cerr << "Module loading failed: " << result.error().message << std::endl;
        return 1;
    }
    
    if (auto result = kernel.enable_modules(); !result) {
        EV3_CRIT("Module enable failed: {}", result.error().message);
        std::cerr << "Module enable failed: " << result.error().message << std::endl;
        return 1;
    }
    
    EV3_INFO("E.V3 Kernel started successfully");
    std::cout << "Kernel running. Press Ctrl+C to stop." << std::endl;
    
    // Run kernel (blocks until stopped)
    kernel.start();
    
    EV3_INFO("E.V3 Kernel exiting");
    return 0;
}
