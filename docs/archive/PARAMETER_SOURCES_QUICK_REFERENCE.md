# ⚡ Quick Answer: Where Balance Check Parameters Come From

## TL;DR - The Complete Flow

```
Template Files (5,327 m³)
         ↓
TemplateDataParser
         ↓
BalanceEntry objects with values
         ↓
BalanceCheckEngine
         ↓
Check: Config JSON says enabled=true?
         ↓
IF yes: Add to total_inflows/outflows/recirculation
IF no:  Skip
         ↓
Display results showing only enabled flows
```

---

## 3 Types of Parameters

### 1. **VALUE PARAMETERS** (m³ amounts)
- **From:** Lines in template files
- **Example:** `MERN_NDCDG_evap = 5,327 m³`
- **File:** `INFLOW_CODES_TEMPLATE.txt`, etc.
- **Read by:** `TemplateDataParser._parse_line()`
- **Stored in:** `BalanceEntry.value_m3`
- **Used in:** Sum total_inflows/outflows/recirculation

### 2. **AREA PARAMETERS** (location)
- **From:** Code prefix extraction
- **Example:** `MERN_` prefix → area = `NDCD1-4`
- **Read by:** `TemplateDataParser._extract_area_from_code()`
- **Stored in:** `BalanceEntry.area`
- **Used in:** Filter by excluded areas, per-area calculations

### 3. **ENABLED/DISABLED PARAMETERS** (user choice)
- **From:** `data/balance_check_config.json`
- **Example:** `{"code": "MERN_SOFT_losses", "enabled": false}`
- **Read by:** `BalanceCheckEngine._load_balance_config()`
- **Stored in:** `BalanceCheckEngine.config`
- **Used in:** `_is_flow_enabled()` to include/exclude flows

---

## File-to-Code Mapping

| File | What's In It | Read By | Stored In | Used In |
|------|-------------|---------|-----------|---------|
| `INFLOW_CODES_TEMPLATE.txt` | 34 inflow entries + values | `TemplateDataParser._load_inflows()` | `parser.inflows` list | `calculate_balance()` loop |
| `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt` | 64 outflow entries + values | `TemplateDataParser._load_outflows()` | `parser.outflows` list | `calculate_balance()` loop |
| `DAM_RECIRCULATION_TEMPLATE.txt` | 12 recirculation entries + values | `TemplateDataParser._load_recirculation()` | `parser.recirculation` list | `calculate_balance()` loop |
| `data/balance_check_config.json` | Which flows are enabled | `BalanceCheckEngine._load_balance_config()` | `engine.config` dict | `_is_flow_enabled()` |
| `config/area_exclusions.json` | Which areas are excluded | `AreaExclusionManager._load_exclusions()` | `exclusion_manager.excluded_areas` | `calculate_balance()` area check |

---

## Code Locations - Where Each Step Happens

```
WHEN: App starts
WHERE: src/main.py → WaterBalanceApp.__init__()
WHAT: Creates TemplateDataParser singleton
RESULT: self.parser.inflows/outflows/recirculation loaded with 110 entries + values

WHEN: App starts  
WHERE: src/utils/balance_check_engine.py → BalanceCheckEngine.__init__()
WHAT: Creates AreaExclusionManager, loads config from JSON
RESULT: self.config loaded from data/balance_check_config.json

WHEN: User clicks Configure Balance Check
WHERE: src/ui/calculations.py → _open_balance_config_editor()
WHAT: Shows dialog with template flows, user unchecks some
RESULT: Saves config to data/balance_check_config.json

WHEN: User clicks Calculate Balance
WHERE: src/ui/calculations.py → _calculate_balance()
WHAT: Calls engine.calculate_balance()
RESULT: BalanceCheckEngine.calculate_balance() executes

WHEN: Engine calculates
WHERE: src/utils/balance_check_engine.py → calculate_balance() (line 161)
WHAT: Loop through parser.inflows/outflows/recirculation
  └─ For each entry: Check if enabled in config
  └─ If yes: Add entry.value_m3 to metrics total
  └─ If no: Skip entry
RESULT: OverallBalanceMetrics with calculated totals

WHEN: Results shown
WHERE: src/ui/calculations.py → _update_balance_check_summary()
WHAT: Display metrics.total_inflows/outflows/recirculation values
RESULT: User sees filtered totals in UI
```

---

## Visual: Data Flow Through The System

```
                    TEMPLATE FILES (START)
                    ├─ INFLOW_CODES_TEMPLATE.txt
                    ├─ OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
                    └─ DAM_RECIRCULATION_TEMPLATE.txt
                             ↓
                    TemplateDataParser
                    ├─ _load_inflows() → 34 BalanceEntry objects
                    ├─ _load_outflows() → 64 BalanceEntry objects
                    └─ _load_recirculation() → 12 BalanceEntry objects
                             ↓
                    self.parser.inflows/outflows/recirculation
                    (Each BalanceEntry has code, name, area, value_m3)
                             ↓
                    ┌─────────────────────────┐
                    │ BalanceCheckEngine      │
                    │ .calculate_balance()    │
                    └────────────┬────────────┘
                                 ↓
                    Load data/balance_check_config.json
                                 ↓
    ┌───────────────────────────┴────────────────────────────┐
    ↓                                                         ↓
for entry in parser.outflows:              Check: _is_flow_enabled()
  └─ 64 iterations                         ├─ Look in config dict
                                           ├─ Find flow by code
                                           └─ Return enabled status
    ↓                                                         ↓
    └─────────────────────────┬────────────────────────────┘
                              ↓
                    if enabled (config says true):
                      └─ metrics.total_outflows += entry.value_m3
                    else (config says false):
                      └─ Skip (don't add value)
                              ↓
                    OverallBalanceMetrics returned
                    ├─ total_inflows = sum
                    ├─ total_outflows = sum  ← FILTERED!
                    └─ balance_difference = inflows - outflows - recirculation
                              ↓
                    UI displays results
                    └─ "Total Outflows: 569,204 m³"  (only enabled flows!)
```

---

## The Key Filter: _is_flow_enabled()

```python
# FILE: src/utils/balance_check_engine.py

def _is_flow_enabled(self, flow_code: str, flow_type: str) -> bool:
    # Step 1: Check if config exists
    if not self.config:
        return True  # No config = include all flows
    
    # Step 2: Check if flow type in config
    if flow_type not in self.config:
        return True  # Type not in config = include all of that type
    
    # Step 3: Look up flow in config
    flows_in_config = self.config.get(flow_type, [])
    for item in flows_in_config:
        if item.get('code') == flow_code:
            # Found it! Return its enabled status
            return item.get('enabled', True)
    
    # Step 4: If we got here, flow not in config
    return False  # Not in config = exclude it

# USAGE:
# if self._is_flow_enabled('MERN_SOFT_losses', 'outflows'):
#     metrics.total_outflows += entry.value_m3  ← Only if enabled!
```

---

## One Complete Example

```
SCENARIO: User disables "MERN_SOFT_losses" outflow

1. FILE: OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
   Line: MERN_SOFT_losses (proc_losses) = 1 063 m³
   
2. PARSE: Template parser reads line
   → Creates BalanceEntry(
       code='MERN_SOFT_losses',
       value_m3=1063.0,
       area='NDSWD1-2'
     )
   
3. STORE: Added to parser.outflows list
   parser.outflows = [
       BalanceEntry(..., code='MERN_SOFT_losses', value_m3=1063.0),
       ... 63 more entries
   ]
   
4. CONFIGURE: User clicks Configure Balance Check
   → Dialog shows MERN_SOFT_losses with checkbox ☑️
   → User unchecks it ☐
   → Saves to data/balance_check_config.json:
      {
        "outflows": [
          {"code": "MERN_SOFT_losses", "enabled": false},
          ... rest
        ]
      }
   
5. CALCULATE: User clicks Calculate Balance
   → Engine loops through parser.outflows
   → Gets entry for MERN_SOFT_losses with value_m3=1063.0
   → Calls: _is_flow_enabled('MERN_SOFT_losses', 'outflows')
   → Looks up config['outflows']
   → Finds: {"code": "MERN_SOFT_losses", "enabled": false}
   → Returns: False
   → Action: SKIP! Don't add 1,063 to total_outflows
   
6. RESULT: Total Outflows = 1,289,125 m³
   (vs 1,290,188 m³ if included)
   → 1,063 m³ EXCLUDED because config says enabled=false
```

---

## Summary Answer

**Q: Where are the balance check parameters being read or activated?**

**A:**
1. **Numerical values (m³)** come from template .txt files, read by TemplateDataParser
2. **Area assignment** comes from code prefix extraction (MERN_ → area code)
3. **Enable/Disable status** comes from data/balance_check_config.json (user controlled)
4. **Excluded areas** come from config/area_exclusions.json
5. **Activation happens** in BalanceCheckEngine.calculate_balance() when it:
   - Loops through parser entries
   - Checks if enabled via _is_flow_enabled()
   - Sums ONLY enabled flows
   - Returns filtered metrics
6. **Display** in UI shows final results with only enabled flows

The key is the **configuration filter** - it controls which of the 110 template entries are actually included in the balance calculation!
