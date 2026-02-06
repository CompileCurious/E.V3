/**
 * @file module.hpp
 * @brief Base module interface for E.V3 kernel
 */

#pragma once

#include "common.hpp"
#include "event_bus.hpp"
#include "config.hpp"
#include <set>

namespace ev3 {

// Forward declarations
class Kernel;
class KernelAPI;

/**
 * @brief Abstract base class for all kernel modules
 * 
 * Each module is an isolated capability with explicit lifecycle and permissions.
 * Modules communicate via the event bus and access kernel services through KernelAPI.
 */
class Module {
public:
    explicit Module(std::string_view name, KernelAPI* api)
        : name_(name), api_(api), state_(ModuleState::Unloaded) {}
    
    virtual ~Module() = default;
    
    // Non-copyable
    Module(const Module&) = delete;
    Module& operator=(const Module&) = delete;
    
    /**
     * @brief Get the module name
     */
    [[nodiscard]] std::string_view name() const noexcept { return name_; }
    
    /**
     * @brief Get the current module state
     */
    [[nodiscard]] ModuleState state() const noexcept { 
        return state_.load(std::memory_order_acquire); 
    }
    
    /**
     * @brief Set module state
     */
    void set_state(ModuleState state) noexcept {
        state_.store(state, std::memory_order_release);
    }
    
    /**
     * @brief Declare required permissions
     * @return Set of permissions this module needs
     */
    [[nodiscard]] virtual Permission required_permissions() const = 0;
    
    /**
     * @brief Declare module dependencies
     * @return Set of module names this module depends on
     */
    [[nodiscard]] virtual std::set<std::string> dependencies() const { return {}; }
    
    /**
     * @brief Load module with configuration
     * Initialize resources, validate config, prepare for enable
     */
    virtual Result<void> load(const ConfigSection& config) = 0;
    
    /**
     * @brief Enable module - start active operations
     */
    virtual Result<void> enable() = 0;
    
    /**
     * @brief Disable module - stop active operations but keep resources
     */
    virtual Result<void> disable() = 0;
    
    /**
     * @brief Shutdown module - release all resources
     */
    virtual Result<void> shutdown() = 0;
    
    /**
     * @brief Handle an event from the event bus
     */
    virtual void handle_event(std::string_view event_type, const EventData& data) = 0;

protected:
    [[nodiscard]] KernelAPI* api() const noexcept { return api_; }
    
private:
    std::string name_;
    KernelAPI* api_;
    std::atomic<ModuleState> state_;
};

/**
 * @brief API interface provided by kernel to modules
 * 
 * Enforces permission boundaries and provides core services.
 */
class KernelAPI {
public:
    KernelAPI(EventBus& event_bus, Config& config)
        : event_bus_(event_bus), config_(config) {}
    
    /**
     * @brief Grant permissions to a module
     */
    void grant_permissions(std::string_view module_name, Permission perms) {
        std::unique_lock lock(mutex_);
        permissions_[std::string(module_name)] = 
            permissions_[std::string(module_name)] | perms;
    }
    
    /**
     * @brief Revoke all permissions from a module
     */
    void revoke_permissions(std::string_view module_name) {
        std::unique_lock lock(mutex_);
        permissions_.erase(std::string(module_name));
    }
    
    /**
     * @brief Check if module has permission
     */
    [[nodiscard]] bool check_permission(std::string_view module_name, Permission perm) const {
        std::shared_lock lock(mutex_);
        auto it = permissions_.find(std::string(module_name));
        if (it == permissions_.end()) return false;
        return has_permission(it->second, perm);
    }
    
    /**
     * @brief Emit an event (requires EventEmit permission)
     */
    bool emit_event(std::string_view module_name, std::string_view event_type, EventData data) {
        if (!check_permission(module_name, Permission::EventEmit)) {
            EV3_WARN("Module '{}' denied EventEmit permission", module_name);
            return false;
        }
        return event_bus_.emit(event_type, std::move(data), module_name);
    }
    
    /**
     * @brief Subscribe to an event type (requires EventSubscribe permission)
     */
    bool subscribe_event(std::string_view module_name, std::string_view event_type) {
        if (!check_permission(module_name, Permission::EventSubscribe)) {
            EV3_WARN("Module '{}' denied EventSubscribe permission", module_name);
            return false;
        }
        return event_bus_.subscribe(event_type, module_name);
    }
    
    /**
     * @brief Get configuration section for module
     */
    [[nodiscard]] const ConfigSection* get_config(std::string_view module_name) const {
        return config_.section_ptr(module_name);
    }
    
    /**
     * @brief Get full configuration
     */
    [[nodiscard]] const Config& config() const { return config_; }
    
    /**
     * @brief Get event bus reference
     */
    [[nodiscard]] EventBus& event_bus() { return event_bus_; }

private:
    mutable std::shared_mutex mutex_;
    std::unordered_map<std::string, Permission> permissions_;
    EventBus& event_bus_;
    Config& config_;
};

} // namespace ev3
