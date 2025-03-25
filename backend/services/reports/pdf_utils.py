# FILE: backend/services/reports/pdf_utils.py

import subprocess
import uuid
import os

def flatten_pdf_with_ghostscript(pdf_bytes: bytes) -> bytes:
    """
    Takes in-memory PDF bytes, writes them to a temp file,
    calls Ghostscript to flatten, and returns flattened PDF bytes.
    """
    random_id = uuid.uuid4().hex
    filled_path = f"/tmp/filled_{random_id}.pdf"
    flattened_path = f"/tmp/flattened_{random_id}.pdf"

    # Write the filled PDF to disk
    with open(filled_path, "wb") as f:
        f.write(pdf_bytes)

    try:
        # Call Ghostscript to flatten
        subprocess.run([
            "gs",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",
            f"-sOutputFile={flattened_path}",
            filled_path
        ], check=True)

        # Read the flattened PDF
        with open(flattened_path, "rb") as f:
            return f.read()
    finally:
        # Always delete temp files
        if os.path.exists(filled_path):
            os.remove(filled_path)
        if os.path.exists(flattened_path):
            os.remove(flattened_path)
