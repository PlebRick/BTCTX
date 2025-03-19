# backend/routers/reports.py

from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db

# --- aggregator & PDF modules ---
from backend.services.reports.reporting_core import generate_report_data
from backend.services.reports.complete_tax_report import generate_comprehensive_tax_report

# If you have specialized modules:
# from backend.services.reports.form_8949 import generate_8949_pdf
# from backend.services.reports.ScheduleD import generate_schedule_d_pdf
# etc.

reports_router = APIRouter()

@reports_router.get("/comprehensive_tax")
def get_comprehensive_tax(
    year: int,
    user_id: Optional[int] = None,   # or required if multi-user
    db: Session = Depends(get_db),
):
    """
    Generates the “Complete/Comprehensive Tax Report” in PDF format
    for the given tax year.
    """
    # 1) aggregator logic
    #    If your aggregator needs `user_id`, pass it in (not shown in the snippet).
    report_dict = generate_report_data(db, year)  

    # 2) Generate PDF using your complete_tax_report.py
    pdf_bytes = generate_comprehensive_tax_report(report_dict)

    # 3) Return PDF
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=CompleteTaxReport.pdf"})


@reports_router.get("/form_8949")
def get_form_8949_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Generates a PDF or fillable PDF of IRS Form 8949 for the given tax year.
    """
    # aggregator data
    report_dict = generate_report_data(db, year)
    
    # If you have a specialized function:
    # pdf_content = generate_8949_pdf(report_dict)
    # For now, a placeholder:
    pdf_content = b"(Placeholder for 8949 PDF bytes)"

    return Response(content=pdf_content, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=Form8949.pdf"})


@reports_router.get("/schedule_d")
def get_schedule_d_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Generates Schedule D PDF for capital gains.
    """
    # aggregator data
    report_dict = generate_report_data(db, year)

    # If you have schedule_d.py:
    # pdf_content = generate_schedule_d_pdf(report_dict)
    pdf_content = b"(Placeholder for Schedule D PDF)"

    return Response(content=pdf_content, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=ScheduleD.pdf"})


@reports_router.get("/turbotax_export")
def get_turbotax_export(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Exports a CSV with capital gains data in the TurboTax Online format.
    Some devs produce a .txf for TurboTax Desktop. 
    """
    report_dict = generate_report_data(db, year)
    
    # Here, you'd build a CSV string. 
    # Possibly something like:
    # csv_data = build_turbotax_csv(report_dict)
    csv_data = "date_acquired,date_sold,proceeds,cost_basis,gain,...\n(etc)"

    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=TurboTax.csv"})


@reports_router.get("/turbotax_cddvd")
def get_turbotax_cd_dvd_export(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Exports a TXF (Tax eXchange Format) for TurboTax CD/DVD version.
    """
    report_dict = generate_report_data(db, year)
    # txf_str = build_txf_file(report_dict)
    txf_str = "(Placeholder TXF data)"

    return Response(content=txf_str, media_type="text/plain",
                    headers={"Content-Disposition": "attachment; filename=TurboTaxCD.txf"})


@reports_router.get("/taxact_export")
def get_taxact_export(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Export capital gains data for TaxAct software (usually CSV).
    """
    report_dict = generate_report_data(db, year)
    # taxact_csv = build_taxact_csv(report_dict)
    taxact_csv = "transaction_date,disposal_date,cost_basis,proceeds,GainLoss\n(etc)"

    return Response(content=taxact_csv, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=TaxAct.csv"})


@reports_router.get("/capital_gains")
def get_capital_gains_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Returns a PDF or CSV summarizing capital gains (short-term & long-term).
    This might be simpler than the full Comprehensive Tax Report.
    """
    report_dict = generate_report_data(db, year)
    # Maybe we want just a CSV here
    # or a simplified PDF. Example CSV:
    gains = report_dict["capital_gains_summary"]

    csv_data = (
        "Type,Proceeds,Basis,Gain\n"
        f"ShortTerm,{gains['short_term']['proceeds']},{gains['short_term']['basis']},{gains['short_term']['gain']}\n"
        f"LongTerm,{gains['long_term']['proceeds']},{gains['long_term']['basis']},{gains['long_term']['gain']}\n"
        f"Total,{gains['total']['proceeds']},{gains['total']['basis']},{gains['total']['gain']}\n"
    )

    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=CapitalGains.csv"})


@reports_router.get("/income")
def get_income_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Summarize deposits flagged as “Income.” Possibly CSV or PDF.
    """
    report_dict = generate_report_data(db, year)
    inc = report_dict["income_summary"]
    # Example CSV
    csv_data = (
        "Mining,Reward,Other,Total\n"
        f"{inc['Mining']},{inc['Reward']},{inc['Other']},{inc['Total']}\n"
    )
    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=Income.csv"})


@reports_router.get("/other_gains")
def get_other_gains_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    If you had a separate classification for “Other Gains” not in capital gains
    or income (like futures, derivatives, or realized PNL).
    """
    return Response("(Placeholder) No other gains logic implemented.")


@reports_router.get("/gifts_donations_lost")
def get_gifts_donations_lost_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Summarize all 'Withdrawal' transactions with purpose in ('Gift','Donation','Lost').
    """
    report_dict = generate_report_data(db, year)
    # We can produce CSV or JSON. For example:
    items = report_dict["gifts_donations_lost"]  # a list of dict
    lines = ["date,asset,amount,value_usd,type"]
    for row in items:
        lines.append(f"{row['date']},{row['asset']},{row['amount']},{row['value_usd']},{row['type']}")
    csv_data = "\n".join(lines)

    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=GiftsDonations.csv"})


@reports_router.get("/expenses")
def get_expenses_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Summarize transactions with purpose=Expenses if you track that as a separate category.
    """
    report_dict = generate_report_data(db, year)
    items = report_dict["expenses"]
    lines = ["date,asset,amount,value_usd,type"]
    for row in items:
        lines.append(f"{row['date']},{row['asset']},{row['amount']},{row['value_usd']},{row['type']}")
    csv_data = "\n".join(lines)

    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=Expenses.csv"})


@reports_router.get("/beginning_year_holdings")
def get_beginning_of_year_holdings(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Typically the end_of_year_holdings from prior year is the beginning for this year.
    But if you want a direct aggregator approach, you can build a new function 
    that checks leftover lots as of Jan 1 of the current year.
    """
    # A placeholder approach: do the same aggregator, but you might do partial-lot re-lot
    # from the prior year. Or just show the eoy from (year-1).
    return Response("(Placeholder) Beginning-of-year holdings not yet implemented.")


@reports_router.get("/end_year_holdings")
def get_end_of_year_holdings(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Summarize leftover BTC at the end of this year (like your eoy_list from aggregator).
    """
    report_dict = generate_report_data(db, year)
    eoy = report_dict["end_of_year_balances"]
    # eoy is a list of dicts: {asset, quantity, cost, value, description}
    lines = ["asset,quantity,cost,value,description"]
    for row in eoy:
        lines.append(
            f"{row['asset']},{row['quantity']},{row['cost']},{row['value']},{row['description']}"
        )
    csv_data = "\n".join(lines)

    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=EndOfYearBalances.csv"})


@reports_router.get("/highest_balance")
def get_highest_balance_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Koinly sometimes does a “Highest Balance” – 
    you’d need to track daily or rolling max BTC quantity. 
    We'll placeholder it.
    """
    return Response("(Placeholder) Highest Balance logic not yet implemented.")


@reports_router.get("/buy_sell_report")
def get_buy_sell_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Summarize all buy/sell transactions, ignoring transfers or deposits. 
    Possibly CSV with date/time, cost basis, proceeds, etc.
    """
    return Response("(Placeholder) Not implemented.")


@reports_router.get("/ledger_balance")
def get_ledger_balance_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Returns a breakdown of all ledger accounts or some 
    net balance in the double-entry system, if you want. 
    Placeholder.
    """
    return Response("(Placeholder) Not implemented.")


@reports_router.get("/balances_per_wallet")
def get_balances_per_wallet_report(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Summarize account-by-account balances at year-end, 
    or monthly, etc. 
    Placeholder.
    """
    return Response("(Placeholder) Not implemented.")


@reports_router.get("/transaction_history")
def get_transaction_history(
    year: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Full history of transactions within the year (or date range).
    Could be a big CSV listing everything from 'generate_report_data' or 
    a simpler function that just does a direct DB query 
    with optional from_date/to_date.
    """
    # Reuse aggregator or just query directly
    report_dict = generate_report_data(db, year)
    all_txs = report_dict["capital_gains_transactions"] + report_dict["income_transactions"] 
    # plus any others if you want a single big CSV
    lines = ["date,type,amount,asset,cost,proceeds,gain_loss,etc"]
    # Your aggregator might not have a single “type” for each row, 
    # so you'd unify it as you see fit. 
    # We'll just do a placeholder:
    lines.append("(Placeholder) Not fully integrated yet.")
    csv_data = "\n".join(lines)

    return Response(content=csv_data, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=TransactionHistory.csv"})
