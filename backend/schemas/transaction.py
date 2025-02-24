"""
backend/schemas/transaction.py

Refactored for the full double-entry approach, compatible with Pydantic v2.
We've removed ConstrainedDecimal (deprecated in pydantic 2.0).
Instead, we store decimal fields directly as Decimal, optionally
adding custom validators or field constraints as needed.

We keep legacy single-entry fields like from_account_id/amount
for backward compatibility or simpler input, but the
actual ledger lines are described by LedgerEntry schemas, and
FIFO acquisitions/disposals are in BitcoinLot and LotDisposal schemas.

- TransactionBase: shared fields
- TransactionCreate: used for creation
- TransactionUpdate: partial update
- TransactionRead: output, includes 'id', 'is_locked', 'created_at', 'updated_at'
- LedgerEntryCreate, LedgerEntryRead: line items
- BitcoinLotCreate, BitcoinLotRead: track BTC acquired
- LotDisposalCreate, LotDisposalRead: partial usage of those BTC lots
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# -------------------------------------------------
# CUSTOM VALIDATORS (Optional)
# -------------------------------------------------
# If you want to strictly enforce max_digits=18, decimal_places=8 (BTC)
# or decimal_places=2 (USD), you can write validators like below.
# For demonstration, here's a BTC validator:
def validate_btc_decimal(value: Decimal) -> Decimal:
    """
    Example check: disallow more than 8 decimal places,
    and disallow total digits > 18. If you'd rather not
    enforce these at the schema level, remove or modify.
    """
    # Convert to string to check places
    s = str(value)
    if '.' in s:
        integer_part, frac_part = s.split('.', 1)
        if len(frac_part) > 8:
            raise ValueError("BTC amount cannot exceed 8 decimal places.")
        if len(integer_part.replace('-', '')) > 10:  # 10 + 8 = 18 digits total
            raise ValueError("BTC amount cannot exceed 18 total digits.")
    return value

def validate_usd_decimal(value: Decimal) -> Decimal:
    """
    Example check for USD decimals: 2 decimal places,
    total digits up to 18 if you prefer.
    """
    s = str(value)
    if '.' in s:
        integer_part, frac_part = s.split('.', 1)
        if len(frac_part) > 2:
            raise ValueError("USD amount cannot exceed 2 decimal places.")
        if len(integer_part.replace('-', '')) > 16:  # 16 + 2 = 18
            raise ValueError("USD amount cannot exceed 18 total digits.")
    return value

# -------------------------------------------------
# TRANSACTION SCHEMAS
# -------------------------------------------------

class TransactionBase(BaseModel):
    """
    Shared fields for a transaction. The real double-entry lines are in LedgerEntry,
    but we keep legacy single-entry fields like 'from_account_id', 'to_account_id',
    'amount', 'fee_amount', etc., so the user can still pass them if desired.
    """

    type: str  # e.g. "Deposit", "Withdrawal", "Buy", "Sell"
    timestamp: Optional[datetime] = None

    # Legacy single-entry fields
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None

    # For BTC decimals, we can add custom validation if desired
    amount: Optional[Decimal] = Field(
        default=None,
        description="Single main transaction amount. For BTC, 8 decimals typical."
    )
    fee_amount: Optional[Decimal] = Field(
        default=None,
        description="Single fee in the old system. For BTC fees, 8 decimals typical."
    )
    fee_currency: Optional[str] = None

    # Additional metadata (legacy or optional)
    source: Optional[str] = None
    purpose: Optional[str] = None

    # Summaries for tax
    cost_basis_usd: Optional[Decimal] = Field(
        default=None,
        description="Summarized cost basis for entire transaction, if relevant."
    )
    proceeds_usd: Optional[Decimal] = Field(
        default=None,
        description="Summarized proceeds for entire transaction, if relevant."
    )
    realized_gain_usd: Optional[Decimal] = Field(
        default=None,
        description="Summarized realized gain, if any."
    )
    holding_period: Optional[str] = None

    # OPTIONAL validators
    # e.g., only if you want to validate strictly for BTC or USD decimal logic:
    @field_validator("amount")
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            # Decide if you want to treat 'amount' as BTC or not
            # For demonstration, let's assume it's BTC. Adjust as needed.
            return validate_btc_decimal(v)
        return v

    @field_validator("fee_amount")
    def validate_fee_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            # Assume BTC fees. Or skip if fees can be USD, etc.
            return validate_btc_decimal(v)
        return v

    @field_validator("cost_basis_usd", "proceeds_usd", "realized_gain_usd")
    def validate_usd_fields(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            return validate_usd_decimal(v)
        return v


class TransactionCreate(TransactionBase):
    """
    Fields for creating a new Transaction.
    Since the front-end may supply only partial info, everything is optional
    except 'type'. We can refine if certain transaction types need fields.
    """
    pass


class TransactionUpdate(BaseModel):
    """
    Fields for updating an existing Transaction.
    All optional, so we can do partial updates.
    """
    type: Optional[str] = None
    timestamp: Optional[datetime] = None

    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    amount: Optional[Decimal] = None
    fee_amount: Optional[Decimal] = None
    fee_currency: Optional[str] = None

    source: Optional[str] = None
    purpose: Optional[str] = None

    cost_basis_usd: Optional[Decimal] = None
    proceeds_usd: Optional[Decimal] = None
    realized_gain_usd: Optional[Decimal] = None
    holding_period: Optional[str] = None

    # If you'd like the same validation as TransactionBase, you can do so:
    @field_validator("amount")
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            return validate_btc_decimal(v)
        return v

    @field_validator("fee_amount")
    def validate_fee_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            return validate_btc_decimal(v)
        return v

    @field_validator("cost_basis_usd", "proceeds_usd", "realized_gain_usd")
    def validate_usd_fields(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            return validate_usd_decimal(v)
        return v


class TransactionRead(TransactionBase):
    """
    Schema returned after reading a Transaction from the DB.
    We include primary key 'id', lock status, and audit timestamps.
    """
    id: int
    is_locked: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        # Let pydantic convert from SQLAlchemy ORM objects
        from_attributes = True  # pydantic v2 uses from_attributes instead of orm_mode


# -------------------------------------------------
# LEDGER ENTRY SCHEMAS
# -------------------------------------------------

class LedgerEntryBase(BaseModel):
    """
    Shared fields for a single ledger line (debit/credit).
    - account_id: which account is impacted
    - amount: negative or positive, or we do a sign convention
    - currency: e.g. 'BTC', 'USD'
    - entry_type: e.g. 'FEE', 'MAIN_IN'
    """
    account_id: int
    amount: Decimal = Field(
        ...,
        description="Signed amount for this ledger line (e.g. -1.0 => outflow)."
    )
    currency: str = "BTC"
    entry_type: Optional[str] = None  # e.g. "FEE", "TRANSFER_OUT"

    # Optional validation for ledger entry amounts:
    @field_validator("amount")
    def validate_ledger_amount(cls, v: Decimal) -> Decimal:
        # If needed, enforce BTC decimals or negative sign constraints, etc.
        return validate_btc_decimal(v)


class LedgerEntryCreate(LedgerEntryBase):
    """
    Fields to create a ledger entry. We typically require transaction_id,
    but that might be assigned automatically in the service.
    """
    transaction_id: int


class LedgerEntryRead(LedgerEntryBase):
    """
    Fields returned after reading a LedgerEntry.
    Includes the DB-generated 'id'.
    """
    id: int

    class Config:
        from_attributes = True


# -------------------------------------------------
# BITCOIN LOT SCHEMAS
# -------------------------------------------------

class BitcoinLotBase(BaseModel):
    """
    Shared fields for a BTC lot.
    total_btc, remaining_btc, cost_basis_usd
    track how much was acquired and how much remains.
    """
    total_btc: Decimal = Field(
        ...,
        description="Total BTC acquired in this lot."
    )
    remaining_btc: Decimal = Field(
        ...,
        description="How many BTC remain undisposed in this lot."
    )
    cost_basis_usd: Decimal = Field(
        ...,
        description="Total USD cost basis for this lot."
    )

    @field_validator("total_btc", "remaining_btc")
    def validate_lot_btc(cls, v: Decimal) -> Decimal:
        return validate_btc_decimal(v)

    @field_validator("cost_basis_usd")
    def validate_lot_usd(cls, v: Decimal) -> Decimal:
        return validate_usd_decimal(v)


class BitcoinLotCreate(BitcoinLotBase):
    """
    For creating a new BitcoinLot when user does a Buy/Deposit transaction.
    'created_txn_id' references the Transaction that introduced the BTC.
    'acquired_date' can default to transaction timestamp if not provided.
    """
    created_txn_id: int
    acquired_date: Optional[datetime] = None


class BitcoinLotRead(BitcoinLotBase):
    """
    Fields returned when reading a BitcoinLot.
    """
    id: int
    created_txn_id: int
    acquired_date: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------
# LOT DISPOSAL SCHEMAS
# -------------------------------------------------

class LotDisposalBase(BaseModel):
    """
    Shared fields for partial disposal of a BTC lot.
    'lot_id' references which lot, 'disposed_btc' how many are used.
    """
    lot_id: int
    disposed_btc: Decimal = Field(
        ...,
        description="How many BTC from this lot were applied to the disposal."
    )

    @field_validator("disposed_btc")
    def validate_disposed_btc(cls, v: Decimal) -> Decimal:
        return validate_btc_decimal(v)


class LotDisposalCreate(LotDisposalBase):
    """
    Fields for creating a partial disposal record, referencing
    the disposal transaction. We can also store partial gain details.
    """
    transaction_id: int
    realized_gain_usd: Optional[Decimal] = None
    disposal_basis_usd: Optional[Decimal] = None
    proceeds_usd_for_that_portion: Optional[Decimal] = None

    @field_validator("realized_gain_usd", "disposal_basis_usd", "proceeds_usd_for_that_portion")
    def validate_disposal_usd(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            return validate_usd_decimal(v)
        return v


class LotDisposalRead(LotDisposalBase):
    """
    Reading a disposal record.
    Includes an 'id' plus optional partial gain fields.
    """
    id: int
    transaction_id: int
    realized_gain_usd: Optional[Decimal] = None
    disposal_basis_usd: Optional[Decimal] = None
    proceeds_usd_for_that_portion: Optional[Decimal] = None

    class Config:
        from_attributes = True