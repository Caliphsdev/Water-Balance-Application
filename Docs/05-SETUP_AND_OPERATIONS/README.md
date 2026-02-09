# Setup and Operations

**Deployment, operations, and troubleshooting**

---

## 🛠️ Common Tasks

### Setting Up Development Environment

1. Clone repository: `git clone https://github.com/Caliphsdev/Water-Balance-Application.git`
2. Create virtual environment: `python -m venv .venv`
3. Activate: `.venv\Scripts\Activate.ps1`
4. Install dependencies: `pip install -r requirements.txt`
5. Run app: `.venv\Scripts\python src/main.py`

See [../00-GETTING_STARTED/QUICKSTART.md](../00-GETTING_STARTED/QUICKSTART.md) for detailed setup.

---

### Running the Application

```bash
.venv\Scripts\python src/main.py
```

**Features:**
- Fast startup with async database loading
- Loading screen during initialization
- License validation
- Auto-recovery on errors

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

### Building an Executable

```powershell
# Build with PyInstaller (preferred: use the script)
.\scripts\packaging\build_windows.ps1
```

Result: `dist/WaterBalanceDashboard/`

Notes:
- PyNaCl uses CFFI; ensure `_cffi_backend` is bundled via the spec file for packaged builds.
- The Windows installer should include the VC++ 2015-2022 x64 redistributable for PyNaCl/native deps.

---

### Database Operations

**Reset database:**
```bash
.venv\Scripts\python -c "from src.database.schema import DatabaseSchema; DatabaseSchema().create_database()"
```

**Backup database:**
```powershell
Copy-Item data\water_balance.db "data\water_balance.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
```

---

## 📦 Release Workflow (Windows)

This is the end-to-end packaging and release workflow used for updates (PyInstaller + Inno Setup + GitHub + Supabase).

### 1) Bump Versions

Update both files to the new version:

- [config/app_config.yaml](../../config/app_config.yaml): `app.version`
- [scripts/packaging/water_balance.iss](../../scripts/packaging/water_balance.iss): `#define AppVersion`

### 2) Build the App Bundle

```powershell
.\scripts\packaging\build_windows.ps1
```

Output:
- `dist/WaterBalanceDashboard/`

### 3) Build the Installer (Inno Setup)

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" .\scripts\packaging\water_balance.iss
```

Output:
- `scripts/packaging/dist/installer/WaterBalanceDashboard-Setup.exe`

### 4) Compute Hash + Size

```powershell
$path = "scripts\packaging\dist\installer\WaterBalanceDashboard-Setup.exe"
Get-FileHash -Algorithm SHA256 $path
(Get-Item $path).Length
```

### 5) Publish GitHub Release

```powershell
gh release create vX.Y.Z "scripts/packaging/dist/installer/WaterBalanceDashboard-Setup.exe" -t "vX.Y.Z" -n "<release notes>"
```

Download URL pattern:
```
https://github.com/Caliphsdev/Water-Balance-Application/releases/download/vX.Y.Z/WaterBalanceDashboard-Setup.exe
```

### 6) Insert Supabase Row

Use `app_updates` so the app can see the new update:

```sql
insert into app_updates (version, min_tiers, download_url, release_notes, file_hash, file_size, is_mandatory)
values (
  'X.Y.Z',
  ARRAY['developer'],
  'https://github.com/Caliphsdev/Water-Balance-Application/releases/download/vX.Y.Z/WaterBalanceDashboard-Setup.exe',
  '<release notes>',
  '<SHA256>',
  <file size bytes>,
  false
);
```

Notes:
- `min_tiers` controls which license tiers get the update.
- `file_hash` must match the SHA256 hash from step 4.
- `file_size` is the installer size in bytes from step 4.


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

### License Token Issuer (Ed25519)

The desktop app verifies offline tokens with an embedded public key. Token signing must happen server-side.

Required setup:
- Set `WATERBALANCE_PUBLIC_KEY` (base64) in the app environment or `license.public_key` in `config/app_config.yaml`.
- Deploy an RPC/Edge Function named `issue_license_token` that returns a signed token for activation/refresh.
- Keep the private key (`WATERBALANCE_PRIVATE_KEY`) only in the admin/server environment.

Generate a key pair (run locally, keep the private key secret):
```bash
python - << 'PY'
from nacl.signing import SigningKey
import base64

sk = SigningKey.generate()
pk = sk.verify_key

private_b64 = base64.urlsafe_b64encode(sk.encode()).decode('utf-8').rstrip('=')
public_b64 = base64.urlsafe_b64encode(pk.encode()).decode('utf-8').rstrip('=')

print('WATERBALANCE_PRIVATE_KEY=' + private_b64)
print('WATERBALANCE_PUBLIC_KEY=' + public_b64)
PY
```

Edge Function deployment (Supabase CLI):
```bash
supabase functions deploy issue_license_token
supabase secrets set APP_SUPABASE_URL=... APP_SUPABASE_SERVICE_ROLE_KEY=... WATERBALANCE_PRIVATE_KEY=...
```
```

---

## 📊 Logs

### Log Files
Location: `logs/` directory

- `app.log` - Application events
- `app_debug.log` - Debug information

### Viewing Logs
```powershell
# Real-time logs
Get-Content logs\app.log -Wait

# Search for errors
Select-String "ERROR" logs\app.log
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

### ImportError: No module named 'PySide6'
```bash
pip install PySide6 PySide6-Addons
```

### ModuleNotFoundError: No module named 'src'
Run from project root:
```bash
cd d:\Projects\dashboard_waterbalance
.venv\Scripts\python src/main.py
```

---

## ✅ Pre-Deployment Checklist

- [ ] All tests passing: `pytest tests/ -v`
- [ ] No linting errors
- [ ] Database is backed up
- [ ] Config file is correct
- [ ] Excel files are in right location
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

## 📚 Related Documentation

- **Getting Started:** [../00-GETTING_STARTED/QUICKSTART.md](../00-GETTING_STARTED/QUICKSTART.md)
- **Architecture:** [../01-ARCHITECTURE/](../01-ARCHITECTURE/)
- **Backend:** [../02-BACKEND/](../02-BACKEND/)
- **Frontend:** [../03-FRONTEND/](../03-FRONTEND/)
