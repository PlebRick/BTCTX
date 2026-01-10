# Roadmap

## Current Priority: StartOS Packaging

Package BitcoinTX for Start9's StartOS platform to enable easy self-hosting.

### Status
A separate wrapper repository handles StartOS packaging: [BTCTX-StartOS](https://github.com/PlebRick/BTCTX-StartOS)

### Requirements (This Repo)
- [x] Docker image published to `b1ackswan/btctx:latest`
- [x] Multi-arch support (amd64/arm64) - see `docs/STARTOS_COMPATIBILITY.md`
- [x] Single container with FastAPI + React on port 80
- [x] Data persistence via `/data` volume mount
- [ ] Build and push multi-arch image to Docker Hub
- [ ] Test sideload to StartOS

### Requirements (Wrapper Repo)
- [ ] Create StartOS manifest and procedures
- [ ] Configure Tor integration
- [ ] Set up backup/restore for SQLite database
- [ ] Build and test `.s9pk` package

### Resources
- Start9 Developer Docs: https://docs.start9.com/latest/developer-docs/
- StartOS SDK: https://github.com/Start9Labs/start-sdk

---

## Future Enhancements

### High Priority
- [ ] **Backdated transactions**: Recalculate cost basis when transactions are added with past dates
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
