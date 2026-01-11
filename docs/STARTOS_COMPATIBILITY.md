# StartOS Container Architecture & Data Persistence

> **CRITICAL:** This document explains how BitcoinTX runs in Docker and StartOS containers. All developers (human or AI) MUST understand this before modifying database paths, file storage, or environment handling.

**Last Updated:** 2025-01-10

---

## Table of Contents

1. [Overview: Two Repositories](#overview-two-repositories)
2. [How Data Persistence Works](#how-data-persistence-works)
3. [The DATABASE_FILE Environment Variable](#the-database_file-environment-variable)
4. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
5. [Docker Image Requirements](#docker-image-requirements)
6. [StartOS Wrapper Configuration](#startos-wrapper-configuration)
7. [Testing Checklist](#testing-checklist)

---

## Overview: Two Repositories

BitcoinTX uses a **two-repository architecture** for StartOS deployment:

```
┌─────────────────────────────────────────────────────────────────┐
│  BTCTX-org (Main Application)                                   │
│  https://github.com/BitcoinTX-org/BTCTX-org                     │
│                                                                 │
│  Contains:                                                      │
│  - Python/FastAPI backend                                       │
│  - React frontend                                               │
│  - Dockerfile                                                   │
│  - All application logic                                        │
│                                                                 │
│  Builds → Docker Hub: b1ackswan/btctx:latest                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    (Docker image is pulled by)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  btctx-startos (StartOS Wrapper)                                │
│  https://github.com/PlebRick/BTCTX-StartOS                      │
│                                                                 │
│  Contains:                                                      │
│  - manifest.ts (package metadata, volume definitions)           │
│  - procedures/main.ts (container startup, env vars)             │
│  - procedures/backups.ts (backup/restore of volumes)            │
│  - No application code - just orchestration                     │
│                                                                 │
│  Builds → .s9pk package for StartOS                             │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight:** The main repo builds a Docker image. The wrapper repo tells StartOS how to run that image, including:
- What volumes to mount
- What environment variables to set
- How to do health checks
- How to backup/restore data

---

## How Data Persistence Works

### The Problem with Containers

Docker containers are **ephemeral** - when the container is removed, all data inside it is lost. This includes:
- The SQLite database
- User settings
- Any files written during runtime

### The Solution: Volume Mounts

StartOS solves this by mounting a **persistent volume** at `/data`:

```typescript
// From btctx-startos/startos/procedures/main.ts
const mounts = sdk.Mounts.of().mountVolume({
  volumeId: 'main',           // StartOS manages this volume
  subpath: null,
  mountpoint: '/data',        // Mounted inside container at /data
  readonly: false,
})
```

**What this means:**
- StartOS creates a persistent storage area called `main`
- This storage is mounted at `/data` inside the container
- Files in `/data` survive container restarts and updates
- Files OUTSIDE `/data` are lost when the container restarts

### Visual Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    StartOS Server                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Persistent Storage (survives restarts)                     ││
│  │  Volume: "main"                                             ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │  /data/btctx.db  ← SQLite database lives here          │││
│  │  │  /data/...       ← Any other persistent files          │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └──────────────────────────────────────│─────────────────────┘│
│                                         │ mounted at /data      │
│  ┌──────────────────────────────────────▼─────────────────────┐│
│  │  Docker Container (ephemeral - rebuilt on updates)         ││
│  │                                                            ││
│  │  /app/backend/     ← Application code (read-only)          ││
│  │  /app/frontend/    ← React build (read-only)               ││
│  │  /data/            ← MOUNT POINT for persistent volume     ││
│  │                                                            ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## The DATABASE_FILE Environment Variable

### Why It Exists

The application needs to know where to store the database. Different environments use different paths:

| Environment | Database Path | Who Sets It |
|-------------|---------------|-------------|
| Local development | `backend/bitcoin_tracker.db` | Default in code |
| Docker (standalone) | `/data/btctx.db` | Docker run command |
| StartOS | `/data/btctx.db` | StartOS wrapper |

### How StartOS Sets It

The wrapper passes the environment variable when starting the container:

```typescript
// From btctx-startos/startos/procedures/main.ts
return sdk.Daemons.of(effects).addDaemon('webui', {
  subcontainer,
  exec: {
    command: ['uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '80'],
    env: {
      DATABASE_FILE: '/data/btctx.db',  // ← THIS IS CRITICAL
    },
  },
  // ...
})
```

### How Application Code Must Read It

**CORRECT - Use the environment variable:**

```python
# backend/database.py (correct implementation)
DATABASE_FILE_ENV = os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db")
DATABASE_FILE = (
    DATABASE_FILE_ENV if os.path.isabs(DATABASE_FILE_ENV)
    else os.path.join(PROJECT_ROOT, DATABASE_FILE_ENV)
)
```

```python
# backend/services/backup.py (correct implementation)
_DATABASE_FILE_ENV = os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db")
_DATABASE_FILE = (
    _DATABASE_FILE_ENV if os.path.isabs(_DATABASE_FILE_ENV)
    else os.path.join(_PROJECT_ROOT, _DATABASE_FILE_ENV)
)
DB_PATH = Path(_DATABASE_FILE)
```

**WRONG - Hardcoded paths:**

```python
# DO NOT DO THIS - breaks in Docker/StartOS
DB_PATH = Path("backend/bitcoin_tracker.db")  # WRONG!
DB_PATH = Path("/app/backend/bitcoin_tracker.db")  # WRONG!
```

---

## Common Mistakes to Avoid

### Mistake 1: Hardcoded Database Paths

**Bug we fixed on 2025-01-10:** `backup.py` had a hardcoded path that didn't match where StartOS puts the database.

```python
# BEFORE (broken):
DB_PATH = Path("backend/bitcoin_tracker.db")

# AFTER (fixed):
DB_PATH = Path(os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db"))
```

**Result:** Backup/restore was writing to a different file than the app was using.

### Mistake 2: Writing Files Outside /data

```python
# WRONG - file will be lost on container restart
with open("/app/exports/report.pdf", "wb") as f:
    f.write(pdf_data)

# RIGHT - temporary files are OK, or use /data for persistence
with tempfile.NamedTemporaryFile() as f:
    f.write(pdf_data)
```

### Mistake 3: Assuming Container Filesystem Persists

```python
# WRONG - assuming previous state exists
if os.path.exists("/app/cache/prices.json"):
    load_cached_prices()

# RIGHT - use /data or fetch fresh data
if os.path.exists("/data/cache/prices.json"):
    load_cached_prices()
```

### Mistake 4: Not Testing in Docker

Always test database operations in Docker before pushing:

```bash
# Build and run with the same env var StartOS uses
docker run -p 80:80 \
  -e DATABASE_FILE=/data/btctx.db \
  -v btctx-data:/data \
  b1ackswan/btctx:latest
```

---

## Docker Image Requirements

### Required Elements in Dockerfile

```dockerfile
# Multi-arch compatible base image
FROM python:3.11-slim

# Create /data directory for the volume mount
RUN mkdir -p /data && chmod 777 /data

# Application must handle DATABASE_FILE env var
# (no Dockerfile changes needed - handled in Python code)

# Expose port 80
EXPOSE 80
```

### Build Command (Multi-Arch Required)

```bash
# StartOS runs on ARM64 (Raspberry Pi) and x86_64
docker buildx build --platform linux/amd64,linux/arm64 \
  -t b1ackswan/btctx:latest \
  --push .
```

### Container Filesystem Layout

```
/app/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── database.py          # Reads DATABASE_FILE env var
│   ├── services/
│   │   ├── backup.py        # MUST read DATABASE_FILE env var
│   │   └── ...
│   └── ...
├── frontend/
│   └── dist/                # Built React app
└── /data/                   # VOLUME MOUNT POINT
    └── btctx.db             # SQLite database (persistent)
```

---

## StartOS Wrapper Configuration

### Key Files in btctx-startos Repository

| File | Purpose |
|------|---------|
| `startos/manifest.ts` | Package metadata, volume declarations, architecture |
| `startos/procedures/main.ts` | Container startup, ENV vars, health checks |
| `startos/procedures/backups.ts` | Backup/restore configuration |
| `startos/procedures/interfaces.ts` | Network ports and URLs |
| `startos/procedures/versions/*.ts` | Version migration scripts |
| `startos/procedures/actions/*.ts` | User actions (e.g., reset credentials) |

### Wrapper Actions

The wrapper includes useful StartOS actions:

| Action | Purpose |
|--------|---------|
| `showDefaultCredentials` | Display the default admin/password credentials |
| `resetCredentials` | Reset login to default (recovery if locked out) |

The reset action directly modifies the SQLite database to restore default credentials using bcrypt hashing.

### Volume Declaration (manifest.ts)

```typescript
export const manifest = setupManifest({
  // ...
  volumes: ['main'],  // Declares a volume named "main"
  // ...
})
```

### Volume Mount + Environment (main.ts)

```typescript
// Mount the volume
const mounts = sdk.Mounts.of().mountVolume({
  volumeId: 'main',
  mountpoint: '/data',
  readonly: false,
})

// Pass DATABASE_FILE to the container
return sdk.Daemons.of(effects).addDaemon('webui', {
  exec: {
    command: ['uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '80'],
    env: {
      DATABASE_FILE: '/data/btctx.db',
    },
  },
})
```

### Backup Configuration (backups.ts)

```typescript
// This tells StartOS to backup the entire "main" volume
export const { createBackup, restoreInit } = sdk.setupBackups(
  async ({ effects }) => sdk.Backups.ofVolumes('main'),
)
```

**Note:** This is the StartOS-level backup (backs up the whole volume). The app also has its own encrypted backup feature via `/api/backup/download` which exports just the database with password encryption.

---

## Testing Checklist

Before pushing changes that touch database paths or file storage:

### 1. Verify DATABASE_FILE is Used

```bash
# Inside the container, check the path
docker exec <container> python -c "
from backend.services.backup import DB_PATH
print('backup.py DB_PATH:', DB_PATH)
"
# Should print: /data/btctx.db
```

### 2. Verify Database is in /data

```bash
docker exec <container> ls -la /data/
# Should show: btctx.db
```

### 3. Test Backup/Restore

```bash
# Download backup
curl -X POST http://localhost:8080/api/backup/download \
  -F "password=test123" -o backup.btx

# Restore backup
curl -X POST http://localhost:8080/api/backup/restore \
  -F "password=test123" -F "file=@backup.btx"
# Should return: {"message":"✅ Database successfully restored."}
```

### 4. Test Data Persistence

```bash
# Create data, stop container, restart, verify data exists
docker stop btctx-test
docker start btctx-test
# Check if transactions/data still exist
```

### 5. Build Multi-Arch

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t b1ackswan/btctx:latest --push .
```

---

## Known Issues & TODO

### Wrapper Architecture Declaration

**Issue:** The wrapper's `manifest.ts` currently only declares `aarch64` support, but the Docker image supports both architectures.

```typescript
// CURRENT (wrapper only allows ARM64):
arch: ['aarch64']

// SHOULD BE (to match Docker image):
arch: ['aarch64', 'x86_64']
```

**Impact:** The package won't install on x86_64 StartOS servers even though the Docker image would work.

**Fix location:** `startos/manifest.ts` in the wrapper repo - update both `images.main.arch` and `hardwareRequirements.arch`.

---

## Summary: Critical Rules

1. **All persistent data MUST go in `/data/`** - anything else is lost on restart
2. **Always use `DATABASE_FILE` env var** - never hardcode database paths
3. **Test in Docker before pushing** - local dev doesn't catch these bugs
4. **Build multi-arch images** - StartOS runs on ARM64 and x86_64
5. **Coordinate wrapper updates** - if you change ports, paths, or env vars, update the wrapper repo too

---

## Quick Reference

| What | Value |
|------|-------|
| Docker image | `b1ackswan/btctx:latest` |
| Architectures | `linux/amd64`, `linux/arm64` |
| Entry point | `backend.main:app` |
| Port | 80 |
| Data volume mount | `/data` |
| Database path | `/data/btctx.db` |
| Database env var | `DATABASE_FILE` |
| Main repo | https://github.com/BitcoinTX-org/BTCTX-org |
| Wrapper repo | https://github.com/PlebRick/BTCTX-StartOS |
