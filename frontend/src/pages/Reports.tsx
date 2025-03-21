// FILE: src/pages/Reports.tsx

import React, { useState } from "react";
import "../styles/reports.css"; // Your custom CSS

/**
 * Hardcoded base URL for your FastAPI backend.
 * Adjust as needed or move to a config/environment variable.
 */
const API_BASE = "http://localhost:8000";

/**
 * Each report definition:
 *  - key: internal identifier
 *  - label: displayed to the user
 *  - endpoint: your FastAPI route
 *  - pdfOnly: indicates if the report can only produce PDF
 */
const REPORTS = [
  {
    key: "completeTax",
    label: "Complete Tax Report",
    endpoint: "/reports/complete_tax_report",
    pdfOnly: true,
  },
  {
    key: "irsReports",
    label: "IRS Reports (Form 8949, Schedule D, etc.)",
    endpoint: "/reports/irs_reports",
    pdfOnly: true,
  },
  {
    key: "transactionHistory",
    label: "Transaction History",
    endpoint: "/reports/transaction_history",
    pdfOnly: false, // can do PDF or CSV
  },
];

const Reports: React.FC = () => {
  // Track which report is selected
  const [selectedReport, setSelectedReport] = useState<string>("completeTax");

  // Single Year Input
  const [taxYear, setTaxYear] = useState<string>("");

  // Format (PDF or CSV). We’ll only use it if the selected report supports CSV.
  const [format, setFormat] = useState<string>("pdf");

  /**
   * Handler when the user clicks "Export"
   */
  const handleExport = async () => {
    if (!taxYear) {
      alert("Please enter a valid year (e.g. 2024).");
      return;
    }

    const reportDef = REPORTS.find((r) => r.key === selectedReport);
    if (!reportDef) {
      alert("Invalid report selection.");
      return;
    }

    // If this report is pdfOnly, ignore the user's 'format' setting and force "pdf"
    const finalFormat = reportDef.pdfOnly ? "pdf" : format;

    // Build query. For transactionHistory we do ?year=XXX&format=pdf/csv
    // For the others, they only consume ?year=XXX, but passing &format=pdf is harmless.
    const url = `${API_BASE}${reportDef.endpoint}?year=${taxYear}&format=${finalFormat}`;

    try {
      const response = await fetch(url, { method: "GET" });
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      // Blob for PDF or CSV
      const blob = await response.blob();

      // Construct file name, e.g. "TransactionHistory_2024.pdf" or "...csv"
      const safeLabel = reportDef.label.replace(/\s+/g, "");
      const fileExt = finalFormat.toLowerCase();
      const fileName = `${safeLabel}_${taxYear}.${fileExt}`;

      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);

    } catch (err) {
      if (err instanceof Error) {
        console.error(`Error generating "${reportDef.label}":`, err.message);
        alert(`Failed to generate ${reportDef.label}. See console for details.`);
      } else {
        console.error("Unknown error:", err);
      }
    }
  };

  // Determine if the user should see the format dropdown or not
  const reportDef = REPORTS.find((r) => r.key === selectedReport);
  const showFormatDropdown = reportDef && !reportDef.pdfOnly;

  return (
    <div className="reports-container">
      <h2 className="reports-title">Reports</h2>
      <p className="reports-description">
        Generate or view financial and tax reports. Select the desired report,
        provide the year, then choose a format (where applicable) and click "Export."
      </p>

      {/* Report Selection */}
      <div className="report-selection">
        {REPORTS.map((r) => (
          <div key={r.key} className="report-radio">
            <input
              type="radio"
              id={r.key}
              name="report"
              value={r.key}
              checked={selectedReport === r.key}
              onChange={() => setSelectedReport(r.key)}
            />
            <label htmlFor={r.key}>{r.label}</label>
          </div>
        ))}
      </div>

      {/* Single Year Input */}
      <div className="input-group">
        <label>Tax Year:</label>
        <input
          type="text"
          className="report-year-input"
          placeholder="e.g. 2024"
          value={taxYear}
          onChange={(e) => setTaxYear(e.target.value)}
        />
      </div>

      {/* Format Selector - only visible if the report supports CSV */}
      {showFormatDropdown && (
        <div className="input-group">
          <label>Format:</label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="report-format-select"
          >
            <option value="pdf">PDF</option>
            <option value="csv">CSV</option>
          </select>
        </div>
      )}

      {/* Single Export Button */}
      <button className="report-button" onClick={handleExport}>
        Export
      </button>
    </div>
  );
};

export default Reports;
