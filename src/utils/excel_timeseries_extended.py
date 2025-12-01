"""
Extended Excel Time Series Repository
Reads additional time-series data from Water_Balance_TimeSeries_Template.xlsx

Provides access to:
- Environmental data (rainfall, evaporation, pan coefficient)
- Storage facility volumes and flows
- Production parameters (concentrate, moisture, density)
- Consumption breakdown (dust, mining, domestic, irrigation, other)
- Seepage losses and gains
- Discharge records
"""

from datetime import date
from typing import Optional, Dict, List, Any
import pandas as pd
from pathlib import Path
from utils.app_logger import logger
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.persistent_cache import ExcelStorageCache


class ExcelTimeSeriesExtended:
    """Extended Excel repository for additional time-series parameters (Singleton with caching)"""
    
    _instance = None
    _lock = None
    
    def __new__(cls, file_path: str = None):
        """Singleton pattern - only one instance per file path"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, file_path: str = None):
        """Initialize with path to Water_Balance_TimeSeries_Template.xlsx"""
        if self._initialized:
            return  # Already initialized
            
        if file_path is None:
            # Get path from config or use default
            from utils.config_manager import config
            template_path = config.get('data_sources.template_excel_path', 'templates/Water_Balance_TimeSeries_Template.xlsx')
            base_dir = Path(__file__).parent.parent.parent
            file_path = base_dir / template_path if not Path(template_path).is_absolute() else Path(template_path)
        
        self.file_path = Path(file_path)
        self._environmental_df = None
        self._storage_df = None
        self._production_df = None
        self._consumption_df = None
        self._seepage_df = None
        self._discharge_df = None
        self._loaded = False
        self._excel_signature = None
        self._excel_path_str = str(self.file_path.resolve())
        
        # Cache for storage calculations to prevent recursive recalculation
        self._storage_cache = {}

        # Persistent on-disk cache (data/excel_cache.sqlite)
        data_dir = Path(__file__).parent.parent.parent / "data"
        cache_path = data_dir / "excel_cache.sqlite"
        self._persistent_cache = ExcelStorageCache(cache_path)
        self._initialized = True
    
    def _load(self):
        """Load all sheets from Excel file with parallel loading and timing"""
        if self._loaded:
            return
        
        # Validate file path strictly (avoid trying to read a directory -> PermissionError)
        if not self.file_path.exists() or not self.file_path.is_file():
            logger.error(f"❌ Application Inputs Excel file missing or invalid: {self.file_path}")
            if self.file_path.exists() and self.file_path.is_dir():
                logger.error("   The configured path points to a DIRECTORY, not an .xlsx file.")
            logger.error("   Open Settings → Data Sources and select the correct Excel workbook (.xlsx).")
            self._loaded = True
            return
        
        try:
            # compute excel signature (mtime:size) for invalidation
            try:
                st = self.file_path.stat()
                self._excel_signature = f"{int(st.st_mtime_ns)}:{int(st.st_size)}"
            except Exception:
                self._excel_signature = "unknown"
            total_start = time.perf_counter()
            logger.info(f"⏱️  Starting Excel load: {self.file_path.name}")
            
            # Define sheet loading tasks
            sheets_config = [
                ("Environmental", "Environmental", None),
                ("Storage_Facilities", "Storage_Facilities", 3),  # Skip 3 header rows
                ("Production", "Production", None),
                ("Consumption", "Consumption", None),
                ("Seepage_Losses", "Seepage_Losses", None),
                ("Discharge", "Discharge", None),
            ]
            
            def load_sheet(sheet_name, sheet_key, skiprows):
                """Load a single sheet with timing"""
                sheet_start = time.perf_counter()
                try:
                    if skiprows:
                        df = pd.read_excel(self.file_path, sheet_name=sheet_name, skiprows=skiprows)
                    else:
                        df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                    
                    elapsed = (time.perf_counter() - sheet_start) * 1000
                    logger.info(f"  ✓ {sheet_name}: {elapsed:.0f}ms ({len(df)} rows)")
                    return (sheet_key, df, None)
                except Exception as e:
                    elapsed = (time.perf_counter() - sheet_start) * 1000
                    logger.warning(f"  ✗ {sheet_name}: {elapsed:.0f}ms - {str(e)[:50]}")
                    return (sheet_key, None, e)
            
            # Load sheets in parallel using ThreadPoolExecutor
            results = {}
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {
                    executor.submit(load_sheet, name, key, skip): key 
                    for key, name, skip in sheets_config
                }
                
                for future in as_completed(futures):
                    sheet_key, df, error = future.result()
                    results[sheet_key] = df
            
            # Assign loaded dataframes
            self._environmental_df = results.get("Environmental")
            self._storage_df = results.get("Storage_Facilities")
            self._production_df = results.get("Production")
            self._consumption_df = results.get("Consumption")
            self._seepage_df = results.get("Seepage_Losses")
            self._discharge_df = results.get("Discharge")
            
            # Convert Date columns to datetime (fast operation)
            date_convert_start = time.perf_counter()
            for df_name, df in [
                ("Environmental", self._environmental_df),
                ("Storage", self._storage_df),
                ("Production", self._production_df),
                ("Consumption", self._consumption_df),
                ("Seepage", self._seepage_df),
                ("Discharge", self._discharge_df)
            ]:
                if df is not None and not df.empty and 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            date_elapsed = (time.perf_counter() - date_convert_start) * 1000
            logger.info(f"  ✓ Date conversion: {date_elapsed:.0f}ms")
            
            self._loaded = True
            total_elapsed = (time.perf_counter() - total_start) * 1000
            logger.info(f"✅ Excel loaded in {total_elapsed:.0f}ms")
            
        except PermissionError as perm_err:
            # Pandas trying to read a directory raises PermissionError on Windows
            total_elapsed = (time.perf_counter() - total_start) * 1000
            logger.error(f"❌ Excel load failed - invalid path (directory?): {self.file_path}")
            logger.error(f"   PermissionError: {perm_err}")
            logger.error("   Go to Settings → Data Sources and select a valid .xlsx file.")
            self._loaded = True
            # Don't show error dialog - let main_window handle it gracefully
        except Exception as e:
            total_elapsed = (time.perf_counter() - total_start) * 1000
            logger.error(f"❌ Excel load failed after {total_elapsed:.0f}ms: {e}")
            self._loaded = True
    
    def reload(self):
        """Force reload of Excel data (e.g., after file changes)"""
        logger.info("Reloading Excel data...")
        self._loaded = False
        self._storage_cache.clear()  # Clear calculation cache
        # Purge persistent cache only for this excel file (optional; sig mismatch also protects)
        try:
            self._persistent_cache.purge_for_excel(self._excel_path_str)
        except Exception:
            pass
        self._load()
        logger.info("Excel data reloaded successfully")
    
    # ==================== ENVIRONMENTAL DATA ====================
    
    def get_rainfall(self, target_date: date) -> Optional[float]:
        """Get rainfall in mm for the month. Returns None if not found."""
        self._load()
        if self._environmental_df is None or self._environmental_df.empty:
            return None
        
        # Filter by month and year
        mask = (self._environmental_df['Date'].dt.year == target_date.year) & \
               (self._environmental_df['Date'].dt.month == target_date.month)
        
        result = self._environmental_df[mask]
        if result.empty:
            return None
        
        rainfall = result.iloc[0]['Rainfall_mm']
        return float(rainfall) if pd.notna(rainfall) else None
    
    def get_custom_evaporation(self, target_date: date) -> Optional[float]:
        """Get custom evaporation in mm for the month. Returns None if not found."""
        self._load()
        if self._environmental_df is None or self._environmental_df.empty:
            return None
        
        mask = (self._environmental_df['Date'].dt.year == target_date.year) & \
               (self._environmental_df['Date'].dt.month == target_date.month)
        
        result = self._environmental_df[mask]
        if result.empty:
            return None
        
        evap = result.iloc[0]['Custom_Evaporation_mm']
        return float(evap) if pd.notna(evap) else None
    
    def get_pan_coefficient(self, target_date: date) -> Optional[float]:
        """Get pan coefficient for the month. Returns None if not found."""
        self._load()
        if self._environmental_df is None or self._environmental_df.empty:
            return None
        
        mask = (self._environmental_df['Date'].dt.year == target_date.year) & \
               (self._environmental_df['Date'].dt.month == target_date.month)
        
        result = self._environmental_df[mask]
        if result.empty:
            return None
        
        pan_coeff = result.iloc[0]['Pan_Coefficient']
        return float(pan_coeff) if pd.notna(pan_coeff) else None
    
    # ==================== STORAGE FACILITIES ====================
    
    def get_storage_data(self, facility_code: str, target_date: date, 
                        facility_capacity: Optional[float] = None,
                        facility_surface_area: Optional[float] = None,
                        db_manager: Optional[Any] = None) -> Optional[Dict]:
        """
        Get storage data for a facility for the month.
        
        NEW SIMPLIFIED FORMAT (Excel has only 4 columns):
          - Date, Facility_Code, Inflow_m3, Outflow_m3
        
        AUTO-CALCULATED:
          - Opening Volume: From previous month's closing (or DB fallback)
          - Closing Volume: Opening + (Inflow + Rainfall) - (Outflow + Evaporation)
          - Level %: Opening ÷ Capacity
          - Rainfall/Evaporation: Auto-added based on surface area
        
        This allows simplified Excel entry - just enter Inflow/Outflow, rest is computed!
        
        Returns dict with: opening_volume, closing_volume, level_percent, inflow, outflow,
                          rainfall_volume, evaporation, overflow, deficit, warnings
        Returns None if not found.
        """
        # Check in-memory cache first to prevent recursive recalculation
        cache_key = f"{facility_code}_{target_date.year}_{target_date.month}"
        if cache_key in self._storage_cache:
            return self._storage_cache[cache_key]

        # Check persistent cache (fast path for cold start)
        t0 = time.perf_counter()
        # Ensure excel signature is available before disk-cache lookup
        if not self._excel_signature:
            try:
                st = self.file_path.stat()
                self._excel_signature = f"{int(st.st_mtime_ns)}:{int(st.st_size)}"
            except Exception:
                self._excel_signature = "unknown"
        try:
            persisted = self._persistent_cache.get(
                self._excel_path_str,
                facility_code,
                int(target_date.year),
                int(target_date.month),
                self._excel_signature or "unknown",
            )
        except Exception:
            persisted = None
        if persisted:
            self._storage_cache[cache_key] = persisted
            logger.info(
                f"  ✓ Cache hit (disk) {facility_code} {target_date.year}-{target_date.month:02d}: {(time.perf_counter()-t0)*1000:.0f}ms"
            )
            return persisted
        
        self._load()
        if self._storage_df is None or self._storage_df.empty:
            return None
        
        mask = (self._storage_df['Date'].dt.year == target_date.year) & \
               (self._storage_df['Date'].dt.month == target_date.month) & \
               (self._storage_df['Facility_Code'] == facility_code)
        
        result = self._storage_df[mask]
        if result.empty:
            return None
        
        row = result.iloc[0]
        
        # Get manual inflow/outflow from Excel (simplified format - only these are required)
        inflow_manual = float(row['Inflow_m3']) if pd.notna(row['Inflow_m3']) else 0.0
        outflow_manual = float(row['Outflow_m3']) if pd.notna(row['Outflow_m3']) else 0.0
        
        # Auto-calculate opening volume from previous month's closing
        prev_month = target_date.replace(day=1) - pd.DateOffset(months=1)
        prev_data = self.get_storage_data(facility_code, prev_month.date(), facility_capacity, facility_surface_area, db_manager)
        if prev_data and prev_data.get('closing_volume') is not None:
            opening_volume = prev_data['closing_volume']
        else:
            # No previous month data - start from 10% of capacity (assumed baseline)
            # This represents typical operational minimum for ongoing operations
            # Avoids unrealistic "starting from empty" in mid-year calculations
            if facility_capacity and facility_capacity > 0:
                opening_volume = facility_capacity * 0.10
            else:
                opening_volume = 0.0
        
        # Add automatic environmental inflows/outflows if facility data available
        rainfall_volume = 0.0
        evaporation_volume = 0.0
        warnings = []
        
        if facility_surface_area and facility_surface_area > 0:
            # Get rainfall for this month
            rainfall_mm = self.get_rainfall(target_date)
            if rainfall_mm is not None and rainfall_mm > 0:
                rainfall_volume = (rainfall_mm / 1000.0) * facility_surface_area
            
            # Get evaporation for this month
            evaporation_mm = self.get_custom_evaporation(target_date)
            if evaporation_mm is not None and evaporation_mm > 0:
                evaporation_volume = (evaporation_mm / 1000.0) * facility_surface_area
        
        # Optional: Abstraction to plant (internal transfer)
        abstraction_to_plant = 0.0
        if 'Abstraction_m3' in self._storage_df.columns:
            try:
                abstraction_to_plant = float(row['Abstraction_m3']) if pd.notna(row['Abstraction_m3']) else 0.0
            except Exception:
                abstraction_to_plant = 0.0

        # Calculate total inflows and outflows (including environmental)
        total_inflow = inflow_manual + rainfall_volume
        # Outflows include manual outflow, evaporation, and abstraction to plant
        total_outflow = outflow_manual + evaporation_volume + abstraction_to_plant
        
        # Auto-calculate closing volume (always calculated now)
        overflow = 0.0
        deficit = 0.0
        
        # Calculate from mass balance: Closing = Opening + Inflow - Outflow
        closing_volume = opening_volume + total_inflow - total_outflow
        
        # Validate and clamp to realistic bounds
        if facility_capacity:
            if closing_volume > facility_capacity:
                overflow = closing_volume - facility_capacity
                closing_volume = facility_capacity
                warnings.append(f"OVERFLOW: Exceeds capacity by {overflow:,.0f} m³")
        
        if closing_volume < 0:
            deficit = abs(closing_volume)
            closing_volume = 0.0
            warnings.append(f"DEFICIT: Insufficient water, deficit of {deficit:,.0f} m³")
        
        # Validate realistic flows
        if facility_capacity:
            # Check if inflow exceeds capacity (unrealistic)
            if total_inflow > facility_capacity * 1.5:
                warnings.append(f"WARNING: Total inflow ({total_inflow:,.0f} m³) exceeds 150% of capacity")
            
            # Check if outflow exceeds opening volume (unrealistic)
            if opening_volume and total_outflow > opening_volume * 1.2:
                warnings.append(f"WARNING: Total outflow ({total_outflow:,.0f} m³) exceeds 120% of opening volume")
        
        # Auto-calculate level percentage
        level_percent = opening_volume / facility_capacity if facility_capacity and facility_capacity > 0 else 0.0
        
        result = {
            'opening_volume': opening_volume,
            'closing_volume': closing_volume,
            'level_percent': level_percent,
            'inflow_manual': inflow_manual,  # User-entered inflow
            'outflow_manual': outflow_manual,  # User-entered outflow
            'inflow_total': total_inflow,  # Including rainfall
            'outflow_total': total_outflow,  # Including evaporation + abstraction
            'rainfall_volume': rainfall_volume,  # Auto-calculated
            'evaporation_volume': evaporation_volume,  # Auto-calculated
            'abstraction_to_plant': abstraction_to_plant,  # Internal transfer
            'overflow': overflow,
            'deficit': deficit,
            'warnings': warnings,
        }
        
        # Cache the result to prevent recursive recalculation (memory + disk)
        cache_key = f"{facility_code}_{target_date.year}_{target_date.month}"
        self._storage_cache[cache_key] = result
        try:
            self._persistent_cache.set(
                self._excel_path_str,
                facility_code,
                int(target_date.year),
                int(target_date.month),
                self._excel_signature or "unknown",
                result,
            )
        except Exception:
            pass
        
        return result

    def get_total_abstraction_to_plant(self, target_date: date) -> float:
        """Sum Abstraction_m3 across facilities for the month (optional column)."""
        self._load()
        if self._storage_df is None or self._storage_df.empty:
            return 0.0
        if 'Abstraction_m3' not in self._storage_df.columns:
            return 0.0
        mask = (self._storage_df['Date'].dt.year == target_date.year) & \
               (self._storage_df['Date'].dt.month == target_date.month)
        dfm = self._storage_df[mask]
        if dfm.empty:
            return 0.0
        vals = dfm['Abstraction_m3']
        try:
            return float(vals.fillna(0.0).sum())
        except Exception:
            return 0.0
    
    def get_all_storage_data(self, target_date: date) -> List[Dict]:
        """
        Get storage data for all facilities for the month.
        Returns simplified data with only inflow/outflow from Excel.
        Use get_storage_data() for full auto-calculated values.
        """
        self._load()
        if self._storage_df is None or self._storage_df.empty:
            return []
        
        mask = (self._storage_df['Date'].dt.year == target_date.year) & \
               (self._storage_df['Date'].dt.month == target_date.month)
        
        results = self._storage_df[mask]
        if results.empty:
            return []
        
        storage_list = []
        for _, row in results.iterrows():
            storage_list.append({
                'facility_code': row['Facility_Code'],
                'inflow': float(row['Inflow_m3']) if pd.notna(row['Inflow_m3']) else 0.0,
                'outflow': float(row['Outflow_m3']) if pd.notna(row['Outflow_m3']) else 0.0,
            })
        
        return storage_list
    
    # ==================== PRODUCTION ====================
    
    def get_concentrate_produced(self, target_date: date) -> Optional[float]:
        """Get concentrate produced in tonnes for the month"""
        self._load()
        if self._production_df is None or self._production_df.empty:
            return None
        
        mask = (self._production_df['Date'].dt.year == target_date.year) & \
               (self._production_df['Date'].dt.month == target_date.month)
        
        result = self._production_df[mask]
        if result.empty:
            return None
        
        conc = result.iloc[0]['Concentrate_Produced_t']
        return float(conc) if pd.notna(conc) else None
    
    def get_concentrate_moisture(self, target_date: date) -> Optional[float]:
        """Get concentrate moisture as decimal (0.08 = 8%)"""
        self._load()
        if self._production_df is None or self._production_df.empty:
            return None
        
        mask = (self._production_df['Date'].dt.year == target_date.year) & \
               (self._production_df['Date'].dt.month == target_date.month)
        
        result = self._production_df[mask]
        if result.empty:
            return None
        
        moisture = result.iloc[0]['Concentrate_Moisture_Percent']
        return float(moisture) if pd.notna(moisture) else None
    
    def get_slurry_density(self, target_date: date) -> Optional[float]:
        """Get slurry density in t/m³"""
        self._load()
        if self._production_df is None or self._production_df.empty:
            return None
        
        mask = (self._production_df['Date'].dt.year == target_date.year) & \
               (self._production_df['Date'].dt.month == target_date.month)
        
        result = self._production_df[mask]
        if result.empty:
            return None
        
        density = result.iloc[0]['Slurry_Density_t_per_m3']
        return float(density) if pd.notna(density) else None
    
    def get_tailings_moisture(self, target_date: date) -> Optional[float]:
        """Get tailings moisture as decimal (0.35 = 35%)"""
        self._load()
        if self._production_df is None or self._production_df.empty:
            return None
        
        mask = (self._production_df['Date'].dt.year == target_date.year) & \
               (self._production_df['Date'].dt.month == target_date.month)
        
        result = self._production_df[mask]
        if result.empty:
            return None
        
        moisture = result.iloc[0]['Tailings_Moisture_Percent']
        return float(moisture) if pd.notna(moisture) else None
    
    # ==================== CONSUMPTION ====================
    
    def get_consumption(self, target_date: date) -> Optional[Dict]:
        """
        Get all consumption values for the month in m³.
        Returns dict with: dust_suppression, mining, domestic, irrigation, other
        All values default to 0.0 if None/missing.
        """
        self._load()
        if self._consumption_df is None or self._consumption_df.empty:
            return None
        
        mask = (self._consumption_df['Date'].dt.year == target_date.year) & \
               (self._consumption_df['Date'].dt.month == target_date.month)
        
        result = self._consumption_df[mask]
        if result.empty:
            return None
        
        row = result.iloc[0]
        return {
            'dust_suppression': float(row['Dust_Suppression_m3']) if pd.notna(row['Dust_Suppression_m3']) else 0.0,
            'mining': float(row['Mining_m3']) if pd.notna(row['Mining_m3']) else 0.0,
            'domestic': float(row['Domestic_m3']) if pd.notna(row['Domestic_m3']) else 0.0,
            'irrigation': float(row['Irrigation_m3']) if pd.notna(row['Irrigation_m3']) else 0.0,
            'other': float(row['Other_m3']) if pd.notna(row['Other_m3']) else 0.0,
        }
    
    # ==================== SEEPAGE ====================
    
    def get_seepage(self, target_date: date) -> Optional[Dict]:
        """
        Get seepage data for the month in m³.
        Returns dict with: seepage_loss, seepage_gain, unaccounted_losses
        """
        self._load()
        if self._seepage_df is None or self._seepage_df.empty:
            return None
        
        mask = (self._seepage_df['Date'].dt.year == target_date.year) & \
               (self._seepage_df['Date'].dt.month == target_date.month)
        
        result = self._seepage_df[mask]
        if result.empty:
            return None
        
        row = result.iloc[0]
        return {
            'seepage_loss': float(row['Seepage_Loss_m3']) if pd.notna(row['Seepage_Loss_m3']) else None,
            'seepage_gain': float(row['Seepage_Gain_m3']) if pd.notna(row['Seepage_Gain_m3']) else None,
            'unaccounted_losses': float(row['Unaccounted_Losses_m3']) if pd.notna(row['Unaccounted_Losses_m3']) else None,
        }
    
    # ==================== DISCHARGE ====================
    
    def get_discharge(self, target_date: date) -> List[Dict]:
        """
        Get all discharge records for the month.
        Returns list of dicts with: facility_code, volume, type, reason, approval_ref
        """
        self._load()
        if self._discharge_df is None or self._discharge_df.empty:
            return []
        
        mask = (self._discharge_df['Date'].dt.year == target_date.year) & \
               (self._discharge_df['Date'].dt.month == target_date.month)
        
        results = self._discharge_df[mask]
        if results.empty:
            return []
        
        discharge_list = []
        for _, row in results.iterrows():
            volume = row['Discharge_Volume_m3']
            if pd.notna(volume) and volume > 0:
                discharge_list.append({
                    'facility_code': row['Facility_Code'],
                    'volume': float(volume),
                    'type': row['Discharge_Type'] if pd.notna(row['Discharge_Type']) else 'Unknown',
                    'reason': row['Reason'] if pd.notna(row['Reason']) else '',
                    'approval_ref': row['Approval_Reference'] if pd.notna(row['Approval_Reference']) else '',
                })
        
        return discharge_list
    
    def get_total_discharge(self, target_date: date) -> float:
        """Get total discharge volume for the month in m³"""
        discharges = self.get_discharge(target_date)
        return sum(d['volume'] for d in discharges)


# Global instance
_extended_repo = None

def get_extended_excel_repo() -> ExcelTimeSeriesExtended:
    """Get the global extended Excel repository instance"""
    global _extended_repo
    if _extended_repo is None:
        _extended_repo = ExcelTimeSeriesExtended()
    return _extended_repo
