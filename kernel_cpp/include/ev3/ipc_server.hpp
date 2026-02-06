/**
 * @file ipc_server.hpp
 * @brief Windows Named Pipe IPC server for shell communication
 */

#pragma once

#include "common.hpp"
#include "logger.hpp"

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#endif

#include <thread>
#include <queue>
#include <functional>

namespace ev3 {

/**
 * @brief JSON-like message structure for IPC
 */
struct IpcMessage {
    std::string type;
    std::unordered_map<std::string, std::string> data;
    
    /**
     * @brief Serialize to JSON string
     */
    [[nodiscard]] std::string to_json() const {
        std::string json = "{\"type\":\"" + escape_json(type) + "\",\"data\":{";
        bool first = true;
        for (const auto& [key, value] : data) {
            if (!first) json += ",";
            json += "\"" + escape_json(key) + "\":\"" + escape_json(value) + "\"";
            first = false;
        }
        json += "}}";
        return json;
    }
    
    /**
     * @brief Parse from JSON string (simple parser)
     */
    static std::optional<IpcMessage> from_json(std::string_view json) {
        IpcMessage msg;
        
        // Find type
        auto type_start = json.find("\"type\":");
        if (type_start == std::string_view::npos) return std::nullopt;
        
        auto type_val_start = json.find('"', type_start + 7);
        auto type_val_end = json.find('"', type_val_start + 1);
        if (type_val_start == std::string_view::npos || type_val_end == std::string_view::npos) {
            return std::nullopt;
        }
        msg.type = std::string(json.substr(type_val_start + 1, type_val_end - type_val_start - 1));
        
        // Find data object
        auto data_start = json.find("\"data\":{");
        if (data_start == std::string_view::npos) return msg;  // No data is ok
        
        auto data_obj_start = json.find('{', data_start);
        auto data_obj_end = json.find('}', data_obj_start);
        if (data_obj_start == std::string_view::npos || data_obj_end == std::string_view::npos) {
            return msg;
        }
        
        // Parse key-value pairs
        auto data_content = json.substr(data_obj_start + 1, data_obj_end - data_obj_start - 1);
        size_t pos = 0;
        while (pos < data_content.size()) {
            // Find key
            auto key_start = data_content.find('"', pos);
            if (key_start == std::string_view::npos) break;
            auto key_end = data_content.find('"', key_start + 1);
            if (key_end == std::string_view::npos) break;
            
            std::string key(data_content.substr(key_start + 1, key_end - key_start - 1));
            
            // Find value
            auto val_start = data_content.find('"', key_end + 2);  // Skip ":"
            if (val_start == std::string_view::npos) break;
            auto val_end = data_content.find('"', val_start + 1);
            if (val_end == std::string_view::npos) break;
            
            std::string value(data_content.substr(val_start + 1, val_end - val_start - 1));
            msg.data[unescape_json(key)] = unescape_json(value);
            
            pos = val_end + 1;
        }
        
        return msg;
    }

private:
    [[nodiscard]] static std::string escape_json(std::string_view s) {
        std::string result;
        result.reserve(s.size());
        for (char c : s) {
            switch (c) {
                case '"': result += "\\\""; break;
                case '\\': result += "\\\\"; break;
                case '\n': result += "\\n"; break;
                case '\r': result += "\\r"; break;
                case '\t': result += "\\t"; break;
                default: result += c;
            }
        }
        return result;
    }
    
    [[nodiscard]] static std::string unescape_json(std::string_view s) {
        std::string result;
        result.reserve(s.size());
        for (size_t i = 0; i < s.size(); ++i) {
            if (s[i] == '\\' && i + 1 < s.size()) {
                switch (s[i + 1]) {
                    case '"': result += '"'; ++i; break;
                    case '\\': result += '\\'; ++i; break;
                    case 'n': result += '\n'; ++i; break;
                    case 'r': result += '\r'; ++i; break;
                    case 't': result += '\t'; ++i; break;
                    default: result += s[i];
                }
            } else {
                result += s[i];
            }
        }
        return result;
    }
};

/**
 * @brief Message handler callback type
 */
using IpcMessageHandler = std::function<void(const IpcMessage&)>;

#ifdef _WIN32

/**
 * @brief Windows Named Pipe IPC Server
 * 
 * Compatible with the existing Python shell's IPCClient.
 * Privacy: All communication is local-only via named pipes.
 */
class IpcServer {
public:
    IpcServer(std::string_view pipe_name = R"(\\.\pipe\E.V3.v2)", 
              size_t buffer_size = 4096)
        : pipe_name_(pipe_name)
        , buffer_size_(buffer_size) {}
    
    ~IpcServer() { stop(); }
    
    // Non-copyable
    IpcServer(const IpcServer&) = delete;
    IpcServer& operator=(const IpcServer&) = delete;
    
    /**
     * @brief Register a handler for a message type
     */
    void register_handler(std::string_view type, IpcMessageHandler handler) {
        std::unique_lock lock(handlers_mutex_);
        handlers_[std::string(type)] = std::move(handler);
        EV3_DEBUG("Registered IPC handler for: {}", type);
    }
    
    /**
     * @brief Start the IPC server
     */
    void start() {
        if (running_.load(std::memory_order_acquire)) return;
        
        running_.store(true, std::memory_order_release);
        server_thread_ = std::thread([this] { run_server(); });
        EV3_INFO("IPC server started on: {}", pipe_name_);
    }
    
    /**
     * @brief Stop the IPC server
     */
    void stop() {
        if (!running_.exchange(false, std::memory_order_acq_rel)) return;
        
        // Signal shutdown by connecting to our own pipe
        HANDLE dummy = CreateFileA(
            pipe_name_.c_str(),
            GENERIC_READ | GENERIC_WRITE,
            0, nullptr, OPEN_EXISTING, 0, nullptr);
        if (dummy != INVALID_HANDLE_VALUE) {
            CloseHandle(dummy);
        }
        
        if (server_thread_.joinable()) {
            server_thread_.join();
        }
        
        EV3_INFO("IPC server stopped");
    }
    
    /**
     * @brief Send a message to connected client
     */
    bool send_message(const IpcMessage& msg) {
        std::unique_lock lock(pipe_mutex_);
        
        if (current_pipe_ == INVALID_HANDLE_VALUE || !client_connected_) {
            EV3_WARN("Cannot send message: no client connected");
            return false;
        }
        
        std::string json = msg.to_json();
        DWORD bytes_written;
        
        BOOL success = WriteFile(
            current_pipe_,
            json.c_str(),
            static_cast<DWORD>(json.size()),
            &bytes_written,
            nullptr);
        
        if (!success) {
            EV3_ERROR("Failed to send IPC message: {}", GetLastError());
            return false;
        }
        
        EV3_DEBUG("Sent IPC message: type={}", msg.type);
        return true;
    }
    
    /**
     * @brief Queue a message to send
     */
    void queue_message(IpcMessage msg) {
        {
            std::unique_lock lock(outbound_mutex_);
            outbound_queue_.push(std::move(msg));
        }
        outbound_cv_.notify_one();
    }
    
    /**
     * @brief Check if client is connected
     */
    [[nodiscard]] bool is_client_connected() const noexcept {
        return client_connected_.load(std::memory_order_acquire);
    }

private:
    void run_server() {
        while (running_.load(std::memory_order_acquire)) {
            // Create named pipe
            HANDLE pipe = CreateNamedPipeA(
                pipe_name_.c_str(),
                PIPE_ACCESS_DUPLEX,
                PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
                5,  // Max instances
                static_cast<DWORD>(buffer_size_),
                static_cast<DWORD>(buffer_size_),
                0,
                nullptr);
            
            if (pipe == INVALID_HANDLE_VALUE) {
                EV3_ERROR("Failed to create named pipe: {}", GetLastError());
                std::this_thread::sleep_for(std::chrono::seconds(2));
                continue;
            }
            
            EV3_DEBUG("Waiting for client connection...");
            
            // Wait for client
            BOOL connected = ConnectNamedPipe(pipe, nullptr) || 
                             (GetLastError() == ERROR_PIPE_CONNECTED);
            
            if (!running_.load(std::memory_order_acquire)) {
                CloseHandle(pipe);
                break;
            }
            
            if (connected) {
                EV3_INFO("Client connected");
                
                {
                    std::unique_lock lock(pipe_mutex_);
                    current_pipe_ = pipe;
                    client_connected_.store(true, std::memory_order_release);
                }
                
                // Handle client communication
                handle_client(pipe);
                
                {
                    std::unique_lock lock(pipe_mutex_);
                    client_connected_.store(false, std::memory_order_release);
                    current_pipe_ = INVALID_HANDLE_VALUE;
                }
                
                EV3_INFO("Client disconnected");
            }
            
            DisconnectNamedPipe(pipe);
            CloseHandle(pipe);
        }
    }
    
    void handle_client(HANDLE pipe) {
        std::vector<char> buffer(buffer_size_);
        
        while (running_.load(std::memory_order_acquire)) {
            // Check for incoming data (non-blocking peek)
            DWORD bytes_available = 0;
            if (!PeekNamedPipe(pipe, nullptr, 0, nullptr, &bytes_available, nullptr)) {
                DWORD error = GetLastError();
                if (error == ERROR_BROKEN_PIPE) {
                    break;  // Client disconnected
                }
            }
            
            if (bytes_available > 0) {
                DWORD bytes_read;
                BOOL success = ReadFile(
                    pipe,
                    buffer.data(),
                    static_cast<DWORD>(buffer.size() - 1),
                    &bytes_read,
                    nullptr);
                
                if (!success) {
                    DWORD error = GetLastError();
                    if (error == ERROR_BROKEN_PIPE) {
                        break;  // Client disconnected
                    }
                    EV3_WARN("Read error: {}", error);
                    continue;
                }
                
                if (bytes_read > 0) {
                    buffer[bytes_read] = '\0';
                    process_message(std::string_view(buffer.data(), bytes_read));
                }
            }
            
            // Send queued messages
            send_queued_messages();
            
            // Small sleep to prevent busy loop
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    }
    
    void process_message(std::string_view json) {
        auto msg = IpcMessage::from_json(json);
        if (!msg) {
            EV3_WARN("Failed to parse IPC message: {}", json);
            return;
        }
        
        EV3_DEBUG("Received IPC message: type={}", msg->type);
        
        std::shared_lock lock(handlers_mutex_);
        auto it = handlers_.find(msg->type);
        if (it != handlers_.end()) {
            try {
                it->second(*msg);
            } catch (const std::exception& e) {
                EV3_ERROR("IPC handler error for '{}': {}", msg->type, e.what());
            }
        } else {
            EV3_WARN("No handler for message type: {}", msg->type);
        }
    }
    
    void send_queued_messages() {
        std::unique_lock lock(outbound_mutex_);
        
        while (!outbound_queue_.empty()) {
            auto msg = std::move(outbound_queue_.front());
            outbound_queue_.pop();
            lock.unlock();
            
            send_message(msg);
            
            lock.lock();
        }
    }
    
    std::string pipe_name_;
    size_t buffer_size_;
    
    std::atomic<bool> running_{false};
    std::atomic<bool> client_connected_{false};
    std::thread server_thread_;
    
    std::mutex pipe_mutex_;
    HANDLE current_pipe_ = INVALID_HANDLE_VALUE;
    
    std::shared_mutex handlers_mutex_;
    std::unordered_map<std::string, IpcMessageHandler> handlers_;
    
    std::mutex outbound_mutex_;
    std::condition_variable outbound_cv_;
    std::queue<IpcMessage> outbound_queue_;
};

#else
// Stub for non-Windows platforms
class IpcServer {
public:
    IpcServer(std::string_view = "", size_t = 4096) {}
    void register_handler(std::string_view, IpcMessageHandler) {}
    void start() { EV3_ERROR("IPC not supported on this platform"); }
    void stop() {}
    bool send_message(const IpcMessage&) { return false; }
    void queue_message(IpcMessage) {}
    bool is_client_connected() const { return false; }
};
#endif

} // namespace ev3
