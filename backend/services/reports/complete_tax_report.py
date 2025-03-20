from typing import Dict, Any, List
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen.canvas import Canvas

def generate_comprehensive_tax_report(report_dict: Dict[str, Any]) -> bytes:
    """
    Comprehensive Tax Report with:
      1) A blank title page (no page number).
      2) Page numbers on subsequent pages, starting at "Page 1" for the second page.
      3) Wider columns & wrapped text to avoid overlap.
      4) Headings left-aligned, and minimal spacing as requested.
    """
    buffer = BytesIO()
    styles = getSampleStyleSheet()

    # Custom heading style (left-aligned)
    heading_style = ParagraphStyle(
        name="Heading2Left",
        parent=styles["Heading2"],
        alignment=0,  # left align
        spaceBefore=12,
        spaceAfter=8,
    )

    # Normal style for body text
    normal_style = styles["Normal"]
    # A style for wrapping table cells so they don't overflow
    wrapped_style = ParagraphStyle(
        name="Wrapped",
        parent=normal_style,
        wordWrap='CJK',  # or 'RTL' or 'CJK'
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    # ----------------------------------------------
    # Page numbering callbacks
    # ----------------------------------------------
    def on_first_page(canvas: Canvas, doc):
        """
        Title page layout callback:
        No page number here.
        """
        pass

    def on_later_pages(canvas: Canvas, doc):
        """
        Subsequent pages layout callback:
        Place "Page X" in the bottom-right corner,
        counting from 1 on the *second* physical page.
        """
        page_num = doc.page - 1  # shift so the second sheet is labeled "Page 1"
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(7.9 * inch, 0.5 * inch, f"Page {page_num}")

    # ----------------------------------------------
    # Build the story
    # ----------------------------------------------
    story: List = []

    # 1) Title Page (no page number)
    tax_year = report_dict.get("tax_year", "Unknown Year")
    report_date = report_dict.get("report_date", "Unknown Date")
    period = report_dict.get("period", "N/A")

    story.append(Paragraph("BitcoinTX Comprehensive Tax Report", styles["Title"]))
    meta_text = (
        f"<b>Tax Year:</b> {tax_year}<br/>"
        f"<b>Report Date:</b> {report_date}<br/>"
        f"<b>Period:</b> {period}"
    )
    story.append(Paragraph(meta_text, normal_style))
    story.append(Spacer(1, 12))

    disclaimers = report_dict.get("disclaimers", "")
    if disclaimers:
        story.append(Paragraph(disclaimers, normal_style))
    story.append(PageBreak())  # End title page, move on to normal pages

    # 2) Capital Gains Summary
    cg_summary = report_dict.get("capital_gains_summary", {})
    if cg_summary:
        story.append(Paragraph("Capital Gains Summary", heading_style))

        short_term = cg_summary.get("short_term", {})
        long_term = cg_summary.get("long_term", {})
        total = cg_summary.get("total", {})

        cg_data = [
            ["Type", "Proceeds", "Cost Basis", "Gain/Loss"],
            [
                "Short-Term",
                f"{short_term.get('proceeds', 0):,.2f}",
                f"{short_term.get('basis', 0):,.2f}",
                f"{short_term.get('gain', 0):,.2f}",
            ],
            [
                "Long-Term",
                f"{long_term.get('proceeds', 0):,.2f}",
                f"{long_term.get('basis', 0):,.2f}",
                f"{long_term.get('gain', 0):,.2f}",
            ],
            [
                "Total",
                f"{total.get('proceeds', 0):,.2f}",
                f"{total.get('basis', 0):,.2f}",
                f"{total.get('gain', 0):,.2f}",
            ],
        ]
        cg_table = Table(cg_data)
        cg_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(cg_table)
        story.append(Spacer(1, 12))

    # 3) Income Summary
    inc_summary = report_dict.get("income_summary", {})
    if inc_summary:
        story.append(Paragraph("Income Summary", heading_style))
        inc_data = [
            ["Mining", "Reward", "Other", "Total"],
            [
                f"{inc_summary.get('Mining', 0):,.2f}",
                f"{inc_summary.get('Reward', 0):,.2f}",
                f"{inc_summary.get('Other', 0):,.2f}",
                f"{inc_summary.get('Total', 0):,.2f}",
            ]
        ]
        inc_table = Table(inc_data)
        inc_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(inc_table)
        story.append(Spacer(1, 12))

    # 4) Capital Gains Transactions (Detailed)
    cg_transactions = report_dict.get("capital_gains_transactions", [])
    if cg_transactions:
        story.append(Paragraph("Capital Gains Transactions (Detailed)", heading_style))

        # We'll define column widths
        col_widths = [
            1.6 * inch,  # Date Sold
            1.6 * inch,  # Date Acquired
            0.7 * inch,  # Asset
            0.9 * inch,  # Amount
            1.0 * inch,  # Cost Basis
            1.0 * inch,  # Proceeds
            1.0 * inch,  # Gain/Loss
            0.7 * inch,  # Holding
        ]

        # Table header
        tx_data = [[
            "Date Sold", "Date Acquired", "Asset", "Amount",
            "Cost Basis", "Proceeds", "Gain/Loss", "Holding"
        ]]

        for tx in cg_transactions:
            # Wrap date_sold + " (multiple lots)" in a Paragraph for word-wrap
            date_sold_para = Paragraph(tx.get("date_sold", ""), wrapped_style)
            date_acq_para  = Paragraph(tx.get("date_acquired", ""), wrapped_style)
            asset = tx.get("asset", "BTC")
            # Convert numeric columns to strings
            amt_str = f"{tx.get('amount', 0):,.8f}"
            cost_str = f"{tx.get('cost', 0):,.2f}"
            proceeds_str = f"{tx.get('proceeds', 0):,.2f}"
            gain_str = f"{tx.get('gain_loss', 0):,.2f}"
            hold_str = tx.get("holding_period", "")

            tx_data.append([
                date_sold_para,
                date_acq_para,
                asset,
                amt_str,
                cost_str,
                proceeds_str,
                gain_str,
                hold_str,
            ])

        cg_table = Table(tx_data, colWidths=col_widths, repeatRows=1)
        cg_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (3, 1), (-2, -1), "RIGHT"),  # Right-align Amount, Cost, Proceeds
            ("VALIGN", (0, 0), (-1, -1), "TOP"),    # top-align wrapped cells
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(cg_table)
        story.append(Spacer(1, 12))

    # 5) Income Transactions (Detailed)
    inc_transactions = report_dict.get("income_transactions", [])
    if inc_transactions:
        story.append(Paragraph("Income Transactions (Detailed)", heading_style))

        inc_col_widths = [
            1.6 * inch,  # Date
            0.7 * inch,  # Asset
            0.9 * inch,  # Amount
            1.0 * inch,  # Value(USD)
            0.8 * inch,  # Type
            2.0 * inch,  # Description
        ]
        inc_data = [[
            "Date", "Asset", "Amount", "Value (USD)", "Type", "Description"
        ]]
        for i_tx in inc_transactions:
            date_p = Paragraph(i_tx.get("date", ""), wrapped_style)
            asset_p = i_tx.get("asset", "BTC")
            amt_str = f"{i_tx.get('amount', 0):,.8f}"
            val_str = f"{i_tx.get('value_usd', 0):,.2f}"
            type_str = i_tx.get("type", "")
            desc_para = Paragraph(i_tx.get("description", ""), wrapped_style)

            inc_data.append([
                date_p,
                asset_p,
                amt_str,
                val_str,
                type_str,
                desc_para,
            ])
        inc_table = Table(inc_data, colWidths=inc_col_widths, repeatRows=1)
        inc_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (2, 1), (3, -1), "RIGHT"),  # Amount & Value right-aligned
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(inc_table)

        # Less space before next section
        story.append(Spacer(1, 8))

    # 6) End-of-Year Holdings
    eoy_balances = report_dict.get("end_of_year_balances", [])
    if eoy_balances:
        story.append(Paragraph("End of Year Holdings", heading_style))

        eoy_col_widths = [
            0.9 * inch,  # Asset
            0.9 * inch,  # Quantity
            1.0 * inch,  # Cost Basis
            1.0 * inch,  # Market Value
            2.3 * inch,  # Description
        ]
        eoy_data = [[
            "Asset", "Quantity", "Cost Basis (USD)", "Market Value (USD)", "Description"
        ]]
        for bal in eoy_balances:
            asset_p = bal.get("asset", "")
            qty_str = f"{bal.get('quantity', 0):,.8f}"
            cost_str = f"{bal.get('cost', 0):,.2f}"
            val_str  = f"{bal.get('value', 0):,.2f}"
            desc_p   = Paragraph(bal.get("description", ""), wrapped_style)

            eoy_data.append([asset_p, qty_str, cost_str, val_str, desc_p])

        eoy_table = Table(eoy_data, colWidths=eoy_col_widths, repeatRows=1)
        eoy_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (1, 1), (3, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(eoy_table)
        story.append(Spacer(1, 12))

    # ----------------------------------------------
    # Finally, build the PDF with custom page callbacks
    # ----------------------------------------------
    doc.build(
        story,
        onFirstPage=on_first_page,
        onLaterPages=on_later_pages
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
