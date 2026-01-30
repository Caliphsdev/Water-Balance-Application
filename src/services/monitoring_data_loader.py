"""
Monitoring Data Loader - Orchestration Service

Loads Excel files from directories, manages caching, handles incremental updates.

Key Features:
- Directory scanning (finds Excel files)
- File validation (checks they're readable)
- Incremental loading (tracks mtimes, skips unchanged files)
- Caching (in-memory + disk cache)
- Background threading (REUSE AsyncDatabaseLoader pattern)
- Error handling (collects errors, continues processing)

Architecture:
1. Scan directory for Excel files
2. Check cache (mtime-based) - skip if unchanged
3. Select parser based on source definition
4. Parse file in background thread
5. Collect results + cache
6. Return combined DataFrame to UI

REUSE: Async pattern from src/utils/async_loader.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import threading
import time
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime
import pandas as pd

from models.monitoring_data import (
    DataSourceDefinition, MonitoringRecord, ParseResult, LoadResult, CacheEntry
)
from services.monitoring_parsers import ParserFactory
from utils.app_logger import logger
from utils.config_manager import config as app_config


# ============================================================================
# CACHE MANAGER (incremental file-level caching)
# ============================================================================

class CacheManager:
    """
    Manages cached parsing results with mtime tracking.
    
    Strategy:
    - Cache by file path
    - Store file modification time
    - Skip unchanged files (instant load)
    - Reparse if file modified
    """
    
    def __init__(self, cache_dir: str):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_cache: Dict[str, List[MonitoringRecord]] = {}
        self.mtime_cache: Dict[str, float] = {}
        
        logger.info(f"Cache manager initialized: {self.cache_dir}")
    
    def get_cache_key(self, file_path: str) -> str:
        """Generate cache key from file path"""
        return Path(file_path).stem  # filename without extension
    
    def is_cached(self, file_path: str) -> bool:
        """Check if file is in cache AND file hasn't been modified"""
        
        key = self.get_cache_key(file_path)
        
        # Not in memory cache
        if key not in self.memory_cache:
            return False
        
        # Check if file was modified
        try:
            current_mtime = os.path.getmtime(file_path)
            cached_mtime = self.mtime_cache.get(key)
            
            if cached_mtime is None:
                return False  # No mtime recorded
            
            return current_mtime == cached_mtime  # Same modification time = not changed
        
        except (OSError, FileNotFoundError):
            return False
    
    def get(self, file_path: str) -> Optional[List[MonitoringRecord]]:
        """Get cached records (if not stale)"""
        if self.is_cached(file_path):
            key = self.get_cache_key(file_path)
            logger.debug(f"  ✓ Cache hit: {Path(file_path).name}")
            return self.memory_cache.get(key)
        return None
    
    def set(self, file_path: str, records: List[MonitoringRecord]):
        """Cache parsed records with current mtime"""
        key = self.get_cache_key(file_path)
        
        try:
            mtime = os.path.getmtime(file_path)
            self.memory_cache[key] = records
            self.mtime_cache[key] = mtime
            logger.debug(f"  ✓ Cached: {Path(file_path).name} ({len(records)} records)")
        except OSError:
            logger.warning(f"Cannot cache: {file_path} (file not accessible)")
    
    def clear(self):
        """Clear all caches"""
        self.memory_cache.clear()
        self.mtime_cache.clear()
        logger.info("Caches cleared")


# ============================================================================
# DATA LOADER
# ============================================================================

class MonitoringDataLoader:
    """
    Load monitoring data from Excel directory.
    
    Usage:
        loader = MonitoringDataLoader(source_def, directory)
        result = loader.load()  # Blocking
        
        # OR async:
        loader.load_async(on_complete=callback)
    """
    
    def __init__(self, source_def: DataSourceDefinition, directory: Optional[Path] = None):
        """
        Initialize loader for specific data source.
        
        Args:
            source_def: Defines how to load this source (from YAML config)
            directory: Where to scan for Excel files (overrides config)
        """
        self.source_def = source_def
        self.directory = directory or Path(source_def.directory_pattern)
        
        # Ensure directory is absolute (relative to WATERBALANCE_USER_DIR)
        if not self.directory.is_absolute():
            base_dir = Path(os.getenv('WATERBALANCE_USER_DIR', '.'))
            self.directory = base_dir / self.directory
        
        # Initialize cache
        cache_dir = Path(app_config.get('monitoring_settings.cache_directory', 'data/monitoring/cache'))
        if not cache_dir.is_absolute():
            base_dir = Path(os.getenv('WATERBALANCE_USER_DIR', '.'))
            cache_dir = base_dir / cache_dir
        
        self.cache = CacheManager(str(cache_dir)) if app_config.get('monitoring_settings.enable_result_caching') else None
        
        # Parser
        self.parser = ParserFactory.create_parser(source_def)
        
        # Results
        self.result: Optional[LoadResult] = None
        self.loading = False
        self.error: Optional[str] = None
        
        logger.info(f"✓ Loader created: {source_def.id}")
    
    def scan_files(self) -> List[Path]:
        """
        Scan directory for Excel files matching pattern.
        
        Returns:
            List of Excel file paths
        """
        if not self.directory.exists():
            logger.warning(f"Directory not found: {self.directory}")
            return []
        
        pattern = self.source_def.file_pattern  # e.g., "*.xlsx"
        files = list(self.directory.glob(pattern))
        
        logger.info(f"Scanned: {len(files)} files in {self.directory}")
        return sorted(files)
    
    def load(self) -> LoadResult:
        """
        Load all files from directory (BLOCKING).
        
        Use load_async() for non-blocking version.
        
        Returns:
            LoadResult with all records and statistics
        """
        self.result = LoadResult(
            source_id=self.source_def.id,
            directory=str(self.directory)
        )
        
        start_time = time.perf_counter()
        
        try:
            # Scan files
            files = self.scan_files()
            self.result.files_scanned = len(files)
            
            if not files:
                logger.warning(f"No Excel files found: {self.directory}")
                return self.result
            
            # Process each file
            max_files = app_config.get('monitoring_settings.max_files_per_source', 100)
            
            for file_path in files[:max_files]:
                logger.info(f"Processing: {file_path.name}")
                
                # Check cache first
                if self.cache:
                    cached_records = self.cache.get(str(file_path))
                    if cached_records:
                        # Use cache
                        parse_result = ParseResult(
                            source_id=self.source_def.id,
                            file_path=str(file_path),
                            records=cached_records,
                            total_rows=len(cached_records),
                            valid_rows=len(cached_records),
                            parse_time_ms=0.5  # Cached - instant
                        )
                        self.result.files_cached += 1
                    else:
                        # Parse file
                        parse_result = self.parser.parse(str(file_path))
                        
                        # Cache result
                        if parse_result.records:
                            self.cache.set(str(file_path), parse_result.records)
                        
                        self.result.files_parsed += 1
                else:
                    # No caching - parse directly
                    parse_result = self.parser.parse(str(file_path))
                    self.result.files_parsed += 1
                
                # Collect results
                self.result.file_results.append(parse_result)
                self.result.total_records += len(parse_result.records)
                self.result.total_errors += len(parse_result.errors)
                
                logger.debug(f"  Result: {parse_result}")
        
        except Exception as e:
            self.error = str(e)
            logger.error(f"Load error: {e}", exc_info=True)
        
        finally:
            self.result.total_time_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"✅ {self.result}")
        
        return self.result
    
    def load_async(self, on_complete: Optional[Callable] = None):
        """
        Load files in background thread (non-blocking).
        
        Reuses AsyncDatabaseLoader pattern from existing app.
        
        Args:
            on_complete: Callback(loader, result, error) when complete
        """
        def worker():
            try:
                self.loading = True
                self.load()
                self.loading = False
                
                if on_complete:
                    on_complete(self, self.result, None)
            
            except Exception as e:
                self.loading = False
                self.error = str(e)
                logger.error(f"Async load error: {e}")
                
                if on_complete:
                    on_complete(self, None, str(e))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        logger.info("🚀 Async load started in background thread")
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Convert loaded records to pandas DataFrame for display/analysis.
        
        Returns:
            DataFrame with all records (empty if no data)
        """
        if not self.result or not self.result.file_results:
            return pd.DataFrame()
        
        # Collect all records from all files
        all_records = []
        for file_result in self.result.file_results:
            all_records.extend(file_result.records)
        
        if not all_records:
            return pd.DataFrame()
        
        # Convert to DataFrame (use model_dump for Pydantic v2)
        try:
            data = [r.model_dump() for r in all_records]
        except AttributeError:
            # Pydantic v1 fallback
            data = [r.dict() for r in all_records]
        
        df = pd.DataFrame(data)
        
        # Sort by measurement date
        if 'measurement_date' in df.columns:
            df = df.sort_values('measurement_date')
        
        logger.info(f"Created DataFrame: {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def get_statistics(self) -> Dict:
        """Get summary statistics about loaded data"""
        if not self.result:
            return {}
        
        return {
            'source_id': self.source_def.id,
            'files_scanned': self.result.files_scanned,
            'files_parsed': self.result.files_parsed,
            'files_cached': self.result.files_cached,
            'total_records': self.result.total_records,
            'total_errors': self.result.total_errors,
            'success_rate': f"{self.result.success_rate:.1f}%",
            'total_time_ms': f"{self.result.total_time_ms:.0f}ms"
        }
    
    def clear_cache(self):
        """Clear all cached data (call after Excel files are updated)"""
        if self.cache:
            self.cache.clear()
        logger.info("Cache cleared for all sources")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_loader(source_def: DataSourceDefinition, directory: Optional[Path] = None) -> MonitoringDataLoader:
    """
    Create loader for data source.
    
    Args:
        source_def: Data source definition from config
        directory: Override directory (for testing)
    
    Returns:
        Configured MonitoringDataLoader
    """
    return MonitoringDataLoader(source_def, directory)


if __name__ == "__main__":
    """Test loader"""
    
    from models.monitoring_data import StructureType, DataType, ColumnMapping
    
    # Create test source
    source_def = DataSourceDefinition(
        id="test_source",
        name="Test Source",
        directory_pattern="data/monitoring/test",
        structure_type=StructureType.STACKED_BLOCKS,
        columns=[
            ColumnMapping(
                id="borehole_id",
                type=DataType.STRING,
                required=True,
                expected_names=["Borehole ID"]
            )
        ]
    )
    
    # Create loader
    loader = MonitoringDataLoader(source_def)
    print(f"✓ Loader created: {loader.source_def.id}")
    print(f"  Directory: {loader.directory}")
    print(f"  Parser: {loader.parser.__class__.__name__}")
    
    # Scan (won't find files in non-existent directory, but that's OK)
    files = loader.scan_files()
    print(f"✓ Scanned: {len(files)} files")
    
    print("\n✅ Loader framework ready!")

