"""
backend/services/csv_import.py

Core parsing and validation logic for CSV import feature.
Handles template-based CSV format with strict validation.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session

from backend.models.transaction import Transaction
from backend.services.transaction import create_transaction_record
from backend.schemas.csv_import import CSVRowPreview, CSVParseError


# Account name to ID mapping
ACCOUNT_NAME_TO_ID: Dict[str, int] = {
    "bank": 1,
    "wallet": 2,
    "exchange usd": 3,
    "exchange btc": 4,
    "external": 99,
}

# Valid transaction types (case-insensitive matching)
VALID_TYPES = {"deposit", "withdrawal", "transfer", "buy", "sell"}

# Required columns in the CSV
REQUIRED_COLUMNS = {
    "date", "type", "amount", "from_account", "to_account"
}

# All valid columns
ALL_COLUMNS = REQUIRED_COLUMNS | {
    "cost_basis_usd", "proceeds_usd", "fee_amount", "fee_currency",
    "source", "purpose", "notes"
}


@dataclass
class ParseResult:
    """Result of parsing a CSV file."""
    transactions: List[Dict[str, Any]] = field(default_factory=list)
    previews: List[CSVRowPreview] = field(default_factory=list)
    errors: List[CSVParseError] = field(default_factory=list)
    warnings: List[CSVParseError] = field(default_factory=list)

    @property
    def can_import(self) -> bool:
        """Returns True if there are no errors (warnings are OK)."""
        return len(self.errors) == 0 and len(self.transactions) > 0


def parse_csv_file(content: bytes) -> ParseResult:
    """
    Parse CSV content and return structured data with errors/warnings.

    Args:
        content: Raw bytes of the CSV file

    Returns:
        ParseResult containing transactions, previews, errors, and warnings
    """
    result = ParseResult()

    # Try to decode the content
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("utf-8-sig")  # UTF-8 with BOM
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except UnicodeDecodeError:
                result.errors.append(CSVParseError(
                    row_number=0,
                    column=None,
                    message="File encoding not supported. Please save as UTF-8.",
                    severity="error"
                ))
                return result

    # Parse CSV
    try:
        reader = csv.DictReader(io.StringIO(text))
    except Exception as e:
        result.errors.append(CSVParseError(
            row_number=0,
            column=None,
            message=f"Invalid CSV format: {str(e)}",
            severity="error"
        ))
        return result

    # Validate headers
    if reader.fieldnames is None:
        result.errors.append(CSVParseError(
            row_number=0,
            column=None,
            message="CSV file is empty or has no headers.",
            severity="error"
        ))
        return result

    # Normalize headers (lowercase, strip whitespace)
    headers = {h.lower().strip() for h in reader.fieldnames if h}

    # Check for required columns
    missing_columns = REQUIRED_COLUMNS - headers
    if missing_columns:
        result.errors.append(CSVParseError(
            row_number=0,
            column=None,
            message=f"Missing required columns: {', '.join(sorted(missing_columns))}",
            severity="error"
        ))
        return result

    # Process each row
    prev_date: Optional[datetime] = None

    for row_number, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
        # Normalize row keys
        normalized_row = {k.lower().strip(): v.strip() if v else "" for k, v in row.items() if k}

        # Validate and parse the row
        tx_data, preview, row_errors, row_warnings = _validate_row(normalized_row, row_number)

        result.errors.extend(row_errors)
        result.warnings.extend(row_warnings)

        if tx_data and preview:
            # Check chronological order
            if prev_date and preview.date < prev_date:
                result.warnings.append(CSVParseError(
                    row_number=row_number,
                    column="date",
                    message="Row is not in chronological order. Import will sort by date.",
                    severity="warning"
                ))
            prev_date = preview.date

            result.transactions.append(tx_data)
            result.previews.append(preview)

    if not result.transactions and not result.errors:
        result.errors.append(CSVParseError(
            row_number=0,
            column=None,
            message="No valid transactions found in file.",
            severity="error"
        ))

    return result


def _validate_row(
    row: Dict[str, str],
    row_number: int
) -> Tuple[Optional[Dict[str, Any]], Optional[CSVRowPreview], List[CSVParseError], List[CSVParseError]]:
    """
    Validate a single CSV row.

    Returns:
        Tuple of (transaction_dict, preview, errors, warnings)
        transaction_dict and preview are None if there are fatal errors
    """
    errors: List[CSVParseError] = []
    warnings: List[CSVParseError] = []

    # Parse date
    date_str = row.get("date", "").strip()
    if not date_str:
        errors.append(CSVParseError(
            row_number=row_number,
            column="date",
            message="Date is required.",
            severity="error"
        ))
        return None, None, errors, warnings

    timestamp = _parse_date(date_str)
    if timestamp is None:
        errors.append(CSVParseError(
            row_number=row_number,
            column="date",
            message=f"Invalid date format: '{date_str}'. Use ISO8601 (e.g., 2024-01-15T10:30:00Z).",
            severity="error"
        ))
        return None, None, errors, warnings

    # Check for future date
    if timestamp > datetime.now(timezone.utc):
        warnings.append(CSVParseError(
            row_number=row_number,
            column="date",
            message="Date is in the future.",
            severity="warning"
        ))

    # Parse type
    tx_type_str = row.get("type", "").strip().lower()
    if not tx_type_str:
        errors.append(CSVParseError(
            row_number=row_number,
            column="type",
            message="Transaction type is required.",
            severity="error"
        ))
        return None, None, errors, warnings

    if tx_type_str not in VALID_TYPES:
        errors.append(CSVParseError(
            row_number=row_number,
            column="type",
            message=f"Invalid type '{tx_type_str}'. Must be one of: Deposit, Withdrawal, Transfer, Buy, Sell.",
            severity="error"
        ))
        return None, None, errors, warnings

    # Normalize type to title case
    tx_type = tx_type_str.title()

    # Parse amount (BTC)
    amount_str = row.get("amount", "").strip()
    if not amount_str:
        errors.append(CSVParseError(
            row_number=row_number,
            column="amount",
            message="Amount is required.",
            severity="error"
        ))
        return None, None, errors, warnings

    amount = _parse_decimal(amount_str, 8)
    if amount is None:
        errors.append(CSVParseError(
            row_number=row_number,
            column="amount",
            message=f"Invalid amount '{amount_str}'. Must be a positive number with up to 8 decimal places.",
            severity="error"
        ))
        return None, None, errors, warnings

    if amount <= 0:
        errors.append(CSVParseError(
            row_number=row_number,
            column="amount",
            message="Amount must be positive.",
            severity="error"
        ))
        return None, None, errors, warnings

    # Parse accounts
    from_account_str = row.get("from_account", "").strip().lower()
    to_account_str = row.get("to_account", "").strip().lower()

    if not from_account_str:
        errors.append(CSVParseError(
            row_number=row_number,
            column="from_account",
            message="From account is required.",
            severity="error"
        ))
        return None, None, errors, warnings

    if not to_account_str:
        errors.append(CSVParseError(
            row_number=row_number,
            column="to_account",
            message="To account is required.",
            severity="error"
        ))
        return None, None, errors, warnings

    from_account_id = ACCOUNT_NAME_TO_ID.get(from_account_str)
    to_account_id = ACCOUNT_NAME_TO_ID.get(to_account_str)

    if from_account_id is None:
        errors.append(CSVParseError(
            row_number=row_number,
            column="from_account",
            message=f"Invalid account '{from_account_str}'. Must be one of: Bank, Wallet, Exchange USD, Exchange BTC, External.",
            severity="error"
        ))
        return None, None, errors, warnings

    if to_account_id is None:
        errors.append(CSVParseError(
            row_number=row_number,
            column="to_account",
            message=f"Invalid account '{to_account_str}'. Must be one of: Bank, Wallet, Exchange USD, Exchange BTC, External.",
            severity="error"
        ))
        return None, None, errors, warnings

    # Validate accounts for transaction type
    type_errors = _validate_accounts_for_type(tx_type, from_account_id, to_account_id, row_number)
    if type_errors:
        errors.extend(type_errors)
        return None, None, errors, warnings

    # Parse optional fields
    cost_basis_usd = _parse_decimal(row.get("cost_basis_usd", ""), 2)
    proceeds_usd = _parse_decimal(row.get("proceeds_usd", ""), 2)
    fee_amount = _parse_decimal(row.get("fee_amount", ""), 8)
    fee_currency = row.get("fee_currency", "").strip().upper() or None
    source = row.get("source", "").strip() or None
    purpose = row.get("purpose", "").strip() or None
    notes = row.get("notes", "").strip() or None

    # Validate fee currency
    if fee_currency and fee_currency not in ("USD", "BTC"):
        errors.append(CSVParseError(
            row_number=row_number,
            column="fee_currency",
            message=f"Invalid fee currency '{fee_currency}'. Must be USD or BTC.",
            severity="error"
        ))
        return None, None, errors, warnings

    # Type-specific validation
    type_specific_errors, type_specific_warnings = _validate_type_specific(
        tx_type, cost_basis_usd, proceeds_usd, fee_currency, source, purpose, row_number
    )
    errors.extend(type_specific_errors)
    warnings.extend(type_specific_warnings)

    if errors:
        return None, None, errors, warnings

    # Build transaction data dict (for create_transaction_record)
    tx_data: Dict[str, Any] = {
        "type": tx_type,
        "timestamp": timestamp,
        "amount": amount,
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
    }

    if cost_basis_usd is not None:
        tx_data["cost_basis_usd"] = cost_basis_usd
    if proceeds_usd is not None:
        tx_data["proceeds_usd"] = proceeds_usd
    if fee_amount is not None and fee_amount > 0:
        tx_data["fee_amount"] = fee_amount
        tx_data["fee_currency"] = fee_currency or _default_fee_currency(tx_type)
    if source:
        tx_data["source"] = source
    if purpose:
        tx_data["purpose"] = purpose

    # Build preview object
    preview = CSVRowPreview(
        row_number=row_number,
        date=timestamp,
        type=tx_type,
        amount=amount,
        from_account=from_account_str.title() if from_account_str != "external" else "External",
        to_account=to_account_str.title() if to_account_str != "external" else "External",
        cost_basis_usd=cost_basis_usd,
        proceeds_usd=proceeds_usd,
        fee_amount=fee_amount,
        fee_currency=fee_currency,
        source=source,
        purpose=purpose,
        notes=notes,
    )

    return tx_data, preview, errors, warnings


def _parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string into a UTC datetime.
    Supports ISO8601 and common date formats.
    """
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S UTC",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Ensure UTC timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError:
            continue

    return None


def _parse_decimal(value: str, max_decimals: int) -> Optional[Decimal]:
    """
    Parse a string to Decimal with validation.
    Returns None if parsing fails or value is empty.
    """
    if not value:
        return None

    # Remove commas (thousand separators)
    value = value.replace(",", "")

    try:
        d = Decimal(value)
        # Check decimal places
        if "." in value:
            decimal_places = len(value.split(".")[1])
            if decimal_places > max_decimals:
                return None
        return d
    except InvalidOperation:
        return None


def _validate_accounts_for_type(
    tx_type: str,
    from_id: int,
    to_id: int,
    row_number: int
) -> List[CSVParseError]:
    """Validate that account IDs are valid for the transaction type."""
    errors = []

    if tx_type == "Deposit":
        if from_id != 99:
            errors.append(CSVParseError(
                row_number=row_number,
                column="from_account",
                message="Deposit must have from_account = 'External'.",
                severity="error"
            ))
        if to_id not in (2, 4):  # Wallet or Exchange BTC
            errors.append(CSVParseError(
                row_number=row_number,
                column="to_account",
                message="Deposit must have to_account = 'Wallet' or 'Exchange BTC'.",
                severity="error"
            ))

    elif tx_type == "Withdrawal":
        if from_id not in (2, 4):  # Wallet or Exchange BTC
            errors.append(CSVParseError(
                row_number=row_number,
                column="from_account",
                message="Withdrawal must have from_account = 'Wallet' or 'Exchange BTC'.",
                severity="error"
            ))
        if to_id != 99:
            errors.append(CSVParseError(
                row_number=row_number,
                column="to_account",
                message="Withdrawal must have to_account = 'External'.",
                severity="error"
            ))

    elif tx_type == "Transfer":
        # Both must be internal BTC accounts
        if from_id not in (2, 4):
            errors.append(CSVParseError(
                row_number=row_number,
                column="from_account",
                message="Transfer must have from_account = 'Wallet' or 'Exchange BTC'.",
                severity="error"
            ))
        if to_id not in (2, 4):
            errors.append(CSVParseError(
                row_number=row_number,
                column="to_account",
                message="Transfer must have to_account = 'Wallet' or 'Exchange BTC'.",
                severity="error"
            ))
        if from_id == to_id:
            errors.append(CSVParseError(
                row_number=row_number,
                column="to_account",
                message="Transfer must have different from_account and to_account.",
                severity="error"
            ))

    elif tx_type == "Buy":
        if from_id != 3:  # Exchange USD
            errors.append(CSVParseError(
                row_number=row_number,
                column="from_account",
                message="Buy must have from_account = 'Exchange USD'.",
                severity="error"
            ))
        if to_id != 4:  # Exchange BTC
            errors.append(CSVParseError(
                row_number=row_number,
                column="to_account",
                message="Buy must have to_account = 'Exchange BTC'.",
                severity="error"
            ))

    elif tx_type == "Sell":
        if from_id != 4:  # Exchange BTC
            errors.append(CSVParseError(
                row_number=row_number,
                column="from_account",
                message="Sell must have from_account = 'Exchange BTC'.",
                severity="error"
            ))
        if to_id != 3:  # Exchange USD
            errors.append(CSVParseError(
                row_number=row_number,
                column="to_account",
                message="Sell must have to_account = 'Exchange USD'.",
                severity="error"
            ))

    return errors


def _validate_type_specific(
    tx_type: str,
    cost_basis_usd: Optional[Decimal],
    proceeds_usd: Optional[Decimal],
    fee_currency: Optional[str],
    source: Optional[str],
    purpose: Optional[str],
    row_number: int
) -> Tuple[List[CSVParseError], List[CSVParseError]]:
    """Validate type-specific field requirements."""
    errors = []
    warnings = []

    if tx_type == "Buy":
        if cost_basis_usd is None:
            errors.append(CSVParseError(
                row_number=row_number,
                column="cost_basis_usd",
                message="cost_basis_usd is required for Buy transactions.",
                severity="error"
            ))
        if fee_currency and fee_currency != "USD":
            errors.append(CSVParseError(
                row_number=row_number,
                column="fee_currency",
                message="Buy fee must be in USD.",
                severity="error"
            ))

    elif tx_type == "Sell":
        if proceeds_usd is None:
            errors.append(CSVParseError(
                row_number=row_number,
                column="proceeds_usd",
                message="proceeds_usd is required for Sell transactions.",
                severity="error"
            ))
        if fee_currency and fee_currency != "USD":
            errors.append(CSVParseError(
                row_number=row_number,
                column="fee_currency",
                message="Sell fee must be in USD.",
                severity="error"
            ))

    elif tx_type == "Deposit":
        if cost_basis_usd is None:
            warnings.append(CSVParseError(
                row_number=row_number,
                column="cost_basis_usd",
                message="No cost_basis_usd provided for Deposit. Will default to $0 (gift/unknown basis).",
                severity="warning"
            ))

    elif tx_type == "Withdrawal":
        if purpose and purpose.lower() in ("spent",) and proceeds_usd is None:
            warnings.append(CSVParseError(
                row_number=row_number,
                column="proceeds_usd",
                message="Withdrawal with purpose='Spent' has no proceeds_usd. Will calculate from market value.",
                severity="warning"
            ))

    elif tx_type == "Transfer":
        if fee_currency and fee_currency != "BTC":
            errors.append(CSVParseError(
                row_number=row_number,
                column="fee_currency",
                message="Transfer fee must be in BTC.",
                severity="error"
            ))

    return errors, warnings


def _default_fee_currency(tx_type: str) -> str:
    """Return the default fee currency for a transaction type."""
    if tx_type in ("Buy", "Sell"):
        return "USD"
    return "BTC"


def check_database_empty(db: Session) -> Tuple[bool, int]:
    """
    Check if the database has any transactions.

    Returns:
        Tuple of (is_empty, transaction_count)
    """
    count = db.query(Transaction).count()
    return count == 0, count


def execute_import(db: Session, transactions: List[Dict[str, Any]]) -> int:
    """
    Import transactions atomically.

    All transactions are created without committing, then committed together
    at the end. If any transaction fails, all are rolled back.

    Args:
        db: Database session
        transactions: List of transaction dicts (output from parse_csv_file)

    Returns:
        Count of imported transactions

    Raises:
        Exception on failure (all transactions rolled back)
    """
    # Sort by timestamp to ensure FIFO is calculated correctly
    sorted_txns = sorted(transactions, key=lambda x: x["timestamp"])

    imported_count = 0

    try:
        for tx_data in sorted_txns:
            # Use auto_commit=False to defer commit until all transactions succeed
            create_transaction_record(tx_data, db, auto_commit=False)
            imported_count += 1

        # All transactions succeeded - commit them all
        db.commit()
        return imported_count

    except Exception as e:
        # Roll back all uncommitted transactions
        db.rollback()
        raise e


def generate_template_csv() -> str:
    """
    Generate a CSV template with headers and sample rows.

    Returns:
        CSV content as a string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "date", "type", "amount", "from_account", "to_account",
        "cost_basis_usd", "proceeds_usd", "fee_amount", "fee_currency",
        "source", "purpose", "notes"
    ])

    # Sample rows (one per type + extras)
    writer.writerow([
        "2024-01-15T10:30:00Z", "Buy", "0.012", "Exchange USD", "Exchange BTC",
        "500.00", "", "5.00", "USD",
        "", "", "Example: Bought BTC on exchange"
    ])
    writer.writerow([
        "2024-01-20T14:00:00Z", "Deposit", "0.5", "External", "Wallet",
        "21000.00", "", "", "",
        "Income", "", "Example: Received payment in BTC"
    ])
    writer.writerow([
        "2024-01-25T08:00:00Z", "Deposit", "0.05", "External", "Wallet",
        "0", "", "", "",
        "Gift", "", "Example: Received BTC as gift (no cost basis)"
    ])
    writer.writerow([
        "2024-02-01T09:00:00Z", "Transfer", "0.4", "Wallet", "Exchange BTC",
        "", "", "0.0001", "BTC",
        "", "", "Example: Moved BTC to exchange"
    ])
    writer.writerow([
        "2024-02-15T11:30:00Z", "Sell", "0.3", "Exchange BTC", "Exchange USD",
        "", "15000.00", "10.00", "USD",
        "", "", "Example: Sold BTC on exchange"
    ])
    writer.writerow([
        "2024-03-01T16:00:00Z", "Withdrawal", "0.1", "Wallet", "External",
        "", "", "0.00005", "BTC",
        "", "Gift", "Example: Sent BTC as gift"
    ])
    writer.writerow([
        "2024-03-10T12:00:00Z", "Withdrawal", "0.05", "Wallet", "External",
        "", "2500.00", "0.00002", "BTC",
        "", "Spent", "Example: Spent BTC on purchase"
    ])

    return output.getvalue()
