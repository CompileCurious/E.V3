"""
System Status Module
Provides real-time system information (time, CPU, RAM, disk, network, antivirus)
to enhance LLM responses with actual system data
"""

from typing import Dict, Any, Set
from loguru import logger
import platform
import psutil
from datetime import datetime

from kernel.module import Module, Permission, KernelAPI


class SystemModule(Module):
    """
    System status module
    Collects and provides system information for LLM context enrichment
    """
    
    def __init__(self, kernel_api: KernelAPI):
        super().__init__("system", kernel_api)
        self.enabled = False
    
    def get_required_permissions(self) -> Set[Permission]:
        """System module needs event subscription and emission"""
        return {
            Permission.EVENT_EMIT,
            Permission.EVENT_SUBSCRIBE
        }
    
    def get_dependencies(self) -> Set[str]:
        """No dependencies"""
        return set()
    
    def load(self, config: Dict[str, Any]) -> bool:
        """Initialize system monitoring"""
        try:
            self.config = config
            
            # Don't subscribe to events - we'll intercept directly in IPC module
            # The IPC module should call us before broadcasting user messages
            
            logger.info("System module loaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load system module: {e}")
            return False
    
    def enable(self) -> bool:
        """Enable system monitoring"""
        try:
            self.enabled = True
            logger.info("System module enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to enable system module: {e}")
            return False
    
    def disable(self) -> bool:
        """Disable system monitoring"""
        try:
            self.enabled = False
            logger.info("System module disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable system module: {e}")
            return False
    
    def unload(self) -> bool:
        """Cleanup"""
        try:
            self.enabled = False
            logger.info("System module unloaded")
            return True
        except Exception as e:
            logger.error(f"Failed to unload system module: {e}")
            return False
    
    def handle_event(self, event_name: str, event_data: Dict[str, Any]):
        """Handle events (not used - we inject via direct call from LLM module)"""
        pass
    
    def inject_context_if_needed(self, message: str) -> str:
        """Inject system context into message if it contains system-related keywords"""
        if not self.enabled:
            return message
        
        # Check if query is about system status
        query_lower = message.lower()
        needs_context = any(keyword in query_lower for keyword in [
            'time', 'date', 'cpu', 'memory', 'ram', 'disk', 'storage',
            'network', 'performance', 'system', 'battery', 'process'
        ])
        
        if not needs_context:
            return message
        
        # Gather system info
        system_info = self.get_system_status()
        context = self._format_system_context(system_info)
        
        logger.info(f"Injecting system context for query: {message[:30]}...")
        return f"{context}\n\nUser query: {message}"
    
    def shutdown(self):
        """Shutdown system module"""
        self.disable()
        self.unload()
    
    def _inject_system_context(self, event_data: Dict[str, Any]):
        """Inject system information into user queries before LLM processing"""
        if not self.enabled:
            return
        
        # Get original message
        original_message = event_data.get("message", "")
        
        # Check if query is about system status
        query_lower = original_message.lower()
        needs_context = any(keyword in query_lower for keyword in [
            'time', 'date', 'cpu', 'memory', 'ram', 'disk', 'storage',
            'network', 'performance', 'system', 'battery', 'process',
            'antivirus', 'defender', 'security'
        ])
        
        if not needs_context:
            return
        
        # Gather system info
        system_info = self.get_system_status()
        
        # Inject context into message
        context = self._format_system_context(system_info)
        enhanced_message = f"{context}\n\nUser query: {original_message}"
        
        # Update event data with enhanced message
        event_data["message"] = enhanced_message
        event_data["_system_context_injected"] = True
        
        logger.info(f"Injected system context for query: {original_message[:30]}...")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Collect current system status"""
        try:
            # Time and date
            now = datetime.now()
            
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory info
            memory = psutil.virtual_memory()
            
            # Disk info
            disk = psutil.disk_usage('/')
            
            # Network info
            net_io = psutil.net_io_counters()
            
            # Battery (if available)
            battery = psutil.sensors_battery() if hasattr(psutil, 'sensors_battery') else None
            
            status = {
                "datetime": {
                    "current_time": now.strftime("%I:%M %p"),
                    "current_date": now.strftime("%A, %B %d, %Y"),
                    "iso": now.isoformat()
                },
                "cpu": {
                    "usage_percent": round(cpu_percent, 1),
                    "core_count": cpu_count,
                    "frequency_mhz": round(cpu_freq.current if cpu_freq else 0, 0)
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 1),
                    "used_gb": round(memory.used / (1024**3), 1),
                    "available_gb": round(memory.available / (1024**3), 1),
                    "percent_used": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 1),
                    "used_gb": round(disk.used / (1024**3), 1),
                    "free_gb": round(disk.free / (1024**3), 1),
                    "percent_used": disk.percent
                },
                "network": {
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 1),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 1)
                },
                "os": {
                    "system": platform.system(),
                    "version": platform.version(),
                    "machine": platform.machine()
                }
            }
            
            if battery:
                status["battery"] = {
                    "percent": battery.percent,
                    "plugged_in": battery.power_plugged,
                    "time_left_minutes": battery.secsleft // 60 if battery.secsleft > 0 else None
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Error collecting system status: {e}")
            return {}
    
    def _format_system_context(self, status: Dict[str, Any]) -> str:
        """Format system status for LLM context"""
        try:
            dt = status.get("datetime", {})
            cpu = status.get("cpu", {})
            mem = status.get("memory", {})
            disk = status.get("disk", {})
            
            context = f"""[SYSTEM CONTEXT]
Current time: {dt.get('current_time', 'N/A')}
Current date: {dt.get('current_date', 'N/A')}
CPU: {cpu.get('usage_percent', 0)}% ({cpu.get('core_count', 0)} cores)
Memory: {mem.get('used_gb', 0)}/{mem.get('total_gb', 0)} GB ({mem.get('percent_used', 0)}%)
Disk: {disk.get('free_gb', 0)} GB free of {disk.get('total_gb', 0)} GB
"""
            
            if "battery" in status:
                bat = status["battery"]
                context += f"Battery: {bat.get('percent', 0)}% {'(Charging)' if bat.get('plugged_in') else ''}\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Error formatting system context: {e}")
            return "[SYSTEM CONTEXT] Error retrieving system information"
