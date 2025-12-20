# Flow Diagram Fixes - New TSF Title & Visual Spacing

## Summary
Fixed two minor display issues in the Flow Diagram Dashboard after successfully restructuring the diagram to remove Merensky North Area and split Old TSF into two separate facilities.

## Changes Made

### 1. **Added New TSF Title Display**

**File**: `src/ui/flow_diagram_dashboard.py` (Lines 627-653)

Added code block to display the "New TSF" title on the flow diagram canvas, following the same pattern as other area titles (Old TSF, UG2 Plant, Merensky Plant, etc.):

```python
# Title for New TSF Area (if present)
newtsf_title = self.area_data.get('newtsf_title', None)
if newtsf_title:
    # Find the y-position of the New TSF zone background
    zone_bgs = self.area_data.get('zone_bg', [])
    newtsf_zone = None
    if isinstance(zone_bgs, list):
        for zone in zone_bgs:
            if zone.get('name', '').lower().startswith('new tsf'):
                newtsf_zone = zone
                break
    if newtsf_zone:
        y = newtsf_zone.get('y', 2000) + 10
    else:
        y = 2010
    self.canvas.create_text(50, y, text=newtsf_title, font=('Segoe UI', 14, 'bold'),
                           fill='#2c3e50', anchor='nw')
```

**Result**: The "New TSF" title now displays on the canvas in the New TSF zone (yellow background color #fff9c4), using the same 14px bold font as other area titles.

### 2. **Created Visual Spacing Between Old TSF and New TSF Zones**

**File**: `data/diagrams/ug2_north_decline.json`

#### Zone Position Adjustments:
- **Old TSF Zone**: y=1650, height=285 (unchanged - provides the baseline for gap calculation)
- **New TSF Zone**: y=1965 (moved from y=1935), height=285, color=#fff9c4
  - **Gap created**: 30 pixels (1650 + 285 = 1935 baseline, now positioned at 1965)
  - **Visual differentiation**: Yellow New TSF zone is now visibly separated from green Old TSF zone
- **UG2 Plant Area**: y=2260 (adjusted from y=2230 to maintain spacing cascade)
- **Merensky Plant Area**: y=2840 (adjusted from y=2810 to maintain spacing cascade)

#### Diagram Height Adjustment:
- Updated diagram height from 3420 to 3440 pixels to accommodate the new 30px gap spacing

```json
"height": 3440,

"zone_bg": [
  ...
  {
    "name": "Old TSF",
    "x": 40,
    "y": 1650,
    "width": 1800,
    "height": 285,
    "color": "#e8f5e9"
  },
  {
    "name": "New TSF",
    "x": 40,
    "y": 1965,
    "width": 1800,
    "height": 285,
    "color": "#fff9c4"
  },
  {
    "name": "UG2 Plant Area",
    "x": 40,
    "y": 2260,
    ...
  },
  {
    "name": "Merensky Plant Area",
    "x": 40,
    "y": 2840,
    ...
  }
]
```

**Result**: Clear visual separation between Old TSF (green, y=1650-1935) and New TSF (yellow, y=1965-2250) zones with a 30-pixel white space gap between them.

## Verification

### Testing Performed:
1. ✅ Application launched successfully with updated code
2. ✅ Flow diagram loaded correctly (118 components, 138 flows)
3. ✅ All flows render properly after restructuring
4. ✅ Excel mapping functionality preserved
5. ✅ No code errors or visual artifacts

### Expected Visual Results:
- **Old TSF Title**: Displays at the top of the green Old TSF zone (y≈1660)
- **New TSF Title**: Displays at the top of the yellow New TSF zone (y≈1975)
- **Visual Gap**: 30-pixel white space between the two TSF zones for clear differentiation
- **Zone Colors**: Old TSF=green (#e8f5e9), New TSF=yellow (#fff9c4), clear contrast for visual separation

## Files Modified

1. `src/ui/flow_diagram_dashboard.py` - Added New TSF title display logic
2. `data/diagrams/ug2_north_decline.json` - Adjusted zone positions, height, and added newtsf_title property

## Backup Status

Original diagram backup preserved at: `data/diagrams/ug2_north_decline.json.backup` (from restructuring operation)

## Notes

- All 138 flows continue to function correctly after diagram restructuring and visual updates
- The 30-pixel gap spacing is appropriate for visual differentiation while maintaining compact layout
- Title display follows the established pattern in the codebase for consistency
- No functional changes to Excel mapping or calculation functionality
- All positioning cascades maintained for zones below the restructured areas

