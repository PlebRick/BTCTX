# FILE: backend/services/reports/pdftk_path.py
"""
Centralized pdftk path resolution for macOS desktop app compatibility.

PyInstaller bundles don't inherit the system PATH, so we need to check
known Homebrew installation locations in addition to shutil.which().
"""

import os
import shutil
from typing import Optional

# Known pdftk installation paths on macOS
PDFTK_SEARCH_PATHS = [
    "/opt/homebrew/bin/pdftk",       # Apple Silicon Homebrew
    "/usr/local/bin/pdftk",          # Intel Homebrew
    "/opt/homebrew/bin/pdftk-java",  # pdftk-java wrapper (Apple Silicon)
    "/usr/local/bin/pdftk-java",     # pdftk-java wrapper (Intel)
]

# Cache the resolved path to avoid repeated filesystem checks
_cached_pdftk_path: Optional[str] = None


def find_pdftk() -> Optional[str]:
    """
    Find pdftk executable in PATH or known installation locations.

    Returns:
        Full path to pdftk executable, or None if not found.
    """
    global _cached_pdftk_path

    # Return cached path if available
    if _cached_pdftk_path is not None:
        return _cached_pdftk_path

    # First, check if pdftk is in PATH (works for normal environments)
    path_result = shutil.which("pdftk")
    if path_result:
        _cached_pdftk_path = path_result
        return _cached_pdftk_path

    # Check known Homebrew locations (for PyInstaller bundles)
    for known_path in PDFTK_SEARCH_PATHS:
        if os.path.isfile(known_path) and os.access(known_path, os.X_OK):
            _cached_pdftk_path = known_path
            return _cached_pdftk_path

    return None


def get_pdftk_path() -> str:
    """
    Get the path to pdftk executable.

    Returns:
        Full path to pdftk executable.

    Raises:
        RuntimeError: If pdftk is not found.
    """
    path = find_pdftk()
    if path is None:
        raise RuntimeError(
            "pdftk is not installed or not found. "
            "Install with: brew install pdftk-java (macOS) or apt-get install pdftk (Linux)"
        )
    return path


def is_pdftk_available() -> bool:
    """
    Check if pdftk is available on the system.

    Returns:
        True if pdftk is found, False otherwise.
    """
    return find_pdftk() is not None


def clear_cache():
    """Clear the cached pdftk path (useful for testing)."""
    global _cached_pdftk_path
    _cached_pdftk_path = None
