from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    attendances = relationship("Attendance", back_populates="user")
    leaves = relationship("LeaveRequest", back_populates="user")
    logs = relationship("AppLog", back_populates="user")
    password_resets = relationship("PasswordResetRequest", back_populates="user")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    login_time = Column(DateTime, default=datetime.datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    
    # Device fingerprint
    hostname = Column(String(100))
    os_info = Column(String(500))
    mac_address = Column(String(100))
    local_ip = Column(String(50))
    public_ip = Column(String(50))
    hardware_id = Column(String(200))
    
    user = relationship("User", back_populates="attendances")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    leave_type = Column(String(50)) # LONG, PRIOR, EMERGENCY
    reason = Column(Text)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String(50), default="PENDING") # PENDING, APPROVED, REJECTED
    
    user = relationship("User", back_populates="leaves")

class AppLog(Base):
    """Stores batch tracked folders & applications."""
    __tablename__ = "app_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime)
    app_name = Column(String(200))
    raw_title = Column(Text)
    
    user = relationship("User", back_populates="logs")

class PasswordResetRequest(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    request_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="PENDING") # PENDING, APPROVED, COMPLETED
    
    user = relationship("User", back_populates="password_resets")
