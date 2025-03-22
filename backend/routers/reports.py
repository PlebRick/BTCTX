# FILE: backend/routers/reports.py

from fastapi import APIRouter, Depends, Response, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.services.reports.reporting_core import generate_report_data
from backend.services.reports.complete_tax_report import generate_comprehensive_tax_report

# NEW: Import the simpler transaction history generator
from backend.services.reports import transaction_history

reports_router = APIRouter()

# ---------------------------------------------------------
# 1) Complete Tax Report (PDF only)
# ---------------------------------------------------------
@reports_router.get("/complete_tax_report")
def get_complete_tax_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Generates the comprehensive/complete tax report in PDF for the given tax year.
    """
    report_dict = generate_report_data(db, year)
    pdf_bytes = generate_comprehensive_tax_report(report_dict)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="CompleteTaxReport_{year}.pdf"'}
    )


# ---------------------------------------------------------
# 2) IRS Reports (Form 8949, Schedule D, etc.) - PDF
# ---------------------------------------------------------
@reports_router.get("/irs_reports")
def get_irs_reports(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Generates or combines multiple IRS-specific PDFs (Form 8949, Schedule D, etc.)
    into a single PDF. This is just a placeholder example.
    """
    # aggregator data
    report_dict = generate_report_data(db, year)

    # For demonstration, returning placeholder PDF bytes
    pdf_placeholder = b"(Placeholder) IRS Reports PDF for 8949, Schedule D, etc."

    return Response(
        content=pdf_placeholder,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="IRSReports_{year}.pdf"'}
    )


# ---------------------------------------------------------
# 3) Simple Transaction History (CSV or PDF) - BYPASS advanced tax logic
# ---------------------------------------------------------
@reports_router.get("/simple_transaction_history")
def get_simple_transaction_history(
    year: int,
    format: str = Query("csv", regex="^(csv|pdf)$"),
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Returns a raw, comprehensive list of transactions for the given year (Deposit, Withdrawal,
    Transfer, Buy, Sell), strictly sorted by date, WITHOUT pulling cost-basis from reporting_core
    or calling external BTC price APIs. The result is guaranteed to include all transactions 
    as they appear in the DB.

    - `?year=YYYY` => filter by year
    - `?format=csv` (default) => CSV
    - `?format=pdf` => PDF

    This uses transaction_history.generate_transaction_history_report(...), which fetches
    the transactions directly from the DB and formats them (CSV/PDF) without any advanced 
    cost-basis logic.
    """
    # Generate the report bytes from transaction_history.py
    report_bytes = transaction_history.generate_transaction_history_report(db, year, format)

    # Return CSV or PDF depending on 'format'
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
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'}
    )
