"""
Monitoring Data Models - Type-Safe Data Validation

Pydantic models for monitoring data sources, column mappings, and record types.
Validates all data at definition time (fail fast on invalid data).

Models:
- DataSourceDefinition: Configuration for each monitoring source
- ColumnMapping: Describes how to find and map Excel columns
- ValidationRules: Data validation constraints (min, max, etc)
- MonitoringRecord: Base class for all record types
- BoreholeStaticRecord: Static borehole measurement
- BoreholeMonitoringRecord: Aquifer monitoring record
- PCDMonitoringRecord: Pollution control dam record
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum
from pathlib import Path


# ============================================================================
# ENUMS
# ============================================================================

class StructureType(str, Enum):
    """How data is organized in Excel files"""
    STACKED_BLOCKS = "stacked_blocks"  # Multiple boreholes stacked vertically
    TIMESERIES = "timeseries"  # Time series: rows = measurements, columns = parameters
    PAIRED_COLUMNS = "paired_columns"  # Date/value pairs in columns


class DataType(str, Enum):
    """Data types for columns"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class ChartType(str, Enum):
    """Chart display types"""
    LINE = "line"
    BAR = "bar"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class TimeUnit(str, Enum):
    """Time axis units"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


# ============================================================================
# VALIDATION RULES
# ============================================================================

class ValidationRules(BaseModel):
    """Validation constraints for a column"""
    
    min: Optional[float] = None
    max: Optional[float] = None
    allow_negative: Optional[bool] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    
    class Config:
        extra = "allow"  # Allow additional fields for extensibility


# ============================================================================
# COLUMN MAPPING
# ============================================================================

class ColumnMapping(BaseModel):
    """Maps a logical column ID to Excel column locations and names"""
    
    id: str = Field(..., description="Unique column identifier (e.g., 'static_level_m')")
    type: DataType = Field(..., description="Data type for this column")
    required: bool = Field(default=False, description="Is this column mandatory?")
    description: str = Field(default="", description="What this column represents")
    expected_names: List[str] = Field(
        default_factory=list,
        description="Column names to search for (fuzzy matched)"
    )
    validation: Optional[ValidationRules] = None
    
    class Config:
        use_enum_values = True


# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

class CacheConfig(BaseModel):
    """Cache settings for data source"""
    
    enabled: bool = Field(default=True)
    ttl_seconds: int = Field(default=3600)  # 1 hour
    incremental: bool = Field(default=True)  # Use mtime tracking


# ============================================================================
# DISPLAY CONFIGURATION
# ============================================================================

class DisplayConfig(BaseModel):
    """How to display data in UI"""
    
    default_chart_type: ChartType = ChartType.LINE
    time_unit: TimeUnit = TimeUnit.MONTH
    show_trend: bool = True
    multi_parameter: bool = False  # Multiple parameters on same chart
    
    class Config:
        use_enum_values = True


# ============================================================================
# DATA SOURCE CONFIGURATION
# ============================================================================

class DataSourceDefinition(BaseModel):
    """Complete definition of a monitoring data source"""
    
    id: str = Field(..., description="Unique source ID (e.g., 'borehole_static_v1')")
    name: str = Field(..., description="Display name (e.g., 'Borehole Static Levels')")
    description: str = Field(default="", description="Human-readable description")
    enabled: bool = Field(default=True)
    
    # Data source location
    directory_pattern: str = Field(..., description="Directory path (relative to WATERBALANCE_USER_DIR)")
    file_pattern: str = Field(default="*.xlsx", description="File glob pattern")
    
    # Structure
    structure_type: StructureType = Field(StructureType.TIMESERIES)
    header_keywords: List[str] = Field(default_factory=list)
    block_markers: Optional[List[str]] = None  # For stacked_blocks structure
    
    # Columns
    columns: List[ColumnMapping] = Field(default_factory=list)
    
    # Validation & cache
    validation_enabled: bool = True
    cache: CacheConfig = Field(default_factory=CacheConfig)
    
    # Display
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    
    @validator('id')
    def id_must_be_valid(cls, v):
        """Validate source ID format"""
        if not v or len(v) < 3:
            raise ValueError("Source ID must be at least 3 characters")
        if not all(c.isalnum() or c == '_' for c in v):
            raise ValueError("Source ID must contain only alphanumeric and underscore")
        return v
    
    class Config:
        use_enum_values = True


# ============================================================================
# MONITORING RECORDS
# ============================================================================

class MonitoringRecord(BaseModel):
    """Base class for all monitoring records"""
    
    record_id: Optional[str] = Field(None, description="Unique record identifier")
    source_id: str = Field(..., description="Which source this record came from")
    source_file: str = Field(..., description="Excel file this record was parsed from")
    measurement_date: date = Field(..., description="When measurement was taken")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    is_valid: bool = True
    error_message: Optional[str] = None
    
    class Config:
        use_enum_values = True
    
    def __str__(self):
        return f"{self.__class__.__name__}(date={self.measurement_date})"


class BoreholeStaticRecord(MonitoringRecord):
    """Borehole static water level measurement"""
    
    borehole_id: str
    borehole_name: str
    static_level_m: float  # meters below surface
    depth_m: Optional[float] = None  # well depth
    
    class Config:
        fields = {
            'static_level_m': {'description': 'Static water level in meters'}
        }


class BoreholeMonitoringRecord(MonitoringRecord):
    """Aquifer monitoring record (multiple parameters)"""
    
    borehole_id: str
    aquifer_depth_m: float
    temperature_c: Optional[float] = None
    conductivity_us_cm: Optional[float] = None  # µS/cm
    ph: Optional[float] = None


class PCDMonitoringRecord(MonitoringRecord):
    """Pollution control dam monitoring record"""
    
    pcd_id: str
    water_level_m: float
    ph: Optional[float] = None
    conductivity_us_cm: Optional[float] = None
    tss_mg_l: Optional[float] = None  # Total suspended solids


# ============================================================================
# PARSER OUTPUT
# ============================================================================

class ParseResult(BaseModel):
    """Result of parsing a single Excel file"""
    
    source_id: str
    file_path: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Results
    records: List[MonitoringRecord] = Field(default_factory=list)
    
    # Statistics
    total_rows: int = 0
    valid_rows: int = 0
    skipped_rows: int = 0
    errors: List[str] = Field(default_factory=list)
    
    # Performance
    parse_time_ms: float = 0.0
    
    @property
    def success(self) -> bool:
        """Was parsing successful (at least some valid records)?"""
        return len(self.records) > 0 and len(self.errors) == 0
    
    @property
    def error_rate(self) -> float:
        """Percentage of rows that failed"""
        if self.total_rows == 0:
            return 0.0
        return (self.skipped_rows / self.total_rows) * 100
    
    def __str__(self):
        return (
            f"ParseResult(file={Path(self.file_path).name}, "
            f"records={len(self.records)}, "
            f"errors={len(self.errors)}, "
            f"time={self.parse_time_ms:.0f}ms)"
        )


class LoadResult(BaseModel):
    """Result of loading all files from a source directory"""
    
    source_id: str
    directory: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # File processing
    files_scanned: int = 0
    files_parsed: int = 0
    files_cached: int = 0
    
    # Data
    total_records: int = 0
    total_errors: int = 0
    
    # Performance
    total_time_ms: float = 0.0
    
    # Per-file results
    file_results: List[ParseResult] = Field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Percentage of files parsed successfully"""
        if self.files_scanned == 0:
            return 0.0
        return ((self.files_parsed + self.files_cached) / self.files_scanned) * 100
    
    def __str__(self):
        return (
            f"LoadResult(source={self.source_id}, "
            f"files={self.files_parsed}/{self.files_scanned}, "
            f"records={self.total_records}, "
            f"time={self.total_time_ms:.0f}ms)"
        )


# ============================================================================
# CACHE ENTRY
# ============================================================================

class CacheEntry(BaseModel):
    """Cache entry for parsed data"""
    
    file_path: str
    file_mtime: float  # Modification time when cached
    cached_at: datetime = Field(default_factory=datetime.now)
    records: List[MonitoringRecord]
    
    def is_stale(self) -> bool:
        """Check if cache entry is stale (file was modified)"""
        import os
        try:
            current_mtime = os.path.getmtime(self.file_path)
            return current_mtime != self.file_mtime
        except (OSError, FileNotFoundError):
            return True  # File deleted or inaccessible - cache is stale


# ============================================================================
# CONFIGURATION
# ============================================================================

class MonitoringConfig(BaseModel):
    """Global monitoring settings"""
    
    cache_directory: str = "data/monitoring/cache"
    max_files_per_source: int = 100
    max_rows_per_file: int = 50000
    
    date_formats: List[str] = Field(
        default_factory=lambda: ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
    )
    
    column_match_threshold: float = 0.85  # Fuzzy matching threshold
    enable_background_parsing: bool = True
    max_parser_threads: int = 3
    enable_incremental_loading: bool = True
    enable_result_caching: bool = True
    cache_ttl_seconds: int = 3600
    skip_invalid_rows: bool = True
    collect_error_statistics: bool = True
    log_parsing_details: bool = False
    
    @validator('column_match_threshold')
    def validate_threshold(cls, v):
        """Ensure threshold is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return v


if __name__ == "__main__":
    """Test models"""
    
    # Test DataSourceDefinition
    source_def = DataSourceDefinition(
        id="borehole_static_v1",
        name="Borehole Static Levels",
        directory_pattern="data/monitoring/borehole_static",
        structure_type=StructureType.STACKED_BLOCKS,
        columns=[
            ColumnMapping(
                id="borehole_id",
                type=DataType.STRING,
                required=True,
                expected_names=["Borehole ID", "Well ID"]
            ),
            ColumnMapping(
                id="static_level_m",
                type=DataType.FLOAT,
                required=True,
                expected_names=["Static Level", "SWL"]
            )
        ]
    )
    
    print(f"✓ DataSourceDefinition: {source_def.id}")
    
    # Test BoreholeStaticRecord
    record = BoreholeStaticRecord(
        source_id="borehole_static_v1",
        source_file="BH001.xlsx",
        measurement_date=date.today(),
        borehole_id="BH001",
        borehole_name="East Shaft",
        static_level_m=42.5
    )
    
    print(f"✓ BoreholeStaticRecord: {record}")
    
    # Test ParseResult
    result = ParseResult(
        source_id="borehole_static_v1",
        file_path="data/BH001.xlsx",
        records=[record],
        total_rows=100,
        valid_rows=99,
        parse_time_ms=245.5
    )
    
    print(f"✓ ParseResult: {result}")
    print(f"  Success: {result.success}")
    print(f"  Error rate: {result.error_rate:.1f}%")
    
    print("\n✅ All models created successfully!")
