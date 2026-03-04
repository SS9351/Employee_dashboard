import sys
import os

sys.path.append(os.path.abspath('.'))

from utils.api_client import APIClient
from utils.tracker import get_device_info

def run_tests():
    c = APIClient()
    print("Base URL:", c.base_url)
    
    health = c.test_connection()
    print("Health Test:", health)
    
    device = get_device_info()
    print("Device Info:", device)
    
    resp, status = c.login('admin', 'admin123', device)
    print(f"Login response [{status}]: {resp}")

if __name__ == '__main__':
    run_tests()
