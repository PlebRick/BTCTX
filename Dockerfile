# Stage 1: Build the Vite frontend
FROM node:18-alpine AS build-frontend

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm install

# Copy the rest of the frontend source
COPY frontend/ ./

# Build the frontend (outputs to dist/)
RUN npm run build

# Stage 2: Set up the FastAPI backend
FROM python:3.11-slim AS final

WORKDIR /app

# Install pipenv for dependency management
RUN pip install pipenv

# Copy backend Pipfile and Pipfile.lock
COPY backend/Pipfile backend/Pipfile.lock ./backend/

# Generate requirements.txt from Pipfile and install dependencies
RUN cd backend && pipenv lock -r > requirements.txt && cd .. && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend static files from the first stage
COPY --from=build-frontend /app/frontend/dist ./frontend/dist

# Expose port 80 for the application
EXPOSE 80

# Command to run the FastAPI application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]