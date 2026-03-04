import os
import platform
import socket
import psutil
import getmac
import uuid
import datetime
import threading
import time
from collections import Counter
try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


def get_device_info():
    """Gathers required device fingerprinting info."""
    return {
        "hostname": socket.gethostname(),
        "os_info": f"{platform.system()} {platform.release()}",
        "mac_address": getmac.get_mac_address(),
        "local_ip": socket.gethostbyname(socket.gethostname()),
        "hardware_id": str(uuid.getnode())
    }

class ActivityTracker:
    def __init__(self, callback=None):
        self.running = False
        self.thread = None
        self.activity_log = []
        self.callback = callback
    
    def get_active_window_title(self):
        if WIN32_AVAILABLE:
            try:
                window = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(window)
                return title
            except:
                pass
        return "Unknown"

    def _monitor_loop(self):
        # We sample active window every 5 seconds
        while self.running:
            title = self.get_active_window_title()
            if title and title.strip():
                # Extract app name normally at the end of window title separated by '-'
                parts = title.rsplit('-', 1)
                app_name = parts[-1].strip() if len(parts) > 1 else title.strip()
                
                timestamp = datetime.datetime.now().isoformat()
                log_entry = {"time": timestamp, "app": app_name, "raw_title": title}
                self.activity_log.append(log_entry)
                
                if self.callback:
                    self.callback(log_entry)
            
            time.sleep(5)
            
            # Keep log from growing infinitely if not flushed (flush every 100 items)
            if len(self.activity_log) > 100:
                self.flush_logs()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def flush_logs(self):
        """Returns the current logs and clears them."""
        logs = list(self.activity_log)
        self.activity_log.clear()
        return logs
