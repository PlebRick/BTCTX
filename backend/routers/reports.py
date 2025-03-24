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

# The updated fill logic that now checks for /AcroForm
from backend.services.reports.form_8949 import (
    build_form_8949_and_schedule_d,
    map_8949_rows_to_field_data,
    Form8949Row  # your custom class for 8949 data
)

reports_router = APIRouter()


@reports_router.get("/complete_tax_report")
def get_complete_tax_report(year: int, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    report_dict = generate_report_data(db, year)
    pdf_bytes = generate_comprehensive_tax_report(report_dict)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename=\"CompleteTaxReport_{year}.pdf\"'}
    )

@reports_router.get("/irs_reports")
def get_irs_reports(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Generates a combined PDF with:
      - Multiple Form 8949 pages (short- & long-term)
      - Schedule D totals
    Merging them into one final PDF using PdfWriter, skipping form fill if no AcroForm.
    """
    # 1) Build short-/long-term data
    report_data = build_form_8949_and_schedule_d(year, db)
    short_rows = [Form8949Row(**r) for r in report_data["short_term"]]
    long_rows = [Form8949Row(**r) for r in report_data["long_term"]]

    # 2) PDF templates
    path_8949 = "backend/assets/irs_templates/Form_8949_Fillable_2024.pdf"
    path_sched_d = "backend/assets/irs_templates/Schedule_D_Fillable_2024.pdf"

    partial_pdfs = []

    # 3) Generate short-term 8949 pages
    for i in range(0, len(short_rows), 14):
        chunk = short_rows[i : i + 14]
        field_data = map_8949_rows_to_field_data(chunk, page=1)
        pdf_bytes = fill_pdf_form(path_8949, field_data)
        partial_pdfs.append(pdf_bytes)

    # 4) Generate long-term 8949 pages
    for i in range(0, len(long_rows), 14):
        chunk = long_rows[i : i + 14]
        field_data = map_8949_rows_to_field_data(chunk, page=2)
        pdf_bytes = fill_pdf_form(path_8949, field_data)
        partial_pdfs.append(pdf_bytes)

    # 5) Fill Schedule D (may or may not have /AcroForm)
    schedule_d_fields = {
        # Example line mappings
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_07[0]": str(report_data["schedule_d"]["short_term"]["proceeds"]),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_08[0]": str(report_data["schedule_d"]["short_term"]["cost"]),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_10[0]": str(report_data["schedule_d"]["short_term"]["gain_loss"]),

        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_27[0]": str(report_data["schedule_d"]["long_term"]["proceeds"]),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_28[0]": str(report_data["schedule_d"]["long_term"]["cost"]),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_30[0]": str(report_data["schedule_d"]["long_term"]["gain_loss"]),
    }
    filled_sd_bytes = fill_pdf_form(path_sched_d, schedule_d_fields)
    partial_pdfs.append(filled_sd_bytes)

    # 6) Merge everything into a single PDF
    final_pdf = _merge_all_pdfs(partial_pdfs)

    return Response(
        content=final_pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename=\"IRSReports_{year}.pdf\"'}
    )


def fill_pdf_form(template_path: str, field_data: Dict[str, str]) -> bytes:
    """
    Safely fills a PDF if it has an /AcroForm. Otherwise, we skip form updates.
    This prevents PyPdfError: No /AcroForm dictionary in PDF of PdfWriter Object.
    """
    reader = PdfReader(template_path)
    writer = PdfWriter()

    # Copy all pages from reader to writer
    for page in reader.pages:
        writer.add_page(page)

    # Check if PDF has an /AcroForm
    root_dict = reader.trailer["/Root"]
    has_acroform = "/AcroForm" in root_dict

    if has_acroform:
        # Add /AcroForm dict to the writer, set NeedAppearances
        acroform = root_dict["/AcroForm"]
        writer._root_object.update({
            NameObject("/AcroForm"): acroform
        })
        writer._root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): BooleanObject(True)
        })

        # Update fields on the first page only
        writer.update_page_form_field_values(writer.pages[0], field_data)

    # If no /AcroForm, we skip filling fields (non-fillable PDF)

    output_buf = BytesIO()
    writer.write(output_buf)
    return output_buf.getvalue()


def _merge_all_pdfs(pdf_list: List[bytes]) -> bytes:
    """
    Merges multiple PDF files (in memory) into one PDF using PdfReader + PdfWriter.
    """
    writer = PdfWriter()
    for pdf_data in pdf_list:
        reader = PdfReader(BytesIO(pdf_data))
        # Add each page to the writer
        for page in reader.pages:
            writer.add_page(page)

    merged_stream = BytesIO()
    writer.write(merged_stream)
    return merged_stream.getvalue()


@reports_router.get("/simple_transaction_history")
def get_simple_transaction_history(
    year: int,
    format: str = Query("csv", regex="^(csv|pdf)$"),
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    report_bytes = transaction_history.generate_transaction_history_report(db, year, format)

    if format.lower() == "csv":
        content_type = "text/csv"
        file_ext = "csv"
    else:
        content_type = "application/pdf"
        file_ext = "pdf"

    file_name = f"SimpleTransactionHistory_{year}.{file_ext}"
    return Response(
        content=report_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename=\"{file_name}\"'}
    )
