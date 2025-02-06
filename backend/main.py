#!/usr/bin/env python
"""
main.py

This module is the entry point for the BitcoinTX backend application.
It configures and launches the FastAPI app, including:
  - Loading environment variables from a consolidated .env file in the project root.
  - Setting up CORS middleware using allowed origins defined in the .env.
  - Configuring JWT-based authentication helper functions.
  - Including routers for transactions, users, and accounts.
  - Defining basic test routes for verifying that the API is running.

This file does not handle database configuration directly—the database
settings are managed by backend/database.py. Ensure that your consolidated
.env file (placed in the project root) contains the correct settings.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Load environment variables from the project root .env file.
# (Make sure your consolidated .env file is located in the project root.)
load_dotenv()

# Retrieve security and authentication settings from environment variables.
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
# JWT_ACCESS_TOKEN_EXPIRE_MINUTES is expected to be set in .env as JWT_ACCESS_TOKEN_EXPIRE_MINUTES.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Retrieve allowed origins for CORS; these should be defined as a comma-separated list in .env.
ALLOWED_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:3000").split(",")

# Set up OAuth2 scheme for JWT authentication.
# The tokenUrl should point to the endpoint that issues tokens (e.g., /api/token).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# Initialize the FastAPI application with descriptive metadata.
app = FastAPI(
    title="BitcoinTX Portfolio Tracker API",
    description="API for managing Bitcoin transactions, accounts, and portfolio tracking.",
    version="1.0",
    debug=True  # Enable debug mode during development; disable in production.
)

# Configure CORS middleware to allow requests from specified origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # These origins come from the .env file.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- JWT Helper Functions ---

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token for authentication.

    Args:
        data (dict): The payload to include in the token. Should include a "sub" key representing the username.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str) -> str:
    """
    Verify a JWT access token and extract the username.

    Args:
        token (str): The JWT token to verify.

    Returns:
        str: The username from the token's payload if the token is valid.

    Raises:
        HTTPException: If the token is invalid or expired.
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
    FastAPI dependency that retrieves the current authenticated user from the JWT token.

    Args:
        token (str): The JWT token provided in the Authorization header.

    Returns:
        str: The username of the authenticated user.
    """
    return verify_access_token(token)

# --- Include Routers for Modular Functionality ---

# Import routers from the backend routers package.
from backend.routers import transaction, user, account

# Include the transactions router under the prefix "/api/transactions".
app.include_router(transaction.router, prefix="/api/transactions", tags=["Transactions"])
# Include the users router under the prefix "/api/users".
app.include_router(user.router, prefix="/api/users", tags=["Users"])
# Include the accounts router under the prefix "/api/accounts".
app.include_router(account.router, prefix="/api/accounts", tags=["Accounts"])

# --- Define Basic Routes ---

@app.get("/protected")
def read_protected_route(current_user: str = Depends(get_current_user)):
    """
    A protected route that requires JWT authentication.

    Args:
        current_user (str): The username extracted from a valid JWT token.

    Returns:
        dict: A message confirming access.
    """
    return {"message": f"Hello, {current_user}. You have access to this route!"}

@app.get("/")
def read_root():
    """
    A basic root route to verify that the API is running.

    Returns:
        dict: A welcome message.
    """
    return {"message": "Welcome to BitcoinTX"}

# --- Placeholders for Future Enhancements ---

# Placeholder for integrating bcrypt for password hashing.
# Placeholder for additional error handling and logging middleware.

# --- Testing and Execution Setup ---
# This block ensures that when the module is run directly, the PYTHONPATH is properly set,
# which can help during testing with pytest or similar tools.
if __name__ == "__main__":
    import sys
    sys.path.append(os.getenv("PYTHONPATH", "."))