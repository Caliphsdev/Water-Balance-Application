# 🚀 Quick Start: Junction Connections

## What You Asked For
**"Is it possible to make it so that lines can connect to other lines (like the image showing Effluent connecting to the Spill line)?"**

## Answer: YES! ✅

You can now connect flow lines **directly to other flow lines**, not just to components!

---

## 🎯 How to Create a Junction Connection

### 3-Step Process

1. **Start Drawing**
   - Click "🖊️ Drawing Mode" button
   - Click source component (e.g., Sewage Treatment)
   - Add waypoints if needed

2. **Finish at Flow Line**
   - Move cursor close to target flow line
   - Click within 15 pixels of the line
   - System auto-detects and prompts for volume

3. **Junction Created!**
   - Arrow head appears at merge point
   - Colored circle marks junction
   - Flow merges into existing line

---

## 🎨 What You'll See

```
Sewage Treatment → Effluent 46,425 m³ → ● → Spill Line → Outflows
                                         ↑
                                    Junction marker
```

- **Arrow head**: Shows flow direction into line
- **Colored circle**: Marks exact junction point (6px diameter)
- **Circle color**: Matches flow type (blue/red/orange)

---

## ✏️ Edit / Delete Junctions

**Edit Properties:**
1. Click "Edit Line" button
2. Select junction from list (shows as "Source → junction_xxx")
3. Modify type/color/volume/bidirectional
4. Changes apply immediately

**Delete:**
1. Click "Delete Line" button
2. Select junction (Ctrl+click for multiple)
3. Click Delete
4. Confirm

---

## 💡 Pro Tips

✅ **Detection Zone**: Click within 15px of target line  
✅ **Visual Feedback**: Junction shows arrow + circle marker  
✅ **Editing**: Full support via Edit/Delete dialogs  
✅ **Persistence**: Junctions save/load with diagram  
✅ **Multi-Delete**: Ctrl+click multiple junctions to batch delete  

---

## 📚 Documentation

- **Full Guide**: See [JUNCTION_CONNECTIONS_GUIDE.md](JUNCTION_CONNECTIONS_GUIDE.md)
- **All Changes**: See [FLOW_DIAGRAM_UPDATE_SUMMARY.md](FLOW_DIAGRAM_UPDATE_SUMMARY.md)
- **Before/After**: See [FLOW_DIAGRAM_BEFORE_AFTER.md](FLOW_DIAGRAM_BEFORE_AFTER.md)

---

## 🧪 Test It Now

1. Launch app: `python src/main.py`
2. Open **Flow Diagram Dashboard**
3. Select area: **UG2 North Decline**
4. Create test junction:
   - Drawing Mode → Click "Sewage Treatment"
   - Click near "Spill" flow line
   - Enter volume: 46425
   - See arrow + circle at junction!

---

**Status**: ✅ Feature complete and ready to use!

