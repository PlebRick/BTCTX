# FILE: backend/services/reports/form_8949.py

"""
Builds Form 8949 and Schedule D data structures from LotDisposal records.
Incorporates:
 1) Box classification logic (A-F) based on placeholders or real 1099-B flags
 2) Rounding via Decimal.quantize(..., rounding=ROUND_HALF_UP)
 3) UTC-aware date/time usage
 4) Acquisition date checks
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Literal, Optional

from sqlalchemy.orm import Session

from backend.models import LotDisposal

# For actual "away from zero" rounding on typical currency fields
CURRENCY_PLACES = Decimal("0.01")


class Form8949Row:
    """
    Represents a single line on Form 8949:
      - description (e.g. "0.05 BTC (acquired 2023-02-01)")
      - date acquired
      - date sold
      - proceeds, cost, net gain/loss
      - holding_period: "SHORT" or "LONG"
      - box: A-F (determined by 1099-B status or manual basis reporting)

    By default, short-term = Box C, long-term = Box F,
    but see _determine_box(...) for how to override.
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
        self.proceeds = proceeds
        self.cost = cost
        self.gain_loss = gain_loss
        self.holding_period = holding_period
        self.box = box

    def to_dict(self) -> Dict:
        """
        Returns the row as a dictionary for JSON or PDF form filling.
        Uses Decimal.quantize(..., rounding=ROUND_HALF_UP) to ensure
        "away from zero" behavior for tax purposes.
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
        """
        Helper for "away from zero" rounding to two decimal places, typical for IRS forms.
        """
        return amount.quantize(CURRENCY_PLACES, rounding=ROUND_HALF_UP)


def build_form_8949_and_schedule_d(
    year: int,
    db: Session,
    basis_reported_flags: Optional[Dict[int, bool]] = None
) -> Dict:
    """
    Generates Form 8949 and Schedule D data for the specified tax year.
    
    :param year: Tax year (e.g. 2024)
    :param db: SQLAlchemy Session
    :param basis_reported_flags:
        Optional mapping of disposal IDs -> bool indicating if basis was reported
        to the IRS on a 1099-B. If omitted or not found, defaults to "not reported."
        For instance: { disposal_id: True/False }.
    
    Return example:
    {
        "short_term": [ {...}, ... ],
        "long_term":  [ {...}, ... ],
        "schedule_d": {
            "short_term": { "proceeds": ..., "cost": ..., "gain_loss": ... },
            "long_term":  { "proceeds": ..., "cost": ..., "gain_loss": ... }
        }
    }
    """
    # 1) Define the date range in UTC
    #    (If your DB times are UTC, you should ensure each disposal.timestamp is also UTC.)
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)

    # 2) Query all disposals in that year
    disposals = (
        db.query(LotDisposal)
        .filter(
            LotDisposal.timestamp >= start_date,
            LotDisposal.timestamp < end_date
        )
        .all()
    )

    rows_short: List[Form8949Row] = []
    rows_long: List[Form8949Row] = []

    # 3) Build row objects
    for disp in disposals:
        # (A) Confirm we have an acquired_date
        if not disp.acquired_date:
            # You might raise an error or set a placeholder:
            raise ValueError(f"Disposal ID {disp.id} is missing an acquired_date.")

        # (B) Determine default Box
        #     If basis was reported, e.g. short-term => "A", long-term => "D"
        #     If not reported, short-term => "B" or "C", long-term => "E" or "F"
        #     This logic is flexible; you can do it however your CPAs recommend.
        basis_reported = False
        if basis_reported_flags and disp.id in basis_reported_flags:
            basis_reported = basis_reported_flags[disp.id]

        box = _determine_box(
            holding_period=disp.holding_period,
            basis_reported=basis_reported
        )

        # (C) Build a user-friendly description
        #     e.g. "0.05 BTC (acquired 2023-02-01)"
        disposed_btc_str = str(disp.disposed_btc)
        acquired_str = disp.acquired_date.date().isoformat()
        descr = f"{disposed_btc_str} BTC (acquired {acquired_str})"

        # (D) Create row
        row = Form8949Row(
            description=descr,
            date_acquired=acquired_str,
            date_sold=disp.timestamp.date().isoformat(),
            proceeds=disp.proceeds_usd_for_that_portion or Decimal("0"),
            cost=disp.disposal_basis_usd or Decimal("0"),
            gain_loss=disp.realized_gain_usd or Decimal("0"),
            holding_period=disp.holding_period,
            box=box
        )

        # (E) Append to short-term or long-term list
        if disp.holding_period == "SHORT":
            rows_short.append(row)
        else:
            rows_long.append(row)

    # 4) Aggregate totals for Schedule D
    schedule_d_data = _build_schedule_d_data(rows_short, rows_long)

    # 5) Return final dictionary
    return {
        "short_term": [r.to_dict() for r in rows_short],
        "long_term": [r.to_dict() for r in rows_long],
        "schedule_d": schedule_d_data
    }


def _build_schedule_d_data(
    short_rows: List[Form8949Row],
    long_rows: List[Form8949Row]
) -> Dict[str, Dict[str, Decimal]]:
    """
    Sums proceeds, cost, and gain_loss from short_rows and long_rows.
    Uses round-away-from-zero for final results.
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


def _determine_box(holding_period: str, basis_reported: bool) -> Literal["A", "B", "C", "D", "E", "F"]:
    """
    Simple helper to decide the correct Box (A-F) based on whether
    cost basis was reported on 1099-B and whether it's short or long term.

    Actual rules vary, but here's a plausible approach:
      - Short-term, basis reported => Box A
      - Short-term, basis not reported => Box B or C (choose one)
      - Long-term, basis reported => Box D
      - Long-term, basis not reported => Box E or F (choose one)
    """
    hp_upper = (holding_period or "").upper()
    if hp_upper == "SHORT":
        if basis_reported:
            return "A"
        else:
            return "C"  # or "B", depending on your reporting approach
    else:
        # LONG
        if basis_reported:
            return "D"
        else:
            return "F"  # or "E", depending on your reporting approach
