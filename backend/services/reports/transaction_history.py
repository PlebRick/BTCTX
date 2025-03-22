# FILE: backend/services/reports/transaction_history.py

"""
transaction_history.py

Generates a Transaction History Report for a given year (including partial data if it's the current year).
Exports either PDF or CSV, listing all Deposits, Withdrawals, Transfers, Buys, and Sells with relevant fields:
    - date
    - type
    - asset
    - amount
    - cost
    - proceeds
    - gain_loss
    - description

We ensure:
  - All valid types (Deposit, Withdrawal, Transfer, Buy, Sell)
  - Strict date/time sort
  - "Transfers" included
  - Combined "Sell/Withdrawal" label for sells/withdrawals,
    plus "Income"/"Reward"/"Interest" for deposit with matching source.
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
    3) Returns the resulting bytes (PDF) or CSV bytes (utf-8).

    The CSV columns are:
       date,type,asset,amount,cost,proceeds,gain_loss,description

    Some rules for 'type':
     - If Deposit + source=Income => type=Income
     - If Deposit + source=Interest => type=Interest
     - If Deposit + source=Reward => type=Reward
     - Else if Deposit => "Deposit"
     - If Sell or Withdrawal => "Sell/Withdrawal"
     - If Transfer => "Transfer"
     - If Buy => "Buy"
    """

    # Determine date range
    start_of_year = datetime.datetime(year, 1, 1)
    now = datetime.datetime.now()
    if year == now.year:
        # current year => up to "today"
        end_of_year = now
    else:
        # full year => up to Dec 31
        end_of_year = datetime.datetime(year, 12, 31, 23, 59, 59)

    # Fetch transactions of all valid types, strictly sorted by timestamp + id
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

    # Build intermediate row data with custom logic
    results = []
    for tx in txs:
        row = _build_csv_row(db, tx)
        results.append(row)

    # Dispatch to PDF or CSV
    if format.lower() == "csv":
        csv_data = _generate_csv(results, year)
        return csv_data.encode("utf-8")
    else:
        pdf_bytes = _generate_pdf(results, year)
        return pdf_bytes


# -----------------------------------------------------------------------------
# Helper to map a single Transaction -> row dict
# -----------------------------------------------------------------------------

def _build_csv_row(db: Session, tx: Transaction) -> dict:
    """
    Replicates the logic from your front-end sample, producing columns:
      date, type, from_account, to_account, asset, amount, cost, proceeds, gain_loss, description
    """
    # 1) Date/time
    dt_str = tx.timestamp.isoformat()  # e.g. 2022-03-01T00:00:00+00:00

    # 2) Type (merges some categories)
    csv_type = _map_tx_type(tx)

    # 3) Account names
    from_acct = _get_account_name(db, tx.from_account_id)
    to_acct = _get_account_name(db, tx.to_account_id)

    # 4) Asset
    csv_asset = "BTC"  # Adjust as needed if some transactions are USD

    # 5) Amount
    amt = tx.amount or Decimal("0")
    amount_str = str(amt)

    # 6) Cost
    cost_str = "N/A"
    if tx.cost_basis_usd is not None:
        cost_str = str(tx.cost_basis_usd)

    # 7) Proceeds
    proceeds_str = "N/A"
    if tx.proceeds_usd is not None:
        proceeds_str = str(tx.proceeds_usd)

    # 8) Gain/Loss
    gain_str = "N/A"
    if tx.realized_gain_usd is not None:
        g = Decimal(tx.realized_gain_usd)
        if g > 0:
            gain_str = f"+{g}"
        elif g < 0:
            gain_str = f"{g}"  # includes the minus sign
        else:
            gain_str = "0.0"

    # 9) Description
    desc_str = _map_description(tx)

    return {
        "date": dt_str,
        "type": csv_type,
        "from_account": from_acct,
        "to_account": to_acct,
        "asset": csv_asset,
        "amount": amount_str,
        "cost": cost_str,
        "proceeds": proceeds_str,
        "gain_loss": gain_str,
        "description": desc_str,
    }


def _map_tx_type(tx: Transaction) -> str:
    """
    Merges your front-end logic to produce the CSV 'type' column:

    - If (Deposit && source=Income) => "Income"
    - If (Deposit && source=Reward) => "Reward"
    - If (Deposit && source=Interest) => "Interest"
    - Else if Deposit => "Deposit"
    - If Sell or Withdrawal => "Sell/Withdrawal"
    - If Transfer => "Transfer"
    - If Buy => "Buy"
    """
    t = tx.type
    if t == "Deposit":
        s = tx.source.lower() if tx.source else ""
        if s == "income":
            return "Income"
        elif s == "reward":
            return "Reward"
        elif s == "interest":
            return "Interest"
        else:
            return "Deposit"
    elif t in ["Sell", "Withdrawal"]:
        return "Sell/Withdrawal"
    elif t == "Transfer":
        return "Transfer"
    elif t == "Buy":
        return "Buy"
    return t  # fallback


def _map_description(tx: Transaction) -> str:
    """
    Your sample CSV last column is 'description'.
    We'll fill it with front-end labels like 'CapitalGainsTransaction'
    or 'Income' or etc. If that data isn't stored, you can combine
    purpose or source.

    For simplicity:
    - If Sell/Withdrawal => "CapitalGainsTransaction" if realized_gain_usd != 0
    - If Deposit => tx.source
    - else => tx.purpose
    """
    if tx.type in ["Sell", "Withdrawal"]:
        if tx.realized_gain_usd is not None and Decimal(tx.realized_gain_usd) != 0:
            return "CapitalGainsTransaction"
        return tx.purpose or ""
    elif tx.type == "Deposit":
        return tx.source or ""
    # For Transfer/Buy or others, fallback to .purpose
    return tx.purpose or ""


def _get_account_name(db: Session, account_id: int) -> str:
    """
    Retrieve the account name for a given account_id.
    Return "" if None. If account_id=99, treat as "External" (example).
    Adjust as needed if your actual DB uses a different structure.
    """
    if not account_id:
        return ""
    if account_id == 99:
        return "External"
    acct = db.query(Account).filter(Account.id == account_id).first()
    return acct.name if acct else ""


# --------------------------------------------------------------------------------
# _generate_csv / _generate_pdf
# --------------------------------------------------------------------------------

def _generate_csv(rows: List[dict], year: int) -> str:
    """
    Build CSV data from the row dicts.
    Each row has columns:
       date, type, from_account, to_account, asset, amount, cost, proceeds, gain_loss, description
    """
    headers = [
        "date",
        "type",
        "from_account",
        "to_account",
        "asset",
        "amount",
        "cost",
        "proceeds",
        "gain_loss",
        "description",
    ]
    lines = [",".join(headers)]

    for r in rows:
        line_elems = [
            _escape_csv(r["date"]),
            _escape_csv(r["type"]),
            _escape_csv(r["from_account"]),
            _escape_csv(r["to_account"]),
            _escape_csv(r["asset"]),
            _escape_csv(r["amount"]),
            _escape_csv(r["cost"]),
            _escape_csv(r["proceeds"]),
            _escape_csv(r["gain_loss"]),
            _escape_csv(r["description"]),
        ]
        lines.append(",".join(line_elems))

    csv_data = "\n".join(lines)
    logger.info(f"Generated Transaction History CSV for {year}, {len(rows)} rows.")
    return csv_data


def _escape_csv(val: str) -> str:
    """
    Minimal CSV escaping: wrap in quotes if there's a comma or quote, double any quotes.
    """
    if not val:
        return ""
    need_quotes = ("," in val) or ('"' in val)
    escaped = val.replace('"', '""')
    if need_quotes:
        return f"\"{escaped}\""
    return escaped


def _generate_pdf(rows: List[dict], year: int) -> bytes:
    """
    Build a PDF with ReportLab from the row dicts.
    Columns: date, type, from_account, to_account, asset, amount, cost, proceeds, gain_loss, description
    """

    buffer = BytesIO()
    styles = getSampleStyleSheet()

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

    # Build table header
    data = [[
        "date",
        "type",
        "from_account",
        "to_account",
        "asset",
        "amount",
        "cost",
        "proceeds",
        "gain_loss",
        "description",
    ]]

    # Add table rows
    for r in rows:
        data.append([
            Paragraph(r["date"], wrapped_style),
            Paragraph(r["type"], wrapped_style),
            Paragraph(r["from_account"], wrapped_style),
            Paragraph(r["to_account"], wrapped_style),
            Paragraph(r["asset"], wrapped_style),
            Paragraph(r["amount"], wrapped_style),
            Paragraph(r["cost"], wrapped_style),
            Paragraph(r["proceeds"], wrapped_style),
            Paragraph(r["gain_loss"], wrapped_style),
            Paragraph(r["description"], wrapped_style),
        ])

    # Adjust column widths as needed
    col_widths = [
        1.3 * inch,  # date
        1.0 * inch,  # type
        1.1 * inch,  # from_account
        1.1 * inch,  # to_account
        0.6 * inch,  # asset
        0.8 * inch,  # amount
        0.8 * inch,  # cost
        0.8 * inch,  # proceeds
        0.9 * inch,  # gain_loss
        1.2 * inch,  # description
    ]
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

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
