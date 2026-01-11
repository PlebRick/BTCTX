# 2025 IRS Form Update - Implementation Plan

> **Purpose:** This document provides complete context for implementing 2025 IRS form support in BitcoinTX. It is designed to be read by a new AI chat session with full context.

**Created:** 2025-01-10
**Pre-refactor Tag:** `v0.2.1-pre-refactor`
**Target Release:** `v0.3.0`

---

## Executive Summary

### What Changed for 2025

1. **New Form 1099-DA** - Exchanges now issue this form for digital asset transactions
   - BitcoinTX does NOT generate this form (users receive it from exchanges)
   - BUT Form 8949 now has new checkboxes (G-L) to indicate 1099-DA transactions

2. **Form 8949 Field Name Changes** - Breaking changes from 2024:
   - Table name: `Table_Line1[0]` → `Table_Line1_Part1[0]` / `Table_Line1_Part2[0]`
   - Field format: `f1_3` → `f1_03` (zero-padded)
   - 6 new checkboxes added (G, H, I, J, K, L)

3. **Schedule D** - Minor field name differences (see docs/IRS_FORM_GENERATION.md)

### What Needs to Change in BitcoinTX

| Component | Change Required |
|-----------|-----------------|
| Template folder structure | Reorganize to year-based folders |
| `reports.py` | Add dynamic template path selection |
| `form_8949.py` | Add year-specific field mapping functions |
| Checkbox logic | Add support for 1099-DA boxes (optional enhancement) |

---

## Background Research (Completed)

### Form 1099-DA Understanding

- **Issued BY:** Exchanges/brokers (Coinbase, Kraken, etc.)
- **Issued TO:** Users who sold/traded crypto on those platforms
- **Purpose:** Report digital asset transactions to IRS
- **BitcoinTX Impact:** We don't generate it, but users selling on exchanges will receive it

### Checkbox Selection Logic for 2025

| Scenario | Short-Term Box | Long-Term Box |
|----------|---------------|---------------|
| No 1099-B or 1099-DA received | C | F |
| 1099-B received, basis reported | A | D |
| 1099-B received, basis NOT reported | B | E |
| **1099-DA received, basis reported** | **G** | **J** |
| **1099-DA received, basis NOT reported** | **H** | **K** |
| **1099-DA received, basis unknown** | **I** | **L** |

For self-custody users (BitcoinTX's primary use case):
- Selling from cold storage → Box C/F (no 1099 received)
- Selling on exchange after transfer → Box H/K (exchange issues 1099-DA but doesn't know your cost basis)

### Field Mapping Differences

See [docs/IRS_FORM_GENERATION.md](IRS_FORM_GENERATION.md) section "Year-Specific Field Differences (CRITICAL)" for complete details.

**Key 2024 → 2025 Changes:**
```
# Form 8949 Row 1, Column (a) - Description
2024: topmostSubform[0].Page1[0].Table_Line1[0].Row1[0].f1_3[0]
2025: topmostSubform[0].Page1[0].Table_Line1_Part1[0].Row1[0].f1_03[0]
```

---

## Phased Implementation Plan

### Phase 1: Infrastructure Setup (Low Risk)

**Goal:** Reorganize templates without changing any code logic

**Tasks:**
1. Create year-based folder structure:
   ```
   backend/assets/irs_templates/
   ├── 2024/
   │   ├── f8949.pdf
   │   └── f1040sd.pdf
   └── 2025/
       ├── f8949.pdf
       └── f1040sd.pdf
   ```

2. Download 2025 forms from IRS.gov:
   - Form 8949: https://www.irs.gov/pub/irs-pdf/f8949.pdf
   - Schedule D: https://www.irs.gov/pub/irs-pdf/f1040sd.pdf

3. Move existing 2024 templates into `2024/` subfolder

4. Rename files to consistent naming:
   - `Form_8949_Fillable_2024.pdf` → `2024/f8949.pdf`
   - `Schedule_D_Fillable_2024.pdf` → `2024/f1040sd.pdf`

**Testing:**
- Verify existing tests still pass with path updates
- No functional changes yet

**Commit:** "Phase 1: Reorganize IRS templates into year-based folders"

---

### Phase 2: Dynamic Template Selection (Medium Risk)

**Goal:** Add year-based template path selection to reports.py

**Tasks:**
1. Add helper function in `reports.py`:
   ```python
   def get_template_path(year: int, form_name: str) -> str:
       """Get the template path for a specific tax year."""
       template_path = os.path.join(_ASSETS_DIR, str(year), form_name)
       if not os.path.exists(template_path):
           raise HTTPException(
               status_code=400,
               detail=f"No template available for tax year {year}"
           )
       return template_path
   ```

2. Add supported years validation:
   ```python
   def get_supported_years() -> list:
       """Return list of years with available templates."""
       # Implementation in docs/IRS_FORM_GENERATION.md
   ```

3. Update `get_irs_reports()` to use `get_template_path(year, "f8949.pdf")`

4. Update path constants to use dynamic selection

**Testing:**
- Test with year=2024 (should work identically to before)
- Test with year=2023 (should fail gracefully - no templates)
- Test with year=2025 (should fail gracefully until Phase 4)

**Commit:** "Phase 2: Add dynamic template path selection by year"

---

### Phase 3: Year-Specific Field Mappings (High Risk - Core Logic)

**Goal:** Refactor field mapping to support different years

**Tasks:**
1. Add field configuration function in `form_8949.py`:
   ```python
   def get_8949_field_config(year: int) -> dict:
       """Return year-specific field configuration."""
       if year >= 2025:
           return {
               "table_name": "Table_Line1_Part1",  # or Part2 for page 2
               "field_format": "{:02d}",  # Zero-padded
               "base_index": 3,
           }
       else:  # 2024 and earlier
           return {
               "table_name": "Table_Line1",
               "field_format": "{}",  # Not zero-padded
               "base_index": 3,
           }
   ```

2. Refactor `map_8949_rows_to_field_data()` to accept year parameter:
   ```python
   def map_8949_rows_to_field_data(rows: List[Form8949Row], page: int = 1, year: int = 2024) -> Dict[str, str]:
   ```

3. Update field name construction to use config:
   ```python
   config = get_8949_field_config(year)
   field_name = f"topmostSubform[0].Page{page}[0].{config['table_name']}[0].Row{row}[0].f{page}_{config['field_format'].format(field_no)}[0]"
   ```

4. Similarly update `map_schedule_d_fields()` for year-specific naming

5. Update `fill_8949_multi_page()` to pass year through the chain

6. Update `reports.py` to pass year to all field mapping functions

**Testing:**
- Extensive testing with 2024 data (must produce identical output)
- Compare PDF field fills before/after refactor
- Run existing test suite

**Commit:** "Phase 3: Add year-specific field mapping infrastructure"

---

### Phase 4: 2025 Form Support (Medium Risk)

**Goal:** Verify and enable 2025 form filling

**Tasks:**
1. Extract field names from 2025 PDFs:
   ```bash
   pdftk backend/assets/irs_templates/2025/f8949.pdf dump_data_fields | grep FieldName
   ```

2. Compare extracted fields with expected mappings from documentation

3. Adjust 2025 field config if any discrepancies found

4. Test PDF generation with 2025 forms:
   - Create test transactions dated in 2025
   - Generate IRS reports for year=2025
   - Verify all fields fill correctly

5. Verify checkbox handling (currently uses C/F for all - correct for self-custody)

**Testing:**
- Generate 2024 report, verify unchanged
- Generate 2025 report, verify all fields populate
- Test multi-page scenarios
- Test edge cases (empty data, single row, 14 rows, 15 rows)

**Commit:** "Phase 4: Enable 2025 IRS form support"

---

### Phase 5: Optional Enhancement - 1099-DA Checkbox Support

**Goal:** Allow users to indicate if transaction was on a 1099-DA

**Tasks (OPTIONAL - can defer to v0.4.0):**
1. Add `has_1099_da` field to Transaction model (or derive from account type)
2. Update `_determine_box()` to use new 2025 checkbox logic
3. Add UI toggle for "Sold on exchange" when applicable

**Rationale for deferral:**
- Most self-custody users use Box C/F anyway
- Box H/K (1099-DA, basis not reported) is the common case for exchange sales
- Can be added later without breaking existing functionality

---

### Phase 6: Release v0.3.0

**Tasks:**
1. Update CHANGELOG.md with all changes
2. Update ROADMAP.md
3. Run full test suite
4. Build and test Docker image
5. Create release tag `v0.3.0`
6. Push to both remotes (origin and plebrick)

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/assets/irs_templates/` | Reorganize to year folders |
| `backend/routers/reports.py` | Add `get_template_path()`, `get_supported_years()`, pass year to functions |
| `backend/services/reports/form_8949.py` | Add `get_8949_field_config()`, update `map_8949_rows_to_field_data()`, `map_schedule_d_fields()` |
| `docs/CHANGELOG.md` | Document changes |
| `docs/ROADMAP.md` | Update status |

---

## Testing Checklist

### Before Starting (Baseline)
- [ ] Run existing tests: `python -m pytest backend/tests/`
- [ ] Generate 2024 IRS report manually, save as reference
- [ ] Verify `v0.2.1-pre-refactor` tag exists

### After Each Phase
- [ ] All existing tests pass
- [ ] 2024 reports generate correctly
- [ ] Compare output to baseline (should be identical until Phase 4)

### Final Verification
- [ ] 2024 report matches baseline exactly
- [ ] 2025 report generates without errors
- [ ] 2025 report fields are filled correctly (manual inspection)
- [ ] Multi-page reports work for both years
- [ ] Docker build succeeds
- [ ] Docker container generates reports correctly

---

## Rollback Plan

If anything goes wrong:
```bash
git checkout v0.2.1-pre-refactor
```

This restores the codebase to the known-good state before any changes.

---

## Commands for New Chat Session

Start the new chat with:
```
Read docs/2025_FORM_UPDATE_PLAN.md and docs/IRS_FORM_GENERATION.md, then implement the phased plan starting with Phase 1. After each phase, commit and test before proceeding.
```

---

## Reference Links

- [IRS Form 8949](https://www.irs.gov/pub/irs-pdf/f8949.pdf)
- [IRS Schedule D](https://www.irs.gov/pub/irs-pdf/f1040sd.pdf)
- [Form 8949 Instructions](https://www.irs.gov/pub/irs-pdf/i8949.pdf)
- [Form 1099-DA Information](https://www.irs.gov/forms-pubs/about-form-1099-da)

---

## Summary for AI Assistant

When starting this implementation:

1. **Read first:** This file + `docs/IRS_FORM_GENERATION.md`
2. **Verify baseline:** Run tests, generate 2024 report as reference
3. **Follow phases sequentially:** Don't skip ahead
4. **Commit after each phase:** Small, testable increments
5. **Test thoroughly:** Compare outputs, run test suite
6. **Rollback if needed:** `git checkout v0.2.1-pre-refactor`

The goal is **working 2025 form support** without breaking 2024 functionality.
