# Water Balance Application - Project Structure

## Directory Organization

```
Water-Balance-Application/
├── .github/              # GitHub configuration and CI/CD
│   ├── copilot-instructions.md
│   └── instructions/     # Code standards and guidelines
│
├── config/               # Application configuration files
│   └── app_config.yaml
│
├── data/                 # Data files and templates
│   ├── *.json           # JSON configuration files
│   ├── diagrams/        # Flow diagram definitions
│   └── templates/       # Template text files
│
├── docs/                 # Documentation (all .md files)
│   ├── README.md        # Documentation index
│   ├── features/        # Feature documentation
│   └── *.md             # Various project docs
│
├── logo/                 # Branding assets
│   ├── Logo Two rivers.png
│   ├── Company Logo.png
│   └── Water Balance.ico
│
├── logs/                 # Application log files
│   └── *.log
│
├── scripts/              # Utility scripts (development only)
│   ├── README.md
│   ├── run_tests.py
│   ├── benchmark_performance.py
│   ├── cleanup_test_transfers.py
│   ├── debug_import.py
│   ├── update_trial.py
│   └── verify_calculations_fixes.py
│
├── src/                  # Source code (application)
│   ├── main.py          # Application entry point
│   ├── config/          # Config management
│   ├── database/        # Database layer
│   ├── licensing/       # License management
│   ├── models/          # Data models
│   ├── ui/              # User interface
│   └── utils/           # Utility modules
│
├── tests/                # Test suite (all test files)
│   ├── test_*.py        # Unit/integration tests
│   ├── ui/              # UI-specific tests
│   └── test_licensing/  # License tests
│
├── .venv/                # Python virtual environment
│
├── build.ps1             # Build script for PyInstaller
├── conftest.py           # Pytest configuration
├── installer.iss         # Inno Setup installer script
├── LICENSE.txt           # Software license
├── pytest.ini            # Pytest settings
├── README.md             # Main project readme
├── requirements.txt      # Python dependencies
├── setup.py              # Package setup
├── sitecustomize.py      # Python customization
└── water_balance.spec    # PyInstaller spec file
```

## Build & Distribution

### Files for PyInstaller
- **water_balance.spec** - PyInstaller specification
- **build.ps1** - PowerShell build script
- **src/** - All source code
- **config/** - Configuration files (included in build)
- **data/** - Data files and templates (included in build)
- **logo/** - Icons for executable

### Files for Inno Setup
- **installer.iss** - Installer configuration
- **dist/WaterBalance/** - Output from PyInstaller
- **LICENSE.txt** - License file for installer
- **README.md** - Readme for installer

### Excluded from Build
- **tests/** - Testing code (development only)
- **scripts/** - Utility scripts (development only)
- **docs/** - Documentation (except key docs in dist)
- **.venv/** - Virtual environment
- **logs/** - Log files
- **.pytest_cache/** - Test cache
- **__pycache__/** - Python cache

## Key Configuration Files

| File | Purpose |
|------|---------|
| `water_balance.spec` | PyInstaller build specification |
| `installer.iss` | Inno Setup installer configuration |
| `build.ps1` | Automated build script |
| `requirements.txt` | Python package dependencies |
| `pytest.ini` | Test runner configuration |
| `conftest.py` | Pytest fixtures and hooks |
| `.gitignore` | Git exclusion rules |
| `config/app_config.yaml` | Application settings |

## Development Workflow

### 1. Development
```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run application
.venv\Scripts\python src\main.py

# Run tests
.venv\Scripts\python -m pytest tests -v

# Run utility scripts
.venv\Scripts\python scripts\<script_name>.py
```

### 2. Building
```powershell
# Build executable with PyInstaller
.\build.ps1

# Output: dist\WaterBalance\WaterBalance.exe
```

### 3. Creating Installer
```powershell
# Open Inno Setup
# Load installer.iss
# Click Build → Compile

# Output: installer_output\WaterBalanceSetup_v1.0.0.exe
```

## File Organization Rules

### ✅ Root Directory - Keep Clean
- Only essential files (config, build, setup)
- No test files
- No documentation files (except README.md, LICENSE.txt)
- No utility scripts

### ✅ Tests Directory
- All test_*.py files
- Test fixtures and conftest.py (root conftest is for pytest config)
- Test-specific data

### ✅ Docs Directory
- All .md documentation files
- Project documentation
- Feature guides
- Development notes

### ✅ Scripts Directory
- Development utility scripts
- Testing helpers
- Maintenance scripts
- Performance tools

## Quick Reference

### Run Application
```powershell
.venv\Scripts\python src\main.py
```

### Run Tests
```powershell
.venv\Scripts\python -m pytest tests -v
```

### Build Executable
```powershell
.\build.ps1
```

### Create Installer
```powershell
# Use Inno Setup Compiler with installer.iss
```

---

**Last Updated:** January 23, 2026  
**Version:** 1.0.0
