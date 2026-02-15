# Water Balance Dashboard

**Professional PySide6 water balance management application for Trans Africa Resources**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)
![Status](https://img.shields.io/badge/Status-Active%20Development-orange.svg)

---

## 🎯 Overview

A comprehensive water balance management system featuring:

- **Interactive Flow Diagrams** - Visual representation of water flows with drag-and-drop editing
- **Real-time Dashboard** - KPI cards showing storage facilities, capacity, utilization
- **Calculation Engine** - Water balance calculations with error tracking
- **Data Integration** - Excel import/export, database storage
- **Licensing + Updates** - License validation with update checks
- **Notifications** - In-app message and notification center
- **Professional UI** - Modern PySide6 interface with dark/light themes

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Windows 10/11

### Installation

```powershell
# Clone the repository
git clone https://github.com/Caliphsdev/Water-Balance-Application.git
cd Water-Balance-Application

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

---

## 📊 Features

### Dashboard
- **Storage Facilities** - Count of active facilities from database
- **Total Capacity** - Combined capacity in Mm³
- **Current Volume** - Live volume readings
- **Utilization** - Percentage utilization with status indicators
- **Environmental KPIs** - Rainfall and evaporation data

### Flow Diagram Editor
- Interactive node placement and editing
- Orthogonal edge routing (90° angles)
- 17 anchor points per node for precise connections
- Color-coded flow types (clean, dirty, recirculation)
- Real-time balance calculations

### Calculation Engine
- Monthly water balance calculations
- Inflow/outflow tracking
- Recirculation monitoring
- Balance error detection with status indicators

### Monitoring and Notifications
- Borehole and PCD monitoring dashboards
- Message center with notification updates

### Updates and Licensing
- License validation on startup (fail-closed)
- Runtime license revalidation every 15 minutes (configurable)
- Runtime checks run in background so UI remains responsive
- Background update checks with download prompts

---

## 📁 Project Structure

```
dashboard_waterbalance/
├── src/
│   ├── main.py                 # Application entry point
│   ├── ui/                     # PySide6 UI components
│   │   ├── main_window.py      # Main application window
│   │   ├── dashboards/         # Page controllers
│   │   ├── dialogs/            # Modal dialogs
│   │   └── components/         # Reusable widgets
│   ├── services/               # Business logic layer
│   ├── database/               # SQLite database access
│   └── models/                 # Pydantic data models
├── config/                     # YAML configuration files
├── data/                       # Diagrams, database files
├── tests/                      # pytest test suite
├── Docs/                       # Documentation
└── .github/                    # Copilot instructions, skills
```

---

## 🧪 Testing

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src

# Run specific test
pytest tests/test_storage_facilities_backend.py -v
```

---

## 📚 Documentation

See [Docs/INDEX.md](Docs/INDEX.md) for complete documentation including:

- [Quick Start Guide](Docs/00-GETTING_STARTED/QUICKSTART.md)
- [Architecture Patterns](Docs/01-ARCHITECTURE/PYSIDE6_PATTERNS.md)
- [UI Development Guide](Docs/03-FRONTEND/UI_DEVELOPMENT_GUIDE.md)
- [PySide6 Modules Reference](Docs/06-REFERENCE/PYSIDE6_MODULES_GUIDE.md)

---

## 🗂️ Data and Configuration

- User data is stored in `%LOCALAPPDATA%\WaterBalanceDashboard` for packaged builds.
- Local config lives in `config/app_config.yaml` and is copied to the user folder on first run.

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **UI Framework** | PySide6 (Qt for Python) |
| **Database** | SQLite |
| **Data Processing** | pandas, numpy |
| **Excel Integration** | openpyxl |
| **Configuration** | PyYAML, Pydantic |
| **Testing** | pytest, pytest-qt |
| **Packaging** | PyInstaller |

---

## 📄 License

Proprietary - Trans Africa Resources

### Third-Party and Qt Notices

- This application uses **PySide6 (Qt for Python)** and related Qt libraries.
- Third-party notices are provided in `THIRD_PARTY_LICENSES.txt`.
- Bundled Qt/PySide license texts are provided in `licenses/qt/` for distribution builds.
- Packaging excludes **Qt Virtual Keyboard** binaries/plugins to avoid accidental GPL-only module distribution in standard builds.

### License Enforcement Behavior

- Startup is **fail-closed** when licensing system is unavailable.
- Splash screen is hidden before any licensing modal is shown.
- Runtime recheck interval is configured by `licensing.runtime_check_interval_seconds` (default `900`).
- Offline token defaults are production-safe (`license.offline_validity_days`, fallback `30` days).
- Blocked states: `expired`, `revoked`, `hwid_mismatch`, `invalid`, `clock_tamper`, `system_unavailable`.

---

## 👥 Contributors

- Development Team - Caliphsdev

---

**Last Updated:** February 2026
