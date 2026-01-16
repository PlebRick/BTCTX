#!/usr/bin/env python3
"""
BitcoinTX Desktop Application Entry Point

Starts the FastAPI backend on a free port and opens a pywebview window.
Handles graceful shutdown and data directory management.
"""

import os
import sys
import socket
import threading
import time
import logging
from pathlib import Path

# Setup logging before any other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BitcoinTX")


def get_application_support_dir() -> Path:
    """
    Returns the macOS Application Support directory for BitcoinTX.
    Creates it if it doesn't exist.
    """
    app_support = Path.home() / "Library" / "Application Support" / "BitcoinTX"
    app_support.mkdir(parents=True, exist_ok=True)
    return app_support


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to a resource, works for dev and PyInstaller bundle.
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = Path(__file__).parent.parent
    return base_path / relative_path


def find_free_port() -> int:
    """Find a free port for the backend server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def wait_for_backend(port: int, timeout: float = 30.0) -> bool:
    """
    Wait for the backend to become ready.
    Uses exponential backoff from 0.1s to 1s.
    """
    import urllib.request
    import urllib.error

    url = f"http://127.0.0.1:{port}/api/accounts/"
    start_time = time.time()
    delay = 0.1

    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    logger.info(f"Backend ready on port {port}")
                    return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            pass

        time.sleep(delay)
        delay = min(delay * 2, 1.0)

    logger.error(f"Backend failed to start within {timeout}s")
    return False


def check_pdftk_available() -> bool:
    """Check if pdftk is installed and available."""
    import shutil
    return shutil.which("pdftk") is not None


def run_backend(port: int):
    """Run the FastAPI backend with Uvicorn."""
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )


def main():
    """Main entry point for the desktop application."""
    import webview

    # Set up data directory
    app_support = get_application_support_dir()
    db_path = app_support / "btctx.db"

    # Set environment variables before importing backend
    os.environ["DATABASE_FILE"] = str(db_path)
    os.environ["SECRET_KEY"] = "desktop-app-secret-key-change-in-production"

    # Set frontend path for bundled app
    if getattr(sys, 'frozen', False):
        frontend_dist = get_resource_path("frontend/dist")
        os.environ["BTCTX_FRONTEND_DIST"] = str(frontend_dist)
        logger.info(f"Running from bundle, frontend at: {frontend_dist}")
    else:
        logger.info("Running in development mode")

    # Check pdftk availability
    pdftk_available = check_pdftk_available()
    if not pdftk_available:
        logger.warning("pdftk not found - IRS form generation will be unavailable")

    # Find a free port
    port = find_free_port()
    logger.info(f"Starting backend on port {port}")

    # Start backend in a daemon thread
    backend_thread = threading.Thread(
        target=run_backend,
        args=(port,),
        daemon=True,
        name="BackendThread"
    )
    backend_thread.start()

    # Wait for backend to be ready
    if not wait_for_backend(port):
        logger.error("Failed to start backend")
        sys.exit(1)

    # Create the webview window
    window = webview.create_window(
        title="BitcoinTX",
        url=f"http://127.0.0.1:{port}/",
        width=1280,
        height=800,
        min_size=(800, 600),
        resizable=True,
        confirm_close=False,
    )

    # Show pdftk warning after window loads (if needed)
    def on_loaded():
        if not pdftk_available:
            webview.windows[0].evaluate_js('''
                setTimeout(function() {
                    if (confirm("pdftk is not installed.\\n\\nIRS form generation requires pdftk.\\nInstall with: brew install pdftk-java\\n\\nAll other features will work normally.\\n\\nClick OK to continue.")) {}
                }, 2000);
            ''')

    window.events.loaded += on_loaded

    # Start the webview (blocks until window is closed)
    webview.start(debug=False)

    logger.info("Application closed")


if __name__ == "__main__":
    main()
