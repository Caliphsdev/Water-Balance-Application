# Help Documentation - Content Quick Reference

## Tab 1: Overview
**What You'll Find:**
- Water balance fundamentals and equation
- Key concepts explained
- Units used throughout the app (m³, Mm³, mm, m³/tonne)
- Data quality flags (MEASURED, CALCULATED, ESTIMATED, ASSUMED)
- Water balance purpose and use

## Tab 2: Dashboards (NEW!)
**6 Dashboards Covered:**

1. **📊 Main Dashboard**
   - Source count, facility count, capacity, utilization
   - Environmental KPIs (rainfall, evaporation)
   - 6-month trends, closure error tracking
   - System status indicators

2. **💰 KPI Dashboard**
   - Water use efficiency metrics
   - Recycling ratio tracking
   - Source dependency breakdown
   - Storage security (days of supply)
   - Excel parity calculations

3. **📈 Analytics Dashboard**
   - Trend analysis over time
   - Seasonal patterns
   - Year-over-year comparisons
   - Anomaly detection
   - Projection capabilities

4. **📉 Charts Dashboard**
   - Inflow/outflow pie charts
   - Facility utilization bar charts
   - Water balance component stacks
   - Closure error trends
   - Exportable visualizations

5. **🗂️ Flow Diagram Dashboard**
   - Visual mapping of water flows
   - 8 operational areas
   - Manual flow line drawing
   - Excel volume overlays
   - Color-coded flow types (clean/dirty/losses)

6. **📋 Monitoring Dashboard**
   - Real-time measurement tracking
   - Borehole, river, facility level data
   - Data quality scoring
   - Anomaly warnings
   - Historical statistics

## Tab 3: Calculations
**⏱️ TIME PERIOD: MONTHLY**
- All calculations designed for monthly periods
- Default ore: 350,000 tonnes/month
- Default mining water rate: 1.43 m³/tonne
- Default TSF return: 56%

**5-Step Calculation Process:**
1. Calculate Total Inflows (6 sources)
2. Calculate Total Outflows (8 categories)
3. Calculate Storage Changes (per facility)
4. Calculate Closure Error (±5% threshold)
5. Generate Results

**Closure Error Status:**
- ✅ CLOSED: Error ≤5% (acceptable)
- ⚠️ OPEN: Error >5% (requires investigation)

## Tab 4: Formulas
**Detailed Mathematical Formulas:**
- Plant water consumption = Ore tonnes × Water per tonne
- TSF return = Plant consumption × (Return Rate %)
- Evaporation = (Rate mm / 1000) × Surface area m²
- Rainfall = (Rainfall mm / 1000) × Surface area m²
- Storage change = Closing volume - Opening volume
- Closure error = Inflows - Outflows - Storage change

## Tab 5: Water Sources
**5 Water Source Types Explained:**

1. **Surface Water** - Rivers, streams, dams
   - Seasonal, measured with flow meters
   - Requires water licenses

2. **Groundwater** - Boreholes, wells
   - Stable flow, usually metered
   - Monitor for aquifer sustainability

3. **Underground** - Mine dewatering
   - Increases with mining depth
   - Often poor quality (high TDS)
   - Free but requires treatment

4. **Rainfall** - Direct precipitation
   - Seasonal and unpredictable
   - Excellent quality (low TDS)
   - Large dams capture significant volume

5. **TSF Return** - Recycled tailings water
   - Most sustainable source
   - Reduces freshwater demand
   - 50-60% typical recovery rate

## Tab 6: Storage
**Storage Facility Management**
- Facility types (process dam, raw water, emergency, PCDs, tanks, TSF)
- Volume calculations from rating curves
- Capacity and utilization tracking
- Freeboard for flood safety
- Storage change analysis and interpretation

**Operational Guidelines:**
- Maintain 40-70% utilization for flexibility
- Keep minimum 90 days supply
- Monitor freeboard during rainy season
- Balance levels across facilities
- Track evaporation losses

## Tab 7: Features
**8 Major Feature Categories:**

1. **💾 Data Management** - Import, store, validate, backup
2. **⚙️ Settings** - Configure all calculation parameters
3. **🔢 Calculations** - 14 calculation types, 40,000x performance
4. **📊 Extended Summary** - Detailed component breakdown
5. **📁 Data Import** - 9 Excel templates
6. **📈 Analytics** - Trends, forecasts, seasonal analysis
7. **📄 Reports** - PDF, Excel, CSV export
8. **🔒 Data Quality** - Validation, gap handling, quality scoring

## Tab 8: Troubleshooting (NEW!)
**11 Common Issues with Solutions:**

1. **Dashboards show '-'** → Load Excel data in Flow Diagram
2. **Closure error >5%** → Check Extended Summary, verify measurements
3. **Import fails** → Check file format, column headers, dates
4. **Calculations slow** → Clear cache, first calculation is normal (~1-3 sec)
5. **Flow Diagram won't save** → Check permissions, disk space
6. **Analytics unavailable** → Need 3+ months of data
7. **Excel mapping errors** → Click Validate or Auto-Map
8. **KPI doesn't match Excel** → Check Settings parameters
9. **Missing data warnings** → Normal, app uses historical averages
10. **Database errors** → Restart application or reset database
11. **Getting help** → Check docs/, logs/, or contact IT

---

## Quick Navigation Tips

**For New Users:** Start with Overview → Dashboards → Calculations
**For Data Entry:** Go to Features → Data Import (then Data Import tab in app)
**Having Issues:** Check Troubleshooting tab first
**Want Details:** See Formulas and Water Sources tabs
**Optimizing System:** Check Features tab (Performance Optimization section)

## Key Statistics

- **6 Dashboards** documented in detail
- **11 Common Issues** covered with solutions
- **9 Import Templates** available
- **5 Water Source Types** explained
- **14 Calculation Types** supported
- **8 Feature Categories** detailed
- **40,000x Cache Performance** improvement
- **±5% Closure Error** threshold
- **350,000 Tonnes/Month** default ore processing
- **56% TSF Return** typical recovery rate

---

**Access:** Click "? Help" in application navigation
**Last Updated:** January 13, 2026
**Status:** Current & Comprehensive
