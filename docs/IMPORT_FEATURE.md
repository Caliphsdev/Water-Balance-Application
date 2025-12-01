# Data Import Feature Documentation

## Overview
The Data Import module allows users to import water balance data from Excel files with comprehensive validation and error handling.

## Features Implemented

### 1. Import Module UI (`src/ui/data_import.py`)
- **Import Type Selection**: Choose between water sources, storage facilities, or measurements
- **File Browser**: Easy Excel file selection with file dialog
- **Data Preview**: View imported data before committing to database
- **Progress Tracking**: Real-time progress bar and status messages
- **Validation**: Automatic column validation against required fields
- **Batch Import**: Import multiple records with error reporting

### 2. Excel Templates (`templates/`)
Three ready-to-use templates created:
- `water_sources_template.xlsx` - 4 sample water sources
- `storage_facilities_template.xlsx` - 4 sample storage facilities  
- `measurements_template.xlsx` - 8 sample measurement records
- `README.txt` - Complete user guide

### 3. Import Configurations
Each import type has defined column requirements:

#### Water Sources
- **Required**: source_code, source_name, source_type
- **Optional**: average_flow_rate, flow_units, reliability_factor, description, active

#### Storage Facilities
- **Required**: facility_code, facility_name, total_capacity
- **Optional**: facility_type, surface_area, minimum_operating_level, maximum_operating_level, description, active

#### Measurements
- **Required**: measurement_date, measurement_type
- **Optional**: source_id, facility_id, volume, flow_rate, measured, data_source

### 4. Validation & Error Handling
- Column validation before import
- Duplicate detection (checks existing codes)
- Date parsing for measurements
- Numeric validation for volumes/capacities
- Individual row error tracking
- Comprehensive error reporting

### 5. Integration
- Accessible via sidebar navigation (Import/Export)
- Quick access button in toolbar (📥 Import Data)
- Database manager integration with full CRUD support

## Usage Instructions

1. **Navigate to Import Module**
   - Click "Import/Export" in sidebar, OR
   - Click "📥 Import Data" button in toolbar

2. **Select Import Type**
   - Choose: water_sources, storage_facilities, or measurements

3. **Browse Excel File**
   - Click "Browse..." button
   - Select your Excel file (.xlsx or .xls)

4. **Preview Data**
   - Click "Preview Data" to validate file
   - Review columns and sample data (first 100 rows)

5. **Import to Database**
   - Click "Import Data" to commit
   - View progress bar and status
   - Review success/error report

## Testing

### Test Suite (`tests/test_import.py`)
All 6 tests passing:
- ✓ Import templates exist
- ✓ Water sources template valid
- ✓ Storage facilities template valid
- ✓ Measurements template valid
- ✓ Import validation detects errors
- ✓ add_measurement method works

### Manual Testing Checklist
- [x] Module loads without errors
- [x] File browser works correctly
- [x] Preview displays data properly
- [x] Validation catches missing columns
- [x] Import creates database records
- [x] Duplicate detection works
- [x] Error reporting is clear
- [x] Progress tracking functions

## Technical Details

### Dependencies
- `pandas`: Excel file reading/writing
- `openpyxl`: Excel format support
- `tkinter.filedialog`: File selection dialog

### Database Integration
Uses DatabaseManager methods:
- `add_water_source(**data)`
- `add_storage_facility(data)`
- `add_measurement(data)`
- `execute_query()` for duplicate checking

### File Format Support
- Excel 2007+ (.xlsx)
- Excel 97-2003 (.xls)
- First sheet is read by default

## Known Limitations & Future Enhancements

### Current Limitations
- Only imports from first sheet
- Preview limited to 100 rows
- No update mode (only insert)
- No Excel export functionality yet

### Planned Enhancements
1. Multi-sheet import
2. Update existing records option
3. Data mapping interface for custom columns
4. Import history tracking
5. Excel template download from app
6. Export to Excel functionality
7. CSV format support

## Files Modified/Created

### New Files
- `src/ui/data_import.py` (470 lines) - Import module UI
- `src/utils/create_templates.py` (150 lines) - Template generator
- `tests/test_import.py` (200 lines) - Test suite
- `templates/water_sources_template.xlsx`
- `templates/storage_facilities_template.xlsx`
- `templates/measurements_template.xlsx`
- `templates/README.txt`
- `docs/IMPORT_FEATURE.md` (this file)

### Modified Files
- `src/ui/main_window.py` - Added _load_import_export() method
- `src/database/db_manager.py` - Verified add_measurement() exists

## Success Metrics
✓ All 6 import tests passing  
✓ Templates generated successfully  
✓ UI integrated into main application  
✓ Validation working correctly  
✓ Error handling comprehensive  
✓ User documentation complete  

**Feature Status: COMPLETE ✓**
