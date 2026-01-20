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
        """Calculate overall and per-area balance metrics from template files
        
        Reads ALL flows from .txt template files:
        - INFLOW_CODES_TEMPLATE.txt
        - OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
        - DAM_RECIRCULATION_TEMPLATE.txt
        
        Returns:
            OverallBalanceMetrics object with all calculations
        """
        return self._calculate_from_templates()

    
    def _calculate_from_templates(self) -> OverallBalanceMetrics:
        """Calculate balance from template files (fallback)
        
        Returns:
            OverallBalanceMetrics with calculations from templates
        """
        metrics = OverallBalanceMetrics()
        
        all_areas = self.parser.get_areas()

        for entry in self.parser.inflows:
            metrics.total_inflows += entry.value_m3

        for entry in self.parser.outflows:
            metrics.total_outflows += entry.value_m3

        for entry in self.parser.recirculation:
            metrics.total_recirculation += entry.value_m3

        for entry in self.parser.inflows:
            metrics.inflow_count += 1
        for entry in self.parser.outflows:
            metrics.outflow_count += 1
        for entry in self.parser.recirculation:
            metrics.recirculation_count += 1
        
        # Calculate per-area metrics (for ALL areas)
        for area in sorted(all_areas):
            area_inflows = self.parser.get_inflows_by_area(area)
            area_outflows = self.parser.get_outflows_by_area(area)
            area_recirculation = self.parser.get_recirculation_by_area(area)
            
            area_metrics = AreaBalanceMetrics(
                area=area,
                total_inflows=sum(e.value_m3 for e in area_inflows),
                total_outflows=sum(e.value_m3 for e in area_outflows),
                total_recirculation=sum(e.value_m3 for e in area_recirculation),
                inflow_count=len(area_inflows),
                outflow_count=len(area_outflows),
                recirculation_count=len(area_recirculation),
            )
            
            metrics.area_metrics[area] = area_metrics
        
        self.metrics = metrics
        self._log_balance_summary(metrics)
        return metrics
    
    def _log_balance_summary(self, metrics: OverallBalanceMetrics):
        """Log balance check summary"""
        
        logger.info("=" * 70)
        logger.info("WATER BALANCE CHECK SUMMARY")
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
