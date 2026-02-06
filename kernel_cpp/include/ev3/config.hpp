/**
 * @file config.hpp
 * @brief Configuration management for E.V3 C++ Kernel
 */

#pragma once

#include "common.hpp"
#include "logger.hpp"
#include <fstream>
#include <filesystem>

// We'll use a simple YAML-like parser for config
// For production, consider yaml-cpp or similar

namespace ev3 {

/**
 * @brief Configuration value type
 */
using ConfigValue = std::variant<
    std::nullptr_t,
    bool,
    int64_t,
    double,
    std::string
>;

/**
 * @brief Configuration section
 */
class ConfigSection {
public:
    ConfigSection() = default;
    
    void set(std::string_view key, ConfigValue value) {
        values_[std::string(key)] = std::move(value);
    }
    
    template <typename T>
    [[nodiscard]] std::optional<T> get(std::string_view key) const {
        auto it = values_.find(std::string(key));
        if (it == values_.end()) return std::nullopt;
        if (auto* val = std::get_if<T>(&it->second)) {
            return *val;
        }
        return std::nullopt;
    }
    
    template <typename T>
    [[nodiscard]] T get_or(std::string_view key, T default_value) const {
        return get<T>(key).value_or(std::move(default_value));
    }
    
    [[nodiscard]] bool has(std::string_view key) const {
        return values_.contains(std::string(key));
    }
    
    [[nodiscard]] ConfigSection& subsection(std::string_view name) {
        return subsections_[std::string(name)];
    }
    
    [[nodiscard]] const ConfigSection* subsection_ptr(std::string_view name) const {
        auto it = subsections_.find(std::string(name));
        return it != subsections_.end() ? &it->second : nullptr;
    }

private:
    std::unordered_map<std::string, ConfigValue> values_;
    std::unordered_map<std::string, ConfigSection> subsections_;
};

/**
 * @brief Configuration manager
 */
class Config {
public:
    Config() = default;
    
    /**
     * @brief Load configuration from YAML file
     */
    Result<void> load(const std::filesystem::path& path) {
        std::ifstream file(path);
        if (!file) {
            return std::unexpected(make_error(
                ErrorCategory::Config, 1, 
                std::format("Failed to open config file: {}", path.string())));
        }
        
        EV3_INFO("Loading configuration from: {}", path.string());
        
        // Simple line-by-line parser (handles basic YAML)
        std::string line;
        std::string current_section;
        std::string current_subsection;
        int line_num = 0;
        
        while (std::getline(file, line)) {
            line_num++;
            
            // Skip empty lines and comments
            auto trimmed = trim(line);
            if (trimmed.empty() || trimmed[0] == '#') continue;
            
            // Detect indentation level
            size_t indent = 0;
            for (char c : line) {
                if (c == ' ') indent++;
                else if (c == '\t') indent += 2;
                else break;
            }
            
            // Parse key: value
            auto colon_pos = trimmed.find(':');
            if (colon_pos == std::string::npos) continue;
            
            std::string key = trim(trimmed.substr(0, colon_pos));
            std::string value_str = trim(trimmed.substr(colon_pos + 1));
            
            // Section header (no value)
            if (value_str.empty()) {
                if (indent == 0) {
                    current_section = key;
                    current_subsection.clear();
                } else {
                    current_subsection = key;
                }
                continue;
            }
            
            // Parse value
            ConfigValue value = parse_value(value_str);
            
            // Store in appropriate section
            if (current_section.empty()) {
                root_.set(key, std::move(value));
            } else if (current_subsection.empty()) {
                root_.subsection(current_section).set(key, std::move(value));
            } else {
                root_.subsection(current_section).subsection(current_subsection).set(key, std::move(value));
            }
        }
        
        loaded_ = true;
        EV3_INFO("Configuration loaded successfully");
        return {};
    }
    
    /**
     * @brief Get the root configuration section
     */
    [[nodiscard]] ConfigSection& root() { return root_; }
    [[nodiscard]] const ConfigSection& root() const { return root_; }
    
    /**
     * @brief Get a named section
     */
    [[nodiscard]] ConfigSection& section(std::string_view name) {
        return root_.subsection(name);
    }
    
    [[nodiscard]] const ConfigSection* section_ptr(std::string_view name) const {
        return root_.subsection_ptr(name);
    }
    
    [[nodiscard]] bool loaded() const noexcept { return loaded_; }
    
private:
    [[nodiscard]] static ConfigValue parse_value(std::string_view str) {
        // Boolean
        if (str == "true" || str == "True" || str == "yes") return true;
        if (str == "false" || str == "False" || str == "no") return false;
        
        // Null
        if (str == "null" || str == "~") return nullptr;
        
        // Try integer
        try {
            size_t pos;
            int64_t i = std::stoll(std::string(str), &pos);
            if (pos == str.size()) return i;
        } catch (...) {}
        
        // Try double
        try {
            size_t pos;
            double d = std::stod(std::string(str), &pos);
            if (pos == str.size()) return d;
        } catch (...) {}
        
        // String (remove quotes if present)
        std::string s(str);
        if (s.size() >= 2 && ((s.front() == '"' && s.back() == '"') ||
                              (s.front() == '\'' && s.back() == '\''))) {
            s = s.substr(1, s.size() - 2);
        }
        return s;
    }
    
    ConfigSection root_;
    bool loaded_ = false;
};

} // namespace ev3
