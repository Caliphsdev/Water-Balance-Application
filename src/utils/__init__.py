"""Utils Package - Utility Functions and Helpers"""

# Lazy imports to avoid pandas dependency until needed
def __getattr__(name):
    """Lazy load modules to avoid importing pandas until needed"""
    if name in ("ExcelTimeSeriesRepository", "ExcelTimeSeriesConfig", "get_default_excel_repo"):
        from .excel_timeseries import ExcelTimeSeriesRepository, ExcelTimeSeriesConfig, get_default_excel_repo
        return globals()[name]
    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = [
	"ExcelTimeSeriesRepository",
	"ExcelTimeSeriesConfig",
	"get_default_excel_repo",
]
