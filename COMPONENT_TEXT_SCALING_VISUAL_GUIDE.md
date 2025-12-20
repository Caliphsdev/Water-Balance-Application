# 🎨 Component Text Scaling - Visual Guide

## The Problem → The Solution

### What Was Happening ❌

When you resized components, the text stayed the same size:

```
┌────────┐                    ┌─────────────────────────────┐
│ Label  │  Resize to large   │ Label                       │
└────────┘        →           │ (text still 8pt, looks tiny)│
                              └─────────────────────────────┘

┌─────────────────────────────┐    Resize to small    ┌──────┐
│ Component Label Text        │         →             │Label │
│ (text 8pt, spills out!)     │                       │Text! │
└─────────────────────────────┘                       │Overfl│
                                                      └──────┘
```

**Result:** Tiny text in large components, overflowing text in small components 😞

---

### What Happens Now ✅

Text automatically scales with component size:

```
Small Component (40×40px)      Medium Component (80×50px)     Large Component (150×80px)
┌─────────────┐                ┌────────────────────┐          ┌──────────────────────────┐
│             │                │  Component Label   │          │    Component Label       │
│   Label     │                │                    │          │     Main Text Here       │
│  (6pt)      │                │   (8pt)            │          │     (10pt)               │
│             │                │                    │          │  Secondary Info          │
└─────────────┘                └────────────────────┘          │     (8pt)                │
                                                              └──────────────────────────┘
✅ Perfect fit    ✅ Readable            ✅ Professional looking
```

---

## Scaling Formula

### How Font Size is Calculated

```
Component Dimension: ████████████████ (40px)
Result: 6pt font

Component Dimension: ███████████████████████████████ (80px)
Result: 8pt font

Component Dimension: ███████████████████████████████████████████████████ (150px)
Result: 10pt font
```

**Formula:**
```
font_size = component_size ÷ 15
(constrained between 6pt minimum and 10pt maximum)
```

---

## What Scales

### 1. Primary Text (Component Name)
```
┌──────────────────┐
│ ★ Largest font   │  ← Primary font scales
└──────────────────┘
```

### 2. Secondary Text (Additional labels)
```
┌──────────────────────┐
│   Main Label         │  ← Primary (scaled)
│   Secondary text     │  ← Secondary (scaled smaller)
└──────────────────────┘
```

### 3. Type Labels
```
┌──────────────────┐
│  Component       │
│  (SOURCE)        │  ← Type label scales
└──────────────────┘
```

### 4. Lock Icon
```
┌──────────────────┐
│ 🔒 Component     │  ← Lock icon size scales
└──────────────────┘
```

### 5. Line Spacing
```
┌─────────────────────────┐
│ Line 1                  │
│ Line 2                  │  ← Spacing adapts
│ Line 3                  │     to component
└─────────────────────────┘     height
```

---

## Visual Comparison: Before vs After

### Scenario 1: Very Small Component (40×40)

**BEFORE:**
```
┌──────────────────┐
│Component Label   │  ← 8pt text too big!
│Text Overflows!!  │
└──────────────────┘
```

**AFTER:**
```
┌─────────────┐
│  Component  │  ← 6pt text fits!
│   Label     │
└─────────────┘
```

---

### Scenario 2: Medium Component (100×60)

**BEFORE:**
```
┌──────────────────────────────┐
│Component Label               │  ← 8pt looks OK
└──────────────────────────────┘
```

**AFTER:**
```
┌──────────────────────────────┐
│   Component Label            │  ← 8pt optimized
│      Secondary Info          │
└──────────────────────────────┘
```

---

### Scenario 3: Large Component (200×100)

**BEFORE:**
```
┌─────────────────────────────────────────┐
│ Component Label                         │  ← 8pt looks tiny
└─────────────────────────────────────────┘
```

**AFTER:**
```
┌─────────────────────────────────────────┐
│      Component Label                    │  ← 10pt fills space well
│   Secondary Information Text            │
│    Additional Details Here              │
└─────────────────────────────────────────┘
```

---

## Text Truncation

### Long Text Handling

If text is too long for the component width, it gets truncated:

```
Original text: "This is a very long component label that doesn't fit"

In small component:          In medium component:      In large component:
┌──────────────┐            ┌────────────────────┐    ┌─────────────────────────┐
│This is a ve… │            │This is a very lon…│    │This is a very long com…│
└──────────────┘            └────────────────────┘    └─────────────────────────┘
  ↑                           ↑                        ↑
  Max characters based on width
```

**Formula:** `max_chars = component_width ÷ 7`

---

## Line Spacing Adaptation

### Vertical Distribution

```
Small component (height: 40px)    Medium component (height: 80px)   Large component (height: 120px)
┌──────────────┐                  ┌──────────────────────┐           ┌────────────────────────────┐
│ Line 1       │                  │  Line 1              │           │     Line 1                 │
│ Line 2       │                  │                      │           │                            │
└──────────────┘                  │  Line 2              │           │     Line 2                 │
                                  │                      │           │                            │
                                  │  Line 3              │           │     Line 3                 │
                                  └──────────────────────┘           └────────────────────────────┘

Spacing: 8px                      Spacing: 13px                      Spacing: 20px
```

---

## Icon and Label Scaling

### Lock Icon Sizes

```
Small (40px):     Medium (80px):      Large (150px):
🔒                 🔒                  🔒
(8pt)              (10pt)              (12pt)
```

### Type Label Sizes

```
TYPE LABEL    TYPE LABEL    TYPE LABEL
(4pt)         (5pt)         (6pt)
```

---

## Customization Guide

### If Text is Too Large

Reduce the scaling factor in `_draw_node`:

```python
# Current (divisor: 15)
primary_font_size = max(6, min(10, int(min_dimension / 15)))

# Make smaller (divisor: 18 = smaller text)
primary_font_size = max(6, min(10, int(min_dimension / 18)))

# Even smaller (divisor: 20)
primary_font_size = max(6, min(10, int(min_dimension / 20)))
```

### If Text is Too Small

Increase the scaling factor:

```python
# Current (divisor: 15)
primary_font_size = max(6, min(10, int(min_dimension / 15)))

# Make larger (divisor: 12 = larger text)
primary_font_size = max(6, min(10, int(min_dimension / 12)))

# Even larger (divisor: 10)
primary_font_size = max(6, min(10, int(min_dimension / 10)))
```

---

## Size Reference Chart

| Component | Primary | Secondary | Type | Line |
|-----------|---------|-----------|------|------|
| 40px | 6pt | 5pt | 4pt | 8px |
| 60px | 7pt | 6pt | 5pt | 10px |
| 80px | 8pt | 7pt | 6pt | 13px |
| 100px | 8pt | 7pt | 6pt | 16px |
| 120px | 9pt | 8pt | 7pt | 20px |
| 150px+ | 10pt | 8pt | 6pt | 25px |

---

## Benefits Summary

✅ **No More Text Overflow** - Text fits in small components  
✅ **Professional Appearance** - Consistent proportions  
✅ **Better Readability** - Font size matches component size  
✅ **Flexible Resizing** - Users can resize freely  
✅ **Visual Hierarchy** - Primary text larger than secondary  
✅ **Automatic** - No manual adjustment needed  

---

## Examples in Action

### Example 1: Fluid Tank

```
SMALL (40×50)          MEDIUM (80×80)              LARGE (150×100)
┌────────────┐         ┌──────────────────┐       ┌──────────────────────┐
│ Fluid Tank │         │   Fluid Tank     │       │    Fluid Tank        │
└────────────┘         │  Storage Vessel  │       │  (Treated Water)     │
                       └──────────────────┘       │  Volume: 1,200m³     │
                                                  └──────────────────────┘
```

### Example 2: Pump Station

```
COMPACT (50×40)        STANDARD (100×60)           DETAILED (180×100)
┌─────────────┐        ┌────────────────────┐     ┌──────────────────────────┐
│   Pump St.  │        │  Pump Station      │     │  Pump Station A1         │
└─────────────┘        │  Capacity: 500GPM  │     │  Capacity: 500GPM        │
                       └────────────────────┘     │  Type: Centrifugal       │
                                                  │  Inlet: North Tank       │
                                                  └──────────────────────────┘
```

---

## Summary

Your components will now automatically display text at the perfect size for their dimensions. No more manual adjustment, no more overflow, no more readability issues! 🎉

**Test it now:** `python src/main.py` → Flow Diagram → Resize a component and watch the text scale!
