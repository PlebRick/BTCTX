# FILE: backend/routers/reports.py

from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, List
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject

from backend.database import get_db
from backend.services.reports.reporting_core import generate_report_data
from backend.services.reports.complete_tax_report import generate_comprehensive_tax_report
from backend.services.reports import transaction_history
from backend.services.reports.form_8949 import (
    build_form_8949_and_schedule_d,
    map_8949_rows_to_field_data,
    Form8949Row,
)

# -------------------------------------------------------------------------
# pdftk-based filler & optional final flatten
# -------------------------------------------------------------------------
from backend.services.reports.pdftk_filler import fill_pdf_with_pdftk
from backend.services.reports.pdf_utils import flatten_pdf_with_pdftk
# -------------------------------------------------------------------------

reports_router = APIRouter()


@reports_router.get("/complete_tax_report")
def get_complete_tax_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Generates a comprehensive tax report (PDF) that includes
    realized gains, income, fees, and balances.

    Uses reportlab-based generation from scratch (complete_tax_report.py).
    We leave it unchanged, as it's working well for custom PDF generation.
    """
    report_dict = generate_report_data(db, year)
    pdf_bytes = generate_comprehensive_tax_report(report_dict)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="CompleteTaxReport_{year}.pdf"'}
    )


@reports_router.get("/irs_reports")
def get_irs_reports(
    year: int,
    flatten: bool = Query(False, description="Set to True to flatten the final PDF via pdftk"),
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Generates a combined PDF for:
      - Form 8949 (short- and long-term pages, chunked 14 rows each)
      - Schedule D (totals only)

    Uses pdftk to fill these potentially XFA-based IRS forms. Then merges
    partial PDFs in memory with pypdf. If ?flatten=true, optionally does
    a final flatten pass with pdftk.

    Return: Merged PDF as bytes, in 'application/pdf'.
    """
    # 1) Build the row data (short & long term) plus schedule_d summary
    report_data = build_form_8949_and_schedule_d(year, db)
    short_rows = [Form8949Row(**r) for r in report_data["short_term"]]
    long_rows = [Form8949Row(**r) for r in report_data["long_term"]]

    path_8949 = "backend/assets/irs_templates/Form_8949_Fillable_2024.pdf"
    path_sched_d = "backend/assets/irs_templates/Schedule_D_Fillable_2024.pdf"

    partial_pdfs: List[bytes] = []

    # 2) Short-term Form 8949, 14 rows per page
    for i in range(0, len(short_rows), 14):
        chunk = short_rows[i:i + 14]
        field_data = map_8949_rows_to_field_data(chunk, page=1)
        # Flattened partial PDF via pdftk
        pdf_bytes = fill_pdf_with_pdftk(path_8949, field_data, drop_xfa=True)
        partial_pdfs.append(pdf_bytes)

    # 3) Long-term Form 8949, 14 rows per page
    for i in range(0, len(long_rows), 14):
        chunk = long_rows[i:i + 14]
        field_data = map_8949_rows_to_field_data(chunk, page=2)
        pdf_bytes = fill_pdf_with_pdftk(path_8949, field_data, drop_xfa=True)
        partial_pdfs.append(pdf_bytes)

    # 4) Schedule D totals
    schedule_d_fields = {
        # Short-term (line 1b)
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_07[0]": str(report_data["schedule_d"]["short_term"]["proceeds"]),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_08[0]": str(report_data["schedule_d"]["short_term"]["cost"]),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_09[0]": "",
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_10[0]": str(report_data["schedule_d"]["short_term"]["gain_loss"]),

        # Long-term (line 8b)
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_27[0]": str(report_data["schedule_d"]["long_term"]["proceeds"]),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_28[0]": str(report_data["schedule_d"]["long_term"]["cost"]),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_29[0]": "",
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_30[0]": str(report_data["schedule_d"]["long_term"]["gain_loss"]),
    }
    filled_sd_bytes = fill_pdf_with_pdftk(path_sched_d, schedule_d_fields, drop_xfa=True)
    partial_pdfs.append(filled_sd_bytes)

    # 5) Merge all partial PDFs (already flattened) in memory with pypdf
    final_pdf = _merge_all_pdfs(partial_pdfs)

    # 6) Optional final flatten
    if flatten:
        final_pdf = flatten_pdf_with_pdftk(final_pdf)
        debug_path = "/tmp/IRSReport_flattened_test.pdf"
        with open(debug_path, "wb") as f:
            f.write(final_pdf)
        print(f"[DEBUG] Flattened PDF (pdftk) written to {debug_path}")

    return Response(
        content=final_pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="IRSReports_{year}.pdf"'}
    )


@reports_router.get("/simple_transaction_history")
def get_simple_transaction_history(
    year: int,
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Exports a raw list of transactions (CSV or PDF).
    Bypasses FIFO and gain/loss logic.

    This route remains unchanged. 'transaction_history.py' uses
    ReportLab for PDF or CSV output.
    """
    report_bytes = transaction_history.generate_transaction_history_report(db, year, format)

    file_ext = format.lower()
    content_type = "text/csv" if file_ext == "csv" else "application/pdf"
    file_name = f"SimpleTransactionHistory_{year}.{file_ext}"

    return Response(
        content=report_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename=\"{file_name}\"'}
    )


# -----------------------------------------------------------------------------
# (DEPRECATED) Old fill_pdf_form with pypdf. Not used for IRS XFA forms.
# -----------------------------------------------------------------------------
def fill_pdf_form(template_path: str, field_data: Dict[str, str]) -> bytes:
    """
    (DEPRECATED) Fills a PDF form using pypdf if it supports AcroForm fields.
    If you have an XFA-based form, pypdf can’t fill it reliably.
    Keeping this for any non-IRS forms or as a fallback.
    """
    reader = PdfReader(template_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    root_dict = reader.trailer.get("/Root", {})
    if "/AcroForm" in root_dict:
        acroform = root_dict["/AcroForm"]
        writer._root_object.update({NameObject("/AcroForm"): acroform})
        writer._root_object["/AcroForm"].update({NameObject("/NeedAppearances"): BooleanObject(True)})
        writer.update_page_form_field_values(writer.pages[0], field_data)

    output_buf = BytesIO()
    writer.write(output_buf)
    return output_buf.getvalue()


def _merge_all_pdfs(pdf_list: List[bytes]) -> bytes:
    """
    Merges multiple PDFs (in-memory bytes) into a single PDF with pypdf.

    Because each chunk is flattened by pdftk, we can safely merge them.
    The final PDF is returned as bytes for immediate response to the user.
    """
    writer = PdfWriter()
    for pdf_data in pdf_list:
        reader = PdfReader(BytesIO(pdf_data))
        for page in reader.pages:
            writer.add_page(page)

    merged_stream = BytesIO()
    writer.write(merged_stream)
    return merged_stream.getvalue()
