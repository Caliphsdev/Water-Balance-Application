# Borehole Analytics & Monitoring System - Implementation Plan

## Overview
Expand the water balance app to include comprehensive borehole monitoring and analytics with individual borehole dashboards showing 2014-2025 trends, statistics, and alerts.

## Current State Analysis

### Existing Structure
- **Water Sources Table**: Has `type_id` linking to `water_source_types`
- **Current Types**: RIVER, BH (Borehole), UG (Underground), RETURN, RAIN
- **Measurements**: Currently tracks `source_flow` for abstraction volumes
- **Data Quality**: Standalone module in main navigation

### Current Limitation
- All boreholes treated as **abstraction** (water supply) sources only
- No distinction between abstraction, monitoring, and static boreholes
- No water level, quality, or baseline measurements
- No individual borehole analytics

## Proposed Solution - Phase 1: Database Extension

### 1.1 Add Borehole Purpose Classification
**Approach**: Extend `water_sources` table with `source_purpose` field

```sql
ALTER TABLE water_sources ADD COLUMN source_purpose TEXT DEFAULT 'ABSTRACTION';
-- Values: 'ABSTRACTION', 'MONITORING', 'STATIC', 'DUAL_PURPOSE'
```

**Benefits**:
- No disruption to existing abstraction boreholes
- Single table maintains all borehole data
- Easy filtering: `WHERE source_purpose = 'MONITORING'`

### 1.2 Add New Measurement Types
Extend the `measurements` table (already supports multiple types):

**New measurement_type values**:
- `'water_level'` - Water level in meters below ground (monitoring boreholes)
- `'static_level'` - Static water level (baseline, no pumping)
- `'water_quality'` - Quality parameters (requires new fields)
- `'pumping_test'` - Pump test data

**Additional fields needed**:
```sql
ALTER TABLE measurements ADD COLUMN water_level_m REAL;  -- Depth to water
ALTER TABLE measurements ADD COLUMN ph REAL;
ALTER TABLE measurements ADD COLUMN conductivity REAL;  -- μS/cm
ALTER TABLE measurements ADD COLUMN temperature REAL;  -- °C
ALTER TABLE measurements ADD COLUMN turbidity REAL;  -- NTU
ALTER TABLE measurements ADD COLUMN quality_notes TEXT;
```

### 1.3 New Table: Borehole Technical Details
```sql
CREATE TABLE borehole_details (
    detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    collar_elevation REAL,  -- m above sea level
    total_depth REAL,  -- m
    casing_depth REAL,  -- m
    screen_top REAL,  -- m
    screen_bottom REAL,  -- m
    aquifer_type TEXT,  -- 'Fractured rock', 'Alluvial', etc.
    installation_date DATE,
    drilling_contractor TEXT,
    borehole_diameter REAL,  -- mm
    pump_type TEXT,
    pump_depth REAL,  -- m
    design_yield REAL,  -- m³/day
    notes TEXT,
    FOREIGN KEY (source_id) REFERENCES water_sources(source_id)
);
```

## Phase 2: UI Reorganization

### 2.1 Move Data Quality to Settings
**Current**: Standalone navigation item
**New**: Tab in Settings module (alongside General, Database, Alerts, Backup)

**Steps**:
1. Remove `data_quality` from main navigation
2. Add "Data Quality" tab to Settings notebook
3. Keep all functionality intact (historical averaging, quality flags, gap detection)

### 2.2 Add Borehole Analytics Module
**New navigation item**: "Borehole Analytics"

**Layout**:
```
┌─────────────────────────────────────────────────────┐
│  Borehole Analytics Dashboard                      │
├─────────────────────────────────────────────────────┤
│  Borehole: [KDB1 ▼]  Purpose: Abstraction         │
│  Date Range: [2014-01-01] to [2025-11-21]         │
│  [📊 Load Analytics]  [📄 Export Report]          │
├──────────────────┬──────────────────────────────────┤
│  Summary Stats   │  Trend Graphs                   │
│  ──────────────  │  ─────────────                  │
│  Total Records:  │  [Line chart: Monthly volumes]  │
│  ├ Measured: 95% │  [Line chart: Water levels]     │
│  └ Estimated: 5% │  [Line chart: Cumulative]       │
│                  │                                  │
│  Average: 3,450  │  [Bar chart: Yearly comparison] │
│  Min: 2,100      │                                  │
│  Max: 4,800      │                                  │
│  Std Dev: 425    │                                  │
│                  │                                  │
│  Trend: ↗ +2.3%  │  [Scatter: Quality vs Flow]     │
│  per year        │                                  │
├──────────────────┴──────────────────────────────────┤
│  Alerts & Anomalies                                │
│  ⚠️ Declining trend detected (last 6 months)       │
│  ⚠️ 3 missing measurements in 2024                 │
│  ℹ️ Average 5% above historical baseline          │
└─────────────────────────────────────────────────────┘
```

## Phase 3: Borehole Analytics Features

### 3.1 Statistical Analysis
- **Descriptive Stats**: Mean, median, mode, std dev, min, max, quartiles
- **Trend Analysis**: Linear regression, moving averages
- **Seasonality**: Monthly patterns, year-over-year comparison
- **Reliability**: % measured vs estimated, data gaps
- **Correlation**: Flow vs rainfall, levels vs abstraction

### 3.2 Visualizations (Using matplotlib)
1. **Time Series Line Charts**:
   - Monthly abstraction volumes (2014-2025)
   - Water levels over time
   - Cumulative abstraction

2. **Bar Charts**:
   - Yearly comparison
   - Monthly averages by year
   - Data quality breakdown

3. **Scatter Plots**:
   - Flow rate vs water level
   - Quality parameters vs time
   - Abstraction vs rainfall

4. **Box Plots**:
   - Monthly distribution patterns
   - Inter-annual variability

### 3.3 Alert System Integration
**New alert rules for individual boreholes**:

```python
# Declining water level
if trend_slope < -0.5:  # meters/year
    alert('Water level declining', severity='WARNING')

# Low abstraction
if current_month < average * 0.7:
    alert('Abstraction below 70% of average', severity='INFO')

# Data gaps
if days_since_last_measurement > 45:
    alert('No data for 45+ days', severity='CRITICAL')

# Quality threshold
if ph < 6.0 or ph > 9.0:
    alert('pH outside acceptable range', severity='WARNING')
```

## Phase 4: Import Templates

### 4.1 Water Level Template
```
measurement_date | source_code | water_level_m | measured | data_source | notes
2024-01-01      | KDB1        | 12.5          | 1        | Manual      | Normal
```

### 4.2 Water Quality Template
```
measurement_date | source_code | ph   | conductivity | temperature | turbidity | notes
2024-01-01      | KDB1        | 7.2  | 450          | 18.5        | 2.1       | Clear
```

### 4.3 Static Level Template
```
measurement_date | source_code | static_level_m | measured | data_source | notes
2024-01-01      | KDB1        | 15.2           | 1        | Manual      | After 24h rest
```

## Implementation Sequence

### Sprint 1: Database & Backend (Day 1-2)
- [ ] Add `source_purpose` to water_sources
- [ ] Add quality fields to measurements
- [ ] Create borehole_details table
- [ ] Update existing boreholes: `UPDATE water_sources SET source_purpose='ABSTRACTION' WHERE type_id=(SELECT type_id FROM water_source_types WHERE type_code='BH')`
- [ ] Create migration script

### Sprint 2: Data Quality Move (Day 2)
- [ ] Add Data Quality tab to Settings module
- [ ] Remove from main navigation
- [ ] Update all references
- [ ] Test functionality

### Sprint 3: Borehole Analytics Module (Day 3-4)
- [ ] Create `src/ui/borehole_analytics.py`
- [ ] Implement borehole selector (dropdown)
- [ ] Add date range picker
- [ ] Create statistics calculation functions
- [ ] Build summary cards UI

### Sprint 4: Visualization (Day 5-6)
- [ ] Install matplotlib (already in venv)
- [ ] Create chart generation functions
- [ ] Embed charts in Tkinter (FigureCanvasTkAgg)
- [ ] Add interactive controls
- [ ] Export to PNG/PDF

### Sprint 5: Alerts & Import (Day 7)
- [ ] Add borehole-specific alert rules
- [ ] Create water level/quality templates
- [ ] Add import handlers for new measurement types
- [ ] Update column synonyms

## Technical Considerations

### Backward Compatibility
✅ **No breaking changes**:
- Existing abstraction data unchanged
- New fields are nullable
- Default `source_purpose='ABSTRACTION'` for existing records
- Water balance calculations unaffected

### Performance
- Add indexes: `CREATE INDEX idx_measurements_type_date ON measurements(measurement_type, measurement_date)`
- Cache analytics results (similar to balance calculations)
- Paginate large datasets (2014-2025 = 132+ months)

### Data Migration
```python
# Migration script
def migrate_to_borehole_analytics():
    # Add new columns
    db.execute("ALTER TABLE water_sources ADD COLUMN source_purpose TEXT DEFAULT 'ABSTRACTION'")
    db.execute("ALTER TABLE measurements ADD COLUMN water_level_m REAL")
    db.execute("ALTER TABLE measurements ADD COLUMN ph REAL")
    # ... add other fields
    
    # Update existing data
    db.execute("""
        UPDATE water_sources 
        SET source_purpose = 'ABSTRACTION' 
        WHERE type_id = (SELECT type_id FROM water_source_types WHERE type_code='BH')
    """)
    
    print("✅ Migration complete")
```

## Navigation Structure After Implementation

```
Water Balance App
├── 📊 Dashboard              (existing)
├── 💧 Water Sources          (existing)
├── 🏗️ Storage Facilities     (existing)
├── 📏 Measurements           (existing)
├── 🔢 Calculations           (existing)
├── 🔬 Borehole Analytics     (NEW) ⭐
├── 📈 KPIs                   (existing)
├── 📄 Reports                (existing)
├── 📥 Import/Export          (existing)
├── ⚙️ Settings               (existing)
│   ├── General
│   ├── Database
│   ├── Data Quality          (MOVED FROM MAIN NAV) ⭐
│   ├── Alerts
│   └── Backup
└── ❓ Help                   (existing)
```

## Client Deliverables

1. **Individual Borehole Dashboard**: Select any borehole, view full history
2. **Trend Analysis**: 2014-2025 data with visual charts
3. **Statistics**: Average, min, max, trends, anomalies
4. **Alert System**: Declining levels, data gaps, quality issues
5. **Three Borehole Types**: Abstraction, Monitoring, Static
6. **Historical Data**: Support for 10+ years of measurements
7. **Export Reports**: PDF/Excel with charts and data

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking water balance calculations | Keep abstraction logic separate, use `source_purpose` filter |
| Large dataset performance | Pagination, caching, indexed queries |
| Complex UI | Phased rollout, start with basic stats then add charts |
| Data migration errors | Create backup before migration, rollback script |
| User confusion (3 borehole types) | Clear labeling, help documentation, training |

## Success Metrics

- ✅ All existing abstraction data works unchanged
- ✅ Can view 10+ years of data for any borehole
- ✅ Analytics load in <2 seconds
- ✅ Can distinguish and filter by borehole purpose
- ✅ Alerts trigger for declining trends/gaps
- ✅ Export reports with charts

## Next Steps

**Immediate**:
1. Review and approve this plan
2. Create database backup
3. Start with Sprint 1 (database extension)

**Questions for Client**:
1. What water quality parameters are most important? (pH, conductivity, temperature, turbidity, dissolved oxygen, TDS?)
2. Historical data: Do you have 2014-2025 data ready to import?
3. How many boreholes total? (abstraction + monitoring + static)
4. Alert thresholds: What defines "declining" or "concerning" levels?
5. Export format preference: PDF, Excel, or both?

---

**Ready to implement?** Start with database schema updates or need clarification on any phase?
