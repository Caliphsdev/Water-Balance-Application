# 🎯 Balance Check Parameters - Complete Answer

## Your Question
> "So where are the parameters being read or activated for balance check coming from?"

## The Complete Answer

### **5 Sources of Parameters**

```
┌─────────────────────────────────────────────────────────────────┐
│  BALANCE CHECK PARAMETERS SOURCES (In Order of Activation)       │
└─────────────────────────────────────────────────────────────────┘

1️⃣  TEMPLATE FILES (Value Source - App Startup)
    ├─ INFLOW_CODES_TEMPLATE.txt
    ├─ OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
    └─ DAM_RECIRCULATION_TEMPLATE.txt
    └─ Contains: 34+64+12 = 110 flows with m³ values
    └─ Activated: src/utils/template_data_parser.py (app startup)

2️⃣  AREA EXTRACTION (Location Assignment - App Startup)
    ├─ Extracted from flow codes
    ├─ Example: MERN_ prefix → area NDCD1-4
    └─ Activated: src/utils/template_data_parser.py._extract_area_from_code()

3️⃣  CONFIGURATION FILE (Filter Control - User Configures)
    ├─ data/balance_check_config.json
    ├─ Contains: Which flows enabled/disabled
    └─ Activated: src/ui/calculations.py._open_balance_config_editor()

4️⃣  AREA EXCLUSIONS (Area Filter - User Configures)
    ├─ config/area_exclusions.json
    ├─ Contains: Which areas to exclude
    └─ Activated: Area Exclusion Manager

5️⃣  CALCULATION ENGINE (Filtering & Summing - User Calculates)
    ├─ Applies all filters above
    ├─ Sums only enabled flows from non-excluded areas
    └─ Activated: src/utils/balance_check_engine.py.calculate_balance()
```

---

## Exact Data Flow

```
STEP 1: VALUES ARE READ
  From: INFLOW_CODES_TEMPLATE.txt (etc.)
  Line: "MERN_NDCDG_evap (evaporation) = 5 327 m³"
  Read: TemplateDataParser._parse_line()
  Store: BalanceEntry(code="MERN_NDCDG_evap", value_m3=5327.0, area="NDCD1-4")
  Where: self.parser.inflows list (34 entries total)

STEP 2: AREA IS EXTRACTED
  From: Flow code "MERN_NDCDG_evap"
  Extract: _extract_area_from_code() looks for "MERN_" prefix
  Assign: area = "NDCD1-4"
  Store: BalanceEntry.area

STEP 3: USER CONFIGURES
  Dialog shows: All 110 flows from parser
  User: Unchecks "MERN_SOFT_losses"
  Save: data/balance_check_config.json
  Config: {"outflows": [{"code": "MERN_SOFT_losses", "enabled": false}, ...]}

STEP 4: ENGINE CALCULATES
  Load config: data/balance_check_config.json
  Load exclusions: config/area_exclusions.json
  For each flow entry in parser.inflows/outflows/recirculation:
    ├─ Check: Is area excluded? → Skip if yes
    ├─ Check: Is flow enabled in config? → Skip if no
    └─ If passes both: metrics.total += entry.value_m3
  
STEP 5: RESULTS DISPLAYED
  Show: "Total Outflows: 569,204 m³"
  Note: Only includes ENABLED flows from non-EXCLUDED areas
```

---

## Where Each Parameter Comes From

### 💧 **Inflow Values (34 entries)**
```
Source: INFLOW_CODES_TEMPLATE.txt
Example: MERN_NDCDG_evap = 5,327 m³

Code:
  src/utils/template_data_parser.py line 170
  └─ self._load_inflows()
    └─ self._parse_line()
      └─ Extract value_m3 = 5327.0

Stored: self.inflows[0] = BalanceEntry(..., value_m3=5327.0)

Used: src/utils/balance_check_engine.py line 180
  for entry in self.parser.inflows:
    if self._is_flow_enabled(...):
      metrics.total_inflows += entry.value_m3  ← 5,327 ADDED HERE!
```

### 🚰 **Outflow Values (64 entries)**
```
Source: OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
Example: MERN_SOFT_losses = 1,063 m³

Code:
  src/utils/template_data_parser.py line 205
  └─ self._load_outflows()
    └─ self._parse_line()
      └─ Extract value_m3 = 1063.0

Stored: self.outflows[N] = BalanceEntry(..., value_m3=1063.0)

Used: src/utils/balance_check_engine.py line 184
  for entry in self.parser.outflows:
    if self._is_flow_enabled(...):
      metrics.total_outflows += entry.value_m3  ← 1,063 ADDED HERE!
    else:  ← If config says disabled
      # Skip - don't add value
```

### ♻️ **Recirculation Values (12 entries)**
```
Source: DAM_RECIRCULATION_TEMPLATE.txt
Example: MERN_NDCDG_loop = 5,000 m³

Code:
  src/utils/template_data_parser.py line 240
  └─ self._load_recirculation()
    └─ self._parse_line()
      └─ Extract value_m3 = 5000.0

Stored: self.recirculation[N] = BalanceEntry(..., value_m3=5000.0)

Used: src/utils/balance_check_engine.py line 188
  for entry in self.parser.recirculation:
    if self._is_flow_enabled(...):
      metrics.total_recirculation += entry.value_m3  ← 5,000 ADDED HERE!
```

### 🏭 **Area Assignment**
```
Source: Derived from code prefix
Example: Code "MERN_NDCDG_evap" → Area "NDCD1-4"

Code:
  src/utils/template_data_parser.py line 140
  └─ self._extract_area_from_code(code)
    └─ if "MERN" in code: return "NDCD1-4"

Stored: BalanceEntry.area = "NDCD1-4"

Used: src/utils/balance_check_engine.py line 179
  if entry.area not in excluded_areas:
    # Include in calculation
```

### ✅ **Enabled/Disabled Status**
```
Source: data/balance_check_config.json
Example: {"code": "MERN_SOFT_losses", "enabled": false}

Created: src/ui/calculations.py line 835
  └─ User clicks "⚙️ Configure Balance Check"
    └─ User unchecks flows
    └─ Save to data/balance_check_config.json

Code:
  src/utils/balance_check_engine.py line 114
  └─ self._load_balance_config()
    └─ json.load(config_path)

Used: src/utils/balance_check_engine.py line 143
  └─ def _is_flow_enabled(self, flow_code, flow_type):
    └─ Return config[flow_type][code]['enabled']

Effect: src/utils/balance_check_engine.py line 180/184/188
  if self._is_flow_enabled(...):  ← Checks this!
    metrics.total_outflows += entry.value_m3
  else:
    # Skip - don't add value
```

---

## Three-Word Answer

### **Templates → Parser → Filter**

1. **Templates** (INFLOW_CODES_TEMPLATE.txt, etc.) contain values
2. **Parser** (TemplateDataParser) reads and stores them as BalanceEntry objects
3. **Filter** (BalanceCheckEngine + config) controls which ones are included

---

## One Sentence Summary

**Balance check parameters come from template files (for values), configuration JSON (for enabled/disabled status), and area assignments (for grouping) - all activated in sequence by the BalanceCheckEngine when you click Calculate Balance.**

---

## Quick File Reference

| What | Where | How Read |
|-----|-------|----------|
| Inflow m³ values | `INFLOW_CODES_TEMPLATE.txt` | Line by line, regex parse |
| Outflow m³ values | `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt` | Line by line, regex parse |
| Recirculation m³ values | `DAM_RECIRCULATION_TEMPLATE.txt` | Line by line, regex parse |
| Which flows enabled | `data/balance_check_config.json` | JSON load + lookup by code |
| Which areas excluded | `config/area_exclusions.json` | JSON load + set membership |
| Calculation logic | `src/utils/balance_check_engine.py` | Python loops + conditionals |
| User interface | `src/ui/calculations.py` | Tkinter dialog + display |

---

## The Magic: _is_flow_enabled()

This ONE function controls which template values are included:

```python
def _is_flow_enabled(self, flow_code: str, flow_type: str) -> bool:
    """
    Returns True if flow should be included in calculation
    Returns False if flow should be excluded
    """
    # No config = include all (backward compatible)
    if not self.config:
        return True
    
    # Look up this flow in the config
    for item in self.config.get(flow_type, []):
        if item.get('code') == flow_code:
            # Found it! Return its enabled status
            return item.get('enabled', True)
    
    # Not in config = exclude it
    return False

# Usage in calculate_balance():
if self._is_flow_enabled('MERN_SOFT_losses', 'outflows'):
    metrics.total_outflows += entry.value_m3  # ← INCLUDE
else:
    pass  # ← EXCLUDE
```

This function is called 110 times (once per flow) and decides which template values are summed!

---

## Visual: Parameter Activation Timeline

```
TIME 0:00 - App Starts
  ├─ Load template files
  ├─ Parse 110 flows → BalanceEntry objects with value_m3
  └─ Store in parser.inflows/outflows/recirculation

TIME 0:05 - User Configures
  ├─ Click "⚙️ Configure Balance Check"
  ├─ Dialog shows 110 flows
  ├─ User unchecks flows
  └─ Save to data/balance_check_config.json

TIME 0:10 - User Calculates
  ├─ Click "Calculate Balance"
  ├─ Engine loads config from JSON
  ├─ Loop 110 times:
  │  ├─ Get entry.value_m3 from parser
  │  ├─ Check _is_flow_enabled(code, type)
  │  ├─ If true: sum += value_m3
  │  └─ If false: skip
  └─ Display results

TIME 0:11 - Results Shown
  └─ UI displays: "Total Outflows: 569,204 m³"
     (Only 45 of 64 outflows if others disabled)
```

---

## Final Answer to Your Question

### Where are the parameters being READ?

1. **Template .txt files** - Read at app startup by TemplateDataParser
2. **Configuration JSON** - Read when Calculate is clicked
3. **Exclusions JSON** - Read when Calculate is clicked

### Where are they ACTIVATED?

1. **TemplateDataParser** - Parses templates → creates objects with values
2. **BalanceCheckEngine** - Loads config → checks _is_flow_enabled() → includes/excludes based on config
3. **UI** - Displays final results from filtered calculation

### The Filter Chain:

```
ALL 110 FLOWS
    ↓
Exclude by Area? → Removed flows from excluded areas
    ↓
Exclude by Config? → Removed flows with enabled=false
    ↓
ENABLED FLOWS ONLY
    ↓
Sum the value_m3 of remaining flows
    ↓
Display: "Total Outflows: X m³"
```

That's the complete picture! 🎯
