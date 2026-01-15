"""
Configuration Manager
Loads and manages application configuration from YAML files
"""

import yaml
import os
from pathlib import Path
from typing import Any, Dict


class ConfigManager:
    """Singleton configuration manager for application settings"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: str = None):
        """Load configuration from YAML file"""
        if config_path is None:
            # Check for user data directory (set by launcher for EXE)
            user_dir = os.environ.get('WATERBALANCE_USER_DIR')
            
            if user_dir:
                # EXE mode: use AppData/Local/WaterBalance/config
                config_path = Path(user_dir) / "config" / "app_config.yaml"
            else:
                # Development mode: use project config
                base_dir = Path(__file__).parent.parent.parent
                config_path = base_dir / "config" / "app_config.yaml"
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            self._config = self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            self._config = self._get_default_config()
        
        # Store config path for saving
        self._config_path = config_path
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('fonts.heading_large.size')
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation
        Example: config.set('data_sources.template_path', '/path/to/file.xlsx')
        """
        keys = key_path.split('.')
        current = self._config
        
        # Navigate to parent, creating dicts as needed
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        self._save_config()
    
    def get_font(self, font_type: str) -> tuple:
        """
        Get font configuration as tuple (family, size, weight)
        Example: config.get_font('heading_large')
        """
        font_config = self.get(f'fonts.{font_type}')
        if font_config:
            return (
                font_config.get('family', 'Segoe UI'),
                font_config.get('size', 10),
                font_config.get('weight', 'normal')
            )
        return ('Segoe UI', 10, 'normal')
    
    def get_color(self, color_name: str) -> str:
        """Get color value from configuration"""
        return self.get(f'colors.{color_name}', '#000000')
    
    def get_logo_path(self) -> str:
        """Get current logo file path"""
        return self.get('branding.logo_path', '')
    
    def set_logo_path(self, path: str):
        """Set logo path and save to config"""
        if 'branding' not in self._config:
            self._config['branding'] = {}
        self._config['branding']['logo_path'] = path
        self._save_config()
    
    def get_company_name(self) -> str:
        """Get company name for reports"""
        return self.get('branding.company_name', 'Water Balance Management')
    
    def set_company_name(self, name: str):
        """Set company name"""
        if 'branding' not in self._config:
            self._config['branding'] = {}
        self._config['branding']['company_name'] = name
        self._save_config()
    
    def _save_config(self):
        """Save current config to file"""
        # Use stored config path (set during load_config)
        config_path = getattr(self, '_config_path', None)
        
        if config_path is None:
            # Fallback to determining path
            user_dir = os.environ.get('WATERBALANCE_USER_DIR')
            if user_dir:
                config_path = Path(user_dir) / "config" / "app_config.yaml"
            else:
                base_dir = Path(__file__).parent.parent.parent
                config_path = base_dir / "config" / "app_config.yaml"
        
        try:
            # Ensure directory exists
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            print(f'Error saving config: {e}')

    # ============ User Session ============
    def get_current_user(self) -> str:
        """Return current logged-in username (or 'system' if none)"""
        return self.get('session.current_user', 'system')

    def set_current_user(self, username: str):
        """Set current logged-in user"""
        if 'session' not in self._config:
            self._config['session'] = {}
        self._config['session']['current_user'] = username
        self._save_config()

    def clear_current_user(self):
        """Clear current user session"""
        if 'session' in self._config and 'current_user' in self._config['session']:
            self._config['session']['current_user'] = 'system'
            self._save_config()
    
    def _get_default_config(self) -> Dict:
        """Return minimal default configuration if file loading fails"""
        # Provide a richer default so the UI is usable even when the
        # external config file is missing on first run (prevents black screen).
        return {
            'app': {
                'name': 'Water Balance System',
                'version': '1.0.0'
            },
            'window': {
                'title': 'Water Balance',
                'geometry': '1400x900',
                'theme': 'arc',
                'min_width': 1200,
                'min_height': 700,
                'auto_scale': True,
                'scale_factor': 1.0
            },
            'ui': {
                'toolbar_height': 56,
                'sidebar_width': 240
            },
            'fonts': {
                'body': {'family': 'Segoe UI', 'size': 11, 'weight': 'normal'},
                'body_bold': {'family': 'Segoe UI', 'size': 11, 'weight': 'bold'},
                'heading_large': {'family': 'Segoe UI', 'size': 20, 'weight': 'bold'},
                'heading_medium': {'family': 'Segoe UI', 'size': 16, 'weight': 'bold'},
                'heading_small': {'family': 'Segoe UI', 'size': 13, 'weight': 'bold'}
            },
            'colors': {
                'primary': '#1976D2',
                'primary_light': '#63A4FF',
                'primary_dark': '#004BA0',
                'bg_main': '#F5F7FA',
                'bg_header': '#0D47A1',
                'bg_sidebar': '#1E2A38',
                'text_primary': '#212121',
                'text_light': '#FFFFFF',
                'divider': '#E0E0E0'
            }
        }
    
    @property
    def app_name(self) -> str:
        return self.get('app.name', 'Water Balance System')
    
    @property
    def app_version(self) -> str:
        return self.get('app.version', '1.0.0')
    
    @property
    def window_title(self) -> str:
        return self.get('window.title', 'Water Balance')
    
    @property
    def window_geometry(self) -> str:
        return self.get('window.geometry', '1400x900')
    
    @property
    def theme(self) -> str:
        return self.get('window.theme', 'arc')


# Global configuration instance
config = ConfigManager()
