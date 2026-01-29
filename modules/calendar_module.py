"""
Calendar Module
Monitors calendar for reminders
"""

from typing import Dict, Any, Set, Optional
from loguru import logger
import threading
import time
from datetime import timedelta, datetime

from kernel.module import Module, Permission, KernelAPI
from service.calendar.calendar_manager import OutlookCalendarProvider, GoogleCalendarProvider, CalendarEvent


class CalendarModule(Module):
    """
    Calendar capability module
    Monitors calendar and emits reminder events
    """
    
    def __init__(self, kernel_api: KernelAPI):
        super().__init__("calendar", kernel_api)
        self.provider = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._check_interval = 300  # 5 minutes default
        self._reminder_advance = 900  # 15 minutes default
    
    def get_required_permissions(self) -> Set[Permission]:
        """Calendar module needs calendar access and event emission"""
        return {
            Permission.CALENDAR_READ,
            Permission.EVENT_EMIT,
            Permission.STORAGE_READ,
        }
    
    def get_dependencies(self) -> Set[str]:
        """Depends on state module for reminders"""
        return {"state"}
    
    def load(self, config: Dict[str, Any]) -> bool:
        """Initialize calendar provider"""
        try:
            self.config = config
            calendar_config = config.get("calendar", {})
            
            if not calendar_config.get("enabled", True):
                logger.info("Calendar module disabled in config")
                return True
            
            # Get configuration
            self._check_interval = calendar_config.get("check_interval", 300)
            self._reminder_advance = calendar_config.get("reminder_advance", 900)
            
            # Initialize provider
            provider_type = calendar_config.get("provider", "outlook")
            
            if provider_type == "outlook":
                self.provider = OutlookCalendarProvider(calendar_config)
            elif provider_type == "google":
                self.provider = GoogleCalendarProvider(calendar_config)
            else:
                logger.warning(f"Unknown calendar provider: {provider_type}")
                return True
            
            # Authenticate
            if not self.provider.authenticate():
                logger.warning("Calendar authentication failed - module will be inactive")
                self.provider = None
                return True
            
            logger.info(f"Calendar module loaded with {provider_type} provider")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load calendar module: {e}")
            return False
    
    def enable(self) -> bool:
        """Start calendar monitoring"""
        try:
            if not self.provider:
                logger.info("Calendar module enabled but no provider available")
                return True
            
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            
            logger.info("Calendar module enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable calendar module: {e}")
            return False
    
    def disable(self) -> bool:
        """Stop calendar monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Calendar module disabled")
        return True
    
    def shutdown(self) -> bool:
        """Cleanup calendar resources"""
        self.disable()
        self.provider = None
        logger.info("Calendar module shutdown")
        return True
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Not subscribed to any events currently"""
        pass
    
    def _monitor_loop(self):
        """Background thread monitoring calendar"""
        logger.debug("Calendar monitoring loop started")
        
        while self._running:
            try:
                self._check_reminders()
            except Exception as e:
                logger.error(f"Error in calendar monitoring: {e}")
            
            # Sleep in small increments to allow quick shutdown
            for _ in range(self._check_interval):
                if not self._running:
                    break
                time.sleep(1)
        
        logger.debug("Calendar monitoring loop stopped")
    
    def _check_reminders(self):
        """Check for upcoming events that need reminders"""
        if not self.provider:
            return
        
        # Get upcoming events (next 24 hours)
        events = self.provider.get_upcoming_events(hours=24)
        
        for event in events:
            if event.should_remind(self._reminder_advance):
                self._emit_reminder(event)
                event.reminded = True
    
    def _emit_reminder(self, event: CalendarEvent):
        """Emit reminder event"""
        minutes_until = int(event.time_until_start() / 60)
        message = f"Reminder: {event.title} in {minutes_until} minutes"
        
        logger.info(f"Emitting reminder: {event.title}")
        
        # Request state transition to reminder
        self.kernel.emit_event(self.name, "state.transition.reminder", {
            "message": message,
            "priority": 1,
            "metadata": {
                "event_title": event.title,
                "event_start": event.start_time.isoformat(),
                "event_location": event.location
            }
        })
