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
    """ Same as before, with numeric fields in Decimal. """

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

def build_form_8949_and_schedule_d(year: int, db: Session, basis_reported_flags: Optional[Dict[int, bool]] = None) -> Dict:
    """
    Same as before: joins transaction, filters by transaction.timestamp, etc.
    """
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)

    disposals = (
        db.query(LotDisposal)
        .join(Transaction, Transaction.id == LotDisposal.transaction_id)
        .filter(
            Transaction.timestamp >= start_date,
            Transaction.timestamp < end_date
        )
        .all()
    )

    rows_short: List[Form8949Row] = []
    rows_long: List[Form8949Row] = []

    for disp in disposals:
        if not disp.acquired_date:
            raise ValueError(f"LotDisposal ID={disp.id} missing acquired_date.")

        basis_reported = basis_reported_flags.get(disp.id, False) if basis_reported_flags else False
        box = _determine_box(disp.holding_period, basis_reported)

        acquired_str = disp.acquired_date.date().isoformat()
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

        if disp.holding_period.upper() == "SHORT":
            rows_short.append(row)
        else:
            rows_long.append(row)

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
    Summation. We know these are already Decimals from the constructor.
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
    hp = (holding_period or "").upper()
    if hp == "SHORT":
        return "A" if basis_reported else "C"
    else:
        return "D" if basis_reported else "F"

def fill_pdf_form(template_path: str, field_data: Dict[str, str]) -> bytes:
    """
    Safely fills a fillable PDF if it has an /AcroForm. If not, we skip form update.
    """
    reader = PdfReader(template_path)
    writer = PdfWriter()

    # Copy pages from the original
    for page in reader.pages:
        writer.add_page(page)

    # Check if PDF has /AcroForm
    root_obj = reader.trailer["/Root"]
    has_acroform = ("/AcroForm" in root_obj)

    if has_acroform:
        # If the PDF is actually fillable, update fields on first page
        writer.update_page_form_field_values(writer.pages[0], field_data)

        # Set /NeedAppearances so typed text is visible
        writer._root_object.update({
            NameObject("/AcroForm"): root_obj["/AcroForm"]
        })
        writer._root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): BooleanObject(True)
        })
    else:
        # If there's no AcroForm, skip. This avoids PyPdfError.
        pass

    output_buf = io.BytesIO()
    writer.write(output_buf)
    return output_buf.getvalue()


def map_8949_rows_to_field_data(rows: List[Form8949Row], page: int = 1) -> Dict[str, str]:
    """
    Maps up to 14 Form8949Row objects => 8949 field names discovered by debug script.
    """
    if len(rows) > 14:
        raise ValueError("Cannot fit more than 14 rows on one 8949 page")

    prefix = f"topmostSubform[0].Page{page}[0].Table_Line1[0].Row"
    field_data = {}
    columns = [
        "description",      # A
        "date_acquired",    # B
        "date_sold",        # C
        "proceeds",         # D
        "cost",             # E
        "",                 # F (unused code)
        "",                 # G (unused adjustment)
        "gain_loss"         # H
    ]

    for i, row in enumerate(rows):
        row_dict = row.to_dict()
        for col_idx, key in enumerate(columns):
            field_num = (page - 1) * 117 + 3 + i * 8 + col_idx
            pdf_field = f"{prefix}{i+1}[0].f{field_num}[0]"
            field_data[pdf_field] = str(row_dict[key]) if key else ""

    return field_data
