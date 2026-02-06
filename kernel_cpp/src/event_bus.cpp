/**
 * @file event_bus.cpp
 * @brief Event bus implementation
 */

#include "ev3/event_bus.hpp"
#include "ev3/module.hpp"

namespace ev3 {

void EventBus::process_events() {
    EV3_DEBUG("Event bus worker started");
    
    while (running_.load(std::memory_order_acquire)) {
        Event event;
        
        {
            std::unique_lock lock(queue_mutex_);
            cv_.wait(lock, [this] {
                return !running_.load(std::memory_order_acquire) || !event_queue_.empty();
            });
            
            if (!running_.load(std::memory_order_acquire) && event_queue_.empty()) {
                break;
            }
            
            if (event_queue_.empty()) continue;
            
            event = std::move(event_queue_.front());
            event_queue_.pop();
        }
        
        deliver_event(event);
    }
    
    EV3_DEBUG("Event bus worker stopped");
}

void EventBus::deliver_event(const Event& event) {
    std::shared_lock lock(mutex_);
    
    auto sub_it = subscriptions_.find(event.type);
    if (sub_it == subscriptions_.end()) {
        EV3_TRACE("No subscribers for event '{}'", event.type);
        return;
    }
    
    const auto& subscribers = sub_it->second;
    EV3_TRACE("Delivering '{}' from '{}' to {} subscribers", 
              event.type, event.source, subscribers.size());
    
    for (const auto& module_name : subscribers) {
        // Don't send event back to source
        if (module_name == event.source) continue;
        
        auto handler_it = handlers_.find(module_name);
        if (handler_it == handlers_.end()) continue;
        
        Module* module = handler_it->second;
        if (!module) continue;
        
        try {
            module->handle_event(event.type, event.data);
        } catch (const std::exception& e) {
            EV3_ERROR("Error handling event '{}' in module '{}': {}", 
                      event.type, module_name, e.what());
        }
    }
}

void EventBus::emit_sync(std::string_view event_type, EventData data, std::string_view source) {
    Event event(event_type, std::move(data), source);
    deliver_event(event);
}

} // namespace ev3
