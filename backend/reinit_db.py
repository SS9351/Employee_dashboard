import os
import subprocess

db_file = "attendance_system.db"
if os.path.exists(db_file):
    os.remove(db_file)
    print("Deleted old DB.")

print("Running init_db.py...")
subprocess.run(["venv\\Scripts\\python.exe", "init_db.py"])
