"""
api.py
ExamForge — FastAPI entry point. Each feature owns its own route file
under routes/; this file only wires them together and serves the frontend.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import upload_routes, generate_routes, submit_routes

FRONTEND_DIR = Path(__file__).parent / "frontend"

app = FastAPI(title="ExamForge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_routes.router)
app.include_router(generate_routes.router)
app.include_router(submit_routes.router)


@app.get("/api/health")
def health():
    return {"status": "ExamForge is running", "phase": "6-7 — LangGraph + grading loop + frontend"}


# Mounted LAST so every /api/... route and /docs above takes priority.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")