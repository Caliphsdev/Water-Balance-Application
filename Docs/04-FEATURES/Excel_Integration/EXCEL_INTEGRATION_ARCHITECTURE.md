# Excel Integration Architecture & Strategy

**Date:** February 1, 2026  
**Status:** Planning Phase  
**Objective:** Consolidate repeating Excel functionality, auto-create columns, embed Excel preview in app

---

## 🎯 Current State Analysis

### Problem: Code Duplication & Manual Workflow

**Repeating Functionality Identified:**

| Component | Location | Purpose | Issue |
|-----------|----------|---------|-------|
| Sheet/Column Listing | `ExcelSetupDialog` | Populate dropdowns with available Excel columns | Duplicated logic |
| Sheet/Column Listing | `EditFlowDialog` | Same dropdown population in edge edit dialog | Duplicated logic |
| Auto-Mapping Logic | `ExcelSetupDialog._on_auto_map_all()` | Intelligent column matching by name | Needs centralization |
| Auto-Mapping Logic | `EditFlowDialog` (TODO) | Same matching needed per-edge | Duplicated implementation |
| Mapping Persistence | `ExcelSetupDialog` | Save/load excel_flow_links.json | Works, but dialogs manage it separately |
| Flow Volume Loading | `FlowVolumeLoader` (legacy from Tkinter) | Read from Excel | Works but read-only |
| Column Creation | **MISSING** | Create new columns in Excel for new flows | User must go to Excel manually |

**User Workflow (Current - Manual):**
1. User creates a flowline in drawing mode
2. Opens Edit Flow Line dialog
3. Manually selects Excel sheet and column
4. If column doesn't exist → User must manually open Excel, add column, save
5. Return to app and reload
6. Repeat for each new flowline

**User Workflow (Desired - Automated):**
1. User creates a flowline in drawing mode
2. Dialog auto-suggests or creates Excel column
3. Mapping saved automatically
4. Data loads on refresh without manual Excel editing

---

## 🏗️ Proposed Architecture

### 1. **Excel Manager Service** (Centralized Backend)

**File:** `src/services/excel_manager.py`

**Purpose:** Single source of truth for all Excel operations

```python
class ExcelManager:
    """
    Excel Operations Manager (CENTRALIZED HUB).
    
    Consolidates all Excel-related operations:
    - Read sheet/column information
    - Load flow volumes for specific month/area
    - Create new columns programmatically
    - Map flows to Excel columns
    - Validate Excel structure
    """
    
    # Core Methods:
    - get_sheets() -> List[str]
    - get_columns_for_sheet(sheet: str) -> List[str]
    - get_volume(sheet: str, column: str, year: int, month: int) -> float
    - create_column(sheet: str, column_name: str) -> bool
    - auto_map_flow(from_id: str, to_id: str) -> Optional[Tuple[sheet, column]]
    - validate_excel() -> Tuple[bool, List[errors]]
    - get_excel_path() -> Path
    - set_excel_path(path: Path) -> bool
```

**Why:**
- Single point for all Excel I/O (no duplication)
- Dialogs/pages call manager, not each other
- Easy to add features (auto-column creation, validation)
- Can add error handling, logging, caching at one place
- Testable independently from UI

### 2. **Excel Column Auto-Creation** (New Feature)

**In ExcelManager:**

```python
def create_column(self, sheet: str, column_name: str) -> bool:
    """
    Create new column in Excel for a new flowline.
    
    Process:
    1. Open Excel file (via openpyxl)
    2. Find sheet
    3. Find next empty column (after data columns)
    4. Write column header: column_name
    5. Add empty data rows matching existing structure (Year/Month/dates)
    6. Save Excel file
    7. Invalidate cache
    
    Called when:
    - New flowline created without existing Excel mapping
    - User clicks "Auto-Create Column" in Edit Flow dialog
    """
```

**Column Naming Convention:**

```
For flowline: BoreHole_123 → Sump
Column Name: BH123_to_Sump  (auto-generated, user can customize)
```

**Excel Row Structure (Auto-Populated):**
```
Row 1: Column Headers (e.g., "BH123_to_Sump")
Row 2+: Empty cells for user to fill with flow data

The manager creates empty structure; user fills volume data at their pace
```

### 3. **Embedded Excel Preview** (PySide6 QAxWidget)

**⚠️ Important Decision: QAxWidget vs Alternatives**

#### Option A: QAxWidget (Windows-Only, Direct Excel Integration)
```python
from PySide6.QtAxContainer import QAxWidget

class ExcelViewerWidget(QWidget):
    def __init__(self):
        self.excel_widget = QAxWidget("Excel.Sheet")
        # Directly embeds Excel in app
        # User can edit cells directly in app
        # Real-time Excel updates without external app
        # Pro: Native Excel editing, real-time updates
        # Con: Windows-only, requires Excel/LibreOffice COM, heavy
```

**Requirements:**
- Windows only (Excel via COM or LibreOffice UNO)
- Heavyweight (embeds entire Excel engine)
- Complex to build for deployment
- Best if user edits flow data frequently

#### Option B: Lightweight HTML Grid (Recommended for Now)

```python
class ExcelPreviewWidget(QWidget):
    def __init__(self):
        # Use QTableWidget to display/edit Excel data
        # Load via pandas, display in table
        # User double-clicks to edit cells
        # Save back to Excel via openpyxl
        # Pro: Cross-platform, lightweight, responsive
        # Con: Not "real" Excel (but looks like it)
```

**This allows:**
- Preview Excel data in app
- Edit cells without leaving app
- Add new rows (months)
- Create new columns
- See changes immediately
- Save back to Excel

#### Option C: Read-Only HTML Export

```python
# Just display Excel as read-only HTML table
# No editing capability
# User still goes to Excel for edits
# Pro: Simplest, safest
# Con: Still requires external Excel
```

---

## 📋 Implementation Plan

### Phase 1: Centralize Excel Operations (Foundation)

**Priority: HIGH - Unblock other work**

**Tasks:**

1. **Create ExcelManager Service** (~200 lines)
   - Consolidate logic from `FlowVolumeLoader` + dialogs
   - Methods: get_sheets(), get_columns(), get_volume(), validate()
   - Singleton pattern: `get_excel_manager()`
   - File: `src/services/excel_manager.py`

2. **Refactor ExcelSetupDialog**
   - Remove duplicate Excel reading code
   - Use ExcelManager instead
   - Result: 100 lines → 50 lines

3. **Refactor EditFlowDialog**
   - Use ExcelManager for sheet/column lists
   - Implement auto-mapping via ExcelManager
   - Result: Cleaner, less duplicated code

4. **Update FlowDiagramPage**
   - `_on_load_excel_clicked()` → Use ExcelManager to load volumes
   - `_on_excel_setup_clicked()` → Already uses ExcelSetupDialog

**Deliverable:** Clean architecture, no duplication, tests pass

---

### Phase 2: Auto-Column Creation (User Experience)

**Priority: HIGH - Major UX improvement**

**Tasks:**

1. **Implement ExcelManager.create_column()**
   - Use openpyxl to append column
   - Auto-generate column name: `{from_id}_to_{to_id}`
   - Populate header row
   - Create empty data rows (Year/Month structure)
   - File operations via direct Excel API (not UI)

2. **Add "Auto-Create Column" Button to EditFlowDialog**
   - When user creates new flowline
   - Button triggers: `manager.create_column(suggested_name)`
   - Show spinner: "Creating column..."
   - On success: Auto-populate mapping, dismiss dialog
   - On error: Show error message with recovery options

3. **Update FlowDiagramPage.new_edge_dialog()**
   - Pass context: `from_id`, `to_id`, `area_code`
   - Dialog can auto-generate column name
   - Option: "Create Column Automatically"

4. **Validation:**
   - Column doesn't already exist
   - Excel file is writable (check permissions)
   - Excel file structure is valid (has Year/Month)
   - Suggested name is unique

**Deliverable:** Users can create new flowlines without touching Excel

---

### Phase 3: Embedded Excel Preview (UI Enhancement)

**Priority: MEDIUM - Polish & UX**

**Recommendation: Start with Option B (QTableWidget)**

**Rationale:**
- No COM dependencies (Windows-only)
- Cross-platform (Windows/Mac/Linux)
- Lightweight, responsive
- Can expand to QAxWidget later if needed
- Users don't expect "real" Excel editing in embedded widget

**Tasks:**

1. **Create ExcelPreviewWidget** (~150 lines)
   - File: `src/ui/components/excel_preview_widget.py`
   - Inherits: `QWidget`
   - Contains: `QTableWidget` + buttons
   - Methods:
     - `load_sheet(sheet_name: str)` → Load via pandas
     - `show_sheet(sheet_name: str)` → Display in table
     - `get_cell(row, col)` → Read value
     - `set_cell(row, col, value)` → Edit cell
     - `save_to_excel()` → Write back via openpyxl
   - Features:
     - Double-click cells to edit
     - Add row button (for new months)
     - Save button (explicit)
     - Read-only mode option
     - Column highlighting (mapped flows)

2. **Add Excel Preview to ExcelSetupDialog**
   - Right pane: Excel preview widget
   - Shows sheet content as table
   - User can see which columns they're mapping
   - Real-time feedback during configuration
   - Edit columns directly in dialog

3. **Add Mini Excel Preview to EditFlowDialog**
   - Small preview showing current column data
   - Shows last 3 months of data for context
   - Helps user verify mapping is correct

**Deliverable:** Users can preview/edit Excel data in-app without external Excel

---

### Phase 4: QAxWidget (Optional, Phase 5+)

**When to use:**
- Users need to edit Excel data frequently
- Want "native" Excel experience
- Windows-only deployment is acceptable
- Team is comfortable with COM/UNO

**Implementation:**
- Use `PySide6.QtAxContainer.QAxWidget`
- Embed Excel ActiveX object directly in dialog
- Load Excel file → edit → save automatically

**Trade-offs:**
- **Pro:** Native Excel UI, powerful
- **Con:** Windows-only, requires Excel install, heavy, complex deployment, licensing issues

**Recommendation:** Defer to Phase 5+, gather user feedback first

---

## 🔄 Data Flow Architecture

### Current Flow (Repeating Code)

```
EditFlowDialog
  ├─ _populate_excel_options()
  │   ├─ Get sheets (duplicated code)
  │   └─ Get columns (duplicated code)
  │
FlowVolumeLoader  (Read-only)
  ├─ _load_sheet()
  └─ get_flow_volume()

ExcelSetupDialog
  ├─ _on_browse_excel()
  │   └─ Open file dialog + validate
  ├─ _on_auto_map_all()
  │   ├─ Get sheets (duplicated code)
  │   ├─ Get columns (duplicated code)
  │   └─ Match flows to columns
  └─ _on_clear_mapping()
```

### Proposed Flow (Centralized)

```
ExcelManager (Singleton Service)
  ├─ get_sheets() → List[str]
  ├─ get_columns_for_sheet(sheet) → List[str]
  ├─ get_volume(sheet, col, year, month) → float
  ├─ create_column(sheet, col_name) → bool
  ├─ auto_map_flow(from_id, to_id) → (sheet, col)
  ├─ validate_excel() → (bool, errors)
  └─ Cache strategy: (sheet_name) → columns

EditFlowDialog
  ├─ Setup: manager.get_sheets()
  ├─ On sheet change: manager.get_columns_for_sheet(sheet)
  ├─ On auto-map: manager.auto_map_flow(from_id, to_id)
  └─ On create column: manager.create_column(sheet, suggested_name)

ExcelSetupDialog
  ├─ Setup: manager.get_sheets()
  ├─ On sheet select: manager.get_columns_for_sheet(sheet)
  ├─ On auto-map: manager.auto_map_flow(flow_key, ...)
  └─ Preview widget: manager.get_columns_for_sheet()

FlowDiagramPage
  ├─ _on_load_excel_clicked():
  │   └─ manager.update_edge_volumes(year, month)
  └─ _on_excel_setup_clicked():
      └─ ExcelSetupDialog (uses manager)
```

---

## 📊 Best Practices for PySide6 + Excel

### 1. **Avoid File Locks**

**Problem:** If Excel file is open in user's Excel, app can't modify it

**Solution:**
```python
# Use context managers to auto-close files
with pd.ExcelFile(path) as xls:
    sheets = xls.sheet_names  # Read-only, won't lock

# Use openpyxl data_only=True to avoid formulas
wb = load_workbook(path, data_only=True)
# Do operations
wb.close()  # Explicit close
```

### 2. **Warn User Before Excel Modifications**

```python
# Before creating column:
QMessageBox.question(
    self, 
    "Create Column",
    f"Create column '{column_name}' in '{sheet}'?\n\n"
    "This will modify the Excel file. You may need to reload the file "
    "if it's currently open in Excel."
)
```

### 3. **Thread Excel Operations**

```python
# Long Excel operations should run in background thread
worker_thread = QThread()
loader = ExcelLoadWorker(sheet, year, month)
loader.moveToThread(worker_thread)
loader.finished.connect(self._on_excel_loaded)
worker_thread.start()
```

### 4. **Graceful Error Handling**

```python
# User-friendly error messages
try:
    manager.create_column(sheet, col_name)
except PermissionError:
    QMessageBox.warning(self, "Error", 
        "Cannot modify Excel file.\n"
        "Make sure the file is not open in Excel.")
except ValueError as e:
    QMessageBox.warning(self, "Error", str(e))
```

### 5. **Cache Excel Metadata**

```python
# Cache sheet/column lists (expires on file modification time check)
class ExcelManager:
    def __init__(self):
        self._sheets_cache = None
        self._columns_cache = {}  # {sheet_name: [columns]}
        self._last_mtime = None
    
    def _check_cache_valid(self) -> bool:
        if not self.excel_path.exists():
            return False
        current_mtime = self.excel_path.stat().st_mtime
        if self._last_mtime != current_mtime:
            self._invalidate_cache()
            self._last_mtime = current_mtime
        return True
```

### 6. **Visual Feedback During Operations**

```python
# Use QProgressDialog or spinner
dialog = QProgressDialog("Creating column...", None, 0, 0, self)
dialog.setWindowModality(Qt.WindowModal)
dialog.show()
QApplication.processEvents()  # Refresh UI

try:
    manager.create_column(sheet, col_name)
finally:
    dialog.close()
```

---

## 🎯 User Experience Improvements

### Before (Current)

1. Create flowline
2. Open Edit dialog
3. Manually select sheet/column (if it exists)
4. If not exists → Close app
5. Open Excel manually
6. Add column header
7. Add empty data rows
8. Save Excel
9. Return to app
10. Reload flowline → Verify mapping

**Friction:** 10 steps, leaves app twice, manual data entry

### After (Proposed)

1. Create flowline
2. Open Edit dialog
3. Auto-suggestions for sheet/column appear
4. Click "Auto-Create Column" if needed (1-2 seconds)
5. Column created, mapped, saved automatically
6. Click OK to save flowline

**Friction:** 6 steps, never leaves app, automatic

---

## 🛠️ Implementation Checklist

### Sprint 1: Core Infrastructure
- [ ] Create `ExcelManager` service class (~200 lines)
- [ ] Add singleton getter: `get_excel_manager()`
- [ ] Implement: `get_sheets()`, `get_columns()`, `get_volume()`
- [ ] Add unit tests for manager methods
- [ ] Refactor `ExcelSetupDialog` to use manager
- [ ] Refactor `EditFlowDialog` to use manager
- [ ] Verify no code duplication

### Sprint 2: Auto-Column Creation
- [ ] Implement `ExcelManager.create_column()` using openpyxl
- [ ] Add column naming convention logic
- [ ] Add validation before creation
- [ ] Add "Auto-Create Column" button to EditFlowDialog
- [ ] Test with real Excel files (validate row structure)
- [ ] Add error handling (file locked, invalid path, etc.)
- [ ] User testing: Create 5 new flowlines, verify Excel updated

### Sprint 3: Excel Preview Widget
- [ ] Create `ExcelPreviewWidget` using QTableWidget (~150 lines)
- [ ] Implement: `load_sheet()`, `show_sheet()`, `save_to_excel()`
- [ ] Add cell editing (double-click)
- [ ] Add "Add Row" button for new months
- [ ] Integrate into `ExcelSetupDialog` (right pane)
- [ ] Add mini-preview to `EditFlowDialog`
- [ ] User testing: Edit cells, save, verify in Excel

### Sprint 4: Polish & Integration
- [ ] Thread long Excel operations
- [ ] Add progress dialogs
- [ ] Handle file locks gracefully
- [ ] Add warning dialogs before modifications
- [ ] Performance optimization (cache sheet list)
- [ ] Documentation in docstrings
- [ ] Full integration testing

---

## 📝 Code Examples

### ExcelManager Structure

```python
# src/services/excel_manager.py

class ExcelManager:
    """Excel operations hub for flow diagram system."""
    
    def __init__(self):
        self.excel_path = self._resolve_path()
        self._sheets_cache = None
        self._columns_cache = {}
        self._last_mtime = None
    
    def get_sheets(self) -> List[str]:
        """Get all sheet names."""
        # Implementation using pandas or openpyxl
        pass
    
    def get_columns_for_sheet(self, sheet: str) -> List[str]:
        """Get column names for a sheet (cached)."""
        # Check file modification time
        # Return from cache if valid
        # Reload from Excel if modified
        pass
    
    def create_column(self, sheet: str, column_name: str) -> bool:
        """
        Create new column in Excel.
        
        Returns: True if successful, False otherwise
        """
        # Open workbook with openpyxl
        # Find target sheet
        # Find next empty column (after data)
        # Write header row
        # Create empty data rows matching structure
        # Save file
        # Invalidate cache
        pass
    
    def get_volume(self, sheet: str, column: str, year: int, month: int) -> Optional[float]:
        """Get flow volume for specific month."""
        # Load sheet data
        # Find matching year/month row
        # Return cell value for column
        pass
    
    def auto_map_flow(self, from_id: str, to_id: str, sheet: str = None) -> Optional[Dict]:
        """
        Auto-detect Excel column for a flow.
        
        Returns: {sheet: str, column: str} or None if no match
        """
        # Generate possible column names
        # Search columns for matches
        # Return best match
        pass
    
    def validate_excel(self) -> Tuple[bool, List[str]]:
        """Validate Excel file structure."""
        # Check file exists
        # Check has Flows_* sheets
        # Check has Year/Month columns
        # Return (is_valid, error_list)
        pass

# Singleton
_manager = None
def get_excel_manager() -> ExcelManager:
    global _manager
    if _manager is None:
        _manager = ExcelManager()
    return _manager
```

---

## 📚 References

**PySide6 with Excel:**
- `pandas.ExcelFile` - Safe, context-managed Excel reading
- `openpyxl.load_workbook()` - Direct Excel cell manipulation
- `QTableWidget` - Display/edit tabular data
- `QProgressDialog` - Long-running operations feedback
- `QThread` - Background file operations

**Excel Best Practices:**
- Always use context managers or explicit close()
- Check file modification time before invalidating cache
- Warn users before modifying files they might have open
- Use data_only=True to avoid formula evaluation issues

---

## 🚀 Next Steps

1. **Review & Approve:** Get feedback on architecture
2. **Create ExcelManager:** Start Sprint 1 implementation
3. **Refactor Dialogs:** Remove duplicate code
4. **Add Auto-Column:** Sprint 2 (biggest UX win)
5. **Preview Widget:** Sprint 3 (polish)
6. **User Testing:** Gather feedback early

**Estimated Effort:**
- Sprint 1: 4-6 hours (foundation)
- Sprint 2: 6-8 hours (auto-column creation)
- Sprint 3: 6-8 hours (preview widget)
- Sprint 4: 3-4 hours (polish, testing)
- **Total: 19-26 hours** (2-3 weeks part-time)

---

## ❓ Questions for User

1. **QAxWidget vs QTableWidget:** Do you want actual Excel editing in the app, or is a spreadsheet-like table sufficient?
2. **Auto-Column Naming:** Should column names auto-generate (e.g., `BH123_to_Sump`), or let user customize?
3. **File Modification Warning:** Should we warn when user creates columns? (Recommended: YES)
4. **Data Entry:** After column creation, do users enter flow data in app (via preview widget) or in Excel? (Recommend: Both supported)
5. **Priority:** Start with Sprint 1 (foundation), then which sprint next? (Recommend: Sprint 2 for UX)

