# -------------------------
# Stage 1: Build the Vite frontend
# -------------------------
FROM node:18-alpine AS build-frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build


# -------------------------
# Stage 2: Python/FastAPI backend + pdftk
# -------------------------
FROM python:3.11-slim AS final

WORKDIR /app

# 1) Install pdftk instead of ghostscript
RUN apt-get update && apt-get install -y --no-install-recommends \
    pdftk \
  && rm -rf /var/lib/apt/lists/*

# 2) Install Python deps
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 3) Copy backend source
COPY backend/ ./backend/

# 4) Copy frontend build
COPY --from=build-frontend /app/frontend/dist ./frontend/dist

# 5) Expose and run
EXPOSE 80
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
