# Excel Integration Strategy - 1-Page Summary

**Goal:** Consolidate Excel code, auto-create columns, embed Excel preview, improve user experience

---

## Current Problems

| Problem | Impact | Location |
|---------|--------|----------|
| **Code Duplication** | Same sheet/column logic in 2+ dialogs | ExcelSetupDialog, EditFlowDialog |
| **Manual Column Creation** | Users must edit Excel outside app | Users go to Excel, add header, add rows, return |
| **No Excel Preview** | Can't see data in app | Must open Excel separately |
| **No Auto-Creation** | New flowlines need manual setup | Time-consuming, error-prone |

---

## Proposed Solution: 3-Layer Architecture

### Layer 1: **ExcelManager Service** (Backend)
```
Purpose: Single source of truth for all Excel operations
Location: src/services/excel_manager.py
Methods:
  - get_sheets() → List of sheet names
  - get_columns(sheet) → Column list for sheet
  - create_column(sheet, name) → Add new column to Excel
  - auto_map_flow(from_id, to_id) → Find or create column
  - get_volume(sheet, col, year, month) → Load flow data
  - validate_excel() → Check file integrity

Benefit: No duplication, centralized, easy to extend
```

### Layer 2: **Dialogs (UI Controllers)**
```
ExcelSetupDialog (Enhanced)
  ├─ Uses ExcelManager (not duplicated code)
  ├─ Shows Excel preview widget
  ├─ Shows column mapping table
  └─ "Auto-Map All Flows" button

EditFlowDialog (Enhanced)
  ├─ Uses ExcelManager for sheet/column lists
  ├─ Shows "Auto-Create Column" button
  ├─ Shows mini Excel preview
  └─ Auto-suggests column name: BH_to_Sump
```

### Layer 3: **Excel Preview Widget** (New)
```
ExcelPreviewWidget (QTableWidget-based)
  ├─ Display Excel data as editable table
  ├─ Double-click cells to edit values
  ├─ "Add Row" button for new months
  ├─ "Save" button to write back to Excel
  └─ Column highlighting for mapped flows

Use: Embedded in dialogs, shows real-time data
```

---

## User Experience: Before → After

### Current Workflow (10 steps, 2 app switches)

```
1. Create flowline in drawing mode
2. Open "Edit Flow" dialog
3. Manually select Excel sheet
4. Manually select Excel column (if exists)
5. ❌ Column doesn't exist → CLOSE APP
6. ❌ Open Excel → Add column header → Add empty rows → Save
7. ❌ Return to app → Reload
8. Verify mapping → Try again
9. Click OK in dialog
10. Flowline created (finally!)
```

**Pain:** Leaves app, manual data entry, tedious

### Proposed Workflow (6 steps, stays in app)

```
1. Create flowline in drawing mode
2. Open "Edit Flow" dialog
3. ✅ Sheets & columns auto-loaded
4. ✅ Auto-suggestion: "BH_to_Sump" column
5. ✅ Click "Auto-Create Column" → (1-2 seconds, done!)
6. Click OK → Flowline created with Excel mapping ready
```

**Win:** Never leaves app, automatic, instant feedback

---

## Implementation Roadmap (4 Sprints)

### Sprint 1: **Foundation** (4-6 hours)
- Create ExcelManager service
- Consolidate duplicate code from dialogs
- Add unit tests

**Result:** Clean architecture, no duplication

---

### Sprint 2: **Auto-Column Creation** (6-8 hours)
- Implement `create_column()` in ExcelManager
- Add "Auto-Create Column" button to EditFlowDialog
- Auto-name columns: `BH123_to_Sump`
- Validate before creation

**Result:** Users create new flowlines without touching Excel

---

### Sprint 3: **Excel Preview Widget** (6-8 hours)
- Build ExcelPreviewWidget (QTableWidget)
- Add cell editing (double-click)
- Add "Add Row" button
- Integrate into ExcelSetupDialog (right pane)
- Add mini-preview to EditFlowDialog

**Result:** Users can see/edit Excel data in-app without external Excel

---

### Sprint 4: **Polish** (3-4 hours)
- Thread long Excel operations (no UI freeze)
- Progress dialogs during operations
- Handle file lock errors gracefully
- Cache sheet/column lists (performance)
- Full integration testing

**Result:** Production-ready, smooth experience

---

## Technology Decisions

### QTableWidget vs QAxWidget

| Aspect | QTableWidget | QAxWidget |
|--------|--------------|-----------|
| **Platform** | Cross-platform | Windows-only |
| **Overhead** | Lightweight | Heavy (embeds Excel) |
| **Editing** | Spreadsheet-like | True Excel UI |
| **Deployment** | Simple | Complex (COM/UNO) |
| **Recommendation** | ✅ **USE NOW** | ❌ Defer to v2 |

**Decision:** Start with QTableWidget, upgrade to QAxWidget later if needed.

---

## Code Duplication Eliminated

### Before (Duplicated)

```
EditFlowDialog._populate_excel_options()
  → Read sheets from Excel (DUPLICATE CODE)
  → Read columns from Excel (DUPLICATE CODE)

ExcelSetupDialog._on_browse_excel()
  → Read sheets from Excel (DUPLICATE CODE)
  → Read columns from Excel (DUPLICATE CODE)

ExcelSetupDialog._on_auto_map_all()
  → Auto-match flow name to column (DUPLICATE LOGIC)
```

### After (Centralized)

```
ExcelManager.get_sheets()
  → Called by: EditFlowDialog, ExcelSetupDialog, FlowDiagramPage
  → ONE implementation

ExcelManager.get_columns_for_sheet(sheet)
  → Called by: EditFlowDialog, ExcelSetupDialog, ExcelPreviewWidget
  → ONE implementation

ExcelManager.auto_map_flow(from_id, to_id)
  → Called by: EditFlowDialog, ExcelSetupDialog, FlowDiagramPage
  → ONE implementation (all dialogs use same matching logic)
```

**Result:** ~50% less code, easier to maintain, consistent behavior

---

## File Structure (New/Modified)

```
src/services/
  ├── excel_manager.py         ← NEW (200 lines) - Central hub
  └── __init__.py

src/ui/components/
  ├── excel_preview_widget.py  ← NEW (150 lines) - Preview table
  └── __init__.py

src/ui/dialogs/
  ├── excel_setup_dialog.py    ← REFACTOR (100→70 lines) - Uses manager
  ├── edit_flow_dialog.py      ← REFACTOR (50 lines) - Uses manager
  └── generated_ui_*.py        ← Auto-generated (no change)
```

---

## Key Benefits

✅ **No Code Duplication** - Single ExcelManager source of truth  
✅ **Better UX** - Auto-create columns, stay in app  
✅ **Real-Time Preview** - See Excel data without external app  
✅ **Maintainable** - Centralized error handling, logging, caching  
✅ **Testable** - ExcelManager is independent unit-testable service  
✅ **Scalable** - Easy to add features (validation, auto-mapping, etc.)  
✅ **Cross-Platform** - Works on Windows/Mac/Linux (QTableWidget approach)  

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| File locks (Excel open in user's editor) | Warn user, check permissions, catch PermissionError |
| Incorrect column naming | Let user customize, validate uniqueness before creation |
| Performance (large Excel files) | Cache sheet/column lists, check file mtime, thread operations |
| Data loss | Validate structure before modify, explicit save buttons, no auto-save |
| Windows-only QAxWidget later | Start with QTableWidget (cross-platform), upgrade path exists |

---

## Effort Estimate

- **Total:** 19-26 hours (2-3 weeks part-time)
- **Sprint 1 (Foundation):** 4-6 hours
- **Sprint 2 (Auto-Column):** 6-8 hours ← **Biggest UX win**
- **Sprint 3 (Preview):** 6-8 hours
- **Sprint 4 (Polish):** 3-4 hours

---

## Next Steps

1. ✅ **Review Architecture** (this doc)
2. ⬜ **Approve Approach** - Confirm QTableWidget vs QAxWidget
3. ⬜ **Start Sprint 1** - Build ExcelManager
4. ⬜ **Refactor Dialogs** - Remove duplicate code
5. ⬜ **Sprint 2** - Auto-column creation (big UX win)
6. ⬜ **Sprint 3** - Preview widget
7. ⬜ **User Testing** - Gather feedback

---

**Questions?** See EXCEL_INTEGRATION_ARCHITECTURE.md for detailed implementation guide.

