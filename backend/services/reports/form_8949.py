# FILE: backend/services/reports/form_8949.py

import io
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Literal, Optional

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject
from sqlalchemy.orm import Session

from backend.models import LotDisposal
from backend.models.transaction import Transaction

CURRENCY_PLACES = Decimal("0.01")


class Form8949Row:
    """
    Represents a single row on IRS Form 8949.
    Includes date acquired, date sold, proceeds, cost basis, gain/loss,
    holding period, and box code (A–F).

    Monetary values are stored as Decimal and rounded using HALF_UP
    to meet IRS requirements.
    """

    def __init__(
        self,
        description: str,
        date_acquired: str,
        date_sold: str,
        proceeds: Decimal,
        cost: Decimal,
        gain_loss: Decimal,
        holding_period: Literal["SHORT", "LONG"],
        box: Literal["A", "B", "C", "D", "E", "F"]
    ):
        self.description = description
        self.date_acquired = date_acquired
        self.date_sold = date_sold
        self.proceeds = Decimal(proceeds)
        self.cost = Decimal(cost)
        self.gain_loss = Decimal(gain_loss)
        self.holding_period = holding_period
        self.box = box

    def to_dict(self) -> Dict:
        """
        Convert the row into a dictionary, rounding numeric fields.
        Used to map to PDF or CSV exports.
        """
        return {
            "description": self.description,
            "date_acquired": self.date_acquired,
            "date_sold": self.date_sold,
            "proceeds": self._round(self.proceeds),
            "cost": self._round(self.cost),
            "gain_loss": self._round(self.gain_loss),
            "holding_period": self.holding_period,
            "box": self.box
        }

    @staticmethod
    def _round(amount) -> Decimal:
        return Decimal(amount).quantize(CURRENCY_PLACES, rounding=ROUND_HALF_UP)


def build_form_8949_and_schedule_d(
    year: int,
    db: Session,
    basis_reported_flags: Optional[Dict[int, bool]] = None
) -> Dict:
    """
    Collects all LotDisposal records for the specified tax year (based on transaction.timestamp),
    separates them into short- and long-term groups, and returns Form 8949 rows + Schedule D summary.

    The returned dict typically looks like:
    {
      "short_term": [...],  # each item is a row dict
      "long_term": [...],
      "schedule_d": {
        "short_term": { "proceeds": ..., "cost": ..., "gain_loss": ... },
        "long_term":  { "proceeds": ..., "cost": ..., "gain_loss": ... }
      }
    }
    """
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)

    # Query all relevant disposals for that tax year
    disposals = (
        db.query(LotDisposal)
        .join(LotDisposal.transaction)
        .join(LotDisposal.lot)
        .filter(
            Transaction.timestamp >= start_date,
            Transaction.timestamp < end_date
        )
        .all()
    )

    rows_short: List[Form8949Row] = []
    rows_long: List[Form8949Row] = []

    for disp in disposals:
        if not disp.lot or not disp.lot.acquired_date:
            raise ValueError(
                f"LotDisposal ID={disp.id} is missing an associated BitcoinLot or acquired_date."
            )

        # 'basis_reported' determines if we use box A/C or D/F
        is_basis_reported = basis_reported_flags.get(disp.id, False) if basis_reported_flags else False
        box = _determine_box(disp.holding_period, is_basis_reported)

        acquired_str = disp.lot.acquired_date.date().isoformat()
        sold_date = disp.transaction.timestamp.date().isoformat()

        proceeds_dec = Decimal(disp.proceeds_usd_for_that_portion or 0)
        cost_dec = Decimal(disp.disposal_basis_usd or 0)
        gain_dec = Decimal(disp.realized_gain_usd or 0)

        row = Form8949Row(
            description=f"{disp.disposed_btc} BTC (acquired {acquired_str})",
            date_acquired=acquired_str,
            date_sold=sold_date,
            proceeds=proceeds_dec,
            cost=cost_dec,
            gain_loss=gain_dec,
            holding_period=disp.holding_period,
            box=box
        )

        # Split into short-term vs long-term
        if (disp.holding_period or "").upper() == "SHORT":
            rows_short.append(row)
        else:
            rows_long.append(row)

    # Build aggregated totals for Schedule D
    schedule_d = _build_schedule_d_data(rows_short, rows_long)

    return {
        "short_term": [r.to_dict() for r in rows_short],
        "long_term": [r.to_dict() for r in rows_long],
        "schedule_d": schedule_d
    }


def _build_schedule_d_data(
    short_rows: List[Form8949Row],
    long_rows: List[Form8949Row]
) -> Dict[str, Dict[str, Decimal]]:
    """
    Computes Schedule D totals for short- and long-term dispositions.
    Summarizes proceeds, cost, and gain/loss.
    """
    st_proceeds = sum(r.proceeds for r in short_rows)
    st_cost = sum(r.cost for r in short_rows)
    st_gain = sum(r.gain_loss for r in short_rows)

    lt_proceeds = sum(r.proceeds for r in long_rows)
    lt_cost = sum(r.cost for r in long_rows)
    lt_gain = sum(r.gain_loss for r in long_rows)

    # Round using the same method as Form8949Row
    return {
        "short_term": {
            "proceeds": Form8949Row._round(st_proceeds),
            "cost": Form8949Row._round(st_cost),
            "gain_loss": Form8949Row._round(st_gain),
        },
        "long_term": {
            "proceeds": Form8949Row._round(lt_proceeds),
            "cost": Form8949Row._round(lt_cost),
            "gain_loss": Form8949Row._round(lt_gain),
        }
    }


def _determine_box(holding_period: str, basis_reported: bool) -> Literal["A", "B", "C", "D", "E", "F"]:
    """
    Decides which box on Form 8949 to use:
      SHORT => A (basis reported) or C (not reported)
      LONG  => D (basis reported) or F (not reported)
    """
    hp = (holding_period or "").upper()
    if hp == "SHORT":
        return "A" if basis_reported else "C"
    else:
        return "D" if basis_reported else "F"


# -----------------------------------------------------------------------------
# (DEPRECATED) pypdf-based fill method for strictly AcroForm PDFs
# -----------------------------------------------------------------------------
def fill_pdf_form(template_path: str, field_data: Dict[str, str]) -> bytes:
    """
    (DEPRECATED) Fills an AcroForm PDF using pypdf. 
    This won't handle XFA forms (typical IRS forms). 
    Retaining for potential fallback if we ever see a pure AcroForm.
    """
    reader = PdfReader(template_path)
    writer = PdfWriter()

    # Copy all pages to the new writer
    for page in reader.pages:
        writer.add_page(page)

    # If there's an AcroForm, set NeedAppearances and fill page 0
    root_obj = reader.trailer.get("/Root", {})
    if "/AcroForm" in root_obj:
        acroform = root_obj["/AcroForm"]
        writer._root_object.update({NameObject("/AcroForm"): acroform})
        writer._root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): BooleanObject(True)
        })
        # Fill fields on page 0
        writer.update_page_form_field_values(writer.pages[0], field_data)

    output_buf = io.BytesIO()
    writer.write(output_buf)
    return output_buf.getvalue()


def map_8949_rows_to_field_data(rows: List[Form8949Row], page: int = 1) -> Dict[str, str]:
    """
    Creates a dictionary of {pdfFieldName: value} for up to 14 Form8949Row 
    objects on a single 8949 page. If more than 14 rows, you'll need additional pages.

    Usage:
      1) For short-term rows (<=14), call map_8949_rows_to_field_data(rows, page=1).
      2) For next 14, page=2 => "f2_..." field names, etc.
      3) Fill the PDF with fill_pdf_with_pdftk(...) or fill_pdf_form(...).
    """
    if len(rows) > 14:
        raise ValueError("Cannot fit more than 14 rows on one Form 8949 page")

    page_prefix = f"Page{page}[0]"  # e.g., "Page1[0]" or "Page2[0]"
    field_prefix = f"f{page}_"      # e.g., "f1_" or "f2_"
    field_data = {}

    # The standard columns A–H, skipping columns F and G
    columns = [
        "description",      # Column A
        "date_acquired",    # Column B
        "date_sold",        # Column C
        "proceeds",         # Column D
        "cost",             # Column E
        "",                 # Column F (unused)
        "",                 # Column G (unused)
        "gain_loss"         # Column H
    ]

    for i, row in enumerate(rows, start=1):
        row_dict = row.to_dict()
        row_subform = f"Row{i}[0]"
        base_index = 3 + (i - 1) * 8

        for col_idx, key in enumerate(columns):
            if key:
                field_num = base_index + col_idx
                pdf_field = (
                    f"topmostSubform[0].{page_prefix}.Table_Line1[0].{row_subform}."
                    f"{field_prefix}{field_num}[0]"
                )
                field_data[pdf_field] = str(row_dict[key])

        # Optional debug print
        print(f"[DEBUG] 8949 Page={page}, Row={i} => fields:")
        for k, v in field_data.items():
            print(f"  {k} = {v}")

    return field_data


def map_schedule_d_fields(schedule_d: Dict[str, Dict[str, Decimal]]) -> Dict[str, str]:
    """
    Maps short-term (line 1b) and long-term (line 8b) totals onto the 
    known Schedule D fields:
      - Row1b => f1_07[0], f1_08[0], f1_09[0], f1_10[0]
      - Row8b => f1_27[0], f1_28[0], f1_29[0], f1_30[0]

    If you have codes in the 'Adjustment' column, place them in f1_09[0] or f1_29[0].
    """
    short_proceeds = schedule_d["short_term"]["proceeds"]
    short_cost = schedule_d["short_term"]["cost"]
    short_gain = schedule_d["short_term"]["gain_loss"]

    long_proceeds = schedule_d["long_term"]["proceeds"]
    long_cost = schedule_d["long_term"]["cost"]
    long_gain = schedule_d["long_term"]["gain_loss"]

    return {
        # Short-term: line 1b
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_07[0]": str(short_proceeds),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_08[0]": str(short_cost),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_09[0]": "",
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_10[0]": str(short_gain),

        # Long-term: line 8b
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_27[0]": str(long_proceeds),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_28[0]": str(long_cost),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_29[0]": "",
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_30[0]": str(long_gain),
    }


# -----------------------------------------------------------------------------
# Best Practice:
# For XFA-based IRS forms, use fill_pdf_with_pdftk(...) from pdftk_filler.py,
# which can drop_xfa and flatten. Then if you have multiple partial PDFs
# (14 rows per page, etc.), merge them in memory with pypdf or using pdftk.
# -----------------------------------------------------------------------------
