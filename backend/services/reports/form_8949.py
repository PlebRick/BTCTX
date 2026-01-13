# FILE: backend/services/reports/form_8949.py

import io
import logging
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

# Set up logging for audit trail
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    # Non-taxable disposal purposes that should NOT appear on Form 8949
    # Gifts, donations, and lost assets are reported separately, not as capital gains/losses
    NON_TAXABLE_PURPOSES = ('Gift', 'Donation', 'Lost')

    disposals = (
        db.query(LotDisposal)
          .join(LotDisposal.transaction)
          .filter(Transaction.timestamp >= start_date, Transaction.timestamp < end_date)
          .filter(
              # Exclude non-taxable disposals (gifts, donations, lost assets)
              # These have a purpose field set; taxable disposals (Sell, Spent, Transfer fees) don't
              (Transaction.purpose.is_(None)) | (~Transaction.purpose.in_(NON_TAXABLE_PURPOSES))
          )
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
# 3) YEAR-SPECIFIC FIELD CONFIGURATION
##############################################################################
def get_8949_field_config(year: int) -> Dict:
    """
    Return year-specific field configuration for Form 8949.

    The IRS changes field names between years. Key differences:
    - 2024: Table_Line1, fields start at f1_3 (not zero-padded)
    - 2025+: Table_Line1_Part1/Part2, fields start at f1_03 (zero-padded for row 1)

    Args:
        year: Tax year (e.g., 2024, 2025)

    Returns:
        Dictionary with field naming configuration
    """
    if year >= 2025:
        return {
            "table_name_page1": "Table_Line1_Part1",
            "table_name_page2": "Table_Line1_Part2",
            "row1_base_index": 3,  # Row 1 starts at field index 3
            "row1_zero_pad": True,  # f1_03, f1_04, ... f1_10
            "row2_plus_zero_pad": False,  # f1_11, f1_12, ... (no padding after row 1)
        }
    else:  # 2024 and earlier
        return {
            "table_name_page1": "Table_Line1",
            "table_name_page2": "Table_Line1",  # Same table name for both pages
            "row1_base_index": 3,
            "row1_zero_pad": False,  # f1_3, f1_4, ...
            "row2_plus_zero_pad": False,
        }


def get_schedule_d_field_config(year: int) -> Dict[str, str]:
    """
    Return year-specific field names for Schedule D.

    IMPORTANT: Self-tracked crypto transactions (not reported on 1099-B/1099-DA) use:
    - Line 3 (Box C or Box I) for short-term
    - Line 10 (Box F or Box L) for long-term

    Key differences by year:
    - 2024: Row3 uses f1_15-f1_18, Row10 uses f1_35-f1_38
    - 2025+: Same field numbers, different structure confirmed

    Args:
        year: Tax year (e.g., 2024, 2025)

    Returns:
        Dictionary mapping field purposes to actual field names
    """
    if year >= 2025:
        return {
            # Short-term (line 3 - Box C/I: not reported on 1099)
            "short_proceeds": "topmostSubform[0].Page1[0].Table_PartI[0].Row3[0].f1_15[0]",
            "short_cost": "topmostSubform[0].Page1[0].Table_PartI[0].Row3[0].f1_16[0]",
            "short_adjustment": "topmostSubform[0].Page1[0].Table_PartI[0].Row3[0].f1_17[0]",
            "short_gain_loss": "topmostSubform[0].Page1[0].Table_PartI[0].Row3[0].f1_18[0]",
            # Long-term (line 10 - Box F/L: not reported on 1099)
            "long_proceeds": "topmostSubform[0].Page1[0].Table_PartII[0].Row10[0].f1_35[0]",
            "long_cost": "topmostSubform[0].Page1[0].Table_PartII[0].Row10[0].f1_36[0]",
            "long_adjustment": "topmostSubform[0].Page1[0].Table_PartII[0].Row10[0].f1_37[0]",
            "long_gain_loss": "topmostSubform[0].Page1[0].Table_PartII[0].Row10[0].f1_38[0]",
        }
    else:  # 2024 and earlier
        return {
            # Short-term (line 3 - Box C: not reported on 1099)
            "short_proceeds": "topmostSubform[0].Page1[0].Table_PartI[0].Row3[0].f1_15[0]",
            "short_cost": "topmostSubform[0].Page1[0].Table_PartI[0].Row3[0].f1_16[0]",
            "short_adjustment": "topmostSubform[0].Page1[0].Table_PartI[0].Row3[0].f1_17[0]",
            "short_gain_loss": "topmostSubform[0].Page1[0].Table_PartI[0].Row3[0].f1_18[0]",
            # Long-term (line 10 - Box F: not reported on 1099)
            "long_proceeds": "topmostSubform[0].Page1[0].Table_PartII[0].Row10[0].f1_35[0]",
            "long_cost": "topmostSubform[0].Page1[0].Table_PartII[0].Row10[0].f1_36[0]",
            "long_adjustment": "topmostSubform[0].Page1[0].Table_PartII[0].Row10[0].f1_37[0]",
            "long_gain_loss": "topmostSubform[0].Page1[0].Table_PartII[0].Row10[0].f1_38[0]",
        }


##############################################################################
# 4) FIELD-MAPPING HELPERS
##############################################################################
def map_8949_rows_to_field_data(rows: List[Form8949Row], page: int = 1, year: int = 2024) -> Dict[str, str]:
    """
    Fills up to 14 lines on a single Form 8949 page, using year-specific field naming.

    Field naming varies by year:
    - 2024: Table_Line1, f1_3, f1_4, ... (not zero-padded)
    - 2025+: Table_Line1_Part1/Part2, f1_03, f1_04, ... (zero-padded for row 1)

    This version supports unlimited pages via dynamic naming:
      page=1 => f1_..., page=2 => f2_..., page=3 => f3_..., etc.

    Args:
        rows: List of Form8949Row objects (max 14 per page)
        page: Page number (1, 2, 3, ...)
        year: Tax year for field name selection

    Returns:
        Dictionary mapping field names to values
    """
    if len(rows) > 14:
        raise ValueError("Cannot fit more than 14 rows on one page")

    # Get year-specific configuration
    config = get_8949_field_config(year)

    # Select table name based on page (Part1 for page 1, Part2 for page 2 in 2025+)
    # For additional pages beyond 2, we use Part1 naming (short-term continuation)
    if page == 1:
        table_name = config["table_name_page1"]
    elif page == 2:
        table_name = config["table_name_page2"]
    else:
        # For pages 3+, use the page1 pattern (additional short-term pages)
        table_name = config["table_name_page1"]

    # Use page as the prefix number => f1_, f2_, ...
    prefix_num = page
    prefix = f"f{prefix_num}_"

    field_data: Dict[str, str] = {}

    for i, row_obj in enumerate(rows, start=1):
        # row1 => base=3, row2 => base=11, row3 => base=19, etc.
        base_index = 3 + (i - 1) * 8

        # Helper to format field number based on year/row
        def format_field_no(field_no: int, row_num: int) -> str:
            # In 2025, row 1 fields (3-10) are zero-padded, but row 2+ are not
            if config["row1_zero_pad"] and row_num == 1 and field_no < 10:
                return f"{field_no:02d}"
            return str(field_no)

        # Helper to build the actual PDF field name
        def field_name(row_i: int, field_no: int) -> str:
            formatted_no = format_field_no(field_no, row_i)
            return (
                f"topmostSubform[0].Page{prefix_num}[0].{table_name}[0].Row{row_i}[0].{prefix}{formatted_no}[0]"
            )

        # col (a) => offset=0 => description
        col_a = field_name(i, base_index + 0)
        field_data[col_a] = row_obj.description

        # col (b) => offset=1 => date acquired
        col_b = field_name(i, base_index + 1)
        field_data[col_b] = row_obj.date_acquired

        # col (c) => offset=2 => date sold
        col_c = field_name(i, base_index + 2)
        field_data[col_c] = row_obj.date_sold

        # col (d) => offset=3 => proceeds
        col_d = field_name(i, base_index + 3)
        field_data[col_d] = str(row_obj.proceeds)

        # col (e) => offset=4 => cost
        col_e = field_name(i, base_index + 4)
        field_data[col_e] = str(row_obj.cost)

        # col (f) => offset=5 => code => store row_obj.box
        col_f = field_name(i, base_index + 5)
        field_data[col_f] = row_obj.box

        # col (g) => offset=6 => adjustment => empty unless needed
        col_g = field_name(i, base_index + 6)
        field_data[col_g] = ""

        # col (h) => offset=7 => gain_loss
        col_h = field_name(i, base_index + 7)
        field_data[col_h] = str(row_obj.gain_loss)

    return field_data


def map_schedule_d_fields(schedule_d: Dict[str, Dict[str, Decimal]], year: int = 2024) -> Dict[str, str]:
    """
    Adapts short_term (line 1b) & long_term (line 8b) totals from 'schedule_d'
    to year-specific fillable PDF field naming.

    Field naming varies by year:
    - 2024: Short-term row 1b uses f1_07, f1_08 (zero-padded)
    - 2025+: Short-term row 1b uses f1_7, f1_8 (NOT zero-padded)

    Args:
        schedule_d: Dictionary with short_term and long_term totals
        year: Tax year for field name selection

    Returns:
        Dictionary mapping field names to values
    """
    short_data = schedule_d["short_term"]
    long_data = schedule_d["long_term"]

    # Get year-specific field names
    config = get_schedule_d_field_config(year)

    return {
        # Short-term (line 1b)
        config["short_proceeds"]: str(short_data["proceeds"]),
        config["short_cost"]: str(short_data["cost"]),
        config["short_adjustment"]: "",  # adjustments
        config["short_gain_loss"]: str(short_data["gain_loss"]),
        # Long-term (line 8b)
        config["long_proceeds"]: str(long_data["proceeds"]),
        config["long_cost"]: str(long_data["cost"]),
        config["long_adjustment"]: "",
        config["long_gain_loss"]: str(long_data["gain_loss"]),
    }


##############################################################################
# 5) MULTI-PAGE PDF GENERATION (HYBRID APPROACH)
##############################################################################
def fill_8949_multi_page(
    rows: List[Form8949Row],
    template_pdf_path: str,
    flatten: bool = True,
    remove_xfa: bool = True,
    year: int = 2024
) -> BytesIO:
    """
    Generates a multi-page Form 8949 PDF, handling more than 2 pages if needed.
    Uses year-specific field naming for compatibility with different IRS form versions.

    - Splits rows into 14-row chunks.
    - Maps each chunk to field data for its page index using year-specific naming.
    - Fills and merges, removing XFA if requested.
    - Optionally flattens the final PDF.

    Args:
        rows (List[Form8949Row]): The line items for Form 8949.
        template_pdf_path (str): Path to the fillable PDF template.
        flatten (bool, optional): Whether to flatten the final PDF. Defaults to True.
        remove_xfa (bool, optional): Whether to remove XFA references. Defaults to True.
        year (int, optional): Tax year for field name selection. Defaults to 2024.

    Returns:
        BytesIO: A buffer containing the merged Form 8949 PDF. Caller must close if needed.

    Raises:
        FileNotFoundError: If the template PDF is not found.
        RuntimeError: For failures during PDF fill/flatten operations.
    """
    if not rows:
        # Return an empty PDF if no rows are provided
        writer = PdfWriter()
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        logger.info("Generated empty Form 8949 PDF due to no rows")
        return output_buffer

    # Validate template PDF exists and is not empty
    try:
        template_reader = PdfReader(template_pdf_path)
        if len(template_reader.pages) == 0:
            raise ValueError("Template PDF is empty")
    except FileNotFoundError:
        raise FileNotFoundError(f"Template PDF not found at: {template_pdf_path}")

    # Break the rows into pages of up to 14
    chunks = [rows[i:i + 14] for i in range(0, len(rows), 14)]
    writer = PdfWriter()

    try:
        for page_num, chunk in enumerate(chunks, start=1):
            logger.info(f"Processing Form 8949 page {page_num} with {len(chunk)} rows")
            try:
                # Map to the correct field data, with dynamic page numbering and year-specific naming
                field_data = map_8949_rows_to_field_data(chunk, page=page_num, year=year)
            except ValueError as e:
                raise RuntimeError(f"Page {page_num} chunk error: {str(e)}")

            # Fill the PDF template for this chunk
            try:
                filled_pdf_bytes = fill_pdf_with_pdftk(template_pdf_path, field_data)
            except Exception as e:
                raise RuntimeError(f"Failed to fill PDF for page {page_num}: {str(e)}")

            # Read the filled PDF page
            single_page_stream = BytesIO(filled_pdf_bytes)
            reader = PdfReader(single_page_stream)

            # Remove XFA if requested
            if remove_xfa and "/XFA" in reader.trailer["/Root"]:
                del reader.trailer["/Root"]["/XFA"]
                logger.info(f"Removed XFA from page {page_num}")

            # Add the single page to our writer
            if len(reader.pages) == 0:
                raise RuntimeError(f"Page {page_num} generated an empty PDF")

            writer.add_page(reader.pages[0])

        # Merge all pages into one PDF
        merged_output = BytesIO()
        writer.write(merged_output)
        merged_pdf_bytes = merged_output.getvalue()

        # Flatten if requested (removes form fields, ensures final compliance)
        if flatten:
            try:
                merged_pdf_bytes = flatten_pdf_with_pdftk(merged_pdf_bytes)
                logger.info("Flattened final Form 8949 PDF")
            except Exception as e:
                raise RuntimeError(f"Failed to flatten the final PDF: {str(e)}")

        final_buffer = BytesIO(merged_pdf_bytes)
        final_buffer.seek(0)
        logger.info(f"Successfully generated Form 8949 PDF with {len(chunks)} pages")
        return final_buffer

    except Exception as e:
        logger.error(f"Error generating multi-page Form 8949 PDF: {str(e)}")
        raise RuntimeError(f"Error generating multi-page Form 8949 PDF: {str(e)}")
    finally:
        # Clean up resources explicitly
        if 'merged_output' in locals():
            merged_output.close()
        if 'single_page_stream' in locals():
            single_page_stream.close()
        if 'final_buffer' in locals():
            final_buffer.seek(0)  # Ensure buffer is ready for reading