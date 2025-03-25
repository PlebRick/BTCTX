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
    # Stage 2: Python/FastAPI backend + Ghostscript
    # -------------------------
    FROM python:3.11-slim AS final
    
    WORKDIR /app
    
    # 1) Install system packages, including Ghostscript
    RUN apt-get update && apt-get install -y --no-install-recommends \
        ghostscript \
      && rm -rf /var/lib/apt/lists/*
    
    # 2) Install Python dependencies
    COPY backend/requirements.txt ./backend/
    RUN pip install --no-cache-dir -r backend/requirements.txt
    
    # 3) Copy backend code
    COPY backend/ ./backend/
    
    # 4) Copy frontend build from first stage
    COPY --from=build-frontend /app/frontend/dist ./frontend/dist
    
    # 5) Expose and run
    EXPOSE 80
    CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
    