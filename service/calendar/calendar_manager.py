"""
Calendar Integration for E.V3
Supports Microsoft Outlook and Google Calendar
Privacy: Only reads calendar data, never writes or shares
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import os
from abc import ABC, abstractmethod
import threading
import time


class CalendarEvent:
    """Represents a calendar event"""
    
    def __init__(self, title: str, start_time: datetime, end_time: datetime, 
                 description: str = "", location: str = ""):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.location = location
        self.reminded = False
    
    def time_until_start(self) -> float:
        """Get seconds until event starts"""
        return (self.start_time - datetime.now()).total_seconds()
    
    def should_remind(self, advance_seconds: int) -> bool:
        """Check if reminder should be shown"""
        if self.reminded:
            return False
        
        time_until = self.time_until_start()
        return 0 < time_until <= advance_seconds
    
    def __repr__(self):
        return f"CalendarEvent('{self.title}' at {self.start_time})"


class CalendarProvider(ABC):
    """Base class for calendar providers"""
    
    @abstractmethod
    def get_upcoming_events(self, hours: int = 24) -> List[CalendarEvent]:
        """Get upcoming events"""
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with calendar service"""
        pass


class OutlookCalendarProvider(CalendarProvider):
    """
    Microsoft Outlook / Office 365 Calendar
    Privacy: Read-only access, credentials stored locally
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.account = None
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Microsoft 365"""
        try:
            from O365 import Account
            
            client_id = os.getenv("OUTLOOK_CLIENT_ID")
            client_secret = os.getenv("OUTLOOK_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                logger.warning("Outlook credentials not configured")
                return False
            
            credentials = (client_id, client_secret)
            
            # Create account
            self.account = Account(credentials)
            
            # Check if already authenticated
            if self.account.is_authenticated:
                self.authenticated = True
                logger.info("Outlook calendar authenticated (existing session)")
                return True
            
            # Authenticate
            if self.account.authenticate(scopes=['basic', 'calendar_all']):
                self.authenticated = True
                logger.info("Outlook calendar authenticated successfully")
                return True
            else:
                logger.error("Failed to authenticate with Outlook")
                return False
                
        except ImportError:
            logger.error("O365 package not installed. Install with: pip install O365")
            return False
        except Exception as e:
            logger.error(f"Outlook authentication error: {e}")
            return False
    
    def get_upcoming_events(self, hours: int = 24) -> List[CalendarEvent]:
        """Get upcoming events from Outlook calendar"""
        if not self.authenticated:
            return []
        
        try:
            schedule = self.account.schedule()
            calendar = schedule.get_default_calendar()
            
            # Get events
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=hours)
            
            query = calendar.new_query('start').greater_equal(start_time)
            query.chain('and').on_attribute('end').less_equal(end_time)
            
            events = []
            for event in calendar.get_events(query=query, include_recurring=True):
                cal_event = CalendarEvent(
                    title=event.subject,
                    start_time=event.start,
                    end_time=event.end,
                    description=event.body,
                    location=event.location.get('displayName', '') if event.location else ''
                )
                events.append(cal_event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error fetching Outlook events: {e}")
            return []


class GoogleCalendarProvider(CalendarProvider):
    """
    Google Calendar
    Privacy: Read-only access, credentials stored locally
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service = None
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
            
            creds = None
            token_path = 'config/credentials/google_token.json'
            creds_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS', 'config/credentials/google_credentials.json')
            
            # Load existing token
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            # Refresh or get new token
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(creds_path):
                        logger.warning("Google Calendar credentials not found")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save token
                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
            self.authenticated = True
            logger.info("Google Calendar authenticated successfully")
            return True
            
        except ImportError:
            logger.error("Google Calendar packages not installed")
            return False
        except Exception as e:
            logger.error(f"Google Calendar authentication error: {e}")
            return False
    
    def get_upcoming_events(self, hours: int = 24) -> List[CalendarEvent]:
        """Get upcoming events from Google Calendar"""
        if not self.authenticated:
            return []
        
        try:
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(hours=hours)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse datetime
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
                cal_event = CalendarEvent(
                    title=event.get('summary', 'Untitled Event'),
                    start_time=start_dt,
                    end_time=end_dt,
                    description=event.get('description', ''),
                    location=event.get('location', '')
                )
                events.append(cal_event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error fetching Google Calendar events: {e}")
            return []


class CalendarManager:
    """
    Manages calendar integration and reminders
    Privacy: All data stays local, read-only access
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider: Optional[CalendarProvider] = None
        self.events: List[CalendarEvent] = []
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._reminder_callbacks = []
        
        # Initialize provider
        provider_type = config.get("calendar", {}).get("provider", "outlook").lower()
        
        if provider_type == "outlook":
            self.provider = OutlookCalendarProvider(config)
        elif provider_type == "google":
            self.provider = GoogleCalendarProvider(config)
        else:
            logger.warning(f"Unknown calendar provider: {provider_type}")
        
        # Authenticate
        if self.provider:
            self.provider.authenticate()
        
        logger.info("Calendar manager initialized")
    
    def register_reminder_callback(self, callback):
        """Register callback for reminders"""
        self._reminder_callbacks.append(callback)
    
    def start(self):
        """Start calendar monitoring"""
        if not self.provider or not self.provider.authenticated:
            logger.warning("Calendar provider not authenticated")
            return
        
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._monitor_calendar, daemon=True)
        self._thread.start()
        logger.info("Calendar monitoring started")
    
    def stop(self):
        """Stop calendar monitoring"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Calendar monitoring stopped")
    
    def _monitor_calendar(self):
        """Monitor calendar for upcoming events"""
        check_interval = self.config.get("calendar", {}).get("check_interval", 300)  # 5 minutes
        reminder_advance = self.config.get("calendar", {}).get("reminder_advance", 900)  # 15 minutes
        
        while self.running:
            try:
                # Fetch upcoming events
                self.events = self.provider.get_upcoming_events(hours=24)
                
                # Check for reminders
                for event in self.events:
                    if event.should_remind(reminder_advance):
                        self._send_reminder(event)
                        event.reminded = True
                
                # Wait before next check
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Calendar monitoring error: {e}")
                time.sleep(check_interval)
    
    def _send_reminder(self, event: CalendarEvent):
        """Send reminder for event"""
        logger.info(f"Reminder: {event.title} in {event.time_until_start() / 60:.0f} minutes")
        
        # Notify callbacks
        for callback in self._reminder_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in reminder callback: {e}")
    
    def get_next_event(self) -> Optional[CalendarEvent]:
        """Get the next upcoming event"""
        if not self.events:
            return None
        
        now = datetime.now()
        upcoming = [e for e in self.events if e.start_time > now]
        
        if upcoming:
            return min(upcoming, key=lambda e: e.start_time)
        
        return None
