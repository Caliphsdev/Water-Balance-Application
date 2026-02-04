# Getting Started Guide

**Quick entry points for new users and developers**

---

## 📖 Files in This Section

### [QUICKSTART.md](./QUICKSTART.md) - **START HERE**
Setup and running instructions for the PySide6 Water Balance Dashboard.

**Topics covered:**
- Environment setup (.venv)
- Installing dependencies
- Running the application
- Project structure overview
- Key components

**Time:** 15-20 minutes

---

## 🎯 Quick Start Path

**For new developers:**
1. ✅ Read [QUICKSTART.md](./QUICKSTART.md) for setup
2. ✅ Run app: `.venv\Scripts\python src/main.py`
3. ✅ Explore the UI and dashboard pages
4. ✅ Move to [01-ARCHITECTURE](../01-ARCHITECTURE/) for design patterns

**For understanding the codebase:**
→ See [01-ARCHITECTURE/](../01-ARCHITECTURE/) for patterns and structure

**For backend development:**
→ See [02-BACKEND/](../02-BACKEND/) for services and database

**For UI development:**
→ See [03-FRONTEND/](../03-FRONTEND/) for PySide6 components

---

## 📚 Project Overview

This is a **PySide6 Water Balance Dashboard** application that provides:
- Storage facility management
- Water balance calculations
- Flow diagram visualization
- Analytics and reporting

### Key Technologies
- **UI Framework:** PySide6 (Qt6)
- **Database:** SQLite
- **Data Processing:** Pandas, NumPy
- **Visualization:** PyQtGraph, Matplotlib

### Project Structure
```
src/
├── ui/           # PySide6 UI (dashboards, dialogs, components)
├── services/     # Business logic layer
├── database/     # Database access layer
├── models/       # Pydantic data models
└── core/         # App infrastructure (logging, config)
```

---

**Time to complete this section:** 15-20 minutes  
**Next:** Head to [01-ARCHITECTURE](../01-ARCHITECTURE/) for design patterns
