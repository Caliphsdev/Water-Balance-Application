"""
Water Balance Application Launcher
Optimized entry point for EXE deployment with external data management
"""

import sys
import os
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import messagebox

# Determine if running as EXE or script
if getattr(sys, 'frozen', False):
    # Running as compiled EXE
    APPLICATION_PATH = Path(sys.executable).parent
    IS_FROZEN = True
else:
    # Running as script
    APPLICATION_PATH = Path(__file__).parent.parent
    IS_FROZEN = False


def get_user_data_dir():
    """Get user data directory (AppData on Windows, ~/.local on Linux)"""
    # Check if running on Windows (even if built in WSL)
    if sys.platform == 'win32' or os.name == 'nt':
        # Windows: C:\Users\{User}\AppData\Local\WaterBalance
        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            # Fallback for older Windows or WSL cross-compilation
            appdata = os.path.join(os.environ.get('USERPROFILE', '~'), 'AppData', 'Local')
        user_dir = Path(appdata) / 'WaterBalance'
    else:
        # Linux/Mac: ~/.local/share/WaterBalance
        user_dir = Path.home() / '.local' / 'share' / 'WaterBalance'
    
    return user_dir


def initialize_user_environment():
    """Create user data directories and copy default config on first run"""
    user_dir = get_user_data_dir()
    
    # Create directory structure
    directories = [
        user_dir,
        user_dir / 'config',
        user_dir / 'data',
        user_dir / 'logs',
        user_dir / 'backups',
        user_dir / 'reports',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Check if config exists
    user_config = user_dir / 'config' / 'app_config.yaml'
    
    if not user_config.exists():
        # First run - copy default config
        if IS_FROZEN:
            # Get embedded default config
            default_config = APPLICATION_PATH / 'config' / 'app_config_default.yaml'
            if not default_config.exists():
                default_config = APPLICATION_PATH / '_internal' / 'config' / 'app_config_default.yaml'
        else:
            default_config = APPLICATION_PATH / 'config' / 'app_config.yaml'
        
        if default_config.exists():
            shutil.copy(default_config, user_config)
            print(f"✓ Created user config at: {user_config}")
        else:
            # Create minimal default config
            create_minimal_config(user_config)
    
    # Check if database exists
    user_db = user_dir / 'data' / 'water_balance.db'
    
    if not user_db.exists():
        # First run - initialize database
        print(f"✓ Database will be created at: {user_db}")
    
    return user_dir


def create_minimal_config(config_path):
    """Create minimal default configuration"""
    minimal_config = """app:
  company: Two Rivers Platinum (TRP)
  name: Water Balance Management System
  version: 1.0.0

branding:
  company_name: Two Rivers Platinum
  logo_path: ""

database:
  auto_backup: true
  backup_frequency: daily

data_sources:
  legacy_excel_path: ""
  template_excel_path: ""

constants:
  mining_water_rate: 1.43
  mean_annual_evaporation: 1950
  tsf_return_rate: 0.56
"""
    
    config_path.write_text(minimal_config)
    print(f"✓ Created minimal config at: {config_path}")


def show_first_run_dialog(user_dir):
    """Show welcome dialog on first run"""
    root = tk.Tk()
    root.withdraw()
    
    message = f"""Welcome to Water Balance Management System!

This is your first time running the application.

User data folder created at:
{user_dir}

📁 Folders created:
  • config/  - Your configuration settings
  • data/    - Database and application data  
  • logs/    - Application logs
  • backups/ - Automatic database backups
  • reports/ - Generated PDF reports

⚙️ Next Steps:
1. Application will launch
2. Go to Settings > Data Sources
3. Configure paths to your Excel files:
   • TRP Water Balance Excel (legacy data - optional)
   • Application Inputs Excel (required)

Click OK to continue..."""
    
    messagebox.showinfo("First Run Setup", message)
    root.destroy()


def main():
    """Main launcher entry point"""
    print("=" * 60)
    print("Water Balance Management System")
    print("=" * 60)
    print(f"Running as: {'EXE' if IS_FROZEN else 'Script'}")
    print(f"Application path: {APPLICATION_PATH}")
    
    # Initialize user environment
    user_dir = initialize_user_environment()
    print(f"User data directory: {user_dir}")
    
    # Check if first run
    config_file = user_dir / 'config' / 'app_config.yaml'
    is_first_run = not config_file.exists() or config_file.stat().st_size < 100
    
    if is_first_run:
        show_first_run_dialog(user_dir)
    
    # Update Python path to include src directory
    src_path = APPLICATION_PATH / 'src' if not IS_FROZEN else APPLICATION_PATH
    sys.path.insert(0, str(src_path))
    
    # Set environment variable for user data directory
    os.environ['WATERBALANCE_USER_DIR'] = str(user_dir)
    
    # Import and run main application
    try:
        if IS_FROZEN:
            # When frozen, modules are in _internal or root
            if (APPLICATION_PATH / '_internal').exists():
                sys.path.insert(0, str(APPLICATION_PATH / '_internal'))
        
        from main import main as app_main
        print("✓ Starting application...")
        app_main()
        
    except Exception as e:
        # Show error dialog
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Application Error",
            f"Failed to start application:\n\n{str(e)}\n\n"
            f"User data directory: {user_dir}\n"
            f"Check logs in: {user_dir / 'logs'}"
        )
        root.destroy()
        raise


if __name__ == '__main__':
    main()
