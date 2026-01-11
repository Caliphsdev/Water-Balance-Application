"""
Data Quality Checker
Validates water balance data completeness and integrity
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Tuple
import json

from database.db_manager import DatabaseManager
from utils.app_logger import logger


class DataQualityChecker:
    """Validates data quality and completeness for water balance calculations."""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def check_calculation_gaps(self, start_date: date, end_date: date) -> Dict:
        """
        Identify missing months in calculations table.
        
        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            
        Returns:
            {
                'has_gaps': bool,
                'missing_months': List[date],
                'gap_count': int,
                'completeness_pct': float,
                'expected_months': int,
                'present_months': int
            }
        """
        # Generate expected months
        expected_months = []
        current = date(start_date.year, start_date.month, 1)
        end_first = date(end_date.year, end_date.month, 1)
        
        while current <= end_first:
            expected_months.append(current)
            current = current + relativedelta(months=1)
        
        # Query existing calculations
        rows = self.db.execute_query(
            """SELECT DISTINCT SUBSTR(calc_date, 1, 7) as month
               FROM calculations 
               WHERE calc_date BETWEEN ? AND ?
               ORDER BY month""",
            (start_date, end_date)
        )
        
        present_months_str = {row['month'] for row in rows}
        present_months = {date(int(m[:4]), int(m[5:7]), 1) for m in present_months_str}
        
        missing_months = [m for m in expected_months if m not in present_months]
        
        expected_count = len(expected_months)
        present_count = len(present_months)
        completeness_pct = (present_count / expected_count * 100) if expected_count > 0 else 0.0
        
        return {
            'has_gaps': len(missing_months) > 0,
            'missing_months': missing_months,
            'gap_count': len(missing_months),
            'completeness_pct': completeness_pct,
            'expected_months': expected_count,
            'present_months': present_count
        }
    
    def check_input_completeness(self, calculation_date: date) -> Dict:
        """
        Check if inputs for a specific date are complete.
        
        Args:
            calculation_date: Date to check
            
        Returns:
            {
                'confidence_score': float (0-100),
                'missing_sources': List[str],
                'warnings': List[str],
                'has_excel_data': bool,
                'has_manual_inputs': bool,
                'facility_measurement_pct': float
            }
        """
        warnings = []
        missing_sources = []
        score = 100.0
        
        # Check for Excel data (via measurements or flow_volume_loader)
        excel_rows = self.db.execute_query(
            """SELECT COUNT(*) as cnt FROM measurements 
               WHERE measurement_date = ? AND data_source LIKE '%excel%'""",
            (calculation_date,)
        )
        has_excel = excel_rows[0]['cnt'] > 0 if excel_rows else False
        
        if not has_excel:
            warnings.append("No Excel meter readings found")
            missing_sources.append("Excel timeseries")
            score -= 30
        
        # Check for manual inputs
        month_start = date(calculation_date.year, calculation_date.month, 1)
        manual_rows = self.db.execute_query(
            """SELECT COUNT(*) as cnt FROM monthly_manual_inputs 
               WHERE month_start = ?""",
            (month_start,)
        )
        has_manual = manual_rows[0]['cnt'] > 0 if manual_rows else False
        
        # Check facility measurements
        facilities = self.db.get_storage_facilities()
        measured_facilities = self.db.execute_query(
            """SELECT DISTINCT facility_id FROM measurements
               WHERE measurement_date = ? AND facility_id IS NOT NULL""",
            (calculation_date,)
        )
        measured_count = len(measured_facilities)
        total_facilities = len(facilities)
        facility_pct = (measured_count / total_facilities * 100) if total_facilities > 0 else 0
        
        if facility_pct < 50:
            warnings.append(f"Only {facility_pct:.0f}% of facilities measured")
            score -= 25
        elif facility_pct < 100:
            score -= (100 - facility_pct) * 0.2  # Partial penalty
        
        # Check source measurements
        sources = self.db.get_water_sources(active_only=True)
        measured_sources = self.db.execute_query(
            """SELECT DISTINCT source_id FROM measurements
               WHERE measurement_date = ? AND source_id IS NOT NULL""",
            (calculation_date,)
        )
        measured_src_count = len(measured_sources)
        total_sources = len(sources)
        
        if measured_src_count < total_sources * 0.5:
            warnings.append(f"Only {measured_src_count}/{total_sources} sources measured")
            score -= 15
        
        return {
            'confidence_score': max(0.0, score),
            'missing_sources': missing_sources,
            'warnings': warnings,
            'has_excel_data': has_excel,
            'has_manual_inputs': has_manual,
            'facility_measurement_pct': facility_pct
        }
    
    def get_quality_level(self, completeness_pct: float, confidence_score: float = None) -> Tuple[str, str]:
        """
        Get quality level and color based on metrics.
        
        Args:
            completeness_pct: Data completeness percentage (0-100)
            confidence_score: Optional confidence score (0-100)
            
        Returns:
            (level: 'good'|'fair'|'poor', color: hex color code)
        """
        # Use average if both provided
        if confidence_score is not None:
            metric = (completeness_pct + confidence_score) / 2
        else:
            metric = completeness_pct
        
        if metric >= 95:
            return ('good', '#28a745')  # Green
        elif metric >= 80:
            return ('fair', '#ffc107')  # Yellow
        else:
            return ('poor', '#dc3545')  # Red
    
    def run_all_checks(self, start_date: date = None, end_date: date = None) -> Dict:
        """
        Run comprehensive data quality checks.
        
        Args:
            start_date: Optional start date (defaults to 12 months ago)
            end_date: Optional end date (defaults to today)
            
        Returns:
            {
                'gap_analysis': Dict,
                'recent_completeness': Dict,
                'quality_level': str,
                'quality_color': str,
                'warnings': int,
                'errors': int,
                'summary': str
            }
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - relativedelta(months=12)
        
        # Run gap analysis
        gap_analysis = self.check_calculation_gaps(start_date, end_date)
        
        # Check most recent month completeness
        recent_completeness = self.check_input_completeness(end_date)
        
        # Determine quality level
        quality_level, quality_color = self.get_quality_level(
            gap_analysis['completeness_pct'],
            recent_completeness['confidence_score']
        )
        
        # Count issues
        warnings = len(recent_completeness['warnings'])
        errors = gap_analysis['gap_count']
        
        # Build summary
        if quality_level == 'good':
            summary = f"Data quality excellent - {gap_analysis['completeness_pct']:.0f}% complete"
        elif quality_level == 'fair':
            summary = f"Data quality fair - {gap_analysis['gap_count']} gaps in last 12 months"
        else:
            summary = f"Data quality poor - {gap_analysis['completeness_pct']:.0f}% complete, {errors} missing months"
        
        # Log to database
        self._log_check_results(gap_analysis, recent_completeness, quality_level)
        
        return {
            'gap_analysis': gap_analysis,
            'recent_completeness': recent_completeness,
            'quality_level': quality_level,
            'quality_color': quality_color,
            'warnings': warnings,
            'errors': errors,
            'summary': summary
        }
    
    def _log_check_results(self, gap_analysis: Dict, completeness: Dict, quality_level: str):
        """Log check results to data_quality_checks table."""
        try:
            check_date = date.today().isoformat()
            
            # Log gap analysis
            if gap_analysis['has_gaps']:
                missing_dates_json = json.dumps([m.isoformat() for m in gap_analysis['missing_months']])
                severity = 'error' if gap_analysis['completeness_pct'] < 80 else 'warning'
                message = f"{gap_analysis['gap_count']} missing months detected ({gap_analysis['completeness_pct']:.1f}% complete)"
                
                self.db.execute_update(
                    """INSERT INTO data_quality_checks 
                       (check_date, check_type, severity, message, affected_dates, completeness_pct, gap_count)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (check_date, 'missing_months', severity, message, missing_dates_json, 
                     gap_analysis['completeness_pct'], gap_analysis['gap_count'])
                )
            
            # Log input completeness
            if completeness['confidence_score'] < 90:
                severity = 'error' if completeness['confidence_score'] < 70 else 'warning'
                message = f"Input completeness {completeness['confidence_score']:.0f}%: {', '.join(completeness['warnings'])}"
                
                self.db.execute_update(
                    """INSERT INTO data_quality_checks 
                       (check_date, check_type, severity, message, completeness_pct)
                       VALUES (?, ?, ?, ?, ?)""",
                    (check_date, 'incomplete_inputs', severity, message, completeness['confidence_score'])
                )
            
            logger.debug(f"Data quality check logged: {quality_level}")
        except Exception as e:
            logger.error(f"Failed to log quality check results: {e}")
    
    def get_recent_warnings(self, days: int = 30) -> List[Dict]:
        """
        Fetch recent quality warnings.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of warning/error records from data_quality_checks
        """
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        
        rows = self.db.execute_query(
            """SELECT * FROM data_quality_checks
               WHERE check_date >= ? AND severity IN ('warning', 'error')
               ORDER BY check_date DESC, severity DESC
               LIMIT 50""",
            (cutoff,)
        )
        
        return rows


# Singleton instance
_checker_instance = None


def get_data_quality_checker() -> DataQualityChecker:
    """Get or create singleton data quality checker instance."""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = DataQualityChecker()
    return _checker_instance


def reset_data_quality_checker():
    """Reset singleton instance (for testing or config changes)."""
    global _checker_instance
    _checker_instance = None
