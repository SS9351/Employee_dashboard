import sys
import threading
import time
from PyQt6.QtWidgets import QApplication, QStackedWidget, QMessageBox

from ui.login_window import LoginWindow
from ui.main_window import DashboardWindow
from ui.styles import MAIN_STYLE
from utils.api_client import APIClient
from utils.tracker import get_device_info, ActivityTracker

class Application(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.setStyleSheet(MAIN_STYLE)
        
        self.api_client = APIClient(base_url="http://127.0.0.1:8000") # Assume EC2 endpoint or local test
        self.device_info = get_device_info()
        self.tracker = ActivityTracker()
        
        # Thread for syncing logs
        self.log_sync_running = False
        
        self.stack = QStackedWidget()
        
        self.login_win = LoginWindow()
        self.login_win.login_attempted.connect(self.handle_login)
        self.stack.addWidget(self.login_win)
        
        self.stack.setWindowTitle("Sahastra Finnovations - Attendance")
        self.stack.resize(800, 600)
        self.stack.show()

    def handle_login(self, username, password):
        # We ping the backend
        data, status = self.api_client.login(username, password, self.device_info)
        
        # We must require a successful login from the backend to get a real token.
        if status == 200: 
            token = data.get("access_token")
            user_info = data.get("user", {"name": username})
            
            # The backend now returns is_admin directly
            is_adm = user_info.get("is_admin", False)
            user_info["is_admin"] = is_adm
            
            self.api_client.set_token(token)
            
            self.dashboard_win = DashboardWindow(self.api_client, self.device_info, user_info)
            self.dashboard_win.logout_btn.clicked.connect(self.handle_logout)
            self.stack.addWidget(self.dashboard_win)
            self.stack.setCurrentWidget(self.dashboard_win)
            
            # Start Activity Tracker
            self.tracker.start()
            self.log_sync_running = True
            threading.Thread(target=self.sync_logs_loop, daemon=True).start()
        else:
            self.login_win.show_error("Invalid credentials or server down.")

    def handle_logout(self):
        # Stop tracking
        self.tracker.stop()
        self.log_sync_running = False
        
        # Logout from API
        self.api_client.logout()
        
        # Flush final logs if possible
        logs = self.tracker.flush_logs()
        if logs:
            self.api_client.sync_activity_logs(logs)

        # Switch back to login
        self.stack.setCurrentWidget(self.login_win)
        self.login_win.reset_state()
        
        # Remove dashboard memory
        if hasattr(self, 'dashboard_win'):
            self.stack.removeWidget(self.dashboard_win)

    def sync_logs_loop(self):
        while self.log_sync_running:
            time.sleep(10) # Sync every 10 seconds for demo
            logs = self.tracker.flush_logs()
            if logs:
                self.api_client.sync_activity_logs(logs)

if __name__ == "__main__":
    app = Application(sys.argv)
    sys.exit(app.exec())
