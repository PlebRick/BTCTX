# Maintenance Guide

> This document provides procedures for maintaining BitcoinTX dependencies and addressing deprecations.
> **Primary audience:** AI assistants (Claude) and developers performing maintenance tasks.

**Last Reviewed:** 2025-01-14

---

## Quick Reference

### Before Updating Any Dependency

1. Check the package's changelog for breaking changes
2. Run full test suite: `python3 backend/tests/test_everything.py`
3. If tests pass, commit with clear message about what was updated
4. Never update multiple unrelated packages in the same commit

### Test Commands

```bash
# Comprehensive test (78 tests)
python3 backend/tests/test_everything.py

# Auth tests (23 tests)
pytest backend/tests/test_password_migration.py -v

# Pre-commit tests (17 tests)
./scripts/pre-commit.sh

# Quick static checks only
python3 backend/tests/pre_commit_tests.py --no-api
```

---

## Current Deprecation Warnings

Track deprecations here. Fix before they become errors in future versions.

| Warning | File | Line | Status | Notes |
|---------|------|------|--------|-------|
| `declarative_base()` moved to `sqlalchemy.orm` | `backend/database.py` | 71 | **TODO** | Change `from sqlalchemy.ext.declarative import declarative_base` to `from sqlalchemy.orm import declarative_base` |

### How to Find New Deprecations

```bash
# Run tests and grep for warnings
python3 -m pytest backend/tests/test_password_migration.py 2>&1 | grep -i "warning\|deprecated"

# Run comprehensive tests with warnings visible
python3 backend/tests/test_everything.py 2>&1 | grep -i "warning\|deprecated"
```

---

## Dependency Risk Levels

### 🟢 Safe to Update (Patch/Minor versions)

These packages follow semver well and rarely break:

| Package | Current | Notes |
|---------|---------|-------|
| `pytest` | 8.3.5 | Test framework, isolated from production |
| `python-dotenv` | 1.0.1 | Simple, stable API |
| `python-dateutil` | 2.9.0 | Mature, stable |
| `requests` | 2.32.0 | Very stable HTTP client |
| `cryptography` | 44.0.2 | Security updates important |

### 🟡 Update with Caution (Check changelog first)

| Package | Current | Risk Factor |
|---------|---------|-------------|
| `fastapi` | 0.115.8 | Check for Pydantic compatibility, Starlette version requirements |
| `pydantic` | 2.12.5 | V1→V2 was breaking; within V2 usually safe |
| `sqlalchemy` | 2.0.45 | 1.x→2.x was breaking; within 2.x check deprecation removals |
| `uvicorn` | 0.40.0 | Usually safe, but check Starlette compatibility |
| `httpx` | 0.28.1 | API changes occasionally; check if async patterns changed |
| `bcrypt` | 5.0.0 | 4.x→5.x changed truncation behavior (we handle this) |

### 🔴 Research Before Major Version Updates

| Package | Current | Known Issues |
|---------|---------|--------------|
| `reportlab` | 4.4.7 | 3.x→4.x removed C extensions, changed XML parser defaults. Test PDF generation thoroughly after updates. |
| `pypdf` | 5.4.0 | Major versions can change merge/fill behavior. Test IRS form generation. |

---

## Package-Specific Notes

### FastAPI + Pydantic + Starlette

These three are tightly coupled. When updating:
1. Check FastAPI's requirements for Pydantic version range
2. Check FastAPI's requirements for Starlette version range
3. Update together if needed
4. Test all API endpoints after update

**Current coupling (as of 0.115.x):**
- Requires Pydantic V2 (V1 support deprecated, removal imminent)
- Requires Starlette >=0.40.0,<0.46.0

### SQLAlchemy

**2.0 Migration:** Completed. We use 2.0-style patterns.

**Watch for:**
- Deprecation of `Query.get()` → Use `Session.get()` ✅ (already migrated)
- Deprecation of `declarative_base()` location → **TODO** (see deprecations table)

**After updating:** Run FIFO tests to ensure lot calculations still work.

### Bcrypt

**5.0 Breaking Change:** No longer silently truncates passwords >72 bytes.

**Our mitigation:** `User.set_password()` raises `ValueError` if password >72 bytes.

**Testing:** `test_password_migration.py` covers this edge case.

### ReportLab

**4.0 Changes:**
- Removed C extensions (rl_accel) - Python-only now
- Default XML parser changed to lxml
- New rendering backend (rlPyCairo)

**After updating:** Generate test PDFs:
```bash
curl "http://localhost:8000/api/reports/complete_tax_report?year=2024" -o /tmp/test.pdf
curl "http://localhost:8000/api/reports/irs_reports?year=2024" -o /tmp/irs.pdf
```

### PyPDF

Used for merging IRS form PDFs. After updates:
```bash
# Test IRS form generation (uses pypdf for merging)
curl "http://localhost:8000/api/reports/irs_reports?year=2024" -o /tmp/irs.pdf
# Verify PDF opens and has multiple pages
```

---

## Update Procedure

### Standard Update (Single Package)

```bash
# 1. Check current version
grep "package-name" backend/requirements.txt

# 2. Check latest version and changelog
# Visit https://pypi.org/project/package-name/
# Read changelog for breaking changes

# 3. Update requirements.txt
# Edit the version number

# 4. Install and test
pip install -r backend/requirements.txt
python3 backend/tests/test_everything.py

# 5. If tests pass, commit
git add backend/requirements.txt
git commit -m "deps: Update package-name X.Y.Z → A.B.C"
```

### Bulk Update (Multiple Packages)

Only do this for clearly safe updates (patch versions, security fixes):

```bash
# 1. Update requirements.txt with new versions

# 2. Install all
pip install -r backend/requirements.txt --upgrade

# 3. Run ALL tests
python3 backend/tests/test_everything.py
pytest backend/tests/test_password_migration.py -v
./scripts/pre-commit.sh

# 4. Generate test reports
curl "http://localhost:8000/api/reports/complete_tax_report?year=2024" -o /tmp/test.pdf
curl "http://localhost:8000/api/reports/irs_reports?year=2024" -o /tmp/irs.pdf

# 5. Test CSV roundtrip (handled by test_everything.py)

# 6. Commit with summary
git add backend/requirements.txt
git commit -m "deps: Update multiple packages to latest versions

- package1 X.Y.Z → A.B.C
- package2 X.Y.Z → A.B.C
..."
```

---

## Checking for Updates

### Manual Check

```bash
# List outdated packages
pip list --outdated
```

### Automated Check (pip-audit for security)

```bash
# Install pip-audit
pip install pip-audit

# Check for known vulnerabilities
pip-audit -r backend/requirements.txt
```

---

## Version Pinning Strategy

We use **exact pinning** (`==`) for reproducibility:

```
fastapi==0.115.8    # Exact version
```

**Why:** Prevents surprise breakage from automatic updates in CI/CD or Docker builds.

**Trade-off:** Requires manual updates, but gives us control over when changes happen.

---

## When to Update

### Update Immediately

- Security vulnerabilities (check `pip-audit`)
- Bug fixes affecting our functionality
- Deprecation warnings becoming errors

### Update Periodically (Monthly)

- Patch versions of all packages
- Minor versions of 🟢 safe packages

### Update Carefully (As Needed)

- Major versions (research first)
- Packages with known breaking change history

---

## Rollback Procedure

If an update breaks something:

```bash
# 1. Check git log for the update commit
git log --oneline backend/requirements.txt

# 2. Revert to previous version
git checkout <previous-commit> -- backend/requirements.txt

# 3. Reinstall
pip install -r backend/requirements.txt

# 4. Verify tests pass
python3 backend/tests/test_everything.py

# 5. Commit the rollback
git add backend/requirements.txt
git commit -m "revert: Rollback package-name due to [issue]"
```

---

## Dependencies Not in requirements.txt

### System Dependencies

| Dependency | Purpose | Install |
|------------|---------|---------|
| `pdftk` | IRS form PDF filling | `brew install pdftk-java` (macOS) or `apt install pdftk` (Linux) |

**Testing pdftk:**
```bash
pdftk --version
# Should output version info, not "command not found"
```

### Frontend Dependencies

Managed separately in `frontend/package.json`. See frontend documentation for Node.js dependency management.

---

## Maintenance Checklist

Use this checklist during maintenance sessions:

- [ ] Run `pip list --outdated` to see available updates
- [ ] Check for new deprecation warnings in test output
- [ ] Update deprecation table in this document if new warnings found
- [ ] Address any **TODO** deprecations if time permits
- [ ] Run full test suite after any changes
- [ ] Update "Last Reviewed" date at top of this document

---

## Contact & Escalation

If uncertain about an update:
1. Research the changelog thoroughly
2. Test in isolation before committing
3. Ask the user before proceeding with risky updates
4. Document any new gotchas in this file for future reference
