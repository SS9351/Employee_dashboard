import os
import requests

class APIClient:
    def __init__(self, base_url="https://employee-dashboard-iler.onrender.com"): # Hosted on Render
        self.base_url = base_url
        self.token = None

    def set_token(self, token):
        self.token = token

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def test_connection(self):
        try:
            domain = self.base_url.replace('/api', '')
            r = requests.get(f"{domain}/health", timeout=5)
            return r.status_code == 200
        except:
            return False

    def login(self, username, password, device_info):
        payload = {
            "username": username,
            "password": password,
            "device_info": device_info
        }
        try:
            # We use /api/auth/login as an endpoint format
            response = requests.post(f"{self.base_url}/api/auth/login", json=payload, headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def get_leaves(self):
        try:
            response = requests.get(f"{self.base_url}/api/leaves", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def apply_leave(self, leave_type, reason, start_date, end_date):
        payload = {
            "leave_type": leave_type,
            "reason": reason,
            "start_date": start_date,
            "end_date": end_date
        }
        try:
            response = requests.post(f"{self.base_url}/api/leaves/apply", json=payload, headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def sync_activity_logs(self, logs):
        if not logs:
            return {}, 200
        try:
            response = requests.post(f"{self.base_url}/api/tracker/sync", json={"logs": logs}, headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def logout(self):
        try:
            # Tell backend to close session
            requests.post(f"{self.base_url}/api/auth/logout", headers=self._headers())
        except:
            pass
        self.token = None

    # --- Admin Endpoints ---
    def get_admin_leaves(self):
        try:
            response = requests.get(f"{self.base_url}/api/admin/leaves", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def update_leave_status(self, leave_id, status):
        try:
            response = requests.post(f"{self.base_url}/api/admin/leaves/{leave_id}/status", json={"status": status}, headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def get_admin_attendance(self):
        try:
            response = requests.get(f"{self.base_url}/api/admin/attendance", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def get_admin_logs(self):
        try:
            response = requests.get(f"{self.base_url}/api/admin/logs", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def get_all_users(self):
        try:
            response = requests.get(f"{self.base_url}/api/admin/users", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
            
    def get_reset_requests(self):
        try:
            response = requests.get(f"{self.base_url}/api/admin/reset-requests", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def approve_reset_request(self, request_id):
        try:
            response = requests.post(f"{self.base_url}/api/admin/reset-requests/{request_id}/approve", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
            
    # --- Auth Additions ---
    
    def request_password_reset(self, username):
        try:
            response = requests.post(f"{self.base_url}/api/auth/forgot-password", json={"username": username}, headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
            
    def reset_password(self, username, new_password):
        try:
            response = requests.post(f"{self.base_url}/api/auth/reset-password", json={"username": username, "new_password": new_password}, headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
            
    # --- Attendance Stats ---

    def get_attendance_stats(self, month=None, year=None):
        try:
            params = {}
            if month: params["month"] = month
            if year: params["year"] = year
            response = requests.get(f"{self.base_url}/api/attendance/stats", params=params, headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def get_admin_actual_attendance(self):
        try:
            response = requests.get(f"{self.base_url}/api/admin/actual-attendance", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
            
    def delete_attendance(self, attendance_id):
        try:
            response = requests.delete(f"{self.base_url}/api/admin/attendance/{attendance_id}", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
            
    def add_manual_attendance(self, user_id, date_str, status):
        try:
            payload = {"user_id": user_id, "date": date_str, "status": status}
            response = requests.post(f"{self.base_url}/api/admin/attendance/manual", json=payload, headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
            
    def get_admin_user_stats(self, user_id, month=None, year=None):
        try:
            params = {}
            if month: params["month"] = month
            if year: params["year"] = year
            response = requests.get(f"{self.base_url}/api/admin/attendance/user-stats/{user_id}", params=params, headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def toggle_admin(self, user_id):
        try:
            response = requests.post(f"{self.base_url}/api/admin/users/{user_id}/toggle-admin", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def terminate_session(self, attendance_id):
        try:
            response = requests.post(f"{self.base_url}/api/admin/attendance/{attendance_id}/terminate", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500

    def export_excel(self):
        try:
            response = requests.get(f"{self.base_url}/api/admin/export-excel", headers=self._headers(), stream=True)
            return response.content, response.status_code
        except Exception as e:
            return None, 500

    def delete_logs(self):
        try:
            response = requests.delete(f"{self.base_url}/api/admin/logs", headers=self._headers())
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
