import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from api import router

# Create DB Schema
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sahastra Attendance Backend")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
