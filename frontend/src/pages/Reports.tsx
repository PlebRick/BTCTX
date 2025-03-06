import React from "react";
import "../styles/reports.css"; // Import CSS file for styling

// ✅ Define the type for report options
interface ReportOption {
  title: string;
  description: string;
}

const Reports: React.FC = () => {
  const reports: ReportOption[] = [
    { title: "IRS Reports (Form 8949, Schedule D & 1)", description: "Generate tax forms for IRS reporting." },
    { title: "Turbotax Export (Gain/Loss)", description: "Export transactions for Turbotax online." },
    { title: "Turbotax CD/DVD (old TXF version)", description: "Export using the older TXF format." },
    { title: "TaxAct Export", description: "Export transactions for TaxAct software." },
    { title: "Complete Tax Report", description: "Generate a full tax summary." },
    { title: "Capital Gains Report", description: "View capital gains calculations." },
    { title: "Income Report", description: "Summarize income from transactions." },
    { title: "Other Gains Report", description: "View additional realized gains." },
    { title: "Gifts, Donations & Lost Assets", description: "Track gifted or lost assets." },
    { title: "Expenses Report", description: "View transaction-related expenses." },
    { title: "Beginning of Year Holdings Report", description: "View your portfolio at the start of the year." },
    { title: "End of Year Holdings Report", description: "View your portfolio at the end of the year." },
    { title: "Highest Balance Report", description: "Identify your highest historical balance." },
    { title: "Buy/Sell Report", description: "View all buys and sells in detail." },
    { title: "Ledger Balance Report", description: "Breakdown of all transaction ledger balances." },
    { title: "Balances per Wallet", description: "View wallet balances at different times." },
    { title: "Transaction History", description: "Full history of all recorded transactions." },
  ];

  return (
    <div className="reports-container">
      <h2 className="reports-title">Reports</h2>
      <p className="reports-description">Generate or view financial and tax reports.</p>

      <div className="reports-section">
        {reports.map((report, index) => (
          <div key={index} className="report-option">
            <div>
              <span className="report-title">{report.title}</span>
              <p className="report-subtitle">{report.description}</p>
            </div>
            <button className="report-button">View</button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Reports;
