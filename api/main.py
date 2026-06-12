"""
main.py
=======
FastAPI application entry point.

CONCEPTS DEMONSTRATED:
    - FastAPI app creation and configuration
    - CORS middleware
    - Router registration
    - Startup/shutdown events
    - Global exception handling
"""

import logging
from contextlib import asynccontextmanager  # setup no-blocking
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.auth.router import router as auth_router
from api.routers.patients import router as patients_router
from api.routers.labs       import router as labs_router
from api.routers.treatments import router as treatments_router
from api.routers.visits     import router as visits_router
from api.middleware.audit import AuditMiddleware # middleware
from database.Connection import engine, Base

# ── Logging setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("oncotrack.api")

# ── Lifespan — startup and shutdown events ────────────────────
# This runs ONCE when the server starts, and ONCE when it stops.
# Perfect place to verify database connection on startup.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    logger.info("OncoTrack API starting up...")
    try:
        # verify database is reachable
        from sqlalchemy import text
        from database.Connection import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    yield  #app runs here

    # ── Shutdown ──
    logger.info("OncoTrack API shutting down...")


# ── Create the FastAPI app ────────────────────────────────────
app = FastAPI(
    title       = "OncoTrack API",
    description = "Oncology patient data management Analytics",
    version     = "1.0.0",
    docs_url    = "/docs",      # Swagger UI at http://localhost:8000/docs
    redoc_url   = "/redoc",     # ReDoc UI at http://localhost:8000/redoc
    lifespan    = lifespan,
)


# ── CORS middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:8501"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# -- Audit middleware -----------------------------------------
app.add_middleware(AuditMiddleware)

# Allows Streamlit (port 8501) to call this API (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins     = [
        "http://localhost:8501"   # Streamlit

    ],
    allow_credentials = True,
    allow_methods     = ["*"],     # GET, POST, PATCH, DELETE etc
    allow_headers     = ["*"],     # Authorization headers etc
)


# ── Global exception handler ──────────────────────────────────
# Catches any unhandled error and returns clean JSON
# instead of an ugly HTML error page
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc} — {request.method} {request.url}")
    return JSONResponse(
        status_code = 500,
        content     = {
            "error"  : "Internal server error",
            "detail" : str(exc),
            "path"   : str(request.url)
        }
    )

# ── Health check endpoint ─────────────────────────────────────

# Visit: http://localhost:8000/health
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status"  : "healthy",
        "version" : "1.0.0",
        "service" : "OncoTrack API"
    }

# ── Root endpoint ─────────────────────────────────────────────
@app.get("/", tags=["System"])
def root():
    return {
        "message" : "Welcome to OncoTrack API",
        "docs"    : "http://localhost:8000/docs",
        "health"  : "http://localhost:8000/health"
    }

# ── Routers ───────────────────────────────────────────────────

app.include_router(auth_router,       prefix="/auth",             tags=["Authentication"])
app.include_router(patients_router,   prefix="/api/patients",     tags=["Patients"])
app.include_router(labs_router,       prefix="/api/labs",         tags=["Labs"])
app.include_router(treatments_router, prefix="/api/treatments",   tags=["Treatments"])
app.include_router(visits_router,     prefix="/api/visits",       tags=["Visits"])
