# How to Use: Monthly Tailings Moisture Input

## Quick Start (30 seconds)

1. **Open Settings**: Click "⚙️ Settings" button in main window
2. **Go to Tab**: Click "  ⚗️ Tailings & Process  " tab
3. **Enter Value**: 
   - Select month (e.g., October)
   - Select year (e.g., 2025)
   - Enter moisture % (e.g., 22.0)
4. **Save**: Click "💾 Save" button → Confirmation appears
5. **Done**: System Balance will use this value next calculation

## What is Tailings Moisture?

Water physically locked in settled tailings solids that doesn't return from the TSF. This is a **permanent water loss** from the system.

**Example:**
- Ore processed: 306,115 tonnes/month
- Concentrate produced: 12,000 tonnes/month
- Tailings dry mass: 294,115 tonnes/month
- **If moisture = 20%:**
  - Water retained: 294,115 × 0.20 = **58,823 m³**
  - This water doesn't return to the plant

## Typical Values

- **15-20%**: Efficient thickening, good drainage
- **20-25%**: Standard operation
- **25%+**: Underperforming thickener (more water retained)

Use your facility's historical performance or thickener efficiency data.

## Steps to Set Monthly Values

### For Single Month:
1. Open Settings → ⚗️ Tailings & Process
2. Select month and year
3. Enter percentage (0-100)
4. Click **Load** to check if value exists first (optional)
5. Click **Save**
6. See confirmation: "Saved: October = 22.0%"

### For All 12 Months (Batch Entry):
1. Open Settings → ⚗️ Tailings & Process
2. **January:**
   - Select "01 - Jan"
   - Enter value (e.g., 18.5)
   - Click Save
3. **February:**
   - Select "02 - Feb"
   - Enter value (e.g., 19.0)
   - Click Save
4. Continue for remaining months...

**Tip:** Keep a spreadsheet of typical values by month for faster entry.

## What Happens with Your Input

**When you Save:**
- Value stored in database (C:\PROJECTS\Water-Balance-Application\data\water_balance.db)
- Timestamp recorded automatically
- Survives app restarts

**During Calculation:**
- System Balance uses database value
- If no value found: uses 0% (conservative fallback)
- Tailings Retention = (Ore - Concentrate) × Moisture_%

**Example: October 2025**
```
Database has: 22.0%
System Balance calculation:
  Tailings dry mass: 294,115 tonnes
  Moisture: 22.0%
  Retention: 294,115 × 0.22 = 64,665 m³
  Report shows: "Tailings Retention 64,665 m³"
```

## Load Previous Value

If you're updating an existing month:
1. Open Settings → ⚗️ Tailings & Process
2. Select month and year
3. Click **Load** 
4. Previous value appears in input field
5. Edit and Save with new value

## Clear Input

Click **Clear** to empty the input field without saving. Does **NOT** delete the database value.

## Validation Rules

✅ **Must be between 0-100%**
❌ Will reject: 150%, -5%, blank entry (shows error message)

## If Something Goes Wrong

**"No Data" message when loading:**
- Month has no entry yet
- Enter value and Save

**"Failed to save" error:**
- Check moisture % is 0-100
- Check app has write permission to data folder
- Try again or contact support

**Value shows 0% after calculation:**
- No entry found for that month
- Check that you Saved (see confirmation message)
- Use Load to verify it was saved

## System Integration

Tailings moisture feeds into:
- **System Balance** sheet: Shows "Tailings Retention" water loss
- **Area Breakdown**: Per-area tailings retention calculations
- **Water Budget**: Overall system water accounting

## Database Storage

Values stored in: `tailings_moisture_monthly` table
Columns: month (1-12), year, tailings_moisture_pct (0-100), notes, updated_at

**Can I edit directly in database?**
- Yes, if you know SQL and SQLite
- Recommended: Use app UI (safer, validated)

## FAQ

**Q: Can I set a default for all months?**
A: Not yet - enter individually. Consider creating a template spreadsheet.

**Q: What if I don't know the moisture percentage?**
A: Use industry standard 20% or check thickener specifications. You can update later.

**Q: How does fallback work?**
A: If no value entered for a month, system assumes 0% moisture (no water retained). This is conservative.

**Q: Can I use different values per year?**
A: Yes! Year selector lets you set 2024, 2025, 2026 separately.

**Q: Is this value used in other calculations?**
A: Only in Tailings Retention (System Balance). Not used for ore moisture or concentrate moisture.

---

**For Technical Details:** See [TAILINGS_MOISTURE_IMPLEMENTATION.md](TAILINGS_MOISTURE_IMPLEMENTATION.md)
