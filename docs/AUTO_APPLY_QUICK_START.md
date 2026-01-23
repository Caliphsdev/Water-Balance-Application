# Auto-Apply Pump Transfers - Quick Start Guide

**Status:** ✅ Backend Complete | ⏳ UI Confirmation Pending  
**Tests:** 2/2 PASSING (22/22 backend suite)  
**Deployment:** READY after UI confirmation flow

---

## What It Does

Automatically applies calculated pump transfers to facility volumes during water balance calculations. When a facility reaches 70% capacity (configurable), the system:

1. **Calculates** 5% transfer to destination facility
2. **Applies** volume changes transactionally (all-or-nothing)
3. **Records** event in `pump_transfer_events` table (audit trail)
4. **Prevents** double-application via idempotency check

---

## Configuration (app_config.yaml)

```yaml
features:
  # Master switch (enables auto-apply feature)
  auto_apply_pump_transfers: true
  
  # Rollout scope: 'global' | 'pilot-area'
  auto_apply_pump_transfers_scope: 'pilot-area'
  
  # Pilot areas (only used when scope='pilot-area')
  auto_apply_pump_transfers_pilot_areas: ['UG2N']
```

---

## Pilot vs Global Deployment

### Pilot Mode (Recommended First)
```yaml
scope: 'pilot-area'
pilot_areas: ['UG2N']
```
- **Only** UG2N facilities receive auto-apply transfers
- Other areas (MERM, OLDTSF, etc.) calculated but **not applied**
- Monitor for 1-2 weeks before global rollout
- Log: "Auto-applied 1 pump transfer(s)" (only UG2N)

### Global Mode (After Pilot Success)
```yaml
scope: 'global'
pilot_areas: []  # Ignored when scope='global'
```
- **All** facilities across all 8 mining areas receive auto-apply
- Higher volume of transfers, more complex redistribution
- Requires careful monitoring of closure errors
- Log: "Auto-applied 21 pump transfer(s)" (all production facilities)

---

## Running Tests

### Quick Validation (2 tests)
```bash
.venv\Scripts\python -m pytest tests/test_auto_apply_pump_transfers.py tests/test_auto_apply_pump_transfers_pilot.py -v
```
**Expected:** `2 passed in ~2s`

### Full Backend Suite (22 tests)
```bash
.venv\Scripts\python -m pytest tests/ -v --ignore=tests/ui --ignore=tests/test_licensing -k "not ui"
```
**Expected:** `22 passed in ~10s`

### Run Specific Test
```bash
# Test 1: Global scope
.venv\Scripts\python -m pytest tests/test_auto_apply_pump_transfers.py::test_auto_apply_pump_transfers_updates_volumes_transactionally -v

# Test 2: Pilot-area gating
.venv\Scripts\python -m pytest tests/test_auto_apply_pump_transfers_pilot.py::test_pilot_area_gating_applies_only_to_configured_area -v
```

---

## Test Details

### Test 1: Global Scope (test_auto_apply_pump_transfers.py)
- **Date:** 2024-12-15 (unique to avoid conflicts)
- **Scope:** `global` (all facilities)
- **Fixtures:** SRC_TEST, DST_TEST (both UG2N area)
- **Validation:** 
  - SRC: 80k → 75k (5k transferred)
  - DST: 60k → 65k (5k received)
  - Event recorded in `pump_transfer_events`

### Test 2: Pilot-Area Gating (test_auto_apply_pump_transfers_pilot.py)
- **Date:** 2024-11-20 (unique to avoid conflicts)
- **Scope:** `pilot-area` with `pilot_areas=['UG2N']`
- **Fixtures:**
  - **UG2N (PILOT):** SRC_UG2N, DST_UG2N → **TRANSFERRED**
  - **MERM (NON-PILOT):** SRC_MERM, DST_MERM → **UNCHANGED**
- **Validation:**
  - UG2N: SRC 80k→75k, DST 60k→65k ✅
  - MERM: SRC 80k→80k, DST 60k→60k ✅ (gated correctly)

---

## Critical Insights

### Idempotency Fix (REQUIRED)
Both tests clean up `pump_transfer_events` for their test date at start:
```python
db.execute_update("DELETE FROM pump_transfer_events WHERE calc_date = ?", (test_date,))
```
**Why:** Previous test runs leave records that block transfers (same date+source+dest tuple). Without cleanup, transfers silently skipped.

### Unique Test Dates
- Test 1: `date(2024, 12, 15)`
- Test 2: `date(2024, 11, 20)`

**Why:** Different dates prevent cross-test contamination. If both used same date, cleanup in one test would affect the other.

### Config Isolation
Each test sets its own config values via `config.set()`:
- Test 1: Sets `scope='global'`
- Test 2: Sets `scope='pilot-area'` and `pilot_areas=['UG2N']`

**Verified:** Config changes don't bleed between tests when run together.

---

## Next Steps (UI Implementation)

### 1. Add Confirmation Dialog (src/ui/calculations.py)

**Before:**
```python
# Current: Auto-applies immediately (no user interaction)
calc.calculate_water_balance(date)
```

**After:**
```python
# Calculate (don't apply yet)
result = calc.calculate_water_balance(date, auto_apply=False)
pump_transfers = result.get('pump_transfers', {})

# Show confirmation dialog if transfers exist
if pump_transfers:
    dialog = PumpTransferConfirmDialog(parent, pump_transfers, date)
    if dialog.show() == 'apply':
        # User confirmed - apply transfers
        db.apply_pump_transfers(date, pump_transfers, user=config.get_current_user())
        # Recalculate with updated volumes
        result = calc.calculate_water_balance(date, auto_apply=False)
    else:
        # User cancelled - use calculated transfers for display only
        pass
```

### 2. Dialog Design (src/ui/pump_transfer_confirm_dialog.py)

**Components:**
- **Title:** "Confirm Pump Transfers for {date}"
- **Summary:** "Apply {count} pump transfer(s) totaling {total_volume} m³"
- **Transfer List (Table):**
  - Source Facility | Destination | Volume (m³) | New Level (%)
  - SRC_UG2N | DST_UG2N | 5000 | 75% → 65%
- **Buttons:**
  - "Apply" (primary, green)
  - "Cancel" (secondary, gray)

### 3. Monitoring Dashboard

**Add to Analytics:**
- Pump transfers applied (count per day/month)
- Total volume transferred (m³)
- Facilities most frequently transferring
- Closure error trends before/after transfers

---

## Troubleshooting

### Tests Failing with "assert 80000.0 == 75000.0"
**Symptom:** Volumes unchanged when should be transferred  
**Cause:** Idempotency blocking (existing `pump_transfer_events` records)  
**Fix:** Run cleanup at start of test:
```python
db.execute_update("DELETE FROM pump_transfer_events WHERE calc_date = ?", (test_date,))
```

### Pilot Gating Not Working
**Symptom:** Non-pilot areas receiving transfers  
**Debug:** Add logging to `db_manager.py` line 344:
```python
logger.info(f"[PILOT-GATING] scope={scope}, pilot_areas={pilot_areas}")
```
**Check:** Verify `config.get('features.auto_apply_pump_transfers_scope')` returns 'pilot-area'

### Transfer Volume Incorrect
**Check:**
- Facility `total_capacity` in database (transfer = 5% of capacity)
- `TRANSFER_INCREMENT = 0.05` in `pump_transfer_engine.py`
- Destination has available capacity (not already >70%)

---

## Key Files

**Production Code:**
- `src/utils/water_balance_calculator.py` (lines 1185-1201) - Feature flag check
- `src/database/db_manager.py` (lines 340-420) - Application logic with pilot gating
- `src/utils/pump_transfer_engine.py` - Transfer calculation engine
- `config/app_config.yaml` - Feature flags and pilot areas

**Tests:**
- `tests/test_auto_apply_pump_transfers.py` - Global scope test
- `tests/test_auto_apply_pump_transfers_pilot.py` - Pilot-area gating test
- `tests/test_pump_transfer_integration.py` - Engine integration tests (7 tests)

**Documentation:**
- `TEST_VALIDATION_SUMMARY.md` - Comprehensive test results and debug journey
- `AUTO_APPLY_QUICK_START.md` (this file) - Quick reference for developers

---

## Performance Benchmarks

- **Single test:** ~0.9s
- **Both tests:** ~2.1s
- **Full backend suite (22 tests):** ~10s
- **Balance calculation:** ~700-800ms (computed), ~0ms (cached)
- **Transfer application:** <10ms per transfer

---

## Production Deployment Checklist

- [x] Backend logic implemented and tested
- [x] Idempotency mechanism working
- [x] Pilot-area gating validated
- [x] Feature flags functional
- [x] Tests passing (22/22)
- [ ] UI confirmation dialog implemented
- [ ] Pilot deployment (UG2N only, 1-2 weeks)
- [ ] Monitoring dashboard updated
- [ ] Global rollout (all areas)
- [ ] User manual updated

---

**Last Updated:** January 23, 2026  
**Test Status:** ✅ 2/2 PASSING  
**Deployment Status:** READY after UI confirmation flow
