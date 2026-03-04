import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from api import router

app = FastAPI(title="Sahastra Attendance Backend")

@app.on_event("startup")
def startup_event():
    # Create DB Schema safely after app boot
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Failed to create schema automatically: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Sahastra Attendance System API"}

@app.get("/api/init-admin")
def setup_admin():
    try:
        import init_db
        import seed_employees
        
        # Initialize DB (creates tables and default admin if missing)
        init_db.init_db()
        
        # Run the mass-injection script to create the 6 user accounts
        seed_employees.seed_users()
        return {"status": "success", "message": "Admin user and all 6 Employee accounts firmly injected into live production database."}
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        return {"status": "error", "message": str(e), "traceback": err}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
