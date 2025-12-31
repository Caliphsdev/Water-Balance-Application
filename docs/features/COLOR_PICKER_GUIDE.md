# Color Picker & Size Controls Quick Reference

## 🎨 How to Use the Color Picker

### In Edit Properties Dialog
1. Select a component (click on it)
2. Right-click → "Edit Properties" OR use Edit button
3. For **Fill Color** or **Outline Color**:
   - Click the **🎨 Pick** button next to the color field
   - Select color from the native color chooser
   - Click OK → Color preview updates instantly
   - Hex value is set automatically

### In Add Component Dialog (Toolbar)
1. Click **Add Component** button in toolbar
2. For **Fill Color** or **Outline Color**:
   - Click the **🎨 Pick** button
   - Choose color from the native dialog
   - Click OK → Preview updates
   - Hex value is set automatically

### In Add Component (Right-click)
1. Right-click on canvas where you want to place component
2. Select **Create Component Here**
3. For colors:
   - Click **🎨 Pick** buttons
   - Select colors from native color chooser
   - Click OK → Previews update

---

## 📏 Size Controls

### Width
- **Range:** 40 to 400 pixels
- **Default:** 120 px
- **Label:** "px" shown next to spinner for clarity
- **How to set:** Use spinbox controls or type directly

### Height
- **Range:** 20 to 200 pixels
- **Default:** 40 px
- **Label:** "px" shown next to spinner for clarity
- **How to set:** Use spinbox controls or type directly

---

## ⚙️ Alternative: Manual Hex Entry

If you prefer typing hex codes directly:
1. Instead of clicking 🎨 Pick button
2. Click in the hex text field (e.g., "#3498db")
3. Type your hex code (must be valid format: #RRGGBB)
4. Press Enter or click away

Valid examples:
- `#FF0000` (Red)
- `#00FF00` (Green)
- `#0000FF` (Blue)
- `#3498db` (Light Blue)
- `#2c3e50` (Dark Blue)

---

## 🎯 Color Preview

- **Preview Box:** Small 30×25px box shows your selected color in real-time
- **Updates:** Preview updates immediately when you:
  - Select color from color chooser dialog
  - Change hex code manually
- **Visual Feedback:** Helps confirm your color choice before creating component

---

## 💡 Tips

1. **Quick Color Selection:** Use color picker buttons for fastest workflow
2. **Precise Colors:** Use hex entry if you have specific color codes
3. **Preview Check:** Always check the preview box to confirm color
4. **Component Types:** 10 types available: source, process, storage, consumption, building, treatment, plant, tsf, reservoir, loss, discharge
5. **Shapes:** Choose from rect, oval, or diamond

---

## 🔄 Workflow Examples

### Example 1: Create Blue Component
1. Click "Add Component" in toolbar
2. Enter Component ID: "tank_1"
3. Enter Label: "Storage Tank"
4. Click 🎨 Pick for Fill Color
5. Select blue from color chooser
6. Click OK
7. Click ✅ Create
✅ Done!

### Example 2: Right-click Add with Colors
1. Right-click on canvas
2. Select "Create Component Here"
3. Enter Component ID: "pump_1"
4. Click 🎨 Pick for Fill Color → Select orange
5. Click 🎨 Pick for Outline Color → Select brown
6. Click ✅ Create
✅ Done! Component appears at clicked position with your colors

### Example 3: Edit Existing Component Colors
1. Click on component to select
2. Right-click → "Edit Properties"
3. Current colors shown in preview boxes
4. Click 🎨 Pick to change fill → Select new color
5. Click 🎨 Pick to change outline → Select new color
6. Click ✅ Apply
✅ Done! Component colors updated

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Color picker doesn't open | Make sure you clicked the 🎨 Pick button (not the text field) |
| Preview doesn't update | Try clicking in another field or pressing Tab to confirm entry |
| Invalid hex error | Check format: must be #RRGGBB (6 hex digits after #) |
| Size won't change | Check range: width 40-400px, height 20-200px |
| Colors don't save | Click ✅ Create or ✅ Apply button to save changes |

---

## 📚 Related Documentation

- [UI_ENHANCEMENTS_SUMMARY.md](UI_ENHANCEMENTS_SUMMARY.md) - Technical details
- [FLOW_DIAGRAM_GUIDE.md](FLOW_DIAGRAM_GUIDE.md) - General flow diagram usage

