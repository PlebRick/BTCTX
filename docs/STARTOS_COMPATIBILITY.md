# BTCTX Docker Compatibility Requirements for StartOS Packaging

> **CRITICAL:** This document defines requirements that MUST be maintained for compatibility with the [BTCTX-StartOS](https://github.com/PlebRick/BTCTX-StartOS) wrapper repository.

**Last Updated:** 2025-01-10

---

## Overview

The BTCTX application is packaged for StartOS using a separate wrapper repository (BTCTX-StartOS). The wrapper pulls the Docker image `b1ackswan/btctx:latest` and runs it on StartOS. Any changes to the BTCTX Dockerfile or application structure must maintain compatibility with this packaging system.

---

## Critical Compatibility Requirements

### 1. Docker Image Tag

The StartOS wrapper references:

```typescript
dockerTag: 'b1ackswan/btctx:latest'
```

**Do:**
- Continue publishing to `b1ackswan/btctx:latest`
- Use semantic versioning for additional tags if needed

**Do NOT:**
- Change the image name or registry without coordinating with the wrapper repo
- Remove the `latest` tag

---

### 2. Architecture (Multi-Arch Required)

The wrapper supports both architectures:
- `linux/arm64` (aarch64) - ARM devices like Raspberry Pi, Apple Silicon
- `linux/amd64` (x86_64) - Intel/AMD servers and desktops

The wrapper manifest is configured as:

```typescript
images: {
  main: {
    source: {
      dockerTag: 'b1ackswan/btctx:latest',
    },
    arch: ['aarch64', 'x86_64'],
  },
},
hardwareRequirements: {
  arch: ['aarch64', 'x86_64'],
},
```

**Build command for multi-arch:**

```bash
# Create builder (one-time setup)
docker buildx create --name multiarch --use

# Build and push multi-arch image
docker buildx build --platform linux/amd64,linux/arm64 \
  -t b1ackswan/btctx:latest \
  --push .
```

**Do:**
- Build for both `linux/amd64` and `linux/arm64`
- Use multi-arch compatible base images (e.g., `python:3.x-slim`)
- Test on both architectures before pushing
- Use `docker buildx` for all builds

**Do NOT:**
- Build for only one architecture
- Use architecture-specific base images
- Include architecture-specific binaries without multi-arch handling
- Use base images that don't support both platforms

---

### 3. Application Entry Point

The StartOS wrapper starts the application with:

```typescript
command: ['uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '80']
```

**Do:**
- Keep FastAPI app at `backend.main:app`
- Ensure uvicorn is installed in the image
- Application must be able to bind to port 80

**Do NOT:**
- Move the FastAPI app entry point without updating the wrapper
- Remove uvicorn from dependencies
- Hardcode a different port in the application

---

### 4. Port Configuration

The wrapper exposes port 80 for the web UI:

```typescript
export const uiPort = 80
```

**Do:**
- Serve both the React frontend and FastAPI backend on port 80
- Use FastAPI's static file mounting for the frontend

**Do NOT:**
- Require multiple ports (e.g., separate frontend/backend ports)
- Use a port other than 80 without coordinating with wrapper

---

### 5. Data Persistence

The wrapper mounts a volume at `/data`:

```typescript
mounts.mountVolume({
  volumeId: 'main',
  subpath: null,
  mountpoint: '/data',
  readonly: false,
})
```

**Do:**
- Store the SQLite database in `/data`
- Store any persistent configuration in `/data`
- Use environment variables or auto-detection for the data path
- Default to `/data` when running in production/Docker

**Do NOT:**
- Hardcode paths outside `/data` for persistent storage
- Store important data in the container filesystem (it's ephemeral)
- Require manual creation of subdirectories (create them programmatically)

---

### 6. Environment

The container runs as a subcontainer in StartOS with:
- No special environment variables injected
- Standard Linux environment
- Network access available

**Do:**
- Use sensible defaults that work without configuration
- Support running without any environment variables set

**Do NOT:**
- Require mandatory environment variables for basic operation
- Depend on external services for core functionality

---

## Dockerfile Best Practices

### Required Elements

```dockerfile
# Must use multi-arch compatible base image
FROM python:3.x-slim

# Must have uvicorn installed
RUN pip install uvicorn

# Application at backend/main.py with FastAPI app
COPY backend/ /app/backend/

# Must be able to run on port 80
EXPOSE 80

# Data directory should exist
RUN mkdir -p /data
```

### Recommended Structure

```
/app
├── backend/
│   ├── main.py          # FastAPI app = FastAPI()
│   └── ...
├── static/              # Built React frontend (served by FastAPI)
└── /data                # Mounted volume for persistence
    └── btctx.db         # SQLite database
```

---

## Health Check

The wrapper checks if port 80 is listening to determine service health:

```typescript
sdk.healthCheck.checkPortListening(effects, 80, {
  successMessage: 'BitcoinTX is ready',
  errorMessage: 'BitcoinTX is not responding',
})
```

**Do:**
- Start listening on port 80 promptly
- Return HTTP responses once ready

**Do NOT:**
- Have long startup delays before binding to port
- Bind to port before the application is ready to serve

---

## Testing Compatibility

Before pushing changes, verify:

1. **Image builds for both architectures:**
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 \
     -t b1ackswan/btctx:latest .
   ```

2. **Application starts correctly:**
   ```bash
   docker run -p 80:80 -v $(pwd)/data:/data b1ackswan/btctx:latest \
     uvicorn backend.main:app --host 0.0.0.0 --port 80
   ```

3. **Data persists in /data:**
   ```bash
   # Create some data, restart container, verify data exists
   ```

---

## Breaking Changes

If you need to make breaking changes to any of the above, coordinate with the wrapper repository:

- **Wrapper repo:** https://github.com/PlebRick/BTCTX-StartOS
- **Manifest file:** `startos/manifest.ts`
- **Daemon config:** `startos/procedures/main.ts`
- **Interface config:** `startos/procedures/interfaces.ts`

---

## Summary Checklist

| Requirement | Value |
|-------------|-------|
| Docker image | `b1ackswan/btctx:latest` |
| Architectures | `linux/amd64`, `linux/arm64` |
| Entry point | `backend.main:app` |
| Port | 80 |
| Data volume | `/data` |
| Uvicorn | Installed |
| Mandatory env vars | None |
| Container count | Single |

---

## Coordination Workflow

When making changes:

1. Update Dockerfile in BTCTX-org
2. Build and push multi-arch image:
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 \
     -t b1ackswan/btctx:latest --push .
   ```
3. Notify wrapper repo if any breaking changes
4. Wrapper repo rebuilds: `make clean && make`
5. Test sideload to StartOS
