#!/usr/bin/env python
"""
backend/main.py

Sets up the FastAPI application for BitcoinTX, a double-entry Bitcoin portfolio tracker.

Key Roles:
 - Loads environment variables & configures session-based authentication
 - Adds CORS middleware for frontend integration
 - Includes 'transaction', 'account', 'user', 'bitcoin', and calculation routers
 - Serves the Vite frontend static files for SPA routing
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse
from backend.routers import backup
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Load environment variables from a .env file at the project root
load_dotenv()

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
# Initialize the FastAPI application
# ---------------------------------------------------------
app = FastAPI(
    title="BitcoinTX Portfolio Tracker API",
    description=(
        "API for managing Bitcoin transactions/accounts with a "
        "double-entry system and FIFO cost basis. Session-based auth."
    ),
    version="1.0",
    debug=True,
    redirect_slashes=True
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
# Database: Create Tables at Startup
# ---------------------------------------------------------
from backend.database import create_tables, get_db

@app.on_event("startup")
def startup_event():
    """
    Ensures tables are created (if not already) when FastAPI starts.
    This won't delete or overwrite existing data; it's idempotent.
    """
    print("Running create_tables() at startup...")
    create_tables()
    print("Database tables created or verified.")

# ---------------------------------------------------------
# Routers (Transaction, User, Account, Calculation, Bitcoin, Reports, Debug)
# ---------------------------------------------------------
# (Mandatory) Routers (Transaction, User, Account, Calculation, Bitcoin, Reports)
from backend.routers import transaction, user, account, calculation, bitcoin, reports, backup

# Mandatory routers
app.include_router(transaction.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(user.router, prefix="/api/users", tags=["users"])
app.include_router(account.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(calculation.router, prefix="/api/calculations", tags=["calculations"])
app.include_router(bitcoin.router, prefix="/api/bitcoin", tags=["Bitcoin"])
app.include_router(reports.reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(backup.router, prefix="/api/backup", tags=["backup"])

# (Optional) Debug Router
try:
    from backend.routers import debug
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])
except ImportError:
    print("WARNING: Could not import 'debug' router. If you need debug features, "
          "ensure 'backend/routers/debug.py' exists.")

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
    # 1) Get user from DB by username
    user = get_user_by_username(login_req.username, db)
    if not user:
        # For security, don't reveal which part is invalid
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    # 2) Check password with passlib
    if not user.verify_password(login_req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    # 3) Store user.id in session (or store username if you prefer)
    request.session["user_id"] = user.id

    # 4) Return success
    return {"detail": f"Logged in as {user.username}"}

@app.post("/api/logout")
def logout(request: Request, response: Response):
    """
    Clear the session to log out the user.
    """
    request.session.clear()
    return {"detail": "Logged out successfully"}

# ---------------------------------------------------------
# ✅ Production: Serve React/Vite frontend
# ---------------------------------------------------------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException

# ✅ Serve built static assets (JS, CSS, fonts) under /static
app.mount("/static", StaticFiles(directory="frontend/dist/assets"), name="static")

# ✅ Catch-all route: Serve SPA index.html for unmatched frontend paths
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Prevent fallback from hijacking real API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")

    index_path = os.path.join("frontend", "dist", "index.html")
    return FileResponse(index_path)

# ---------------------------------------------------------
# Root Route
# ---------------------------------------------------------
@app.get("/")
def read_root():
    """
    Basic root path to confirm the API is running.
    """
    return {"message": "Welcome to BitcoinTX - Double-Entry Accounting Ready!"}

# ---------------------------------------------------------
# Local Testing
# ---------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.append(os.getenv("PYTHONPATH", "."))
    # e.g. run: uvicorn main:app --reload
