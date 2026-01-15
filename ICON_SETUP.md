# Application Icon Setup
## Water Balance Application

---

## Icon Requirements

### For Windows Distribution

**Format**: ICO (Icon file)  
**Sizes required**: 256x256, 128x128, 64x64, 48x48, 32x32, 16x16

### Two icons needed:
1. **app_icon.ico** - Used by the application window
2. **installer_icon.ico** - Used by the Windows installer

---

## Creation Steps

### Option 1: Using Online Converter

1. **Create or obtain** a 256x256 PNG image
   - Use Water Balance theme (blue/water colors)
   - Include "WB" monogram or water droplet
   - Ensure transparency for modern look

2. **Convert to ICO** using:
   - https://convertio.co/png-ico/
   - https://icoconvert.com/
   - https://online-converting.com/image/convert2ico/

3. **Download** the ICO file with multiple sizes embedded

4. **Place files**:
   ```
   assets/icons/app_icon.ico
   assets/icons/installer_icon.ico
   ```

### Option 2: Using ImageMagick (if installed)

```powershell
# Convert PNG to multi-size ICO
magick convert icon_256x256.png -define icon:auto-resize=256,128,64,48,32,16 app_icon.ico

# Copy for installer
Copy-Item assets\icons\app_icon.ico assets\icons\installer_icon.ico
```

### Option 3: Using GIMP

1. Open GIMP
2. Create new image: 256x256, transparent background
3. Design icon
4. Export As → .ico
5. Check all size options (256, 128, 64, 48, 32, 16)
6. Save

---

## Current Status

**Icon files needed in:**
```
c:\PROJECTS\Water-Balance-Application\assets\icons\
    ├── app_icon.ico         (❌ Not yet created)
    └── installer_icon.ico   (❌ Not yet created)
```

### Temporary Solution

If building immediately without custom icon:

1. Download a placeholder ICO from:
   - https://icon-library.com/icon/application-icon-18.html
   
2. Or use Windows default app icon temporarily

3. Replace later with branded icon

---

## Icon Design Suggestions

### Theme: Water/Industrial
- **Colors**: Blue (#0066cc), Gray (#7f8c8d), White
- **Elements**: 
  - Water droplet
  - Industrial gauge/meter
  - "WB" monogram
  - Flow chart symbol
  - Dam/reservoir silhouette

### Professional Examples
- Water droplet with gauge inside
- Blue circular badge with "WB"
- Flowing water with graph overlay
- Industrial water tower icon

---

## After Icon Creation

Update code references (if needed):
```python
# In src/main.py (already configured)
self.root.iconbitmap('assets/icons/app_icon.ico')
```

Build files (already configured):
- `water_balance.spec` → icon='assets/icons/app_icon.ico'
- `installer.iss` → SetupIconFile=assets\icons\installer_icon.ico

---

## Verification

After creating icons:

1. **Check file exists**:
   ```powershell
   Test-Path assets/icons/app_icon.ico
   Test-Path assets/icons/installer_icon.ico
   ```

2. **View icon**:
   - Right-click ICO file
   - Properties → Preview
   - Should show multiple sizes

3. **Test in build**:
   ```powershell
   .\build.ps1
   ```
   
4. **Verify**:
   - Check EXE icon in dist/WaterBalance/
   - Check installer icon in installer_output/

---

**Status**: Waiting for icon creation  
**Blocker**: No - can build with default Windows icon  
**Priority**: Medium - Enhances professional appearance
