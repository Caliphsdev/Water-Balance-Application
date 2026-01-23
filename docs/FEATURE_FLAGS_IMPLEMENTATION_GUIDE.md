# 🎯 Feature Flags & Plugin Architecture Setup Guide

**Quick Reference for Implementing Non-Disruptive Future Features**

---

## What This Solves

✅ **Add new features without breaking existing code**  
✅ **Enable/disable features via config, not code**  
✅ **Tier features by subscription level (Standard → Professional → Enterprise)**  
✅ **A/B test features before full rollout**  
✅ **Showcase upcoming features as "Under Development"**

---

## Architecture Overview

```
┌─ Current (UNCHANGED) ─────────────────────┐
│ src/ui/                (dashboards)       │
│ src/utils/             (calculators)      │
│ src/database/          (DB logic)         │
│ config/app_config.yaml (existing config)  │
└──────────────────────────────────────────┘
         ↓ (NOT MODIFIED)
┌─ New (ADDITIVE ONLY) ──────────────────────┐
│ src/features/                              │
│ ├── compliance/        (NEW: reporting)    │
│ ├── alerts/            (NEW: warnings)     │
│ ├── air_quality/       (NEW: sustainability)
│ ├── analytics/         (NEW: insights)     │
│ ├── exports/           (NEW: data export)  │
│ └── __init__.py        (loader)            │
│                                            │
│ config/feature_flags.yaml (NEW: control)   │
└────────────────────────────────────────────┘
```

---

## Step 1: Feature Flag Configuration

**File:** `config/feature_flags.yaml` (NEW)

```yaml
# Feature Flags - Control which features are enabled
# Set to 'false' to completely disable a feature (zero overhead)
# Set to 'true' to enable feature in production

features:
  # Current Features (Always True)
  core_calculations: true
  flow_diagrams: true
  pump_transfers: true
  
  # Q2 2026 Features
  compliance_reporting: false        # Set to true in May 2026
  alert_system: false               # Set to true in May 2026
  
  # Q3 2026 Features  
  air_quality_monitoring: false     # Set to true in Aug 2026
  advanced_analytics: false         # Set to true in Aug 2026
  
  # Q4 2026 Features
  predictive_analytics: false       # Set to true in Nov 2026
  multi_site_management: false      # Set to true in Nov 2026
  
  # Enterprise Features
  rest_api: false                   # Set to true for Enterprise tier
  custom_report_builder: false
  integrations: false

# Tier-Based Feature Sets (Optional: For automatic tier assignment)
tier_features:
  standard:
    - core_calculations
    - flow_diagrams
    - pump_transfers
    - basic_export
  
  professional:
    - core_calculations
    - flow_diagrams
    - pump_transfers
    - basic_export
    - compliance_reporting
    - alert_system
    - air_quality_monitoring
    - advanced_analytics
  
  enterprise:
    - core_calculations
    - flow_diagrams
    - pump_transfers
    - basic_export
    - compliance_reporting
    - alert_system
    - air_quality_monitoring
    - advanced_analytics
    - predictive_analytics
    - multi_site_management
    - rest_api
    - custom_report_builder
    - integrations

# Demo Mode - Show previews of unreleased features
demo_mode: false  # Enable on staging/demo servers
demo_features:
    - compliance_reporting
    - alert_system
    - air_quality_monitoring
```

**Update main config:** `config/app_config.yaml`

```yaml
# Existing config...

licensing:
  # Current licensing settings...
  current_tier: 'standard'  # 'standard', 'professional', 'enterprise'

feature_flags_path: 'config/feature_flags.yaml'
```

---

## Step 2: Feature Flag Loader

**File:** `src/utils/feature_manager.py` (NEW)

```python
"""
Feature Manager - Load and check feature flags at runtime.

This module provides non-intrusive feature enablement:
- Disabled features consume zero resources
- Features can be toggled without app restart
- Tier-based access control integrated
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from typing import Dict, List, Set
from utils.config_manager import config
from utils.app_logger import logger


class FeatureManager:
    """Centralized feature flag management.
    
    Usage:
        from utils.feature_manager import get_feature_manager
        fm = get_feature_manager()
        
        if fm.is_enabled('compliance_reporting'):
            # Load compliance module
            pass
    
    Features can be enabled/disabled via:
    1. config/feature_flags.yaml
    2. Dynamically at runtime (for testing)
    3. Per user via licensing tier
    """
    
    def __init__(self):
        """Initialize feature manager with flags from config file."""
        self._flags = {}
        self._tier_features = {}
        self._demo_features = set()
        self._current_tier = 'standard'
        self._reload_flags()
    
    def _reload_flags(self):
        """Load feature flags from YAML configuration file."""
        try:
            flags_path = Path(config.get('feature_flags_path', 'config/feature_flags.yaml'))
            
            if flags_path.exists():
                with open(flags_path, 'r') as f:
                    data = yaml.safe_load(f)
                    
                    self._flags = data.get('features', {})
                    self._tier_features = data.get('tier_features', {})
                    
                    if data.get('demo_mode', False):
                        self._demo_features = set(data.get('demo_features', []))
                    
                    logger.debug(f"Loaded {len(self._flags)} feature flags")
            else:
                logger.warning(f"Feature flags file not found: {flags_path}")
                self._flags = {}
                
        except Exception as e:
            logger.error(f"Error loading feature flags: {e}")
            self._flags = {}
    
    def is_enabled(self, feature_name: str) -> bool:
        """Check if feature is enabled.
        
        Args:
            feature_name: Feature key (e.g., 'compliance_reporting')
        
        Returns:
            True if feature is enabled, False otherwise
        
        Example:
            if feature_manager.is_enabled('alert_system'):
                alert_engine = AlertEngine()  # Load only if enabled
        """
        # Always enabled for current tier
        if feature_name in self.get_tier_features(self._current_tier):
            return True
        
        # Check demo mode
        if feature_name in self._demo_features:
            return True
        
        # Check explicit flag
        return self._flags.get(feature_name, False)
    
    def get_tier_features(self, tier: str) -> List[str]:
        """Get list of features available for a tier.
        
        Args:
            tier: 'standard', 'professional', or 'enterprise'
        
        Returns:
            List of feature names available in tier
        """
        return self._tier_features.get(tier, [])
    
    def set_tier(self, tier: str):
        """Set current user tier (for licensing integration).
        
        Args:
            tier: 'standard', 'professional', or 'enterprise'
        """
        if tier in self._tier_features:
            self._current_tier = tier
            logger.info(f"Feature tier set to: {tier}")
        else:
            logger.warning(f"Invalid tier: {tier}")
    
    def enable_feature(self, feature_name: str):
        """Temporarily enable feature at runtime (for testing).
        
        Args:
            feature_name: Feature to enable
        """
        self._flags[feature_name] = True
        logger.debug(f"Feature enabled (runtime): {feature_name}")
    
    def disable_feature(self, feature_name: str):
        """Temporarily disable feature at runtime (for testing).
        
        Args:
            feature_name: Feature to disable
        """
        self._flags[feature_name] = False
        logger.debug(f"Feature disabled (runtime): {feature_name}")
    
    def get_all_features(self) -> Dict[str, bool]:
        """Get status of all features.
        
        Returns:
            Dict mapping feature names to enabled status
        """
        all_features = {}
        for feature in self._flags.keys():
            all_features[feature] = self.is_enabled(feature)
        return all_features
    
    def reload(self):
        """Reload feature flags from file (after config change)."""
        self._reload_flags()
        logger.info("Feature flags reloaded")


# Singleton instance
_feature_manager = None

def get_feature_manager() -> FeatureManager:
    """Get singleton feature manager instance."""
    global _feature_manager
    if _feature_manager is None:
        _feature_manager = FeatureManager()
    return _feature_manager


def reset_feature_manager():
    """Reset singleton (for testing)."""
    global _feature_manager
    _feature_manager = None


if __name__ == '__main__':
    # Quick test
    fm = get_feature_manager()
    print("Feature Status:")
    for feature, enabled in fm.get_all_features().items():
        status = "✅ ENABLED" if enabled else "❌ DISABLED"
        print(f"  {feature:30s} {status}")
```

---

## Step 3: Feature Plugin Loader

**File:** `src/features/__init__.py` (NEW)

```python
"""
Feature Plugin System - Dynamically load enabled features only.

This module implements a non-intrusive plugin architecture:
- Only imports enabled features (zero import overhead when disabled)
- Prevents circular imports and coupling
- Enables A/B testing and staged rollouts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Any, Optional
from utils.feature_manager import get_feature_manager
from utils.app_logger import logger


class FeatureLoader:
    """Load and manage feature modules.
    
    Usage:
        from features import get_enabled_features
        features = get_enabled_features()
        
        if 'alerts' in features:
            alert_engine = features['alerts']['engine']
        
        if 'compliance' in features:
            report_gen = features['compliance']['generator']
    """
    
    def __init__(self):
        """Initialize feature loader."""
        self.features = {}
        self.fm = get_feature_manager()
    
    def load(self) -> Dict[str, Dict[str, Any]]:
        """Load all enabled features.
        
        Returns:
            Dict mapping feature names to feature modules
            
            Example:
            {
                'compliance': {
                    'engine': ComplianceEngine(),
                    'validator': ComplianceValidator(),
                    ...
                },
                'alerts': {
                    'engine': AlertEngine(),
                    'detector': AnomalyDetector(),
                    ...
                }
            }
        """
        self.features = {}
        
        # Load compliance feature (Q2 2026)
        if self.fm.is_enabled('compliance_reporting'):
            try:
                from .compliance import ComplianceEngine
                self.features['compliance'] = {
                    'engine': ComplianceEngine(),
                }
                logger.info("✅ Compliance feature loaded")
            except ImportError as e:
                logger.warning(f"Could not load compliance feature: {e}")
        
        # Load alert feature (Q2 2026)
        if self.fm.is_enabled('alert_system'):
            try:
                from .alerts import AlertEngine, AnomalyDetector
                self.features['alerts'] = {
                    'engine': AlertEngine(),
                    'detector': AnomalyDetector(),
                }
                logger.info("✅ Alert feature loaded")
            except ImportError as e:
                logger.warning(f"Could not load alert feature: {e}")
        
        # Load air quality feature (Q3 2026)
        if self.fm.is_enabled('air_quality_monitoring'):
            try:
                from .air_quality import AirQualityEngine, SustainabilityCalculator
                self.features['air_quality'] = {
                    'engine': AirQualityEngine(),
                    'sustainability': SustainabilityCalculator(),
                }
                logger.info("✅ Air Quality feature loaded")
            except ImportError as e:
                logger.warning(f"Could not load air quality feature: {e}")
        
        # Load analytics feature (Q3 2026)
        if self.fm.is_enabled('advanced_analytics'):
            try:
                from .analytics import AnalyticsEngine, AnomalyDetector, DataQualityChecker
                self.features['analytics'] = {
                    'engine': AnalyticsEngine(),
                    'anomaly_detector': AnomalyDetector(),
                    'quality_checker': DataQualityChecker(),
                }
                logger.info("✅ Analytics feature loaded")
            except ImportError as e:
                logger.warning(f"Could not load analytics feature: {e}")
        
        # Load export feature (Q2 2026)
        if self.fm.is_enabled('export_import_suite'):
            try:
                from .exports import ExportEngine, ImportEngine
                self.features['exports'] = {
                    'export_engine': ExportEngine(),
                    'import_engine': ImportEngine(),
                }
                logger.info("✅ Export/Import feature loaded")
            except ImportError as e:
                logger.warning(f"Could not load export feature: {e}")
        
        logger.info(f"Loaded {len(self.features)} enabled features")
        return self.features
    
    def get(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Get feature module by name.
        
        Args:
            feature_name: Feature key (e.g., 'alerts')
        
        Returns:
            Feature module dict, or None if not loaded
        """
        return self.features.get(feature_name)
    
    def is_loaded(self, feature_name: str) -> bool:
        """Check if feature is loaded.
        
        Args:
            feature_name: Feature key
        
        Returns:
            True if feature loaded and enabled
        """
        return feature_name in self.features


# Singleton loader
_loader = None

def get_enabled_features() -> Dict[str, Dict[str, Any]]:
    """Get all enabled features (lazy load).
    
    Usage:
        features = get_enabled_features()
        if 'alerts' in features:
            engine = features['alerts']['engine']
    """
    global _loader
    if _loader is None:
        _loader = FeatureLoader()
        _loader.load()
    return _loader.features


def reload_features():
    """Reload features (after config change)."""
    global _loader
    _loader = None
    return get_enabled_features()
```

---

## Step 4: Update Main Window Sidebar

**File:** `src/ui/main_window.py` (MODIFY)

Add to sidebar creation method:

```python
def _create_sidebar(self):
    """Create sidebar with existing + dynamic features."""
    # Existing items (unchanged)
    self._add_sidebar_item("Dashboard", self._show_dashboard)
    self._add_sidebar_item("Calculations", self._show_calculations)
    self._add_sidebar_item("Flow Diagrams", self._show_flow_diagrams)
    self._add_sidebar_item("Analytics", self._show_analytics)
    
    # ============ NEW: Dynamic features ============
    from features import get_enabled_features
    from utils.feature_manager import get_feature_manager
    
    enabled_features = get_enabled_features()
    fm = get_feature_manager()
    
    # Compliance feature (Q2 2026)
    if fm.is_enabled('compliance_reporting'):
        self._add_sidebar_item("📋 Compliance", self._show_compliance)
    
    # Alert feature (Q2 2026)
    if fm.is_enabled('alert_system'):
        self._add_sidebar_item("🚨 Alerts", self._show_alerts)
    
    # Air quality feature (Q3 2026)
    if fm.is_enabled('air_quality_monitoring'):
        self._add_sidebar_item("🌍 Sustainability", self._show_sustainability)
    
    # ============ Coming Soon / Roadmap ============
    self._add_sidebar_item("🔮 Coming Soon", self._show_roadmap)
    
    # Settings and Help
    self._add_sidebar_item("Settings", self._show_settings)
    self._add_sidebar_item("Help", self._show_help)
```

---

## Step 5: "Coming Soon" Tab Implementation

**File:** `src/ui/roadmap_preview.py` (NEW)

```python
"""
Roadmap Preview - Beautiful showcase of upcoming features.

Displays features under development as a sales/marketing tool.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from tkinter import ttk
from utils.app_logger import logger


class RoadmapPreview:
    """Display future features roadmap with launch dates and pricing tiers."""
    
    FEATURES = [
        {
            'name': 'Compliance Reporting',
            'icon': '📋',
            'description': 'Automate EPA, state, and mining board regulatory reporting',
            'launch_date': 'Q2 2026',
            'tier': 'Professional',
            'benefits': [
                '✅ Pre-built regulatory templates',
                '✅ Validation before submission',
                '✅ 80% reduction in manual work'
            ]
        },
        {
            'name': 'Intelligent Alerts',
            'icon': '🚨',
            'description': 'Real-time monitoring with multi-channel notifications',
            'launch_date': 'Q2 2026',
            'tier': 'Professional',
            'benefits': [
                '✅ 5 alert categories',
                '✅ Email, SMS, Slack integration',
                '✅ Smart escalation'
            ]
        },
        {
            'name': 'Air Quality & Sustainability',
            'icon': '🌍',
            'description': 'Track environmental impact and sustainability metrics',
            'launch_date': 'Q3 2026',
            'tier': 'Professional',
            'benefits': [
                '✅ Carbon footprint calculation',
                '✅ Air quality monitoring',
                '✅ Facility efficiency scoring'
            ]
        },
        {
            'name': 'Advanced Analytics',
            'icon': '📊',
            'description': 'Deep-dive analysis with trend forecasting and benchmarking',
            'launch_date': 'Q3 2026',
            'tier': 'Professional',
            'benefits': [
                '✅ Trend analysis & forecasting',
                '✅ Facility benchmarking',
                '✅ Anomaly detection'
            ]
        },
        {
            'name': 'Export/Import Suite',
            'icon': '📤',
            'description': 'Flexible data export/import in multiple formats',
            'launch_date': 'Q2 2026',
            'tier': 'Professional',
            'benefits': [
                '✅ Excel, PDF, CSV, JSON exports',
                '✅ Scheduled reports',
                '✅ Email distribution'
            ]
        },
        {
            'name': 'Multi-Site Management',
            'icon': '🏢',
            'description': 'Manage multiple mines from unified dashboard',
            'launch_date': 'Q4 2026',
            'tier': 'Enterprise',
            'benefits': [
                '✅ Consolidated dashboards',
                '✅ Cross-site analytics',
                '✅ Centralized admin'
            ]
        },
        {
            'name': 'REST API & Webhooks',
            'icon': '🔌',
            'description': 'Integrate with external systems and build custom apps',
            'launch_date': 'Q4 2026',
            'tier': 'Enterprise',
            'benefits': [
                '✅ Real-time data access',
                '✅ Event webhooks',
                '✅ Custom integrations'
            ]
        },
        {
            'name': 'Custom Report Builder',
            'icon': '✏️',
            'description': 'Build professional reports without coding',
            'launch_date': 'Q4 2026',
            'tier': 'Enterprise',
            'benefits': [
                '✅ Drag-and-drop interface',
                '✅ Template library',
                '✅ Conditional formatting'
            ]
        },
    ]
    
    def __init__(self, parent):
        """Initialize roadmap preview."""
        self.parent = parent
        self.frame = None
    
    def render(self, parent_frame):
        """Render roadmap preview in given frame."""
        self.frame = parent_frame
        
        # Title
        title = tk.Label(
            parent_frame,
            text="🚀 Water Balance Application - Future Roadmap 2026+",
            font=("Arial", 16, "bold"),
            fg="#2E86AB"
        )
        title.pack(pady=20)
        
        # Subtitle
        subtitle = tk.Label(
            parent_frame,
            text="Exciting new features coming soon to your suite",
            font=("Arial", 11),
            fg="#666"
        )
        subtitle.pack(pady=(0, 20))
        
        # Create scrollable frame
        canvas = tk.Canvas(parent_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.scroll_region)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create feature cards
        for feature in self.FEATURES:
            self._create_feature_card(scrollable_frame, feature)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Bottom CTA
        cta_frame = tk.Frame(parent_frame, bg="#f0f0f0")
        cta_frame.pack(fill="x", padx=0, pady=0)
        
        cta_label = tk.Label(
            cta_frame,
            text="📧 Want early access? Contact sales@waterbalance.app",
            font=("Arial", 10),
            bg="#f0f0f0",
            fg="#2E86AB",
            padx=20,
            pady=10
        )
        cta_label.pack()
    
    def _create_feature_card(self, parent, feature):
        """Create a feature card."""
        card = tk.Frame(parent, bg="white", relief="solid", bd=1)
        card.pack(fill="x", pady=10, padx=5)
        
        # Header
        header = tk.Frame(card, bg="#f9f9f9")
        header.pack(fill="x", padx=15, pady=10)
        
        icon_name = tk.Label(header, text=f"{feature['icon']} {feature['name']}", 
                             font=("Arial", 12, "bold"), bg="#f9f9f9")
        icon_name.pack(side="left")
        
        tier_label = tk.Label(header, text=feature['tier'],
                             font=("Arial", 9, "bold"),
                             bg=self._tier_color(feature['tier']),
                             fg="white",
                             padx=8, pady=2)
        tier_label.pack(side="right")
        
        # Description
        desc = tk.Label(card, text=feature['description'],
                       font=("Arial", 10), bg="white", wraplength=400,
                       justify="left")
        desc.pack(fill="x", padx=15, pady=(0, 10))
        
        # Benefits
        for benefit in feature['benefits']:
            b = tk.Label(card, text=benefit, font=("Arial", 9),
                        bg="white", fg="#4a4a4a", justify="left")
            b.pack(anchor="w", padx=15)
        
        # Launch date
        launch = tk.Label(card, text=f"🎯 Available: {feature['launch_date']}",
                         font=("Arial", 9, "italic"), bg="white", fg="#888")
        launch.pack(anchor="w", padx=15, pady=(5, 10))
    
    @staticmethod
    def _tier_color(tier):
        """Get color for tier badge."""
        colors = {
            'Standard': '#4CAF50',
            'Professional': '#2196F3',
            'Enterprise': '#FF9800'
        }
        return colors.get(tier, '#999')
```

---

## Step 6: Update Database Schema Migration

**File:** `src/database/schema.py` (MODIFY)

Add to schema creation:

```python
def create_feature_tables(self):
    """Create tables for enabled features only.
    
    This is backward-compatible - tables only created if feature enabled.
    """
    from utils.feature_manager import get_feature_manager
    fm = get_feature_manager()
    
    # Create Compliance tables if enabled
    if fm.is_enabled('compliance_reporting'):
        self._create_compliance_tables()
    
    # Create Alert tables if enabled
    if fm.is_enabled('alert_system'):
        self._create_alert_tables()
    
    # Create Air Quality tables if enabled
    if fm.is_enabled('air_quality_monitoring'):
        self._create_air_quality_tables()
    
    # etc.
```

---

## Testing Feature Flags

**File:** `tests/test_feature_manager.py` (NEW)

```python
import pytest
from utils.feature_manager import get_feature_manager, reset_feature_manager


def test_feature_enabled():
    """Test checking if feature is enabled."""
    reset_feature_manager()
    fm = get_feature_manager()
    
    # Core features should always be enabled
    assert fm.is_enabled('core_calculations')
    
    # New features should be disabled by default
    assert not fm.is_enabled('compliance_reporting')


def test_feature_enable_runtime():
    """Test enabling feature at runtime."""
    reset_feature_manager()
    fm = get_feature_manager()
    
    assert not fm.is_enabled('alert_system')
    fm.enable_feature('alert_system')
    assert fm.is_enabled('alert_system')


def test_tier_features():
    """Test tier-based feature access."""
    reset_feature_manager()
    fm = get_feature_manager()
    
    standard_features = fm.get_tier_features('standard')
    professional_features = fm.get_tier_features('professional')
    
    # Professional should have more features
    assert len(professional_features) > len(standard_features)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

---

## Deployment Checklist

### Before Q2 2026 Launch

- [ ] Feature flag system implemented & tested
- [ ] Plugin loader working for compliance & alerts
- [ ] Database schema migration supports new tables
- [ ] "Coming Soon" roadmap UI implemented
- [ ] Config files updated with feature flags
- [ ] Compliance feature 90% complete
- [ ] Alert feature 90% complete
- [ ] All new tests passing
- [ ] Documentation updated
- [ ] Sales team trained on new tiers

### Launch Day (Q2 2026)

- [ ] Set `compliance_reporting: true` in feature_flags.yaml
- [ ] Set `alert_system: true` in feature_flags.yaml
- [ ] Deploy to production
- [ ] Monitor for errors 24/7
- [ ] Send announcement email to users
- [ ] Update website pricing & features
- [ ] Support team briefing

### Post-Launch Monitoring

- [ ] Check feature adoption (% users upgrading)
- [ ] Monitor performance (no degradation)
- [ ] Gather user feedback
- [ ] Fix any reported issues
- [ ] Prepare Q3 features for development

---

## Quick Reference: Using Features in Code

```python
# Check if feature is enabled
from utils.feature_manager import get_feature_manager
fm = get_feature_manager()

if fm.is_enabled('compliance_reporting'):
    # Load compliance module
    from features.compliance import ComplianceEngine
    engine = ComplianceEngine()
    # Use compliance features
    reports = engine.generate_reports(facility, date_range)

# Or use feature loader
from features import get_enabled_features
features = get_enabled_features()

if 'alerts' in features:
    alert_engine = features['alerts']['engine']
    # Use alerts
    alert_engine.check_metrics()
```

---

**Status:** Ready to implement  
**Effort:** 3-5 days for architecture + "Coming Soon" UI  
**Risk:** Very Low (non-disruptive, all additive)  
**Next Step:** Set up feature flags directory and implement Step 1

