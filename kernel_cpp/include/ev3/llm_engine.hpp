/**
 * @file llm_engine.hpp
 * @brief LLM inference engine with persistent model loading
 * 
 * Direct integration with llama.cpp for high-performance local inference.
 * Models are loaded once at startup and kept in memory.
 */

#pragma once

#include "common.hpp"
#include "logger.hpp"
#include "task_queue.hpp"
#include "config.hpp"

// llama.cpp headers
#include "llama.h"

#include <filesystem>
#include <atomic>
#include <deque>

namespace ev3 {

/**
 * @brief Inference request parameters
 */
struct InferenceRequest {
    std::string prompt;
    int32_t max_tokens = 128;
    float temperature = 0.7f;
    float top_p = 0.9f;
    int32_t top_k = 40;
    float repeat_penalty = 1.1f;
    int32_t mirostat_mode = 0;  // 0=disabled, 1=mirostat, 2=mirostat2
    float mirostat_tau = 5.0f;
    float mirostat_eta = 0.1f;
    std::vector<std::string> stop_sequences;
    
    // Callbacks
    TokenCallback on_token;         // Called for each generated token (for streaming)
    CompletionCallback on_complete; // Called when generation completes
    
    // Cancellation token
    std::atomic<bool>* cancel_token = nullptr;
};

/**
 * @brief Model information
 */
struct ModelInfo {
    std::string path;
    std::string name;
    LlmMode mode;
    int64_t size_bytes = 0;
    int32_t context_length = 0;
    int32_t vocab_size = 0;
    bool loaded = false;
};

/**
 * @brief Persistent LLM model wrapper
 * 
 * Wraps a llama.cpp model with persistent context.
 * Thread-safe for concurrent inference requests.
 */
class LlmModel {
public:
    LlmModel() = default;
    ~LlmModel() { unload(); }
    
    // Non-copyable
    LlmModel(const LlmModel&) = delete;
    LlmModel& operator=(const LlmModel&) = delete;
    
    /**
     * @brief Load a GGUF model file
     */
    Result<void> load(const std::filesystem::path& model_path, const ConfigSection& config) {
        std::unique_lock lock(mutex_);
        
        if (model_) {
            return std::unexpected(make_error(
                ErrorCategory::LLM, 1, "Model already loaded"));
        }
        
        if (!std::filesystem::exists(model_path)) {
            return std::unexpected(make_error(
                ErrorCategory::LLM, 2, 
                std::format("Model file not found: {}", model_path.string())));
        }
        
        EV3_INFO("Loading LLM model: {}", model_path.string());
        auto start = now();
        
        // Initialize llama backend (once per process)
        static std::once_flag init_flag;
        std::call_once(init_flag, [] {
            llama_backend_init();
            EV3_INFO("llama.cpp backend initialized");
        });
        
        // Model parameters
        llama_model_params model_params = llama_model_default_params();
        
        // GPU layers
        bool use_gpu = config.get_or<bool>("use_gpu", true);
        int32_t gpu_layers = static_cast<int32_t>(config.get_or<int64_t>("gpu_layers", 35));
        model_params.n_gpu_layers = use_gpu ? gpu_layers : 0;
        
        // Load model
        model_ = llama_load_model_from_file(model_path.string().c_str(), model_params);
        if (!model_) {
            return std::unexpected(make_error(
                ErrorCategory::LLM, 3, "Failed to load model"));
        }
        
        // Context parameters
        llama_context_params ctx_params = llama_context_default_params();
        ctx_params.n_ctx = static_cast<uint32_t>(config.get_or<int64_t>("context_length", 512));
        ctx_params.n_batch = static_cast<uint32_t>(config.get_or<int64_t>("n_batch", 512));
        ctx_params.n_threads = static_cast<int32_t>(config.get_or<int64_t>("n_threads", 4));
        ctx_params.n_threads_batch = ctx_params.n_threads;
        ctx_params.flash_attn = true;  // Enable flash attention if available
        
        // Create context
        ctx_ = llama_new_context_with_model(model_, ctx_params);
        if (!ctx_) {
            llama_free_model(model_);
            model_ = nullptr;
            return std::unexpected(make_error(
                ErrorCategory::LLM, 4, "Failed to create context"));
        }
        
        // Store info
        info_.path = model_path.string();
        info_.name = model_path.stem().string();
        info_.context_length = ctx_params.n_ctx;
        info_.vocab_size = llama_n_vocab(model_);
        info_.size_bytes = std::filesystem::file_size(model_path);
        info_.loaded = true;
        
        auto load_time = elapsed_ms(start);
        EV3_INFO("Model loaded in {}ms: {} (vocab={}, ctx={})", 
                 load_time, info_.name, info_.vocab_size, info_.context_length);
        
        return {};
    }
    
    /**
     * @brief Unload the model and free resources
     */
    void unload() {
        std::unique_lock lock(mutex_);
        
        if (ctx_) {
            llama_free(ctx_);
            ctx_ = nullptr;
        }
        
        if (model_) {
            llama_free_model(model_);
            model_ = nullptr;
        }
        
        if (info_.loaded) {
            EV3_INFO("Model unloaded: {}", info_.name);
            info_.loaded = false;
        }
    }
    
    /**
     * @brief Check if model is loaded
     */
    [[nodiscard]] bool is_loaded() const {
        std::shared_lock lock(mutex_);
        return model_ != nullptr && ctx_ != nullptr;
    }
    
    /**
     * @brief Get model information
     */
    [[nodiscard]] const ModelInfo& info() const {
        std::shared_lock lock(mutex_);
        return info_;
    }
    
    /**
     * @brief Generate text from prompt
     * 
     * Thread-safe. Uses a mutex to serialize inference requests.
     * Supports streaming via callback and cancellation.
     */
    Result<std::string> generate(const InferenceRequest& request) {
        std::unique_lock lock(mutex_);
        
        if (!model_ || !ctx_) {
            return std::unexpected(make_error(
                ErrorCategory::LLM, 10, "Model not loaded"));
        }
        
        auto start = now();
        
        // Tokenize prompt
        std::vector<llama_token> tokens(info_.context_length);
        int n_tokens = llama_tokenize(
            model_,
            request.prompt.c_str(),
            static_cast<int32_t>(request.prompt.size()),
            tokens.data(),
            static_cast<int32_t>(tokens.size()),
            true,  // add_special
            true   // parse_special
        );
        
        if (n_tokens < 0) {
            return std::unexpected(make_error(
                ErrorCategory::LLM, 11, "Failed to tokenize prompt"));
        }
        
        tokens.resize(n_tokens);
        EV3_DEBUG("Tokenized prompt: {} tokens", n_tokens);
        
        // Check context size
        if (n_tokens > static_cast<int>(info_.context_length) - 4) {
            return std::unexpected(make_error(
                ErrorCategory::LLM, 12, "Prompt too long for context"));
        }
        
        // Clear KV cache for fresh context
        llama_kv_cache_clear(ctx_);
        
        // Create batch
        llama_batch batch = llama_batch_init(info_.context_length, 0, 1);
        auto batch_guard = make_scope_guard([&] { llama_batch_free(batch); });
        
        // Add prompt tokens to batch
        for (int i = 0; i < n_tokens; ++i) {
            llama_batch_add(batch, tokens[i], i, {0}, false);
        }
        batch.logits[batch.n_tokens - 1] = true;  // Enable logits for last token
        
        // Evaluate prompt
        if (llama_decode(ctx_, batch) != 0) {
            return std::unexpected(make_error(
                ErrorCategory::LLM, 13, "Failed to evaluate prompt"));
        }
        
        // Setup sampler
        auto sampler = create_sampler(request);
        auto sampler_guard = make_scope_guard([&] { llama_sampler_free(sampler); });
        
        // Generate tokens
        std::string output;
        int n_generated = 0;
        int n_cur = n_tokens;
        
        // Stop token detection
        std::vector<std::string> stop_seqs = request.stop_sequences;
        if (stop_seqs.empty()) {
            stop_seqs = {"</s>", "[/INST]", "<|end|>", "<|endoftext|>", "<|im_end|>"};
        }
        
        while (n_generated < request.max_tokens) {
            // Check cancellation
            if (request.cancel_token && 
                request.cancel_token->load(std::memory_order_acquire)) {
                EV3_DEBUG("Generation cancelled after {} tokens", n_generated);
                break;
            }
            
            // Sample next token
            llama_token new_token = llama_sampler_sample(sampler, ctx_, -1);
            
            // Check for end of generation
            if (llama_token_is_eog(model_, new_token)) {
                EV3_DEBUG("End of generation token");
                break;
            }
            
            // Convert token to text
            char buf[256];
            int n = llama_token_to_piece(model_, new_token, buf, sizeof(buf), 0, true);
            if (n < 0) {
                EV3_WARN("Failed to decode token {}", new_token);
                continue;
            }
            
            std::string piece(buf, n);
            output += piece;
            n_generated++;
            
            // Stream callback
            if (request.on_token) {
                if (!request.on_token(piece)) {
                    EV3_DEBUG("Streaming stopped by callback");
                    break;
                }
            }
            
            // Check stop sequences
            bool should_stop = false;
            for (const auto& stop : stop_seqs) {
                if (output.ends_with(stop)) {
                    // Remove stop sequence from output
                    output.resize(output.size() - stop.size());
                    should_stop = true;
                    break;
                }
            }
            if (should_stop) break;
            
            // Prepare next batch
            llama_batch_clear(batch);
            llama_batch_add(batch, new_token, n_cur, {0}, true);
            n_cur++;
            
            // Evaluate
            if (llama_decode(ctx_, batch) != 0) {
                return std::unexpected(make_error(
                    ErrorCategory::LLM, 14, "Failed during token generation"));
            }
        }
        
        auto gen_time = elapsed_ms(start);
        float tokens_per_sec = n_generated > 0 ? (n_generated * 1000.0f / gen_time) : 0;
        EV3_INFO("Generated {} tokens in {}ms ({:.1f} tok/s)", 
                 n_generated, gen_time, tokens_per_sec);
        
        return trim(output);
    }

private:
    llama_sampler* create_sampler(const InferenceRequest& request) {
        llama_sampler_chain_params chain_params = llama_sampler_chain_default_params();
        llama_sampler* sampler = llama_sampler_chain_init(chain_params);
        
        // Add samplers based on mode
        if (request.mirostat_mode == 1) {
            llama_sampler_chain_add(sampler, 
                llama_sampler_init_mirostat(
                    llama_n_vocab(model_),
                    0,  // seed
                    request.mirostat_tau,
                    request.mirostat_eta,
                    100  // m
                ));
        } else if (request.mirostat_mode == 2) {
            llama_sampler_chain_add(sampler,
                llama_sampler_init_mirostat_v2(
                    0,  // seed
                    request.mirostat_tau,
                    request.mirostat_eta
                ));
        } else {
            // Standard sampling chain
            llama_sampler_chain_add(sampler, llama_sampler_init_top_k(request.top_k));
            llama_sampler_chain_add(sampler, llama_sampler_init_top_p(request.top_p, 1));
            llama_sampler_chain_add(sampler, llama_sampler_init_temp(request.temperature));
            llama_sampler_chain_add(sampler, llama_sampler_init_dist(0));
        }
        
        // Add repetition penalty
        if (request.repeat_penalty != 1.0f) {
            llama_sampler_chain_add(sampler,
                llama_sampler_init_penalties(
                    64,                      // last_n
                    request.repeat_penalty,  // repeat
                    0.0f,                    // freq
                    0.0f                     // presence
                ));
        }
        
        return sampler;
    }
    
    mutable std::shared_mutex mutex_;
    llama_model* model_ = nullptr;
    llama_context* ctx_ = nullptr;
    ModelInfo info_;
};

/**
 * @brief Model manager for dual-mode LLM support
 * 
 * Manages persistent loading of fast (Phi-3) and deep (Mistral) models.
 */
class ModelManager {
public:
    ModelManager() = default;
    ~ModelManager() { shutdown(); }
    
    /**
     * @brief Initialize model manager with configuration
     */
    Result<void> initialize(const ConfigSection& config) {
        config_ = config;
        
        auto model_path = config.get_or<std::string>("model_path", "models/llm/");
        model_base_path_ = std::filesystem::path(model_path);
        
        // Determine initial mode
        auto mode_str = config.get_or<std::string>("mode", "fast");
        current_mode_ = (mode_str == "deep") ? LlmMode::Deep : LlmMode::Fast;
        
        // Load active model
        return load_model(current_mode_);
    }
    
    /**
     * @brief Load a specific model mode
     */
    Result<void> load_model(LlmMode mode) {
        std::string filename;
        const ConfigSection* section_config = &config_;
        
        if (mode == LlmMode::Fast) {
            filename = config_.get_or<std::string>("fast_model", "Phi-3-mini-4k-instruct-q4.gguf");
        } else {
            filename = config_.get_or<std::string>("deep_model", "mistral-7b-instruct-v0.2.Q4_K_M.gguf");
        }
        
        auto full_path = model_base_path_ / filename;
        
        // Get appropriate model slot
        auto& model = (mode == LlmMode::Fast) ? fast_model_ : deep_model_;
        
        if (auto result = model.load(full_path, config_); !result) {
            return result;
        }
        
        current_mode_ = mode;
        EV3_INFO("Model manager: {} mode active", to_string(mode));
        
        return {};
    }
    
    /**
     * @brief Switch to a different model mode
     */
    Result<void> switch_mode(LlmMode mode) {
        if (mode == current_mode_ && get_active_model().is_loaded()) {
            return {};  // Already on this mode
        }
        
        // Load if not already loaded
        auto& model = (mode == LlmMode::Fast) ? fast_model_ : deep_model_;
        if (!model.is_loaded()) {
            if (auto result = load_model(mode); !result) {
                return result;
            }
        }
        
        current_mode_ = mode;
        EV3_INFO("Switched to {} mode", to_string(mode));
        return {};
    }
    
    /**
     * @brief Get the currently active model
     */
    [[nodiscard]] LlmModel& get_active_model() {
        return (current_mode_ == LlmMode::Fast) ? fast_model_ : deep_model_;
    }
    
    /**
     * @brief Get current mode
     */
    [[nodiscard]] LlmMode current_mode() const noexcept { return current_mode_; }
    
    /**
     * @brief Generate response using active model
     */
    Result<std::string> generate(const InferenceRequest& request) {
        return get_active_model().generate(request);
    }
    
    /**
     * @brief Shutdown and unload all models
     */
    void shutdown() {
        fast_model_.unload();
        deep_model_.unload();
        EV3_INFO("Model manager shutdown");
    }

private:
    ConfigSection config_;
    std::filesystem::path model_base_path_;
    LlmMode current_mode_ = LlmMode::Fast;
    
    LlmModel fast_model_;
    LlmModel deep_model_;
};

/**
 * @brief Async inference engine with task queue
 * 
 * Wraps ModelManager with async task submission for non-blocking inference.
 */
class InferenceEngine {
public:
    InferenceEngine() : task_queue_(1) {}  // Single worker for serialized inference
    
    ~InferenceEngine() { shutdown(); }
    
    /**
     * @brief Initialize the inference engine
     */
    Result<void> initialize(const ConfigSection& config) {
        if (auto result = model_manager_.initialize(config); !result) {
            return result;
        }
        
        task_queue_.start();
        initialized_ = true;
        EV3_INFO("Inference engine initialized");
        return {};
    }
    
    /**
     * @brief Submit an inference request (non-blocking)
     * @return Handle for tracking/cancelling the request
     */
    TaskHandle submit(InferenceRequest request) {
        return task_queue_.submit([this, req = std::move(request)]() mutable {
            auto result = model_manager_.generate(req);
            
            if (req.on_complete) {
                req.on_complete(std::move(result));
            }
        }, TaskPriority::Normal);
    }
    
    /**
     * @brief Generate synchronously (blocks until complete)
     */
    Result<std::string> generate_sync(const InferenceRequest& request) {
        return model_manager_.generate(request);
    }
    
    /**
     * @brief Switch model mode
     */
    Result<void> switch_mode(LlmMode mode) {
        return model_manager_.switch_mode(mode);
    }
    
    /**
     * @brief Get current mode
     */
    [[nodiscard]] LlmMode current_mode() const noexcept {
        return model_manager_.current_mode();
    }
    
    /**
     * @brief Check if engine is ready
     */
    [[nodiscard]] bool is_ready() const noexcept { return initialized_; }
    
    /**
     * @brief Shutdown the engine
     */
    void shutdown() {
        if (!initialized_) return;
        
        task_queue_.stop();
        model_manager_.shutdown();
        initialized_ = false;
        
        EV3_INFO("Inference engine shutdown");
    }

private:
    ModelManager model_manager_;
    TaskQueue task_queue_;
    bool initialized_ = false;
};

} // namespace ev3
