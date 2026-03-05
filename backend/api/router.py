from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO

from sqlalchemy.orm import Session

from database import get_db

from models import User, Attendance, LeaveRequest, AppLog

from auth import verify_password, create_access_token, decode_access_token, get_password_hash
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import datetime
from sqlalchemy import desc
from ist_helper import get_ist_now

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

        login_time=get_ist_now(),

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

    today_start = get_ist_now().replace(hour=0, minute=0, second=0)

    attendance = db.query(Attendance).filter(

        Attendance.user_id == current_user.id,

        Attendance.login_time >= today_start,

        Attendance.logout_time == None

    ).order_by(Attendance.id.desc()).first()

    if attendance:

        attendance.logout_time = get_ist_now()

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

        start_date = get_ist_now()

        end_date = get_ist_now()


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

            ts = get_ist_now()
            

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

@router.post("/admin/users/{user_id}/toggle-admin")
def toggle_admin_status(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_admin = not user.is_admin
    db.commit()
    
    return {"message": f"User {user.username} admin status changed to {user.is_admin}", "is_admin": user.is_admin}
    
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

    today_start = get_ist_now().replace(hour=0, minute=0, second=0)

    records = db.query(Attendance).filter(Attendance.login_time >= today_start).order_by(Attendance.login_time.desc()).all()
    

    result = []
    for r in records:

        result.append({

            "id": r.id,
            "employee_name": r.user.full_name,
            "login_time": r.login_time.isoformat() if r.login_time else "",
            "logout_time": r.logout_time.isoformat() if r.logout_time else "",
            "hostname": r.hostname,
            "ip": r.local_ip,
            "mac_address": r.mac_address
        })

    return {"attendance": result}

@router.post("/admin/attendance/{attendance_id}/terminate")
def terminate_attendance_session(attendance_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
        
    if attendance.logout_time:
        return {"message": "Session is already terminated!"}
        
    from ist_helper import get_ist_now
    attendance.logout_time = get_ist_now()
    db.commit()
    
    return {"message": f"Successfully terminated {attendance.user.full_name}'s session."}


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

@router.get("/admin/export-excel")
def export_excel(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        users = db.query(User).all()
        pd.DataFrame([{ "ID": u.id, "Username": u.username, "Full Name": u.full_name, "Email": u.email, "Is Admin": u.is_admin } for u in users]).to_excel(writer, sheet_name="Users", index=False)
        
        attendance = db.query(Attendance).all()
        pd.DataFrame([{ "ID": a.id, "Employee": a.user.full_name, "Login Time": a.login_time.isoformat() if a.login_time else "", "Logout Time": a.logout_time.isoformat() if a.logout_time else "", "IP": a.local_ip, "MAC": a.mac_address } for a in attendance]).to_excel(writer, sheet_name="Attendance", index=False)
        
        leaves = db.query(LeaveRequest).all()
        pd.DataFrame([{ "ID": l.id, "Employee": l.user.full_name, "Type": l.leave_type, "Reason": l.reason, "Start": l.start_date.isoformat() if l.start_date else "", "End": l.end_date.isoformat() if l.end_date else "", "Status": l.status } for l in leaves]).to_excel(writer, sheet_name="Leaves", index=False)
        
        logs = db.query(AppLog).all()
        pd.DataFrame([{ "ID": l.id, "Employee": l.user.full_name, "Timestamp": l.timestamp.isoformat() if l.timestamp else "", "App Name": l.app_name, "Window Title": l.raw_title } for l in logs]).to_excel(writer, sheet_name="App Logs", index=False)
        
    output.seek(0)
    
    # Store timestamp for 2-minute deletion lock using in-memory dictionary
    if not hasattr(request.app.state, "last_export_time"):
        request.app.state.last_export_time = {}
    request.app.state.last_export_time[current_user.id] = get_ist_now()
    
    return StreamingResponse(
        output, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": f"attachment; filename=sahastra_export_{get_ist_now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
    )

@router.delete("/admin/logs")
def delete_all_logs(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if not hasattr(request.app.state, "last_export_time") or current_user.id not in request.app.state.last_export_time:
        raise HTTPException(status_code=400, detail="You must export to Excel first before deleting logs.")
        
    last_export = request.app.state.last_export_time[current_user.id]
    diff = get_ist_now() - last_export
    if diff.total_seconds() > 120:
        raise HTTPException(status_code=400, detail="Export expired. You must export again within 2 minutes to delete logs.")
        
    db.query(AppLog).delete()
    db.commit()
    return {"message": "All application logs have been successfully deleted."}

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
    
    now = get_ist_now()
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
    
    # Build complete calendar days struct for frontend Calendar
    calendar_days = {}
    for day_num in range(1, days_passed + 1):
        check_date = start_of_month.date().replace(day=day_num)
        
        if check_date in present_days:
            calendar_days[check_date.isoformat()] = "Present"
        elif check_date in approved_leave_days:
            calendar_days[check_date.isoformat()] = "Approved Leave"
        else:
            calendar_days[check_date.isoformat()] = "Absent"
            
    return {
        "present": present_count,
        "absent": absent_count,
        "approved_leaves": approved_leave_count,
        "total_days_so_far": days_passed,
        "calendar_days": calendar_days
    }

@router.get("/admin/wipe-database-danger")
def wipe_database_danger(db: Session = Depends(get_db)):
    db.query(Attendance).delete()
    db.query(LeaveRequest).delete()
    db.query(AppLog).delete()
    db.query(PasswordResetRequest).delete()
    db.commit()
    return {"message": "ALL OPERATIONAL DATA WIPED"}
