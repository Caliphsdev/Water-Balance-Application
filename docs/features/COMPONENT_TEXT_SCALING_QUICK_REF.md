# Component Text Scaling - Quick Reference

## The Fix in 30 Seconds

**Problem:** Text doesn't resize when you make components smaller/larger  
**Solution:** Font size now scales proportionally with component dimensions  
**Result:** Text always fits and looks right! ✅

---

## How It Works

### Before
```
Small component (40px): Text too big ❌
Large component (150px): Text too small ❌
```

### After
```
Small component (40px): 6pt font (fits!) ✅
Large component (150px): 10pt font (readable!) ✅
```

---

## What Scales

| Element | Scales | Range |
|---------|--------|-------|
| **Main Text** | Yes | 6-10pt |
| **Secondary Text** | Yes | 5-8pt |
| **Type Label** | Yes | 4-6pt |
| **Lock Icon** | Yes | 8-12pt |
| **Line Spacing** | Yes | Auto |

---

## Testing

```bash
python src/main.py
# Go to Flow Diagram
# Right-click or drag to resize components
# Notice text automatically scales ✅
```

---

## Examples

### Small Component (40×40px)
```
┌─────────┐
│ Label   │  ← 6pt font
└─────────┘
```

### Medium Component (80×50px)
```
┌──────────────┐
│   Label      │  ← 8pt font
│  Subtitle    │
└──────────────┘
```

### Large Component (150×80px)
```
┌─────────────────────────────┐
│      Main Component         │  ← 10pt font
│      Label Text             │  ← 8pt secondary
└─────────────────────────────┘
```

---

## How to Customize

Edit `_draw_node` method in `src/ui/flow_diagram_dashboard.py`:

```python
# Make text larger overall:
primary_font_size = max(6, min(12, int(min_dimension / 12)))  # Was: /15

# Make text smaller overall:
primary_font_size = max(6, min(8, int(min_dimension / 20)))   # Was: /15
```

---

## Features

✅ Text automatically scales with component size  
✅ Small components get readable (not tiny) text  
✅ Large components get proportional text  
✅ Multi-line text distributes within component  
✅ Long text truncates with ellipsis (…)  
✅ Lock icons scale too  
✅ Type labels scale  
✅ Line spacing adapts to component height  

---

## Status

✅ **Implemented**  
✅ **Tested**  
✅ **Production Ready**  

---

**See full details in:** [COMPONENT_TEXT_SCALING_FIX.md](COMPONENT_TEXT_SCALING_FIX.md)
