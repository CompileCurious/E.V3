/**
 * @file event_bus.hpp
 * @brief Thread-safe event bus for module communication
 */

#pragma once

#include "common.hpp"
#include "logger.hpp"
#include <queue>

namespace ev3 {

// Forward declarations
class Module;

/**
 * @brief Event message structure
 */
struct Event {
    std::string type;
    EventData data;
    std::string source;
    TimePoint timestamp;
    
    Event() : timestamp(now()) {}
    Event(std::string_view t, EventData d, std::string_view s)
        : type(t), data(std::move(d)), source(s), timestamp(now()) {}
};

/**
 * @brief Event handler function type
 */
using EventHandler = std::function<void(const Event&)>;

/**
 * @brief Thread-safe event bus for inter-module communication
 * 
 * The event bus provides publish-subscribe messaging between modules.
 * All operations are thread-safe and can be called from any thread.
 */
class EventBus {
public:
    EventBus() = default;
    ~EventBus() { stop(); }
    
    // Non-copyable, non-movable
    EventBus(const EventBus&) = delete;
    EventBus& operator=(const EventBus&) = delete;
    
    /**
     * @brief Start the event bus processing thread
     */
    void start() {
        if (running_.load(std::memory_order_acquire)) return;
        
        running_.store(true, std::memory_order_release);
        worker_ = std::thread([this] { process_events(); });
        EV3_INFO("Event bus started");
    }
    
    /**
     * @brief Stop the event bus
     */
    void stop() {
        if (!running_.exchange(false, std::memory_order_acq_rel)) return;
        
        cv_.notify_all();
        if (worker_.joinable()) {
            worker_.join();
        }
        EV3_INFO("Event bus stopped");
    }
    
    /**
     * @brief Register a module's event handler
     */
    void register_handler(std::string_view module_name, Module* handler) {
        std::unique_lock lock(mutex_);
        handlers_[std::string(module_name)] = handler;
        EV3_DEBUG("Registered event handler for module '{}'", module_name);
    }
    
    /**
     * @brief Unregister a module
     */
    void unregister_handler(std::string_view module_name) {
        std::unique_lock lock(mutex_);
        handlers_.erase(std::string(module_name));
        
        // Remove from all subscriptions
        for (auto& [event_type, subscribers] : subscriptions_) {
            subscribers.erase(std::string(module_name));
        }
        EV3_DEBUG("Unregistered module '{}'", module_name);
    }
    
    /**
     * @brief Subscribe a module to an event type
     */
    bool subscribe(std::string_view event_type, std::string_view module_name) {
        std::unique_lock lock(mutex_);
        
        if (!handlers_.contains(std::string(module_name))) {
            EV3_WARN("Cannot subscribe unregistered module '{}'", module_name);
            return false;
        }
        
        subscriptions_[std::string(event_type)].insert(std::string(module_name));
        EV3_DEBUG("Module '{}' subscribed to '{}'", module_name, event_type);
        return true;
    }
    
    /**
     * @brief Unsubscribe a module from an event type
     */
    void unsubscribe(std::string_view event_type, std::string_view module_name) {
        std::unique_lock lock(mutex_);
        
        auto it = subscriptions_.find(std::string(event_type));
        if (it != subscriptions_.end()) {
            it->second.erase(std::string(module_name));
        }
    }
    
    /**
     * @brief Emit an event (non-blocking, queues for async delivery)
     */
    bool emit(std::string_view event_type, EventData data, std::string_view source) {
        Event event(event_type, std::move(data), source);
        
        {
            std::unique_lock lock(queue_mutex_);
            event_queue_.push(std::move(event));
        }
        
        cv_.notify_one();
        return true;
    }
    
    /**
     * @brief Emit an event synchronously (blocks until all handlers complete)
     */
    void emit_sync(std::string_view event_type, EventData data, std::string_view source);
    
    /**
     * @brief Get the number of pending events
     */
    [[nodiscard]] size_t pending_count() const {
        std::unique_lock lock(queue_mutex_);
        return event_queue_.size();
    }

private:
    void process_events();
    void deliver_event(const Event& event);
    
    mutable std::mutex mutex_;
    mutable std::mutex queue_mutex_;
    std::condition_variable cv_;
    
    std::unordered_map<std::string, Module*> handlers_;
    std::unordered_map<std::string, std::unordered_set<std::string>> subscriptions_;
    std::queue<Event> event_queue_;
    
    std::atomic<bool> running_{false};
    std::thread worker_;
};

} // namespace ev3
