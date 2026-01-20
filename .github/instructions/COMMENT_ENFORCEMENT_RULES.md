# Comment Enforcement Rules for Code Generation

**Status:** MANDATORY for all code changes  
**Effective Date:** January 20, 2026  
**Applies To:** All Python files in `src/` directory

## Golden Rule

**EVERY code change MUST include comment updates or the code will be REJECTED.**

No exceptions. No "I'll add comments later." Comments are part of the implementation.

## Enforcement Checklist

Before submitting any code change, verify:

### ✅ Module Level (Every File)
```python
"""
Module Purpose - One sentence summary

Detailed description of:
- What this module does
- What data sources it uses (Excel sheets, DB tables)
- Key dependencies
- Main entry points
"""
```

### ✅ Class Level (Every Class)
```python
class ClassName:
    """Class Purpose (SHORT LABEL).
    
    Multi-line description:
    - What the class does
    - Key methods
    - State management
    - Dependencies
    """
```

### ✅ Function Level (Every Function/Method)
```python
def function_name(arg1: Type1, arg2: Type2) -> ReturnType:
    """Function purpose (DESCRIPTIVE LABEL).
    
    Multi-line explanation:
    - What it does
    - When to call it
    - Prerequisites
    
    Args:
        arg1: Description of what arg1 should be
        arg2: Description of what arg2 should be
    
    Returns:
        Description of return value and structure
    
    Raises:
        ExceptionType: When/why this exception is raised
    
    Example:
        result = function_name(value1, value2)
    """
```

### ✅ Complex Logic (Every Complex Block)
```python
# Explain WHY this logic exists, not WHAT it does
# Business rule: [explain the reason]
# Example: Cache results keyed by (date, facility) to avoid re-reads from Excel
```

### ✅ Cache Usage (Every Cache)
```python
# Cache strategy:
# - Key format: {date}_{facility_code}
# - TTL: Session (cleared on Excel reload)
# - Invalidation trigger: call clear_cache() when Excel updated
# - Why: Avoid expensive file I/O on repeated calculations
```

### ✅ Data Source Clarity (Every Excel/DB Query)
```python
# Read from METER READINGS Excel ("Meter Readings" sheet):
# - Column A: tonnes_milled
# - Column B: rwd_volume
# - File: legacy_excel_path (data\New Water Balance...xlsx)
# - NOT the Flow Diagram Excel (timeseries_excel_path)
```

### ✅ Excel File Distinction (CRITICAL)
Every Excel operation MUST clarify which Excel file:
```
❌ BAD:
data = loader.get_volume('UG2N', 3)

✅ GOOD:
# Load flow volume from Flow Diagram Excel (Flows_UG2N sheet), March data
# NOT from Meter Readings Excel - that file has operational metrics
data = flow_loader.get_volume('UG2N', 3)
```

### ✅ Error Handling (Every Exception)
```python
try:
    risky_operation()
except ValueError as e:
    # Input validation failed - user likely provided wrong month or facility
    logger.warning(f"Invalid input: {e}")
```

## Commit Message Requirements

Every commit MUST include comment-related information:

```
[Fix|Add|Refactor] [component] - [what changed]

- Updated [function] docstring to explain [change]
- Added inline comments to [section] explaining [business logic]
- Clarified [data source] vs [other data source] distinction
```

**Example:**
```
Fix balance calculation for OLDTSF

- Updated clear_cache() docstring to document invalidation triggers
- Added inline comments to _validate_facility_flows() explaining data quality checks
- Clarified difference between Meter Readings Excel vs Flow Diagram Excel
```

## Category-Specific Rules

### Database Operations
✅ Comment table names and column meanings  
✅ Explain joins and foreign key relationships  
✅ Document any schema migrations or special handling  
✅ Explain why query optimization is needed (if applicable)

**Example:**
```python
def get_facilities_by_area(self, area_code: str):
    """Get storage facilities for mining area (DATA RETRIEVAL).
    
    Queries storage_facilities table:
    - Filters by area_code (FK to mine_areas table)
    - Returns active facilities only (active = 1)
    - Ordered by facility priority for pump transfers
    """
```

### Calculation/Logic
✅ Explain the mathematical formula or algorithm  
✅ Document any assumptions or constraints  
✅ Reference business rules or regulatory requirements  
✅ Explain why this approach was chosen

**Example:**
```python
def calculate_balance(facility_code, month, year):
    """Calculate water balance (CORE ALGORITHM).
    
    Implements water balance equation:
    balance_error = fresh_inflows - outflows - delta_storage
    
    Science: Fresh water is conserved mass. Recycled water (RWD) shows as
    storage change (returns to TSF), not in direct balance.
    
    Closure < 5% indicates good data quality.
    > 5% suggests measurement errors.
    """
```

### Excel Integration
✅ Always specify WHICH Excel file (by full path and sheets)  
✅ Document column names and data types  
✅ Explain any data transformations or unit conversions  
✅ Reference the Excel file path from config

**Example:**
```python
def load_meter_readings(month, year):
    """Load operational metrics from Meter Readings Excel.
    
    File: legacy_excel_path (e.g., data/New Water Balance 20250930 Oct.xlsx)
    Sheet: "Meter Readings"
    Columns:
    - A: facility_code (text, e.g., 'UG2N')
    - B: tonnes_milled (numeric, tonnes/month)
    - C: rwd_volume (numeric, m³/month)
    
    Transformation: Convert tonnes to m³ using facility-specific conversion factor
    
    NOT from Flow Diagram Excel (different file, different data).
    """
```

### UI Components
✅ Explain what user sees and why  
✅ Document user interactions and flows  
✅ Reference data sources for displayed values  
✅ Explain tooltips and help text

**Example:**
```python
def display_balance_summary(self, balance_result):
    """Display water balance summary to user (UI RENDERING).
    
    Shows key metrics:
    - Fresh Inflows: Total natural water entering system
    - Total Outflows: All water leaving system
    - Balance Error: Closure error % (should be <5%)
    - Status: GREEN (<5%), RED (>5%)
    
    Data source: WaterBalanceCalculator.calculate_balance() result
    
    Tooltips explain metrics to educate users on water balance concepts.
    """
```

### Performance-Critical Code
✅ Explain why optimization is needed  
✅ Document cache strategy (key, TTL, invalidation)  
✅ Reference performance measurements or benchmarks  
✅ Explain trade-offs (speed vs memory vs clarity)

**Example:**
```python
def get_facility_level_pct(self, facility):
    """Calculate facility storage level percentage (PERFORMANCE CRITICAL).
    
    Called 100+ times per balance calculation, so must be fast.
    
    Cache strategy: Memoize by facility_code for duration of calculation
    - Key: facility_code
    - TTL: Single calculation (cleared on next month)
    - Why: Avoid repeated database queries
    
    Trade-off: Uses more memory but improves calculation speed by 10x
    """
```

## Anti-Patterns (WILL BE REJECTED)

### ❌ Comments that just repeat code
```python
# BAD:
volume = volume * 1000  # Multiply volume by 1000
facilities = db.query(...)  # Query facilities from database

# GOOD:
volume_m3 = volume_ml * 1000  # Convert mL (Meter Readings) to m³ for balance engine
facilities = db.query(...)  # Get active facilities; used for pump transfer priority order
```

### ❌ Missing data source information
```python
# BAD:
data = excel.get_value('column_B', row)

# GOOD:
# Load RWD volume from Meter Readings Excel, Sheet "Meter Readings", Column B
rwd_volume = meter_excel.get_value('RWD_m3', month)
```

### ❌ Unclear business logic
```python
# BAD:
if level > 70:
    transfer(0.05 * current_volume)

# GOOD:
# Pump transfer trigger: If facility level ≥ 70% (pump_start_level),
# start transferring 5% of current volume to downstream facilities.
# Business rule: Prevents overflow and ensures continuous supply.
if level >= facility.pump_start_level:  # Default 70%
    transfer_volume = current_volume * TRANSFER_INCREMENT  # 5% per operation
    transfer(transfer_volume)
```

### ❌ Undocumented cache usage
```python
# BAD:
self._cache[key] = result
return self._cache.get(key)

# GOOD:
# Cache balance result keyed by (date, facility) to avoid re-reading Excel
# TTL: Session (cleared when Excel reloaded)
# Why: Balance calculations hit Excel file 100+ times; caching improves speed 10x
cache_key = f"{date}_{facility_code}"
self._balance_cache[cache_key] = result
return self._balance_cache.get(cache_key)
```

## Validation

### Before Submission:
```bash
# Find functions without docstrings
grep -r "def " src/ | grep -v "\"\"\"" 

# Find classes without docstrings
grep -r "class " src/ | grep -v "\"\"\"" 

# Search for complex logic without comments
grep -r "for.*in.*:" src/ | wc -l  # Should be commented if non-obvious
```

### Code Review Checklist:
- [ ] Every function has docstring with purpose, args, returns
- [ ] Every class has docstring explaining purpose and state
- [ ] Complex logic has inline comments (WHY not WHAT)
- [ ] Cache usage is documented (key, TTL, invalidation)
- [ ] Data sources are clearly identified (which Excel file, sheet, column)
- [ ] Excel file distinction is clear (Meter Readings vs Flow Diagram)
- [ ] Business rules and constraints are explained
- [ ] Error conditions are documented
- [ ] Commit message references comment updates

## Consequences

### ✅ Code WITH proper comments:
- Gets merged quickly
- Is easier to maintain
- Prevents future bugs
- Helps new developers
- Builds professional reputation

### ❌ Code WITHOUT proper comments:
- Will be **REJECTED** on review
- Must be resubmitted with comments added
- Blocks merge and delays release
- Frustrates future maintainers
- Causes technical debt

## Questions?

If unsure about comments, check:
1. **Example in this file** - most cases covered
2. **Existing code** - follow patterns in similar functions
3. **Copilot Instructions** - detailed guidelines section
4. **Performance Guide** - for optimization-related comments

**Remember:** Comments are NOT optional. They are part of the definition of done.

---

**Last Updated:** January 20, 2026  
**Version:** 1.0  
**Status:** Active Enforcement
