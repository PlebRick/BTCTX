# FILE: backend/services/reports/pdf_utils.py

import subprocess
import tempfile
import os

from backend.services.reports.pdftk_path import get_pdftk_path

# -----------------------------------------------------------------------------
# (DEPRECATED) Old Ghostscript flattening method
# -----------------------------------------------------------------------------
# def flatten_pdf_with_ghostscript(pdf_bytes: bytes) -> bytes:
#     """
#     (DEPRECATED) Flatten PDF via Ghostscript.
#     No longer used now that we rely on pdftk for XFA forms.
#     """
#     ...


def flatten_pdf_with_pdftk(pdf_bytes: bytes) -> bytes:
    """
    Flattens a PDF in memory using pdftk. This approach replaces
    the old Ghostscript flattening. Suitable for final flatten
    if needed after forms have been filled.

    Steps:
      1) Write the PDF bytes to a temp file.
      2) Call 'pdftk input.pdf output output.pdf flatten'.
      3) Return the flattened PDF as bytes.
      4) Cleanup is automatic via TemporaryDirectory.
    """
    # Get the resolved pdftk path (handles PyInstaller bundles)
    pdftk_bin = get_pdftk_path()

    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdf = os.path.join(tmpdir, "original.pdf")
        flattened_pdf = os.path.join(tmpdir, "flattened.pdf")

        # 1) Write the original PDF bytes to disk
        with open(input_pdf, "wb") as f:
            f.write(pdf_bytes)

        # 2) Run pdftk to flatten
        cmd = [pdftk_bin, input_pdf, "output", flattened_pdf, "flatten"]
        subprocess.run(cmd, check=True)

        # 3) Read the flattened output
        with open(flattened_pdf, "rb") as f:
            final_bytes = f.read()

        return final_bytes
