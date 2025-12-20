# Right-Click Context Menu - Quick Reference

## 🎯 What It Does

Right-click on the canvas → Automatically add components at that exact location without typing coordinates.

## 📍 Two Right-Click Behaviors

### Empty Canvas Space
```
Right-Click on empty area
    ↓
📍 Canvas Position: (X, Y)
➕ Create Component Here
    ↓
Dialog opens with coordinates pre-filled
    ↓
✅ Component created at exact click position
```

### Existing Component
```
Right-Click on component
    ↓
✏️ Edit Properties
🔒 Lock/Unlock
🌀 Draw Flowline
🗑️ Delete Component
    ↓
(Same as before)
```

## ⚡ Quick Workflow

| Step | Action | Result |
|------|--------|--------|
| 1 | Right-click where you want component | Context menu appears at cursor |
| 2 | Click "➕ Create Component Here" | Dialog opens with X/Y pre-filled |
| 3 | Enter: ID, Label, Type, Shape, Colors | Form ready for details |
| 4 | Click "✅ Create" | Component appears at clicked location |

## 🎨 Dialog Fields (Auto-Filled Position)

```
Position: X: 645, Y: 320  ← AUTO-FILLED FROM RIGHT-CLICK
Component ID: __________ ← You enter (required, unique)
Label: NEW COMPONENT  ← You enter
Type: [process ▼]  ← Select from dropdown
Shape: [rect ▼]  ← Select shape
Width: [120]  ← Adjust size
Height: [40]  ← Adjust size
Fill Color: [#3498db]  ← Color choice
Outline Color: [#2c3e50]  ← Outline choice
```

## ✅ Validation

- **Component ID:** Must be non-empty and unique
- **Position:** Cannot be changed (auto-filled)
- **Other Fields:** Accept any valid input

## 🚀 Benefits vs Old Method

| Aspect | Before | After |
|--------|--------|-------|
| **Location** | Type X and Y manually | Click where you want it |
| **Accuracy** | Easy to mistype | Visually confirmed |
| **Speed** | Slow coordinate entry | Instant placement |
| **Errors** | Coordinates off-by-default | Exact click position used |

## 💡 Tips

✓ Right-click away from existing components  
✓ Create multiple components rapidly  
✓ Use visual canvas to plan layout  
✓ Drag components later to fine-tune  
✓ Right-click component menu unchanged  

## 🔧 Implementation

- **File Modified:** `src/ui/flow_diagram_dashboard.py`
- **Methods Added:** 
  - `_show_canvas_context_menu()` - Show menu for empty space
  - `_add_component_at_position()` - Create with coordinates
- **Methods Modified:** `_on_canvas_right_click()` - Route to right menu
- **User-Facing:** Zero code changes needed - just right-click!

## ❌ Common Issues

| Issue | Solution |
|-------|----------|
| Menu doesn't appear on right-click | Make sure you're right-clicking on canvas (not toolbar) |
| Coordinates show (0,0) | Canvas coords start at top-left; click in diagram area |
| Can't modify position | Position is auto-set from right-click (by design) |
| Component ID rejected | Use unique ID, no special characters |

## 🎓 Related Features

- **Toolbar Button:** "➕ Add Component" (traditional method, still available)
- **Component Editing:** Right-click component → "✏️ Edit Properties"
- **Flowlines:** Draw manually or from right-click menu on components
- **Diagram Persistence:** Auto-saves to JSON diagram file

---

**Last Updated:** 2025-12-19  
**Feature Status:** ✅ Complete and tested  
**Compatibility:** All areas and diagram types
