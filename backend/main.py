#!/usr/bin/env python
"""
main.py

Sets up the FastAPI application for BitcoinTX, a double-entry Bitcoin portfolio tracker.

Key Roles:
 - Load environment variables & configure JWT authentication
 - Add CORS middleware for frontend integration
 - Include the 'transaction', 'account', and 'user' routers
   which now implement multi-line ledger entries, BTC lot tracking, etc.

Because our double-entry logic is in the services and routers, no special
changes are needed here beyond referencing them. This file is the entry
point for running the API and hooking up the authentication + routing.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Load environment variables from a .env file at the project root
load_dotenv()

# ---------------------------------------------------------
# JWT & Auth Configuration
# ---------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")  # Fallback if not set
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Default CORS origins if none specified
default_origins = (
    "http://127.0.0.1:3000,"
    "http://localhost:3000,"
    "http://127.0.0.1:5173,"
    "http://localhost:5173"
)
raw_origins = os.getenv("CORS_ALLOW_ORIGINS", default_origins)
ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",")]

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# ---------------------------------------------------------
# Initialize the FastAPI application
# ---------------------------------------------------------
app = FastAPI(
    title="BitcoinTX Portfolio Tracker API",
    description=(
        "API for managing Bitcoin transactions and accounts with a "
        "fully double-entry system, plus FIFO cost basis for BTC. "
        "Handles user authentication via JWT."
    ),
    version="1.0",
    debug=True
)

# ---------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# JWT Helper Functions
# ---------------------------------------------------------
def create_access_token(data: dict) -> str:
    """
    Create a JWT access token using SECRET_KEY.
    The double-entry design does not affect auth, but
    we keep it consistent so that only authenticated
    users can access certain routes if desired.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str) -> str:
    """
    Verify a JWT, extracting the 'sub' (username). 
    Raises HTTPException(401) if invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency for protected endpoints:
    verifies the token and returns the username.
    """
    return verify_access_token(token)

# ---------------------------------------------------------
# Include Routers
# ---------------------------------------------------------
# We import the transaction, user, and account routers,
# each referencing the multi-line ledger or user/account logic.
from backend.routers import transaction, user, account

app.include_router(transaction.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(user.router, prefix="/api/users", tags=["users"])
app.include_router(account.router, prefix="/api/accounts", tags=["accounts"])

# ---------------------------------------------------------
# Protected Route Example
# ---------------------------------------------------------
@app.get("/protected")
def read_protected_route(current_user: str = Depends(get_current_user)):
    """
    Demonstration of a JWT-protected endpoint. The double-entry system
    is unaffected by auth logic, but you could restrict transaction 
    creation to authenticated users only, for example.
    """
    return {"message": f"Hello, {current_user}. You have access to this route!"}

# ---------------------------------------------------------
# Root Route
# ---------------------------------------------------------
@app.get("/")
def read_root():
    """
    The basic root path to confirm the API is running.
    Does not intersect with the double-entry logic directly.
    """
    return {"message": "Welcome to BitcoinTX - Double-Entry Accounting Ready!"}

# ---------------------------------------------------------
# Local Testing
# ---------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.append(os.getenv("PYTHONPATH", "."))
    # You could run: python main.py (with a dev server, e.g. 'uvicorn main:app --reload')
    # The double-entry system is loaded in the transaction, account, user routers.
