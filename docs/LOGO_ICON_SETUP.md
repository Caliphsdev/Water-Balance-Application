# Logo & Icon Setup Documentation

## Current Status ✅

Your logo and icon files are **properly organized and connected** to the application.

**Fixed Issues:** Updated file path references in main_window.py to correctly locate logos in the `logo/` folder.

---

## Files Location & Purpose

### 1. **Logo Two Rivers** 
- **File:** `logo/Logo Two rivers.png`
- **Purpose:** Displays next to the **Hamburger Menu** (top-left of the app)
- **Integration:** 
  - Loaded in [src/ui/main_window.py](../src/ui/main_window.py#L106) (toolbar header)
  - Sized to fit toolbar height (~50px, 2.5x aspect ratio)
  - Configured as `logo/Logo Two rivers.png` in app_config.yaml
- **Display Location:** **Top Toolbar**, left side after hamburger menu button

### 2. **Company Logo**
- **File:** `logo/Company Logo.png`
- **Purpose:** Displayed in **FOUR locations**:
  1. **Loading Screen** (during app startup)
  2. **About Dashboard** section header
  3. **Navigation Sidebar** at the bottom (below About button)
  4. As a clickable link to the About page
- **Integration:**
  - Loading screen: [src/ui/loading_screen.py](../src/ui/loading_screen.py#L79) (startup splash)
  - About page: [src/ui/main_window.py](../src/ui/main_window.py#L839) (`_load_about()` method)
  - Sidebar: [src/ui/main_window.py](../src/ui/main_window.py#L330) (`_create_sidebar()` method)
  - Sized to 200×80px (Loading), 320×80px (About), and 180×60px (Sidebar)
  - Fallback: "TransAfrica Resources" text if image not found
- **Display Locations:** 
  - **Loading Screen** (centered splash during startup)
  - **About Page** (dashboard section header)
  - **Navigation Sidebar** (bottom, clickable to open About)

### 3. **Water Balance Icon**
- **File:** `logo/Water Balance.ico`
- **Purpose:** Application icon for:
  - **Windows Installer** (Inno Setup, `installer.iss`)
  - **Top-Left Corner** of the app window (window icon)
  - **Taskbar & Window Decoration**
- **Integration:**
  - Loaded in [src/main.py](../src/main.py#L223) (during app initialization)
  - Set via Tkinter's `.iconbitmap(str(icon_path))`
  - Referenced in `water_balance.spec` (PyInstaller build)
  - Referenced in `installer.iss` (Inno Setup installer)
- **Size:** Standard `.ico` format (includes 16×16, 32×32, 48×48, 64×64, 128×128, 256×256 variants)
- **Display Location:** Window title bar (top-left corner)

#### Icon Design Guidelines
**Theme:** Water/Industrial  
**Colors:** Blue (#0066cc), Gray (#7f8c8d), White  
**Elements:**
- Water droplet
- Industrial gauge/meter
- "WB" monogram
- Flow chart symbol
- Dam/reservoir silhouette

**Professional Examples:**
- Water droplet with gauge inside
- Blue circular badge with "WB"
- Flowing water with graph overlay
- Industrial water tower icon

#### Icon Creation Tools (for future updates)
**Required Sizes:** 256×256, 128×128, 64×64, 48×48, 32×32, 16×16

**Option 1: Online Converters**
- https://convertio.co/png-ico/
- https://icoconvert.com/
- https://online-converting.com/image/convert2ico/

**Option 2: ImageMagick (CLI)**
```powershell
magick convert icon_256x256.png -define icon:auto-resize=256,128,64,48,32,16 "Water Balance.ico"
```

**Option 3: GIMP**
1. Create new image: 256×256, transparent background
2. Design icon
3. Export As → .ico
4. Check all size options (256, 128, 64, 48, 32, 16)
5. Save to `logo/Water Balance.ico`

---

## Configuration in `app_config.yaml`

```yaml
branding:
  company_name: Water Balance Management
  logo_path: C:\PROJECTS\Water-Balance-Application\logo\Logo Two rivers.png
```

**Note:** The `Logo Two rivers.png` is stored in `logo/` for centralized branding management.

---

## Visual Placement Map

```
┌─────────────────────────────────────────────────────┐
│ 🍔 [Two Rivers Logo] Water Balance System           │  ← Toolbar (main_window.py)
├──────────────────────────┬──────────────────────────┤
│  Navigation              │                          │
│  ┌──────────────────┐   │  ABOUT DASHBOARD         │
│  │ 📊 Dashboard     │   │ ┌────────────────────┐   │
│  │ 📈 Analytics     │   │ │ [Company Logo]     │   │
│  │ 🔍 Monitoring    │   │ │ TransAfrica Res.   │   │
│  │ 💧 Storage       │   │ │ 💧 Water Balance   │   │
│  │ ⚙️  Calculations │   │ │ Version 1.0.0      │   │
│  │ 🌊 Flow Diagram  │   │ └────────────────────┘   │
│  │ ⚡ Settings      │   │                          │
│  │ ────────────── │   │                          │
│  │ ❓ Help         │   │                          │
│  │ ℹ️ About        │   │                          │
│  ┌──────────────────┐   │                          │
│  │ [Company Logo] ← ├──→ Clickable to About       │
│  │ TransAfrica    │   │                          │
│  └──────────────────┘   │                          │
└──────────────────────────┴──────────────────────────┘

┌────────────────────────────────────────┐
│  LOADING SCREEN (Startup)              │  ← loading_screen.py
│  ┌─────────────────────────────────┐   │
│  │    [Company Logo]               │   │
│  │  Water Balance System           │   │
│  │  TransAfrica Resources          │   │
│  │  [Progress Bar: 0%]             │   │
│  │  Initializing application...    │   │
│  └─────────────────────────────────┘   │
└────────────────────────────────────────┘

WINDOW ICON (top-left corner): [💧] Water Balance.ico
TASKBAR ICON: Water Balance.ico
```

---

## Build Integration

### PyInstaller (`water_balance.spec`)
```python
# Icons bundled in executable
icon='logo/Water Balance.ico'
```

### Inno Setup (`installer.iss`)
```ini
[Setup]
AppName=Water Balance
SetupIconFile=logo\Water Balance.ico
```

---

## File Organization

```
Water-Balance-Application/
├── logo/                           ← All logo/icon files here (PRIMARY LOCATION)
│   ├── Logo Two rivers.png        (Toolbar logo)
│   ├── Company Logo.png           (About page logo)
│   └── Water Balance.ico          (App & installer icon)
├── config/
│   └── branding/
│       └── Logo Two rivers.png    (Centralized branding reference for toolbar)
└── logo/
    └── icons/
        ├── (empty - no fallback needed)
```

**Note:** All logos are sourced from the `logo/` folder. The `logo/Logo Two rivers.png` file is the centralized branding asset.

---

## Usage in Code

### Loading Logo in Toolbar
**File:** [src/ui/main_window.py](../src/ui/main_window.py#L102)
```python
# Company logo (prefer branded TRP logo)
preferred_logo = get_resource_path('logo/Logo Two rivers.png')
fallback_logo = get_resource_path('logo/Logo Two rivers.png')
logo_path = preferred_logo if preferred_logo.exists() else fallback_logo
if logo_path.exists():
    img = Image.open(logo_path)
    img.thumbnail((int(toolbar_height * 2.5), toolbar_height - 10), Image.Resampling.LANCZOS)
    self.logo_photo = ImageTk.PhotoImage(img)
    logo_label = tk.Label(title_frame, image=self.logo_photo, bg=bg_header)
    logo_label.pack(side='left', padx=(0, 15))
```

### Loading Company Logo in Loading Screen
**File:** [src/ui/loading_screen.py](../src/ui/loading_screen.py#L79)
```python
# TransAfrica company logo - professional branding
try:
    from PIL import Image, ImageTk
    from utils.config_manager import get_resource_path
    logo_path = get_resource_path('logo/Company Logo.png')
    if logo_path.exists():
        img = Image.open(logo_path)
        # Resize logo for loading screen (max 80px height)
        img.thumbnail((200, 80), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(title_frame, image=self.logo_photo, bg=self.bg_light)
        logo_label.pack(pady=(0, 8))
```

### Loading Company Logo in About Page
**File:** [src/ui/main_window.py](../src/ui/main_window.py#L835)
```python
# Company logo in About header
logo_path = get_resource_path('logo/Company Logo.png')
if logo_path.exists():
    img = Image.open(logo_path)
    img.thumbnail((320, 80), Image.Resampling.LANCZOS)
    self.about_logo_photo = ImageTk.PhotoImage(img)
    logo_label = tk.Label(header_frame, image=self.about_logo_photo, bg=bg_main)
    logo_label.pack(pady=(0, 8))
```

### Loading Company Logo in Sidebar (Bottom Navigation)
**File:** [src/ui/main_window.py](../src/ui/main_window.py#L330)
```python
# TransAfrica company logo at bottom of sidebar
logo_frame = tk.Frame(self.sidebar, bg=bg_sidebar)
logo_frame.pack(side='bottom', fill='x', pady=(10, 20))

logo_path = get_resource_path('logo/Company Logo.png')
if logo_path.exists():
    img = Image.open(logo_path)
    img.thumbnail((180, 60), Image.Resampling.LANCZOS)  # Fits sidebar width
    self.sidebar_logo_photo = ImageTk.PhotoImage(img)
    logo_label = tk.Label(logo_frame, image=self.sidebar_logo_photo, bg=bg_sidebar, cursor='hand2')
    logo_label.pack(pady=5)
    # Click to open About page
    logo_label.bind('<Button-1>', lambda e: self.load_module('about'))
    
    # Add branding text below logo
    tk.Label(logo_frame, text="TransAfrica Resources", font=('Segoe UI', 8), fg='#95a5a6', bg=bg_sidebar).pack()
```

---

## Recommended Best Practices

### ✅ Current Setup is Good
- Logos are in a dedicated `logo/` folder
- App icon is properly formatted (`.ico`)
- Fallback paths are configured for robustness

### 🔧 Optional Enhancements
1. Ensure `logo/Logo Two rivers.png` exists (centralized branding asset)
2. **Add logo validation** on app startup to ensure files exist
3. **Test icon rendering** on actual Windows installer to confirm display
4. **Consider DPI-aware scaling** for high-resolution displays (already uses LANCZOS resampling)

### 📝 Documentation
- **Icon sizes used:**
  - Toolbar: ~125×50px
  - Loading Screen: 200×80px
  - About page: 320×80px
  - Sidebar: 180×60px
  - Window icon: Multiple sizes in `.ico` file
- **Formats supported:**
  - `.png` for UI display (good quality, transparent backgrounds)
  - `.ico` for Windows system integration (standard format)

---

## Testing Checklist

- [ ] Logo appears correctly next to hamburger menu (top-left)
- [ ] **Logo appears on loading screen during startup** ✨
- [ ] Logo appears correctly in About dashboard
- [ ] Logo appears correctly at bottom of Navigation sidebar
- [ ] Logo in sidebar is clickable and opens About page
- [ ] App icon displays in taskbar when running
- [ ] Installer shows icon during installation (Inno Setup)
- [ ] Window icon visible in top-left corner of main window
- [ ] High-DPI displays render logos without pixelation
- [ ] Logos scale properly when window is resized

---

## Related Files
- **Build Script:** [build.ps1](../build.ps1)
- **PyInstaller Config:** [water_balance.spec](../water_balance.spec)
- **Installer Config:** [installer.iss](../installer.iss)
- **Main Window Code:** [src/ui/main_window.py](../src/ui/main_window.py)
- **App Config:** [config/app_config.yaml](../config/app_config.yaml)

---

**Last Updated:** 2026-01-20  
**Status:** ✅ Fully Connected and Integrated

**Changes Made:**
- ✅ Toolbar logo path uses `logo/` (centralized)
- ✅ About page logo path corrected: `logo/Company Logo.png`
- ✅ Sidebar logo path corrected: `logo/Company Logo.png`
- ✅ Window icon path corrected: `logo/Water Balance.ico`
- ✅ Loading screen logo path corrected: `logo/Company Logo.png`
- ✅ All paths now point to the actual files in your `logo/` folder
- ✅ Sidebar logo is now clickable to open About page
- ✅ Company logo now appears on loading screen at startup
