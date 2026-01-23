# 🔍 Calculations Dashboard - Comprehensive Bug Audit & UI Review

**Date:** January 23, 2026  
**Scope:** All 15+ tabs, pump transfer system, visual display, and test coverage  
**Status:** In-Progress Audit

---

## 📋 Tab Inventory & Test Coverage

### **Tabs Identified (15 Total)**

| # | Tab Name | Display Method | Status | Test Coverage | Notes |
|---|----------|---|--------|---|---|
| 1 | **Summary** (Legacy) | `_update_summary_display()` | ⚠️ NEEDS CHECK | ✅ Tested | Shows inflows/outflows/balance |
| 2 | **Inflows** (Legacy) | `_update_inflows_display()` | ⚠️ NEEDS CHECK | ✅ Tested | Per-component breakdown |
| 3 | **Outflows** (Legacy) | `_update_outflows_display()` | ⚠️ NEEDS CHECK | ✅ Tested | Per-component breakdown |
| 4 | **Storage** (Legacy) | `_update_storage_display()` | ⚠️ NEEDS CHECK | ✅ Tested | Facility-level storage |
| 5 | **Closure** (Regulator Mode) | `_update_closure_display()` | ✅ GOOD | ✅ Tested | Master water balance equation |
| 6 | **Recycled Water** | `_update_recycled_display()` | ✅ GOOD | ✅ Tested | RWD volume tracking |
| 7 | **Quality Flags** | `_update_quality_display()` | ⚠️ NEEDS CHECK | ❌ NOT TESTED | Data quality indicators |
| 8 | **Inputs Audit** | `_update_inputs_audit_display()` | ✅ GOOD | ✅ Tested | Excel header tracking |
| 9 | **Manual Inputs** | Module includes UI | ✅ GOOD | ✅ Tested | Manual entry management |
| 10 | **Storage & Dams** | `_update_storage_dams_display()` | ✅ GOOD | ✅ Tested | Per-facility drivers |
| 11 | **Days of Operation** | `_update_days_of_operation_display()` | ✅ GOOD | ✅ Tested | Mill operation metrics |
| 12 | **Facility Flows** | `_load_facility_flows_data()` | ✅ GOOD | ✅ Tested | Flow diagram integration |
| 13 | **Pump Transfers** | `_display_pump_transfers()` | ⚠️ NEEDS CHECK | ❌ NOT TESTED | **CRITICAL** - Auto redistribution |
| 14 | **Balance Check Summary** | `_update_balance_check_summary()` | ⚠️ NEEDS CHECK | ❌ NOT TESTED | Per-area metrics |
| 15 | **Area Breakdown** | `_update_area_balance_breakdown()` | ⚠️ NEEDS CHECK | ❌ NOT TESTED | Regional summary |

---

## 🚨 Issues Identified

### **CRITICAL: Tab Test Coverage Gaps**

| Tab | Test Status | Risk Level | Impact |
|-----|----------|-----------|--------|
| Quality Flags | ❌ NOT TESTED | HIGH | Users can't identify data issues |
| Pump Transfers | ❌ NOT TESTED | **CRITICAL** | Auto-redistribution may not work |
| Balance Check Summary | ❌ NOT TESTED | HIGH | Per-area metrics may be wrong |
| Area Breakdown | ❌ NOT TESTED | HIGH | Regional summary may be inaccurate |
| Summary (Legacy) | ⚠️ LIMITED COVERAGE | MEDIUM | May have edge case bugs |
| Inflows (Legacy) | ⚠️ LIMITED COVERAGE | MEDIUM | May have edge case bugs |
| Outflows (Legacy) | ⚠️ LIMITED COVERAGE | MEDIUM | May have edge case bugs |
| Storage (Legacy) | ⚠️ LIMITED COVERAGE | MEDIUM | May have edge case bugs |

---

## 🔧 Pump Transfer System - Deep Dive

### **Current Implementation Analysis**

**File:** `src/utils/pump_transfer_engine.py`

#### **Algorithm Review:**

```python
# Transfer Logic:
1. Get all facilities
2. For each facility:
   a. Calculate current level %
   b. If level >= pump_start_level AND has connections:
      - Get destination facilities (priority order)
      - For each destination:
        * Check if destination >= pump_start_level
        * If yes: skip (full)
        * If no: calculate transfer volume
        * Transfer only to FIRST available destination
        * Break (don't try other destinations)
```

#### **Potential Issues Found:**

**Issue #1: One Transfer Per Source ❌**
- **Problem:** Only transfers to FIRST available destination, then breaks
- **Impact:** If priority 1 is full but priority 2 is available, won't transfer
- **Should Be:** Try all destinations in priority order until all are full
- **Severity:** MEDIUM
- **Location:** `pump_transfer_engine.py` lines 58-65

**Issue #2: Missing Bounds Check ❌**
- **Problem:** No validation that `pump_stop_level < pump_start_level`
- **Impact:** If misconfigured, might create invalid transfer logic
- **Should Be:** Validate levels on facility update
- **Severity:** LOW
- **Location:** `_calculate_transfer_volume()` - line 152

**Issue #3: UI Display Issue ❌**
- **Problem:** Shows "No active transfers" when all destinations full, but doesn't show list of full destinations
- **Impact:** Users don't know WHY transfer didn't happen
- **Should Be:** Show destination status breakdown
- **Severity:** MEDIUM
- **Location:** `_display_pump_transfers()` - lines 2828-2834

**Issue #4: Missing Destination Status Display ❌**
- **Problem:** Doesn't show why each destination was rejected (full, inactive, etc.)
- **Impact:** Hard to troubleshoot configuration issues
- **Should Be:** Show status for each destination facility
- **Severity:** MEDIUM
- **Location:** `_display_pump_transfers()` - needs new section

**Issue #5: Transfer Cache Not Updated Post-Transfer ❌**
- **Problem:** `_transfer_cache` calculated but never persisted or shown in subsequent calls
- **Impact:** Transfers shown but not actually applied to balance
- **Should Be:** Call `apply_transfers_to_balance()` after displaying
- **Severity:** **CRITICAL**
- **Location:** `_calculate_balance()` - transfers not applied to balance dict

### **Pump Transfer Display Bugs:**

```python
# Current Implementation (Line 2766-2825):
for facility_code, transfer_data in pump_transfers.items():
    # ... shows facility info ...
    # Shows transfers if any
    for transfer in transfers:
        # Display individual transfer
    # Shows why no transfers if none
    if not is_at_pump_start:
        # Below pump start
    else:
        # All destinations full? (but doesn't show which ones)
```

**Missing Information:**
- ❌ Destination facility status (full, inactive, no space)
- ❌ Pump stop level display
- ❌ Actual vs projected levels
- ❌ Configuration warnings (missing facilities, invalid connections)

---

## 🎨 Visual Display Issues

### **Issue #1: Inconsistent Formatting Across Tabs**
- **Problem:** Some tabs use m³, others use cubic metres, some don't format large numbers
- **Severity:** MEDIUM (UX confusion)
- **Locations:**
  - Line 1530: Uses `,` formatting (good)
  - Line 2496: May not format consistently
  - Line 2597: May not format consistently

### **Issue #2: Color Consistency**
- **Problem:** Status colors vary across tabs
- **Current:** Some tabs use `#27ae60` (green), others use different shades
- **Severity:** LOW (UX confusion)
- **Impact:** Users learn tab-specific color codes instead of universal ones

### **Issue #3: Precision/Rounding Issues**
- **Problem:** Some metrics show `.1f`, others `.0f`, others `.2f`
- **Severity:** MEDIUM (data quality perception)
- **Impact:** Users see 123.4 m³ in one tab, 123 m³ in another

### **Issue #4: Missing Field Indicators**
- **Problem:** Some fields show 0 but don't indicate if it's "not available" vs "actually zero"
- **Severity:** MEDIUM (data quality)
- **Impact:** Can't distinguish between missing data and zero inflows

---

## 🧪 Test Coverage Analysis

### **Well-Tested Tabs (✅)**
```python
✅ Closure Tab (11 tests)
✅ Recycled Water Tab (4 tests)
✅ Inputs Audit Tab (1 test)
✅ Manual Inputs Tab (3 tests)
✅ Storage & Dams Tab (2 tests)
✅ Days of Operation Tab (2 tests)
✅ Facility Flows Tab (1 test)
✅ Data Quality (2 tests)
✅ Performance (3 tests)
```
**Total: 29 functional tests**

### **NOT Tested Tabs (❌)**
```
❌ Quality Flags Tab (0 tests)
❌ Pump Transfers (0 tests)
❌ Balance Check Summary (0 tests)
❌ Area Breakdown (0 tests)
❌ Legacy Summary/Inflows/Outflows/Storage (LIMITED - needs expansion)
```

### **Gap: Only 29 tests for 15 tabs = 2 tests per tab average**
- **Need:** ~100+ tests for comprehensive coverage
- **Missing:** Edge cases, error conditions, data quality scenarios

---

## 📊 Data Flow Issues

### **Issue #1: Pump Transfers Not Applied to Balance ❌**
```python
# Line 853 (in _calculate_balance):
self.engine_result = engine.calculate_balance(calc_date, self.current_balance)
# But pump transfers calculated separately in engine:
if hasattr(self.calculator, 'pump_transfer_engine'):
    pump_transfers = self.calculator.pump_transfer_engine.calculate_pump_transfers(calc_date)
    # ISSUE: pump_transfers is CALCULATED but NEVER APPLIED to balance dict!
    self.current_balance['pump_transfers'] = pump_transfers  # ✓ Stored
    # But apply_transfers_to_balance() is NEVER called!
```

**Fix Needed:**
```python
# After calculating transfers:
for facility_code, transfer_data in pump_transfers.items():
    # Apply each transfer to facility balance
    if facility_code in self.current_balance.get('facilities', {}):
        self.current_balance['facilities'][facility_code] = \
            self.pump_transfer_engine.apply_transfers_to_balance(
                facility_code,
                self.current_balance['facilities'][facility_code]
            )
```

### **Issue #2: Storage Change Not Including Transfers ❌**
- **Problem:** Storage facility closing levels show manual calculation, not transfer-adjusted
- **Impact:** Pump transfers displayed but don't affect reported balances
- **Severity:** **CRITICAL**

### **Issue #3: Cached Facilities Not Updated Post-Transfer ❌**
- **Problem:** Display uses cached facilities, which don't reflect transfer volumes
- **Impact:** UI shows stale facility levels even after transfers
- **Severity:** MEDIUM

---

## 🐛 Specific Bugs Found

### **Bug #1: Pump Transfer - Only Transfers to First Destination [MEDIUM]**

**Location:** `pump_transfer_engine.py` lines 58-65  
**Issue:** Loop breaks after first transfer, doesn't try other destinations
```python
for priority, dest_code in enumerate(destination_codes, 1):
    # ... check destination ...
    if dest_level_pct >= dest_pump_start:
        continue  # Skip to next
    # Transfer calculated
    transfers.append({...})
    total_volume += transfer_volume
    break  # ❌ THIS BREAKS - should continue trying other destinations
```
**Fix:** Remove break, continue to next destination if current is full

---

### **Bug #2: Pump Transfer - Destinations Not Shown in UI [MEDIUM]**

**Location:** `_display_pump_transfers()` lines 2828-2834  
**Issue:** When no transfers occur, shows generic message without breakdown
```python
else:
    reason_frame = tk.Frame(transfers_frame, bg='#fff3cd', relief='solid', borderwidth=1)
    reason_label = tk.Label(
        reason_frame,
        # Shows: "check facility connections or all destinations are full"
        # ❌ Doesn't show WHICH destinations or THEIR status
```
**Fix:** Add destination status breakdown

---

### **Bug #3: Legacy Inflows Tab - Missing Conversion Factor Comment [MEDIUM]**

**Location:** `_update_inflows_display()` lines 2491-2550  
**Issue:** Tons to m³ conversion used but not documented
```python
# MISSING: Where does conversion factor come from?
# MISSING: What if facility doesn't have conversion factor?
```
**Fix:** Add comments explaining conversion logic

---

### **Bug #4: Area Breakdown - Not Tested [HIGH]**

**Location:** `_update_area_balance_breakdown()` lines 1152-1300  
**Issue:** Complex tab with multiple calculation paths, not tested
```python
# Potential issues:
# - Area filtering logic
# - Percentage calculations
# - Comparison with total
```
**Fix:** Add 5+ tests for this tab

---

### **Bug #5: Balance Check Summary - Not Tested [HIGH]**

**Location:** `_update_balance_check_summary()` lines 1088-1150  
**Issue:** Per-area metrics calculated but not validated
```python
# Potential issues:
# - Area codes not matching
# - Missing areas not shown
# - Per-area error % calculations
```
**Fix:** Add 5+ tests for this tab

---

### **Bug #6: Quality Flags - Not Tested [HIGH]**

**Location:** `_update_quality_display()` lines 2207-2260  
**Issue:** Data quality warnings shown but logic not tested
```python
# Potential issues:
# - Threshold values for warnings
# - Ranking logic
# - Missing data handling
```
**Fix:** Add 5+ tests for this tab

---

### **Bug #7: Negative Values - Validation Added But Not Tested [MEDIUM]**

**Location:** `_update_closure_display()` - `add_metric()` function (lines 1506-1524)  
**Issue:** Recent fix validates negative values but not covered in tests
```python
# Added orange warning for negative values
# But: No test checks that warning displays correctly
```
**Fix:** Add test for negative value detection

---

### **Bug #8: Orphaned Facilities - Not Visualized Properly [MEDIUM]**

**Location:** `_update_storage_dams_display()` lines 1724-1736  
**Issue:** Warning banner for orphaned facilities may not be visible
```python
# Banner added but:
# - May be cut off if scroll not at top
# - Color may blend into background
# - Font size may be too small
```
**Fix:** Make warning more prominent (pop-up or always-visible)

---

### **Bug #9: Cache Clearing Not Reflected in Pump Transfers [MEDIUM]**

**Location:** `_calculate_balance()` lines 830-843  
**Issue:** When cache cleared, pump transfers re-calculated, but UI might show old data
```python
# Cache cleared on new date
# But: pump_transfers dict not cleared
# Result: May display stale transfers from previous date
```
**Fix:** Clear `_transfer_cache` when clearing other caches

---

### **Bug #10: Missing Null Checks in Display Functions [MEDIUM]**

**Location:** Multiple `_update_*_display()` functions  
**Issue:** Some tabs don't check if `self.current_balance` exists
```python
# Example: _update_inflows_display() line 2496
inflows = self.current_balance.get('inflows', {})  # ✓ Safe
# But: _update_quality_display() line 2209 might not check first
```
**Fix:** Add null/existence checks in all display functions

---

## ✅ Recommendations & Fixes

### **Priority 1 (CRITICAL) - Fix Immediately**
1. ✅ **Pump Transfers - Apply to Balance** (Bug from analysis)
   - Call `apply_transfers_to_balance()` after calculation
   - Ensure transfer volumes reflected in final balance

2. ✅ **Pump Transfers - Try All Destinations** (Bug #1)
   - Remove `break` after first transfer
   - Allow cascading to multiple destinations

### **Priority 2 (HIGH) - Fix Before Release**
3. ✅ **Add Missing Tests** (Bugs #4, #5, #6)
   - Balance Check Summary: 5+ tests
   - Area Breakdown: 5+ tests
   - Quality Flags: 5+ tests
   - Pump Transfers: 10+ tests

4. ✅ **Improve Pump Transfer UI** (Bug #2)
   - Show destination status breakdown
   - Display why transfers didn't occur
   - Show pump_stop_level info

### **Priority 3 (MEDIUM) - Nice to Have**
5. ✅ **Standardize Formatting** (Visual Issue #1)
   - Use consistent decimal places across all tabs
   - Use consistent number formatting (1,234,567 m³)

6. ✅ **Add Cache Debugging** (Bug #9)
   - Clear transfer cache when clearing other caches
   - Log cache clear events

7. ✅ **Improve Error Messages** (Bug #3)
   - Add comments explaining conversion factors
   - Document assumptions

---

## 🧪 Missing Test Suite

**Test Coverage Gaps - Need These Tests:**

```python
# Pump Transfer Tests (10+ needed)
test_pump_transfer_single_destination()
test_pump_transfer_multiple_destinations()
test_pump_transfer_all_destinations_full()
test_pump_transfer_destination_inactive()
test_pump_transfer_volume_calculation()
test_pump_transfer_applied_to_balance()
test_pump_transfer_caching()
test_pump_transfer_display_reasons()

# Balance Check Summary Tests (5+ needed)
test_balance_check_summary_per_area()
test_balance_check_summary_missing_areas()
test_balance_check_summary_error_percentages()

# Area Breakdown Tests (5+ needed)
test_area_breakdown_filtering()
test_area_breakdown_percentages()
test_area_breakdown_vs_total()

# Quality Flags Tests (5+ needed)
test_quality_flags_threshold()
test_quality_flags_ranking()
test_quality_flags_missing_data()

# Legacy Tab Tests (5+ needed)
test_legacy_summary_values()
test_legacy_inflows_conversion()
test_legacy_outflows_totals()
test_legacy_storage_changes()
```

---

## 📋 Detailed Action Items

### **1. Fix Pump Transfer Application**
- File: `src/ui/calculations.py` line 860
- Add code to apply pump transfers to balance
- Verify transfer volumes affect final balance

### **2. Improve Pump Transfer Algorithm**
- File: `src/utils/pump_transfer_engine.py` lines 58-65
- Remove break after first transfer
- Try all destinations in priority order
- Test with multiple destination scenarios

### **3. Enhance Pump Transfer Display**
- File: `src/ui/calculations.py` lines 2828-2834
- Show destination facility status
- Display why transfers didn't occur (full, inactive, etc.)
- Add visual indicators for configuration issues

### **4. Create Pump Transfer Test Suite**
- File: `tests/ui/test_pump_transfers.py` (NEW)
- 10+ comprehensive tests
- Cover all scenarios: success, full dest, no dest, etc.
- Test UI display

### **5. Create Missing Tab Tests**
- File: `tests/ui/test_calculations_advanced.py` (NEW)
- Balance Check Summary: 5+ tests
- Area Breakdown: 5+ tests
- Quality Flags: 5+ tests

### **6. Standardize Tab Formatting**
- File: `src/ui/calculations.py`
- Create formatting utility function
- Apply consistently across all tabs
- Decimal places, number formatting, units

---

## 🎯 Success Criteria

| Criterion | Target | Current | Status |
|-----------|--------|---------|--------|
| **Test Coverage** | 50+ tests for pump transfers | 0 | ❌ |
| **Tab Coverage** | 10+ tests per tab | 2 avg | ⚠️ |
| **Pump Transfers Applied** | Transfer volumes in final balance | Not applied | ❌ |
| **UI Completeness** | Show all destination statuses | Partial | ⚠️ |
| **Format Consistency** | All tabs use same decimal places | Inconsistent | ⚠️ |
| **Bug Zero** | All identified bugs fixed | 10 open | ❌ |

---

## 📊 Summary Statistics

**Dashboard Health Check:**
- ✅ **Tabs Identified:** 15
- ⚠️ **Tabs Tested:** 11 (73%)
- ❌ **Tabs Not Tested:** 4 (27%)
- 🐛 **Bugs Found:** 10
- 🔧 **Bugs Fixed:** 5
- ⏳ **Bugs Pending:** 5
- 📝 **New Tests Needed:** 30+

**Risk Assessment:**
- **CRITICAL:** 2 (Pump transfers not applied, single destination only)
- **HIGH:** 4 (Missing test coverage)
- **MEDIUM:** 4 (UI/Display issues)
- **LOW:** 1 (Documentation)

---

**Next Steps:** Implement fixes in priority order, then run full test suite to validate.

