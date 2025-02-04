import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from backend.routers import transaction, user, account

# --- Load Environment Variables ---
load_dotenv()

# --- Environment Variables Setup ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bitcoin_tracker.db")
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ALLOWED_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:3000").split(",")

# --- OAuth2 Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# --- Initialize FastAPI App ---
app = FastAPI(
    title="BitcoinTX Portfolio Tracker API",
    description="API for managing Bitcoin transactions, accounts, and portfolio tracking.",
    version="1.0",
    debug=True  # Enable debug mode
)

# --- Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Read allowed origins from .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- JWT Helper Functions ---
def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    
    Args:
        data (dict): Payload data to encode in the token.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str) -> str:
    """
    Verify and decode a JWT access token.
    
    Args:
        token (str): JWT token to verify.

    Returns:
        str: Username from the token's payload if valid.

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

# --- Dependency to Protect Routes ---
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency to retrieve the current user from a valid JWT token.
    
    Args:
        token (str): Bearer token from the request.

    Returns:
        str: Username of the authenticated user.
    """
    return verify_access_token(token)

# --- Include Routers ---
app.include_router(transaction.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(user.router, prefix="/api/users", tags=["Users"])
app.include_router(account.router, prefix="/api/accounts", tags=["Accounts"])

# --- Example Protected Route ---
@app.get("/protected")
def read_protected_route(current_user: str = Depends(get_current_user)):
    """
    Example protected route.
    
    Args:
        current_user (str): Username of the authenticated user.

    Returns:
        dict: Message confirming access.
    """
    return {"message": f"Hello, {current_user}. You have access to this route!"}

# --- Basic Root Route ---
@app.get("/")
def read_root():
    """
    Basic route to confirm the API is running.
    """
    return {"message": "Welcome to BitcoinTX"}

# --- Placeholder for bcrypt Setup ---
# In the future, password hashing and verification will be added with bcrypt.
# For now, we will integrate bcrypt when setting up user authentication details.

# --- Placeholder for Additional Features ---
# Example: Custom error handling middleware
# Example: Logging and monitoring services

# --- Testing Path Setup for pytest ---
# Ensures that PYTHONPATH is correctly set when running tests.
if __name__ == "__main__":
    import sys
    sys.path.append(os.getenv("PYTHONPATH", "."))  # Add the PYTHONPATH from .env for testing