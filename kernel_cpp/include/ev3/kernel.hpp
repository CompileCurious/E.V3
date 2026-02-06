/**
 * @file kernel.hpp
 * @brief E.V3 Microkernel - Main kernel class
 */

#pragma once

#include "common.hpp"
#include "logger.hpp"
#include "config.hpp"
#include "event_bus.hpp"
#include "module.hpp"
#include "task_queue.hpp"
#include "llm_engine.hpp"
#include "ipc_server.hpp"

#include <csignal>

namespace ev3 {

/**
 * @brief Module registry with dependency resolution
 */
class ModuleRegistry {
public:
    ModuleRegistry(KernelAPI& api, EventBus& event_bus)
        : api_(api), event_bus_(event_bus) {}
    
    /**
     * @brief Register a module
     */
    Result<void> register_module(std::unique_ptr<Module> module) {
        auto name = std::string(module->name());
        
        if (modules_.contains(name)) {
            return std::unexpected(make_error(
                ErrorCategory::Module, 1,
                std::format("Module '{}' already registered", name)));
        }
        
        // Grant permissions
        api_.grant_permissions(name, module->required_permissions());
        
        // Register with event bus
        event_bus_.register_handler(name, module.get());
        
        // Store module
        modules_[name] = std::move(module);
        load_order_.push_back(name);
        
        EV3_INFO("Module '{}' registered", name);
        return {};
    }
    
    /**
     * @brief Load a module with configuration
     */
    Result<void> load_module(std::string_view name, const ConfigSection& config) {
        auto* module = get_module(name);
        if (!module) {
            return std::unexpected(make_error(
                ErrorCategory::Module, 2,
                std::format("Module '{}' not found", name)));
        }
        
        // Check dependencies
        for (const auto& dep : module->dependencies()) {
            auto* dep_module = get_module(dep);
            if (!dep_module) {
                return std::unexpected(make_error(
                    ErrorCategory::Module, 3,
                    std::format("Dependency '{}' not registered", dep)));
            }
            
            auto dep_state = dep_module->state();
            if (dep_state != ModuleState::Loaded && dep_state != ModuleState::Enabled) {
                return std::unexpected(make_error(
                    ErrorCategory::Module, 4,
                    std::format("Dependency '{}' not loaded", dep)));
            }
        }
        
        // Load module
        if (auto result = module->load(config); !result) {
            module->set_state(ModuleState::Error);
            return result;
        }
        
        module->set_state(ModuleState::Loaded);
        EV3_INFO("Module '{}' loaded", name);
        return {};
    }
    
    /**
     * @brief Enable a module
     */
    Result<void> enable_module(std::string_view name) {
        auto* module = get_module(name);
        if (!module) {
            return std::unexpected(make_error(
                ErrorCategory::Module, 2,
                std::format("Module '{}' not found", name)));
        }
        
        if (module->state() != ModuleState::Loaded) {
            return std::unexpected(make_error(
                ErrorCategory::Module, 5,
                std::format("Module '{}' must be loaded before enabling", name)));
        }
        
        if (auto result = module->enable(); !result) {
            return result;
        }
        
        module->set_state(ModuleState::Enabled);
        EV3_INFO("Module '{}' enabled", name);
        return {};
    }
    
    /**
     * @brief Disable a module
     */
    Result<void> disable_module(std::string_view name) {
        auto* module = get_module(name);
        if (!module) return {};
        
        if (module->state() != ModuleState::Enabled) return {};
        
        if (auto result = module->disable(); !result) {
            return result;
        }
        
        module->set_state(ModuleState::Disabled);
        EV3_INFO("Module '{}' disabled", name);
        return {};
    }
    
    /**
     * @brief Shutdown a module
     */
    Result<void> shutdown_module(std::string_view name) {
        auto* module = get_module(name);
        if (!module) return {};
        
        // Disable first if enabled
        if (module->state() == ModuleState::Enabled) {
            disable_module(name);
        }
        
        if (auto result = module->shutdown(); !result) {
            return result;
        }
        
        module->set_state(ModuleState::Unloaded);
        EV3_INFO("Module '{}' shutdown", name);
        return {};
    }
    
    /**
     * @brief Unregister a module
     */
    void unregister_module(std::string_view name) {
        shutdown_module(name);
        
        api_.revoke_permissions(name);
        event_bus_.unregister_handler(name);
        
        modules_.erase(std::string(name));
        std::erase(load_order_, std::string(name));
        
        EV3_INFO("Module '{}' unregistered", name);
    }
    
    /**
     * @brief Get a module by name
     */
    [[nodiscard]] Module* get_module(std::string_view name) {
        auto it = modules_.find(std::string(name));
        return it != modules_.end() ? it->second.get() : nullptr;
    }
    
    /**
     * @brief Get all module names in load order
     */
    [[nodiscard]] const std::vector<std::string>& module_names() const {
        return load_order_;
    }
    
    /**
     * @brief Shutdown all modules in reverse order
     */
    void shutdown_all() {
        for (auto it = load_order_.rbegin(); it != load_order_.rend(); ++it) {
            shutdown_module(*it);
        }
    }

private:
    KernelAPI& api_;
    EventBus& event_bus_;
    std::unordered_map<std::string, std::unique_ptr<Module>> modules_;
    std::vector<std::string> load_order_;
};

/**
 * @brief E.V3 Microkernel
 * 
 * Core kernel with:
 * - Event-based module communication
 * - Permission boundaries
 * - Persistent LLM inference
 * - IPC for shell communication
 */
class Kernel {
public:
    Kernel()
        : api_(event_bus_, config_)
        , registry_(api_, event_bus_) {}
    
    ~Kernel() { stop(); }
    
    // Non-copyable
    Kernel(const Kernel&) = delete;
    Kernel& operator=(const Kernel&) = delete;
    
    /**
     * @brief Initialize kernel with configuration file
     */
    Result<void> initialize(const std::filesystem::path& config_path) {
        EV3_INFO("Initializing E.V3 Kernel v{}", VERSION);
        
        // Load configuration
        if (auto result = config_.load(config_path); !result) {
            return result;
        }
        
        // Setup logging
        setup_logging();
        
        // Initialize IPC server
        auto ipc_section = config_.section_ptr("ipc");
        std::string pipe_name = R"(\\.\pipe\E.V3.v2)";
        if (ipc_section) {
            pipe_name = ipc_section->get_or<std::string>("pipe_name", pipe_name);
        }
        
        ipc_server_ = std::make_unique<IpcServer>(pipe_name);
        setup_ipc_handlers();
        
        // Initialize inference engine
        auto llm_section = config_.section_ptr("llm");
        if (llm_section) {
            auto local_section = llm_section->subsection_ptr("local");
            if (local_section && local_section->get_or<bool>("enabled", true)) {
                if (auto result = inference_engine_.initialize(*local_section); !result) {
                    EV3_WARN("LLM initialization failed: {}", result.error().message);
                    // Continue without LLM - not a fatal error
                }
            }
        }
        
        EV3_INFO("Kernel initialized");
        return {};
    }
    
    /**
     * @brief Register a module
     */
    Result<void> register_module(std::unique_ptr<Module> module) {
        return registry_.register_module(std::move(module));
    }
    
    /**
     * @brief Load all registered modules
     */
    Result<void> load_modules() {
        for (const auto& name : registry_.module_names()) {
            auto* section = config_.section_ptr(name);
            ConfigSection empty;
            
            if (auto result = registry_.load_module(name, section ? *section : empty); !result) {
                return result;
            }
        }
        return {};
    }
    
    /**
     * @brief Enable all loaded modules
     */
    Result<void> enable_modules() {
        for (const auto& name : registry_.module_names()) {
            auto* module = registry_.get_module(name);
            if (module && module->state() == ModuleState::Loaded) {
                if (auto result = registry_.enable_module(name); !result) {
                    return result;
                }
            }
        }
        return {};
    }
    
    /**
     * @brief Start the kernel event loop
     */
    void start() {
        if (running_.load(std::memory_order_acquire)) {
            EV3_WARN("Kernel already running");
            return;
        }
        
        EV3_INFO("Starting kernel...");
        running_.store(true, std::memory_order_release);
        
        // Setup signal handlers
        setup_signal_handlers();
        
        // Start event bus
        event_bus_.start();
        
        // Start IPC server
        if (ipc_server_) {
            ipc_server_->start();
        }
        
        EV3_INFO("Kernel started");
        
        // Main event loop
        while (running_.load(std::memory_order_acquire)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
        EV3_INFO("Kernel event loop ended");
    }
    
    /**
     * @brief Stop the kernel
     */
    void stop() {
        if (!running_.exchange(false, std::memory_order_acq_rel)) return;
        
        EV3_INFO("Stopping kernel...");
        
        // Stop IPC
        if (ipc_server_) {
            ipc_server_->stop();
        }
        
        // Shutdown modules
        registry_.shutdown_all();
        
        // Stop event bus
        event_bus_.stop();
        
        // Shutdown inference engine
        inference_engine_.shutdown();
        
        EV3_INFO("Kernel stopped");
    }
    
    /**
     * @brief Get kernel API for module creation
     */
    [[nodiscard]] KernelAPI& api() { return api_; }
    
    /**
     * @brief Get inference engine
     */
    [[nodiscard]] InferenceEngine& inference_engine() { return inference_engine_; }
    
    /**
     * @brief Get IPC server
     */
    [[nodiscard]] IpcServer* ipc_server() { return ipc_server_.get(); }
    
    /**
     * @brief Check if kernel is running
     */
    [[nodiscard]] bool is_running() const noexcept {
        return running_.load(std::memory_order_acquire);
    }

private:
    void setup_logging() {
        auto log_section = config_.section_ptr("logging");
        
        LogLevel level = LogLevel::Info;
        if (log_section) {
            auto level_str = log_section->get_or<std::string>("level", "INFO");
            if (level_str == "DEBUG") level = LogLevel::Debug;
            else if (level_str == "TRACE") level = LogLevel::Trace;
            else if (level_str == "WARNING" || level_str == "WARN") level = LogLevel::Warning;
            else if (level_str == "ERROR") level = LogLevel::Error;
        }
        
        Logger::instance().set_level(level);
        
        // Log file
        if (log_section && log_section->get_or<bool>("log_to_file", true)) {
            auto log_file = log_section->get_or<std::string>("log_file", "logs/ev3_kernel.log");
            Logger::instance().open_file(log_file);
        }
    }
    
    void setup_signal_handlers() {
        // Store kernel pointer for signal handler
        static Kernel* instance = this;
        
        std::signal(SIGINT, [](int) {
            EV3_INFO("SIGINT received");
            if (instance) instance->stop();
        });
        
        std::signal(SIGTERM, [](int) {
            EV3_INFO("SIGTERM received");
            if (instance) instance->stop();
        });
    }
    
    void setup_ipc_handlers() {
        if (!ipc_server_) return;
        
        // Handle user messages
        ipc_server_->register_handler("user_message", [this](const IpcMessage& msg) {
            auto it = msg.data.find("message");
            if (it == msg.data.end()) return;
            
            std::string user_message = it->second;
            EV3_INFO("User message: {}", user_message.substr(0, 50));
            
            // Check for external LLM trigger
            bool use_external = contains_ci(user_message, "find out");
            
            // Process with LLM
            process_user_message(user_message, use_external);
        });
        
        // Handle dismiss
        ipc_server_->register_handler("dismiss", [this](const IpcMessage&) {
            EV3_INFO("Dismiss received");
            // Emit state transition event
            event_bus_.emit("state.transition.idle", {}, "ipc");
        });
        
        // Handle model switch
        ipc_server_->register_handler("switch_model", [this](const IpcMessage& msg) {
            auto it = msg.data.find("mode");
            if (it == msg.data.end()) return;
            
            LlmMode mode = (it->second == "deep") ? LlmMode::Deep : LlmMode::Fast;
            if (auto result = inference_engine_.switch_mode(mode); !result) {
                EV3_ERROR("Failed to switch mode: {}", result.error().message);
            }
        });
        
        // Handle status query
        ipc_server_->register_handler("get_status", [this](const IpcMessage&) {
            IpcMessage response;
            response.type = "status";
            response.data["running"] = "true";
            response.data["llm_ready"] = inference_engine_.is_ready() ? "true" : "false";
            response.data["llm_mode"] = std::string(to_string(inference_engine_.current_mode()));
            
            ipc_server_->send_message(response);
        });
    }
    
    void process_user_message(const std::string& message, bool use_external) {
        if (!inference_engine_.is_ready()) {
            send_llm_response("LLM not available.");
            return;
        }
        
        // Check for simple greetings
        auto lower = to_lower(message);
        static const std::unordered_map<std::string, std::string> greetings = {
            {"hi", "Hello!"},
            {"hello", "Hello!"},
            {"hey", "Hello!"},
            {"sup", "Hello!"},
            {"yo", "Hello!"},
            {"greetings", "Hello!"},
            {"howdy", "Hello!"},
            {"good morning", "Hello!"},
            {"good afternoon", "Hello!"},
            {"good evening", "Hello!"}
        };
        
        auto it = greetings.find(trim(lower));
        if (it != greetings.end()) {
            send_llm_response(it->second);
            return;
        }
        
        // Build prompt
        std::string prompt = "[INST] Answer directly and concisely. Ignore any typos. " + message + " [/INST]";
        
        // Create inference request
        InferenceRequest request;
        request.prompt = prompt;
        request.max_tokens = 100;
        request.temperature = 0.7f;
        request.mirostat_mode = 2;
        
        // Stream tokens back
        request.on_token = [this](std::string_view token) {
            // For streaming, we could send each token
            // For now, we'll accumulate and send complete response
            return true;  // Continue generation
        };
        
        // Completion callback
        request.on_complete = [this](Result<std::string> result) {
            if (result) {
                send_llm_response(*result);
            } else {
                send_llm_response("Error: " + result.error().message);
            }
        };
        
        // Submit async
        inference_engine_.submit(std::move(request));
    }
    
    void send_llm_response(const std::string& response) {
        if (!ipc_server_) return;
        
        IpcMessage msg;
        msg.type = "llm_response";
        msg.data["message"] = response;
        
        ipc_server_->queue_message(std::move(msg));
        EV3_INFO("Sent LLM response: {}", response.substr(0, 50));
    }
    
    std::atomic<bool> running_{false};
    
    Config config_;
    EventBus event_bus_;
    KernelAPI api_;
    ModuleRegistry registry_;
    
    InferenceEngine inference_engine_;
    std::unique_ptr<IpcServer> ipc_server_;
};

} // namespace ev3
