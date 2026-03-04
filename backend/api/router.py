from fastapi import APIRouter, Depends, HTTPException, status, Request

from sqlalchemy.orm import Session

from database import get_db

from models import User, Attendance, LeaveRequest, AppLog

from auth import verify_password, create_access_token, decode_access_token, get_password_hash
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import datetime
from sqlalchemy import desc


router = APIRouter()

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):

    try:

        payload = decode_access_token(credentials.credentials)

        username: str = payload.get("sub")

        if username is None:

            raise HTTPException(status_code=401, detail="Invalid token")

    except Exception:

        raise HTTPException(status_code=401, detail="Invalid token")


    user = db.query(User).filter(User.username == username).first()

    if user is None:

        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/auth/login")

def login(request: Request, payload: dict, db: Session = Depends(get_db)):

    # Very basic validation, schema checks could be added

    username = payload.get("username")

    password = payload.get("password")

    device_info = payload.get("device_info", {})


    user = db.query(User).filter(User.username == username).first()
    

    # Auto-creating test users for DEMO purposes
    if not user and username == "test":

        from auth import get_password_hash

        user = User(username="test", hashed_password=get_password_hash("test1234"), full_name="Test Employee")

        db.add(user)

        db.commit()

        db.refresh(user)


    if not user or not verify_password(password, user.hashed_password):

        raise HTTPException(status_code=401, detail="Invalid username or password")


    # Record Attendance

    attendance = Attendance(
        user_id=user.id,

        login_time=datetime.datetime.utcnow(),

        hostname=device_info.get("hostname", ""),

        os_info=device_info.get("os_info", ""),

        mac_address=device_info.get("mac_address", ""),

        local_ip=device_info.get("local_ip", ""),

        public_ip=request.client.host,

        hardware_id=device_info.get("hardware_id", "")
    )

    db.add(attendance)

    db.commit()


    token = create_access_token(data={"sub": user.username})

    return {"access_token": token, "user": {"name": user.full_name, "is_admin": user.is_admin}}


@router.post("/auth/logout")

def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    # Mark logout time for most recent login today

    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0)

    attendance = db.query(Attendance).filter(

        Attendance.user_id == current_user.id,

        Attendance.login_time >= today_start,

        Attendance.logout_time == None

    ).order_by(Attendance.id.desc()).first()

    if attendance:

        attendance.logout_time = datetime.datetime.utcnow()

        db.commit()
    

    return {"message": "Logged out successfully"}

@router.post("/auth/forgot-password")
def request_password_reset(payload: dict, db: Session = Depends(get_db)):
    username = payload.get("username")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Don't reveal if user exists for security, just return success
        return {"message": "If the username exists, a reset request has been logged."}
        
    # Check if a pending request already exists to avoid spam
    from models import PasswordResetRequest
    existing_req = db.query(PasswordResetRequest).filter(
        PasswordResetRequest.user_id == user.id,
        PasswordResetRequest.status == "PENDING"
    ).first()
    
    if existing_req:
        return {"message": "A reset request is already pending approval from the admin."}
        
    # Create new request
    new_req = PasswordResetRequest(user_id=user.id, status="PENDING")
    db.add(new_req)
    db.commit()
    
    return {"message": "Reset request sent to admin for approval."}

@router.post("/auth/reset-password")
def reset_password(payload: dict, db: Session = Depends(get_db)):
    username = payload.get("username")
    new_password = payload.get("new_password")
    
    if not username or not new_password:
        raise HTTPException(status_code=400, detail="Missing username or new password")
        
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    from models import PasswordResetRequest
    approved_req = db.query(PasswordResetRequest).filter(
        PasswordResetRequest.user_id == user.id,
        PasswordResetRequest.status == "APPROVED"
    ).order_by(desc(PasswordResetRequest.id)).first()
    
    if not approved_req:
        raise HTTPException(status_code=403, detail="Reset not approved or no pending request.")
        
    # Apply new password
    user.hashed_password = get_password_hash(new_password)
    
    # Mark request as completed
    approved_req.status = "COMPLETED"
    
    db.commit()
    
    return {"message": "Password successfully reset! You can now login."}


@router.get("/leaves")

def get_leaves(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    leaves = db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id).all()

    result = []

    for lv in leaves:

        result.append({

            "type": lv.leave_type,

            "reason": lv.reason,

            "start_date": lv.start_date.isoformat() if lv.start_date else "",

            "end_date": lv.end_date.isoformat() if lv.end_date else "",

            "status": lv.status

        })

    return {"leaves": result}


@router.post("/leaves/apply")

def apply_leave(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    try:

        start_date = datetime.datetime.fromisoformat(payload.get("start_date"))

        end_date = datetime.datetime.fromisoformat(payload.get("end_date"))

    except:

        start_date = datetime.datetime.utcnow()

        end_date = datetime.datetime.utcnow()


    leave = LeaveRequest(
        user_id=current_user.id,

        leave_type=payload.get("leave_type", "UNKNOWN"),

        reason=payload.get("reason", ""),
        start_date=start_date,
        end_date=end_date,

        status="PENDING"
    )

    db.add(leave)

    db.commit()

    return {"message": "Leave request submitted."}


@router.post("/tracker/sync")

def sync_activity(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    logs_data = payload.get("logs", [])
    for log in logs_data:

        try:
            ts = datetime.datetime.fromisoformat(log.get("time"))

        except:

            ts = datetime.datetime.utcnow()
            

        app_log = AppLog(
            user_id=current_user.id,
            timestamp=ts,
            app_name=log.get("app", ""),

            raw_title=log.get("raw_title", "")
        )

        db.add(app_log)

    db.commit()

    return {"message": "Synced"}


from models import PasswordResetRequest
from sqlalchemy import desc

# --- Admin Endpoints ---

@router.get("/admin/users")
def get_all_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    users = db.query(User).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "is_admin": u.is_admin,
            "is_active": u.is_active
        })
    return {"users": result}
    
@router.get("/admin/reset-requests")
def get_reset_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    requests = db.query(PasswordResetRequest).order_by(desc(PasswordResetRequest.request_date)).all()
    result = []
    for req in requests:
        result.append({
            "id": req.id,
            "employee_name": req.user.full_name,
            "username": req.user.username,
            "request_date": req.request_date.isoformat(),
            "status": req.status
        })
    return {"requests": result}

@router.post("/admin/reset-requests/{request_id}/approve")
def approve_reset_request(request_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    req = db.query(PasswordResetRequest).filter(PasswordResetRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    req.status = "APPROVED"
    db.commit()
    
    return {"message": "Reset request approved."}


@router.get("/admin/leaves")

def get_all_leaves(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:

        raise HTTPException(status_code=403, detail="Not authorized")
        

    leaves = db.query(LeaveRequest).order_by(LeaveRequest.id.desc()).all()

    result = []

    for lv in leaves:

        result.append({

            "id": lv.id,

            "employee_name": lv.user.full_name,

            "type": lv.leave_type,

            "reason": lv.reason,

            "start_date": lv.start_date.isoformat() if lv.start_date else "",

            "end_date": lv.end_date.isoformat() if lv.end_date else "",

            "status": lv.status

        })

    return {"leaves": result}


@router.post("/admin/leaves/{leave_id}/status")

def update_leave_status(leave_id: int, payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:

        raise HTTPException(status_code=403, detail="Not authorized")
        

    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()

    if not leave:

        raise HTTPException(status_code=404, detail="Leave not found")
        

    status = payload.get("status")

    if status in ["APPROVED", "REJECTED"]:

        leave.status = status

        db.commit()

        return {"message": f"Leave status updated to {status}"}

    raise HTTPException(status_code=400, detail="Invalid status")


@router.get("/admin/attendance")

def get_all_attendance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:

        raise HTTPException(status_code=403, detail="Not authorized")
        

    # Get all attendance records from today

    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0)

    records = db.query(Attendance).filter(Attendance.login_time >= today_start).order_by(Attendance.login_time.desc()).all()
    

    result = []
    for r in records:

        result.append({

            "employee_name": r.user.full_name,
            "login_time": r.login_time.isoformat() if r.login_time else "",
            "logout_time": r.logout_time.isoformat() if r.logout_time else "",
            "hostname": r.hostname,
            "ip": r.local_ip,
            "mac_address": r.mac_address
        })

    return {"attendance": result}


@router.get("/admin/logs")

def get_all_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:

        raise HTTPException(status_code=403, detail="Not authorized")
        

    # Fetch recent logs (e.g. last 100)

    logs = db.query(AppLog).order_by(AppLog.timestamp.desc()).limit(100).all()

    result = []
    for log in logs:

        result.append({

            "employee_name": log.user.full_name,
            "time": log.timestamp.isoformat() if log.timestamp else "",
            "app_name": log.app_name,

            "raw_title": log.raw_title

        })

    return {"logs": result}

@router.get("/admin/actual-attendance")
def get_actual_attendance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # We evaluate all attendance records.
    records = db.query(Attendance).order_by(Attendance.login_time.desc()).all()
    
    result = []
    for r in records:
        if r.login_time and r.logout_time:
            duration = r.logout_time - r.login_time
            duration_hours = duration.total_seconds() / 3600.0
            status = "Present" if duration_hours >= 6 else "Absent (< 6 Hrs)"
            duration_str = str(duration).split('.')[0] # HH:MM:SS
        else:
            duration_str = "Session Active"
            status = "In Progress"
            
        result.append({
            "employee_name": r.user.full_name,
            "date": r.login_time.date().isoformat() if r.login_time else "",
            "login_time": r.login_time.time().strftime("%H:%M:%S") if r.login_time else "",
            "logout_time": r.logout_time.time().strftime("%H:%M:%S") if r.logout_time else "",
            "duration": duration_str,
            "status": status
        })
        
    return {"actual_attendance": result}

@router.get("/attendance/stats")
def get_attendance_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import calendar
    
    now = datetime.datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get all attendance records for this month
    records = db.query(Attendance).filter(
        Attendance.user_id == current_user.id,
        Attendance.login_time >= start_of_month
    ).all()
    
    # Track which days have "Present" status
    present_days = set()
    for r in records:
        if r.login_time and r.logout_time:
            duration_hours = (r.logout_time - r.login_time).total_seconds() / 3600.0
            if duration_hours >= 6:
                present_days.add(r.login_time.date())
                
    # Get approved leaves for this month
    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == current_user.id,
        LeaveRequest.status == "APPROVED",
        LeaveRequest.start_date >= start_of_month
    ).all()
    
    approved_leave_days = set()
    for lv in leaves:
        current_date = lv.start_date
        while current_date <= lv.end_date:
            approved_leave_days.add(current_date.date())
            current_date += datetime.timedelta(days=1)
            
    days_passed = now.day
    present_count = len(present_days)
    approved_leave_count = len([d for d in approved_leave_days if d.month == now.month and d.day <= now.day])
    
    total_active = present_count + approved_leave_count
    absent_count = max(0, days_passed - total_active)
    
    return {
        "present": present_count,
        "absent": absent_count,
        "approved_leaves": approved_leave_count,
        "total_days_so_far": days_passed
    }

