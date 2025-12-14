"""
On-demand Excel-based flow volume loader for flow diagram segments.

Reads monthly flow volumes directly from Excel without database storage.
Each flow segment is registered in Excel and volumes are fetched on-demand.
"""

import sys
from pathlib import Path
from datetime import date
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from utils.app_logger import logger
from utils.config_manager import config


class FlowVolumeLoader:
    """Load flow volumes from Excel on-demand for specific months."""
    
    def __init__(self, excel_path: Optional[Path] = None):
        """
        Initialize the flow volume loader.
        
        Args:
            excel_path: Path to Excel file containing flow data.
                       If None, uses config value.
        """
        # Use provided path or fallback to config
        self._df_cache: Dict[str, pd.DataFrame] = {}  # Cache for each sheet
        self.excel_path = self._resolve_excel_path(excel_path)

    def _resolve_excel_path(self, override_path: Optional[Path]) -> Path:
        """Resolve the Excel path, honoring an override and the latest config value."""
        if override_path:
            return Path(override_path)

        # Reload config to pick up latest Settings changes
        try:
            config.load_config()
        except Exception:
            pass

        # Prefer explicit timeseries path; fall back to template_excel_path if set
        excel_config_path = config.get(
            'data_sources.timeseries_excel_path',
            config.get('data_sources.template_excel_path',
                       'test_templates/Water_Balance_TimeSeries_Template.xlsx')
        )

        cfg_path = Path(excel_config_path)
        if cfg_path.is_absolute():
            return cfg_path

        base_dir = Path(__file__).resolve().parents[2]
        return base_dir / cfg_path
    
    def _load_sheet(self, sheet_name: str) -> pd.DataFrame:
        """Load a sheet from Excel with caching."""
        # Refresh path from config so Settings changes are picked up without restart
        new_path = self._resolve_excel_path(None)
        if new_path != self.excel_path:
            self.excel_path = new_path
            self.clear_cache()  # Path changed, drop cached sheets

        if sheet_name in self._df_cache:
            return self._df_cache[sheet_name]
        
        if not self.excel_path.exists():
            logger.error(f"❌ Excel file not found: {self.excel_path}")
            return pd.DataFrame()
        
        try:
            # Read the sheet: Try header=2 first (row 3 as data), then header=0
            df = None
            for header_row in [2, 0]:
                try:
                    df = pd.read_excel(
                        self.excel_path,
                        sheet_name=sheet_name,
                        header=header_row,
                        engine='openpyxl'
                    )
                    # Check if we got valid column names
                    if 'Date' in df.columns or 'Year' in df.columns:
                        break
                except:
                    continue
            
            if df is None or df.empty:
                logger.error(f"❌ Could not read sheet '{sheet_name}'")
                return pd.DataFrame()
            
            # Ensure we have Year and Month columns
            if 'Date' in df.columns and 'Year' not in df.columns:
                # Convert Date column to datetime and extract Year/Month
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
                df['Year'] = df['Date'].apply(lambda d: d.year if pd.notna(d) else None)
                df['Month'] = df['Date'].apply(lambda d: d.month if pd.notna(d) else None)
            elif 'Year' in df.columns and 'Month' in df.columns:
                # Already have Year and Month columns - ensure they're numeric
                df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
                df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
            else:
                logger.error(f"❌ Sheet '{sheet_name}' missing Date or Year/Month columns")
                return pd.DataFrame()
            
            self._df_cache[sheet_name] = df
            logger.info(f"📥 Loaded sheet '{sheet_name}': {len(df)} rows, {len(df.columns)} columns")
            return df
        
        except Exception as e:
            logger.error(f"❌ Error loading sheet '{sheet_name}': {e}")
            return pd.DataFrame()
    
    def get_monthly_volume(self, 
                          area_code: str,
                          flow_id: str,
                          year: int,
                          month: int) -> Optional[float]:
        """
        Get monthly volume for a specific flow.
        
        Args:
            area_code: Mine area code (e.g., 'UG2N', 'MERN', 'MERENSKY_NORTH')
            flow_id: Flow identifier/name (matches column in Excel)
            year: Year
            month: Month (1-12)
        
        Returns:
            Volume in m³, or None if not found
        """
        sheet_name = f"Flows_{area_code}"
        df = self._load_sheet(sheet_name)
        
        if df.empty:
            logger.debug(f"⚠️ No data for sheet '{sheet_name}'")
            return None
        
        # Find row matching year and month
        matching_rows = df[(df['Year'] == year) & (df['Month'] == month)]
        
        if matching_rows.empty:
            logger.debug(f"⚠️ No data for {area_code}/{flow_id} in {year}-{month:02d}")
            return None
        
        row = matching_rows.iloc[0]
        
        # Get volume from column named after flow_id
        if flow_id not in row.index:
            logger.debug(f"⚠️ Column '{flow_id}' not found in sheet '{sheet_name}'")
            return None
        
        try:
            volume = float(row[flow_id])
            # Allow negative values; only skip NaN
            if pd.isna(volume):
                return None
            return volume
        except (TypeError, ValueError):
            logger.debug(f"⚠️ Invalid volume for {flow_id}: {row[flow_id]}")
            return None
    
    def get_all_volumes_for_month(self,
                                  area_code: str,
                                  year: int,
                                  month: int) -> Dict[str, float]:
        """
        Get all flow volumes for an area for a specific month.
        
        Args:
            area_code: Mine area code
            year: Year
            month: Month (1-12)
        
        Returns:
            Dictionary mapping flow_id -> volume (m³)
        """
        sheet_name = f"Flows_{area_code}"
        df = self._load_sheet(sheet_name)
        
        if df.empty:
            return {}
        
        # Find row matching year and month
        matching_rows = df[(df['Year'] == year) & (df['Month'] == month)]
        
        if matching_rows.empty:
            return {}
        
        row = matching_rows.iloc[0]
        volumes = {}
        
        # Extract all numeric columns (skip Date, Year, Month)
        skip_cols = {'Date', 'Year', 'Month'}
        for col in df.columns:
            if col not in skip_cols:
                try:
                    vol = float(row[col])
                    # Allow negative values; only skip NaN
                    if not pd.isna(vol):
                        volumes[col] = vol
                except (TypeError, ValueError):
                    pass
        
        logger.info(f"📊 Loaded {len(volumes)} flows for {area_code} ({year}-{month:02d})")
        return volumes
    
    def update_diagram_edges(self,
                            area_data: Dict,
                            area_code: str,
                            year: int,
                            month: int) -> Dict:
        """
        Update all edges in diagram with volumes from Excel.
        
        Args:
            area_data: Diagram JSON data with nodes and edges
            area_code: Mine area code (default sheet to load)
            year: Year
            month: Month
        
        Returns:
            Updated area_data with volumes refreshed
        """
        # Collect all unique sheets referenced by edges
        edges = area_data.get('edges', [])
        sheets_to_load = set()
        
        for edge in edges:
            excel_mapping = edge.get('excel_mapping', {})
            if excel_mapping.get('enabled'):
                sheet = excel_mapping.get('sheet', f'Flows_{area_code}')
                sheets_to_load.add(sheet)
        
        # Load volumes from all required sheets
        all_volumes = {}
        for sheet in sheets_to_load:
            # Extract area code from sheet name (e.g., Flows_UG2N -> UG2N)
            sheet_area_code = sheet.replace('Flows_', '') if sheet.startswith('Flows_') else area_code
            volumes = self.get_all_volumes_for_month(sheet_area_code, year, month)
            all_volumes.update(volumes)
        
        # Update edges with volumes
        updated_count = 0
        for edge in edges:
            excel_mapping = edge.get('excel_mapping', {})
            if not excel_mapping.get('enabled'):
                continue
            
            flow_id = excel_mapping.get('column')
            if not flow_id or flow_id not in all_volumes:
                continue
            
            # Update edge with new volume
            new_volume = all_volumes[flow_id]
            edge['volume'] = new_volume
            edge['label'] = f"{new_volume:,.0f}"
            updated_count += 1
            
            logger.debug(f"✅ Updated {edge.get('from')} → {edge.get('to')}: {new_volume:,.0f} m³")
        
        logger.info(f"📈 Updated {updated_count} flow volumes from Excel (sheets: {', '.join(sheets_to_load)})")
        return area_data
    
    def get_available_months(self, area_code: str) -> List[Tuple[int, int]]:
        """
        Get list of available months (year, month) for an area.
        
        Returns:
            List of (year, month) tuples
        """
        sheet_name = f"Flows_{area_code}"
        df = self._load_sheet(sheet_name)
        
        if df.empty or 'Year' not in df.columns or 'Month' not in df.columns:
            return []
        
        # Remove rows with missing Year/Month
        valid = df.dropna(subset=['Year', 'Month'])
        
        # Get unique (year, month) pairs
        months = valid[['Year', 'Month']].drop_duplicates().values.tolist()
        months = [(int(y), int(m)) for y, m in months]
        months.sort()
        
        return months
    
    def clear_cache(self):
        """Clear the sheet cache to force reload from Excel."""
        self._df_cache.clear()
        logger.info("🧹 Flow volume cache cleared")

    def list_sheets(self) -> List[str]:
        """List available sheet names in the Excel workbook."""
        if not self.excel_path.exists():
            return []
        try:
            xls = pd.ExcelFile(self.excel_path, engine='openpyxl')
            return list(xls.sheet_names)
        except Exception:
            return []

    def list_sheet_columns(self, sheet_name: str) -> List[str]:
        """List column names for a given sheet (excluding Date/Year/Month)."""
        df = self._load_sheet(sheet_name)
        if df.empty:
            return []
        skip = {'Date', 'Year', 'Month'}
        return [c for c in df.columns if c not in skip]


# Singleton instance
_loader_instance: Optional[FlowVolumeLoader] = None


def get_flow_volume_loader() -> FlowVolumeLoader:
    """Get singleton instance of flow volume loader."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = FlowVolumeLoader()
    return _loader_instance


def reset_flow_volume_loader():
    """Reset singleton instance to force path reload from config."""
    global _loader_instance
    _loader_instance = None
    logger.info("🔄 Flow volume loader reset")
