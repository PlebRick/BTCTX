FROM debian:bookworm-slim AS builder

# frontend build
WORKDIR /frontend
COPY ./frontend .
RUN npm ci
RUN npm run build

# build backend
WORKDIR /backend
COPY ./backend .
# build step for backend
# RUN uvicorn backend.main:app

FROM debian:bookworm-slim AS final

COPY --from=builder /frontend/dist ./ 