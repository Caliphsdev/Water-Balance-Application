"""
Directory Loader Worker (QThread for background directory scanning).

Purpose:
- Load and combine multiple Excel files from a directory in a background thread (non-blocking UI).
- Emit progress signals for UI updates (progress bar, status label, etc.).
- Collect and report errors for files that fail to load (locked, corrupt, wrong format).
- Thread-safe logging to dashboard-specific folders.
- Support cancellation if user wants to stop loading.

Architecture:
- DirectoryLoadWorker: QThread worker that scans directory and loads Excel files.
- Signals: progress, file_loaded, error, complete, cancel_requested.
- Thread Safety: Uses Qt signals/slots for UI updates, logging is thread-safe.

Data Flow:
1. User selects directory → emit folder path to worker.start()
2. Worker scans for Excel files in directory.
3. For each file:
   - Emit "file_loading" signal (update progress).
   - Load and parse file with pandas.
   - Collect errors (if file fails).
4. Worker emits "complete" signal with combined DataFrame and error summary.
5. Main thread receives signal, updates UI (table, status label, error dialog).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, List, Tuple
from PySide6.QtCore import QThread, Signal, QObject
from shiboken6 import isValid
import pandas as pd

from core.app_logger import logger as app_logger


class DirectoryLoadWorker(QObject):
    """Background worker for loading and combining Excel files from a directory (DIRECTORY SCANNER).
    
    Responsibilities:
    - Scan a directory for all .xlsx/.xls files.
    - Load each file with pandas in a background thread (non-blocking UI).
    - Combine all DataFrames into one.
    - Track which files failed and why (locked, corrupt, wrong format, etc.).
    - Emit signals for progress, completion, and errors.
    - Thread-safe logging to dashboard-specific folder.
    
    Signals:
    - progress: Emitted for each file (current_file, total_files, current_file_name).
    - file_loaded: Emitted when a file is successfully loaded.
    - error: Emitted when a file fails to load (file_name, error_message).
    - complete: Emitted when all files processed (data, error_summary).
    - cancelled: Emitted if user cancels mid-load.
    
    Example Usage:
        worker = DirectoryLoadWorker("static_boreholes")
        worker.load_directory("/path/to/folder")
        worker.progress.connect(lambda c, t, n: logger.info("Loading %s (%s/%s)...", n, c, t))
        worker.complete.connect(on_load_complete)
        worker.start()
    """

    # Signals
    progress = Signal(int, int, str)  # (current_file_idx, total_files, file_name)
    file_loaded = Signal(str, int)     # (file_name, row_count)
    error = Signal(str, str)           # (file_name, error_reason)
    complete = Signal(pd.DataFrame, dict)  # (combined_df, error_summary)
    cancelled = Signal()
    cache_stats = Signal(dict)         # (cache_statistics: {cached, parsed, total})

    def __init__(self, dashboard_name: str) -> None:
        """Initialize worker with dashboard-specific logger.
        
        Args:
            dashboard_name: Dashboard name (e.g., "static_boreholes", "borehole_monitoring", "pcd_monitoring")
                          - Used for logging folder and logger name.
        """
        super().__init__()
        self._cancel_requested = False
        self._folder_path: Optional[Path] = None
        self.dashboard_name = dashboard_name
        
        # Cache functions (set from dashboard)
        self._cache_loader = None
        self._cache_saver = None
        self._cache_stats = {'files_cached': 0, 'files_parsed': 0, 'total_files': 0}
        
        # Dashboard-specific logger (logs to logs/monitoring/{dashboard_name}/)
        self.logger = app_logger.get_dashboard_logger(f"monitoring.{dashboard_name}")
        self.logger.info(f"DirectoryLoadWorker initialized for {dashboard_name}")

    def set_cache_functions(self, loader, saver):
        """Set cache loader and saver functions (CACHE INTEGRATION).
        
        Args:
            loader: Function(file_path: str) -> Optional[pd.DataFrame] to load from cache
            saver: Function(file_path: str, dataframe: pd.DataFrame) to save to cache
        """
        self._cache_loader = loader
        self._cache_saver = saver
        self.logger.info("Cache functions configured")
    
    def load_directory(self, folder_path: str) -> None:
        """Set the directory to scan. Call this before start().
        
        Args:
            folder_path: Path to directory containing Excel files.
        """
        self._folder_path = Path(folder_path)
        self._cancel_requested = False
        self._cache_stats = {'files_cached': 0, 'files_parsed': 0, 'total_files': 0}
        self.logger.info(f"Set load directory: {folder_path}")

    def cancel(self) -> None:
        """Request cancellation of current load operation (thread-safe)."""
        self._cancel_requested = True
        self.logger.info("Cancel requested by user")

    def _emit_safe(self, signal, *args) -> bool:
        """Safely emit a signal with error handling (THREAD SAFETY).
        
        Prevents "Signal source has been deleted" errors by catching exceptions
        when the worker/thread has been destroyed while a signal is being emitted.
        
        Args:
            signal: Qt signal to emit
            *args: Arguments to pass to the signal
        
        Returns:
            True if signal emitted successfully, False if worker/thread deleted
        """
        try:
            signal.emit(*args)
            return True
        except RuntimeError as e:
            if "Signal source has been deleted" in str(e):
                # Worker thread has been destroyed, silently ignore
                return False
            # Re-raise other RuntimeErrors
            raise

    def run(self) -> None:
        """Scan directory and load Excel files (run in QThread).
        
        This method is called when QThread.start() is invoked.
        It scans the directory, loads all .xlsx/.xls files, combines them,
        and emits progress/completion signals.
        
        Thread Safety: Uses _emit_safe() to handle deleted signals gracefully.
        """
        if not self._folder_path or not self._folder_path.exists():
            error_msg = f"Folder not found: {self._folder_path}"
            self.logger.error(error_msg)
            self._emit_safe(self.complete, pd.DataFrame(), {"error": error_msg})
            return

        try:
            # Scan for all Excel files in directory
            excel_files = sorted(
                list(self._folder_path.glob("*.xlsx")) + list(self._folder_path.glob("*.xls"))
            )
            
            if not excel_files:
                msg = f"No Excel files found in {self._folder_path}"
                self.logger.warning(msg)
                self._emit_safe(self.complete, pd.DataFrame(), {"warning": msg})
                return

            self.logger.info(f"Found {len(excel_files)} Excel files in {self._folder_path}")
            self._cache_stats['total_files'] = len(excel_files)

            # Load each file
            frames: List[pd.DataFrame] = []
            errors: Dict[str, str] = {}  # {filename: error_reason}
            
            for idx, excel_file in enumerate(excel_files):
                # Check for cancellation
                if self._cancel_requested:
                    self.logger.info("Loading cancelled by user")
                    self._emit_safe(self.cancelled)
                    return

                # Emit progress signal (update progress bar/label)
                self._emit_safe(self.progress, idx + 1, len(excel_files), excel_file.name)

                # Try cache first if loader provided
                df = None
                cache_hit = False
                if self._cache_loader:
                    df = self._cache_loader(str(excel_file))
                    if df is not None:
                        cache_hit = True
                        self._cache_stats['files_cached'] += 1
                        self.logger.debug(f"Cache HIT: {excel_file.name}")
                        frames.append(df)
                        self._emit_safe(self.file_loaded, excel_file.name, len(df))
                        continue  # Skip parsing, use cached data

                # Parse file if not cached
                try:
                    # Use STACKED BLOCKS parser for monitoring tabs (Tkinter's proven approach)
                    if self.dashboard_name == "borehole_monitoring":
                        # Use Tkinter's proven stacked blocks parser
                        from services.monitoring_excel_parser_v2 import parse_borehole_stacked_blocks
                        df = parse_borehole_stacked_blocks(str(excel_file))
                        if df.empty:
                            error_msg = "Failed to parse monitoring file (no data found)"
                            self.logger.warning(f"{excel_file.name}: {error_msg}")
                            errors[excel_file.name] = error_msg
                            self._emit_safe(self.error, excel_file.name, error_msg)
                            continue
                    elif self.dashboard_name == "pcd_monitoring":
                        # Use same stacked blocks parser
                        from services.monitoring_excel_parser_v2 import parse_borehole_stacked_blocks
                        df = parse_borehole_stacked_blocks(str(excel_file))
                        if df.empty:
                            error_msg = "Failed to parse PCD file (no data found)"
                            self.logger.warning(f"{excel_file.name}: {error_msg}")
                            errors[excel_file.name] = error_msg
                            self._emit_safe(self.error, excel_file.name, error_msg)
                            continue
                    else:
                        # Static levels: use simple parsing (DON'T TOUCH - IT'S WORKING)
                        df = pd.read_excel(excel_file)
                        df["source_file"] = excel_file.name
                    
                    # Save to cache if saver provided
                    if self._cache_saver and not cache_hit:
                        self._cache_saver(str(excel_file), df)
                        self._cache_stats['files_parsed'] += 1
                    
                    frames.append(df)
                    self._emit_safe(self.file_loaded, excel_file.name, len(df))

                except PermissionError as e:
                    error_msg = f"File is locked (open in another program): {str(e)}"
                    self.logger.error(f"{excel_file.name}: {error_msg}")
                    errors[excel_file.name] = error_msg
                    self._emit_safe(self.error, excel_file.name, error_msg)

                except Exception as e:
                    error_msg = f"Failed to read file: {str(e)}"
                    self.logger.error(f"{excel_file.name}: {error_msg}")
                    errors[excel_file.name] = error_msg
                    self._emit_safe(self.error, excel_file.name, error_msg)

            # Combine all loaded DataFrames
            if frames:
                combined_df = pd.concat(frames, ignore_index=True)
                self.logger.info(
                    f"Combined {len(frames)} files into DataFrame: "
                    f"{len(combined_df)} total rows, {len(combined_df.columns)} columns"
                )
            else:
                combined_df = pd.DataFrame()
                self.logger.warning("No files loaded successfully; returning empty DataFrame")

            # Build error summary
            error_summary = {
                "total_files": len(excel_files),
                "loaded_files": len(frames),
                "failed_files": len(errors),
                "errors": errors if errors else None,
            }

            # Emit cache statistics
            if self._cache_loader:
                self._emit_safe(self.cache_stats, self._cache_stats)
                self.logger.info(
                    f"Cache performance: {self._cache_stats['files_cached']} cached, "
                    f"{self._cache_stats['files_parsed']} parsed, "
                    f"{self._cache_stats['total_files']} total"
                )
            
            # Emit complete signal with data and error summary
            self._emit_safe(self.complete, combined_df, error_summary)
            self.logger.info("Directory loading complete")

        except Exception as e:
            error_msg = f"Unexpected error during directory load: {str(e)}"
            self.logger.error(error_msg)
            self._emit_safe(self.complete, pd.DataFrame(), {"exception": error_msg})


class DirectoryLoaderThread(QThread):
    """QThread wrapper for DirectoryLoadWorker (CONVENIENCE CLASS).
    
    Usage:
        thread = DirectoryLoaderThread("static_boreholes")
        thread.set_cache_functions(load_func, save_func)
        thread.load_directory("/path/to/folder")
        thread.complete.connect(on_load_complete)
        thread.cache_stats.connect(on_cache_stats)
        thread.start()
    
    Note: This class ensures proper cleanup on shutdown to avoid "thread destroyed while running" warnings.
    """

    complete = Signal(pd.DataFrame, dict)  # Forwarded from worker
    progress = Signal(int, int, str)       # Forwarded from worker
    error = Signal(str, str)               # Forwarded from worker
    cache_stats = Signal(dict)             # Forwarded from worker (cache performance)

    def __init__(self, dashboard_name: str) -> None:
        super().__init__()
        self.worker = DirectoryLoadWorker(dashboard_name)
        self.worker.moveToThread(self)

        # Forward signals from worker
        self.worker.complete.connect(self.complete.emit)
        self.worker.progress.connect(self.progress.emit)
        self.worker.error.connect(self.error.emit)
        self.worker.cache_stats.connect(self.cache_stats.emit)
        
        self.finished.connect(self.worker.deleteLater)
    
    def set_cache_functions(self, loader, saver):
        """Pass cache functions to worker."""
        self.worker.set_cache_functions(loader, saver)

    def load_directory(self, folder_path: str) -> None:
        """Set directory to load."""
        self.worker.load_directory(folder_path)

    def run(self) -> None:
        """Run worker in this thread."""
        self.worker.run()

    def cancel(self) -> None:
        """Request cancellation."""
        self.worker.cancel()
    
    def __del__(self) -> None:
        """Avoid touching Qt objects during Python GC shutdown.

        Thread shutdown is handled explicitly by page/main window lifecycle.
        """
        return
