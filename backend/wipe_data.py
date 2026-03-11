import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Attendance, LeaveRequest, ApplicationLog, PasswordResetRequest

# Load environment variables
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable is not set.")
    exit(1)

# Handle SQLAlchemy 1.4+ postgresql:// vs postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to database...")

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    print("Wiping Attendance logs...")
    session.query(Attendance).delete()

    print("Wiping Leave Requests...")
    session.query(LeaveRequest).delete()

    print("Wiping Application Logs...")
    session.query(ApplicationLog).delete()

    print("Wiping Password Reset Requests...")
    session.query(PasswordResetRequest).delete()

    session.commit()
    print("Successfully wiped all operational data. User accounts have been preserved.")

except Exception as e:
    print(f"An error occurred: {e}")
    session.rollback()
finally:
    if 'session' in locals():
        session.close()
