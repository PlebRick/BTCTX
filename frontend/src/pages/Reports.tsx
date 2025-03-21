// FILE: src/components/Reports.tsx

import React, { useState } from "react";
import "../styles/reports.css"; // Import your CSS

/**
 * If you prefer, you can move this to a config file or use environment
 * variables. For simplicity, we hardcode your FastAPI base URL here.
 */
const API_BASE = "http://localhost:8000";

interface ReportOption {
  title: string;
  description: string;
  endpoint: string;         // which backend route to call
  needsYearInput?: boolean; // does this report require a taxYear?
  fileExtension?: string;   // "pdf" or "csv"
}

const Reports: React.FC = () => {
  // We define your three reports.
  // Each has an `endpoint` so we know which route to call.
  // For "Transaction History," let's assume it's PDF by default,
  // but if you prefer CSV, just set fileExtension="csv".
  const reports: ReportOption[] = [
    {
      title: "Complete Tax Report",
      description: "Generate a full tax summary.",
      endpoint: "/reports/complete_tax_report",
      needsYearInput: true,
      fileExtension: "pdf",
    },
    {
      title: "IRS Reports (Form 8949, Schedule D & 1)",
      description: "Generate tax forms for IRS reporting.",
      endpoint: "/reports/irs_reports",
      needsYearInput: true,
      fileExtension: "pdf",
    },
    {
      title: "Transaction History",
      description: "Full history of all recorded transactions.",
      endpoint: "/reports/transaction_history",
      needsYearInput: true,
      fileExtension: "csv", // or "pdf" if you prefer
    },
  ];

  // Local state for the user’s selected year
  const [taxYear, setTaxYear] = useState("");

  // Unified handler for the three buttons
  const handleGenerate = async (report: ReportOption) => {
    // If this report needs a year, make sure one is entered
    if (report.needsYearInput && !taxYear) {
      alert("Please enter a tax year (e.g. 2024).");
      return;
    }

    try {
      // Build the final URL. Example: "http://localhost:8000/reports/complete_tax_report?year=2024"
      const url = `${API_BASE}${report.endpoint}${
        report.needsYearInput ? `?year=${taxYear}` : ""
      }`;

      const response = await fetch(url, {
        method: "GET",
        // If your server needs session cookies: credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      // For both PDF and CSV, we can treat it as a Blob
      const blob = await response.blob();

      // Derive a filename from the report’s title + extension
      const extension = report.fileExtension || "pdf";
      const safeTitle = report.title.replace(/\s+/g, "");
      const fileName = `${safeTitle}_${taxYear || "latest"}.${extension}`;

      // Create a temporary link to download
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      if (err instanceof Error) {
        console.error(`Error generating "${report.title}":`, err.message);
        alert(`Failed to generate ${report.title}. See console for details.`);
      } else {
        console.error("Unknown error:", err);
      }
    }
  };

  return (
    <div className="reports-container">
      <h2 className="reports-title">Reports</h2>
      <p className="reports-description">
        Generate or view financial and tax reports.
      </p>

      <div className="reports-section">
        {reports.map((report, index) => (
          <div key={index} className="report-option">
            <div>
              <span className="report-title">{report.title}</span>
              <p className="report-subtitle">{report.description}</p>
            </div>

            {/* If this report needs a year, show an input */}
            {report.needsYearInput && (
              <input
                type="text"
                className="report-year-input"
                placeholder="Enter Year (e.g. 2024)"
                value={taxYear}
                onChange={(e) => setTaxYear(e.target.value)}
              />
            )}

            <button className="report-button" onClick={() => handleGenerate(report)}>
              Generate
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Reports;
