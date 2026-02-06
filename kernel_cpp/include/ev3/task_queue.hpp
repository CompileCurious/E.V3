/**
 * @file task_queue.hpp
 * @brief Async task queue with worker thread pool for E.V3 kernel
 */

#pragma once

#include "common.hpp"
#include "logger.hpp"
#include <queue>
#include <future>
#include <thread>

namespace ev3 {

/**
 * @brief Unique task identifier
 */
using TaskId = uint64_t;

/**
 * @brief Task descriptor
 */
struct Task {
    TaskId id;
    TaskPriority priority;
    std::function<void()> work;
    std::atomic<TaskStatus>* status;
    std::atomic<bool>* cancelled;
    TimePoint queued_at;
    
    // Priority comparison for priority queue (higher priority first)
    bool operator<(const Task& other) const {
        return static_cast<int>(priority) < static_cast<int>(other.priority);
    }
};

/**
 * @brief Handle for tracking and cancelling tasks
 */
class TaskHandle {
public:
    TaskHandle() : id_(0), status_(nullptr), cancelled_(nullptr) {}
    
    TaskHandle(TaskId id, std::shared_ptr<std::atomic<TaskStatus>> status,
               std::shared_ptr<std::atomic<bool>> cancelled)
        : id_(id), status_(std::move(status)), cancelled_(std::move(cancelled)) {}
    
    [[nodiscard]] TaskId id() const noexcept { return id_; }
    
    [[nodiscard]] TaskStatus status() const noexcept {
        return status_ ? status_->load(std::memory_order_acquire) : TaskStatus::Failed;
    }
    
    [[nodiscard]] bool is_pending() const noexcept {
        return status() == TaskStatus::Pending;
    }
    
    [[nodiscard]] bool is_running() const noexcept {
        return status() == TaskStatus::Running;
    }
    
    [[nodiscard]] bool is_done() const noexcept {
        auto s = status();
        return s == TaskStatus::Completed || s == TaskStatus::Cancelled || s == TaskStatus::Failed;
    }
    
    /**
     * @brief Request cancellation of this task
     */
    bool cancel() {
        if (!cancelled_) return false;
        cancelled_->store(true, std::memory_order_release);
        return true;
    }
    
    [[nodiscard]] bool is_cancelled() const noexcept {
        return cancelled_ && cancelled_->load(std::memory_order_acquire);
    }

private:
    TaskId id_;
    std::shared_ptr<std::atomic<TaskStatus>> status_;
    std::shared_ptr<std::atomic<bool>> cancelled_;
};

/**
 * @brief Thread-safe task queue with worker pool
 * 
 * Provides asynchronous task execution with:
 * - Priority scheduling
 * - Task cancellation
 * - Worker thread pool
 * - Non-blocking submission
 */
class TaskQueue {
public:
    explicit TaskQueue(size_t num_workers = 0)
        : num_workers_(num_workers == 0 ? std::thread::hardware_concurrency() : num_workers)
        , next_id_(1) {}
    
    ~TaskQueue() { stop(); }
    
    // Non-copyable
    TaskQueue(const TaskQueue&) = delete;
    TaskQueue& operator=(const TaskQueue&) = delete;
    
    /**
     * @brief Start the worker threads
     */
    void start() {
        if (running_.load(std::memory_order_acquire)) return;
        
        running_.store(true, std::memory_order_release);
        
        workers_.reserve(num_workers_);
        for (size_t i = 0; i < num_workers_; ++i) {
            workers_.emplace_back([this, i] { worker_loop(i); });
        }
        
        EV3_INFO("Task queue started with {} workers", num_workers_);
    }
    
    /**
     * @brief Stop all workers and clear pending tasks
     */
    void stop() {
        if (!running_.exchange(false, std::memory_order_acq_rel)) return;
        
        cv_.notify_all();
        
        for (auto& worker : workers_) {
            if (worker.joinable()) {
                worker.join();
            }
        }
        workers_.clear();
        
        // Clear pending tasks
        {
            std::unique_lock lock(mutex_);
            while (!queue_.empty()) {
                queue_.pop();
            }
        }
        
        EV3_INFO("Task queue stopped");
    }
    
    /**
     * @brief Submit a task for execution
     * @return Handle for tracking/cancelling the task
     */
    template <typename F>
    TaskHandle submit(F&& work, TaskPriority priority = TaskPriority::Normal) {
        auto status = std::make_shared<std::atomic<TaskStatus>>(TaskStatus::Pending);
        auto cancelled = std::make_shared<std::atomic<bool>>(false);
        
        TaskId id = next_id_.fetch_add(1, std::memory_order_relaxed);
        
        Task task{
            .id = id,
            .priority = priority,
            .work = [work = std::forward<F>(work), status, cancelled]() mutable {
                if (cancelled->load(std::memory_order_acquire)) {
                    status->store(TaskStatus::Cancelled, std::memory_order_release);
                    return;
                }
                
                status->store(TaskStatus::Running, std::memory_order_release);
                
                try {
                    work();
                    status->store(TaskStatus::Completed, std::memory_order_release);
                } catch (const std::exception& e) {
                    EV3_ERROR("Task failed with exception: {}", e.what());
                    status->store(TaskStatus::Failed, std::memory_order_release);
                }
            },
            .status = status.get(),
            .cancelled = cancelled.get(),
            .queued_at = now()
        };
        
        {
            std::unique_lock lock(mutex_);
            queue_.push(std::move(task));
        }
        
        cv_.notify_one();
        
        return TaskHandle(id, std::move(status), std::move(cancelled));
    }
    
    /**
     * @brief Submit a task and get a future for the result
     */
    template <typename F, typename R = std::invoke_result_t<F>>
    std::pair<TaskHandle, std::future<R>> submit_with_result(F&& work, TaskPriority priority = TaskPriority::Normal) {
        auto promise = std::make_shared<std::promise<R>>();
        auto future = promise->get_future();
        
        auto handle = submit([work = std::forward<F>(work), promise]() mutable {
            try {
                if constexpr (std::is_void_v<R>) {
                    work();
                    promise->set_value();
                } else {
                    promise->set_value(work());
                }
            } catch (...) {
                promise->set_exception(std::current_exception());
            }
        }, priority);
        
        return {std::move(handle), std::move(future)};
    }
    
    /**
     * @brief Get the number of pending tasks
     */
    [[nodiscard]] size_t pending_count() const {
        std::unique_lock lock(mutex_);
        return queue_.size();
    }
    
    /**
     * @brief Get the number of worker threads
     */
    [[nodiscard]] size_t worker_count() const noexcept { return num_workers_; }

private:
    void worker_loop(size_t worker_id) {
        EV3_DEBUG("Worker {} started", worker_id);
        
        while (running_.load(std::memory_order_acquire)) {
            Task task;
            
            {
                std::unique_lock lock(mutex_);
                cv_.wait(lock, [this] {
                    return !running_.load(std::memory_order_acquire) || !queue_.empty();
                });
                
                if (!running_.load(std::memory_order_acquire) && queue_.empty()) {
                    break;
                }
                
                if (queue_.empty()) continue;
                
                task = std::move(const_cast<Task&>(queue_.top()));
                queue_.pop();
            }
            
            // Execute the task
            if (task.work) {
                task.work();
            }
        }
        
        EV3_DEBUG("Worker {} stopped", worker_id);
    }
    
    size_t num_workers_;
    std::atomic<TaskId> next_id_;
    std::atomic<bool> running_{false};
    
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    std::priority_queue<Task> queue_;
    std::vector<std::thread> workers_;
};

} // namespace ev3
