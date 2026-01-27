"""IPC package - Native Windows communication"""
from .native_pipe import IPCServer, IPCClient

__all__ = ['IPCServer', 'IPCClient']
