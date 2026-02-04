# Setup and Operations

**Deployment, operations, and troubleshooting**

---

## 📖 Files in This Section

### [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
Common issues and solutions.

**Topics covered:**
- Common problems
- Error messages and solutions
- Debugging techniques
- Performance issues
- Environment problems
- Database issues
- UI rendering problems

**Use when:**
- Something isn't working
- Need to fix an error
- Diagnosing issues
- Performance problems

**Time:** Reference as needed

---

## 🛠️ Common Tasks

### Setting Up Development Environment

1. Clone repository
2. Create virtual environment: `.venv\Scripts\python -m pip install -r requirements.txt`
3. Run app: `.venv\Scripts\python src/main.py`
4. Run tests: `.venv\Scripts\python -m pytest tests/ -v`

See [../00-GETTING_STARTED/QUICK_START.md](../00-GETTING_STARTED/QUICK_START.md) for detailed setup.

---

### Running the Application

```bash
.venv\Scripts\python src/main.py
```

**Features:**
- Fast startup (async DB loading)
- Loading screen during initialization
- License validation
- Auto-recovery on errors

---

### Building an Executable

```bash
# Compile UI files first
./compile_ui.ps1

# Build with PyInstaller
pyinstaller water_balance.spec
```

Result: `dist/water_balance.exe`

---

### Database Operations

**Reset database:**
```bash
.venv\Scripts\python -c "from src.database.schema import DatabaseSchema; DatabaseSchema().create_database()"
```

**Backup database:**
Database auto-backs up before major operations. Manual backup:
```bash
cp data/water_balance.db data/water_balance.db.bak-$(date +%Y%m%d_%H%M%S)
```

---

### Running Tests

```bash
# All tests
.venv\Scripts\python -m pytest tests/ -v

# Specific test file
.venv\Scripts\python -m pytest tests/test_storage_facilities_backend.py -v

# With coverage
.venv\Scripts\python -m pytest tests/ --cov=src --cov-report=html
```

---

## 🔧 Configuration

Main config file: `config/app_config.yaml`

Key settings:
```yaml
features:
  fast_startup: true          # Enable async DB loading
  excel_monitoring: true      # Watch Excel file changes

data_sources:
  database_path: data/water_balance.db
  meter_readings_excel: data/meter_readings.xlsx
  
licensing:
  offline_grace_days: 7       # Grace period when no network
```

---

## 📊 Monitoring & Logs

### Log Files
Location: `logs/` directory

- `app.log` - Application events
- `database.log` - Database operations
- `excel.log` - Excel file monitoring
- `calculations.log` - Balance calculations

### Viewing Logs
```bash
# Real-time logs
tail -f logs/app.log

# Search for errors
grep "ERROR" logs/app.log
```

---

## ⚠️ Common Issues

### App Won't Start
→ Check logs in `logs/app.log`  
→ Verify `.venv` exists and is activated  
→ Check database: `data/water_balance.db` exists

### Database Errors
→ Check database is not locked (not open elsewhere)  
→ Try backing up and resetting: see Database Operations above  
→ Check file permissions

### Excel Not Loading
→ Verify file path in `config/app_config.yaml`  
→ Check file is not open elsewhere  
→ Ensure Excel file format is `.xlsx` (not `.xls`)

### UI Not Rendering
→ Check GPU drivers are up to date  
→ Try disabling hardware acceleration in config  
→ Clear cache and restart

---

## 📚 Related Documentation

- **Getting Started:** See [00-GETTING_STARTED/QUICK_START.md](../00-GETTING_STARTED/QUICK_START.md)
- **Architecture:** See [01-ARCHITECTURE/](../01-ARCHITECTURE/)
- **Reference:** See [DOCUMENTATION/SETUP_GUIDE.md](../DOCUMENTATION/SETUP_GUIDE.md) for detailed setup

---

## ✅ Pre-Deployment Checklist

- [ ] All tests passing: `pytest tests/ -v`
- [ ] No linting errors
- [ ] Database is backed up
- [ ] Config file is correct
- [ ] Excel files are in right location
- [ ] License validation passing
- [ ] UI renders correctly
- [ ] Performance is acceptable

---

## 🚀 Deployment Steps

1. Test locally: `.venv\Scripts\python src/main.py`
2. Run full test suite: `.venv\Scripts\python -m pytest tests/ -v`
3. Build executable: `pyinstaller water_balance.spec`
4. Test executable: `dist/water_balance.exe`
5. Create installer (if needed): `iscc installer.iss`
6. Deploy and monitor logs

---

**For more details:** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for specific issues.
