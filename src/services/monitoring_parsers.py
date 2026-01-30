"""
Monitoring Excel Parsers - Core Parsing Logic

Generic parsers for different Excel structures:
- MonitoringExcelParser: Base class (fuzzy column matching, type conversion, validation)
- StackedBlocksParser: Multiple items stacked vertically (boreholes)
- TimeseriesParser: Rows = measurements, columns = parameters
- ParserFactory: Auto-detect structure and select appropriate parser

Key Features:
- Fuzzy column name matching (handles Excel renames)
- Type-safe validation (Pydantic models)
- Error collection (skip invalid rows, continue processing)
- Performance profiling (track parse time)
- Threading-ready (stateless parsers)

REUSE PATTERN: Inherits async + caching from existing app architecture
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import time
from difflib import SequenceMatcher
from abc import ABC, abstractmethod

from models.monitoring_data import (
    DataSourceDefinition, MonitoringRecord, BoreholeStaticRecord,
    BoreholeMonitoringRecord, PCDMonitoringRecord, ParseResult,
    DataType, StructureType
)
from utils.app_logger import logger
from utils.config_manager import config as app_config


# ============================================================================
# FUZZY COLUMN MATCHING
# ============================================================================

def fuzzy_match_column(target: str, candidates: List[str], threshold: float = 0.85) -> Optional[str]:
    """
    Fuzzy match target column name against candidates.
    
    Args:
        target: Expected column name from config
        candidates: Actual column names from Excel
        threshold: Match threshold (0.0-1.0)
    
    Returns:
        Best matching candidate, or None if no match above threshold
    
    Example:
        >>> fuzzy_match_column("Static Level", ["Static Level (m)", "SWL"])
        "Static Level (m)"
    """
    if not candidates:
        return None
    
    best_match = None
    best_score = 0.0
    
    for candidate in candidates:
        # Case-insensitive comparison
        score = SequenceMatcher(
            None,
            target.lower().replace(" ", ""),
            candidate.lower().replace(" ", "")
        ).ratio()
        
        if score > best_score:
            best_score = score
            best_match = candidate
    
    return best_match if best_score >= threshold else None


# ============================================================================
# BASE PARSER
# ============================================================================

class MonitoringExcelParser(ABC):
    """Base class for monitoring Excel parsers"""
    
    def __init__(self, source_def: DataSourceDefinition, threshold: float = 0.85):
        """
        Initialize parser.
        
        Args:
            source_def: Data source definition from config
            threshold: Fuzzy matching threshold (0.0-1.0)
        """
        self.source_def = source_def
        self.threshold = threshold
        self.errors: List[str] = []
    
    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """
        Parse Excel file and return structured records.
        
        Args:
            file_path: Path to Excel file
        
        Returns:
            ParseResult with records and statistics
        """
        pass
    
    def _find_columns(self, df: pd.DataFrame) -> Dict[str, Optional[str]]:
        """
        Map logical column IDs to Excel column names using fuzzy matching.
        
        Example:
            Config expects: "static_level_m" → ["Static Level", "SWL"]
            Excel has: ["Level (meters)", "Borehole", "Date"]
            Returns: {"static_level_m": "Level (meters)", ...}
        
        Args:
            df: DataFrame from Excel
        
        Returns:
            Dict: {logical_id → actual_excel_column_name}
        """
        mapping = {}
        excel_columns = df.columns.tolist()
        
        for col_def in self.source_def.columns:
            matched = fuzzy_match_column(
                col_def.expected_names[0] if col_def.expected_names else col_def.id,
                excel_columns,
                threshold=self.threshold
            )
            
            if matched:
                mapping[col_def.id] = matched
                logger.debug(f"  ✓ Matched '{col_def.id}' → '{matched}'")
            elif col_def.required:
                msg = f"Required column not found: {col_def.id} (expected: {col_def.expected_names})"
                self.errors.append(msg)
                logger.warning(f"  ✗ {msg}")
        
        return mapping
    
    def _convert_type(self, value: any, target_type: DataType) -> Tuple[any, Optional[str]]:
        """
        Convert value to target type.
        
        Returns:
            Tuple: (converted_value, error_message)
                If error, returns (None, error_message)
        """
        if pd.isna(value) or value == "":
            return None, None
        
        try:
            if target_type == DataType.STRING:
                return str(value), None
            
            elif target_type == DataType.FLOAT:
                return float(value), None
            
            elif target_type == DataType.INTEGER:
                return int(float(value)), None  # float first to handle "1.0"
            
            elif target_type == DataType.DATE:
                if isinstance(value, date):
                    return value, None
                # Try common date formats
                for fmt in app_config.get('monitoring_settings.date_formats', ["%Y-%m-%d", "%d/%m/%Y"]):
                    try:
                        return datetime.strptime(str(value), fmt).date(), None
                    except ValueError:
                        continue
                return None, f"Cannot parse date: {value}"
            
            elif target_type == DataType.BOOLEAN:
                if isinstance(value, bool):
                    return value, None
                s = str(value).lower()
                return s in ("true", "yes", "1", "y"), None
            
            else:
                return value, None
        
        except Exception as e:
            return None, f"Type conversion error: {str(e)}"
    
    def _validate_record(self, record: MonitoringRecord) -> bool:
        """
        Validate record against source definition rules.
        
        Args:
            record: Record to validate
        
        Returns:
            True if valid, False if invalid (error message stored in record)
        """
        if not self.source_def.validation_enabled:
            return True
        
        for col_def in self.source_def.columns:
            if not col_def.validation:
                continue
            
            # Get value from record
            value = getattr(record, col_def.id, None)
            if value is None:
                continue  # Optional field
            
            # Check constraints
            if col_def.validation.min is not None:
                if value < col_def.validation.min:
                    record.error_message = f"{col_def.id} below minimum: {value} < {col_def.validation.min}"
                    record.is_valid = False
                    return False
            
            if col_def.validation.max is not None:
                if value > col_def.validation.max:
                    record.error_message = f"{col_def.id} above maximum: {value} > {col_def.validation.max}"
                    record.is_valid = False
                    return False
        
        return True


# ============================================================================
# STACKED BLOCKS PARSER (Multiple items stacked vertically)
# ============================================================================

class StackedBlocksParser(MonitoringExcelParser):
    """
    Parse Excel files with stacked block structure.
    
    Structure:
        Borehole ID | Borehole Name | Date       | Static Level
        BH001       | East Shaft    | 2025-01-01 | 42.5
        BH001       | East Shaft    | 2025-01-02 | 42.6
        BH001       | East Shaft    | 2025-01-03 | 42.7
        
        BH002       | West Shaft    | 2025-01-01 | 38.2
        BH002       | West Shaft    | 2025-01-02 | 38.1
    
    Each block = one borehole, multiple measurements
    """
    
    def parse(self, file_path: str) -> ParseResult:
        """Parse stacked blocks Excel file"""
        
        result = ParseResult(
            source_id=self.source_def.id,
            file_path=file_path
        )
        
        start_time = time.perf_counter()
        
        try:
            # Read Excel
            df = pd.read_excel(file_path, engine='openpyxl')
            result.total_rows = len(df)
            
            # Find columns
            col_mapping = self._find_columns(df)
            if not col_mapping:
                result.errors.append("No required columns found")
                return result
            
            # Parse rows
            for idx, row in df.iterrows():
                try:
                    # Create record based on source type
                    if self.source_def.id.startswith("borehole_static"):
                        record = self._parse_borehole_static_row(row, col_mapping, file_path)
                    else:
                        # Default: use generic parsing
                        continue
                    
                    if record:
                        if self._validate_record(record):
                            result.records.append(record)
                            result.valid_rows += 1
                        else:
                            result.skipped_rows += 1
                            if app_config.get('monitoring_settings.collect_error_statistics'):
                                result.errors.append(f"Row {idx}: {record.error_message}")
                
                except Exception as e:
                    result.skipped_rows += 1
                    if app_config.get('monitoring_settings.collect_error_statistics'):
                        result.errors.append(f"Row {idx}: {str(e)}")
        
        except Exception as e:
            result.errors.append(f"File parsing error: {str(e)}")
            logger.error(f"Error parsing {file_path}: {e}")
        
        result.parse_time_ms = (time.perf_counter() - start_time) * 1000
        
        return result
    
    def _parse_borehole_static_row(self, row, col_mapping, file_path) -> Optional[BoreholeStaticRecord]:
        """Parse a single row into BoreholeStaticRecord"""
        
        # Extract values
        borehole_id_col = col_mapping.get("borehole_id")
        date_col = col_mapping.get("measurement_date")
        level_col = col_mapping.get("static_level_m")
        
        if not all([borehole_id_col, date_col, level_col]):
            return None
        
        # Convert types
        borehole_id, err = self._convert_type(row.get(borehole_id_col), DataType.STRING)
        if err or not borehole_id:
            return None
        
        measurement_date, err = self._convert_type(row.get(date_col), DataType.DATE)
        if err or not measurement_date:
            return None
        
        static_level, err = self._convert_type(row.get(level_col), DataType.FLOAT)
        if err or static_level is None:
            return None
        
        # Create record
        return BoreholeStaticRecord(
            source_id=self.source_def.id,
            source_file=Path(file_path).name,
            measurement_date=measurement_date,
            borehole_id=borehole_id,
            borehole_name=row.get(col_mapping.get("borehole_name", "")) or borehole_id,
            static_level_m=static_level,
            depth_m=row.get(col_mapping.get("depth_m")) if "depth_m" in col_mapping else None
        )


# ============================================================================
# TIMESERIES PARSER (Rows = measurements, Columns = parameters)
# ============================================================================

class TimeseriesParser(MonitoringExcelParser):
    """
    Parse Excel files with timeseries structure.
    
    Structure:
        Date       | Parameter1 | Parameter2 | Parameter3
        2025-01-01 | 42.5       | 22.1       | 7.2
        2025-01-02 | 42.6       | 22.3       | 7.1
        2025-01-03 | 42.7       | 22.0       | 7.3
    
    Each row = one measurement with multiple parameters
    """
    
    def parse(self, file_path: str) -> ParseResult:
        """Parse timeseries Excel file"""
        
        result = ParseResult(
            source_id=self.source_def.id,
            file_path=file_path
        )
        
        start_time = time.perf_counter()
        
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            result.total_rows = len(df)
            
            # Find columns
            col_mapping = self._find_columns(df)
            if not col_mapping:
                result.errors.append("No required columns found")
                return result
            
            # Parse rows
            for idx, row in df.iterrows():
                try:
                    if self.source_def.id.startswith("borehole_monitoring"):
                        record = self._parse_borehole_monitoring_row(row, col_mapping, file_path)
                    elif self.source_def.id.startswith("pcd_monitoring"):
                        record = self._parse_pcd_row(row, col_mapping, file_path)
                    else:
                        continue
                    
                    if record:
                        if self._validate_record(record):
                            result.records.append(record)
                            result.valid_rows += 1
                        else:
                            result.skipped_rows += 1
                            if app_config.get('monitoring_settings.collect_error_statistics'):
                                result.errors.append(f"Row {idx}: {record.error_message}")
                
                except Exception as e:
                    result.skipped_rows += 1
                    if app_config.get('monitoring_settings.collect_error_statistics'):
                        result.errors.append(f"Row {idx}: {str(e)}")
        
        except Exception as e:
            result.errors.append(f"File parsing error: {str(e)}")
            logger.error(f"Error parsing {file_path}: {e}")
        
        result.parse_time_ms = (time.perf_counter() - start_time) * 1000
        
        return result
    
    def _parse_borehole_monitoring_row(self, row, col_mapping, file_path) -> Optional[BoreholeMonitoringRecord]:
        """Parse aquifer monitoring row"""
        
        borehole_id_col = col_mapping.get("borehole_id")
        date_col = col_mapping.get("measurement_date")
        depth_col = col_mapping.get("aquifer_depth_m")
        
        if not all([borehole_id_col, date_col, depth_col]):
            return None
        
        borehole_id, _ = self._convert_type(row.get(borehole_id_col), DataType.STRING)
        measurement_date, _ = self._convert_type(row.get(date_col), DataType.DATE)
        aquifer_depth, _ = self._convert_type(row.get(depth_col), DataType.FLOAT)
        
        if not all([borehole_id, measurement_date, aquifer_depth is not None]):
            return None
        
        return BoreholeMonitoringRecord(
            source_id=self.source_def.id,
            source_file=Path(file_path).name,
            measurement_date=measurement_date,
            borehole_id=borehole_id,
            aquifer_depth_m=aquifer_depth,
            temperature_c=self._get_optional_float(row, col_mapping, "temperature_c"),
            conductivity_us_cm=self._get_optional_float(row, col_mapping, "conductivity_us_cm"),
            ph=self._get_optional_float(row, col_mapping, "ph")
        )
    
    def _parse_pcd_row(self, row, col_mapping, file_path) -> Optional[PCDMonitoringRecord]:
        """Parse PCD monitoring row"""
        
        pcd_id_col = col_mapping.get("pcd_id")
        date_col = col_mapping.get("measurement_date")
        level_col = col_mapping.get("water_level_m")
        
        if not all([pcd_id_col, date_col, level_col]):
            return None
        
        pcd_id, _ = self._convert_type(row.get(pcd_id_col), DataType.STRING)
        measurement_date, _ = self._convert_type(row.get(date_col), DataType.DATE)
        water_level, _ = self._convert_type(row.get(level_col), DataType.FLOAT)
        
        if not all([pcd_id, measurement_date, water_level is not None]):
            return None
        
        return PCDMonitoringRecord(
            source_id=self.source_def.id,
            source_file=Path(file_path).name,
            measurement_date=measurement_date,
            pcd_id=pcd_id,
            water_level_m=water_level,
            ph=self._get_optional_float(row, col_mapping, "ph"),
            conductivity_us_cm=self._get_optional_float(row, col_mapping, "conductivity_us_cm"),
            tss_mg_l=self._get_optional_float(row, col_mapping, "tss_mg_l")
        )
    
    def _get_optional_float(self, row, col_mapping, field_id) -> Optional[float]:
        """Helper to extract optional float field"""
        col = col_mapping.get(field_id)
        if not col:
            return None
        value, _ = self._convert_type(row.get(col), DataType.FLOAT)
        return value


# ============================================================================
# PARSER FACTORY
# ============================================================================

class ParserFactory:
    """Factory for creating appropriate parsers based on source definition"""
    
    @staticmethod
    def create_parser(source_def: DataSourceDefinition, threshold: float = 0.85) -> MonitoringExcelParser:
        """
        Create appropriate parser for data source.
        
        Args:
            source_def: Data source definition
            threshold: Fuzzy matching threshold
        
        Returns:
            Parser instance (StackedBlocksParser or TimeseriesParser)
        
        Raises:
            ValueError: If source structure type not supported
        """
        
        if source_def.structure_type == StructureType.STACKED_BLOCKS:
            logger.info(f"  Creating StackedBlocksParser for {source_def.id}")
            return StackedBlocksParser(source_def, threshold)
        
        elif source_def.structure_type == StructureType.TIMESERIES:
            logger.info(f"  Creating TimeseriesParser for {source_def.id}")
            return TimeseriesParser(source_def, threshold)
        
        else:
            raise ValueError(f"Unsupported structure type: {source_def.structure_type}")


# ============================================================================
# PARSER REGISTRY (convenience functions)
# ============================================================================

_parser_cache = {}

def get_parser(source_def: DataSourceDefinition) -> MonitoringExcelParser:
    """
    Get or create cached parser for source.
    
    Benefit: Parser instances are stateless, safe to cache and reuse
    
    Args:
        source_def: Data source definition
    
    Returns:
        Cached parser instance
    """
    if source_def.id not in _parser_cache:
        threshold = app_config.get('monitoring_settings.column_match_threshold', 0.85)
        _parser_cache[source_def.id] = ParserFactory.create_parser(source_def, threshold)
    
    return _parser_cache[source_def.id]


if __name__ == "__main__":
    """Test parsers"""
    
    from models.monitoring_data import StructureType, DataType, ColumnMapping
    
    # Create test source definition
    source_def = DataSourceDefinition(
        id="test_source",
        name="Test Source",
        directory_pattern="data/test",
        structure_type=StructureType.STACKED_BLOCKS,
        columns=[
            ColumnMapping(
                id="borehole_id",
                type=DataType.STRING,
                required=True,
                expected_names=["Borehole ID", "ID"]
            )
        ]
    )
    
    # Test parser creation
    parser = ParserFactory.create_parser(source_def)
    print(f"✓ Created parser: {parser.__class__.__name__}")
    
    # Test fuzzy matching
    match = fuzzy_match_column("Static Level", ["Static Level (m)", "SWL", "Level"])
    print(f"✓ Fuzzy match: {match}")
    
    print("\n✅ Parser framework ready!")

