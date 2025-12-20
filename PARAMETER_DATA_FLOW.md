# 📊 Where Balance Check Parameters Come From - Complete Flow

## Data Source Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│  BALANCE CHECK PARAMETERS - Data Source Flow                        │
└─────────────────────────────────────────────────────────────────────┘

LEVEL 1: TEXT TEMPLATE FILES (Source of Truth)
═════════════════════════════════════════════════════════════════════
├─ INFLOW_CODES_TEMPLATE.txt
│  └─ 34 entries: codes, names, values in m³
│     Example: MERN_NDCDG_evap = 5,327 m³
│
├─ OUTFLOW_CODES_TEMPLATE_CORRECTED.txt  
│  └─ 64 entries: codes, names, values in m³
│     Example: MERN_SOFT_losses = 1,063 m³
│
└─ DAM_RECIRCULATION_TEMPLATE.txt
   └─ 12 entries: codes, names, values in m³
      Example: MERN_NDCDG_loop = 5,000 m³

        ⬇️  (Parsed by TemplateDataParser)


LEVEL 2: PYTHON PARSER - In-Memory Objects
═════════════════════════════════════════════════════════════════════
src/utils/template_data_parser.py

├─ BalanceEntry dataclass
│  ├─ code: str (e.g., "MERN_NDCDG_evap")
│  ├─ name: str (e.g., "Evaporation")
│  ├─ area: str (e.g., "NDCD1-4")
│  ├─ value_m3: float (e.g., 5327.0)
│  └─ unit: str (always "m³")
│
├─ TemplateDataParser singleton
│  ├─ self.inflows: List[BalanceEntry] = 34 entries
│  ├─ self.outflows: List[BalanceEntry] = 64 entries
│  ├─ self.recirculation: List[BalanceEntry] = 12 entries
│  └─ self.areas: set = ['NDCD1-4', 'NDSWD1-2', ...]
│
└─ Methods:
   ├─ get_inflows_by_area(area) → List[BalanceEntry]
   ├─ get_outflows_by_area(area) → List[BalanceEntry]
   ├─ get_total_inflows() → float
   └─ get_total_outflows() → float

        ⬇️  (Filtered by BalanceCheckEngine)


LEVEL 3: CONFIGURATION FILTER - Enable/Disable Control
═════════════════════════════════════════════════════════════════════
data/balance_check_config.json

├─ Created by user via Configure dialog
├─ Structure:
│  {
│    "inflows": [
│      {"code": "MERN_NDCDG_evap", "enabled": true},
│      {"code": "MERN_SOFT_losses", "enabled": false},  ← EXCLUDED
│      ...
│    ],
│    "outflows": [...],
│    "recirculation": [...]
│  }
│
└─ If no config exists: ALL flows included by default (backward compatible)

        ⬇️  (Applied by BalanceCheckEngine._is_flow_enabled())


LEVEL 4: BALANCE CHECK ENGINE - Calculation
═════════════════════════════════════════════════════════════════════
src/utils/balance_check_engine.py

BalanceCheckEngine class:
├─ __init__()
│  ├─ self.parser = get_template_parser() ← Loads template files
│  └─ self.config = self._load_balance_config() ← Loads JSON config
│
├─ calculate_balance() method
│  ├─ for entry in self.parser.inflows:
│  │  └─ if self._is_flow_enabled(entry.code, 'inflows'):
│  │     └─ metrics.total_inflows += entry.value_m3 ✅ INCLUDED
│  │
│  ├─ for entry in self.parser.outflows:
│  │  └─ if self._is_flow_enabled(entry.code, 'outflows'):
│  │     └─ metrics.total_outflows += entry.value_m3 ✅ INCLUDED
│  │
│  └─ for entry in self.parser.recirculation:
│     └─ if self._is_flow_enabled(entry.code, 'recirculation'):
│        └─ metrics.total_recirculation += entry.value_m3 ✅ INCLUDED
│
├─ _is_flow_enabled(flow_code, flow_type) → bool
│  ├─ If no config: return True (include all)
│  ├─ If config empty: return True (include all)
│  ├─ If flow not in config: return False (exclude)
│  └─ If flow in config: return config[flow].enabled
│
└─ Returns: OverallBalanceMetrics with calculated totals

        ⬇️  (Displayed in UI)


LEVEL 5: USER INTERFACE - Display
═════════════════════════════════════════════════════════════════════
src/ui/calculations.py

CalculationsModule:
├─ _update_balance_check_summary()
│  ├─ Calls: engine.calculate_balance()
│  └─ Displays:
│     ├─ Total Inflows: {metrics.total_inflows} m³
│     ├─ Total Outflows: {metrics.total_outflows} m³
│     ├─ Total Recirculation: {metrics.total_recirculation} m³
│     ├─ Balance Difference: {metrics.balance_difference} m³
│     └─ Error %: {metrics.balance_error_percent}%
│
└─ _update_balance_calculation_breakdown()
   └─ Shows step-by-step calculation with values from metrics

```

---

## Specific Code Locations

### 1. **Where Inflow Values Come From**
```python
# FILE: src/utils/template_data_parser.py (lines 170-180)

def _load_inflows(self):
    """Parse INFLOW_CODES_TEMPLATE.txt"""
    with open(self.inflows_file) as f:
        for line in f:
            parsed = self._parse_line(line)
            if parsed:
                code, name, _, value = parsed
                area = self._extract_area_from_code(code)
                self.inflows.append(BalanceEntry(code, name, area, value))
                # Now self.inflows has the values from template!
```

### 2. **Where Outflow Values Come From**
```python
# FILE: src/utils/template_data_parser.py (lines 205-215)

def _load_outflows(self):
    """Parse OUTFLOW_CODES_TEMPLATE_CORRECTED.txt"""
    with open(self.outflows_file) as f:
        for line in f:
            parsed = self._parse_line(line)
            if parsed:
                code, name, _, value = parsed
                area = self._extract_area_from_code(code)
                self.outflows.append(BalanceEntry(code, name, area, value))
                # Now self.outflows has 64 entries with values!
```

### 3. **Where Config Filter Is Applied**
```python
# FILE: src/utils/balance_check_engine.py (lines 161-191)

def calculate_balance(self) -> OverallBalanceMetrics:
    metrics = OverallBalanceMetrics()
    
    # ONLY include flows that are:
    # 1. Not in excluded areas (from area_exclusion_manager)
    # 2. Marked as enabled in config (from balance_check_config.json)
    
    for entry in self.parser.inflows:
        if entry.area not in excluded_areas and self._is_flow_enabled(entry.code, 'inflows'):
            metrics.total_inflows += entry.value_m3  # ← VALUE FROM TEMPLATE!
```

### 4. **Where Configuration Controls It**
```python
# FILE: src/utils/balance_check_engine.py (lines 126-156)

def _is_flow_enabled(self, flow_code: str, flow_type: str) -> bool:
    """Check if flow should be included"""
    
    # If no config → include all (backward compatible)
    if not self.config:
        return True  # ALL flows included
    
    if flow_type not in self.config:
        return True  # All flows of this type included
    
    # Check if flow is in config and enabled
    flows_in_config = self.config.get(flow_type, [])
    for item in flows_in_config:
        if item.get('code') == flow_code:
            return item.get('enabled', True)  # ← CONFIG CONTROLS THIS!
    
    # Not in config → don't include
    return False
```

---

## Complete Parameter Activation Flow

```
1. USER CONFIGURES
   ├─ Clicks "⚙️ Configure Balance Check"
   ├─ Dialog shows template flows
   ├─ User unchecks "MERN_SOFT_losses"
   └─ Saves to data/balance_check_config.json

2. ENGINE LOADS PARAMETERS
   ├─ TemplateDataParser reads OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
   ├─ Parses line: "MERN_SOFT_losses (proc_losses) = 1 063 m³"
   ├─ Creates: BalanceEntry(code='MERN_SOFT_losses', value_m3=1063.0)
   ├─ Stores in: self.parser.outflows list
   └─ Total: 64 outflow entries with values

3. ENGINE FILTERS BY CONFIG
   ├─ Loads data/balance_check_config.json
   ├─ Checks: Is 'MERN_SOFT_losses' enabled?
   ├─ Finds: "enabled": false
   └─ Result: SKIP this entry - don't add value_m3 to total!

4. ENGINE CALCULATES TOTALS
   ├─ for entry in self.parser.outflows:
   │  ├─ Check: _is_flow_enabled('MERN_SOFT_losses', 'outflows')
   │  ├─ Result: False
   │  └─ Action: Skip - don't add 1,063 m³ to total_outflows
   │
   └─ total_outflows = sum of ONLY enabled entries

5. UI DISPLAYS RESULTS
   └─ Shows: "Total Outflows: X m³ (only from enabled flows)"
```

---

## Summary: Where Are Parameters READ or ACTIVATED?

| Component | Parameter Source | How It's Read | When It's Activated |
|-----------|-----------------|---------------|-------------------|
| **Templates** | INFLOW_CODES_TEMPLATE.txt | Parsed by TemplateDataParser | App startup |
| **Values** | Lines in .txt files (e.g., "= 5,327 m³") | Regex parsing in _parse_line() | During _load_inflows() |
| **Areas** | Code prefix (MERN_ → NDCD1-4) | _extract_area_from_code() | During template load |
| **Config** | data/balance_check_config.json | JSON.load() in __init__() | Engine initialization |
| **Enabled/Disabled** | Config JSON "enabled" field | _is_flow_enabled() check | During calculate_balance() |
| **Final Values** | entry.value_m3 from BalanceEntry | Sum in loops | When included flows are summed |

---

## Answer to Your Question

**"Where are the parameters being read or activated?"**

1. **READ FROM:**
   - Template .txt files (source of values)
   - Configuration JSON (source of enable/disable status)

2. **ACTIVATED IN:**
   - `TemplateDataParser._load_inflows()` - Reads template → creates objects
   - `BalanceCheckEngine._load_balance_config()` - Reads config → stores in self.config
   - `BalanceCheckEngine._is_flow_enabled()` - Checks if flow should be included
   - `BalanceCheckEngine.calculate_balance()` - Sums only enabled flows

3. **DISPLAYED IN:**
   - `CalculationsModule._update_balance_check_summary()` - Shows the final totals
