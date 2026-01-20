"""
Alert Management System
Automatic monitoring and alerting for water balance metrics
"""

import sys
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from utils.ui_notify import notifier
from utils.app_logger import logger


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertRule:
    """Alert rule definition"""
    
    def __init__(self, rule_data: Dict):
        """Initialize alert rule from database row"""
        self.rule_id = rule_data['rule_id']
        self.rule_code = rule_data['rule_code']
        self.rule_name = rule_data['rule_name']
        self.rule_category = rule_data['rule_category']
        self.metric_name = rule_data['metric_name']
        self.condition_operator = rule_data['condition_operator']
        self.threshold_value = rule_data['threshold_value']
        self.threshold_unit = rule_data.get('threshold_unit', '')
        self.severity = rule_data['severity']
        self.alert_title = rule_data['alert_title']
        self.alert_message = rule_data['alert_message']
        self.show_popup = bool(rule_data.get('show_popup', 1))
        self.send_email = bool(rule_data.get('send_email', 0))
        self.email_recipients = rule_data.get('email_recipients', '')
        self.auto_resolve = bool(rule_data.get('auto_resolve', 1))
        self.active = bool(rule_data.get('active', 1))
        self.priority = rule_data.get('priority', 3)
        self.description = rule_data.get('description', '')
    
    def evaluate(self, metric_value: float) -> bool:
        """
        Evaluate if metric value triggers this rule
        
        Args:
            metric_value: Current value of the metric
        
        Returns:
            True if condition is met, False otherwise
        """
        if metric_value is None:
            return False
        
        try:
            if self.condition_operator == '<':
                return metric_value < self.threshold_value
            elif self.condition_operator == '>':
                return metric_value > self.threshold_value
            elif self.condition_operator == '<=':
                return metric_value <= self.threshold_value
            elif self.condition_operator == '>=':
                return metric_value >= self.threshold_value
            elif self.condition_operator == '=':
                return abs(metric_value - self.threshold_value) < 0.01
            else:
                logger.warning(f"Unknown operator {self.condition_operator} in rule {self.rule_code}")
                return False
        except (TypeError, ValueError) as e:
            logger.error(f"Error evaluating rule {self.rule_code}: {e}")
            return False
    
    def format_message(self, metric_value: float) -> str:
        """Format alert message with actual metric value"""
        try:
            return self.alert_message.format(metric_value=metric_value, threshold=self.threshold_value)
        except (KeyError, ValueError):
            return self.alert_message


class AlertManager:
    """Centralized alert management system"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize alert manager"""
        if not hasattr(self, '_initialized'):
            self.db = DatabaseManager()
            self._alert_cache = {}
            self._rules_cache = None
            self._last_rules_load = None
            self._initialized = True
    
    def load_rules(self, force_reload: bool = False, include_disabled: bool = False) -> List[AlertRule]:
        """
        Load alert rules from database
        
        Args:
            force_reload: Force reload even if cached
            include_disabled: Include disabled rules (default: False)
        
        Returns:
            List of AlertRule objects
        """
        # Use cache if available and recent (within 5 minutes) and not including disabled
        if not force_reload and not include_disabled and self._rules_cache and self._last_rules_load:
            elapsed = (datetime.now() - self._last_rules_load).total_seconds()
            if elapsed < 300:  # 5 minutes
                return self._rules_cache
        
        if include_disabled:
            rules_data = self.db.execute_query(
                "SELECT * FROM alert_rules ORDER BY priority ASC, rule_id ASC"
            )
        else:
            rules_data = self.db.execute_query(
                "SELECT * FROM alert_rules WHERE active = 1 ORDER BY priority ASC, rule_id ASC"
            )
        
        rules = [AlertRule(rule) for rule in rules_data]
        
        # Only cache active rules
        if not include_disabled:
            self._rules_cache = rules
            self._last_rules_load = datetime.now()
        
        logger.info(f"Loaded {len(rules)} alert rules (include_disabled={include_disabled})")
        return rules
    
    def check_storage_security(self, calculation_date: date, security_metrics: Dict) -> List[Dict]:
        """
        Check storage security metrics against alert rules
        
        Args:
            calculation_date: Date of calculation
            security_metrics: Dict with days_cover, days_to_minimum, storage_utilization, etc.
        
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        rules = self.load_rules()
        
        # Map metrics to rule metric names
        metrics_map = {
            'days_cover': security_metrics.get('days_cover'),
            'days_to_minimum': security_metrics.get('days_to_minimum'),
            'storage_utilization': security_metrics.get('storage_utilization_pct'),
            'current_storage_m3': security_metrics.get('current_storage_m3'),
        }
        
        for rule in rules:
            if rule.rule_category != 'storage':
                continue
            
            metric_value = metrics_map.get(rule.metric_name)
            if metric_value is None:
                continue
            
            if rule.evaluate(metric_value):
                alert = self._trigger_alert(rule, metric_value, calculation_date)
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    def check_facility_level(self, calculation_date: date, facility_id: int, 
                            level_percent: float, volume: float) -> List[Dict]:
        """
        Check facility level against alert rules
        
        Args:
            calculation_date: Date of measurement
            facility_id: Facility ID
            level_percent: Current level as percentage
            volume: Current volume in m³
        
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        rules = self.load_rules()
        
        metrics_map = {
            'level_percent': level_percent,
            'volume_m3': volume,
        }
        
        for rule in rules:
            if rule.rule_category != 'level':
                continue
            
            metric_value = metrics_map.get(rule.metric_name)
            if metric_value is None:
                continue
            
            if rule.evaluate(metric_value):
                alert = self._trigger_alert(rule, metric_value, calculation_date, facility_id=facility_id)
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    def check_compliance(self, calculation_date: date, compliance_metrics: Dict) -> List[Dict]:
        """
        Check compliance metrics against alert rules
        
        Args:
            calculation_date: Date of calculation
            compliance_metrics: Dict with closure_error_pct, violations_count, etc.
        
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        rules = self.load_rules()
        
        metrics_map = {
            'closure_error_pct': compliance_metrics.get('closure_error_pct'),
            'violations_count': compliance_metrics.get('violations_count'),
            'utilization_pct': compliance_metrics.get('overall_utilization_pct'),
        }
        
        for rule in rules:
            if rule.rule_category != 'compliance':
                continue
            
            metric_value = metrics_map.get(rule.metric_name)
            if metric_value is None:
                continue
            
            if rule.evaluate(metric_value):
                alert = self._trigger_alert(rule, metric_value, calculation_date)
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    def _trigger_alert(self, rule: AlertRule, metric_value: float, 
                      calculation_date: date, facility_id: int = None, 
                      source_id: int = None) -> Dict:
        """
        Trigger an alert and save to database
        
        Args:
            rule: AlertRule that triggered
            metric_value: Actual value that triggered the alert
            calculation_date: Date of calculation
            facility_id: Optional facility ID
            source_id: Optional source ID
        
        Returns:
            Alert data dict
        """
        # Format message with actual values
        formatted_message = rule.format_message(metric_value)
        
        # Check if similar alert already active (prevent duplicates)
        existing = self.db.execute_query("""
            SELECT alert_id FROM alerts
            WHERE rule_id = ? AND status = 'active'
            AND calculation_date = ?
            AND (facility_id IS NULL OR facility_id = ?)
            AND (source_id IS NULL OR source_id = ?)
        """, (rule.rule_id, calculation_date, facility_id, source_id))
        
        if existing:
            # Update existing alert
            alert_id = existing[0]['alert_id']
            self.db.execute_update("""
                UPDATE alerts
                SET metric_value = ?, last_checked_at = ?
                WHERE alert_id = ?
            """, (metric_value, datetime.now(), alert_id))
            
            logger.debug(f"Updated existing alert {alert_id} for rule {rule.rule_code}")
        else:
            # Create new alert
            alert_data = {
                'rule_id': rule.rule_id,
                'severity': rule.severity,
                'title': rule.alert_title,
                'message': formatted_message,
                'metric_value': metric_value,
                'threshold_value': rule.threshold_value,
                'calculation_date': calculation_date,
                'facility_id': facility_id,
                'source_id': source_id,
                'status': 'active',
            }
            
            query = """
                INSERT INTO alerts (
                    rule_id, severity, title, message, metric_value, threshold_value,
                    calculation_date, facility_id, source_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            alert_id = self.db.execute_insert(query, (
                alert_data['rule_id'], alert_data['severity'], alert_data['title'],
                alert_data['message'], alert_data['metric_value'], alert_data['threshold_value'],
                alert_data['calculation_date'], alert_data['facility_id'], 
                alert_data['source_id'], alert_data['status']
            ))
            
            alert_data['alert_id'] = alert_id
            
            logger.info(f"Triggered {rule.severity} alert: {rule.rule_name} (value={metric_value:.1f})")
            
            # Show popup notification if configured
            if rule.show_popup:
                self._show_notification(rule.severity, rule.alert_title, formatted_message)
        
        # Return alert summary
        return {
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'severity': rule.severity,
            'title': rule.alert_title,
            'message': formatted_message,
            'metric_value': metric_value,
            'threshold_value': rule.threshold_value,
        }
    
    def _show_notification(self, severity: str, title: str, message: str):
        """Show UI notification for alert"""
        if severity == 'critical':
            notifier.error(message, title=title, show_dialog=True)
        elif severity == 'warning':
            notifier.warning(message, title=title, show_dialog=True)
        else:
            notifier.info(message, title=title, show_dialog=False)
    
    def auto_resolve_alerts(self, calculation_date: date):
        """
        Auto-resolve alerts when conditions no longer met
        
        Args:
            calculation_date: Date to check
        """
        # Get all active alerts with auto_resolve enabled
        active_alerts = self.db.execute_query("""
            SELECT 
                a.*, 
                r.rule_code, r.rule_name, r.rule_category,
                r.metric_name, r.condition_operator, r.threshold_value, r.threshold_unit,
                r.severity, r.alert_title, r.alert_message,
                r.show_popup, r.send_email, r.email_recipients,
                r.auto_resolve, r.active, r.priority, r.description
            FROM alerts a
            JOIN alert_rules r ON a.rule_id = r.rule_id
            WHERE a.status = 'active' AND r.auto_resolve = 1
            AND a.calculation_date = ?
        """, (calculation_date,))
        
        for alert in active_alerts:
            # Re-evaluate condition with current metric value
            rule = AlertRule(alert)
            if not rule.evaluate(alert['metric_value']):
                # Condition no longer met, resolve alert
                self.db.execute_update("""
                    UPDATE alerts
                    SET status = 'resolved', resolved_at = ?, resolved_by = 'auto'
                    WHERE alert_id = ?
                """, (datetime.now(), alert['alert_id']))
                
                logger.info(f"Auto-resolved alert {alert['alert_id']} - condition no longer met")
    
    def get_active_alerts(self, severity: str = None, limit: int = 100) -> List[Dict]:
        """
        Get active alerts
        
        Args:
            severity: Filter by severity ('info', 'warning', 'critical')
            limit: Maximum number of alerts to return
        
        Returns:
            List of active alert dicts
        """
        if severity:
            query = """
                SELECT a.*, r.rule_name, r.rule_category
                FROM alerts a
                JOIN alert_rules r ON a.rule_id = r.rule_id
                WHERE a.status = 'active' AND a.severity = ?
                ORDER BY a.triggered_at DESC
                LIMIT ?
            """
            return self.db.execute_query(query, (severity, limit))
        else:
            query = """
                SELECT a.*, r.rule_name, r.rule_category
                FROM alerts a
                JOIN alert_rules r ON a.rule_id = r.rule_id
                WHERE a.status = 'active'
                ORDER BY 
                    CASE a.severity
                        WHEN 'critical' THEN 1
                        WHEN 'warning' THEN 2
                        WHEN 'info' THEN 3
                    END,
                    a.triggered_at DESC
                LIMIT ?
            """
            return self.db.execute_query(query, (limit,))
    
    def get_alert_count(self, status: str = 'active', severity: str = None) -> int:
        """
        Get count of alerts by status and severity
        
        Args:
            status: Alert status ('active', 'acknowledged', 'resolved')
            severity: Optional severity filter
        
        Returns:
            Count of matching alerts
        """
        if severity:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM alerts WHERE status = ? AND severity = ?",
                (status, severity)
            )
        else:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM alerts WHERE status = ?",
                (status,)
            )
        
        return result[0]['count'] if result else 0
    
    def acknowledge_alert(self, alert_id: int, user: str = 'user', note: str = None):
        """Acknowledge an alert"""
        self.db.execute_update("""
            UPDATE alerts
            SET status = 'acknowledged', acknowledged_at = ?, acknowledged_by = ?,
                resolution_note = ?
            WHERE alert_id = ?
        """, (datetime.now(), user, note, alert_id))
        
        logger.info(f"Alert {alert_id} acknowledged by {user}")
    
    def resolve_alert(self, alert_id: int, user: str = 'user', note: str = None):
        """Manually resolve an alert"""
        self.db.execute_update("""
            UPDATE alerts
            SET status = 'resolved', resolved_at = ?, resolved_by = ?,
                resolution_note = ?
            WHERE alert_id = ?
        """, (datetime.now(), user, note, alert_id))
        
        logger.info(f"Alert {alert_id} resolved by {user}")
    
    def get_alert_summary(self) -> Dict[str, int]:
        """
        Get summary of alert counts by severity
        
        Returns:
            Dict with counts: {critical: X, warning: Y, info: Z, total: N}
        """
        result = self.db.execute_query("""
            SELECT severity, COUNT(*) as count
            FROM alerts
            WHERE status = 'active'
            GROUP BY severity
        """)
        
        summary = {'critical': 0, 'warning': 0, 'info': 0, 'total': 0}
        
        for row in result:
            summary[row['severity']] = row['count']
            summary['total'] += row['count']
        
        return summary


# Global alert manager instance
alert_manager = AlertManager()
