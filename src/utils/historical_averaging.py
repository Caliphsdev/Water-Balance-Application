"""
Historical Averaging Engine
Implements Excel-style AVERAGE functions for missing data estimation
Replicates: =AVERAGE(U144:U165) pattern from legacy workbooks
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from statistics import mean, median, stdev
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager


class HistoricalAveraging:
    """Excel-style historical averaging for missing measurements"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
    
    def estimate_missing_value(self, source_id: int, measurement_date: date,
                               measurement_type: str = 'inflow',
                               window_months: int = 12,
                               method: str = 'average') -> Dict:
        """
        Estimate missing measurement using historical data (Excel: AVERAGE formula)
        
        Args:
            source_id: Water source ID
            measurement_date: Date of missing measurement
            measurement_type: Type of measurement
            window_months: Lookback window (Excel: typically 12-24 months)
            method: 'average', 'median', 'weighted', 'seasonal'
        
        Returns:
            Dict with estimated_value, confidence, data_points_used, quality_flag
        """
        # Get historical measurements for this source
        start_date = measurement_date - timedelta(days=window_months * 30)
        
        historical_data = self.db.execute_query(
            """
            SELECT measurement_date, volume, measured, quality_flag
            FROM measurements
            WHERE source_id = ?
              AND measurement_type = ?
              AND measurement_date BETWEEN ? AND ?
              AND measurement_date < ?
              AND volume IS NOT NULL
              AND volume >= 0
            ORDER BY measurement_date DESC
            """,
            (source_id, measurement_type, start_date, measurement_date, measurement_date)
        )
        
        if not historical_data or len(historical_data) < 3:
            # Insufficient data - use system default
            return self._get_default_value(source_id, measurement_type)
        
        # Extract values
        values = [row['volume'] for row in historical_data]
        measured_count = sum(1 for row in historical_data if row.get('measured', True))
        
        # Calculate estimate based on method
        if method == 'average':
            # Excel: =AVERAGE(range)
            estimated_value = mean(values)
        elif method == 'median':
            estimated_value = median(values)
        elif method == 'weighted':
            # Recent data weighted more heavily
            estimated_value = self._weighted_average(historical_data, measurement_date)
        elif method == 'seasonal':
            # Same month in previous years
            estimated_value = self._seasonal_average(source_id, measurement_date, measurement_type)
        else:
            estimated_value = mean(values)
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(
            data_points=len(values),
            measured_ratio=measured_count / len(values),
            std_deviation=stdev(values) if len(values) > 1 else 0,
            mean_value=estimated_value
        )
        
        # Quality flag
        if confidence >= 0.8:
            quality_flag = 'good'
        elif confidence >= 0.6:
            quality_flag = 'estimated'
        elif confidence >= 0.4:
            quality_flag = 'interpolated'
        else:
            quality_flag = 'default'
        
        return {
            'estimated_value': estimated_value,
            'confidence': confidence,
            'data_points_used': len(values),
            'measured_points': measured_count,
            'quality_flag': quality_flag,
            'method': method,
            'window_months': window_months,
            'min_value': min(values),
            'max_value': max(values),
            'std_deviation': stdev(values) if len(values) > 1 else 0
        }
    
    def _weighted_average(self, historical_data: List[Dict], target_date: date) -> float:
        """Calculate weighted average (Excel: recent data weighted more)"""
        total_weight = 0.0
        weighted_sum = 0.0
        
        for row in historical_data:
            measurement_date = row['measurement_date']
            if isinstance(measurement_date, str):
                measurement_date = date.fromisoformat(measurement_date)
            
            # Weight decreases with age (Excel pattern)
            days_ago = (target_date - measurement_date).days
            weight = 1.0 / (1.0 + days_ago / 30.0)  # Decay over months
            
            weighted_sum += row['volume'] * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _seasonal_average(self, source_id: int, target_date: date, 
                         measurement_type: str) -> float:
        """Calculate seasonal average (Excel: same month in previous years)"""
        target_month = target_date.month
        
        # Get measurements from same month in previous 3 years
        seasonal_data = self.db.execute_query(
            """
            SELECT volume FROM measurements
            WHERE source_id = ?
              AND measurement_type = ?
              AND CAST(strftime('%m', measurement_date) AS INTEGER) = ?
              AND measurement_date < ?
              AND volume IS NOT NULL
              AND volume >= 0
            ORDER BY measurement_date DESC
            LIMIT 36
            """,
            (source_id, measurement_type, target_month, target_date)
        )
        
        if seasonal_data:
            values = [row['volume'] for row in seasonal_data]
            return mean(values)
        
        return 0.0
    
    def _calculate_confidence(self, data_points: int, measured_ratio: float,
                             std_deviation: float, mean_value: float) -> float:
        """Calculate confidence score (0-1) for estimate quality"""
        # Base confidence from data points (Excel: more data = better)
        if data_points >= 12:
            points_score = 1.0
        elif data_points >= 6:
            points_score = 0.8
        elif data_points >= 3:
            points_score = 0.6
        else:
            points_score = 0.3
        
        # Measured vs estimated data
        measured_score = measured_ratio
        
        # Variability score (lower CV = higher confidence)
        if mean_value > 0:
            cv = std_deviation / mean_value  # Coefficient of variation
            if cv < 0.1:
                variability_score = 1.0
            elif cv < 0.3:
                variability_score = 0.8
            elif cv < 0.5:
                variability_score = 0.6
            else:
                variability_score = 0.4
        else:
            variability_score = 0.5
        
        # Weighted combination
        confidence = (points_score * 0.4 + measured_score * 0.3 + variability_score * 0.3)
        
        return min(1.0, max(0.0, confidence))
    
    def _get_default_value(self, source_id: int, measurement_type: str) -> Dict:
        """Get default value when insufficient historical data (Excel: fixed defaults)"""
        # Get source-specific default
        source = self.db.get_water_source(source_id)
        
        default_value = 0.0
        if source:
            # Excel pattern: different defaults per source type
            source_type = source.get('type_name', '').lower()
            
            if 'borehole' in source_type:
                # Excel defaults for boreholes (from analysis)
                default_value = 3000.0  # m³/month
            elif 'river' in source_type:
                default_value = 50000.0  # m³/month
            elif 'underground' in source_type:
                default_value = 13000.0  # m³/month
            
            # Override with source-specific default if available
            if source.get('authorized_volume'):
                default_value = source['authorized_volume'] * 0.7  # 70% utilization
        
        return {
            'estimated_value': default_value,
            'confidence': 0.3,
            'data_points_used': 0,
            'measured_points': 0,
            'quality_flag': 'default',
            'method': 'default',
            'window_months': 0,
            'min_value': default_value,
            'max_value': default_value,
            'std_deviation': 0.0
        }
    
    def fill_missing_measurements(self, start_date: date, end_date: date,
                                  source_ids: List[int] = None,
                                  dry_run: bool = False) -> Dict:
        """
        Fill all missing measurements for a date range (Excel: auto-fill gaps)
        
        Args:
            start_date: Start of period
            end_date: End of period
            source_ids: Optional list of specific sources (None = all active)
            dry_run: If True, don't save, just report what would be filled
        
        Returns:
            Summary of filled measurements
        """
        if source_ids is None:
            sources = self.db.get_water_sources(active_only=True)
            source_ids = [s['source_id'] for s in sources]
        
        filled_count = 0
        estimates = []
        
        current_date = start_date
        while current_date <= end_date:
            for source_id in source_ids:
                # Check if measurement exists
                existing = self.db.execute_query(
                    """
                    SELECT measurement_id FROM measurements
                    WHERE source_id = ? AND measurement_date = ? AND measurement_type = 'inflow'
                    """,
                    (source_id, current_date)
                )
                
                if not existing:
                    # Missing - estimate it
                    estimate = self.estimate_missing_value(
                        source_id, current_date, 'inflow',
                        window_months=12, method='weighted'
                    )
                    
                    if not dry_run and estimate['estimated_value'] > 0:
                        # Insert estimated measurement
                        self.db.execute_insert(
                            """
                            INSERT INTO measurements (
                                measurement_date, measurement_type, source_id,
                                volume, measured, quality_flag, data_source
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (current_date, 'inflow', source_id,
                             estimate['estimated_value'], False,
                             estimate['quality_flag'], 'historical_average')
                        )
                        filled_count += 1
                    
                    estimates.append({
                        'date': current_date,
                        'source_id': source_id,
                        **estimate
                    })
            
            # Next date (monthly)
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        
        return {
            'filled_count': filled_count,
            'total_estimates': len(estimates),
            'dry_run': dry_run,
            'date_range': f"{start_date} to {end_date}",
            'sources_processed': len(source_ids),
            'estimates': estimates
        }
    
    def get_data_quality_report(self, start_date: date, end_date: date) -> Dict:
        """
        Generate data quality report (Excel: quality dashboard)
        Shows measured vs estimated vs missing data
        """
        quality_data = self.db.execute_query(
            """
            SELECT 
                quality_flag,
                COUNT(*) as count,
                AVG(volume) as avg_volume
            FROM measurements
            WHERE measurement_date BETWEEN ? AND ?
            GROUP BY quality_flag
            """,
            (start_date, end_date)
        )
        
        total_measurements = sum(row['count'] for row in quality_data)
        
        quality_breakdown = {}
        for row in quality_data:
            flag = row['quality_flag'] or 'good'
            quality_breakdown[flag] = {
                'count': row['count'],
                'percentage': (row['count'] / total_measurements * 100) if total_measurements > 0 else 0,
                'avg_volume': row['avg_volume']
            }
        
        # Calculate quality score
        weights = {'good': 1.0, 'estimated': 0.7, 'interpolated': 0.5, 'default': 0.3}
        weighted_score = sum(
            quality_breakdown.get(flag, {}).get('percentage', 0) * weight
            for flag, weight in weights.items()
        )
        
        return {
            'period': f"{start_date} to {end_date}",
            'total_measurements': total_measurements,
            'quality_breakdown': quality_breakdown,
            'overall_quality_score': weighted_score / 100.0,
            'quality_rating': self._rate_quality(weighted_score / 100.0)
        }
    
    def _rate_quality(self, score: float) -> str:
        """Rate overall data quality"""
        if score >= 0.9:
            return 'Excellent'
        elif score >= 0.75:
            return 'Good'
        elif score >= 0.6:
            return 'Acceptable'
        elif score >= 0.4:
            return 'Poor'
        else:
            return 'Critical'
    
    def interpolate_gap(self, source_id: int, gap_start: date, gap_end: date,
                       measurement_type: str = 'inflow') -> List[Dict]:
        """
        Interpolate values for a continuous gap (Excel: linear interpolation)
        """
        # Get boundary values
        before = self.db.execute_query(
            """
            SELECT volume, measurement_date FROM measurements
            WHERE source_id = ? AND measurement_type = ?
              AND measurement_date < ?
              AND volume IS NOT NULL
            ORDER BY measurement_date DESC
            LIMIT 1
            """,
            (source_id, measurement_type, gap_start)
        )
        
        after = self.db.execute_query(
            """
            SELECT volume, measurement_date FROM measurements
            WHERE source_id = ? AND measurement_type = ?
              AND measurement_date > ?
              AND volume IS NOT NULL
            ORDER BY measurement_date ASC
            LIMIT 1
            """,
            (source_id, measurement_type, gap_end)
        )
        
        if not before or not after:
            # Can't interpolate - use averaging instead
            return []
        
        before_val = before[0]['volume']
        after_val = after[0]['volume']
        
        before_date = date.fromisoformat(before[0]['measurement_date']) if isinstance(before[0]['measurement_date'], str) else before[0]['measurement_date']
        after_date = date.fromisoformat(after[0]['measurement_date']) if isinstance(after[0]['measurement_date'], str) else after[0]['measurement_date']
        
        # Linear interpolation
        total_days = (after_date - before_date).days
        
        interpolated = []
        current = gap_start
        
        while current <= gap_end:
            days_from_start = (current - before_date).days
            ratio = days_from_start / total_days if total_days > 0 else 0.5
            
            value = before_val + (after_val - before_val) * ratio
            
            interpolated.append({
                'date': current,
                'source_id': source_id,
                'measurement_type': measurement_type,
                'estimated_value': value,
                'quality_flag': 'interpolated',
                'method': 'linear_interpolation'
            })
            
            # Next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        
        return interpolated
