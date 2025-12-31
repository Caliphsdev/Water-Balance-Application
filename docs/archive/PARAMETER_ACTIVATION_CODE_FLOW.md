# 🔄 Exact Code Flow: Balance Check Parameters

## Path 1: INFLOWS (How Inflow Parameters Get Into Balance Calculation)

```
START: User clicks "Calculate Balance"
    ⬇️
Calculations._calculate_balance()  [src/ui/calculations.py:288]
    ├─ self.calculator.calculate_water_balance()
    └─ self.balance_engine.calculate_balance()  ← HERE!
    
    ⬇️
BalanceCheckEngine.calculate_balance()  [src/utils/balance_check_engine.py:161]
    ⬇️
    │ self.parser = already loaded (created in __init__)
    │ self.config = already loaded (created in __init__)
    ⬇️
    for entry in self.parser.inflows:  ← ALL 34 inflow entries
        ├─ entry.code = "MERN_NDCDG_evap"
        ├─ entry.value_m3 = 5327.0  ← VALUE FROM TEMPLATE!
        ├─ entry.area = "NDCD1-4"
        │
        └─ if entry.area not in excluded_areas:  [Line 180]
            ├─ Status: True (NDCD1-4 not excluded)
            │
            └─ if self._is_flow_enabled(entry.code, 'inflows'):  [Line 180]
                ├─ Checks: config['inflows'] for entry where code=='MERN_NDCDG_evap'
                ├─ Status: True (enabled in config) [or True if no config]
                │
                └─ metrics.total_inflows += entry.value_m3  ← 5,327 ADDED!
    
    ⬇️
return OverallBalanceMetrics(total_inflows=4,897,861, ...)
    ⬇️
Displayed in UI
```

## Path 2: OUTFLOWS (How Outflow Parameters Get Into Balance Calculation)

```
BalanceCheckEngine.calculate_balance()  [Line 161]
    ⬇️
    for entry in self.parser.outflows:  ← ALL 64 outflow entries
        ├─ entry.code = "MERN_SOFT_losses"
        ├─ entry.value_m3 = 1063.0  ← VALUE PARSED FROM: OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
        ├─ entry.area = "NDSWD1-2"
        │
        └─ if entry.area not in excluded_areas:  [Line 184]
            ├─ Status: True (NDSWD1-2 not excluded)
            │
            └─ if self._is_flow_enabled(entry.code, 'outflows'):  [Line 184]
                ├─ Looks up config['outflows']
                ├─ Searches for item.code == "MERN_SOFT_losses"
                ├─ Status depends on item.get('enabled')
                │
                ├─ IF enabled in config:
                │   └─ metrics.total_outflows += entry.value_m3  ← VALUE ADDED!
                │
                └─ IF disabled in config:
                    └─ Skip this entry (value NOT added)
    
    ⬇️
return OverallBalanceMetrics(total_outflows=X, ...)
```

---

## Where Each Value Actually Comes From

### INFLOWS Example: "MERN_NDCDG_evap = 5,327 m³"

```
1. TEXT FILE: INFLOW_CODES_TEMPLATE.txt
   ┌─────────────────────────────────────────────────┐
   │ 💧 EVAPORATION (Auto-calculated from dam...):  │
   │   MERN_NDCDG_evap = 5 327 m³                   │
   └─────────────────────────────────────────────────┘
        ⬇️ [File read line by line]

2. PARSER: template_data_parser.py
   ┌─────────────────────────────────────────────────┐
   │ def _parse_line(self, line: str):              │
   │     # Extracts: code, name, value, area        │
   │     # From line: "MERN_NDCDG_evap = 5 327 m³" │
   │     value_str = "5327"                          │
   │     value = float("5327") = 5327.0              │
   │     return (code, name, "UNKNOWN", 5327.0)      │
   └─────────────────────────────────────────────────┘
        ⬇️ [Creates BalanceEntry object]

3. BALANCE ENTRY: BalanceEntry dataclass
   ┌─────────────────────────────────────────────────┐
   │ BalanceEntry(                                   │
   │     code="MERN_NDCDG_evap",                     │
   │     name="Evaporation",                         │
   │     area="NDCD1-4",  ← Extracted from code     │
   │     value_m3=5327.0,  ← STORED HERE!           │
   │     unit="m³"                                   │
   │ )                                               │
   └─────────────────────────────────────────────────┘
        ⬇️ [Added to parser.inflows list]

4. TEMPLATE PARSER: Stores in list
   ┌─────────────────────────────────────────────────┐
   │ self.inflows = [                                │
   │     BalanceEntry(..., value_m3=5327.0),        │
   │     BalanceEntry(..., value_m3=90320.0),       │
   │     ...  (34 total entries)                    │
   │ ]                                               │
   └─────────────────────────────────────────────────┘
        ⬇️ [Engine accesses via self.parser]

5. BALANCE ENGINE: Uses in calculation
   ┌─────────────────────────────────────────────────┐
   │ for entry in self.parser.inflows:              │
   │     if self._is_flow_enabled(entry.code...):   │
   │         metrics.total_inflows += entry.value_m3│
   │                                  ↑              │
   │                           5327.0 USED HERE     │
   │                                                 │
   │ Result: total_inflows = 4,897,861 m³           │
   └─────────────────────────────────────────────────┘
```

---

## Configuration Filter Layer

```
BEFORE CONFIG FILTER:
├─ MERN_SOFT_losses = 1,063 m³  ← In template
├─ MERP_PLANT_losses = 4,839 m³  ← In template
├─ ... (64 total outflows)
└─ total_outflows = 1,290,188 m³  (sum of all)

CONFIG FILE (data/balance_check_config.json):
{
  "outflows": [
    {"code": "MERN_SOFT_losses", "enabled": false},  ← DISABLED!
    {"code": "MERP_PLANT_losses", "enabled": true},   ← ENABLED
    ...
  ]
}

AFTER FILTER (_is_flow_enabled):
├─ MERN_SOFT_losses ❌ (config says enabled=false)
│   └─ Skip: -1,063 m³ (NOT added to total)
│
├─ MERP_PLANT_losses ✅ (config says enabled=true)
│   └─ Add: +4,839 m³ (ADDED to total)
│
└─ total_outflows = 1,290,188 - 1,063 = 1,289,125 m³

HOW IT WORKS:
    for entry in self.parser.outflows:
        ├─ Check: _is_flow_enabled(entry.code, 'outflows')
        ├─ Look up: self.config['outflows']
        ├─ Find: item where item['code'] == entry.code
        ├─ Result: item['enabled'] = True or False
        └─ Include or Exclude based on result
```

---

## Step-by-Step: From Template File to Display

```
┌─ STEP 1: File exists ─────────────────────────────┐
│                                                   │
│ OUTFLOW_CODES_TEMPLATE_CORRECTED.txt              │
│ Line 12: MERN_SOFT_losses = 1 063 m³              │
│ Line 13: MERP_PLANT_losses = 4 839 m³             │
│ ... (62 more lines)                               │
└─────────────────────────────────────────────────────┘
                    ⬇️ App starts

┌─ STEP 2: Parser loads file ───────────────────────┐
│                                                   │
│ TemplateDataParser.__init__()                     │
│   └─ self._load_outflows()                        │
│      ├─ open(self.outflows_file)                  │
│      ├─ for line in f:                            │
│      │   ├─ self._parse_line(line)                │
│      │   ├─ Create BalanceEntry(...)              │
│      │   └─ self.outflows.append(entry)           │
│      └─ Result: self.outflows = [64 entries]      │
│                                                   │
│ Each entry has:                                   │
│   - code: "MERN_SOFT_losses"                      │
│   - value_m3: 1063.0  ← FROM TEMPLATE!            │
│   - area: "NDSWD1-2"  ← EXTRACTED FROM CODE      │
└─────────────────────────────────────────────────────┘
                    ⬇️ User configures

┌─ STEP 3: User configures via dialog ──────────────┐
│                                                   │
│ CalculationsModule._open_balance_config_editor()  │
│   ├─ Dialog shows 64 outflow entries              │
│   ├─ User unchecks "MERN_SOFT_losses"             │
│   ├─ User saves                                   │
│   └─ Writes to: data/balance_check_config.json    │
│      {                                            │
│        "outflows": [                              │
│          {                                        │
│            "code": "MERN_SOFT_losses",            │
│            "enabled": false  ← USER DISABLED IT!  │
│          },                                       │
│          ...                                      │
│        ]                                          │
│      }                                            │
└─────────────────────────────────────────────────────┘
                    ⬇️ User calculates

┌─ STEP 4: Engine filters by config ────────────────┐
│                                                   │
│ BalanceCheckEngine.calculate_balance()            │
│   ├─ for entry in self.parser.outflows:           │
│   │  ├─ entry.code = "MERN_SOFT_losses"           │
│   │  ├─ entry.value_m3 = 1063.0                   │
│   │  │                                            │
│   │  └─ if self._is_flow_enabled('MERN_...'):     │
│   │     ├─ Check: config['outflows']              │
│   │     ├─ Find: "MERN_SOFT_losses"               │
│   │     ├─ Get: enabled = false                   │
│   │     └─ Result: False → Skip!                  │
│   │        (Don't add 1,063 to total)             │
│   │                                               │
│   │  ✅ Next entry: "MERP_PLANT_losses"           │
│   │     └─ if self._is_flow_enabled(...):         │
│   │        ├─ Check: config['outflows']           │
│   │        ├─ Find: "MERP_PLANT_losses"           │
│   │        ├─ Get: enabled = true                 │
│   │        └─ Result: True → Include!             │
│   │           (Add 4,839 to total)                │
│   │                                               │
│   └─ metrics.total_outflows = sum of ONLY enabled │
└─────────────────────────────────────────────────────┘
                    ⬇️ Display results

┌─ STEP 5: UI displays filtered totals ──────────────┐
│                                                   │
│ CalculationsModule._update_balance_check_summary()│
│   ├─ Show: "Total Outflows: 1,289,125 m³"         │
│   │         ↑ This is REDUCED because             │
│   │         MERN_SOFT_losses was disabled!        │
│   │                                               │
│   ├─ Show: "Outflow Count: 25 flows"              │
│   │         ↑ Was 44, now only 25 enabled         │
│   │                                               │
│   └─ Show: "Balance Error: 88.33%"                │
│            ↑ Changed because outflows changed     │
└─────────────────────────────────────────────────────┘
```

---

## All Parameters at a Glance

```
WHERE PARAMETERS COME FROM:

Value Parameters:
  ├─ Source: INFLOW_CODES_TEMPLATE.txt (34 entries with m³ values)
  ├─ Source: OUTFLOW_CODES_TEMPLATE_CORRECTED.txt (64 entries with m³ values)
  ├─ Source: DAM_RECIRCULATION_TEMPLATE.txt (12 entries with m³ values)
  ├─ Read by: TemplateDataParser._parse_line()
  ├─ Stored in: BalanceEntry.value_m3
  └─ Used in: BalanceCheckEngine.calculate_balance() loop

Area Parameters:
  ├─ Source: Extracted from flow codes (MERN_ → NDCD1-4)
  ├─ Read by: TemplateDataParser._extract_area_from_code()
  ├─ Stored in: BalanceEntry.area
  └─ Used in: Area filtering and per-area calculations

Enabled/Disabled Parameters:
  ├─ Source: data/balance_check_config.json
  ├─ Read by: BalanceCheckEngine._load_balance_config()
  ├─ Stored in: BalanceCheckEngine.config
  └─ Checked in: BalanceCheckEngine._is_flow_enabled()

Excluded Areas:
  ├─ Source: config/area_exclusions.json
  ├─ Read by: AreaExclusionManager._load_exclusions()
  ├─ Stored in: AreaExclusionManager.excluded_areas
  └─ Checked in: BalanceCheckEngine.calculate_balance()
```

---

## Summary

**Q: Where are the parameters being read or activated?**

**A:**
1. **READ FROM:**
   - `INFLOW_CODES_TEMPLATE.txt` (line by line) → BalanceCheckEngine
   - `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt` (line by line) → BalanceCheckEngine
   - `DAM_RECIRCULATION_TEMPLATE.txt` (line by line) → BalanceCheckEngine
   - `data/balance_check_config.json` (JSON) → BalanceCheckEngine
   - `config/area_exclusions.json` (JSON) → AreaExclusionManager

2. **ACTIVATED IN:**
   - `src/utils/template_data_parser.py` - Parses templates and creates BalanceEntry objects
   - `src/utils/balance_check_engine.py` - Loads config and filters flows
   - `src/ui/calculations.py` - Calls engine and displays results

3. **FLOW:**
   ```
   Template Files → Parser → BalanceEntry objects
           ↓                        ↓
       Values                    Config ← User Configuration
           ↓                        ↓
   ─────────────────────────────────
           ↓
   BalanceCheckEngine.calculate_balance()
           ↓
   Filters: Is flow enabled? Is area excluded?
           ↓
   Sums ONLY included flows
           ↓
   OverallBalanceMetrics
           ↓
   UI Display
   ```
