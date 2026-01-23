# Water Balance Application

Calculating water balance of a mine across 8 areas with interactive flow diagrams, balance checking, and Excel integration.

> **📦 Ready for Distribution:** Project organized and configured for PyInstaller and Inno Setup builds. See [BUILD_GUIDE.md](BUILD_GUIDE.md) for instructions.

## 📁 Directory Structure

### Core Directories

\\\
Water-Balance-Application/
├── src/                          # Application source code
│   ├── main.py                   # Entry point
│   ├── ui/                       # User interface modules
│   ├── utils/                    # Utility functions and calculators
│   └── database/                 # Database management
│
├── data/                         # Data files
│   ├── water_balance.db          # SQLite database
│   ├── diagrams/                 # Flow diagram JSON files
│   └── timeseries/               # Excel data files
│
├── config/                       # Configuration
│   └── app_config.yaml           # Application settings
│
├── docs/                         # Documentation
│   ├── features/                 # Feature guides and tutorials
│   ├── archive/                  # Historical documentation
│   └── *.md                      # Main documentation files
│
├── scripts/                      # Utility and debug scripts
│   ├── debug/                    # Diagnostic tools (organized by type)
│   │   ├── excel_mapping/        # Excel/mapping checks
│   │   ├── structure/            # Database structure checks
│   │   ├── area_specific/        # Area-specific debugging
│   │   ├── flow_checks/          # Flow validation
│   │   ├── verification/         # System verification
│   │   └── misc/                 # Miscellaneous checks
│   │
│   ├── utilities/                # One-off automation scripts
│   └── *.py                      # Setup and utility scripts
│
├── .github/                      # GitHub configuration
│   ├── instructions/             # Coding conventions
│   └── workflows/                # CI/CD pipelines
│
└── logo/, backups/               # Supporting files
\\\

## 🚀 Getting Started

1. **Install dependencies**: \pip install -r requirements.txt\
2. **Run the application**: \python src/main.py\
3. **Check documentation**: See [Feature Guides](docs/features/INDEX.md)

## 📚 Documentation

### Main Topics
- [Balance Check System](docs/BALANCE_CHECK_README.md) - Validate water balance calculations
- [Flow Diagrams](docs/FLOW_DIAGRAM_GUIDE.md) - Interactive visualization and editing
- [Component Management](docs/features/COMPONENT_RENAME_SYSTEM_INDEX.md) - Add, edit, and rename components
- [Excel Integration](docs/features/EXCEL_INTEGRATION_SUMMARY.md) - Map and sync flow data

### All Features
See [Feature Documentation Index](docs/features/INDEX.md) for complete list of guides.

## 🛠️ Debug & Utilities

### Debug Scripts
Located in \scripts/debug/\ - organized by purpose:
- **excel_mapping/** - Excel validation and mapping checks
- **structure/** - Database and JSON structure validation
- **area_specific/** - Area-specific debugging tools
- **flow_checks/** - Individual flow and component validation
- **verification/** - System verification and testing
- **misc/** - Miscellaneous diagnostic tools

👉 See [\scripts/debug/README.md\](scripts/debug/README.md) for detailed guide.

### Utility Scripts
Located in \scripts/utilities/\ - one-off automation and fixes:
- Data structure creation and updates
- Excel synchronization
- Component renaming and addition
- Area setup and configuration

👉 See [\scripts/utilities/README.md\](scripts/utilities/README.md) for detailed guide.

## 📋 Templates
Located in `data/templates/`:- \INFLOW_CODES_TEMPLATE.txt\ - Inflow component definitions
- \OUTFLOW_CODES_TEMPLATE_CORRECTED.txt\ - Outflow component definitions
- \DAM_RECIRCULATION_TEMPLATE.txt\ - Recirculation loop definitions

## 🗂️ Archived Documentation

Older status reports, implementation summaries, and superseded documentation are kept in [\docs/archive/\](docs/archive/) for historical reference.

## 📖 Quick Links

| Need | Location |
|------|----------|
| **Balance Checking** | [docs/BALANCE_CHECK_README.md](docs/BALANCE_CHECK_README.md) |
| **Flow Diagram Usage** | [docs/FLOW_DIAGRAM_GUIDE.md](docs/FLOW_DIAGRAM_GUIDE.md) |
| **Add Components** | [Component Guide](docs/features/ADD_COMPONENTS_UI_GUIDE.md) |
| **Excel Mapping** | [Excel Integration](docs/features/EXCEL_INTEGRATION_SUMMARY.md) |
| **Debug Tools** | [Debug Guide](scripts/debug/README.md) |
| **Utilities** | [Utilities Guide](scripts/utilities/README.md) |
| **All Features** | [Feature Index](docs/features/INDEX.md) |
| **Component Rename** | [scripts/component_rename_manager.py](scripts/component_rename_manager.py) |
| **Auto-Sync Flows** | [scripts/autosync_flows_to_excel.py](scripts/autosync_flows_to_excel.py) |

---

*Water Balance Application - Mining Operations Water Management*
