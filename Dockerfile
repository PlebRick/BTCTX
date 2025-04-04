# -------------------------
# Stage 1: Build Vite Frontend
# -------------------------
  FROM node:18-alpine AS frontend-builder

  WORKDIR /frontend
  
  # Copy and install frontend deps
  COPY frontend/package*.json ./
  RUN npm install
  
  # Copy rest of frontend and build
  COPY frontend/ ./
  RUN npm run build
  
  # -------------------------
  # Stage 2: Final Python + FastAPI + pdftk image
  # -------------------------
  FROM python:3.11-slim AS final
  
  WORKDIR /app
  
  # Install system-level tools like pdftk
  RUN apt-get update && apt-get install -y --no-install-recommends \
      pdftk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
  
  # Copy and install backend dependencies
  COPY backend/requirements.txt ./backend/requirements.txt
  RUN pip install --no-cache-dir -r backend/requirements.txt
  
  # Copy backend code
  COPY backend/ ./backend/
  
  # Copy built frontend files from first stage
  COPY --from=frontend-builder /frontend/dist ./frontend/dist
  
  # Set environment for production
  ENV PYTHONUNBUFFERED=1
  
  # Expose default port
  EXPOSE 80
  
  # Start FastAPI app with Uvicorn, serving the frontend from backend.main
  CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
  