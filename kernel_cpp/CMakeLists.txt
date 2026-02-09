# E.V3 C++ Kernel
# CMake build configuration
#
# Requirements:
# - CMake 3.21+
# - C++20 compatible compiler (MSVC 2022, GCC 12+, Clang 14+)
# - llama.cpp (fetched automatically or provide LLAMA_CPP_DIR)
#
# Build:
#   mkdir build && cd build
#   cmake .. -DCMAKE_BUILD_TYPE=Release
#   cmake --build . --config Release
#
# Options:
#   -DLLAMA_CUBLAS=ON         Enable CUDA GPU acceleration
#   -DLLAMA_CPP_DIR=<path>    Use existing llama.cpp directory
#   -DBUILD_SHARED_LIBS=ON    Build shared library

cmake_minimum_required(VERSION 3.21)

# Use Clang compiler if available
if(NOT CMAKE_CXX_COMPILER)
    find_program(CLANG_CXX clang++)
    if(CLANG_CXX)
        set(CMAKE_CXX_COMPILER ${CLANG_CXX})
    endif()
endif()

if(NOT CMAKE_C_COMPILER)
    find_program(CLANG_C clang)
    if(CLANG_C)
        set(CMAKE_C_COMPILER ${CLANG_C})
    endif()
endif()

# Disable manifest requirement which needs RC compiler
if(MSVC OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    if(MSVC)
        add_link_options(/MANIFEST:NO)
    endif()
endif()

project(EV3Kernel
    VERSION 2.0.0
    DESCRIPTION "E.V3 High-Performance C++ Kernel"
    LANGUAGES CXX
)

# ============================================================================
# Options
# ============================================================================

option(LLAMA_CUBLAS "Build with CUDA GPU support" OFF)
option(LLAMA_METAL "Build with Metal GPU support (macOS)" OFF)
option(BUILD_SHARED_LIBS "Build shared library" OFF)
option(EV3_BUILD_TESTS "Build tests" OFF)

set(LLAMA_CPP_DIR "" CACHE PATH "Path to existing llama.cpp directory")

# ============================================================================
# C++ Standard
# ============================================================================

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile commands for IDE support
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ============================================================================
# Compiler Flags
# ============================================================================

if(MSVC)
    add_compile_options(
        /W4             # High warning level
        /permissive-    # Strict conformance
        /Zc:__cplusplus # Correct __cplusplus macro
        /utf-8          # UTF-8 source and execution charset
        /MP             # Multi-processor compilation
    )
    
    # Release optimizations
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        add_compile_options(/O2 /Ob2 /Oi /Ot /GL)
        add_link_options(/LTCG)
    endif()
else()
    add_compile_options(
        -Wall
        -Wextra
        -Wpedantic
        -Wno-unused-parameter
    )
    
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        add_compile_options(-O3 -march=native -flto)
        add_link_options(-flto)
    endif()
endif()

# ============================================================================
# llama.cpp Dependency
# ============================================================================

if(LLAMA_CPP_DIR)
    # Use provided llama.cpp directory
    message(STATUS "Using llama.cpp from: ${LLAMA_CPP_DIR}")
    add_subdirectory(${LLAMA_CPP_DIR} llama.cpp EXCLUDE_FROM_ALL)
else()
    # Fetch llama.cpp
    include(FetchContent)
    
    message(STATUS "Fetching llama.cpp...")
    FetchContent_Declare(
        llama_cpp
        GIT_REPOSITORY https://github.com/ggerganov/llama.cpp.git
        GIT_TAG        master
        GIT_SHALLOW    TRUE
    )
    
    # Configure llama.cpp build options
    set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    set(LLAMA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)
    
    if(LLAMA_CUBLAS)
        set(LLAMA_CUDA ON CACHE BOOL "" FORCE)
    endif()
    
    if(LLAMA_METAL)
        set(LLAMA_METAL ON CACHE BOOL "" FORCE)
    endif()
    
    FetchContent_MakeAvailable(llama_cpp)
endif()

# ============================================================================
# E.V3 Kernel Library
# ============================================================================

set(EV3_SOURCES
    src/event_bus.cpp
)

set(EV3_HEADERS
    include/ev3/common.hpp
    include/ev3/logger.hpp
    include/ev3/config.hpp
    include/ev3/event_bus.hpp
    include/ev3/module.hpp
    include/ev3/task_queue.hpp
    include/ev3/llm_engine.hpp
    include/ev3/ipc_server.hpp
    include/ev3/kernel.hpp
    include/ev3/ev3.hpp
)

add_library(ev3_kernel ${EV3_SOURCES} ${EV3_HEADERS})

target_include_directories(ev3_kernel
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(ev3_kernel
    PUBLIC
        llama
)

# Windows-specific libraries
if(WIN32)
    target_link_libraries(ev3_kernel
        PUBLIC
            ws2_32
    )
endif()

# Set output name
set_target_properties(ev3_kernel PROPERTIES
    OUTPUT_NAME "ev3kernel"
    DEBUG_POSTFIX "d"
)

# ============================================================================
# E.V3 Kernel Executable
# ============================================================================

add_executable(ev3_kernel_exe src/main.cpp)

target_link_libraries(ev3_kernel_exe
    PRIVATE
        ev3_kernel
)

set_target_properties(ev3_kernel_exe PROPERTIES
    OUTPUT_NAME "EV3Kernel"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/../dist/Kernel"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_SOURCE_DIR}/../dist/Kernel"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/../dist/Kernel"
)

# Copy config and models directories for development
add_custom_command(TARGET ev3_kernel_exe POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CMAKE_SOURCE_DIR}/../config"
        "${CMAKE_BINARY_DIR}/bin/config"
    COMMENT "Copying config directory..."
)

# ============================================================================
# Python Extension Module (optional)
# ============================================================================

find_package(Python3 COMPONENTS Interpreter Development)

if(Python3_FOUND AND Python3_Development_FOUND)
    message(STATUS "Python found: ${Python3_EXECUTABLE}")
    message(STATUS "Building Python extension module...")
    
    add_library(ev3_kernel_python MODULE
        src/python_bindings.cpp
    )
    
    target_link_libraries(ev3_kernel_python
        PRIVATE
            ev3_kernel
            Python3::Python
    )
    
    set_target_properties(ev3_kernel_python PROPERTIES
        PREFIX ""
        OUTPUT_NAME "ev3_kernel_cpp"
        SUFFIX "${Python3_SOABI}"
    )
    
    if(WIN32)
        set_target_properties(ev3_kernel_python PROPERTIES
            SUFFIX ".pyd"
        )
    endif()
else()
    message(STATUS "Python development files not found, skipping Python bindings")
endif()

# ============================================================================
# Installation (Commented out - not needed for local builds)
# ============================================================================

# include(GNUInstallDirs)

# install(TARGETS ev3_kernel ev3_kernel_exe
#     EXPORT EV3KernelTargets
#     LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
#     ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
#     RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
# )

# install(DIRECTORY include/
#     DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
# )

# install(EXPORT EV3KernelTargets
#     FILE EV3KernelTargets.cmake
#     NAMESPACE EV3::
#     DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/EV3Kernel
# )

# ============================================================================
# Package Configuration (Commented out - not needed for local builds)
# ============================================================================

# include(CMakePackageConfigHelpers)

# configure_package_config_file(
#     "${CMAKE_CURRENT_SOURCE_DIR}/cmake/EV3KernelConfig.cmake.in"
#     "${CMAKE_CURRENT_BINARY_DIR}/EV3KernelConfig.cmake"
#     INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/EV3Kernel
# )

# write_basic_package_version_file(
#     "${CMAKE_CURRENT_BINARY_DIR}/EV3KernelConfigVersion.cmake"
#     VERSION ${PROJECT_VERSION}
#     COMPATIBILITY SameMajorVersion
# )

# install(FILES
#     "${CMAKE_CURRENT_BINARY_DIR}/EV3KernelConfig.cmake"
#     "${CMAKE_CURRENT_BINARY_DIR}/EV3KernelConfigVersion.cmake"
#     DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/EV3Kernel
# )

# ============================================================================
# Summary
# ============================================================================

message(STATUS "")
message(STATUS "========================================")
message(STATUS "E.V3 C++ Kernel Configuration Summary")
message(STATUS "========================================")
message(STATUS "Version:        ${PROJECT_VERSION}")
message(STATUS "Build type:     ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard:   C++${CMAKE_CXX_STANDARD}")
message(STATUS "Compiler:       ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "")
message(STATUS "GPU Support:")
message(STATUS "  CUDA:         ${LLAMA_CUBLAS}")
message(STATUS "  Metal:        ${LLAMA_METAL}")
message(STATUS "")
message(STATUS "Python:         ${Python3_FOUND}")
if(Python3_FOUND)
    message(STATUS "  Version:      ${Python3_VERSION}")
endif()
message(STATUS "========================================")
message(STATUS "")
