# Roadmap

## Current Priority: StartOS Packaging

Package BitcoinTX for Start9's StartOS platform to enable easy self-hosting.

### Requirements
- [ ] Create `manifest.yaml` with app metadata
- [ ] Create `docker_entrypoint.sh` for container startup
- [ ] Add health check endpoint (may use existing `/api/health` or create new)
- [ ] Create `instructions.md` for user documentation
- [ ] Add app icon (`icon.png`)
- [ ] Configure Tor integration (StartOS apps typically run over Tor)
- [ ] Set up backup/restore for SQLite database
- [ ] Build and test `.s9pk` package

### Resources
- Start9 Developer Docs: https://docs.start9.com/latest/developer-docs/
- Example packages: https://github.com/Start9Labs/

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
