# Utility Scripts

This directory contains utility scripts for development, testing, and maintenance.

## Scripts

### Testing & Validation
- **run_tests.py** - Main test runner for pytest suite
- **cleanup_test_transfers.py** - Clean up test data for pump transfers
- **verify_calculations_fixes.py** - Verify water balance calculation fixes

### Performance & Debugging
- **benchmark_performance.py** - Performance benchmarking tool
- **debug_import.py** - Debug Python import issues

### License Management
- **update_trial.py** - Update trial license information

## Usage

Run scripts from the project root using:
```powershell
.venv\Scripts\python scripts\<script_name>.py
```

Or from within the scripts directory:
```powershell
.venv\Scripts\python <script_name>.py
```

## Note

These scripts are for development/maintenance only and are NOT included in production builds.
