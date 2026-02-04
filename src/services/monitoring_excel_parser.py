"""
Monitoring Excel Parser - Config-Driven Column Mapping (COPIED FROM TKINTER)

Uses fuzzy matching to map Excel columns to logical field IDs.
Based on proven Tkinter implementation at Water-Balance-Application/src/services/monitoring_parsers.py

ONLY USED FOR: Borehole Monitoring and PCD Monitoring tabs
DOES NOT AFFECT: Static Levels tab (that code is separate and working)
"""
import pandas as pd
from typing import Dict, Optional, List
from difflib import SequenceMatcher
from pathlib import Path
import yaml

from core.app_logger import logger


def fuzzy_match_column(target: str, candidates: List[str], threshold: float = 0.85) -> Optional[str]:
    """
    Fuzzy match target column name against candidates (TKINTER PROVEN ALGORITHM).
    
    Args:
        target: Expected column name from config
        candidates: Actual column names from Excel
        threshold: Match threshold (0.0-1.0, default 0.85)
    
    Returns:
        Best matching candidate, or None if no match above threshold
    
    Example:
        >>> fuzzy_match_column("Calcium", ["Calcium^", "Chloride^"])
        "Calcium^"  # 92% match
    """
    if not candidates:
        return None
    
    best_match = None
    best_score = 0.0
    
    for candidate in candidates:
        # Case-insensitive comparison, ignore spaces
        score = SequenceMatcher(
            None,
            target.lower().replace(" ", ""),
            candidate.lower().replace(" ", "")
        ).ratio()
        
        if score > best_score:
            best_score = score
            best_match = candidate
    
    return best_match if best_score >= threshold else None


def load_monitoring_config() -> dict:
    """
    Load monitoring data sources config from YAML.
    
    Returns:
        Dict with data source definitions
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "monitoring_data_sources.yaml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('monitoring_data_sources', [])
    except Exception as e:
        logger.error(f"Failed to load monitoring config: {e}")
        return []


def find_columns_from_config(df: pd.DataFrame, column_defs: list, threshold: float = 0.85) -> Dict[str, Optional[str]]:
    """
    Map logical column IDs to Excel column names using fuzzy matching.
    
    Args:
        df: DataFrame from Excel
        column_defs: List of column definitions from YAML config
        threshold: Fuzzy matching threshold
    
    Returns:
        Dict: {logical_id → actual_excel_column_name}
    
    Example:
        Config: {"id": "calcium", "expected_names": ["Calcium", "Calcium (mg/l)"]}
        Excel columns: ["Calcium^", "Chloride^", "Magnesium^"]
        Returns: {"calcium": "Calcium^"}
    """
    mapping = {}
    excel_columns = [str(col) for col in df.columns.tolist()]  # Convert to strings, handle nan
    
    for col_def in column_defs:
        col_id = col_def['id']
        expected_names = col_def.get('expected_names', [])
        
        # Try each expected name
        matched = None
        for expected_name in expected_names:
            matched = fuzzy_match_column(expected_name, excel_columns, threshold)
            if matched:
                break
        
        mapping[col_id] = matched
        
        if matched:
            logger.debug(f"✓ Mapped '{col_id}' -> '{matched}'")
        elif col_def.get('required', False):
            logger.warning(f"✗ Required column '{col_id}' not found (tried: {expected_names})")
    
    return mapping


def parse_monitoring_excel(file_path: str, source_id: str) -> pd.DataFrame:
    """
    Parse monitoring Excel file using config-driven column mapping (MAIN ENTRY POINT).
    
    This replaces all complex header detection logic with simple fuzzy matching.
    
    Args:
        file_path: Path to Excel file
        source_id: Data source ID (e.g., "borehole_monitoring_v1", "pcd_monitoring_v1")
    
    Returns:
        DataFrame with mapped columns (logical IDs as column names)
    
    Example:
        df = parse_monitoring_excel("Boreholes Q3 2021.xls", "borehole_monitoring_v1")
        # Returns DataFrame with columns: borehole_id, measurement_date, aquifer_depth_m, etc.
    """
    try:
        # 1. Load config for this source
        all_sources = load_monitoring_config()
        source_config = next((s for s in all_sources if s['id'] == source_id), None)
        
        if not source_config:
            logger.error(f"No config found for source '{source_id}'")
            return pd.DataFrame()
        
        # 2. Read Excel normally (pandas auto-detects headers)
        df_raw = pd.read_excel(file_path)
        logger.info(f"Loaded {Path(file_path).name}: {len(df_raw)} rows, {len(df_raw.columns)} columns")
        logger.debug(f"Excel columns: {list(df_raw.columns)}")
        
        # 3. Find column mapping using fuzzy matching
        column_defs = source_config.get('columns', [])
        col_mapping = find_columns_from_config(df_raw, column_defs)
        
        # 4. Create new DataFrame with logical column names
        df_mapped = pd.DataFrame()
        
        for logical_id, excel_col in col_mapping.items():
            if excel_col and excel_col in df_raw.columns:
                df_mapped[logical_id] = df_raw[excel_col]
        
        # 5. Add source file metadata
        df_mapped['source_file'] = Path(file_path).name
        
        logger.info(f"[OK] Parsed {Path(file_path).name}: {len(df_mapped)} rows, {len(df_mapped.columns)} mapped columns")
        logger.debug(f"Mapped columns: {list(df_mapped.columns)}")
        
        return df_mapped
    
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}", exc_info=True)
        return pd.DataFrame()  # Return empty DataFrame on error
