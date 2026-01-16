# macOS Desktop App Build Guide

> Complete documentation for building BitcoinTX as a native macOS application.

**Version:** 0.6.0
**Last Updated:** 2025-01-17
**Branch:** `feature/macos-desktop`

---

## Overview

BitcoinTX can be packaged as a standalone macOS desktop application using **PyInstaller** and **pywebview**. The app bundles the entire FastAPI backend and React frontend into a single `.app` bundle that runs locally on the user's Mac.

### Architecture

```
BitcoinTX.app (Launch)
        │
        ▼
   entrypoint.py
        │
        ├──► Start Uvicorn server (daemon thread)
        │         │
        │         ▼
        │    FastAPI backend (127.0.0.1:{random_port})
        │         │
        │         ▼
        │    SQLite database
        │    (~Library/Application Support/BitcoinTX/btctx.db)
        │
        └──► Create pywebview window
                  │
                  ▼
             Embedded WebKit browser
             pointing to localhost backend
```

### Key Features

- **Self-contained**: No Python installation required for end users
- **Data persistence**: Database stored in macOS Application Support folder
- **Native feel**: Runs as a proper macOS app with dock icon
- **Dark mode**: Full dark mode support
- **Portable**: Single `.app` bundle (~61MB)

---

## Directory Structure

All desktop-related files are in the `/desktop` directory:

```
desktop/
├── entrypoint.py       # Main launcher script
├── BitcoinTX.spec      # PyInstaller configuration
├── build-mac.sh        # Automated build script
├── requirements.txt    # Desktop-specific dependencies
├── README.md           # User-facing readme
├── resources/          # App resources (icons, etc.)
│   └── icon.icns       # App icon (optional)
├── build/              # PyInstaller work directory (gitignored)
├── dist/               # Built app output (gitignored)
│   └── BitcoinTX.app   # The final macOS application
└── .venv/              # Build virtual environment (gitignored)
```

---

## Prerequisites

### For Building

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.10+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| npm | (comes with Node) | `npm --version` |

### For End Users (Optional)

| Requirement | Purpose | Install Command |
|-------------|---------|-----------------|
| pdftk-java | IRS form generation | `brew install pdftk-java` |

> **Note:** The app will work without pdftk, but IRS Form 8949 and Schedule D generation will be disabled. A warning dialog appears at startup if pdftk is missing.

---

## Building the App

### Quick Build

```bash
cd desktop
./build-mac.sh
```

The script will:
1. Check prerequisites (Python 3.10+, Node.js 18+)
2. Create a Python virtual environment
3. Install all dependencies
4. Build the React frontend
5. Run PyInstaller to create the app bundle

### Manual Build Steps

If you need more control:

```bash
cd desktop

# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -r ../backend/requirements.txt

# 3. Build frontend
cd ../frontend
npm install
npm run build
cd ../desktop

# 4. Run PyInstaller
pyinstaller --clean --noconfirm BitcoinTX.spec
```

### Build Output

After a successful build:
- **App location:** `desktop/dist/BitcoinTX.app`
- **Size:** ~61MB
- **Test:** `open dist/BitcoinTX.app`

---

## Creating a DMG for Distribution

To create a distributable disk image:

```bash
# Simple DMG
hdiutil create -volname "BitcoinTX" -srcfolder dist/BitcoinTX.app \
  -ov -format UDZO dist/BitcoinTX.dmg

# Or use create-dmg for a prettier result
brew install create-dmg
create-dmg \
  --volname "BitcoinTX" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "BitcoinTX.app" 150 190 \
  --app-drop-link 450 190 \
  dist/BitcoinTX.dmg \
  dist/BitcoinTX.app
```

---

## Technical Details

### entrypoint.py

The main launcher script (`desktop/entrypoint.py`) handles:

1. **Resource Path Resolution**
   ```python
   def get_resource_path(relative_path):
       # Handles both development and PyInstaller bundle paths
       if hasattr(sys, '_MEIPASS'):
           return os.path.join(sys._MEIPASS, relative_path)
       return os.path.join(os.path.dirname(__file__), '..', relative_path)
   ```

2. **Data Directory Setup**
   ```python
   def get_application_support_dir():
       # Returns ~/Library/Application Support/BitcoinTX/
       home = os.path.expanduser('~')
       return os.path.join(home, 'Library', 'Application Support', 'BitcoinTX')
   ```

3. **Dynamic Port Allocation**
   ```python
   def find_free_port():
       # Finds an available port for the backend
       with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
           s.bind(('', 0))
           return s.getsockname()[1]
   ```

4. **Backend Startup with Health Check**
   - Starts Uvicorn in a daemon thread
   - Polls `/api/health` with exponential backoff (0.1s → 1s)
   - Times out after 30 seconds

5. **pywebview Window**
   ```python
   webview.create_window(
       'BitcoinTX',
       url,
       width=1280,
       height=800,
       min_size=(800, 600),
       resizable=True
   )
   ```

### BitcoinTX.spec (PyInstaller Config)

Key configuration sections:

**Hidden Imports** - Required for dynamic imports:
```python
hiddenimports = [
    'uvicorn.logging', 'uvicorn.loops', 'uvicorn.protocols',
    'sqlalchemy.dialects.sqlite',
    'pydantic', 'pydantic_core',
    'backend.routers.*', 'backend.services.*', 'backend.models.*',
    # ... many more
]
```

**Data Collection** - Bundles these directories:
```python
datas = [
    ('../backend', 'backend'),           # Entire backend
    ('../frontend/dist', 'frontend/dist'), # Built frontend
]
```

**Exclusions** - Reduces bundle size:
```python
excludes = ['pytest', 'tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas']
```

**macOS Bundle Configuration**:
```python
app = BUNDLE(
    name='BitcoinTX.app',
    bundle_identifier='org.bitcointx.desktop',
    info_plist={
        'CFBundleVersion': '0.6.0',
        'LSMinimumSystemVersion': '10.15',
        'NSRequiresAquaSystemAppearance': False,  # Dark mode support
    }
)
```

### Backend Integration

The backend (`backend/main.py`) was modified to support bundled operation:

```python
# Support for bundled frontend path
frontend_dist = os.environ.get('BTCTX_FRONTEND_DIST')
if frontend_dist is None:
    frontend_dist = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
```

Environment variables set by entrypoint.py:
- `DATABASE_FILE`: Path to SQLite database in Application Support
- `SECRET_KEY`: Desktop app secret key
- `BTCTX_FRONTEND_DIST`: Path to bundled frontend dist

---

## Data Storage

### Database Location

User data is stored in the standard macOS Application Support folder:

```
~/Library/Application Support/BitcoinTX/
└── btctx.db    # SQLite database
```

### Accessing User Data

```bash
# Open data folder in Finder
open ~/Library/Application\ Support/BitcoinTX/

# View database
sqlite3 ~/Library/Application\ Support/BitcoinTX/btctx.db
```

### Backup

To backup user data, copy the entire `BitcoinTX` folder from Application Support.

---

## Troubleshooting

### App Won't Open (Gatekeeper)

macOS may block unsigned apps:

```bash
# Remove quarantine attribute
xattr -cr /path/to/BitcoinTX.app

# Or allow in System Preferences:
# System Preferences → Security & Privacy → General → "Open Anyway"
```

### pdftk Warning at Startup

If you see "pdftk not found" warning:

```bash
# Install pdftk via Homebrew
brew install pdftk-java
```

### App Crashes on Launch

1. Check Console.app for crash logs
2. Run from terminal to see output:
   ```bash
   /path/to/BitcoinTX.app/Contents/MacOS/BitcoinTX
   ```

### Backend Port Conflicts

The app automatically finds a free port. If issues persist:
1. Check for zombie processes: `ps aux | grep uvicorn`
2. Kill any stale processes: `pkill -f uvicorn`

### Blank Window

If the window is blank:
1. Wait for backend to start (can take a few seconds)
2. Check if backend is running: `curl http://127.0.0.1:{port}/api/health`

---

## Creating an App Icon

If you don't have `resources/icon.icns`:

1. Create a 1024x1024 PNG icon
2. Convert to .icns:
   ```bash
   mkdir icon.iconset
   sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
   sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
   sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
   sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
   sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
   sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
   sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
   sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
   sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
   sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png
   iconutil -c icns icon.iconset
   mv icon.icns desktop/resources/
   ```

---

## Development Notes

### Making Changes

1. **Backend changes**: No special handling needed - backend is bundled as-is
2. **Frontend changes**: Run `npm run build` before rebuilding the app
3. **Desktop changes**: Edit files in `desktop/`, then rebuild

### Testing During Development

Run the entrypoint directly without building:

```bash
cd desktop
source .venv/bin/activate
python entrypoint.py
```

### Debugging PyInstaller Issues

```bash
# Build with debug output
pyinstaller --debug=all BitcoinTX.spec

# Check for missing imports
pyinstaller --debug=imports BitcoinTX.spec
```

### Adding New Dependencies

If you add new Python packages to the backend:

1. Add to `backend/requirements.txt`
2. Check if PyInstaller needs `hiddenimports` in `BitcoinTX.spec`
3. Rebuild and test

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.6.0 | 2025-01-17 | Initial macOS desktop app release |

---

## Related Documentation

- [Main README](../README.md) - Project overview
- [CLAUDE.md](../CLAUDE.md) - AI assistant context
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [desktop/README.md](../desktop/README.md) - Quick start guide
