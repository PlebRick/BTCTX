# FILE: backend/services/reports/form_8949.py

import io
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Literal, Optional
from sqlalchemy.orm import Session

from pypdf import PdfReader, PdfWriter
from io import BytesIO

from backend.models import LotDisposal
from backend.models.transaction import Transaction
from backend.services.reports.pdftk_filler import fill_pdf_with_pdftk
from backend.services.reports.pdf_utils import flatten_pdf_with_pdftk
from pypdf import PdfReader, PdfWriter


##############################################################################
# 1) FORM 8949 ROW DEFINITION
##############################################################################
CURRENCY_PLACES = Decimal("0.01")

class Form8949Row:
    """
    Represents a single row on IRS Form 8949 (one line).
    (a) Description of property
    (b) Date acquired
    (c) Date sold
    (d) proceeds
    (e) cost
    (f) code (if any) or basis status
    (g) adjustment
    (h) gain/loss
    """
    def __init__(
        self,
        description: str,           # col (a)
        date_acquired: str,         # col (b)
        date_sold: str,             # col (c)
        proceeds: Decimal,          # col (d)
        cost: Decimal,              # col (e)
        gain_loss: Decimal,         # col (h)
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
        # For columns (f) and (g) (code & adjustment), we might not store them if your code
        # doesn’t require adjustments. If you do, you can expand below.

    def to_dict(self) -> Dict:
        """Convert to a dictionary with final, rounded decimal amounts."""
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


##############################################################################
# 2) BUILDING 8949 DATA FROM DB
##############################################################################
def build_form_8949_and_schedule_d(
    year: int,
    db: Session,
    basis_reported_flags: Optional[Dict[int, bool]] = None
) -> Dict:
    """
    Gathers all LotDisposals for the given tax year, separates short vs. long,
    and returns a dict for your get_irs_reports route:

    {
      "short_term": [...row dicts...],
      "long_term":  [...row dicts...],
      "schedule_d": {
         "short_term": {"proceeds":..., "cost":..., "gain_loss":...},
         "long_term":  {"proceeds":..., "cost":..., "gain_loss":...}
      }
    }
    """
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)

    disposals = (
        db.query(LotDisposal)
          .join(LotDisposal.transaction)
          .filter(Transaction.timestamp >= start_date, Transaction.timestamp < end_date)
          .all()
    )

    rows_short: List[Form8949Row] = []
    rows_long: List[Form8949Row] = []

    for disp in disposals:
        # If you do basis_reported_flags => A or C (short), D or F (long)
        is_basis_reported = False
        if basis_reported_flags and disp.id in basis_reported_flags:
            is_basis_reported = basis_reported_flags[disp.id]

        # Decide box letter
        box = _determine_box(disp.holding_period, is_basis_reported)

        # Format date_acquired
        if disp.lot and disp.lot.acquired_date:
            acquired_str = disp.lot.acquired_date.strftime("%m/%d/%Y")
        else:
            acquired_str = ""

        # date_sold
        sold_str = ""
        if disp.transaction and disp.transaction.timestamp:
            sold_str = disp.transaction.timestamp.strftime("%m/%d/%Y")

        # parse amounts
        proceeds_dec = Decimal(disp.proceeds_usd_for_that_portion or 0)
        cost_dec = Decimal(disp.disposal_basis_usd or 0)
        gain_dec = Decimal(disp.realized_gain_usd or 0)
        hp_str = (disp.holding_period or "SHORT").upper()

        row = Form8949Row(
            description=f"{disp.disposed_btc} BTC",
            date_acquired=acquired_str,
            date_sold=sold_str,
            proceeds=proceeds_dec,
            cost=cost_dec,
            gain_loss=gain_dec,
            holding_period=hp_str,
            box=box
        )

        if hp_str == "LONG":
            rows_long.append(row)
        else:
            rows_short.append(row)

    # Summaries for schedule D lines
    schedule_d = _build_schedule_d_data(rows_short, rows_long)

    return {
        "short_term": [r.to_dict() for r in rows_short],
        "long_term":  [r.to_dict() for r in rows_long],
        "schedule_d": schedule_d
    }


def _determine_box(holding_period: str, basis_reported: bool) -> Literal["A", "B", "C", "D", "E", "F"]:
    """
    short => A (if basis reported) or C (if not)
    long => D (if basis reported) or F (if not)
    """
    hp = holding_period.upper()
    if hp == "LONG":
        return "D" if basis_reported else "F"
    return "A" if basis_reported else "C"


def _build_schedule_d_data(short_rows: List[Form8949Row], long_rows: List[Form8949Row]) -> Dict[str, Dict[str, Decimal]]:
    """
    Summarize short vs. long for schedule D lines 1b & 8b.
    """
    st_proceeds = sum(r.proceeds for r in short_rows)
    st_cost = sum(r.cost for r in short_rows)
    st_gain = sum(r.gain_loss for r in short_rows)

    lt_proceeds = sum(r.proceeds for r in long_rows)
    lt_cost = sum(r.cost for r in long_rows)
    lt_gain = sum(r.gain_loss for r in long_rows)

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


##############################################################################
# 3) FIELD-MAPPING HELPERS
##############################################################################
def map_8949_rows_to_field_data(rows: List[Form8949Row], page: int = 1) -> Dict[str, str]:
    """
    Fills up to 14 lines on a single Form 8949 page, matching official field naming
    like:
      Row1 => f1_3..f1_10,
      Row2 => f1_11..f1_18, etc.
    If page=2 => you might use "f2_3..f2_10" etc.
    """
    if len(rows) > 14:
        raise ValueError("Cannot fit more than 14 rows on one page")

    # if your PDF uses Page1 => f1_..., Page2 => f2_...
    # let's build that prefix:
    # e.g. page=1 => "f1_", page=2 => "f2_"
    prefix_num = 1 if page == 1 else 2
    prefix = f"f{prefix_num}_"

    # Also, the PDF structure might require something like:
    # "topmostSubform[0].Page1[0].Table_Line1[0].Row1[0].f1_3[0]"
    # We'll combine them in a final string below.

    # For row i => the base field index is (3 + (i-1)*8).
    # col (a) => offset 0 => f1_(base_index + 0)
    # col (b) => offset 1
    # ...
    # col (h) => offset 7
    # So the "field number" = base_index + offset.
    #
    # Then we append "[0]" at the end.

    field_data: Dict[str, str] = {}

    for i, row_obj in enumerate(rows, start=1):
        # row1 => base=3, row2 => base=11, row3 => base=19, etc.
        base_index = 3 + (i - 1) * 8

        # We'll handle columns (a)–(h). If you want columns (f) & (g) for code/adj,
        # you'd expand the logic. For now let's do:
        #   col (a)=description => offset=0
        #   col (b)=date_acq => offset=1
        #   col (c)=date_sold => offset=2
        #   col (d)=proceeds => offset=3
        #   col (e)=cost => offset=4
        #   col (f)=??? -> skip or store row_obj.box
        #   col (g)=??? -> skip if no adjustments
        #   col (h)=gain_loss => offset=7

        # field => topmostSubform[0].Page{prefix_num}[0].Table_Line1[0].Row{i}[0].f1_{field_num}[0]
        # let's define a helper function
        def field_name(row_i: int, field_no: int) -> str:
            return (
                f"topmostSubform[0].Page{prefix_num}[0].Table_Line1[0].Row{row_i}[0].{prefix}{field_no}[0]"
            )

        # col (a) => offset=0 => field # = base_index+0
        col_a = field_name(i, base_index + 0)
        field_data[col_a] = row_obj.description

        # col (b) => offset=1 => date_acquired
        col_b = field_name(i, base_index + 1)
        field_data[col_b] = row_obj.date_acquired

        # col (c) => offset=2 => date_sold
        col_c = field_name(i, base_index + 2)
        field_data[col_c] = row_obj.date_sold

        # col (d) => offset=3 => proceeds
        col_d = field_name(i, base_index + 3)
        field_data[col_d] = str(row_obj.proceeds)

        # col (e) => offset=4 => cost
        col_e = field_name(i, base_index + 4)
        field_data[col_e] = str(row_obj.cost)

        # col (f) => offset=5 => code => you might store row_obj.box here if you want
        # or if your PDF does it differently, skip. We'll store box for demonstration:
        col_f = field_name(i, base_index + 5)
        field_data[col_f] = row_obj.box  # e.g. "A/C" or "D/F"

        # col (g) => offset=6 => adjustment => skip if you don't have it
        col_g = field_name(i, base_index + 6)
        field_data[col_g] = ""  # or row_obj.adjustment if you track it

        # col (h) => offset=7 => gain_loss
        col_h = field_name(i, base_index + 7)
        field_data[col_h] = str(row_obj.gain_loss)

    return field_data


def map_schedule_d_fields(schedule_d: Dict[str, Dict[str, Decimal]]) -> Dict[str, str]:
    """
    Adapts short_term (line 1b) & long_term (line 8b) totals from 'schedule_d'
    to your fillable PDF field naming:

      topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_07[0] => short proceeds
      ...
      topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_27[0] => long proceeds
    """
    short_data = schedule_d["short_term"]
    long_data  = schedule_d["long_term"]

    return {
        # short => line 1b fields
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_07[0]": str(short_data["proceeds"]),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_08[0]": str(short_data["cost"]),
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_09[0]": "",  # adjustments
        "topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_10[0]": str(short_data["gain_loss"]),

        # long => line 8b
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_27[0]": str(long_data["proceeds"]),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_28[0]": str(long_data["cost"]),
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_29[0]": "",
        "topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_30[0]": str(long_data["gain_loss"]),
    }
