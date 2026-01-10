# IRS Form Generation - Technical Documentation

> **CRITICAL:** This document explains how BitcoinTX generates IRS tax forms. This is complex code that uses workarounds for PDF form filling. Keep this document updated whenever changes are made.

**Last Updated:** 2025-01-10

---

## Overview

BitcoinTX generates three types of tax reports:

| Report | Endpoint | Method | Output |
|--------|----------|--------|--------|
| **IRS Reports** | `/api/reports/irs_reports` | pdftk form filling | Form 8949 + Schedule D (official IRS forms) |
| **Complete Tax Report** | `/api/reports/complete_tax_report` | ReportLab from scratch | Custom PDF with all tax data |
| **Transaction History** | `/api/reports/simple_transaction_history` | CSV or ReportLab | Raw transaction list |

The IRS Reports endpoint is the most complex because it fills official IRS PDF forms.

---

## The XFA Problem and Our Workaround

### Why This Is Hard

IRS fillable PDFs use **XFA (XML Forms Architecture)**, a complex Adobe format that most PDF libraries cannot handle. Standard Python PDF libraries (PyPDF, reportlab) cannot fill XFA forms.

### Our Solution: pdftk

We use `pdftk` (PDF Toolkit) with a multi-step workaround:

```
1. pdftk template.pdf output no_xfa.pdf drop_xfa
   → Removes XFA, exposing the underlying AcroForm fields

2. Generate FDF (Forms Data Format) file with field values
   → Simple text format that maps field names to values

3. pdftk no_xfa.pdf fill_form data.fdf output filled.pdf flatten
   → Fills the form and flattens (locks) it
```

**This is a hack**, but it works reliably for IRS forms.

---

## Multi-Year Form Strategy

**Design Decision:** The app maintains all historical IRS form templates, allowing users to generate reports for any supported tax year.

### Directory Structure

```
backend/assets/irs_templates/
├── 2024/
│   ├── f8949.pdf
│   └── f1040sd.pdf
├── 2025/
│   ├── f8949.pdf
│   └── f1040sd.pdf
└── 2026/
    └── (added January 2027)
```

### Why This Approach

1. **Single codebase** - No maintaining multiple app versions
2. **Amended returns** - Users can file late/amended returns for prior years
3. **Simple updates** - New tax year = new folder + any field mapping changes
4. **No version rollback** - Users always have latest app with all form years

### Adding New Tax Year Forms

When IRS releases new forms (typically late December):
1. Create new year folder in `backend/assets/irs_templates/`
2. Download fillable PDFs from IRS.gov
3. Extract and compare field names (see "Updating for New Tax Years" section)
4. Update field mappings if changed
5. Bump minor version (e.g., v0.3.0 for 2025 forms)

---

## File Structure

```
backend/
├── assets/irs_templates/
│   └── [year]/                        # One folder per tax year
│       ├── f8949.pdf                  # IRS Form 8949 template
│       └── f1040sd.pdf                # IRS Schedule D template
├── services/reports/
│   ├── pdftk_filler.py                # Core pdftk operations
│   ├── pdf_utils.py                   # PDF flattening utility
│   ├── form_8949.py                   # Data model & field mapping
│   ├── complete_tax_report.py         # ReportLab-based report
│   ├── transaction_history.py         # CSV/PDF export
│   └── reporting_core.py              # Data aggregation
├── routers/
│   └── reports.py                     # API endpoints
└── scripts/
    ├── extract_fields_8949.py         # Utility to discover field names
    └── inspect_8949_fields.py         # Field inspection tool
```

---

## How Form 8949 Generation Works

### Step-by-Step Process

1. **Query Database**: Get all `LotDisposal` records for the tax year
2. **Build Rows**: Convert each disposal to a `Form8949Row` object
3. **Separate by Holding Period**: Split into short-term and long-term lists
4. **Chunk into Pages**: Each Form 8949 page holds 14 rows max
5. **Map to Field Names**: Convert row data to PDF field names
6. **Fill Each Page**: Use pdftk to fill the template for each chunk
7. **Fill Schedule D**: Fill summary totals
8. **Merge Pages**: Combine all pages with pypdf
9. **Flatten**: Final pdftk flatten to lock the form

### Code Flow

```
GET /api/reports/irs_reports?year=2024
    ↓
reports.py: get_irs_reports()
    ↓
form_8949.py: build_form_8949_and_schedule_d()
    → Queries LotDisposal records
    → Creates Form8949Row objects
    → Separates short/long term
    → Calculates Schedule D totals
    ↓
reports.py: Loop through chunks of 14 rows
    ↓
form_8949.py: map_8949_rows_to_field_data()
    → Converts rows to {field_name: value} dict
    ↓
pdftk_filler.py: fill_pdf_with_pdftk()
    → Generates FDF
    → Calls pdftk drop_xfa
    → Calls pdftk fill_form + flatten
    ↓
reports.py: _merge_all_pdfs()
    → Combines pages with pypdf
    ↓
pdf_utils.py: flatten_pdf_with_pdftk()
    → Final flatten pass
    ↓
Return PDF bytes
```

---

## Form 8949 Field Mapping

### Field Naming Convention

IRS PDF forms use deeply nested XPath-style field names:

```
topmostSubform[0].Page1[0].Table_Line1[0].Row1[0].f1_3[0]
                 ↑                        ↑       ↑
                 Page number              Row     Field index
```

### Row Field Indices

Each row has 8 columns (a-h) with consecutive field indices:

| Column | Content | Offset from Base |
|--------|---------|------------------|
| (a) | Description of property | +0 |
| (b) | Date acquired | +1 |
| (c) | Date sold | +2 |
| (d) | Proceeds | +3 |
| (e) | Cost or other basis | +4 |
| (f) | Code (if any) | +5 |
| (g) | Adjustment | +6 |
| (h) | Gain or (loss) | +7 |

### Base Index Calculation

```python
# Row 1 starts at index 3
# Each row adds 8 to the base
base_index = 3 + (row_number - 1) * 8

# Examples:
# Row 1: base = 3  → fields f1_3 through f1_10
# Row 2: base = 11 → fields f1_11 through f1_18
# Row 3: base = 19 → fields f1_19 through f1_26
# ...
# Row 14: base = 107 → fields f1_107 through f1_114
```

### Full Field Name Construction

```python
def field_name(page: int, row: int, field_offset: int) -> str:
    base_index = 3 + (row - 1) * 8
    field_no = base_index + field_offset
    return f"topmostSubform[0].Page{page}[0].Table_Line1[0].Row{row}[0].f{page}_{field_no}[0]"
```

### Multi-Page Handling

When there are more than 14 rows:
- Rows 1-14 → Page 1 (field prefix `f1_`)
- Rows 15-28 → Page 2 (field prefix `f2_`)
- etc.

**Important**: The page number in the field name changes (`f1_`, `f2_`, `f3_`...).

---

## Schedule D Field Mapping

Schedule D summarizes the Form 8949 totals.

### Short-Term (Part I, Line 1b)

```python
"topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_07[0]"  # Proceeds
"topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_08[0]"  # Cost
"topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_09[0]"  # Adjustment (empty)
"topmostSubform[0].Page1[0].Table_PartI[0].Row1b[0].f1_10[0]"  # Gain/Loss
```

### Long-Term (Part II, Line 8b)

```python
"topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_27[0]"  # Proceeds
"topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_28[0]"  # Cost
"topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_29[0]"  # Adjustment (empty)
"topmostSubform[0].Page1[0].Table_PartII[0].Row8b[0].f1_30[0]"  # Gain/Loss
```

---

## Checkbox Logic (Box Selection)

Form 8949 has checkboxes to indicate the type of transaction:

### Current Implementation (2024 Forms)

| Holding Period | Basis Reported to IRS | Box |
|----------------|----------------------|-----|
| Short-term | Yes | A |
| Short-term | No | C |
| Long-term | Yes | D |
| Long-term | No | F |

```python
def _determine_box(holding_period: str, basis_reported: bool):
    if holding_period == "LONG":
        return "D" if basis_reported else "F"
    return "A" if basis_reported else "C"
```

### 2025 Form Changes (Future)

The 2025 forms add new boxes for digital assets reported on Form 1099-DA:
- **Box G**: Short-term, 1099-DA, basis reported
- **Box H**: Short-term, 1099-DA, basis NOT reported
- **Box J**: Long-term, 1099-DA, basis reported
- **Box K**: Long-term, 1099-DA, basis NOT reported
- **Box L**: Long-term digital assets NOT on 1099-DA or 1099-B

This will require updating `_determine_box()` when 2025 templates are adopted.

---

## FDF Generation

FDF (Forms Data Format) is a simple text format for PDF form data:

```fdf
%FDF-1.2
1 0 obj <<
/FDF << /Fields [
<< /T (field_name_1) /V (value_1) >>
<< /T (field_name_2) /V (value_2) >>
] >>
>>
endobj
trailer
<< /Root 1 0 R >>
%%EOF
```

The `generate_fdf()` function in `pdftk_filler.py` creates this format.

**Important**: Parentheses in field names or values must be escaped with backslashes.

---

## Dependencies

### Required for IRS Forms

- **pdftk** (or pdftk-java): Form filling and flattening
  - macOS: `brew install pdftk-java`
  - Linux: `apt-get install pdftk`
  - Docker: Installed via Dockerfile

- **pypdf**: PDF reading and merging (pure Python)

### Required for Other Reports

- **ReportLab**: PDF generation from scratch (Complete Tax Report, Transaction History PDF)

---

## Docker Considerations

The Dockerfile must include pdftk:

```dockerfile
# Install pdftk for PDF form filling
RUN apt-get update && apt-get install -y pdftk
```

Template paths use absolute paths based on `__file__`:

```python
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_THIS_DIR)
_ASSETS_DIR = os.path.join(_BACKEND_DIR, "assets", "irs_templates")
```

---

## Updating for New Tax Years

When IRS releases new forms (typically December each year):

### Step 1: Download New Templates

1. Go to https://www.irs.gov/forms-pubs
2. Download fillable PDF versions of Form 8949 and Schedule D
3. Save to `backend/assets/irs_templates/` with year suffix

### Step 2: Extract Field Names

```bash
cd backend/scripts
python extract_fields_8949.py
```

This will print all field names in the new PDF. Compare with the old field names.

### Step 3: Update Field Mappings

If field names changed, update:
- `form_8949.py`: `map_8949_rows_to_field_data()`
- `reports.py`: `schedule_d_fields` dictionary

### Step 4: Update Checkbox Logic

If new checkboxes were added (like 1099-DA boxes for 2025):
- Update `form_8949.py`: `_determine_box()`

### Step 5: Update Path Constants

In `reports.py`:
```python
PATH_FORM_8949 = os.path.join(_ASSETS_DIR, "Form_8949_Fillable_2025.pdf")
PATH_SCHEDULE_D = os.path.join(_ASSETS_DIR, "Schedule_D_Fillable_2025.pdf")
```

### Step 6: Test Thoroughly

1. Generate reports with sample data
2. Open PDFs and verify all fields are filled correctly
3. Test with edge cases (many transactions, spanning multiple pages)

---

## Troubleshooting

### "pdftk not found"

```
HTTPException: pdftk is not installed or not in PATH
```

**Solution**: Install pdftk (`brew install pdftk-java` on macOS)

### "Template PDF not found"

```
HTTPException: Missing IRS template PDFs
```

**Solution**: Verify templates exist in `backend/assets/irs_templates/`

### Fields Not Filling

Possible causes:
1. Field names changed in new IRS form version
2. XFA not properly removed
3. FDF escaping issue with special characters

**Debug**:
```bash
# List fields in a PDF
pdftk Form_8949_Fillable_2024.pdf dump_data_fields
```

### Multi-Page Issues

If pages aren't merging correctly:
1. Check that page prefix (`f1_`, `f2_`) matches the page number
2. Verify pypdf merge is including all pages
3. Check for exceptions in the chunk loop

---

## Alternative Approaches (Not Currently Used)

### ReportLab-Only Approach

Instead of filling IRS forms, generate custom PDFs that replicate the form layout. This would:
- Remove pdftk dependency
- Be more maintainable
- But NOT produce official IRS forms

The Complete Tax Report already uses this approach for non-IRS documentation.

### Browser-Based PDF Filling

Use JavaScript PDF libraries in the frontend to fill forms client-side. This would:
- Remove server-side PDF processing
- But require sending templates to client
- And may have browser compatibility issues

### Commercial PDF APIs

Services like Adobe PDF Services or DocuSign can fill forms. This would:
- Be more reliable
- But add cost and external dependency
- And require API keys / internet access

---

## Related Documentation

- [STARTOS_COMPATIBILITY.md](STARTOS_COMPATIBILITY.md) - Docker requirements
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [ROADMAP.md](ROADMAP.md) - Future plans including 2025 form updates

---

## Contact / Questions

If you're working on this code and have questions:
1. Read this document thoroughly first
2. Check the scripts in `backend/scripts/` for field inspection
3. Test with `pdftk dump_data_fields` to see actual field names
4. Update this document with any new findings
