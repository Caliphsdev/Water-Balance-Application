# License Admin Tool

Standalone application for managing license keys.

## Features

- Generate new license keys
- View all licenses with filtering and search
- Activate/Deactivate/Revoke licenses
- Update license tiers
- Export license list to CSV

## Running

### Windows (Batch file)
```batch
tools\license_admin\run_admin.bat
```

### Manual
```powershell
# From project root
.venv\Scripts\python tools\license_admin\main.py
```

## Configuration

Set environment variables before running:

```powershell
$env:SUPABASE_URL = "https://xxxxx.supabase.co"
$env:SUPABASE_SERVICE_KEY = "your-service-role-key"
```

Or configure via Tools → Configure Supabase in the application.

## Notes

- Uses service role key for full access to licenses table
- anon key works but limited by RLS policies
- Export creates CSV with all license fields
