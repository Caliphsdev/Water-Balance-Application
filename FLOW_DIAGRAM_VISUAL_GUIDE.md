# Flow Diagram - Quick Visual Guide

## What You'll See Now

```
┌─────────────────────────────────────────────────────────────────┐
│ WATER FLOW DIAGRAM                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SOURCES     │  TREATMENT   │  STORAGE      │  DISTRIBUTION   │
│  ┌─────────┐ │  ┌────────┐  │  ┌────────┐   │  ┌────────────┐ │
│  │Borehole │─→│Softening│──→│Reservoir│───→│Guest House   │ │
│  └─────────┘ │  └────────┘  │  └────────┘   │  └────────────┘ │
│              │              │               │                 │
│  ┌────────┐  │              │               │  ┌────────────┐ │
│  │Rainfall│  │              │               │  │   Offices  │ │
│  └────────┘  │              │               │  └────────────┘ │
│              │  ┌────────┐  │               │                 │
│              │  │Sewage  │  │               │  ┌────────────┐ │
│              │  │Treat.  │  │               │  │Septic Tank │ │
│              │  └────────┘  │               │  └────────────┘ │
│              │              │               │                 │
│              │              │  ┌────────┐   │                 │
│              │              │  │  NDCD  │───→ Mining Dewater │
│              │              │  └────────┘   │                 │
│              │              │               │  ┌────────────┐ │
│              │              │               │  │   Losses   │ │
│              │              │               │  └────────────┘ │
│                                                                 │
│  Legend:                                                        │
│  ─→ Blue arrow: Clean water flows                              │
│  ─→ Red arrow: Dirty/Effluent flows                            │
│  ─→ Black arrow: Losses                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components You'll See

| Component | Color | Position | Type |
|-----------|-------|----------|------|
| Borehole (NDGWA 1-6) | Light Blue | Left top | SOURCE |
| Direct Rainfall | Light Lavender | Left middle | SOURCE |
| Softening Plant | Orange | Left-center | TREATMENT |
| Reservoir | Dark Blue (Oval) | Center | STORAGE |
| **Guest House** | Light Blue | **Top-left middle** | **CONSUMPTION** |
| **Offices** | Light Blue | **Top-right middle** | **CONSUMPTION** |
| Sewage Treatment | Orange | Center | TREATMENT |
| NDCD 1-2/NDSWD 1 | Darker Blue (Oval) | Right-center | STORAGE |
| North Decline | Red | Bottom center | PROCESS |
| North Shaft | Light Red | Bottom left | PROCESS |
| Septic Tank | White/Red border | Top right | CONSUMPTION |
| Losses | White/Black border | Right middle | LOSS |

## Flow Values

Typical flows you'll see labeled on arrows:
- **71,530** m³ - Borehole to Softening
- **47,485** m³ - Softening to Reservoir
- **16,105** m³ - Reservoir to Guest House ← NEW!
- **14,246** m³ - Reservoir to Offices ← NEW!
- **2,594** m³ - Offices to Septic Tank ← NEW!
- **1,470** m³ - Guest House to Septic Tank ← NEW!
- **947** m³ - Guest House to Losses

...and more showing the complete water balance

## Color Coding

### Component Colors
- **Light Blue (#8ab7e6)** - Boreholes/Sources
- **Light Lavender (#b7d4f3)** - Natural sources (Rainfall)
- **Orange (#e89c3d)** - Treatment facilities
- **Dark Blue (#4b78a8)** - Main storage
- **Darker Blue (#3f6ea3)** - Secondary storage
- **Light Blue (#5d88b6)** - Consumption facilities
- **Red (#a34136)** - Mining operations
- **White + Red Border** - Septic/Special handling

### Flow Arrow Colors
- **Blue (#4b78a8)** - Clean water
- **Red (#e74c3c)** - Dirty/Effluent water
- **Black** - Water losses/evaporation

## Interaction

- **Scroll**: Use mouse wheel to pan around
- **Horizontal scroll**: Use shift + wheel or bottom scrollbar
- **Zoom**: Not yet, but can be added

## If Something Looks Off

1. Check the logs - they tell you exactly what was drawn
2. The diagram loads JSON data - verify `data/diagrams/ug2_north_decline.json` exists
3. All 12 components should be visible
4. All 12 connections should show arrows with labels

## If You Want to Change Positions

Edit the JSON file directly:
```
data/diagrams/ug2_north_decline.json
  └── nodes array: edit "x" and "y" values
      └── Restart app to see changes
```

NO code changes needed! It's all data-driven now.
