import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from api import router

app = FastAPI(title="Sahastra Attendance Backend")

@app.on_event("startup")
def startup_event():
    # Attempt to create DB Schema safely after app boot
    try:
        from database import engine
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Failed to create schema automatically: {e}")
        try:
            from database import engine
            engine.dispose() # Free up the hung connection thread!
        except:
            pass

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
        import seed_employees
        
        # Run the mass-injection script to create the Admin + 6 normal accounts
        seed_employees.seed_users()
        return {"status": "success", "message": "Admin user and all 6 Employee accounts firmly injected into live production database."}
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        return {"status": "error", "message": str(e), "traceback": err}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
