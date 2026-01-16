# BitcoinTX Desktop App (macOS)

This directory contains the build configuration for the macOS desktop application.

## Prerequisites

1. **Python 3.10+** with pip (install with `brew install python@3.11`)
2. **Node.js 18+** with npm
3. **pdftk-java** (optional, for IRS form generation):
   ```bash
   brew install pdftk-java
   ```

## Building

```bash
# From project root
./desktop/build-mac.sh
```

The build script will:
1. Create a Python virtual environment
2. Install all dependencies
3. Build the React frontend
4. Bundle everything with PyInstaller
5. Create `BitcoinTX.app` in `desktop/dist/`

## Testing

```bash
open desktop/dist/BitcoinTX.app
```

## Creating a DMG for Distribution

```bash
hdiutil create -volname BitcoinTX \
  -srcfolder desktop/dist/BitcoinTX.app \
  -ov -format UDZO \
  BitcoinTX.dmg
```

## Architecture

```
BitcoinTX.app/
├── Contents/
│   ├── MacOS/
│   │   └── BitcoinTX        # Main executable
│   ├── Resources/
│   │   ├── icon.icns        # App icon
│   │   ├── backend/         # Python backend
│   │   ├── frontend/dist/   # React build
│   │   └── ...              # Python dependencies
│   └── Info.plist           # App metadata
```

## Data Storage

User data is stored in:
```
~/Library/Application Support/BitcoinTX/
└── btctx.db                  # SQLite database
```

## Troubleshooting

### "pdftk not found" warning
Install pdftk-java: `brew install pdftk-java`

### App won't open (macOS Gatekeeper)
Right-click > Open, or: `xattr -cr desktop/dist/BitcoinTX.app`

### Backend fails to start
Check Console.app for BitcoinTX logs.

## Creating the App Icon

To create `icon.icns` from the SVG logo:

1. Export `frontend/public/icon.svg` to PNG at multiple sizes (16, 32, 128, 256, 512, 1024)
2. Create an iconset:
   ```bash
   mkdir BitcoinTX.iconset
   # Add PNGs named: icon_16x16.png, icon_32x32.png, etc.
   # Also add @2x versions: icon_16x16@2x.png, etc.
   iconutil -c icns BitcoinTX.iconset -o resources/icon.icns
   ```

Or use a tool like Image2Icon (free on App Store).

## Files

| File | Purpose |
|------|---------|
| `entrypoint.py` | Main launcher - starts Uvicorn and pywebview |
| `BitcoinTX.spec` | PyInstaller configuration |
| `build-mac.sh` | Build automation script |
| `requirements.txt` | Desktop-specific Python packages |
| `resources/icon.icns` | macOS app icon |
