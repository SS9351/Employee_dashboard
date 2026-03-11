import time
import requests

url = "https://employee-dashboard-iler.onrender.com/api/admin/wipe-database-danger"
print(f"Waiting for {url} to go live on Render and wipe the DB...")

for i in range(30):
    try:
        response = requests.get(url)
        print(f"Attempt {i+1}: HTTP {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS WIPED:", response.json())
            break
    except Exception as e:
        pass
    time.sleep(15)
