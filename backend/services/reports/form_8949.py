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
from .pdf_utils import flatten_pdf_with_ghostscript

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

        # Determine which box (A/C or D/F) based on holding period + basis_reported_flags
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
    Computes Schedule D totals for proceeds, cost, and gain/loss from the
    given Form8949Row lists (short- and long-term).
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
    Decide which Form 8949 box to use:
    SHORT term => A (basis reported) or C (not reported)
    LONG term  => D (basis reported) or F (not reported)
    """
    hp = (holding_period or "").upper()
    if hp == "SHORT":
        return "A" if basis_reported else "C"
    else:
        return "D" if basis_reported else "F"


def fill_pdf_form(template_path: str, field_data: Dict[str, str]) -> bytes:
    """
    Fills a fillable PDF form with data if /AcroForm is present.
    Sets /NeedAppearances to ensure visibility in Adobe Acrobat.
    Returns the filled PDF as bytes.
    """
    reader = PdfReader(template_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    root_obj = reader.trailer["/Root"]
    has_acroform = "/AcroForm" in root_obj

    if has_acroform:
        # Fill fields on page 0 only—if you have multiple pages, you can adapt as needed
        writer.update_page_form_field_values(writer.pages[0], field_data)

        writer._root_object.update({NameObject("/AcroForm"): root_obj["/AcroForm"]})
        writer._root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): BooleanObject(True)
        })

    output_buf = io.BytesIO()
    writer.write(output_buf)
    return output_buf.getvalue()


def map_8949_rows_to_field_data(rows: List[Form8949Row], page: int = 1) -> Dict[str, str]:
    """
    Maps up to 14 Form8949Row objects => the official 8949 field names discovered.
    Each page uses a prefix "f1_" on Page 1, "f2_" on Page 2, etc.
    For row i, the fields go from f1_(3 + 8*(i-1)) through f1_(10 + 8*(i-1)).

    Example: Page 1, Row 1 => f1_3..f1_10
             Page 1, Row 2 => f1_11..f1_18
             ...
             Page 2, Row 1 => f2_3..f2_10
    """
    if len(rows) > 14:
        raise ValueError("Cannot fit more than 14 rows on one Form 8949 page")

    # The subform prefix: topmostSubform[0].Page1[0]... or Page2[0], etc.
    page_prefix = f"Page{page}[0]"  # e.g., "Page1[0]" or "Page2[0]"
    # The field name prefix for the columns: "f1_" if page=1, "f2_" if page=2, etc.
    field_prefix = f"f{page}_"      # e.g., "f1_" or "f2_"

    # The form structure for line entries on each page:
    # "topmostSubform[0].Page1[0].Table_Line1[0].Row{i}[0].f1_XX[0]"
    field_data = {}
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
        # The row number in the PDF (Row1[0], Row2[0], etc.)
        row_subform = f"Row{i}[0]"
        # The base offset for this row is 3 + (i-1)*8
        base_index = 3 + (i - 1) * 8

        for col_idx, key in enumerate(columns):
            if key:  # skip if it's the blank columns (F/G)
                # e.g. for row=1, col_idx=0 => field_num=3 => f1_3 => Column A
                field_num = base_index + col_idx
                pdf_field = (
                    f"topmostSubform[0].{page_prefix}.Table_Line1[0].{row_subform}."
                    f"{field_prefix}{field_num}[0]"
                )
                field_data[pdf_field] = str(row_dict[key])

        # 🔍 DEBUG OUTPUT
        print("FIELD DATA (Form 8949 Page", page, ")")
        for k, v in field_data.items():
            print(f"{k} = {v}")

    return field_data


def map_schedule_d_fields(schedule_d: Dict[str, Dict[str, Decimal]]) -> Dict[str, str]:
    """
    Maps short-term (line 1b) and long-term (line 8b) totals onto Schedule D fields.
    Discovered from your script:
      - Row1b => f1_07[0], f1_08[0], f1_09[0], f1_10[0]
      - Row8b => f1_27[0], f1_28[0], f1_29[0], f1_30[0]
    (If you have codes in the 'Adjustment' column, place them in f1_09[0]/f1_29[0].)
    """
    # Example usage: schedule_d["short_term"]["proceeds"] => ...
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
        # f1_09[0] => Code or adjustment, if any. If none, leave blank:
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_09[0]": "",
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_10[0]": str(short_gain),

        # Long-term: line 8b
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_27[0]": str(long_proceeds),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_28[0]": str(long_cost),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_29[0]": "",
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_30[0]": str(long_gain),
    }

# HELPER: Flatten a filled 8949 page so it's visible everywhere
from .pdf_utils import flatten_pdf_with_ghostscript
