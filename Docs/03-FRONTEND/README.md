# Frontend Documentation

**UI/UX development, design guidelines, and frontend components**

---

## 📖 Files in This Section

### 1. [UI_DEVELOPMENT_GUIDE.md](./UI_DEVELOPMENT_GUIDE.md) - **START HERE**
Comprehensive UI development guidelines.

**Topics covered:**
- UI development workflow (Designer → Compile → Controller)
- Component structure and naming conventions
- Layout patterns and best practices
- Widget organization
- Styling and theming
- Responsive design
- Testing UI components

**Use when:**
- Building new UI components
- Understanding development workflow
- Styling pages and dialogs
- Following naming conventions
- Writing UI tests

**Time:** 40-60 minutes

---

### 2. [UI_DESIGN_CHECKLIST.md](./UI_DESIGN_CHECKLIST.md)
UI design review checklist.

**Topics covered:**
- Pre-design checklist
- Component naming standards
- Layout verification
- Styling requirements
- Accessibility checks
- Testing checklist
- Code review items

**Use when:**
- Before submitting UI code
- Reviewing others' UI code
- Ensuring consistency
- Validating design
- Quality assurance

**Time:** 10-20 minutes (reference during review)

---

### 3. [ANALYTICS_VISUAL_GUIDE.md](./ANALYTICS_VISUAL_GUIDE.md)
Analytics dashboard visual specifications.

**Topics covered:**
- Dashboard layout
- Chart specifications
- KPI card design
- Color scheme
- Data visualization
- Responsive layout
- Visual hierarchy

**Use when:**
- Building analytics dashboard
- Implementing charts
- Styling dashboard pages
- Understanding visual requirements

**Time:** 20-30 minutes

---

### 4. [ANALYTICS_TEST_GUIDE.md](./ANALYTICS_TEST_GUIDE.md)
Analytics page testing guide.

**Topics covered:**
- Test scenarios
- User workflows
- Edge cases
- Performance testing
- Data validation
- Visual regression testing
- Error handling

**Use when:**
- Testing analytics features
- Validating functionality
- Ensuring reliability
- Checking edge cases

**Time:** 20-30 minutes

---

## 🎯 Development Workflow

### Widget Development (Designer → Code)

1. **Design in Qt Designer**
   - Create `.ui` file
   - Use consistent naming (btn_*, input_*, label_*)
   - Apply stylesheets

2. **Compile to Python**
   - `pyside6-uic dashboard.ui -o generated_ui_dashboard.py`
   - Fix imports in generated file

3. **Create Controller**
   - Implement business logic
   - Connect signals/slots
   - Add validation

4. **Mount in Main Window**
   - Add to page stack
   - Wire data sources
   - Test integration

---

## 🏗️ Component Structure

### Dialog Components
```
src/ui/dialogs/
├── generated_ui_*.py      (compiled from .ui)
├── *_dialog.py            (controller, logic)
└── *_dialog.ui (design-time only)
```

### Dashboard Components
```
src/ui/dashboards/
├── generated_ui_*.py      (compiled from .ui)
├── *_dashboard.py         (controller, logic)
└── *_dashboard.ui (design-time only)
```

---

## 🎨 Styling

### Color Palette
- **Primary Blue:** `rgb(13, 71, 161)`
- **Background Gray:** `#F5F6F7`
- **Card White:** `white`
- **Border:** `#E0E0E0`
- **Text Dark:** `rgb(51, 51, 51)`
- **Text Gray:** `rgb(102, 102, 102)`

### Sizing Standards
- **Card Height:** 180px
- **Card Width:** 200px
- **Margin:** 20px
- **Spacing:** 15px between items
- **Button Height:** 32px

---

## ✅ Before Starting UI Development

Make sure you understand:
- [ ] Qt Designer workflow
- [ ] Signal/slot pattern
- [ ] Component naming conventions
- [ ] Styling approach (QSS)
- [ ] Data binding patterns
- [ ] Layout management
- [ ] Testing approach

---

## 📚 Related Documentation

- **Architecture:** See [01-ARCHITECTURE/PYSIDE6_PATTERNS.md](../01-ARCHITECTURE/PYSIDE6_PATTERNS.md) for patterns
- **Backend Integration:** See [02-BACKEND/](../02-BACKEND/) for service integration
- **Features:** See [04-FEATURES/](../04-FEATURES/) for feature-specific UI

---

## 🔗 Quick Links

- **Qt Designer Help:** https://doc.qt.io/qtforpython-6/
- **PySide6 Docs:** https://doc.qt.io/qtforpython-6/
- **Color Reference:** Check color palette section above

---

**Reading order:**
1. UI_DEVELOPMENT_GUIDE.md (40-60 min)
2. UI_DESIGN_CHECKLIST.md (quick reference)
3. ANALYTICS_VISUAL_GUIDE.md (for specific features)
4. ANALYTICS_TEST_GUIDE.md (for testing)

**Total time:** 70-110 minutes (including reference time)
