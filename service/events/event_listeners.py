"""
Windows Event Listeners
Monitors Windows Defender, Firewall, and System events
Privacy: Events are anonymized before processing
"""

import win32evtlog
import win32evtlogutil
import win32con
import wmi
import threading
from typing import Callable, Optional, List, Dict, Any
from loguru import logger
import time


class WindowsEventListener:
    """
    Base class for Windows event listeners
    Privacy: No raw event data is sent externally
    """
    
    def __init__(self, log_name: str, event_ids: Optional[List[int]] = None):
        self.log_name = log_name
        self.event_ids = event_ids or []
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
    
    def register_callback(self, callback: Callable):
        """Register callback for events"""
        self._callbacks.append(callback)
        logger.debug(f"Registered callback for {self.log_name}")
    
    def start(self):
        """Start listening for events"""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        logger.info(f"Started listening to {self.log_name}")
    
    def stop(self):
        """Stop listening"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info(f"Stopped listening to {self.log_name}")
    
    def _listen(self):
        """Main listening loop"""
        try:
            # Open event log
            hand = win32evtlog.OpenEventLog(None, self.log_name)
            flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            # Get current position
            total = win32evtlog.GetNumberOfEventLogRecords(hand)
            
            while self.running:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                
                if events:
                    for event in events:
                        # Filter by event ID if specified
                        if not self.event_ids or event.EventID in self.event_ids:
                            self._process_event(event)
                else:
                    time.sleep(1)  # Wait before checking again
                    
        except Exception as e:
            logger.error(f"Error in {self.log_name} listener: {e}")
        finally:
            try:
                win32evtlog.CloseEventLog(hand)
            except:
                pass
    
    def _process_event(self, event):
        """Process and anonymize event"""
        try:
            # Anonymize event data
            event_data = self._anonymize_event(event)
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(event_data)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    def _anonymize_event(self, event) -> Dict[str, Any]:
        """
        Anonymize event data - remove personal information
        Privacy: Only keep essential non-identifying information
        """
        return {
            "event_id": event.EventID,
            "event_type": event.EventType,
            "time_generated": event.TimeGenerated.isoformat() if event.TimeGenerated else None,
            "source": event.SourceName,
            # Do NOT include: Computer name, user names, file paths, IPs
            "category": event.EventCategory,
        }


class DefenderEventListener(WindowsEventListener):
    """
    Windows Defender event listener
    Monitors security events without compromising privacy
    """
    
    def __init__(self, event_ids: Optional[List[int]] = None):
        # Default Defender event IDs
        default_ids = [
            1116,  # Malware detected
            1117,  # Malware action taken
            5001,  # Real-time protection disabled
            5010,  # Scanning disabled
            5012,  # Tampering detected
        ]
        super().__init__(
            "Microsoft-Windows-Windows Defender/Operational",
            event_ids or default_ids
        )
    
    def _anonymize_event(self, event) -> Dict[str, Any]:
        """Anonymize Defender event"""
        base_data = super()._anonymize_event(event)
        
        # Add defender-specific anonymized data
        base_data.update({
            "threat_detected": event.EventID in [1116, 1117],
            "protection_disabled": event.EventID in [5001, 5010],
            "tampering": event.EventID == 5012,
        })
        
        return base_data


class FirewallEventListener(WindowsEventListener):
    """
    Windows Firewall event listener
    Privacy: Only monitors rule changes, not connections
    """
    
    def __init__(self):
        super().__init__(
            "Microsoft-Windows-Windows Firewall With Advanced Security/Firewall",
            [2004, 2005, 2006, 2033]  # Rule changes
        )
    
    def _anonymize_event(self, event) -> Dict[str, Any]:
        """Anonymize Firewall event"""
        base_data = super()._anonymize_event(event)
        
        base_data.update({
            "rule_added": event.EventID == 2004,
            "rule_modified": event.EventID == 2005,
            "rule_deleted": event.EventID == 2006,
        })
        
        return base_data


class SystemEventListener:
    """
    System notification listener using WMI
    Privacy: Monitors system state, not user activity
    """
    
    def __init__(self):
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        self.wmi = None
    
    def register_callback(self, callback: Callable):
        """Register callback for system events"""
        self._callbacks.append(callback)
    
    def start(self):
        """Start monitoring system events"""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        logger.info("Started system event monitoring")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Stopped system event monitoring")
    
    def _monitor(self):
        """Monitor system events"""
        try:
            self.wmi = wmi.WMI()
            
            while self.running:
                # Monitor system state changes
                # This is a simplified version - real implementation would use WMI event queries
                time.sleep(5)
                
                # Check for important system state changes
                self._check_system_state()
                
        except Exception as e:
            logger.error(f"System monitoring error: {e}")
    
    def _check_system_state(self):
        """Check system state for important changes"""
        try:
            # This is a placeholder - implement actual system checks
            # Examples: Battery low, disk space low, updates available
            pass
        except Exception as e:
            logger.error(f"Error checking system state: {e}")


class EventManager:
    """
    Manages all event listeners
    Privacy: Coordinates event monitoring without data leakage
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.listeners = {}
        
        # Initialize listeners based on config
        if config.get("events", {}).get("windows_defender", {}).get("enabled", True):
            event_ids = config.get("events", {}).get("windows_defender", {}).get("event_ids")
            self.listeners["defender"] = DefenderEventListener(event_ids)
        
        if config.get("events", {}).get("firewall", {}).get("enabled", True):
            self.listeners["firewall"] = FirewallEventListener()
        
        if config.get("events", {}).get("system_notifications", {}).get("enabled", True):
            self.listeners["system"] = SystemEventListener()
        
        logger.info(f"Event manager initialized with {len(self.listeners)} listeners")
    
    def register_callback(self, listener_name: str, callback: Callable):
        """Register callback for specific listener"""
        if listener_name in self.listeners:
            self.listeners[listener_name].register_callback(callback)
    
    def start_all(self):
        """Start all listeners"""
        for name, listener in self.listeners.items():
            try:
                listener.start()
            except Exception as e:
                logger.error(f"Failed to start {name} listener: {e}")
    
    def stop_all(self):
        """Stop all listeners"""
        for listener in self.listeners.values():
            listener.stop()
