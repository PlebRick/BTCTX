# -------------------------
# Stage 1: Build the Vite frontend
# -------------------------
    FROM node:18-alpine AS build-frontend

    WORKDIR /app/frontend
    
    # Install dependencies
    COPY frontend/package*.json ./
    RUN npm install
    
    # Copy the rest of the frontend source
    COPY frontend/ ./
    RUN npm run build
    
    # -------------------------
    # Stage 2: Build & run the Python/FastAPI backend
    # -------------------------
    FROM python:3.11-slim AS final
    
    WORKDIR /app
    
    # Install Python dependencies
    COPY backend/requirements.txt ./backend/
    RUN pip install --no-cache-dir -r backend/requirements.txt
    
    # Copy backend code
    COPY backend/ ./backend/
    
    # Copy frontend build from first stage into the backend
    COPY --from=build-frontend /app/frontend/dist ./frontend/dist
    
    # Expose port 80 (or 8000 if needed)
    EXPOSE 80
    
    # Start FastAPI with Uvicorn
    CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
    