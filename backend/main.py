#!/usr/bin/env python
"""
main.py

Refactored for clarity regarding our double-entry changes:
 - This file mostly sets up FastAPI, JWT auth, and includes routers.
 - The transaction router now uses a double-entry system internally, 
   but no adjustments are needed here since we just include the router.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Load environment variables from project root .env
load_dotenv()

# Retrieve security and authentication settings
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Default origins if none set
default_origins = (
    "http://127.0.0.1:3000,"
    "http://localhost:3000,"
    "http://127.0.0.1:5173,"
    "http://localhost:5173"
)
raw_origins = os.getenv("CORS_ALLOW_ORIGINS", default_origins)
ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",")]

from fastapi.security import OAuth2PasswordBearer

# The tokenUrl points to your token endpoint (in user router or similar).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# Initialize the FastAPI application
app = FastAPI(
    title="BitcoinTX Portfolio Tracker API",
    description="API for managing Bitcoin transactions, accounts, and portfolio tracking with a double-entry system.",
    version="1.0",
    debug=True
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- JWT Helper Functions ---

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token. 
    Double-entry changes do not affect auth logic.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str) -> str:
    """
    Verify a JWT access token and extract the username (sub field).
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
    Retrieve the current authenticated user from the JWT token.
    """
    return verify_access_token(token)

# --- Include Routers ---
from backend.routers import transaction, user, account

# The transaction router (Plan B: from_account_id/to_account_id) is included here.
app.include_router(transaction.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(user.router, prefix="/api/users", tags=["Users"])
app.include_router(account.router, prefix="/api/accounts", tags=["Accounts"])

# --- Protected Route Example ---
@app.get("/protected")
def read_protected_route(current_user: str = Depends(get_current_user)):
    """
    A test route requiring JWT authentication.
    Double-entry does not affect this logic.
    """
    return {"message": f"Hello, {current_user}. You have access to this route!"}

# --- Root Route ---
@app.get("/")
def read_root():
    """
    Basic root route to confirm the API is running.
    """
    return {"message": "Welcome to BitcoinTX"}

# --- For local testing with 'python main.py' ---
if __name__ == "__main__":
    import sys
    sys.path.append(os.getenv("PYTHONPATH", "."))
