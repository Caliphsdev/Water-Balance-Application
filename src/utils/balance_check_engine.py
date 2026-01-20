"""
Balance Check Calculation Engine - Computes water balance metrics
Uses template data without writing to database except constants when missing
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from utils.template_data_parser import get_template_parser
from utils.app_logger import logger


@dataclass
class AreaBalanceMetrics:
    """Balance metrics for a single area"""
    area: str
    total_inflows: float = 0.0
    total_outflows: float = 0.0
    total_recirculation: float = 0.0
    inflow_count: int = 0
    outflow_count: int = 0
    recirculation_count: int = 0
    
    @property
    def balance_difference(self) -> float:
        """Calculate balance difference (should be close to 0)"""
        return self.total_inflows - self.total_recirculation - self.total_outflows
    
    @property
    def balance_error_percent(self) -> float:
        """Calculate balance error percentage"""
        if self.total_inflows == 0:
            return 0.0
        return (self.balance_difference / self.total_inflows) * 100
    
    @property
    def is_balanced(self) -> bool:
        """Check if area is balanced (error < 0.5%)"""
        return abs(self.balance_error_percent) < 0.5
    
    @property
    def status_label(self) -> str:
        """Get status label"""
        error = abs(self.balance_error_percent)
        if error < 0.1:
            return "✅ Excellent"
        elif error < 0.5:
            return "⚠️ Good"
        else:
            return "❌ Check"


@dataclass
class OverallBalanceMetrics:
    """Overall water balance metrics"""
    total_inflows: float = 0.0
    total_outflows: float = 0.0
    total_recirculation: float = 0.0
    inflow_count: int = 0
    outflow_count: int = 0
    recirculation_count: int = 0
    area_metrics: Dict[str, AreaBalanceMetrics] = field(default_factory=dict)
    
    @property
    def balance_difference(self) -> float:
        """Calculate overall balance difference"""
        return self.total_inflows - self.total_recirculation - self.total_outflows
    
    @property
    def balance_error_percent(self) -> float:
        """Calculate overall balance error percentage"""
        if self.total_inflows == 0:
            return 0.0
        return (self.balance_difference / self.total_inflows) * 100
    
    @property
    def is_balanced(self) -> bool:
        """Check if overall balance is acceptable (error < 0.5%)"""
        return abs(self.balance_error_percent) < 0.5
    
    @property
    def status_label(self) -> str:
        """Get status label"""
        error = abs(self.balance_error_percent)
        if error < 0.1:
            return "✅ Excellent"
        elif error < 0.5:
            return "⚠️ Good"
        else:
            return "❌ Check"


class BalanceCheckEngine:
    """Calculates water balance metrics from template data
    
    Uses ALL flows from templates - no configuration filtering
    """
    
    def __init__(self):
        self.parser = get_template_parser()
        self.metrics: Optional[OverallBalanceMetrics] = None
    
    def calculate_balance(self) -> OverallBalanceMetrics:
        """Calculate overall and per-area balance metrics from template files (MASTER VALIDATOR).
        
        This method reads ALL flows from immutable .txt template files and calculates:
        - Total inflows across all areas (natural water entering system)
        - Total outflows across all areas (water leaving system)
        - Total recirculation (water recycled within system)
        - Per-area metrics (balance for each mining area independently)
        - Closure error (how well the balance equation closes)
        
        Template files loaded (read-only):
        - INFLOW_CODES_TEMPLATE.txt: All natural water entering the system
        - OUTFLOW_CODES_TEMPLATE_CORRECTED.txt: All water leaving the system
        - DAM_RECIRCULATION_TEMPLATE.txt: All recycled/internal water transfers
        
        Returns:
            OverallBalanceMetrics object with:
            - Overall metrics: total_inflows, total_outflows, total_recirculation, error %
            - Per-area breakdown: {area: AreaBalanceMetrics} for analysis by mining area
            - Status indicators: is_balanced, status_label (GREEN/YELLOW/RED)
        
        Note: Uses ALL flows from templates - no configuration filtering.
        Scientific basis: Fresh Inflows = Outflows + ΔStorage + Error
        """
        return self._calculate_from_templates()

    def _calculate_from_templates(self) -> OverallBalanceMetrics:
        """Calculate balance from template files (Internal calculation engine).
        
        Reads flows from the three immutable template files and aggregates them:
        1. Sums all inflows (natural water entry points)
        2. Sums all outflows (natural water exit points)
        3. Sums all recirculation flows (recycled water)
        4. Computes per-area metrics for each mining area
        5. Calculates closure error (should be < 0.5% for balanced system)
        
        Returns:
            OverallBalanceMetrics: Complete balance snapshot with:
            - Totals across all areas
            - Per-area breakdown
            - Closure metrics (balance_difference, balance_error_percent)
        
        Note: This method is called by calculate_balance() and should not be used directly.
        """
        metrics = OverallBalanceMetrics()
        
        all_areas = self.parser.get_areas()

        # Sum all inflows from template
        for entry in self.parser.inflows:
            metrics.total_inflows += entry.value_m3

        # Sum all outflows from template
        for entry in self.parser.outflows:
            metrics.total_outflows += entry.value_m3

        # Sum all recirculation flows (self-loops within system)
        for entry in self.parser.recirculation:
            metrics.total_recirculation += entry.value_m3

        # Count flow entries for metrics
        for entry in self.parser.inflows:
            metrics.inflow_count += 1
        for entry in self.parser.outflows:
            metrics.outflow_count += 1
        for entry in self.parser.recirculation:
            metrics.recirculation_count += 1
        
        # Calculate per-area metrics (for EACH mining area independently)
        for area in sorted(all_areas):
            # Get flows for this specific area
            area_inflows = self.parser.get_inflows_by_area(area)
            area_outflows = self.parser.get_outflows_by_area(area)
            area_recirculation = self.parser.get_recirculation_by_area(area)
            
            # Create area-specific metrics
            area_metrics = AreaBalanceMetrics(
                area=area,
                total_inflows=sum(e.value_m3 for e in area_inflows),
                total_outflows=sum(e.value_m3 for e in area_outflows),
                total_recirculation=sum(e.value_m3 for e in area_recirculation),
                inflow_count=len(area_inflows),
                outflow_count=len(area_outflows),
                recirculation_count=len(area_recirculation),
            )
            
            # Store area metrics for later analysis
            metrics.area_metrics[area] = area_metrics
        
        # Cache metrics for later retrieval
        self.metrics = metrics
        self._log_balance_summary(metrics)
        return metrics
    
    def _log_balance_summary(self, metrics: OverallBalanceMetrics):
        """Log balance check summary to console and log file (VISIBILITY).
        
        Produces a formatted balance report showing:
        - Total inflows, outflows, recirculation (across all areas)
        - Balance difference and error percentage
        - Per-area status (GREEN/YELLOW/RED indicators)
        
        This helps validate system balance at a glance.
        """
        logger.info("=" * 70)
        logger.info("WATER BALANCE CHECK SUMMARY (SYSTEM-WIDE)")
        logger.info("=" * 70)
        logger.info(f"Total Inflows: {metrics.total_inflows:>20,.0f} m³ ({metrics.inflow_count} sources)")
        logger.info(f"Total Outflows: {metrics.total_outflows:>19,.0f} m³ ({metrics.outflow_count} flows)")
        logger.info(f"Total Recirculation: {metrics.total_recirculation:>14,.0f} m³ ({metrics.recirculation_count} self-loops)")
        logger.info("-" * 70)
        logger.info(f"Balance Difference: {metrics.balance_difference:>17,.0f} m³")
        logger.info(f"Balance Error: {metrics.balance_error_percent:>26.2f}%")
        logger.info(f"Status: {metrics.status_label}")
        logger.info("=" * 70)
    
    def get_metrics(self) -> Optional[OverallBalanceMetrics]:
        """Get cached metrics (returns None if not yet calculated)"""
        return self.metrics
    
    def refresh(self) -> OverallBalanceMetrics:
        """Refresh template data and recalculate balance"""
        logger.info("Refreshing template data...")
        self.parser.reload()
        return self.calculate_balance()
    
    def format_value(self, value: float) -> str:
        """Format value for display"""
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        elif abs(value) >= 1_000:
            return f"{value / 1_000:.1f}K"
        else:
            return f"{value:.0f}"
    

# Singleton instance
_engine_instance = None


def get_balance_check_engine() -> BalanceCheckEngine:
    """Get singleton engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = BalanceCheckEngine()
    return _engine_instance
