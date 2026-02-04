# ExcelManager Implementation Guide - Quick Start

**Target:** Create `src/services/excel_manager.py` (200-250 lines)

---

## Step 1: Create the Service File

**File:** `src/services/excel_manager.py`

```python
"""
Excel Manager Service (CENTRALIZED HUB).

Purpose:
- Consolidate all Excel operations (read, write, create columns, auto-map)
- Eliminate code duplication from dialogs
- Provide single API for all Excel interactions
- Cache sheet/column lists for performance
- Handle errors gracefully

Usage:
    manager = get_excel_manager()
    sheets = manager.get_sheets()
    columns = manager.get_columns_for_sheet('Flows_UG2 North')
    success = manager.create_column('Flows_UG2 North', 'BH_to_Sump')
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List, Optional, Tuple
from openpyxl import load_workbook
import pandas as pd

from utils.app_logger import logger
from utils.config_manager import config, get_resource_path


class ExcelManager:
    """Excel operations hub for flow diagram system (SINGLETON)."""
    
    def __init__(self):
        """Initialize manager with config paths."""
        self.excel_path = self._resolve_excel_path()
        self._sheets_cache: Optional[List[str]] = None
        self._columns_cache: Dict[str, List[str]] = {}
        self._last_mtime: Optional[float] = None
    
    def _resolve_excel_path(self) -> Path:
        """Resolve Excel file path from config."""
        # Get from config: data_sources.timeseries_excel_path
        excel_config_path = config.get(
            'data_sources.timeseries_excel_path',
            'test_templates/Water_Balance_TimeSeries_Template.xlsx'
        )
        
        cfg_path = Path(excel_config_path)
        if cfg_path.is_absolute():
            return cfg_path
        
        base_dir = get_resource_path('')
        return base_dir / cfg_path
    
    def _check_cache_validity(self) -> bool:
        """Check if Excel file was modified since last load."""
        if not self.excel_path.exists():
            return False
        
        try:
            current_mtime = self.excel_path.stat().st_mtime
            if self._last_mtime is not None and current_mtime != self._last_mtime:
                # File modified - invalidate cache
                self._invalidate_cache()
            self._last_mtime = current_mtime
            return True
        except Exception as e:
            logger.error(f"Error checking Excel file: {e}")
            return False
    
    def _invalidate_cache(self):
        """Clear all caches."""
        self._sheets_cache = None
        self._columns_cache.clear()
        logger.info("📁 Excel cache invalidated")
    
    # ===================== Core Methods =====================
    
    def get_sheets(self) -> List[str]:
        """
        Get all sheet names from Excel workbook.
        
        Returns:
            List of sheet names (e.g., ['Flows_UG2 North', 'Flows_Merensky South'])
        """
        if not self._check_cache_validity():
            return []
        
        if self._sheets_cache is not None:
            return self._sheets_cache
        
        try:
            with pd.ExcelFile(self.excel_path, engine='openpyxl') as xls:
                self._sheets_cache = xls.sheet_names
                return self._sheets_cache
        except Exception as e:
            logger.error(f"Error reading Excel sheets: {e}")
            return []
    
    def get_columns_for_sheet(self, sheet_name: str) -> List[str]:
        """
        Get column names for a specific sheet.
        
        Skips system columns (Date, Year, Month) and returns data columns only.
        
        Args:
            sheet_name: Excel sheet name (e.g., 'Flows_UG2 North')
        
        Returns:
            List of column names (e.g., ['BH_to_Sump', 'Sump_to_Plant', ...])
        """
        if not self._check_cache_validity():
            return []
        
        if sheet_name in self._columns_cache:
            return self._columns_cache[sheet_name]
        
        try:
            df = pd.read_excel(
                self.excel_path,
                sheet_name=sheet_name,
                nrows=1,
                engine='openpyxl'
            )
            
            # Filter out system columns
            skip_cols = {'Date', 'Year', 'Month'}
            columns = [col for col in df.columns if col not in skip_cols]
            
            self._columns_cache[sheet_name] = columns
            return columns
        except Exception as e:
            logger.warning(f"Error reading columns from '{sheet_name}': {e}")
            return []
    
    def create_column(self, sheet_name: str, column_name: str) -> bool:
        """
        Create a new column in Excel for a flowline.
        
        Process:
        1. Load workbook with openpyxl
        2. Find target sheet
        3. Find next empty column (after existing data)
        4. Write column header
        5. Create empty data rows (matching existing Year/Month structure)
        6. Save workbook
        7. Invalidate cache
        
        Args:
            sheet_name: Target sheet (e.g., 'Flows_UG2 North')
            column_name: New column header (e.g., 'BH_to_Sump')
        
        Returns:
            True if successful, False if error
        """
        if not self.excel_path.exists():
            logger.error(f"Excel file not found: {self.excel_path}")
            return False
        
        try:
            # Load workbook
            wb = load_workbook(self.excel_path)
            
            if sheet_name not in wb.sheetnames:
                logger.error(f"Sheet '{sheet_name}' not found in Excel")
                return False
            
            ws = wb[sheet_name]
            
            # Find next empty column (after existing data)
            next_col = ws.max_column + 1
            
            # Write header (assume row 1 is headers)
            ws.cell(row=1, column=next_col, value=column_name)
            
            # Create empty data rows (matching existing structure)
            # TODO: Detect how many rows have data, create matching empty cells
            for row in range(2, ws.max_row + 1):
                ws.cell(row=row, column=next_col, value=None)
            
            # Save workbook
            wb.save(self.excel_path)
            wb.close()
            
            # Invalidate cache so next read gets new column
            self._invalidate_cache()
            
            logger.info(f"✅ Created column '{column_name}' in '{sheet_name}'")
            return True
        
        except Exception as e:
            logger.error(f"Error creating column: {e}")
            return False
    
    def auto_map_flow(self, from_id: str, to_id: str, sheet_name: str = None) -> Optional[Dict]:
        """
        Auto-detect or suggest Excel column for a flowline.
        
        Strategy:
        1. Generate likely column names (e.g., BH_to_Sump, bh_to_sump)
        2. Search for exact match in sheet columns
        3. Return match or None
        
        Args:
            from_id: Source node ID (e.g., 'BH')
            to_id: Destination node ID (e.g., 'Sump')
            sheet_name: Sheet to search (if None, search all sheets)
        
        Returns:
            {sheet: str, column: str} if match found, else None
        """
        # Generate possible column names
        candidates = [
            f"{from_id}_to_{to_id}",
            f"{from_id.lower()}_to_{to_id.lower()}",
            f"{from_id}_{to_id}",
            f"{from_id}{to_id}",
        ]
        
        sheets_to_search = [sheet_name] if sheet_name else self.get_sheets()
        
        for sheet in sheets_to_search:
            columns = self.get_columns_for_sheet(sheet)
            
            # Try exact match first
            for candidate in candidates:
                if candidate in columns:
                    logger.info(f"Found auto-mapping: {sheet}:{candidate}")
                    return {'sheet': sheet, 'column': candidate}
            
            # Try case-insensitive match
            columns_lower = {col.lower(): col for col in columns}
            for candidate in candidates:
                candidate_lower = candidate.lower()
                if candidate_lower in columns_lower:
                    actual_column = columns_lower[candidate_lower]
                    logger.info(f"Found auto-mapping (case-insensitive): {sheet}:{actual_column}")
                    return {'sheet': sheet, 'column': actual_column}
        
        logger.debug(f"No auto-mapping found for {from_id}→{to_id}")
        return None
    
    def get_volume(self, sheet_name: str, column_name: str, year: int, month: int) -> Optional[float]:
        """
        Get flow volume for a specific month from Excel.
        
        Args:
            sheet_name: Excel sheet name
            column_name: Column name (header)
            year: Year
            month: Month (1-12)
        
        Returns:
            Volume in m³, or None if not found
        """
        try:
            df = pd.read_excel(
                self.excel_path,
                sheet_name=sheet_name,
                engine='openpyxl'
            )
            
            # Find row matching year/month
            matching = df[(df.get('Year') == year) & (df.get('Month') == month)]
            
            if matching.empty or column_name not in df.columns:
                return None
            
            value = matching.iloc[0][column_name]
            return float(value) if pd.notna(value) else None
        
        except Exception as e:
            logger.error(f"Error reading volume from Excel: {e}")
            return None
    
    def validate_excel(self) -> Tuple[bool, List[str]]:
        """
        Validate Excel file structure.
        
        Checks:
        - File exists
        - Has at least one 'Flows_*' sheet
        - Sheets have Year/Month or Date columns
        - Sheets have data rows
        
        Returns:
            (is_valid: bool, error_list: List[str])
        """
        errors = []
        
        if not self.excel_path.exists():
            errors.append(f"Excel file not found: {self.excel_path}")
            return False, errors
        
        sheets = self.get_sheets()
        if not sheets:
            errors.append("Cannot read sheets from Excel file")
            return False, errors
        
        flow_sheets = [s for s in sheets if s.startswith('Flows_')]
        if not flow_sheets:
            errors.append("No 'Flows_*' sheets found in Excel")
            return False, errors
        
        # Validate structure of first flow sheet
        try:
            df = pd.read_excel(
                self.excel_path,
                sheet_name=flow_sheets[0],
                nrows=5,
                engine='openpyxl'
            )
            
            required = {'Year', 'Month'} or {'Date'}
            has_time_cols = required.issubset(set(df.columns))
            
            if not has_time_cols:
                errors.append(f"Sheets missing Year/Month or Date columns")
        
        except Exception as e:
            errors.append(f"Error validating Excel structure: {e}")
            return False, errors
        
        return len(errors) == 0, errors
    
    def set_excel_path(self, path: Path) -> bool:
        """
        Change Excel file path (for user-selected file).
        
        Args:
            path: New Excel file path
        
        Returns:
            True if file exists and valid, False otherwise
        """
        if not Path(path).exists():
            logger.error(f"Excel file not found: {path}")
            return False
        
        self.excel_path = Path(path)
        self._invalidate_cache()
        
        is_valid, errors = self.validate_excel()
        if not is_valid:
            logger.warning(f"Excel file validation failed: {errors}")
            return False
        
        logger.info(f"✅ Excel path updated: {self.excel_path}")
        return True


# ===================== Singleton =====================

_manager_instance: Optional[ExcelManager] = None


def get_excel_manager() -> ExcelManager:
    """Get singleton instance of ExcelManager."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ExcelManager()
    return _manager_instance


def reset_excel_manager():
    """Reset singleton (for testing or reconfiguration)."""
    global _manager_instance
    _manager_instance = None
    logger.info("🔄 Excel manager reset")
```

---

## Step 2: Update Dialogs to Use ExcelManager

### EditFlowDialog Refactor

**Before:**
```python
def _populate_excel_options(self):
    # TODO: Get sheet names from ExcelManager
    # TODO: Get column names for selected sheet from ExcelManager
    sheets = [...]  # DUPLICATED CODE
```

**After:**
```python
def _populate_excel_options(self):
    """Populate Excel sheet and column dropdowns using ExcelManager."""
    manager = get_excel_manager()
    
    # Get sheets
    sheets = manager.get_sheets()
    self.ui.combo_sheet.addItems(sheets)
    
    # Connect: when sheet changes, reload columns
    self.ui.combo_sheet.currentTextChanged.connect(self._on_sheet_changed)

def _on_sheet_changed(self, sheet_name: str):
    """Update column list when sheet changes."""
    manager = get_excel_manager()
    columns = manager.get_columns_for_sheet(sheet_name)
    self.ui.combo_column.clear()
    self.ui.combo_column.addItems(columns)

def _on_auto_map_clicked(self):
    """Auto-detect column for this flowline."""
    manager = get_excel_manager()
    mapping = manager.auto_map_flow(
        from_id=self.from_node_data.get('id'),
        to_id=self.to_node_data.get('id')
    )
    if mapping:
        self.ui.combo_sheet.setCurrentText(mapping['sheet'])
        self.ui.combo_column.setCurrentText(mapping['column'])
```

### ExcelSetupDialog Refactor

**Similar approach - use manager instead of duplicate code**

---

## Step 3: Add to Services __init__

**File:** `src/services/__init__.py`

```python
from .excel_manager import get_excel_manager, reset_excel_manager

__all__ = ['get_excel_manager', 'reset_excel_manager']
```

---

## Step 4: Testing

**File:** `tests/test_services/test_excel_manager.py`

```python
"""
Unit tests for ExcelManager service.

Test:
- get_sheets() returns list
- get_columns_for_sheet() returns data columns (skips Date/Year/Month)
- create_column() adds header and empty rows
- auto_map_flow() finds matches
- validate_excel() checks structure
"""
```

---

## Next: Auto-Column Creation (Sprint 2)

Once ExcelManager is done, add to EditFlowDialog:

```python
def _on_auto_create_column_clicked(self):
    """Auto-create Excel column for this new flowline."""
    manager = get_excel_manager()
    
    from_id = self.from_node_data.get('id')
    to_id = self.to_node_data.get('id')
    suggested_name = f"{from_id}_to_{to_id}"
    sheet = self.ui.combo_sheet.currentText()
    
    # Show progress
    dialog = QProgressDialog(
        f"Creating column '{suggested_name}'...",
        None, 0, 0, self
    )
    dialog.setWindowModality(Qt.WindowModal)
    dialog.show()
    QApplication.processEvents()
    
    try:
        success = manager.create_column(sheet, suggested_name)
        if success:
            # Reload columns and select the new one
            self._on_sheet_changed(sheet)
            self.ui.combo_column.setCurrentText(suggested_name)
            QMessageBox.information(self, "Success", 
                f"Column '{suggested_name}' created!")
        else:
            QMessageBox.warning(self, "Error", 
                "Failed to create column. Check Excel file.")
    finally:
        dialog.close()
```

---

## Files Modified

```
src/services/
  ├── excel_manager.py         ← NEW
  └── __init__.py              ← UPDATE

src/ui/dialogs/
  ├── edit_flow_dialog.py      ← REFACTOR (remove duplicate code)
  ├── excel_setup_dialog.py    ← REFACTOR (use manager)
  
tests/test_services/
  ├── test_excel_manager.py    ← NEW (unit tests)
```

---

## Effort

- ExcelManager: 2-3 hours (write + test)
- Refactor dialogs: 1-2 hours
- Integration test: 1 hour
- **Total Sprint 1: 4-6 hours**

---

**Ready to proceed?** Approve this plan and we'll start implementation!

