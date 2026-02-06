"""LLM package"""
# DEPRECATED: This module uses the old Python-based LLM system.
# For best performance, use the C++ kernel instead (see kernel_cpp/docs/BUILD.md)
#
# The C++ kernel provides:
# - 2-3x faster inference
# - Direct llama.cpp integration (no Python overhead)
# - Persistent model loading
# - Native async/streaming
from .llm_manager import LLMManager, LocalLLM, ExternalLLM

__all__ = ['LLMManager', 'LocalLLM', 'ExternalLLM']
