# Roadmap

## Current Status: v0.3.0 - 2025 IRS Form Support ✅ COMPLETE

Multi-year IRS form support is now implemented. Users can generate Form 8949 and Schedule D for both 2024 and 2025 tax years.

**Details:** See [2025_FORM_UPDATE_PLAN.md](2025_FORM_UPDATE_PLAN.md)

### Completed Phases
- [x] Phase 1: Reorganize templates into year-based folders
- [x] Phase 2: Add dynamic template path selection
- [x] Phase 3: Implement year-specific field mappings
- [x] Phase 4: Enable and test 2025 form support
- [ ] Phase 5: (Deferred to v0.4.0) Add 1099-DA checkbox support
- [ ] Phase 6: Release v0.3.0 (pending Docker build/test)

### Key Fixes in This Release
- Schedule D uses Line 3/10 (Box C/F) for self-tracked crypto, not Line 1b/8b
- Complete Tax Report generation fixed - Transfer lot restoration in partial re-lot
- Comprehensive test dataset covering all deposit sources and withdrawal purposes

---

## Next Up: Beta Testing & Refinement

With 2025 form support complete, focus shifts to testing and refining the application.

---

## Future Enhancements

### High Priority
- [ ] **CSV import**: Bulk import transactions from exchange exports
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
