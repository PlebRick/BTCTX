from typing import Dict, Any
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def generate_comprehensive_tax_report(report_dict: Dict[str, Any]) -> bytes:
    """
    Generates a 'Comprehensive Tax Report' that includes BOTH
    high-level summaries (capital gains, income) AND detailed 
    transaction data (like 8949 line items).
    """
    # Prepare in-memory PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    story = []

    # --- Title & Metadata ---
    tax_year = report_dict.get("tax_year", "Unknown Year")
    report_date = report_dict.get("report_date", "Unknown Date")
    period = report_dict.get("period", "")

    story.append(Paragraph(f"<b>BitcoinTX Comprehensive Tax Report</b>", styles["Title"]))
    meta_text = (
        f"<b>Tax Year:</b> {tax_year}<br/>"
        f"<b>Report Date:</b> {report_date}<br/>"
        f"<b>Period:</b> {period}"
    )
    story.append(Paragraph(meta_text, styles["Normal"]))
    story.append(Spacer(1, 12))

    # ------------------------------------------------------
    # (A) Capital Gains Summary (Short/Long/Total)
    # ------------------------------------------------------
    cg_summary = report_dict.get("capital_gains_summary", {})
    if cg_summary:
        story.append(Paragraph("<b>Capital Gains Summary</b>", styles["Heading2"]))

        short_term = cg_summary.get("short_term", {})
        long_term = cg_summary.get("long_term", {})
        total = cg_summary.get("total", {})

        cg_data = [
            ["Type", "Proceeds", "Cost Basis", "Gain/Loss"],
            ["Short-Term",
             short_term.get("proceeds", 0),
             short_term.get("basis", 0),
             short_term.get("gain", 0)],
            ["Long-Term",
             long_term.get("proceeds", 0),
             long_term.get("basis", 0),
             long_term.get("gain", 0)],
            ["Total",
             total.get("proceeds", 0),
             total.get("basis", 0),
             total.get("gain", 0)],
        ]

        table = Table(cg_data)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # ------------------------------------------------------
    # (B) Income Summary
    # ------------------------------------------------------
    inc_summary = report_dict.get("income_summary", {})
    if inc_summary:
        story.append(Paragraph("<b>Income Summary</b>", styles["Heading2"]))

        inc_data = [
            ["Mining", "Reward", "Other", "Total"],
            [
                inc_summary.get("Mining", 0),
                inc_summary.get("Reward", 0),
                inc_summary.get("Other", 0),
                inc_summary.get("Total", 0),
            ]
        ]
        table = Table(inc_data)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # ------------------------------------------------------
    # (C) Detailed Capital Gains Transactions
    # ------------------------------------------------------
    cg_transactions = report_dict.get("capital_gains_transactions", [])
    if cg_transactions:
        story.append(Paragraph("<b>Capital Gains Transactions</b>", styles["Heading2"]))

        tx_data = [["Date Sold", "Date Acquired", "Asset", "Amount", 
                    "Cost Basis", "Proceeds", "Gain/Loss", "Holding"]]
        for tx in cg_transactions:
            tx_data.append([
                tx.get("date_sold", ""),
                tx.get("date_acquired", ""),
                tx.get("asset", ""),
                f"{tx.get('amount', 0):.8f}",
                f"${tx.get('cost', 0):.2f}",
                f"${tx.get('proceeds', 0):.2f}",
                f"${tx.get('gain_loss', 0):.2f}",
                tx.get("holding_period", "")
            ])
        table = Table(tx_data)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # ------------------------------------------------------
    # (D) Detailed Income Transactions
    # ------------------------------------------------------
    inc_transactions = report_dict.get("income_transactions", [])
    if inc_transactions:
        story.append(Paragraph("<b>Income Transactions</b>", styles["Heading2"]))

        inc_data = [["Date", "Asset", "Amount", "Value (USD)", "Type", "Description"]]
        for i_tx in inc_transactions:
            inc_data.append([
                i_tx.get("date", ""),
                i_tx.get("asset", ""),
                f"{i_tx.get('amount', 0):.8f}",
                f"${i_tx.get('value_usd', 0):.2f}",
                i_tx.get("type", ""),
                i_tx.get("description", ""),
            ])
        table = Table(inc_data)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # ------------------------------------------------------
    # (E) End-of-Year Balances
    # ------------------------------------------------------
    eoy_balances = report_dict.get("end_of_year_balances", [])
    if eoy_balances:
        story.append(Paragraph("<b>End of Year Holdings</b>", styles["Heading2"]))

        bal_data = [["Asset", "Quantity", "Cost Basis", "Market Value", "Description"]]
        for bal in eoy_balances:
            bal_data.append([
                bal.get("asset", ""),
                f"{bal.get('quantity', 0):.8f}",
                f"${bal.get('cost', 0):.2f}",
                f"${bal.get('value', 0):.2f}",
                bal.get("description", "")
            ])
        table = Table(bal_data)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # Build the PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
