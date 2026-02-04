# Analytics Page - Quick Test Guide

## 🎯 What to Test

Your Analytics & Trends page has been completely rebuilt. Here's what to verify:

---

## ✅ TEST 1: Collapse/Expand Sections

### Data Source File Section
1. **Initial State**: Should be **COLLAPSED** (arrow pointing right ►)
2. **Click the "DataSource File" button** (with folder icon)
   - Expected: Arrow changes to DOWN ▼, file path input + "Select File" button appear
3. **Click again to collapse**
   - Expected: Arrow back to RIGHT ►, file section hides

### Chart Options Section
1. **Initial State**: Should be **COLLAPSED** (arrow pointing right ►)
2. **Click the "Chart Options" button** (with chart icon)
   - Expected: Arrow changes to DOWN ▼, all dropdowns + Generate/Save buttons appear
3. **Click again to collapse**
   - Expected: Arrow back to RIGHT ►, chart options hide

**✅ PASS if**: Each section collapses/expands **smoothly** with **no lag**

---

## ✅ TEST 2: File Selection

1. **Expand Data Source File section** (click button)
2. **Click "Select File" button** (cyan colored)
   - Expected: File browser dialog opens
3. **Navigate to** `data/Water_Balance_TimeSeries_Template.xlsx`
4. **Click "Open"**
   - Expected: File path appears in the text field above button

**✅ PASS if**: Dialog opens, file path updates

---

## ✅ TEST 3: Chart Generation

1. **Expand Chart Options section** (click button)
2. **Choose from dropdowns** (optional):
   - Chart Type: Line Chart, Bar Chart, or Box Plot
   - Water Source: "Tonnes Milled"
   - Date Range: Select year/month ranges
3. **Click "Generate Chart" button** (green)
   - Expected: Chart renders in the gray area below
   - Placeholder text "Select Excel file..." disappears

**✅ PASS if**: Chart appears with demo data

---

## ✅ TEST 4: Page Layout

1. **Look at the page** - No scrollbars should appear
2. **All buttons visible**: 
   - ✅ Select File (cyan, Data Source section)
   - ✅ Generate Chart (green, Chart Options section)
   - ✅ Save Chart (blue, Chart Options section)
3. **Page fits within window** without needing to scroll

**✅ PASS if**: Everything fits on screen without scrolling

---

## ✅ TEST 5: Visual Polish

- Headers "DataSource File" and "Chart Options" are clear and clickable
- Icons load from resources (folder icon, chart icon)
- Buttons have proper colors:
  - Select File: Cyan rgb(8, 201, 255)
  - Generate Chart: Green rgb(51, 186, 28)
  - Save Chart: Blue rgb(42, 150, 232)
- Spacing between sections is consistent

**✅ PASS if**: Page looks clean and professional

---

## 🐛 Common Issues to Watch For

| Issue | Fix |
|-------|-----|
| Buttons don't respond to clicks | Restart app, try again |
| Charts not showing | Ensure file is selected first |
| Collapse not working | Check browser console for errors |
| Scrollbars appear on page | Window too small, resize larger |
| Icons missing (placeholders only) | Resources not compiled; run compile_ui.ps1 |

---

## 📝 If You Find Issues

If something doesn't work:
1. **Note the exact behavior** (what you clicked, what happened)
2. **Check window size** (should be at least 1196×800)
3. **Restart the app** (kill Python, run again)
4. **Check logs** (look in `logs/` folder for errors)
5. **Report to development** with steps to reproduce

---

## ✅ Success Criteria

**ALL of these must pass**:
- [ ] Data Source File section collapses/expands smoothly
- [ ] Chart Options section collapses/expands smoothly
- [ ] Select File button opens file dialog
- [ ] File path updates when file is selected
- [ ] Generate Chart button renders a chart
- [ ] Save Chart button is visible and clickable
- [ ] Page fits entire screen with no scrolling
- [ ] All buttons are visible and have correct colors
- [ ] Icons load properly (not placeholder text)
- [ ] No errors in console or logs

---

**Once all tests pass**, the Analytics page is ready for production! 🚀

Next: Replicate this pattern for remaining 6 pages.
