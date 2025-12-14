# Dynamic Flow Diagram Labels from Excel - Implementation Plan

## 🎯 Vision

Transform flow diagram from **static template data** → **dynamic monthly Excel data** while maintaining 100% resilience if Excel unavailable.

```
Before (Static):
  Flow Diagram: "Boreholes: 12,000 m³" (hardcoded)
  
After (Dynamic):
  User clicks "📊 Load January 2025 Data"
  ↓
  App reads Excel time-series
  ↓
  Sums individual boreholes (BH-01: 400 + BH-02: 450 + BH-03: 480 = 1,330)
  ↓
  Updates all diagram labels in real-time
  ↓
  Shows indicator: "📊 Live Data - January 2025"
```

---

## 📊 Current Problem: Data Structure Mismatch

### **Excel Structure** (What You Have)
```
Column Headers in Excel:
Date | BH_01 | BH_02 | BH_03 | River_1 | River_2 | Dewater_North | ...
2025-01-01 | 400   | 450   | 480   | 2500    | 3200    | 1500         |
2025-01-02 | 410   | 460   | 470   | 2600    | 3100    | 1480         |
```
**Problem**: Individual monthly readings need to be SUMMED for diagram display

### **Diagram Structure** (What You Display)
```
Nodes/Flows:
- "Total Boreholes" → Should show SUM(BH_01 + BH_02 + BH_03) = 1,330
- "Rivers" → Should show SUM(River_1 + River_2) = 5,700
- "Dewatering" → Should show Dewater_North = 1,500
```

**Solution**: Create a **Mapping Configuration** that groups Excel columns into diagram flows

---

## 🗺️ Mapping Configuration (New File)

### **File**: `config/excel_flow_mapping.json`

```json
{
  "version": "1.0",
  "description": "Maps Excel columns to flow diagram nodes",
  "mapping": [
    {
      "diagram_node_id": "boreholes_total",
      "diagram_label": "Total Boreholes",
      "excel_columns": ["BH_01", "BH_02", "BH_03", "BH_04"],
      "aggregation": "sum",
      "category": "inflow",
      "unit": "m³"
    },
    {
      "diagram_node_id": "rivers_total",
      "diagram_label": "Rivers (Raw Water)",
      "excel_columns": ["RIVER_1", "RIVER_2"],
      "aggregation": "sum",
      "category": "inflow",
      "unit": "m³"
    },
    {
      "diagram_node_id": "dewatering_north",
      "diagram_label": "Dewatering North",
      "excel_columns": ["DEWATER_NORTH"],
      "aggregation": "first",
      "category": "inflow",
      "unit": "m³"
    },
    {
      "diagram_node_id": "mining_consumption",
      "diagram_label": "Mining Consumption",
      "excel_columns": ["MINING_WATER"],
      "aggregation": "sum",
      "category": "outflow",
      "unit": "m³"
    },
    {
      "diagram_node_id": "evaporation",
      "diagram_label": "Evaporation Loss",
      "excel_columns": ["EVAP_TSF", "EVAP_DAM"],
      "aggregation": "sum",
      "category": "outflow",
      "unit": "m³"
    }
  ],
  "excel_config": {
    "date_column": "Date",
    "date_format": "%Y-%m-%d",
    "monthly_aggregation": "last",
    "description": "For monthly data, take the LAST day of each month"
  }
}
```

**Aggregation Types**:
- `sum`: Add all columns (boreholes, rivers, losses)
- `first`: Take first value (single source)
- `average`: Average across period
- `last`: Last reading of month (for monthly aggregate)

---

## 🏗️ Architecture: 4 New Components

### **1. Excel Mapping Manager** (`src/utils/excel_flow_mapper.py`)

```python
class ExcelFlowMapper:
    """Maps Excel columns to diagram flows"""
    
    def __init__(self, mapping_file='config/excel_flow_mapping.json'):
        self.mapping = self._load_mapping(mapping_file)
    
    def get_flow_value(self, flow_node_id, excel_data, target_date):
        """
        Get aggregated value for a diagram flow node from Excel data
        
        Args:
            flow_node_id: e.g., "boreholes_total"
            excel_data: DataFrame from Excel reader
            target_date: date object (2025-01-31 for January data)
        
        Returns:
            float: Aggregated value, or None if no data
        """
        # Find mapping for this node
        config = self._get_config_for_node(flow_node_id)
        if not config:
            return None
        
        # Extract columns
        columns = config['excel_columns']
        available_cols = [col for col in columns if col in excel_data.columns]
        
        if not available_cols:
            return None
        
        # Get data for target date
        date_data = excel_data[excel_data['Date'] == target_date]
        
        if date_data.empty:
            return None
        
        # Apply aggregation
        values = date_data[available_cols].values[0]
        aggregation = config['aggregation']
        
        if aggregation == 'sum':
            return float(sum(values))
        elif aggregation == 'average':
            return float(sum(values) / len(values))
        elif aggregation == 'first':
            return float(values[0])
        else:
            return None
```

### **2. Excel Reader (On-Demand)** (`src/utils/excel_monthly_reader.py`)

```python
class ExcelMonthlyReader:
    """Reads Excel data on-demand with caching"""
    
    def __init__(self):
        self._cache = {}  # {(file, month_key): DataFrame}
        self.last_error = None
    
    def get_month_data(self, excel_file, year, month):
        """
        Get Excel data for a specific month
        Returns None if Excel unavailable (graceful degradation)
        """
        cache_key = (str(excel_file), f"{year}-{month:02d}")
        
        # Return cached if available
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            import openpyxl
            import pandas as pd
            
            df = pd.read_excel(excel_file, sheet_name='TimeSeries')
            
            # Filter to month
            df['Date'] = pd.to_datetime(df['Date'])
            df_month = df[
                (df['Date'].dt.year == year) & 
                (df['Date'].dt.month == month)
            ]
            
            self._cache[cache_key] = df_month
            self.last_error = None
            return df_month
            
        except Exception as e:
            self.last_error = f"Excel read error: {str(e)}"
            logger.warning(self.last_error)
            return None  # Graceful degradation
```

### **3. Dynamic Label Updater** (`src/utils/dynamic_flow_labels.py`)

```python
class DynamicFlowLabels:
    """Updates flow diagram labels from Excel"""
    
    def __init__(self, mapper, excel_reader):
        self.mapper = mapper
        self.excel_reader = excel_reader
    
    def update_diagram_labels(self, diagram_area_data, excel_file, year, month):
        """
        Update all flow labels in diagram_area_data with Excel data
        
        Returns: (updated_edges, success, error_message)
        """
        # Try to read Excel
        excel_data = self.excel_reader.get_month_data(excel_file, year, month)
        
        if excel_data is None:
            error = self.excel_reader.last_error
            logger.warning(f"Falling back to template data: {error}")
            return (None, False, error)
        
        # Calculate target date (last day of month)
        target_date = self._get_month_end_date(year, month)
        
        # Update each edge in diagram
        edges = diagram_area_data.get('edges', [])
        updated_count = 0
        
        for edge in edges:
            flow_node = edge.get('from')
            
            # Get value from Excel
            value = self.mapper.get_flow_value(flow_node, excel_data, target_date)
            
            if value is not None:
                edge['volume'] = value
                edge['label'] = f"{value:,.0f}"
                edge['data_source'] = 'excel'
                updated_count += 1
        
        return (edges, True, f"Updated {updated_count} labels from {year}-{month:02d}")
```

### **4. UI Integration in Flow Diagram**

Add to toolbar:
```python
# New button in flow_diagram_dashboard.py
Button(button_frame, text='📊 Load Monthly Data', 
       command=self._load_excel_data,
       bg='#1abc9c', fg='white', font=('Segoe UI', 9)).pack(side='left', padx=5)

# New method
def _load_excel_data(self):
    """Load Excel data for selected month"""
    # Show dialog: Select Year/Month
    # Try to read Excel
    # Update diagram labels
    # Show status: "✅ Live Data - January 2025" or "⚠️ Using Template Data"
```

---

## 📋 Data Flow Diagram

```
User Interface
├─ Select Month (Jan 2025)
├─ Click "📊 Load Monthly Data"
│
└─→ DynamicFlowLabels.update_diagram_labels()
    │
    ├─→ ExcelMonthlyReader.get_month_data(year=2025, month=1)
    │   ├─ Try: Read Excel → Cache result
    │   └─ Fail: Return None (graceful fallback)
    │
    ├─→ ExcelFlowMapper.get_flow_value(node_id, excel_data, target_date)
    │   ├─ Find mapping config
    │   ├─ Get Excel columns (BH_01, BH_02, ...)
    │   ├─ Apply aggregation (sum/avg/first)
    │   └─ Return: 1,330 m³
    │
    └─→ Update diagram edges
        ├─ Set edge['volume'] = 1,330
        ├─ Set edge['label'] = "1,330"
        ├─ Set edge['data_source'] = 'excel'
        └─ Redraw diagram

Result: "📊 Live Data - January 2025"
```

---

## ✅ Resilience & Fallback Strategy

### **Scenario 1: Excel Unavailable**
```
User clicks "Load Monthly Data"
    ↓
ExcelMonthlyReader tries to read Excel
    ↓
ERROR: "File not found" or "Corrupted"
    ↓
Returns None (graceful degradation)
    ↓
Show warning: "⚠️ Excel unavailable, using template data"
    ↓
Use current .txt template labels
    ↓
App continues normally ✅
```

### **Scenario 2: Excel Column Missing**
```
Mapping expects "BH_01" column
    ↓
Excel file exists but doesn't have BH_01
    ↓
ExcelFlowMapper.get_flow_value() returns None
    ↓
Keep existing diagram label (don't update)
    ↓
Show warning: "⚠️ Column BH_01 not found in Excel"
    ↓
App continues normally ✅
```

### **Scenario 3: Excel Available & Valid**
```
All columns found, aggregation successful
    ↓
Update all diagram labels
    ↓
Show success: "✅ Updated 47 flows - January 2025"
    ↓
Display indicator: "📊 Live Data"
    ↓
User can edit/save diagram with live data ✅
```

---

## 🔄 Integration with Balance Check

### **Option A: Use Same Mapping for Balance Check**
```python
# In balance_check_engine.py
class BalanceCheckEngine:
    def calculate_balance(self, use_excel=False, year=None, month=None):
        if use_excel and year and month:
            # Try to read Excel using same mapping
            excel_data = self.excel_reader.get_month_data(excel_file, year, month)
            if excel_data:
                # Use Excel-based values instead of templates
                # Same aggregation logic
        else:
            # Fallback to .txt templates
            # Existing logic
```

### **Option B: Separate Excel Config for Balance Check**
```
config/excel_flow_mapping.json (diagram)
config/excel_balance_mapping.json (balance check)

Allows different mappings for different use cases
```

---

## 📝 Implementation Steps (Recommended Order)

### **Phase 1: Core Infrastructure** (2-3 hours)
1. ✅ Create `excel_flow_mapping.json` (understand Excel structure first!)
2. ✅ Implement `ExcelFlowMapper` class
3. ✅ Implement `ExcelMonthlyReader` class with caching
4. ✅ Add error handling and graceful degradation

### **Phase 2: Flow Diagram Integration** (2-3 hours)
1. ✅ Add "📊 Load Monthly Data" button
2. ✅ Add month/year selector dialog
3. ✅ Integrate `DynamicFlowLabels` class
4. ✅ Update diagram labels on demand
5. ✅ Show data source indicator (Live vs Template)

### **Phase 3: Balance Check Integration** (1-2 hours)
1. ✅ Refactor balance check to use same mapping
2. ✅ Add "Use Excel Data" option to balance tab
3. ✅ Show which data source is being used

### **Phase 4: Testing & Polish** (1-2 hours)
1. ✅ Test Excel read errors
2. ✅ Test missing columns
3. ✅ Test caching behavior
4. ✅ Test month transitions

---

## 🎯 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Mapping in JSON** | Easy to edit without code changes; version control friendly |
| **On-demand loading** | Don't block startup if Excel slow/unavailable |
| **Caching by month** | Switching months fast, minimal Excel reads |
| **Graceful degradation** | App NEVER crashes due to Excel issues |
| **Same mapper for both** | Single source of truth for Excel→diagram mapping |
| **Indicator (📊 vs 📋)** | User always knows which data they're viewing |
| **No automatic updates** | User explicitly chooses when to load; prevents confusion |

---

## 💡 Example Workflow for User

```
1. User opens Flow Diagram Dashboard
   → Shows template data (📋 Template Data - Static)

2. User wants current January 2025 data
   → Clicks "📊 Load Monthly Data"
   → Selects January 2025
   → Waits <2 seconds

3. Excel reads successfully
   → All labels update: "1,330" instead of "12,000"
   → Shows "📊 Live Data - January 2025"
   → User can edit/drag/save as normal

4. User switches to February
   → Clicks "📊 Load Monthly Data" again
   → Selects February 2025
   → Labels update to February values

5. If Excel unavailable
   → User clicks "📊 Load Monthly Data"
   → Gets error: "Excel file not found"
   → Labels stay as template (still usable)
   → User can still work, just with static data
```

---

## ❓ Questions Before Implementation

1. **Excel File Location**: Where is the main Excel file? Single file or multiple?
2. **Sheet Name**: What is the sheet name with time-series data? (assuming "TimeSeries"?)
3. **Date Format**: How are dates stored in Excel? (YYYY-MM-DD?)
4. **Monthly vs Daily**: Is data daily, weekly, or already monthly?
5. **Column Names**: What are exact column headers for boreholes, rivers, etc.?
6. **Audit Trail**: Should we log which data source was used? (for reporting later)
7. **Simultaneous Users**: Can multiple users load Excel simultaneously?

---

**Ready to proceed when you have answers to Excel structure questions!**
