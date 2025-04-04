# -------------------------
#    Stage 1: Frontend
# -------------------------
  FROM node:18-slim AS frontend-builder

  # Create and move into /app/frontend
  WORKDIR /app/frontend
  
  # Copy package files and install (includes devDependencies for build)
  COPY frontend/package*.json ./
  RUN npm ci
  
  # Copy the rest of your frontend source
  COPY frontend/. .
  
  # Build the React app into frontend/dist
  RUN npm run build
  
  
  # -------------------------
  #    Stage 2: Backend
  # -------------------------
  FROM python:3.11-slim AS backend
  
  # Avoid caching pip packages
  ENV PIP_NO_CACHE_DIR=1
  # Ensures stdout/stderr is unbuffered, so logs appear immediately
  ENV PYTHONUNBUFFERED=1
  # Give the app a default DB path in /data for persistence
  # (You can override this at runtime if StartOS or Docker sets DATABASE_FILE)
  ENV DATABASE_FILE=/data/bitcoin_tracker.db
  
  # Install system-level dependencies (pdftk, etc.)
  RUN apt-get update && apt-get install -y --no-install-recommends \
      pdftk \
   && apt-get clean \
   && rm -rf /var/lib/apt/lists/*
  
  # Create a directory for the backend code
  WORKDIR /app
  
  # Copy your production Python requirements
  COPY backend/requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  
  # Copy the backend source code and the built frontend files
  COPY backend/. ./backend
  COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
  
  # Create non-root user and group for security
  RUN groupadd -r app && useradd -r -g app app && \
      mkdir -p /data && chown -R app:app /app /data
  
  # Switch to that user
  USER app
  
  # Expose port 80 for StartOS to map
  EXPOSE 80
  
  # Final startup command: run FastAPI via Uvicorn
  CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
  