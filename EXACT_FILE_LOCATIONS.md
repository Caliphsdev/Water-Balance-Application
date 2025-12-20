# 📍 Exact File Locations - Balance Check Parameters

## All Parameter Sources at a Glance

```
┌────────────────────────────────────────────────────────────────────┐
│  PARAMETERS FOR BALANCE CHECK - WHERE THEY COME FROM               │
└────────────────────────────────────────────────────────────────────┘

📁 ROOT DIRECTORY (Project root)
│
├─ 📄 INFLOW_CODES_TEMPLATE.txt
│  └─ Contains: 34 inflow entries with values (m³)
│     Example line: "MERN_NDCDG_evap (evaporation) = 5 327 m³"
│     ⬇️  Read by: src/utils/template_data_parser.py line 170
│     ⬇️  Used in: BalanceCheckEngine.calculate_balance() line 181
│
├─ 📄 OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
│  └─ Contains: 64 outflow entries with values (m³)
│     Example line: "MERN_SOFT_losses (proc_losses) = 1 063 m³"
│     ⬇️  Read by: src/utils/template_data_parser.py line 205
│     ⬇️  Used in: BalanceCheckEngine.calculate_balance() line 185
│
├─ 📄 DAM_RECIRCULATION_TEMPLATE.txt
│  └─ Contains: 12 recirculation entries with values (m³)
│     Example line: "MERN_NDCDG_loop (self-loop) = 5 000 m³"
│     ⬇️  Read by: src/utils/template_data_parser.py line 240
│     ⬇️  Used in: BalanceCheckEngine.calculate_balance() line 189
│
├─ 📁 data/
│  ├─ 📄 water_balance.db
│  │  └─ Database (NOT used by balance check - templates used instead)
│  │
│  ├─ 📄 balance_check_config.json
│  │  └─ Contains: Which flows are enabled/disabled (JSON)
│  │     Example:
│  │     {
│  │       "inflows": [
│  │         {"code": "MERN_NDCDG_evap", "enabled": true},
│  │         {"code": "MERN_SOFT_losses", "enabled": false},
│  │         ...
│  │       ],
│  │       "outflows": [...],
│  │       "recirculation": [...]
│  │     }
│  │     ⬇️  Created/Modified by: src/ui/calculations.py line 780
│  │     ⬇️  Read by: src/utils/balance_check_engine.py line 114
│  │     ⬇️  Used by: BalanceCheckEngine._is_flow_enabled() line 143
│  │
│  └─ 📄 diagrams/
│     └─ (Flow diagrams - not used by balance check)
│
├─ 📁 config/
│  ├─ 📄 app_config.yaml
│  │  └─ General app config (NOT used by balance check)
│  │
│  └─ 📄 area_exclusions.json
│     └─ Contains: Which areas are excluded (JSON)
│        Example: {"excluded_areas": ["OLD_TSF", "STOCKPILE"]}
│        ⬇️  Created/Modified by: Area Exclusion Manager
│        ⬇️  Read by: src/utils/area_exclusion_manager.py line 26
│        ⬇️  Used by: BalanceCheckEngine.calculate_balance() line 180
│
└─ 📁 src/
   ├─ 📁 utils/
   │  ├─ 📄 template_data_parser.py
   │  │  ├─ Line 25: Loads template file paths
   │  │  ├─ Line 54: _load_all_templates() - Entry point
   │  │  ├─ Line 170: _load_inflows() - Reads INFLOW_CODES_TEMPLATE.txt
   │  │  ├─ Line 205: _load_outflows() - Reads OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
   │  │  ├─ Line 240: _load_recirculation() - Reads DAM_RECIRCULATION_TEMPLATE.txt
   │  │  ├─ Line 88: _parse_line() - Parses each line to extract code, name, value
   │  │  ├─ Line 140: _extract_area_from_code() - Gets area from code prefix
   │  │  └─ Result: self.inflows, self.outflows, self.recirculation lists
   │  │
   │  ├─ 📄 balance_check_engine.py
   │  │  ├─ Line 93: __init__() - Loads config from JSON
   │  │  ├─ Line 100: _load_balance_config() - Reads data/balance_check_config.json
   │  │  ├─ Line 126: _is_flow_enabled() - Checks if flow enabled in config
   │  │  ├─ Line 161: calculate_balance() - Main calculation method
   │  │  ├─ Line 180: Loops through inflows, checks enabled, sums values
   │  │  ├─ Line 184: Loops through outflows, checks enabled, sums values
   │  │  ├─ Line 188: Loops through recirculation, checks enabled, sums values
   │  │  └─ Returns: OverallBalanceMetrics with calculated totals
   │  │
   │  └─ 📄 area_exclusion_manager.py
   │     ├─ Line 15: CONFIG_FILE = config/area_exclusions.json
   │     ├─ Line 23: _load_exclusions() - Reads area exclusions
   │     └─ Used by: BalanceCheckEngine to exclude certain areas
   │
   └─ 📁 ui/
      └─ 📄 calculations.py
         ├─ Line 288: _calculate_balance() - User clicks Calculate
         ├─ Line 699: _open_balance_config_editor() - User clicks Configure
         ├─ Line 780: Saves config to data/balance_check_config.json
         └─ Line 916: _update_balance_check_summary() - Displays results
```

---

## Execution Flow: Line Numbers

```
👤 USER STARTS APP
    ⬇️
📄 src/main.py
    ⬇️
🔄 WaterBalanceApp.__init__()
    ⬇️
📄 src/utils/template_data_parser.py
├─ Line 54: _load_all_templates()
├─ Line 170: _load_inflows()
│  ├─ Open: INFLOW_CODES_TEMPLATE.txt
│  ├─ Line 88: _parse_line() for each line
│  ├─ Line 140: _extract_area_from_code()
│  └─ Result: 34 BalanceEntry objects in self.inflows
├─ Line 205: _load_outflows()
│  ├─ Open: OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
│  ├─ Parse each line → 64 BalanceEntry objects
│  └─ Result: self.outflows = [64 entries]
└─ Line 240: _load_recirculation()
   ├─ Open: DAM_RECIRCULATION_TEMPLATE.txt
   ├─ Parse each line → 12 BalanceEntry objects
   └─ Result: self.recirculation = [12 entries]

👤 USER CONFIGURES
    ⬇️
📄 src/ui/calculations.py
├─ Line 699: _open_balance_config_editor()
├─ Line 728: Get flows from parser (uses above loaded data!)
├─ Line 780: Dialog shows flows to user
├─ Line 800: User unchecks flows
└─ Line 835: Save config to data/balance_check_config.json

👤 USER CALCULATES
    ⬇️
📄 src/ui/calculations.py
├─ Line 288: _calculate_balance()
└─ Line 291: self.balance_engine.calculate_balance()
    ⬇️
📄 src/utils/balance_check_engine.py
├─ Line 161: calculate_balance() starts
├─ Line 178: for entry in self.parser.inflows:
│  ├─ entry.code, entry.value_m3, entry.area
│  ├─ Line 179: Check if excluded area
│  └─ Line 180: Call self._is_flow_enabled(entry.code, 'inflows')
│     ⬇️
│     Line 143: _is_flow_enabled()
│     ├─ Line 149: Check if self.config exists
│     ├─ Line 152: Check if flow_type in config
│     ├─ Line 156: Loop through config to find code
│     └─ Line 157: Return item.get('enabled') ← THIS CONTROLS IT!
│     ⬇️
│  ├─ Line 181: if enabled: metrics.total_inflows += entry.value_m3
│  └─ else: skip
├─ Line 184: Same for outflows (64 entries)
├─ Line 188: Same for recirculation (12 entries)
└─ Return: OverallBalanceMetrics
    ⬇️
📄 src/ui/calculations.py
├─ Line 916: _update_balance_check_summary()
├─ Show: metrics.total_inflows (only enabled flows!)
├─ Show: metrics.total_outflows (only enabled flows!)
└─ Show: metrics.balance_difference

👤 USER SEES RESULTS
```

---

## File Dependencies

```
Template Files
    ↓
    └─ INFLOW_CODES_TEMPLATE.txt (Line values)
    ├─ OUTFLOW_CODES_TEMPLATE_CORRECTED.txt (Line values)
    └─ DAM_RECIRCULATION_TEMPLATE.txt (Line values)
            ⬇️  Parsed
    
TemplateDataParser (src/utils/template_data_parser.py)
    ├─ Creates BalanceEntry objects with value_m3
    ├─ Singleton: get_template_parser()
    └─ Loaded at: App startup
            ⬇️  Used by
    
BalanceCheckEngine (src/utils/balance_check_engine.py)
    ├─ Loads config from data/balance_check_config.json
    ├─ Filters flows: only include if enabled=true
    ├─ Sums values: sum of entry.value_m3
    └─ Singleton: get_balance_check_engine()
            ⬇️  Called from
    
CalculationsModule (src/ui/calculations.py)
    ├─ Shows Configure dialog
    ├─ Saves config to data/balance_check_config.json
    ├─ Calls engine.calculate_balance()
    └─ Displays results in UI
```

---

## Parameter Sources: Complete Map

```
┌─ VALUE PARAMETERS ─────────────────────────┐
│ Source Files:                              │
│  ├─ INFLOW_CODES_TEMPLATE.txt              │
│  ├─ OUTFLOW_CODES_TEMPLATE_CORRECTED.txt   │
│  └─ DAM_RECIRCULATION_TEMPLATE.txt         │
│                                            │
│ Parser File: src/utils/template_data_parser.py
│  ├─ _parse_line() extracts value
│  └─ Creates BalanceEntry.value_m3
│                                            │
│ Engine File: src/utils/balance_check_engine.py
│  ├─ Accesses: entry.value_m3
│  └─ Sums: metrics.total_inflows += value_m3
│                                            │
│ UI File: src/ui/calculations.py
│  └─ Displays: "Total Inflows: {value} m³"
└────────────────────────────────────────────┘

┌─ AREA PARAMETERS ──────────────────────────┐
│ Derived From: Flow codes (MERN_ prefix)   │
│                                            │
│ Parser File: src/utils/template_data_parser.py
│  ├─ _extract_area_from_code()
│  └─ Creates BalanceEntry.area = "NDCD1-4" │
│                                            │
│ Engine File: src/utils/balance_check_engine.py
│  ├─ Checks: if entry.area not in excluded │
│  └─ Uses: For per-area breakdown
└────────────────────────────────────────────┘

┌─ ENABLED/DISABLED PARAMETERS ──────────────┐
│ Source File: data/balance_check_config.json│
│                                            │
│ UI File: src/ui/calculations.py
│  ├─ _open_balance_config_editor()
│  └─ Saves: data/balance_check_config.json
│                                            │
│ Engine File: src/utils/balance_check_engine.py
│  ├─ _load_balance_config()
│  ├─ _is_flow_enabled()
│  └─ Returns: True/False to include/exclude
└────────────────────────────────────────────┘

┌─ EXCLUDED AREAS ───────────────────────────┐
│ Source File: config/area_exclusions.json   │
│                                            │
│ Manager File: src/utils/area_exclusion_manager.py
│  ├─ _load_exclusions()
│  └─ get_excluded_areas()
│                                            │
│ Engine File: src/utils/balance_check_engine.py
│  └─ Checks: if area in excluded_areas
└────────────────────────────────────────────┘
```

---

## Summary: The 5 Sources of Truth

| # | Parameter Type | File | Read By | How |
|---|---|---|---|---|
| 1 | Inflow Values (m³) | `INFLOW_CODES_TEMPLATE.txt` | TemplateDataParser | Line by line parsing |
| 2 | Outflow Values (m³) | `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt` | TemplateDataParser | Line by line parsing |
| 3 | Recirculation Values (m³) | `DAM_RECIRCULATION_TEMPLATE.txt` | TemplateDataParser | Line by line parsing |
| 4 | Enabled/Disabled Flows | `data/balance_check_config.json` | BalanceCheckEngine | JSON load, then lookup |
| 5 | Excluded Areas | `config/area_exclusions.json` | AreaExclusionManager | JSON load, then check |

**When balance calculation runs:**
1. Get values from Sources 1-3 (template files)
2. Get enable status from Source 4 (config JSON)
3. Get excluded areas from Source 5 (exclusions JSON)
4. Filter: only sum values from Sources 1-3 where Source 4 says enabled=true AND area not in Source 5
5. Display result: "Total = X m³"
