# Roadmap

## Current Status: v0.3.1 - Stable Release ✅

Multi-year IRS form support is implemented. Users can generate Form 8949 and Schedule D for both 2024 and 2025 tax years.

**Details:** See [2025_FORM_UPDATE_PLAN.md](2025_FORM_UPDATE_PLAN.md)

### v0.3.1 Fixes
- StartOS compatibility: DATABASE_FILE env var support in backup/restore
- Fixed race condition in backup file download using BackgroundTasks
- Comprehensive StartOS container documentation

---

## Next Up: v0.4.0 - CSV Import

Enable users to import transactions from CSV files (Koinly exports, exchange exports, personal spreadsheets).

**Details:** See [CSV_IMPORT_PLAN.md](CSV_IMPORT_PLAN.md)

### Phase 1 (v0.4.0)
- [ ] Koinly CSV import only
- [ ] Empty database requirement (prevents accidental data corruption)
- [ ] Preview before commit
- [ ] Full validation and rollback safety

### Phase 2 (v0.5.0)
- [ ] BitcoinTX native CSV format
- [ ] Column mapping UI for arbitrary CSVs
- [ ] Saved mapping presets

### Phase 3 (Future)
- [ ] Merge with existing data (complex - requires duplicate detection)

---

## Future Enhancements

### High Priority
- [ ] **CSV import**: See [CSV_IMPORT_PLAN.md](CSV_IMPORT_PLAN.md) - Target v0.4.0
- [ ] **Improved error handling**: Better user feedback for failed operations

### Medium Priority
- [ ] **Multi-year reports**: Generate reports spanning multiple tax years
- [ ] **Cost basis methods**: Support LIFO, specific identification (not just FIFO)
- [ ] **Transaction categories**: Tags/labels for transaction organization
- [ ] **Data validation**: Audit tool to verify ledger balance integrity

### Low Priority / Nice-to-Have
- [ ] **Multi-user support**: Separate portfolios for household members
- [ ] **Exchange API sync**: Optional automatic import from exchanges
- [ ] **Dark mode**: UI theme toggle
- [ ] **Mobile responsive**: Better mobile layout

---

## Completed

### January 2025
- [x] **v0.3.0: 2025 IRS form support** - Multi-year form generation working
- [x] **2025 IRS form update planning** - Research and documentation complete
- [x] **StartOS packaging complete** - `.s9pk` tested and working
- [x] Multi-arch Docker image (amd64/arm64) on Docker Hub
- [x] Backdated transaction FIFO recalculation
- [x] Lost BTC capital loss tax treatment fix
- [x] Insufficient BTC validation
- [x] UI responsiveness improvements
- [x] IRS form generation documentation
- [x] Docker container working with PDF generation
- [x] All three report endpoints functional
- [x] Python 3.9 compatibility
- [x] Repository cleanup and branch strategy
- [x] Docker Hub publishing (`b1ackswan/btctx:latest`)
- [x] Documentation structure (`docs/` directory)

---

## Notes

- **Philosophy**: Get basic functionality working first, refine edge cases later
- **Git workflow**: `develop` branch for work, merge to `master` for releases
- **Testing**: Manual testing preferred; automated tests exist but coverage is limited
