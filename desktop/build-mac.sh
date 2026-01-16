#!/bin/bash
#
# Build script for BitcoinTX macOS Desktop App
#
# Prerequisites:
#   - Python 3.10+ with pip (brew install python@3.11)
#   - Node.js 18+ with npm
#
# Usage:
#   ./desktop/build-mac.sh
#

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo ""
echo "========================================"
echo "  BitcoinTX macOS Desktop Build"
echo "========================================"
echo ""

cd "$PROJECT_ROOT"

# Step 1: Check prerequisites
echo "[1/6] Checking prerequisites..."

if ! command -v npm &> /dev/null; then
    echo "ERROR: npm not found"
    exit 1
fi

# Find Python 3.10+
PYTHON_CMD=""
for py in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$py" &> /dev/null; then
        PY_VER=$("$py" -c "import sys; print(sys.version_info.minor)")
        PY_MAJOR=$("$py" -c "import sys; print(sys.version_info.major)")
        if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_VER" -ge 10 ]; then
            PYTHON_CMD="$py"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "ERROR: Python 3.10+ is required but not found"
    echo ""
    echo "Install with Homebrew:"
    echo "  brew install python@3.11"
    echo ""
    echo "Then run this script again."
    exit 1
fi

PYTHON_VERSION=$("$PYTHON_CMD" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python: $PYTHON_VERSION ($PYTHON_CMD)"

NODE_VERSION=$(node --version)
echo "  Node: $NODE_VERSION"

# Step 2: Create/update virtual environment
echo ""
echo "[2/6] Setting up Python virtual environment..."

VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    echo "  Created virtual environment"
else
    echo "  Using existing virtual environment"
fi

source "$VENV_DIR/bin/activate"

# Install dependencies
pip install --upgrade pip wheel > /dev/null 2>&1
pip install -r "$PROJECT_ROOT/backend/requirements.txt" > /dev/null 2>&1
pip install -r "$SCRIPT_DIR/requirements.txt" > /dev/null 2>&1
echo "  Dependencies installed"

# Step 3: Build frontend
echo ""
echo "[3/6] Building frontend..."

cd "$PROJECT_ROOT/frontend"
npm ci --silent 2>/dev/null || npm ci
npm run build
cd "$PROJECT_ROOT"
echo "  Frontend built to frontend/dist/"

# Step 4: Verify resources
echo ""
echo "[4/6] Verifying resources..."

if [ ! -f "$SCRIPT_DIR/resources/icon.icns" ]; then
    echo "  WARNING: icon.icns not found at $SCRIPT_DIR/resources/icon.icns"
    echo "  The app will be built without a custom icon."
    echo "  To add an icon, convert logo.svg to icon.icns and place it in desktop/resources/"
fi

if [ ! -d "$PROJECT_ROOT/backend/assets/irs_templates" ]; then
    echo "  ERROR: IRS templates not found at backend/assets/irs_templates/"
    exit 1
fi

echo "  Resources verified"

# Step 5: Run PyInstaller
echo ""
echo "[5/6] Building application bundle..."

cd "$SCRIPT_DIR"
pyinstaller --clean --noconfirm BitcoinTX.spec

# Step 6: Report results
echo ""
echo "[6/6] Build complete!"

APP_PATH="$SCRIPT_DIR/dist/BitcoinTX.app"
if [ -d "$APP_PATH" ]; then
    APP_SIZE=$(du -sh "$APP_PATH" | cut -f1)
    echo ""
    echo "  Application: $APP_PATH"
    echo "  Size: $APP_SIZE"
    echo ""
    echo "To test:"
    echo "  open $APP_PATH"
    echo ""
    echo "To create DMG for distribution:"
    echo "  hdiutil create -volname BitcoinTX -srcfolder $APP_PATH -ov -format UDZO BitcoinTX.dmg"
else
    echo "  ERROR: Application bundle not created"
    deactivate
    exit 1
fi

# Deactivate virtual environment
deactivate
