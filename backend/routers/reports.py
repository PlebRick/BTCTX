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
# NEW: Import pdftk-based filler & flatten from pdf_utils
# (Make sure these files exist as you've set up.)
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

    This uses reportlab-based generation from scratch
    (complete_tax_report.py) and remains unchanged.
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
      - Form 8949 (short- and long-term pages)
      - Schedule D (totals only)

    We now use pdftk for filling these XFA-based IRS forms.
    If ?flatten=true, we flatten the final merged PDF again with pdftk
    so all fields appear in any PDF viewer.
    """
    # 1) Build the Form 8949 row data
    report_data = build_form_8949_and_schedule_d(year, db)
    short_rows = [Form8949Row(**r) for r in report_data["short_term"]]
    long_rows = [Form8949Row(**r) for r in report_data["long_term"]]

    path_8949 = "backend/assets/irs_templates/Form_8949_Fillable_2024.pdf"
    path_sched_d = "backend/assets/irs_templates/Schedule_D_Fillable_2024.pdf"

    partial_pdfs: List[bytes] = []

    # 2) Short-term Form 8949 pages (14 rows per page)
    for i in range(0, len(short_rows), 14):
        chunk = short_rows[i:i + 14]
        field_data = map_8949_rows_to_field_data(chunk, page=1)

        # Fill with pdftk, dropping XFA so data actually appears
        pdf_bytes = fill_pdf_with_pdftk(path_8949, field_data, drop_xfa=True)
        partial_pdfs.append(pdf_bytes)

    # 3) Long-term Form 8949 pages
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

    # 5) Merge all partial PDFs
    final_pdf = _merge_all_pdfs(partial_pdfs)

    # 6) Optionally flatten again with pdftk if user set ?flatten=true
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

    This route remains unchanged, as transaction_history.py
    uses ReportLab for PDF output or CSV directly.
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
# (DEPRECATED) Old fill_pdf_form() method with pypdf (no longer used for IRS forms)
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
    Merges multiple in-memory PDFs into a single PDF using pypdf.

    Even though we fill and flatten each chunk with pdftk,
    we can safely merge them with pypdf. The final result is a single PDF file.
    """
    writer = PdfWriter()
    for pdf_data in pdf_list:
        reader = PdfReader(BytesIO(pdf_data))
        for page in reader.pages:
            writer.add_page(page)

    merged_stream = BytesIO()
    writer.write(merged_stream)
    return merged_stream.getvalue()
