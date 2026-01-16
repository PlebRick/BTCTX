# Roadmap

## Current Status: v0.5.3 - macOS Desktop App & Testing ✅

Native macOS desktop app complete with PyInstaller + pywebview. Comprehensive test suite with 131 pytest tests + 17 pre-commit checks. Mobile-responsive UI.

### v0.5.x Features
- macOS desktop app (.app bundle with embedded backend)
- Mobile responsiveness overhaul (10 CSS files, touch-friendly)
- Comprehensive test suite (stress testing, edge cases, IRS form validation)
- Pre-commit test suite for CI/CD
- Desktop app download fixes (Settings + Reports pages)
- pdftk path resolution for bundled apps

### Previous Releases
- v0.5.0: Backend refactoring, Pydantic V2, dependency updates
- v0.4.0: CSV template import
- v0.3.2: Backup restore session fix
- v0.3.1: StartOS compatibility fixes
- v0.3.0: Multi-year IRS form support (2024/2025)

---

## Next Up: v1.0.0 - Production Release

Polish and stabilize for production release.

### v1.0.0 Goals
- [ ] Final QA pass on all features
- [ ] 2025 IRS form template updates (when released by IRS)
- [ ] Documentation review and updates
- [ ] Performance optimization if needed

### Future (Post v1.0.0)
- [ ] CSV import merge with existing data (Phase 2)
- [ ] Column mapping UI for arbitrary exchange CSVs
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
- [x] ~~**Dark mode**: UI theme toggle~~ (theme system added, dark mode ready to implement)
- [x] ~~**Mobile responsive**: Better mobile layout~~ (completed Jan 2025)

---

## Completed

### January 2025
- [x] **macOS desktop app** - Native .app bundle with PyInstaller + pywebview
- [x] **Comprehensive test suite** - 131 pytest tests + 17 pre-commit checks
  - `test_stress_and_forms.py`: stress testing, edge cases, IRS form validation
  - All deposit sources and withdrawal purposes tested
  - Account-specific FIFO verification
- [x] **Mobile responsiveness overhaul** - 10 CSS files, touch-friendly UI, 44px touch targets
- [x] **Pre-commit test suite** - Docker/StartOS compat, FIFO integrity, report generation
- [x] **Desktop app download fixes** - Settings and Reports pages work in pywebview
- [x] **pdftk path resolution** - Centralized module for macOS desktop compatibility
- [x] **Frontend design system refactor** - Custom hooks, toast notifications, error boundaries, theme system
- [x] **v0.5.0: Backend refactoring** - Pydantic V2, dependency updates, code modernization
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
- **Testing**: Comprehensive automated test suite
  - 131 pytest tests covering transactions, FIFO, edge cases, IRS forms
  - 17 pre-commit checks for Docker/StartOS compatibility
  - Run: `pytest backend/tests/` or `./scripts/pre-commit.sh`
