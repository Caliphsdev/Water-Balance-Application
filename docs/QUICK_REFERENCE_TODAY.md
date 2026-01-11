# Quick Reference: What Changed Today

## For Users
**New Feature:** Monthly Tailings Moisture Input in Settings

**How to Use:**
```
Settings → ⚗️ Tailings & Process → Enter Month/Year/% → Save
```

**What It Does:**
- Lets you set tailings moisture for each month (0-100%)
- Used in System Balance calculation
- Replaces hardcoded 20% value

**Example Values:**
- January-March: 18.5% (dry season)
- October-December: 22% (wet season)

---

## For Developers

### New Database Table
```
tailings_moisture_monthly
├── month (1-12)
├── year (e.g., 2025)
├── tailings_moisture_pct (0-100%)
├── updated_at (timestamp)
└── UNIQUE(month, year)
```

### New Database Methods
```python
db.get_tailings_moisture_monthly(10, 2025)      # → 22.0 or None
db.set_tailings_moisture_monthly(10, 2025, 22.0) # → bool
db.get_tailings_moisture_all_months(2025)       # → {10: 22.0, ...}
```

### Calculator Data Flow
```
Database → Excel → 0% (fallback)
```

Old: Database → Excel → **20%** ❌
New: Database → Excel → **0%** ✅

### Files Changed
1. `schema.py` - Table definition
2. `db_manager.py` - CRUD methods  
3. `water_balance_calculator.py` - Priority change
4. `settings.py` - New UI tab

### Verification
```bash
# Compile check (no errors)
python -m py_compile src/ui/settings.py
python -m py_compile src/database/db_manager.py

# Database test (passed all tests)
python test_tailings_moisture.py
```

---

## Data Priority Pattern

Used for all optional inputs across system:

```
Tier 1: DATABASE (user control)
Tier 2: EXCEL (legacy/readonly)
Tier 3: CONSTANT (safe default)
```

**Applied to:**
- Regional Rainfall: DB → Excel → 0
- Regional Evaporation: DB → Excel → 0  
- Facility Flows: DB → Excel → 0
- **Tailings Moisture: DB → Excel → 0** (NEW)

---

## Configuration Reference

**Config File:** `config/app_config.yaml`

```yaml
environmental:
  evaporation_zone: "4A"  # Regional zone for weather data
  
database:
  path: "data/water_balance.db"
```

**Reload After Changes:**
```python
from config_manager import config
config.load_config()  # Reloads from disk
```

---

## Testing Summary

✅ All 6 CRUD test cases pass
- Insert/Replace with proper commits
- Read single month (returns float or None)
- Read all months (returns Dict)
- Validation (rejects >100%, <0%)
- Missing values (returns None for fallback)
- Edge cases (empty result, null handling)

---

## Documentation Files

| File | Purpose |
|------|---------|
| `TAILINGS_MOISTURE_IMPLEMENTATION.md` | Technical details, schema, code |
| `TAILINGS_MOISTURE_USER_GUIDE.md` | User instructions, FAQ, examples |
| `SESSION_COMPREHENSIVE_SUMMARY.md` | Full session overview, patterns |
| **← You are here** | Quick reference |

---

## Common Tasks

### Add Tailings Moisture for Month
```python
from database.db_manager import db

db.set_tailings_moisture_monthly(
    month=10,      # October
    year=2025,
    pct=22.0,      # 22%
    notes="End of month thickener test"
)
```

### Get Tailings Moisture for Month  
```python
value = db.get_tailings_moisture_monthly(10, 2025)
if value:
    print(f"October moisture: {value}%")
else:
    print("No entry found, using fallback 0%")
```

### Get All Months for Year
```python
all_months = db.get_tailings_moisture_all_months(2025)
for month, pct in sorted(all_months.items()):
    print(f"Month {month}: {pct}%")
```

---

## Troubleshooting

**Calculation shows 0% retention?**
- Check database has value for that month
- Settings → Load to verify save worked
- Check month/year match calculation date

**Can't save value?**
- Value must be 0-100%
- App must have write access to data/ folder
- Check error message in Settings

**Want to reset all values?**
```bash
# Delete database (will be recreated on next run)
rm data/water_balance.db

# Or drop table (keeps other data)
sqlite3 data/water_balance.db "DROP TABLE tailings_moisture_monthly;"
```

---

## Next Steps / Future Work

1. **Bulk Import** - Load values from CSV/Excel
2. **Templates** - Save/load month value templates
3. **Forecasting** - Auto-calculate based on equipment efficiency
4. **Reporting** - Export entered values with timestamp
5. **Audit Trail UI** - View who changed what when

---

## Links & References

- **User Guide:** docs/TAILINGS_MOISTURE_USER_GUIDE.md
- **Implementation:** docs/TAILINGS_MOISTURE_IMPLEMENTATION.md  
- **Full Summary:** docs/SESSION_COMPREHENSIVE_SUMMARY.md
- **Database Schema:** src/database/schema.py (lines 450-468)
- **DB Methods:** src/database/db_manager.py (lines 1467-1509)
- **Settings UI:** src/ui/settings.py (lines 707-845)
- **Calculator:** src/utils/water_balance_calculator.py (line ~480)

---

**Status:** ✅ Ready to use - Database, UI, and Calculator all integrated
