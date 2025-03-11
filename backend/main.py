#!/usr/bin/env python
"""
main.py

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

# Load environment variables from a .env file at the project root
load_dotenv()

# ---------------------------------------------------------
# Session Configuration
# ---------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")  # Fallback if not set
# We use SECRET_KEY to sign session cookies. Starlette stores sessions in-memory by default.

# Default CORS origins if none specified (e.g., dev environment)
default_origins = (
    "http://127.0.0.1:3000,"
    "http://localhost:3000,"
    "http://127.0.0.1:5173,"
    "http://localhost:5173"
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
    debug=True
)

# ---------------------------------------------------------
# Add Session Middleware
# ---------------------------------------------------------
# This middleware automatically sets/respects a signed cookie
# named "btc_session_id" (you can rename if desired).
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
from backend.database import create_tables

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
# Routers (Transaction, User, Account, Calculation, Bitcoin)
# ---------------------------------------------------------
from backend.routers import transaction, user, account, calculation, bitcoin

app.include_router(transaction.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(user.router, prefix="/api/users", tags=["users"])
app.include_router(account.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(calculation.router, prefix="/api/calculations", tags=["calculations"])
app.include_router(bitcoin.router, prefix="/api", tags=["Bitcoin"])

# ---------------------------------------------------------
# Session-Based Auth Helpers
# ---------------------------------------------------------
def get_current_user(request: Request) -> str:
    """
    Session-based "get_current_user" dependency.
    Looks up 'user_id' in request.session. If not found,
    raises 401. Otherwise, returns the user_id (or username).
    
    In a real app, you might store a "username" or full user object.
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
# Login / Logout Example Endpoints
# ---------------------------------------------------------
@app.post("/api/login")
def login(request: Request, response: Response, username: str):
    """
    Simple example of session-based login:
      1. Verify credentials (skipped here for brevity).
      2. If valid, store user_id or username in session.
    """
    # TODO: Check user in DB, verify password, etc. For now, just store "username"
    request.session["user_id"] = username
    return {"detail": f"Logged in as {username}"}

@app.post("/api/logout")
def logout(request: Request, response: Response):
    """
    Clear the session to log out the user.
    """
    request.session.clear()
    return {"detail": "Logged out successfully"}

# ---------------------------------------------------------
# Serve Vite Frontend Static Files with SPA Routing
# ---------------------------------------------------------
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as ex:
            if ex.status_code == 404:
                # Serve index.html for any 404 (unmatched routes)
                return FileResponse(os.path.join(self.directory, "index.html"))
            else:
                raise

app.mount("/", SPAStaticFiles(directory="frontend/dist", html=True), name="static")

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
    # Session-based auth is now set up in place of JWT.