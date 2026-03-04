import pymysql
import os

# Connect directly to the MySQL server (without a DB name yet)
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Shrutika@22")  # Syncing with database.py
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DB = os.getenv("MYSQL_DB", "sahastra_attendance")

try:
    print(f"Connecting to MySQL Server on {MYSQL_HOST}...")
    connection = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        port=MYSQL_PORT
    )
    
    with connection.cursor() as cursor:
        print(f"Creating database '{MYSQL_DB}' if it doesn't exist...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}`;")
    
    connection.commit()
    connection.close()

    print(f"Database setup complete. Invoking SQLAlchemy metadata mapping...")
    
    # After ensuring the DB exists, let SQLAlchemy build out the Tables
    from database import engine, Base
    import models # Load all models
    
    Base.metadata.create_all(bind=engine)
    print("\u2705 Tables successfully created inside MySQL!")
    
    # Create default Admin if none exists
    from sqlalchemy.orm import sessionmaker
    from auth import get_password_hash
    Session = sessionmaker(bind=engine)
    db = Session()
    
    admin_user = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin_user:
        new_admin = models.User(
            username="admin",
            hashed_password=get_password_hash("admin123"), # Default admin pass
            full_name="System Administrator",
            is_admin=True
        )
        db.add(new_admin)
        db.commit()
        print("\u2705 Default Admin User ('admin' / 'admin123') created!")
    
    db.close()

except Exception as e:
    print(f"\u274c Error setting up MySQL: {e}")
