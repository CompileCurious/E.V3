"""
Windows Service Installer for E.V3
Installs E.V3 as a native Windows background service
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from service.core import EV3Service


class EV3WindowsService(win32serviceutil.ServiceFramework):
    """
    Windows Service wrapper for E.V3
    """
    
    _svc_name_ = "EV3CompanionService"
    _svc_display_name_ = "E.V3 Privacy Companion Service"
    _svc_description_ = "Privacy-focused desktop companion that monitors system events and provides intelligent assistance"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.service: EV3Service = None
    
    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        
        if self.service:
            self.service.stop()
    
    def SvcDoRun(self):
        """Run the service"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            # Initialize and start service
            self.service = EV3Service()
            self.service.initialize()
            
            # Run service
            self.service.running = True
            
            # Start components
            if self.service.ipc_server:
                self.service.ipc_server.start()
            
            if self.service.event_manager:
                self.service.event_manager.start_all()
            
            if self.service.calendar_manager:
                self.service.calendar_manager.start()
            
            # Wait for stop signal
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {e}")
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )


def install_service():
    """Install the service"""
    print("Installing E.V3 Companion Service...")
    
    try:
        # Install service
        win32serviceutil.InstallService(
            EV3WindowsService._svc_reg_class_,
            EV3WindowsService._svc_name_,
            EV3WindowsService._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START,
            description=EV3WindowsService._svc_description_
        )
        
        print("✓ Service installed successfully")
        print(f"  Name: {EV3WindowsService._svc_name_}")
        print(f"  Display Name: {EV3WindowsService._svc_display_name_}")
        print("\nTo start the service, run:")
        print(f"  net start {EV3WindowsService._svc_name_}")
        print("\nOr use:")
        print("  python install_service.py start")
        
    except Exception as e:
        print(f"✗ Failed to install service: {e}")
        return False
    
    return True


def uninstall_service():
    """Uninstall the service"""
    print("Uninstalling E.V3 Companion Service...")
    
    try:
        win32serviceutil.RemoveService(EV3WindowsService._svc_name_)
        print("✓ Service uninstalled successfully")
    except Exception as e:
        print(f"✗ Failed to uninstall service: {e}")
        return False
    
    return True


def start_service():
    """Start the service"""
    print("Starting E.V3 Companion Service...")
    
    try:
        win32serviceutil.StartService(EV3WindowsService._svc_name_)
        print("✓ Service started successfully")
    except Exception as e:
        print(f"✗ Failed to start service: {e}")
        return False
    
    return True


def stop_service():
    """Stop the service"""
    print("Stopping E.V3 Companion Service...")
    
    try:
        win32serviceutil.StopService(EV3WindowsService._svc_name_)
        print("✓ Service stopped successfully")
    except Exception as e:
        print(f"✗ Failed to stop service: {e}")
        return False
    
    return True


def restart_service():
    """Restart the service"""
    print("Restarting E.V3 Companion Service...")
    
    try:
        win32serviceutil.RestartService(EV3WindowsService._svc_name_)
        print("✓ Service restarted successfully")
    except Exception as e:
        print(f"✗ Failed to restart service: {e}")
        return False
    
    return True


def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        # Run as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(EV3WindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Handle command line
        command = sys.argv[1].lower()
        
        if command == 'install':
            install_service()
        elif command == 'uninstall':
            uninstall_service()
        elif command == 'start':
            start_service()
        elif command == 'stop':
            stop_service()
        elif command == 'restart':
            restart_service()
        else:
            print("E.V3 Windows Service Manager")
            print("\nUsage:")
            print("  python install_service.py install   - Install the service")
            print("  python install_service.py uninstall - Uninstall the service")
            print("  python install_service.py start     - Start the service")
            print("  python install_service.py stop      - Stop the service")
            print("  python install_service.py restart   - Restart the service")


if __name__ == '__main__':
    main()
