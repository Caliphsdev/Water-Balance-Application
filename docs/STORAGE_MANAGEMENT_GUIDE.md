# Storage Volume Management Guide

## Overview
Storage facility volumes are now centrally managed in the **Water_Balance_TimeSeries_Template.xlsx** file, making it much easier to update and track storage levels over time.

## 📊 How It Works

### Data Source Priority
The system now uses this priority for storage volumes:
1. **Excel Template** (PRIMARY) - Opening volumes from `Storage_Facilities` sheet
2. **Database** (FALLBACK) - Only used if Excel data is not available for the date

### Benefits of Excel-Based Management
✅ **Centralized** - All time-series data in one place  
✅ **Easy to Update** - Simple spreadsheet editing  
✅ **Version Control** - Track changes over time  
✅ **Bulk Import** - Add multiple months at once  
✅ **Audit Trail** - Clear history of storage levels  

## 📝 How to Manage Storage Volumes

### Location
```
templates/Water_Balance_TimeSeries_Template.xlsx
Sheet: Storage_Facilities
```

### Data Structure

**SIMPLIFIED! You only need to enter Inflow and Outflow - everything else is AUTO-CALCULATED!**

| Column | Required? | Description | Example |
|--------|-----------|-------------|---------|
| Date | ✅ Required | Month start date | 2025-05-01 |
| Facility_Code | ✅ Required | Facility code from database | MDCD5-6 |
| Opening_Volume_m3 | 🔄 Auto | AUTO: Previous month's closing | (leave blank) |
| Closing_Volume_m3 | 🔄 Auto | AUTO: Opening + Inflow - Outflow | (leave blank) |
| Level_Percent | 🔄 Auto | AUTO: Opening / Capacity | (leave blank) |
| Inflow_m3 | ✅ Required | Total inflows for month | 5500 |
| Outflow_m3 | ✅ Required | Total outflows for month | 4000 |

**Auto-Calculation Logic:**
```
Opening Volume = Previous month's Closing Volume (chains across months)
Closing Volume = Opening + Inflow - Outflow (mass balance)
Level Percent  = Opening / Facility Capacity (utilization)
```

**You can also override auto-calculation by entering explicit values when needed!**

### Your Storage Facilities
| Code | Name | Capacity (m³) |
|------|------|---------------|
| MDCD5-6 | Merensky Decline Clean Dams 5-6 | 40,000 |
| MDSWD3-4 | Merensky Decline Storm Water Dams 3-4 | 35,000 |
| NDCD1-4 | North Decline Clean Dams 1-4 | 92,184 |
| NDSWD1-2 | North Decline Storm Water Dams 1-2 | 50,000 |
| **TOTAL** | | **217,184** |

## 🔄 Monthly Update Process - SIMPLIFIED!

### Step 1: Add New Month Data (Simplified - Only Inflows/Outflows!)

Open the Excel template and add a row for each facility with ONLY Date, Facility_Code, Inflow, and Outflow:

```excel
Date         Facility_Code  Opening_Volume_m3  Closing_Volume_m3  Level_Percent  Inflow_m3  Outflow_m3
2025-06-01   MDCD5-6        (blank/auto)       (blank/auto)       (blank/auto)   6000       4500
2025-06-01   MDSWD3-4       (blank/auto)       (blank/auto)       (blank/auto)   5000       3500
2025-06-01   NDCD1-4        (blank/auto)       (blank/auto)       (blank/auto)   11000      9500
2025-06-01   NDSWD1-2       (blank/auto)       (blank/auto)       (blank/auto)   8000       6500
```

**That's it! The system will automatically calculate:**
- Opening = Previous month's closing
- Closing = Opening + Inflow - Outflow  
- Level% = Opening / Capacity

### Step 2: Save and Test
1. Save the Excel file
2. Open the Water Balance Application
3. Go to **Calculations** dashboard
4. Select the new month date
5. Verify storage metrics display correctly

## 📈 Calculating Storage Values

### Opening Volume
- Use previous month's closing volume
- Or use actual measured volume from site

### Closing Volume
Use one of these methods:

**Method 1: Measured**
```
Closing_Volume = Actual measured volume at month end
```

**Method 2: Calculated**
```
Closing_Volume = Opening_Volume + Total_Inflows - Total_Outflows
```

### Inflows and Outflows
Get from:
- Site measurements
- SCADA systems
- Flow meters
- Water balance calculations

## 🎯 Best Practices

### 1. Monthly Updates
- Update storage volumes at the start of each month
- Use actual measurements when available
- Reconcile with water balance calculations

### 2. Data Validation
```
✓ Opening volume ≤ Total capacity
✓ Closing volume ≤ Total capacity
✓ Level_Percent between 0 and 1
✓ Inflows and outflows are positive
✓ Balance equation holds (within tolerance)
```

### 3. Backup Strategy
- Keep backups of Excel template before major changes
- Version control: `Water_Balance_TimeSeries_Template_YYYY-MM.xlsx`
- Document any adjustments or corrections

### 4. Consistency
- Use same date format: YYYY-MM-DD
- Use month start dates (e.g., 2025-05-01)
- Facility codes must match database exactly

## 🔍 Dashboard Metrics Explained

### Storage Current Volume
- Sum of all facility opening volumes for selected date
- Source: Excel `Opening_Volume_m3` column
- Fallback: Database `current_volume` if Excel data missing

### Storage Utilization %
```
Utilization = (Current_Volume ÷ Total_Capacity) × 100
```

Example with May 2025 data:
```
(150,500 ÷ 217,184) × 100 = 69.30%
```

### Days of Operation Cover
```
Days_Cover = Current_Storage ÷ Daily_Consumption
Daily_Consumption = Monthly_Outflows ÷ 30
```

Example:
```
Daily_Consumption = 227,353 ÷ 30 = 7,578 m³/day
Days_Cover = 150,500 ÷ 7,578 = 19.9 days
```

### Security Status
| Days Cover | Status | Color | Action |
|------------|--------|-------|--------|
| ≥ 30 days | Excellent | Green | Normal operations |
| 14-29 days | Good | Blue | Monitor trends |
| 7-13 days | Adequate | Cyan | Watch closely |
| 3-6 days | Low | Yellow | Plan contingencies |
| < 3 days | Critical | Red | Immediate action |

## 🛠️ Troubleshooting

### Issue: Dashboard shows 0% utilization
**Cause**: No Excel data for selected date  
**Solution**: Add storage data for that month in Excel template

### Issue: Values don't update after editing Excel
**Cause**: Python cache  
**Solution**: 
```bash
cd /home/caliphs/Projects/water_balance_app
rm -rf src/**/__pycache__
python src/main.py
```

### Issue: Different facilities show different dates
**Cause**: Missing data for some facilities  
**Solution**: Ensure all facilities have data for each month

### Issue: Opening volume doesn't match previous closing
**Cause**: Data entry error or actual discrepancy  
**Solution**: 
- Investigate water losses/gains
- Check for unrecorded transfers
- Verify measurement accuracy
- Document adjustment reason

## 📊 Example: Complete Month Entry

### NEW SIMPLIFIED APPROACH (Recommended)

**You only need to enter Date, Facility, Inflow, and Outflow!**

```excel
# June 2025 - SIMPLIFIED Entry (Only inflows/outflows required!)
Date         Facility_Code  Opening  Closing  Level%  Inflow  Outflow
2025-06-01   MDCD5-6        -        -        -       6000    4500
2025-06-01   MDSWD3-4       -        -        -       5000    3500
2025-06-01   NDCD1-4        -        -        -       11000   9500
2025-06-01   NDSWD1-2       -        -        -       8000    6500

# System AUTO-CALCULATES from May data:
MDCD5-6:  Opening=29,500 (May close) → +6,000-4,500 → Closing=31,000 → Level=73.8%
MDSWD3-4: Opening=22,500 (May close) → +5,000-3,500 → Closing=24,000 → Level=64.3%
NDCD1-4:  Opening=71,500 (May close) → +11,000-9,500 → Closing=73,000 → Level=77.6%
NDSWD1-2: Opening=34,000 (May close) → +8,000-6,500 → Closing=35,500 → Level=68.0%

Total: 157,500 m³ → 163,500 m³ (75.3% utilization)
```

### TRADITIONAL APPROACH (Optional - for manual verification)

**If you prefer explicit control, you can still enter all values:**

```excel
# May 2025 Complete Entry - Traditional Format
Date         Facility_Code  Opening  Closing  Level%  Inflow  Outflow
2025-05-01   MDCD5-6        28000    29500    0.74    5500    4000
2025-05-01   MDSWD3-4       21000    22500    0.64    4500    3000
2025-05-01   NDCD1-4        69000    71500    0.78    10500   8000
2025-05-01   NDSWD1-2       32500    34000    0.68    7500    6000

# Totals for verification:
Opening Total:  150,500 m³ (69.30% utilization)
Closing Total:  157,500 m³ (72.52% utilization)
Net Change:     +7,000 m³
Total Inflows:  27,500 m³
Total Outflows: 20,500 m³
Balance Check:  150,500 + 27,500 - 20,500 = 157,500 ✓
```

**Mix and Match:** You can use auto-calculation for some months and explicit values for others!

## 🎓 Training Checklist

For users managing storage data:

- [ ] Understand facility codes and capacities
- [ ] Know how to calculate Level_Percent
- [ ] Can verify water balance equation
- [ ] Know where to find source measurements
- [ ] Understand security status thresholds
- [ ] Can interpret dashboard metrics
- [ ] Know troubleshooting steps
- [ ] Understand backup procedures

## 📞 Support

For issues or questions about storage management:
1. Check this guide first
2. Verify Excel template format
3. Review application logs: `logs/water_balance.log`
4. Contact system administrator

---

**Last Updated**: November 26, 2025  
**Version**: 1.0  
**Maintained By**: Water Balance Application Team
