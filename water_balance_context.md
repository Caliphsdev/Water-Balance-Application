# Mine Water Balance Context & Rules
Version: 1.0
Purpose: Authoritative context for fixing and simplifying the water balance engine

---

## 1. Objective

This water balance engine supports a platinum mine with UG2 and Merensky operations.
It must serve TWO audiences:

1. Regulators / auditors (compliance, defensibility)
2. Operations / management (decision-making, KPIs)

The engine must therefore separate:
- Scientific water accounting
- Operational water efficiency metrics

---

## 2. Core Scientific Principle (Non-Negotiable)

There is ONE valid water balance equation:

Fresh Inflows
– Total Outflows
– Δ Storage
= Balance Error

Where:

Fresh Inflows include ONLY:
- River abstraction
- Borehole abstraction
- Municipal supply
- Other external freshwater sources

Fresh Inflows EXCLUDE:
- TSF return water
- Internal recycling
- Process recirculation

---

## 3. Recycled Water Rule (Critical)

Recycled water (e.g. TSF return water):
- Is NOT a source of water
- Must NEVER be used to close the balance
- Is tracked for KPIs only

Recycled water may be:
- Displayed
- Reported
- Benchmarked

But MUST NOT:
- Affect balance error
- Be inferred without explicit labelling

---

## 4. Outflows (Explicit and Complete)

Outflows MUST be reported explicitly as:

- Tailings entrained water
- Product moisture
- Evaporation losses
- Seepage losses
- Discharge (if any)
- Dust suppression
- Mining water use
- Domestic water use

Auxiliary uses (dust, mining, domestic):
- Are NOT plant water
- Are NOT subtracted from “fresh-to-plant”
- Are independent outflows

---

## 5. Storage Handling

Priority order for storage change (Δ Storage):

1. Measured opening and closing volumes (authoritative)
2. Modelled storage balance (only if data missing)

Modelled storage must:
- Include rainfall, evaporation, seepage
- Be clearly flagged as "SIMULATED"

Evaporation and seepage:
- Affect storage
- Must NOT be double-counted as outflows

---

## 6. TSF Return Water Rules

TSF return water must be:
- Provided as measured input (Excel, DB)
OR
- Provided as explicitly labelled estimate

TSF return water must NEVER be:
- Back-calculated silently from plant math
- Used to force balance closure

If TSF return data is missing:
- Balance proceeds WITHOUT it
- Dashboard flags data quality warning

---

## 7. Plant Water Accounting (Secondary Balance)

Plant water calculations (gross, net, retention):
- Are PROCESS metrics
- Do NOT define the system water balance

Plant metrics may include:
- Gross plant water
- Net plant water
- Tailings water
- Product moisture

These must reconcile internally but remain separate from system closure.

---

## 8. Operating Modes

### 8.1 Regulator Mode
Purpose: Compliance, licensing, audits

Rules:
- Conservative assumptions
- No inferred flows
- Measured data preferred
- Clear error reporting
- No optimisation logic

Outputs:
- Fresh inflows
- Explicit outflows
- Δ Storage
- Balance error (%)
- Data quality flags

---

### 8.2 Operations Mode
Purpose: Efficiency, optimisation, planning

Rules:
- May show inferred or estimated values
- Must clearly label estimates
- Can include KPIs and ratios

Additional Outputs:
- % recycled water
- Plant water intensity (m³/t)
- TSF recovery efficiency
- Storage utilisation

---

## 9. Dashboard Design (Required)

### Top KPIs
- Fresh Water Used (m³)
- Recycled Water Used (m³)
- % Recycled
- Balance Error (%)
- Status: CLOSED / WARNING / FAIL

### Main Visual
- Sankey or stacked flow:
  Fresh In → Uses → Losses → Storage

### Tabs
1. System Balance (authoritative)
2. Recycled Water & TSF
3. Plant Water Performance
4. Storage & Dams
5. Data Quality & Assumptions

---

## 10. Legacy / Template Balance Engine

The template-based balance check engine:
- Is QA ONLY
- Must never be presented as a final balance
- Must not be compared numerically to the main balance

---

## 11. Refactor Guidance

When reviewing existing code:
- Prefer deletion over addition
- Prefer explicit data over derived values
- Prefer clarity over cleverness

If a calculation:
- Cannot be explained in one sentence → refactor or remove
- Depends on multiple fallbacks → flag as risk
- Exists only for closure → remove

---

## 12. Success Criteria

The refactored system is correct if:
- A regulator can audit it without explanation
- A dashboard user understands it in 30 seconds
- Balance error reflects reality, not model gymnastics
