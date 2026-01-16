#!/usr/bin/env python
"""
backend/main.py

Sets up the FastAPI application for BitcoinTX, a double-entry Bitcoin portfolio tracker.

Key Roles:
 - Loads environment variables & configures session-based authentication
 - Adds CORS middleware for frontend integration
 - Includes 'transaction', 'account', 'user', 'bitcoin', and calculation routers
 - Serves the built React/Vite frontend from 'frontend/dist'
"""

import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Load environment variables from a .env file at the project root
load_dotenv()

# ---------------------------------------------------------
# Frontend dist path (needed early for SPA fallback handler)
# Supports BTCTX_FRONTEND_DIST env var for desktop app bundling
# ---------------------------------------------------------
frontend_dist = os.environ.get(
    "BTCTX_FRONTEND_DIST",
    os.path.join(os.path.dirname(__file__), "../frontend/dist")
)

# ---------------------------------------------------------
# Session Configuration
# ---------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")  # Fallback if not set

# Default CORS origins if none specified (dev environment)
default_origins = (
    "http://127.0.0.1:3000,"
    "http://localhost:3000,"
    "http://127.0.0.1:5173,"
    "http://localhost:5173,"
    "http://127.0.0.1:8000,"
    "http://localhost:8000"
)
raw_origins = os.getenv("CORS_ALLOW_ORIGINS", default_origins)
ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",")]

# ---------------------------------------------------------
# Database import (needed before lifespan)
# ---------------------------------------------------------
from backend.database import create_tables, get_db

# ---------------------------------------------------------
# Lifespan context manager for startup/shutdown
# ---------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    Ensures tables are created when FastAPI starts.
    """
    # Startup
    logger.info("Running create_tables() at startup...")
    create_tables()
    logger.info("Database tables created or verified.")
    yield
    # Shutdown (nothing needed currently)

# ---------------------------------------------------------
# Initialize the FastAPI application
# ---------------------------------------------------------
app = FastAPI(
    title="BitcoinTX Portfolio Tracker API",
    description=(
        "API for managing Bitcoin transactions/accounts with a "
        "double-entry system and FIFO cost basis. Session-based auth."
    ),
    version="1.0",
    debug=os.getenv("DEBUG", "false").lower() == "true",
    redirect_slashes=True,
    lifespan=lifespan
)

# ---------------------------------------------------------
# Add Session Middleware
# ---------------------------------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="btc_session_id",
    https_only=False  # Set to True in production if you serve over HTTPS
)

# ---------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Or ["*"] in dev if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# SPA Fallback Exception Handler
# ---------------------------------------------------------
from starlette.responses import JSONResponse

@app.exception_handler(StarletteHTTPException)
async def spa_fallback_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle 404 errors for SPA routing.

    When a user navigates directly to a client-side route (e.g., /dashboard),
    StaticFiles raises a 404 because no such file exists. This handler
    catches those 404s and serves index.html, allowing React Router to
    handle the route on the client side.

    API routes (/api/*) are excluded - they should return proper JSON errors.
    """
    if exc.status_code == 404 and not request.url.path.startswith("/api/"):
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")

    # For API routes or non-404 errors, return JSON response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail or "Error"}
    )

# ---------------------------------------------------------
# Routers (Transaction, User, Account, Calculation, Bitcoin, Reports, Debug)
# ---------------------------------------------------------
# (Mandatory) Routers (Transaction, User, Account, Calculation, Bitcoin, Reports)
from backend.routers import transaction, user, account, calculation, bitcoin, reports, backup, csv_import

# Mandatory routers
app.include_router(transaction.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(user.router, prefix="/api/users", tags=["users"])
app.include_router(account.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(calculation.router, prefix="/api/calculations", tags=["calculations"])
app.include_router(bitcoin.router, prefix="/api/bitcoin", tags=["Bitcoin"])
app.include_router(reports.reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(backup.router, prefix="/api/backup", tags=["backup"])
app.include_router(csv_import.router, prefix="/api/import", tags=["import"])

# (Optional) Debug Router
try:
    from backend.routers import debug
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])
except ImportError:
    print(
        "WARNING: Could not import 'debug' router. If you need debug features, "
        "ensure 'backend/routers/debug.py' exists."
    )

# ---------------------------------------------------------
# Session-Based Auth Helpers
# ---------------------------------------------------------
def get_current_user(request: Request) -> str:
    """
    Session-based "get_current_user" dependency.
    Looks up 'user_id' in request.session. If not found,
    raises 401. Otherwise, returns the user_id (or username).
    
    In a real app, you might store a "username" or a full user object.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id

# ---------------------------------------------------------
# Protected Route Example
# ---------------------------------------------------------
@app.get("/api/protected")
def read_protected_route(current_user: str = Depends(get_current_user)):
    """
    Demonstration of a session-protected endpoint.
    If 'user_id' isn't in the session, we raise 401.
    Otherwise, we greet the logged-in user.
    """
    return {"message": f"Hello, user {current_user}. You have access to this route!"}

# ---------------------------------------------------------
# LoginRequest Pydantic Model
# ---------------------------------------------------------
class LoginRequest(BaseModel):
    """
    Schema for login JSON:
      { "username": "someName", "password": "somePass" }
    """
    username: str
    password: str

# ---------------------------------------------------------
# Production-Ready Login / Logout Endpoints
# ---------------------------------------------------------
from backend.services.user import get_user_by_username  # for verifying credentials

@app.post("/api/login")
def login(
    login_req: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Production-level session-based login:
      1) Accepts JSON { "username": "...", "password": "..." }
      2) Look up the user in the DB, check hashed password
      3) If valid, store user.id in session
      4) Return success message
    """
    user = get_user_by_username(login_req.username, db)
    if not user:
        # For security, don't reveal which part is invalid
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if not user.verify_password(login_req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    request.session["user_id"] = user.id
    return {"detail": f"Logged in as {user.username}"}

@app.post("/api/logout")
def logout(request: Request, response: Response):
    """
    Clear the session to log out the user.
    """
    request.session.clear()
    return {"detail": "Logged out successfully"}

# ---------------------------------------------------------
# Production: Serve React/Vite frontend from dist/ at "/"
# ---------------------------------------------------------
from fastapi.staticfiles import StaticFiles

# Mount static files from dist/ at root ("/")
# Note: html=True serves index.html for root and directories only.
# The SPA fallback for client-side routes is handled by spa_fallback_handler above.
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

# ---------------------------------------------------------
# Local Testing
# ---------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.append(os.getenv("PYTHONPATH", "."))
    # e.g. run: uvicorn main:app --reload
