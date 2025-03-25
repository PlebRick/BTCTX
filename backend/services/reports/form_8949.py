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

# -----------------------------------------------------------------------------
# (DEPRECATED) Old Ghostscript flatten import - removed
# -----------------------------------------------------------------------------
# from .pdf_utils import flatten_pdf_with_ghostscript
# -----------------------------------------------------------------------------
# If needed, import fill_pdf_with_pdftk or flatten_pdf_with_pdftk from pdftk_filler or pdf_utils:
# from .pdftk_filler import fill_pdf_with_pdftk
# -----------------------------------------------------------------------------

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
    def _round(amount: Decimal) -> Decimal:
        return amount.quantize(CURRENCY_PLACES, rounding=ROUND_HALF_UP)


def build_form_8949_and_schedule_d(
    year: int,
    db: Session,
    basis_reported_flags: Optional[Dict[int, bool]] = None
) -> Dict:
    """
    Collects all LotDisposal records for the specified tax year (based on transaction.timestamp),
    separates them into short- and long-term groups, and returns Form 8949 rows + Schedule D summary.

    Returned dict example:
    {
      "short_term": [ {...}, {...}, ... ],
      "long_term": [ {...}, {...}, ... ],
      "schedule_d": {
        "short_term": {...},
        "long_term": {...}
      }
    }
    """
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)

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
                f"LotDisposal ID={disp.id} missing associated BitcoinLot or acquired_date."
            )

        # basis_reported: If the user flagged this disposal as basis reported
        basis_reported = basis_reported_flags.get(disp.id, False) if basis_reported_flags else False
        box = _determine_box(disp.holding_period, basis_reported)

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

        # Short- vs. Long-Term
        if (disp.holding_period or "").upper() == "SHORT":
            rows_short.append(row)
        else:
            rows_long.append(row)

    # Build totals for Schedule D
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
    Computes Schedule D totals from the short_rows and long_rows.
    Each row is a Form8949Row that has proceeds, cost, gain_loss.
    """
    st_proceeds = sum((r.proceeds for r in short_rows), Decimal("0.0"))
    st_cost = sum((r.cost for r in short_rows), Decimal("0.0"))
    st_gain = sum((r.gain_loss for r in short_rows), Decimal("0.0"))

    lt_proceeds = sum((r.proceeds for r in long_rows), Decimal("0.0"))
    lt_cost = sum((r.cost for r in long_rows), Decimal("0.0"))
    lt_gain = sum((r.gain_loss for r in long_rows), Decimal("0.0"))

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
    Decide which 8949 box to use:
      SHORT => A (basis reported) or C (not reported)
      LONG  => D (basis reported) or F (not reported)
    """
    hp = (holding_period or "").upper()
    if hp == "SHORT":
        return "A" if basis_reported else "C"
    else:
        return "D" if basis_reported else "F"


# -----------------------------------------------------------------------------
# DEPRECATED pypdf-based fill method
# -----------------------------------------------------------------------------
def fill_pdf_form(template_path: str, field_data: Dict[str, str]) -> bytes:
    """
    (DEPRECATED) Fill a PDF using pypdf if it has AcroForm fields. 
    This won't work for XFA forms (like IRS forms).
    Keeping it for any strictly AcroForm-based PDFs that might come along.
    """
    reader = PdfReader(template_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    root_obj = reader.trailer.get("/Root", {})
    if "/AcroForm" in root_obj:
        acroform = root_obj["/AcroForm"]
        writer._root_object.update({NameObject("/AcroForm"): acroform})
        writer._root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): BooleanObject(True)
        })
        writer.update_page_form_field_values(writer.pages[0], field_data)

    output_buf = io.BytesIO()
    writer.write(output_buf)
    return output_buf.getvalue()


def map_8949_rows_to_field_data(rows: List[Form8949Row], page: int = 1) -> Dict[str, str]:
    """
    Creates a dictionary of {pdfFieldName: value} for up to 14 rows 
    on a single 8949 page. You then pass this dict to your filler 
    (pdftk or pypdf) to insert data into the PDF form fields.

    If you have more than 14 lines, you need multiple 8949 pages 
    (page=1 => "f1_", page=2 => "f2_", etc.).
    """
    if len(rows) > 14:
        raise ValueError("Cannot fit more than 14 rows on one Form 8949 page")

    page_prefix = f"Page{page}[0]"      # e.g., "Page1[0]" or "Page2[0]"
    field_prefix = f"f{page}_"          # e.g., "f1_" or "f2_"
    field_data = {}

    # These columns correspond to columns A through H, skipping F/G
    columns = [
        "description",      # Column A
        "date_acquired",    # Column B
        "date_sold",        # Column C
        "proceeds",         # Column D
        "cost",             # Column E
        "",                 # Column F (unused code)
        "",                 # Column G (unused adjustment)
        "gain_loss"         # Column H
    ]

    for i, row in enumerate(rows, start=1):
        row_dict = row.to_dict()

        # e.g. Row1[0], Row2[0], etc.
        row_subform = f"Row{i}[0]"
        # Base offset for row i => 3 + (i-1)*8
        base_index = 3 + (i - 1) * 8

        for col_idx, key in enumerate(columns):
            if key:
                field_num = base_index + col_idx
                pdf_field = (
                    f"topmostSubform[0].{page_prefix}.Table_Line1[0].{row_subform}."
                    f"{field_prefix}{field_num}[0]"
                )
                field_data[pdf_field] = str(row_dict[key])

        # Debug print
        print(f"[DEBUG] 8949 Page={page}, Row={i} => fields:")
        for k, v in field_data.items():
            print(f"  {k} = {v}")

    return field_data


def map_schedule_d_fields(schedule_d: Dict[str, Dict[str, Decimal]]) -> Dict[str, str]:
    """
    Maps short-term (line 1b) and long-term (line 8b) totals onto Schedule D fields.
    Example fields discovered:
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
        # Short-term line 1b
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_07[0]": str(short_proceeds),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_08[0]": str(short_cost),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_09[0]": "",
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_10[0]": str(short_gain),

        # Long-term line 8b
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_27[0]": str(long_proceeds),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_28[0]": str(long_cost),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_29[0]": "",
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_30[0]": str(long_gain),
    }


# -----------------------------------------------------------------------------
# Best Practice: Use fill_pdf_with_pdftk(...) if you have XFA-based IRS forms.
#
# Merging partial PDFs is usually done at a higher level (e.g., in /irs_reports)
# where you chunk 14 rows per 8949 page. You can merge them with pypdf if they
# are flattened or with pdftk. Either approach is fine if each chunk is flattened.
# -----------------------------------------------------------------------------
