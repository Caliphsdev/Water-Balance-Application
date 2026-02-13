"""
Calculation Constants Loader (CONFIGURABLE PARAMETERS).

Loads calculation constants from database and configuration.
Provides defaults when values are not configured.

Constants include:
- Evaporation pan coefficient
- Seepage rates (lined vs unlined)
- Default moisture percentages
- License limits
- Conversion factors

Why centralized:
1. Single source of truth for all calculation parameters
2. Easy to update without changing code
3. Supports per-site customization
4. Auditable (track what constants were used)
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class CalculationConstants:
    """Container for all calculation constants.
    
    Groups related constants for easier access.
    All values have sensible defaults for initial setup.
    """
    
    # Evaporation constants
    evap_pan_coefficient: float = 0.7  # Pan to lake evaporation conversion
    evap_temperature_factor: float = 1.0  # Temperature adjustment (1.0 = none)
    
    # Seepage rates (% of volume per month)
    seepage_rate_lined_pct: float = 0.1  # HDPE/clay lined dams
    seepage_rate_unlined_pct: float = 0.5  # Natural soil (unlined)
    
    # TSF (Tailings Storage Facility) constants
    tsf_return_water_pct: float = 36.0  # % of plant water returning from TSF
    tailings_moisture_pct: float = 45.0  # % moisture retained in tailings (fallback)
    tailings_solids_density: float = 2.7  # Ore/solids density (t/m³) for moisture calc from slurry density
    
    # Ore processing constants
    ore_moisture_pct: float = 3.5  # % moisture in mined ore
    ore_density_tonnes_per_m3: float = 2.7  # Ore density
    product_moisture_pct: float = 8.0  # % moisture in concentrate/product
    recovery_rate_pct: float = 2.0  # % of ore mass recovered as product
    
    # Dust suppression
    dust_suppression_rate_l_per_t: float = 1.0  # Litres water per tonne ore
    
    # Mining consumption (underground operations)
    mining_water_rate_m3_per_t: float = 0.05  # m³ water per tonne ore mined
    # Typical breakdown: drilling 40%, cooling 30%, dust 20%, other 10%
    
    # Domestic/sanitation consumption
    domestic_consumption_l_per_person_day: float = 150.0  # L per person per day
    # WHO minimum 50 L, SA urban 200+ L, mine camps typically 100-200 L
    
    # License limits (m³/year) - site specific
    abstraction_license_annual_m3: Optional[float] = None
    discharge_license_annual_m3: Optional[float] = None
    
    # Pump transfer thresholds
    pump_start_level_pct: float = 70.0  # Start pumping at this % full
    pump_increment_pct: float = 5.0  # Transfer 5% per operation
    
    # Data quality thresholds
    balance_error_threshold_pct: float = 5.0  # Error < 5% = acceptable
    stale_data_warning_days: int = 30  # Warn if data older than this
    
    # Feature toggles (can be enabled/disabled in settings)
    runoff_enabled: bool = False  # Enable catchment runoff calculation
    dewatering_enabled: bool = True  # Enable underground dewatering as inflow
    
    # Outflow component toggles
    # Mining consumption: Set to False if underground water is recaptured as dewatering
    # (avoids double-counting: once as outflow, once as dewatering inflow)
    mining_consumption_enabled: bool = False  # Default OFF - water returns as dewatering
    
    # Domestic consumption: Set to False if sewage is treated and recycled on-site
    domestic_consumption_enabled: bool = True  # Default ON - typically exits system
    
    # Runoff coefficients by surface type
    runoff_coefficients: Dict[str, float] = field(default_factory=lambda: {
        'open_water': 1.0,
        'bare_tailings': 0.60,
        'compacted_roads': 0.75,
        'vegetated': 0.30,
        'natural_bush': 0.20,
    })


class ConstantsLoader:
    """Loads and manages calculation constants.
    
    Sources (in priority order):
    1. Database (system_constants table)
    2. Configuration file (app_config.yaml)
    3. Default values
    
    Caches loaded constants for performance.
    Call refresh() to reload from sources.
    """
    
    _instance: Optional['ConstantsLoader'] = None
    _constants: Optional[CalculationConstants] = None
    _db_overrides: set[str] = set()
    
    def __new__(cls):
        """Singleton pattern for constant loader."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize constants loader."""
        if self._constants is None:
            self._load_constants()
    
    def _load_constants(self) -> None:
        """Load constants from database and config.
        
        Priority:
        1. Database values (most specific)
        2. Config file values
        3. Defaults (least specific)
        """
        self._constants = CalculationConstants()
        self._db_overrides = set()
        
        # Try to load from database
        try:
            self._load_from_database()
        except Exception as e:
            logger.warning(f"Could not load constants from database: {e}")
        
        # Try to load from config (overrides defaults, not DB)
        try:
            self._load_from_config()
        except Exception as e:
            logger.warning(f"Could not load constants from config: {e}")
        
        logger.debug("Calculation constants loaded")
    
    def _load_from_database(self) -> None:
        """Load constants from system_constants table.

        Supports both schemas:
        - With `active` column (newer admin schema)
        - Without `active` column (legacy/local schema)
        """
        try:
            from database.db_manager import DatabaseManager

            db = DatabaseManager()
            conn = db.get_connection()
            try:
                columns = {
                    str(row["name"]).lower()
                    for row in conn.execute("PRAGMA table_info(system_constants)").fetchall()
                }
                has_active = "active" in columns
                has_unit = "unit" in columns

                select_fields = "constant_key, constant_value"
                if has_unit:
                    select_fields += ", unit"

                sql = f"SELECT {select_fields} FROM system_constants"
                if has_active:
                    sql += " WHERE active = 1"

                rows = conn.execute(sql).fetchall()
                for row in rows:
                    key = row["constant_key"]
                    value = row["constant_value"]
                    unit = row["unit"] if has_unit else None
                    applied_attr = self._apply_constant(key, value, unit=unit)
                    if applied_attr:
                        self._db_overrides.add(applied_attr)
            finally:
                conn.close()

        except Exception as e:
            logger.debug(f"Database constants not available: {e}")
    
    def _load_from_config(self) -> None:
        """Load constants from app_config.yaml."""
        try:
            from core.config_manager import config
            
            calc_config = config.get('calculation', {})
            if isinstance(calc_config, dict):
                for key, value in calc_config.items():
                    attr_name = self._resolve_attr_name(key)
                    # Database values are authoritative when both sources define the same key.
                    if attr_name in self._db_overrides:
                        continue
                    self._apply_constant(key, value)
                    
        except Exception as e:
            logger.debug(f"Config constants not available: {e}")
    
    def _resolve_attr_name(self, key: str) -> str:
        """Resolve external key aliases to CalculationConstants attribute names."""
        key_mapping = {
            # Evaporation
            'evap_pan_coefficient': 'evap_pan_coefficient',
            'pan_coefficient': 'evap_pan_coefficient',
            'EVAP_PAN_COEFF': 'evap_pan_coefficient',
            # Seepage
            'seepage_rate_lined': 'seepage_rate_lined_pct',
            'lined_seepage_rate_pct': 'seepage_rate_lined_pct',
            'seepage_rate_unlined': 'seepage_rate_unlined_pct',
            'unlined_seepage_rate_pct': 'seepage_rate_unlined_pct',
            # TSF
            'tsf_return_pct': 'tsf_return_water_pct',
            'tsf_return_water_pct': 'tsf_return_water_pct',
            'tailings_moisture_pct': 'tailings_moisture_pct',
            # Ore processing
            'ore_moisture_pct': 'ore_moisture_pct',
            'product_moisture_pct': 'product_moisture_pct',
            'recovery_rate_pct': 'recovery_rate_pct',
            # Dust suppression
            'dust_suppression_rate': 'dust_suppression_rate_l_per_t',
            'dust_suppression_rate_l_per_t': 'dust_suppression_rate_l_per_t',
            # Mining/Domestic
            'mining_water_rate': 'mining_water_rate_m3_per_t',
            'mining_water_rate_m3_per_t': 'mining_water_rate_m3_per_t',
            'domestic_consumption_rate': 'domestic_consumption_l_per_person_day',
            'domestic_consumption_l_per_person_day': 'domestic_consumption_l_per_person_day',
            # Pump transfer
            'pump_start_level': 'pump_start_level_pct',
            'pump_start_level_pct': 'pump_start_level_pct',
            # Thresholds
            'balance_error_threshold': 'balance_error_threshold_pct',
            'abstraction_license_m3': 'abstraction_license_annual_m3',
            # Feature toggles (can be set in config or database)
            'runoff_enabled': 'runoff_enabled',
            'enable_runoff': 'runoff_enabled',
            'dewatering_enabled': 'dewatering_enabled',
            'enable_dewatering': 'dewatering_enabled',
            # Outflow component toggles
            'mining_consumption_enabled': 'mining_consumption_enabled',
            'enable_mining_consumption': 'mining_consumption_enabled',
            'domestic_consumption_enabled': 'domestic_consumption_enabled',
            'enable_domestic_consumption': 'domestic_consumption_enabled',
        }
        return key_mapping.get(key, key)

    def _apply_constant(self, key: str, value: Any, unit: Any = None) -> Optional[str]:
        """Apply a constant value to the constants object.
        
        Maps database/config keys to CalculationConstants attributes.
        
        Args:
            key: Constant key (e.g., 'evap_pan_coefficient')
            value: Constant value (will be type-converted)
        """
        attr_name = self._resolve_attr_name(key)

        # Backward-compatible unit normalization:
        # Dust suppression is consumed by the engine as L/t. If DB is configured as m3/t,
        # convert here so runtime formula stays consistent.
        if attr_name == "dust_suppression_rate_l_per_t" and unit is not None:
            unit_text = str(unit).strip().lower()
            if unit_text in {"m3/t", "m^3/t", "m³/t", "cum/t"}:
                try:
                    value = float(value) * 1000.0
                    logger.info(
                        "Converted dust_suppression_rate from m3/t to L/t for calculation runtime."
                    )
                except Exception:
                    pass
        
        if hasattr(self._constants, attr_name):
            try:
                # Get expected type from current value
                current = getattr(self._constants, attr_name)
                if current is not None:
                    # Convert to same type as the default
                    current_type = type(current)
                    if current_type == bool:
                        # Handle various boolean representations
                        if isinstance(value, str):
                            value = value.lower() in ('true', '1', 'yes', 'on', 'enabled')
                        elif isinstance(value, (int, float)):
                            value = bool(value)
                        else:
                            value = bool(value)
                    elif current_type == float:
                        value = float(value)
                    elif current_type == int:
                        value = int(value)
                
                setattr(self._constants, attr_name, value)
                logger.debug(f"Loaded constant {attr_name}={value}")
                return attr_name
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid constant value for {key}: {value} ({e})")
        return None
    
    @property
    def constants(self) -> CalculationConstants:
        """Get the loaded constants object."""
        if self._constants is None:
            self._load_constants()
        return self._constants
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific constant by key.
        
        Args:
            key: Constant attribute name
            default: Value to return if not found
        
        Returns:
            Constant value or default
        """
        return getattr(self.constants, key, default)
    
    def refresh(self) -> None:
        """Reload constants from all sources.
        
        Call after database or config updates.
        """
        self._constants = None
        self._load_constants()
    
    def as_dict(self) -> Dict[str, Any]:
        """Export all constants as a dictionary.
        
        Useful for auditing and debugging.
        """
        from dataclasses import asdict
        return asdict(self.constants)


# Singleton instance getter
def get_constants() -> CalculationConstants:
    """Get the calculation constants singleton.
    
    Usage:
        from services.calculation.constants import get_constants
        
        constants = get_constants()
        pan_coeff = constants.evap_pan_coefficient
    """
    return ConstantsLoader().constants


def get_constant(key: str, default: Any = None) -> Any:
    """Get a specific calculation constant.
    
    Usage:
        from services.calculation.constants import get_constant
        
        pan_coeff = get_constant('evap_pan_coefficient', 0.7)
    """
    return ConstantsLoader().get(key, default)
