# FILE: backend/services/reports/pdftk_filler.py

import subprocess
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


def generate_fdf(field_data: dict) -> str:
    """
    Generates FDF (Forms Data Format) content from a Python dictionary
    representing form fields. Each key in field_data is the PDF form field name,
    and its value is the string to insert.

    The result is a text string conforming to the FDF 1.2 spec, which pdftk
    can consume to fill a PDF form (AcroForm or XFA-based, if combined
    with 'drop_xfa').

    Notes:
      - Basic escaping is applied to parentheses: '(' => '\(', ')' => '\)'.
      - If you have more complex or non-ASCII characters, consider expanding
        the escaping logic.
    """
    # Header lines for FDF 1.2
    lines = [
        "%FDF-1.2",
        "1 0 obj << ",
        "/FDF << /Fields ["
    ]

    # For each key/value pair in field_data, create a line in the FDF.
    for key, value in field_data.items():
        # Escape parentheses just in case
        escaped_key = key.replace("(", r"\(").replace(")", r"\)")
        escaped_value = value.replace("(", r"\(").replace(")", r"\)")

        # /T => field name, /V => field value
        lines.append(f"<< /T ({escaped_key}) /V ({escaped_value}) >>")

    # Footer lines for the FDF structure
    lines.append("] >> ")
    lines.append(">>")
    lines.append("endobj")
    lines.append("trailer")
    lines.append("<< /Root 1 0 R >>")
    lines.append("%%EOF")

    # Join everything with newlines to form the final FDF text
    return "\n".join(lines)


def fill_pdf_with_pdftk(template_path: str, field_data: dict, drop_xfa: bool = True) -> bytes:
    """
    Fills a PDF form (AcroForm or XFA) using pdftk by:
      1) Optionally dropping XFA to ensure AcroForm fields are recognized.
      2) Generating an FDF file from 'field_data'.
      3) Calling 'pdftk ... fill_form ... flatten' to produce a flattened PDF.

    Args:
        template_path (str):
            The filesystem path to your PDF form (e.g., "Form_8949_Fillable_2024.pdf").

        field_data (dict):
            A dict of { "PDF_FieldName": "StringValue" } from your
            row-mapping logic (e.g., map_8949_rows_to_field_data(...)).

        drop_xfa (bool):
            Whether to remove XFA data first. If the PDF is known to be XFA-based,
            set True (default). If you're sure it's AcroForm-only, you can set False
            to skip an extra pdftk command.

    Returns:
        bytes: The filled and flattened PDF data as in-memory bytes.

    Raises:
        subprocess.CalledProcessError:
            If pdftk encounters an error (e.g., invalid PDF, missing executable).

    Usage Example:
        from backend.services.reports.pdftk_filler import fill_pdf_with_pdftk

        fields = {
            "topmostSubform[0].Page1[0].f1_03[0]": "My field text"
        }
        final_pdf_bytes = fill_pdf_with_pdftk("Form_8949_Fillable_2024.pdf", fields, drop_xfa=True)
        # 'final_pdf_bytes' is now a flattened PDF in memory
    """
    with tempfile.TemporaryDirectory() as tmpdir:

        # 1) Possibly remove XFA
        if drop_xfa:
            no_xfa_path = os.path.join(tmpdir, "no_xfa.pdf")
            # IMPORTANT: place "drop_xfa" *after* "output no_xfa_path"
            cmd_drop = [
                "pdftk",
                template_path,
                "output",
                no_xfa_path,
                "drop_xfa"
            ]
            subprocess.run(cmd_drop, check=True)
            final_template = no_xfa_path

            logger.debug(
                "Dropped XFA from template => %s => %s",
                template_path, no_xfa_path
            )
        else:
            final_template = template_path

        # 2) Generate an FDF file in the temp directory
        fdf_content = generate_fdf(field_data)
        fdf_path = os.path.join(tmpdir, "data.fdf")
        with open(fdf_path, "w", encoding="utf-8") as fdf_file:
            fdf_file.write(fdf_content)

        logger.debug(
            "Generated FDF at %s with %d fields",
            fdf_path, len(field_data)
        )

        # 3) Fill form & flatten
        filled_path = os.path.join(tmpdir, "filled_form.pdf")
        cmd_fill = [
            "pdftk",
            final_template,
            "fill_form",
            fdf_path,
            "output",
            filled_path,
            "flatten"
        ]
        subprocess.run(cmd_fill, check=True)

        logger.debug(
            "pdftk fill_form+flatten executed successfully, output => %s",
            filled_path
        )

        # 4) Return the filled PDF from memory
        with open(filled_path, "rb") as f:
            filled_pdf_bytes = f.read()

        return filled_pdf_bytes
