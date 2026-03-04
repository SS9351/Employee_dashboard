import sys
import os
sys.path.append('.')

from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from auth import get_password_hash

def seed_users():
    db = SessionLocal()
    
    users_to_add = [
        {"username": "Sneha", "email": "Sneha@sahastra.in", "full_name": "Sneha Patil", "is_admin": False, "password": "password123"},
        {"username": "Akansha", "email": "Akansha@sahastra.in", "full_name": "Akansha gurav", "is_admin": False, "password": "password123"},
        {"username": "Durga", "email": "Durga@sahastra.in", "full_name": "Durga ungle", "is_admin": False, "password": "password123"},
        {"username": "Shalini", "email": "shalini@sahastra.in", "full_name": "Shalini hake", "is_admin": True, "password": "password123"},
        {"username": "Shankar", "email": "Shabkarappa@sahastra.in", "full_name": "Shankarappa Shabadi", "is_admin": True, "password": "password123"},
        {"username": "Shreyash", "email": "test@test.test", "full_name": "Shreyash Shabadi", "is_admin": True, "password": "password123"}
    ]

    for user_data in users_to_add:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing_user:
            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                is_admin=user_data["is_admin"],
                hashed_password=get_password_hash(user_data["password"])
            )
            db.add(new_user)
            print(f"Added {user_data['username']}")
        else:
            print(f"Skipped {user_data['username']} (Already exists)")
            
    db.commit()
    db.close()
    print("Database seeding complete!")

if __name__ == "__main__":
    seed_users()
