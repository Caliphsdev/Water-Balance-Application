# Automatic Storage Volume Update System

## Overview
The system now automatically tracks and updates storage facility volumes when you calculate and save water balances. This ensures volumes stay synchronized with your calculations.

## How It Works

### 1. **Volume Calculation Date Tracking**
- Each storage facility now has a `volume_calc_date` field
- This tracks which calculation date the current volumes correspond to
- Visible on the dashboard header: "DB Volumes: November 2025"

### 2. **Automatic Volume Updates**
When you save a calculation:
1. **New Date:** Updates all facility volumes to the new closing values
2. **Same Date:** Replaces old volumes with latest calculated values
3. **Logs:** Shows "✅ Updated 7 facility volumes for 2025-11-30"

### 3. **Duplicate Handling**
If you recalculate the same date:
- System asks: "Do you want to replace it with the new calculation?"
- **Yes:** Deletes old calculation, saves new one, updates volumes
- **No:** Keeps existing calculation, no changes made

## User Interface Changes

### Dashboard
- Header now shows: `Latest: December 2025 (Closing Volumes) | DB Volumes: November 2025`
- This tells you:
  - **Latest:** Current month you're viewing (Excel-calculated closing volumes)
  - **DB Volumes:** Which date the database volumes were last updated from

### Calculations Module
When saving a calculation, you'll see:
- **New calculation:** "✅ Saved to database (ID: 123) | Storage volumes updated to 2025-11-30"
- **Duplicate found:** Dialog asking if you want to replace
- **Replaced:** "✅ Replaced existing calculation (new ID: 124) | Storage volumes updated to 2025-11-30"

## Key Benefits

1. **Always Current:** Volumes automatically update when you save calculations
2. **Date Awareness:** Know exactly which calculation date your volumes represent
3. **Flexible:** Can recalculate and replace old data easily
4. **Auditable:** Every volume update is logged and tracked

## Technical Details

### Database Changes
- Added `volume_calc_date DATE` column to `storage_facilities` table
- Automatically migrated on first run (non-destructive)

### Code Changes
- `db_manager.py`: Added volume_calc_date to schema migration
- `water_balance_calculator.py`: Enhanced `persist_storage_volumes()` with date tracking
- `calculations.py`: Added duplicate replacement dialog
- `dashboard.py`: Shows volume calculation date in header

## Example Workflow

1. **Calculate October 2025 balance** → Click "Calculate Balance"
2. **Save to database** → Volumes update to October 2025 closing values
3. **Dashboard shows** → "DB Volumes: October 2025"
4. **Calculate November 2025** → Click "Calculate Balance"
5. **Save to database** → Volumes update to November 2025 closing values
6. **Dashboard shows** → "DB Volumes: November 2025"
7. **Recalculate November** → System asks to replace
8. **Confirm replace** → Latest November values stored

## Notes
- Volume updates only happen when you save calculations (not just calculate)
- Dashboard always shows live-calculated Excel volumes (recalculated on load)
- Database stores static snapshots from your last saved calculation
- Cache is automatically invalidated when volumes are updated
