# Interactive Flow Diagram - Quick Reference

## 🎮 Controls Cheat Sheet

| Action | How | Result |
|--------|-----|--------|
| **Move Component** | Click + Drag | Component repositions, arrows follow |
| **Connect Components** | 1. Click 🔗 button | Enter Connection Mode |
| | 2. Click first component | (Highlights red) |
| | 3. Click second component | (Creates connection) |
| | 4. Enter flow value | Connection appears with arrow |
| **Delete Component** | Right-click + Yes | Component removed + all connections |
| **Save All Changes** | Click 💾 button | All positions/connections saved to JSON |
| **Reload from File** | Click ↺ button | Discard unsaved changes |
| **Pan Around** | Mouse wheel | Scroll to see more diagram |
| **Scroll Right/Left** | Shift + Wheel | Horizontal scroll |

---

## 📍 Current Components (UG2 North Decline)

| # | Name | Type | Color | Current Position |
|---|------|------|-------|------------------|
| 1 | Borehole NDGWA 1-6 | SOURCE | Light Blue | Top-left |
| 2 | Direct Rainfall | SOURCE | Lavender | Left |
| 3 | Softening Plant | TREATMENT | Orange | Left-center |
| 4 | Reservoir | STORAGE | Dark Blue (Oval) | Center |
| 5 | Guest House | CONSUMPTION | Light Blue | Top-middle |
| 6 | Offices | CONSUMPTION | Light Blue | Top-middle-right |
| 7 | Sewage Treatment | TREATMENT | Orange | Center |
| 8 | NDCD 1-2/NDSWD 1 | STORAGE | Dark Blue (Oval) | Right-center |
| 9 | North Decline | PROCESS | Red | Bottom-center |
| 10 | North Shaft | PROCESS | Light Red | Bottom-left |
| 11 | Septic Tank | CONSUMPTION | White/Red | Top-right |
| 12 | Losses | LOSS | White/Black | Right |

---

## 🔗 Current Connections (Can Add More!)

| From | To | Value (m³) | Status |
|------|-----|-----------|--------|
| Borehole → Softening | 71,530 | ✓ |
| Softening → Reservoir | 47,485 | ✓ |
| Reservoir → Guest House | 16,105 | ✓ |
| Reservoir → Offices | 14,246 | ✓ |
| Reservoir → Sewage | 47,485 | ✓ |
| Sewage → NDCD | 46,425 | ✓ |
| Rainfall → NDCD | 5,363 | ✓ |
| NDCD → North Decline | 187,761 | ✓ |
| North Decline → NDCD | 245,572 | ✓ |
| Offices → Septic | 2,594 | ✓ |
| Guest House → Septic | 1,470 | ✓ |
| Guest House → Losses | 947 | ✓ |

---

## 📝 Common Tasks

### Task: Move Guest House to the Right
```
1. Click "Guest House" component
2. Drag it to the right
3. Release mouse
4. Click "Save Changes"
✓ Done - position saved
```

### Task: Create New Connection (e.g., Offices to Losses)
```
1. Click "🔗 Connect Components"
2. Click "Offices" (highlights red)
3. Click "Losses"
4. Enter value: 2000
5. Click "Save Changes"
✓ Done - new connection created
```

### Task: Delete Septic Tank
```
1. Right-click "Septic Tank"
2. Click "Yes" on confirmation
3. Click "Save Changes"
✓ Done - component removed with all connections
```

### Task: Undo Changes
```
1. Click "↺ Reload from File"
2. Click "Yes" on confirmation
✓ Done - back to last saved version
```

### Task: Reorganize for Better Layout
```
1. Drag "Borehole" to upper-left
2. Drag "Softening" below it
3. Drag "Reservoir" to the right
4. Drag "NDCD" to far right
5. Drag consumption components (Guest House, Offices) above
6. Drag "North Decline" below
7. Click "Save Changes"
✓ Done - new layout saved
```

---

## 🎨 Button Reference

| Button | Color | Purpose | What Happens |
|--------|-------|---------|--------------|
| 🔗 Connect | Blue | Enable connection mode | Click 2 components to connect them |
| 💾 Save | Green | Save all changes | All positions/connections saved to JSON |
| ↺ Reload | Orange | Revert changes | Load last saved version |

---

## ⚠️ Important Notes

- ✅ Changes appear **instantly** when you move/connect
- ✅ Click **"Save Changes"** to make permanent
- ❌ Without saving, changes are **lost** when you close app
- ✅ Reload anytime to **undo** unsaved changes
- ✅ Right-click deletes **both** component and connections
- ✅ You can create **unlimited** connections
- ⚠️ All changes saved to: `data/diagrams/ug2_north_decline.json`

---

## 🔍 What Gets Saved

When you click "💾 Save Changes":

✅ Component positions (x, y coordinates)
✅ All connections (from → to)
✅ Flow values on connections
✅ Component properties (colors, sizes, labels)

Saved to: `data/diagrams/ug2_north_decline.json`

---

## 🚀 Feature Summary

| Feature | Status | How to Use |
|---------|--------|-----------|
| Drag components | ✅ | Click + hold + drag |
| Create connections | ✅ | 🔗 button → click 2 components |
| Delete components | ✅ | Right-click → Yes |
| Save changes | ✅ | 💾 button |
| Reload from file | ✅ | ↺ button |
| Add new components | ⏳ | Edit JSON manually |
| Export as image | ⏳ | Coming soon |
| Real-time data | ⏳ | Coming soon |

---

## 📞 Troubleshooting

**Q: My changes disappeared!**
A: Did you click "💾 Save Changes"? Without it, changes are lost on close.

**Q: Can't drag component?**
A: Make sure you're clicking the component itself, not an arrow.

**Q: Connection won't create?**
A: Check if you're in Connect mode (blue button is pressed). If connection exists already, it will warn you.

**Q: Arrows don't follow when I drag?**
A: They should - if not, try saving and reloading.

**Q: How to delete a connection?**
A: Delete one of its components (right-click → Yes), and the connection is removed too.

---

## 💡 Pro Tips

1. **Organize by flow**: Left-to-right layout is intuitive
2. **Group by type**: Keep sources together, storage together, etc.
3. **Avoid crossings**: Position components so arrows don't overlap
4. **Name clearly**: Labels help you identify components quickly
5. **Save often**: Click 💾 after each change group
6. **Experiment freely**: Click ↺ anytime to revert

---

## 📊 Data Flow

```
Your Actions
    ↓
Editor displays changes
    ↓
Click "💾 Save"
    ↓
Changes written to JSON
    ↓
JSON file saved to disk
    ↓
Changes persist on restart
```

---

## ✨ You Have Full Control Now!

- No limitations
- No code changes needed
- Visual, intuitive interface
- Everything saved automatically
- Experiment freely!

**Happy diagramming! 🎯**
