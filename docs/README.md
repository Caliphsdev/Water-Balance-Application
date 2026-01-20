# Documentation Index

Welcome to the Water Balance Application documentation! This folder contains all project documentation.

---

## 📚 Available Documentation

### Branding & UI
- [**LOGO_ICON_SETUP.md**](LOGO_ICON_SETUP.md) - Complete guide to logo and icon setup, integration, and creation
  - Logo Two Rivers (toolbar)
  - Company Logo (loading screen, about page, sidebar)
  - Water Balance Icon (app window & installer)
  - Icon design guidelines and creation tools

---

## 📁 Folder Structure

```
docs/
├── README.md               ← You are here (documentation index)
└── LOGO_ICON_SETUP.md      ← Complete logo & icon guide (setup, integration, creation)
```

---

## 🚀 Quick Links

### Getting Started
- [Logo & Icon Setup (Complete Guide)](LOGO_ICON_SETUP.md)

### Configuration
- All logos and icons are stored in `logo/` folder
- Configuration references in `config/branding/`

### Integration Points
- Toolbar: `src/ui/main_window.py` (line 106)
- Loading Screen: `src/ui/loading_screen.py` (line 79)
- About Dashboard: `src/ui/main_window.py` (line 839)
- Navigation Sidebar: `src/ui/main_window.py` (line 330)
- Window Icon: `src/main.py` (line 223)

---

## 📝 Adding New Documentation

When adding new `.md` files to this `docs/` folder:

1. Create your file in this `docs/` folder
2. Add a link to it in this README.md
3. Use relative paths to link to source code or other docs

**Example link formats:**
- Same folder: `[Link Text](FILENAME.md)`
- Parent folder: `[Link Text](../filename.md)`
- Source code: `[Link Text](../src/path/to/file.py)`

---

## 📂 Related Folders

- **Source Code:** `src/` - Application source code
- **Configuration:** `config/` - Application configuration files
- **Branding:** `config/branding/` - Centralized branding assets
- **Logos/Icons:** `logo/` - All visual branding assets
- **Build Files:** Root level - Build scripts and configurations

---

**Last Updated:** 2026-01-20  
**Status:** ✅ Documentation structure established
