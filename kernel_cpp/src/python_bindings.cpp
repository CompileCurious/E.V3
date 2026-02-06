/**
 * @file python_bindings.cpp
 * @brief Python C extension for E.V3 kernel integration
 * 
 * This provides a thin Python wrapper around the C++ kernel,
 * allowing the existing Python shell to communicate with the
 * new high-performance kernel.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "ev3/ev3.hpp"

#include <memory>
#include <string>

// ============================================================================
// Global Kernel Instance
// ============================================================================

static std::unique_ptr<ev3::Kernel> g_kernel;

// ============================================================================
// Python Module Functions
// ============================================================================

static PyObject* ev3_initialize(PyObject* self, PyObject* args) {
    const char* config_path = nullptr;
    
    if (!PyArg_ParseTuple(args, "|s", &config_path)) {
        return nullptr;
    }
    
    if (g_kernel) {
        PyErr_SetString(PyExc_RuntimeError, "Kernel already initialized");
        return nullptr;
    }
    
    g_kernel = std::make_unique<ev3::Kernel>();
    
    std::filesystem::path path = config_path ? config_path : "config/config.yaml";
    
    if (auto result = g_kernel->initialize(path); !result) {
        PyErr_SetString(PyExc_RuntimeError, result.error().message.c_str());
        g_kernel.reset();
        return nullptr;
    }
    
    Py_RETURN_TRUE;
}

static PyObject* ev3_start(PyObject* self, PyObject* args) {
    if (!g_kernel) {
        PyErr_SetString(PyExc_RuntimeError, "Kernel not initialized");
        return nullptr;
    }
    
    // Load and enable modules
    if (auto result = g_kernel->load_modules(); !result) {
        PyErr_SetString(PyExc_RuntimeError, result.error().message.c_str());
        return nullptr;
    }
    
    if (auto result = g_kernel->enable_modules(); !result) {
        PyErr_SetString(PyExc_RuntimeError, result.error().message.c_str());
        return nullptr;
    }
    
    // Start in background thread
    Py_BEGIN_ALLOW_THREADS
    g_kernel->start();
    Py_END_ALLOW_THREADS
    
    Py_RETURN_TRUE;
}

static PyObject* ev3_stop(PyObject* self, PyObject* args) {
    if (!g_kernel) {
        Py_RETURN_NONE;
    }
    
    g_kernel->stop();
    g_kernel.reset();
    
    Py_RETURN_TRUE;
}

static PyObject* ev3_is_running(PyObject* self, PyObject* args) {
    if (!g_kernel) {
        Py_RETURN_FALSE;
    }
    
    if (g_kernel->is_running()) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

static PyObject* ev3_generate(PyObject* self, PyObject* args, PyObject* kwargs) {
    const char* prompt = nullptr;
    int max_tokens = 128;
    float temperature = 0.7f;
    PyObject* callback = nullptr;
    
    static const char* kwlist[] = {"prompt", "max_tokens", "temperature", "callback", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|ifO", 
            const_cast<char**>(kwlist),
            &prompt, &max_tokens, &temperature, &callback)) {
        return nullptr;
    }
    
    if (!g_kernel) {
        PyErr_SetString(PyExc_RuntimeError, "Kernel not initialized");
        return nullptr;
    }
    
    if (!g_kernel->inference_engine().is_ready()) {
        PyErr_SetString(PyExc_RuntimeError, "LLM not available");
        return nullptr;
    }
    
    ev3::InferenceRequest request;
    request.prompt = prompt;
    request.max_tokens = max_tokens;
    request.temperature = temperature;
    
    // If callback provided, use streaming
    if (callback && PyCallable_Check(callback)) {
        Py_INCREF(callback);
        
        request.on_token = [callback](std::string_view token) -> bool {
            PyGILState_STATE gstate = PyGILState_Ensure();
            
            PyObject* result = PyObject_CallFunction(callback, "s#", 
                token.data(), static_cast<Py_ssize_t>(token.size()));
            
            bool continue_gen = true;
            if (result) {
                continue_gen = PyObject_IsTrue(result);
                Py_DECREF(result);
            } else {
                PyErr_Clear();
                continue_gen = false;
            }
            
            PyGILState_Release(gstate);
            return continue_gen;
        };
    }
    
    // Generate (blocking)
    std::string response;
    
    Py_BEGIN_ALLOW_THREADS
    auto result = g_kernel->inference_engine().generate_sync(request);
    if (result) {
        response = *result;
    }
    Py_END_ALLOW_THREADS
    
    if (callback) {
        Py_DECREF(callback);
    }
    
    return PyUnicode_FromStringAndSize(response.c_str(), response.size());
}

static PyObject* ev3_switch_mode(PyObject* self, PyObject* args) {
    const char* mode_str = nullptr;
    
    if (!PyArg_ParseTuple(args, "s", &mode_str)) {
        return nullptr;
    }
    
    if (!g_kernel) {
        PyErr_SetString(PyExc_RuntimeError, "Kernel not initialized");
        return nullptr;
    }
    
    ev3::LlmMode mode = (std::string(mode_str) == "deep") 
        ? ev3::LlmMode::Deep : ev3::LlmMode::Fast;
    
    if (auto result = g_kernel->inference_engine().switch_mode(mode); !result) {
        PyErr_SetString(PyExc_RuntimeError, result.error().message.c_str());
        return nullptr;
    }
    
    Py_RETURN_TRUE;
}

static PyObject* ev3_get_mode(PyObject* self, PyObject* args) {
    if (!g_kernel) {
        PyErr_SetString(PyExc_RuntimeError, "Kernel not initialized");
        return nullptr;
    }
    
    auto mode = g_kernel->inference_engine().current_mode();
    const char* mode_str = (mode == ev3::LlmMode::Deep) ? "deep" : "fast";
    
    return PyUnicode_FromString(mode_str);
}

static PyObject* ev3_send_ipc(PyObject* self, PyObject* args) {
    const char* msg_type = nullptr;
    PyObject* data_dict = nullptr;
    
    if (!PyArg_ParseTuple(args, "s|O", &msg_type, &data_dict)) {
        return nullptr;
    }
    
    if (!g_kernel || !g_kernel->ipc_server()) {
        PyErr_SetString(PyExc_RuntimeError, "IPC not available");
        return nullptr;
    }
    
    ev3::IpcMessage msg;
    msg.type = msg_type;
    
    if (data_dict && PyDict_Check(data_dict)) {
        PyObject* key;
        PyObject* value;
        Py_ssize_t pos = 0;
        
        while (PyDict_Next(data_dict, &pos, &key, &value)) {
            const char* key_str = PyUnicode_AsUTF8(key);
            const char* val_str = PyUnicode_AsUTF8(value);
            if (key_str && val_str) {
                msg.data[key_str] = val_str;
            }
        }
    }
    
    g_kernel->ipc_server()->queue_message(std::move(msg));
    
    Py_RETURN_TRUE;
}

// ============================================================================
// Module Definition
// ============================================================================

static PyMethodDef ev3_methods[] = {
    {"initialize", ev3_initialize, METH_VARARGS, 
     "Initialize the E.V3 kernel with optional config path"},
    {"start", ev3_start, METH_NOARGS, 
     "Start the kernel (load modules, enable, run)"},
    {"stop", ev3_stop, METH_NOARGS, 
     "Stop the kernel and cleanup"},
    {"is_running", ev3_is_running, METH_NOARGS, 
     "Check if kernel is running"},
    {"generate", reinterpret_cast<PyCFunction>(ev3_generate), METH_VARARGS | METH_KEYWORDS, 
     "Generate text from prompt using LLM"},
    {"switch_mode", ev3_switch_mode, METH_VARARGS, 
     "Switch LLM mode ('fast' or 'deep')"},
    {"get_mode", ev3_get_mode, METH_NOARGS, 
     "Get current LLM mode"},
    {"send_ipc", ev3_send_ipc, METH_VARARGS, 
     "Send IPC message to connected client"},
    {nullptr, nullptr, 0, nullptr}
};

static struct PyModuleDef ev3_module = {
    PyModuleDef_HEAD_INIT,
    "ev3_kernel_cpp",
    "E.V3 C++ Kernel Python bindings",
    -1,
    ev3_methods
};

PyMODINIT_FUNC PyInit_ev3_kernel_cpp(void) {
    return PyModule_Create(&ev3_module);
}
