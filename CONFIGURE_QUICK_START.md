# 🎯 Quick Start - Configure Balance Check Feature

## The Problem It Solves

You were asking: **"Why does Configure Balance Check exist if it always uses the .txt files?"**

**Answer**: Now it doesn't! The Configure function now actually works and controls what flows are included in your balance calculation.

---

## How to Use It

### Step 1: Open Configuration
1. Launch the app: `python src/main.py`
2. Go to **Calculations** module
3. Click button: **"⚙️ Configure Balance Check"**

### Step 2: Select Flows
A dialog appears with 3 tabs:
- **Inflows** - 34 sources (all checked by default)
- **Recirculation** - 12 loops (all checked by default)
- **Outflows** - 64 flows (all checked by default)

Each row shows:
```
☑️ MERN_NDCDG_evap   Evaporation (5,327 m³)
☑️ MERN_NDCDG → MERN_ND   Underground Return (90,320 m³)
☑️ MERN_SOFT_losses   Softening Plant losses (1,063 m³)
...
```

### Step 3: Uncheck to Exclude
**To exclude specific flows:**
1. Find the flow you want to exclude
2. Click the checkbox to uncheck it
3. It will be marked as disabled (☐)

**Example**: If you want to exclude evaporation calculations:
```
☐ MERN_NDCDG_evap   Evaporation (5,327 m³)   ← UNCHECKED - will be excluded
```

### Step 4: Save
Click button: **"💾 Save Configuration"**

Message shows: `✅ Balance check configuration saved! X flows will be included in calculations.`

---

## What Happens Next

When you calculate the balance:
1. Only **enabled (checked)** flows are included
2. Disabled flows are ignored
3. Balance results reflect only the selected flows

**Example:**
- If you disable 20 outflows
- Total Outflows will be calculated from only 44 remaining outflows
- Balance difference changes accordingly

---

## Common Scenarios

### Scenario 1: Exclude Areas
You don't want OLD_TSF to be included:

1. Open Configure
2. Go to **Outflows** tab
3. Find all flows starting with `TRTD_` or `OT_`
4. Uncheck all of them
5. Save

Result: OLD_TSF flows are excluded from balance calculation

### Scenario 2: Test Specific Flows
You want to see balance with ONLY inflows and outflows (no recirculation):

1. Open Configure
2. Go to **Recirculation** tab
3. Uncheck all 12 entries
4. Save

Result: Balance calculation ignores recirculation completely

### Scenario 3: Exclude Problem Flows
Some flows are causing large errors:

1. Open Configure
2. Find the problematic flows
3. Uncheck them
4. Save and recalculate
5. See if balance improves

---

## Under the Hood

**Files Involved:**
- Config saved to: `data/balance_check_config.json`
- Engine uses it: `src/utils/balance_check_engine.py`
- Dialog in: `src/ui/calculations.py`

**When You Calculate:**
```
User clicks "Calculate Balance"
         ⬇️
Engine loads `balance_check_config.json`
         ⬇️
Filters flows: only includes `enabled: true`
         ⬇️
Sums up only enabled flows
         ⬇️
Shows results
```

**Backward Compatibility:**
If no config file exists → ALL flows included (original behavior)

---

## Pro Tips

✅ **Save Different Configs**
- Configure for full calculation
- Save the config file
- Reconfigure with different flows
- Toggle between them by copying/renaming config files

✅ **Test Incrementally**
- Start with all flows enabled (default)
- Disable 5-10 at a time
- See how balance changes
- Find problem flows

✅ **Document Your Choices**
- Write down which flows you disabled and why
- Makes it easier to explain the balance later

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Configure button does nothing" | Make sure you have templates: `INFLOW_CODES_TEMPLATE.txt`, `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt`, `DAM_RECIRCULATION_TEMPLATE.txt` |
| "Dialog shows no flows" | Check templates are in root folder and have data |
| "Changes not affecting balance" | Make sure you clicked "💾 Save Configuration" |
| "Want to include all flows again" | Delete `data/balance_check_config.json` and recalculate |

---

## Technical Details

**Configuration File Format** (`data/balance_check_config.json`):
```json
{
  "inflows": [
    {
      "code": "MERN_NDCDG_evap",
      "name": "Evaporation",
      "area": "NDCD1-4",
      "enabled": true
    },
    ...
  ],
  "outflows": [...],
  "recirculation": [...]
}
```

**Engine Logic:**
```python
for entry in parser.outflows:
    if self._is_flow_enabled(entry.code, 'outflows'):
        # Include in calculation
        metrics.total_outflows += entry.value_m3
```

---

✅ **Done!** Now Configure Balance Check actually does something!
