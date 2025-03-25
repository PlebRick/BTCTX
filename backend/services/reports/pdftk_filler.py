# FILE: backend/services/reports/pdftk_filler.py

import subprocess
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


def generate_fdf(field_data: dict) -> str:
    """
    Generates FDF (Forms Data Format) content from a Python dict.
    Each key is a PDF form field name, and each value is the text to insert.
    
    The output is a string representing the entire .fdf file in text form.
    For XFA or standard AcroForm usage with pdftk.
    """
    lines = [
        "%FDF-1.2",
        "1 0 obj << ",
        "/FDF << /Fields ["
    ]
    
    for key, value in field_data.items():
        # Escape parentheses if needed
        escaped_key = key.replace("(", r"\(").replace(")", r"\)")
        escaped_value = value.replace("(", r"\(").replace(")", r"\)")
        lines.append(f"<< /T ({escaped_key}) /V ({escaped_value}) >>")
    
    lines.append("] >> ")
    lines.append(">>")
    lines.append("endobj")
    lines.append("trailer")
    lines.append("<< /Root 1 0 R >>")
    lines.append("%%EOF")
    
    return "\n".join(lines)


def fill_pdf_with_pdftk(template_path: str, field_data: dict, drop_xfa: bool = True) -> bytes:
    """
    Fills a PDF using pdftk and an FDF data dictionary.
    - If drop_xfa=True, we first call 'pdftk template.pdf drop_xfa output no_xfa.pdf'
      to remove any XFA data so the form fields can be standard AcroForm.
    - Then we generate an FDF from field_data.
    - Finally, we run 'pdftk ... fill_form ... flatten' to produce the filled PDF.

    Returns the filled PDF as in-memory bytes.
    Raises subprocess.CalledProcessError if pdftk fails for any reason.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1) Possibly remove XFA
        if drop_xfa:
            no_xfa_path = os.path.join(tmpdir, "no_xfa.pdf")
            cmd_drop = ["pdftk", template_path, "drop_xfa", "output", no_xfa_path]
            subprocess.run(cmd_drop, check=True)
            final_template = no_xfa_path
            logger.debug("Dropped XFA from template: %s -> %s", template_path, no_xfa_path)
        else:
            final_template = template_path
        
        # 2) Generate FDF
        fdf_content = generate_fdf(field_data)
        fdf_path = os.path.join(tmpdir, "data.fdf")
        with open(fdf_path, "w", encoding="utf-8") as fdf_file:
            fdf_file.write(fdf_content)
        logger.debug("Generated FDF at %s with %d fields", fdf_path, len(field_data))
        
        # 3) Fill form & flatten
        filled_path = os.path.join(tmpdir, "filled_form.pdf")
        cmd_fill = [
            "pdftk", final_template,
            "fill_form", fdf_path,
            "output", filled_path,
            "flatten"
        ]
        subprocess.run(cmd_fill, check=True)
        logger.debug("pdftk fill_form+flatten executed, output: %s", filled_path)

        # 4) Return the result as bytes
        with open(filled_path, "rb") as f:
            filled_pdf_bytes = f.read()
        
        return filled_pdf_bytes
