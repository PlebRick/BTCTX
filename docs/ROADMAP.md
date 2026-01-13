# Roadmap

## Current Status: v0.4.0 - CSV Import Complete ✅

Template-based CSV import is implemented. Users can download a CSV template, fill it with their data, preview, and import atomically.

**Details:** See [CSV_IMPORT_PLAN.md](CSV_IMPORT_PLAN.md)

### v0.4.0 Features
- Download CSV template with exact column structure
- Preview parsed transactions with error/warning display
- Atomic import (all-or-nothing) with rollback on failure
- Requires empty database (Phase 1)

### Previous Releases
- v0.3.2: Backup restore session fix
- v0.3.1: StartOS compatibility fixes
- v0.3.0: Multi-year IRS form support (2024/2025)

---

## Next Up: v0.5.0 - CSV Import Phase 2

Enhance CSV import with merge capabilities and column mapping.

### Phase 2 Goals
- [ ] Merge with existing data (requires duplicate detection)
- [ ] Column mapping UI for arbitrary CSVs
- [ ] Saved mapping presets for different exchange formats

---

## Future Enhancements

### High Priority
- [ ] **CSV import merge**: Phase 2 - merge with existing data
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
- [x] **v0.4.0: CSV template import** - Bulk import with preview and atomic commits
- [x] **v0.3.2: Backup restore fix** - Session clearing and login redirect
- [x] **v0.3.1: StartOS compatibility** - DATABASE_FILE env var, BackgroundTasks cleanup
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
