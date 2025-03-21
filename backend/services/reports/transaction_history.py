# FILE: backend/services/reports/transaction_history.py

"""
transaction_history.py

Generates a Transaction History Report for a given year (including partial data if it's the current year).
Exports either PDF or CSV, listing all Deposits, Withdrawals, Transfers, Buys, and Sells with relevant fields:
    - Date
    - Type
    - FromAccount
    - ToAccount
    - Amount
    - Fee
    - FeeCurrency
    - CostBasisUSD
    - ProceedsUSD
    - Purpose

Industry Best Practices:
 - This report follows a double-entry accounting paradigm for Bitcoin and fiat transactions.
 - Aligns with FIFO cost basis tracking for IRS tax considerations.
 - Always verify final outputs with a qualified tax professional if using this data for official filings.
"""

import datetime
import logging
from io import BytesIO
from decimal import Decimal
from typing import List

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen.canvas import Canvas

from sqlalchemy.orm import Session
from backend.models.transaction import Transaction
from backend.models.account import Account

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_transaction_history_report(
    db: Session,
    year: int,
    format: str = "pdf"
) -> bytes:
    """
    High-level function to generate the Transaction History for a given year in PDF or CSV.

    1) Queries all transactions matching one of [Deposit, Withdrawal, Transfer, Buy, Sell]
       within the specified year. If it's the current year, fetch up to today's date.
    2) Depending on 'format':
       - "pdf": calls _generate_pdf(...)
       - "csv": calls _generate_csv(...)
    3) Returns the resulting bytes (PDF) or bytes-encoded CSV.

    :param db:        SQLAlchemy Session
    :param year:      The year to filter by. If `year` is the current year, we limit up to today's date.
    :param format:    "pdf" or "csv". Defaults to "pdf".
    :return:          PDF or CSV data as bytes
    """

    # Determine start/end times
    start_of_year = datetime.datetime(year, 1, 1)
    now = datetime.datetime.now()
    if year == now.year:
        # current year => up to "today"
        end_of_year = now
    else:
        # full year => up to Dec 31
        end_of_year = datetime.datetime(year, 12, 31, 23, 59, 59)

    # Query relevant transactions
    # We only include types in (Deposit, Withdrawal, Transfer, Buy, Sell).
    valid_types = ["Deposit", "Withdrawal", "Transfer", "Buy", "Sell"]
    txs = (
        db.query(Transaction)
          .filter(
              Transaction.type.in_(valid_types),
              Transaction.timestamp >= start_of_year,
              Transaction.timestamp <= end_of_year
          )
          .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
          .all()
    )

    # Collect rows with all relevant columns:
    #   Date, Type, FromAccount, ToAccount, Amount, Fee, FeeCurrency,
    #   CostBasisUSD, ProceedsUSD, Purpose
    results = []
    for tx in txs:
        date_str = tx.timestamp.isoformat()
        # Convert to a simpler YYYY-MM-DD if desired
        # date_str = tx.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        from_acct_name = _get_account_name(db, tx.from_account_id)
        to_acct_name = _get_account_name(db, tx.to_account_id)

        # Turn any None decimals into "0.0"
        fee_amt = tx.fee_amount if tx.fee_amount else Decimal("0.0")
        cost_basis = tx.cost_basis_usd if tx.cost_basis_usd else Decimal("0.0")
        proceeds = tx.proceeds_usd if tx.proceeds_usd else Decimal("0.0")

        row = {
            "date": date_str,
            "type": tx.type,
            "from_account": from_acct_name,
            "to_account": to_acct_name,
            "amount": str(tx.amount or "0.0"),
            "fee": str(fee_amt),
            "fee_currency": tx.fee_currency or "",
            "cost_basis_usd": str(cost_basis),
            "proceeds_usd": str(proceeds),
            "purpose": tx.purpose or "",
        }
        results.append(row)

    # Dispatch to PDF or CSV
    if format.lower() == "csv":
        csv_data = _generate_csv(results, year)
        return csv_data.encode("utf-8")
    else:
        pdf_bytes = _generate_pdf(results, year)
        return pdf_bytes


# --------------------------------------------------------------------------------
# Internal Helpers
# --------------------------------------------------------------------------------

def _get_account_name(db: Session, account_id: int) -> str:
    """
    Retrieve the account name for a given account_id. Returns "" if not found or if ID is None/99.
    """
    if not account_id or account_id == 99:
        return "External" if account_id == 99 else ""
    acct = db.query(Account).filter(Account.id == account_id).first()
    return acct.name if acct else ""


def _generate_csv(rows: List[dict], year: int) -> str:
    """
    Build CSV data from the list of row dicts. Return as a string.
    """
    # CSV header
    headers = [
        "Date",
        "Type",
        "FromAccount",
        "ToAccount",
        "Amount",
        "Fee",
        "FeeCurrency",
        "CostBasisUSD",
        "ProceedsUSD",
        "Purpose",
    ]
    lines = [",".join(headers)]

    for row in rows:
        line = (
            f"{row['date']},"
            f"{row['type']},"
            f"{row['from_account']},"
            f"{row['to_account']},"
            f"{row['amount']},"
            f"{row['fee']},"
            f"{row['fee_currency']},"
            f"{row['cost_basis_usd']},"
            f"{row['proceeds_usd']},"
            f"\"{row['purpose'].replace('\"','\"\"')}\""  # handle commas or quotes in purpose
        )
        lines.append(line)

    csv_data = "\n".join(lines)
    logger.info(f"Generated Transaction History CSV for {year}, {len(rows)} rows.")
    return csv_data


def _generate_pdf(rows: List[dict], year: int) -> bytes:
    """
    Build a PDF with ReportLab from the list of row dicts.
    Return the PDF as raw bytes in memory.

    We create a simple table including:
      - Date
      - Type
      - FromAccount
      - ToAccount
      - Amount
      - Fee
      - FeeCurrency
      - CostBasisUSD
      - ProceedsUSD
      - Purpose
    """

    buffer = BytesIO()
    styles = getSampleStyleSheet()

    # Custom styles
    heading_style = ParagraphStyle(
        name="Heading1Left",
        parent=styles["Heading1"],
        alignment=0,
        spaceBefore=12,
        spaceAfter=8,
    )
    normal_style = styles["Normal"]
    wrapped_style = ParagraphStyle(
        name="Wrapped",
        parent=normal_style,
        fontSize=8,
        leading=10,
        wordWrap="CJK",
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    def on_first_page(canvas: Canvas, doc_obj):
        # Title or blank
        pass

    def on_later_pages(canvas: Canvas, doc_obj):
        page_num = doc_obj.page
        canvas.setFont("Helvetica", 9)
        canvas.drawString(0.5 * inch, 0.5 * inch, "Generated by BitcoinTX")
        canvas.drawRightString(7.5 * inch, 0.5 * inch, f"Page {page_num}")

    story = []

    # Title
    story.append(Paragraph(f"Transaction History for {year}", heading_style))
    story.append(Spacer(1, 0.2 * inch))

    if not rows:
        story.append(Paragraph("No transactions found for this period.", normal_style))
        doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        logger.info(f"Generated empty Transaction History PDF for {year}.")
        return pdf_bytes

    # Table Header
    data = [[
        "Date",
        "Type",
        "From",
        "To",
        "Amount",
        "Fee",
        "FeeCur",
        "CostBasis",
        "Proceeds",
        "Purpose",
    ]]

    # Fill table rows
    for row in rows:
        data.append([
            Paragraph(row["date"], wrapped_style),
            Paragraph(row["type"], wrapped_style),
            Paragraph(row["from_account"], wrapped_style),
            Paragraph(row["to_account"], wrapped_style),
            Paragraph(row["amount"], wrapped_style),
            Paragraph(row["fee"], wrapped_style),
            Paragraph(row["fee_currency"], wrapped_style),
            Paragraph(row["cost_basis_usd"], wrapped_style),
            Paragraph(row["proceeds_usd"], wrapped_style),
            Paragraph(row["purpose"], wrapped_style),
        ])

    # Build the table with styling
    col_widths = [1.2*inch, 0.8*inch, 1.0*inch, 1.0*inch, 0.8*inch,
                  0.7*inch, 0.6*inch, 0.8*inch, 0.8*inch, 1.2*inch]
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    # Footer
    story.append(
        Paragraph(
            "All amounts are shown as recorded in BitcoinTX's ledger. "
            "For official tax usage, please consult your accountant.",
            normal_style
        )
    )

    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    logger.info(f"Generated Transaction History PDF for {year}, {len(rows)} rows.")
    return pdf_bytes
