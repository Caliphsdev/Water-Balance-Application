---
name: desktop-design
description: Apply professional design thinking principles to PySide6/Qt desktop applications. Use this skill when styling dashboards, creating custom widgets, designing layouts, choosing typography, selecting color palettes, or adding visual polish to any Qt-based desktop interface. Adapted from web design best practices for the Qt framework.
---

# Desktop Design Principles for PySide6 Applications

This skill guides creation of distinctive, professional desktop interfaces using PySide6/Qt. Apply these design thinking principles when styling dashboards, creating custom widgets, or refining UI aesthetics.

---

## Design Thinking Process

Before coding UI, understand the context and commit to a clear aesthetic direction:

### 1. Purpose & Audience
- **Who uses this?** Mine engineers, operations managers, data analysts
- **What problem does it solve?** Water balance monitoring, KPI tracking, flow visualization
- **Context of use:** Office desktop, control room displays, presentations

### 2. Tone & Aesthetic Direction
Choose a clear direction and execute with precision:

| Aesthetic | Description | Best For |
|-----------|-------------|----------|
| **Professional/Corporate** | Clean, neutral, data-focused | Dashboards, reports |
| **Industrial/Utilitarian** | Rugged, high-contrast, control-panel | Monitoring systems |
| **Minimalist/Modern** | Generous whitespace, subtle accents | Analytics views |
| **Dark Mode/Technical** | Low-light optimized, vivid accents | 24/7 operations |
| **Data-Dense/Editorial** | Information-rich, typography-driven | Complex data tables |

### 3. Differentiation
Ask: *What makes this interface memorable and effective?*
- Clear visual hierarchy
- Distinctive but readable typography
- Purposeful color usage (not decoration)
- Smooth, meaningful animations

---

## Typography for Qt Applications

### Font Selection Principles
```python
# AVOID: Generic, overused fonts
# ❌ Arial, Helvetica, Times New Roman, Comic Sans
# ❌ System default fonts without customization

# USE: Distinctive, professional fonts
# ✅ Segoe UI Variable (Windows 11 modern)
# ✅ SF Pro (macOS native)
# ✅ IBM Plex Sans/Mono (technical, open source)
# ✅ JetBrains Mono (code/data display)
# ✅ Roboto Flex (variable weight, Google)
# ✅ Source Sans Pro (Adobe, professional)
```

### Typography Hierarchy
```python
from PySide6.QtGui import QFont

# Define clear hierarchy with purpose
FONTS = {
    # Page titles - bold, commanding
    'title': QFont('Segoe UI Variable', 24, QFont.Weight.DemiBold),
    
    # Section headers - clear separation
    'header': QFont('Segoe UI Variable', 16, QFont.Weight.Medium),
    
    # Body text - optimized for reading
    'body': QFont('Segoe UI', 11, QFont.Weight.Normal),
    
    # Data/numbers - monospace for alignment
    'data': QFont('JetBrains Mono', 11, QFont.Weight.Normal),
    
    # Captions/labels - subtle, supporting
    'caption': QFont('Segoe UI', 9, QFont.Weight.Normal),
    
    # KPI values - large, impactful
    'kpi_value': QFont('Segoe UI Variable', 32, QFont.Weight.Bold),
}
```

### QSS Typography Styling
```css
/* Typography hierarchy in QSS */
QLabel#pageTitle {
    font-size: 24px;
    font-weight: 600;
    color: #FFFFFF;
    letter-spacing: -0.5px;  /* Tighten for large text */
}

QLabel#sectionHeader {
    font-size: 16px;
    font-weight: 500;
    color: #E6EDF3;
    padding-bottom: 8px;
    border-bottom: 1px solid #30363D;
}

QLabel#bodyText {
    font-size: 11px;
    font-weight: 400;
    color: #8B949E;
    line-height: 1.5;
}

QLabel#kpiValue {
    font-size: 32px;
    font-weight: 700;
    color: #58A6FF;
}
```

---

## Color & Theme Design

### Color Palette Principles
1. **Dominant + Accent**: One primary color, sharp accents for actions
2. **Semantic Colors**: Consistent meaning (green=success, red=error, blue=info)
3. **Contrast**: WCAG AA minimum (4.5:1 for text)
4. **Hierarchy**: Lighter/darker shades create depth

### Professional Dark Theme Palette
```python
# Dark theme - professional, low eye strain
COLORS_DARK = {
    # Backgrounds (layered depth)
    'bg_primary': '#0D1117',      # Deepest - main canvas
    'bg_secondary': '#161B22',    # Cards, panels
    'bg_tertiary': '#21262D',     # Hover states, elevated
    'bg_overlay': '#30363D',      # Modals, tooltips
    
    # Text hierarchy
    'text_primary': '#E6EDF3',    # Main content
    'text_secondary': '#8B949E',  # Supporting text
    'text_muted': '#484F58',      # Disabled, hints
    
    # Semantic colors
    'accent_blue': '#58A6FF',     # Primary actions, links
    'accent_green': '#238636',    # Success, positive values
    'accent_red': '#F85149',      # Errors, negative values
    'accent_yellow': '#D29922',   # Warnings, caution
    'accent_purple': '#A371F7',   # Special, highlighted
    
    # Borders & dividers
    'border_default': '#30363D',
    'border_muted': '#21262D',
    
    # Status indicators
    'status_online': '#238636',
    'status_offline': '#6E7681',
    'status_warning': '#D29922',
    'status_error': '#F85149',
}
```

### Professional Light Theme Palette
```python
# Light theme - clean, high readability
COLORS_LIGHT = {
    # Backgrounds
    'bg_primary': '#FFFFFF',
    'bg_secondary': '#F6F8FA',
    'bg_tertiary': '#EAEEF2',
    'bg_overlay': '#FFFFFF',
    
    # Text hierarchy
    'text_primary': '#1F2328',
    'text_secondary': '#656D76',
    'text_muted': '#8C959F',
    
    # Semantic colors (adjusted for light bg)
    'accent_blue': '#0969DA',
    'accent_green': '#1A7F37',
    'accent_red': '#CF222E',
    'accent_yellow': '#9A6700',
    'accent_purple': '#8250DF',
    
    # Borders
    'border_default': '#D0D7DE',
    'border_muted': '#EAEEF2',
}
```

### QSS Theme Application
```css
/* CSS Variables pattern in QSS */
QWidget {
    background-color: #0D1117;
    color: #E6EDF3;
}

/* Card/panel styling with depth */
QFrame#card {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 16px;
}

/* Accent buttons */
QPushButton#primaryAction {
    background-color: #238636;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton#primaryAction:hover {
    background-color: #2EA043;
}

QPushButton#primaryAction:pressed {
    background-color: #238636;
    border: 2px solid #58A6FF;
}

/* Semantic status colors */
QLabel#statusSuccess { color: #238636; }
QLabel#statusError { color: #F85149; }
QLabel#statusWarning { color: #D29922; }
QLabel#statusInfo { color: #58A6FF; }
```

---

## Spatial Composition & Layout

### Layout Principles
1. **Visual Hierarchy**: Important elements larger, higher, or more prominent
2. **Grouping**: Related items close together (Gestalt proximity)
3. **Whitespace**: Generous padding prevents visual clutter
4. **Alignment**: Consistent grid system creates order
5. **Rhythm**: Repeating patterns create visual harmony

### Spacing System (8px Grid)
```python
# Consistent spacing based on 8px grid
SPACING = {
    'xs': 4,    # Tight: icon to text
    'sm': 8,    # Compact: related items
    'md': 16,   # Standard: between groups
    'lg': 24,   # Generous: section separation
    'xl': 32,   # Spacious: major sections
    'xxl': 48,  # Hero: page margins
}

# Apply in layouts
layout = QVBoxLayout()
layout.setContentsMargins(SPACING['xl'], SPACING['lg'], SPACING['xl'], SPACING['lg'])
layout.setSpacing(SPACING['md'])
```

### Dashboard Layout Patterns
```python
# KPI Cards Row (3-4 cards, equal width)
kpi_layout = QHBoxLayout()
kpi_layout.setSpacing(16)
for kpi_data in kpis:
    card = KPICard(kpi_data)
    kpi_layout.addWidget(card, stretch=1)  # Equal stretch

# Two-column content (sidebar + main)
content_layout = QHBoxLayout()
sidebar = QWidget()
sidebar.setFixedWidth(280)  # Fixed sidebar
main_content = QWidget()
content_layout.addWidget(sidebar)
content_layout.addWidget(main_content, stretch=1)  # Main stretches

# Grid of cards (responsive feel)
grid = QGridLayout()
grid.setSpacing(16)
for i, item in enumerate(items):
    row, col = divmod(i, 3)  # 3 columns
    grid.addWidget(ItemCard(item), row, col)
```

### Visual Grouping with Cards
```python
class CardFrame(QFrame):
    """Reusable card container with consistent styling."""
    
    def __init__(self, title: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            layout.addWidget(title_label)
```

---

## Visual Details & Polish

### Shadows & Depth (QPainter)
```python
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

def add_card_shadow(widget: QWidget):
    """Add subtle shadow for depth (VISUAL POLISH)."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    shadow.setColor(QColor(0, 0, 0, 40))  # 15% opacity black
    widget.setGraphicsEffect(shadow)
```

### Border Radius & Rounded Corners
```css
/* Consistent border radius scale */
QFrame#card { border-radius: 8px; }
QPushButton { border-radius: 6px; }
QLineEdit { border-radius: 4px; }
QLabel#badge { border-radius: 12px; }  /* Pill shape for small badges */
```

### Subtle Gradients & Backgrounds
```css
/* Subtle gradient for depth */
QWidget#sidebar {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #161B22,
        stop: 1 #0D1117
    );
}

/* Accent gradient for buttons */
QPushButton#heroButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #238636,
        stop: 1 #2EA043
    );
}
```

### Icons & Visual Indicators
```python
# Use icons purposefully, not decoratively
from PySide6.QtGui import QIcon

# Status indicators with color + icon
def create_status_indicator(status: str) -> QLabel:
    """Create status badge with icon and color (VISUAL INDICATOR)."""
    label = QLabel()
    
    status_config = {
        'online': ('●', '#238636'),
        'offline': ('○', '#6E7681'),
        'warning': ('⚠', '#D29922'),
        'error': ('✕', '#F85149'),
    }
    
    icon, color = status_config.get(status, ('?', '#8B949E'))
    label.setText(f"{icon} {status.title()}")
    label.setStyleSheet(f"color: {color}; font-weight: 500;")
    return label
```

---

## Motion & Animation

### Animation Principles
1. **Purpose**: Animation should communicate, not decorate
2. **Duration**: 150-300ms for UI feedback, 300-500ms for transitions
3. **Easing**: Use natural curves (ease-out for entries, ease-in for exits)
4. **Consistency**: Same animation for same action type

### Qt Animation Implementation
```python
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup

def fade_in_widget(widget: QWidget, duration: int = 200):
    """Fade in widget on show (MICRO-INTERACTION)."""
    widget.setWindowOpacity(0)
    
    animation = QPropertyAnimation(widget, b"windowOpacity")
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start()

def slide_in_panel(widget: QWidget, direction: str = 'left', duration: int = 300):
    """Slide panel into view (PAGE TRANSITION)."""
    start_pos = widget.pos()
    
    if direction == 'left':
        widget.move(start_pos.x() - 50, start_pos.y())
    elif direction == 'right':
        widget.move(start_pos.x() + 50, start_pos.y())
    
    animation = QPropertyAnimation(widget, b"pos")
    animation.setDuration(duration)
    animation.setEndValue(start_pos)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start()

def pulse_attention(widget: QWidget):
    """Pulse widget to draw attention (NOTIFICATION)."""
    animation = QPropertyAnimation(widget, b"windowOpacity")
    animation.setDuration(150)
    animation.setKeyValueAt(0, 1.0)
    animation.setKeyValueAt(0.5, 0.6)
    animation.setKeyValueAt(1, 1.0)
    animation.start()
```

### Hover State Animations
```python
class AnimatedButton(QPushButton):
    """Button with smooth hover animation (MICRO-INTERACTION)."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(100)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def enterEvent(self, event):
        # Subtle scale up on hover
        current = self.geometry()
        self._animation.setStartValue(current)
        expanded = current.adjusted(-2, -1, 2, 1)
        self._animation.setEndValue(expanded)
        self._animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        # Return to original size
        self._animation.setDirection(QPropertyAnimation.Direction.Backward)
        self._animation.start()
        super().leaveEvent(event)
```

---

## Design Checklist

Before shipping any UI:

### Typography
- [ ] Clear hierarchy (title > header > body > caption)
- [ ] Consistent font family throughout
- [ ] Appropriate sizes (not too small, not too large)
- [ ] Sufficient line height for readability

### Color
- [ ] Semantic colors used consistently
- [ ] Sufficient contrast for accessibility
- [ ] Dark/light theme support (if applicable)
- [ ] Accent colors draw attention purposefully

### Layout
- [ ] Consistent spacing (8px grid)
- [ ] Visual grouping of related items
- [ ] Alignment on invisible grid
- [ ] Adequate whitespace

### Polish
- [ ] Smooth animations where appropriate
- [ ] Hover/active states for interactive elements
- [ ] Loading states for async operations
- [ ] Error states are clear and helpful

### Accessibility
- [ ] Keyboard navigation works
- [ ] Focus states are visible
- [ ] Color is not the only indicator
- [ ] Text is resizable

---

## Resources

### Qt/PySide6 Specific
- **PySide6 Book**: `Docs/pyside6/create-gui-applications-pyside6.pdf` (Chapter 4: Theming)
- **Qt Style Sheets Reference**: https://doc.qt.io/qt-6/stylesheet-reference.html
- **Qt Animation Framework**: https://doc.qt.io/qt-6/animation-overview.html

### Design Inspiration
- **Dribbble**: https://dribbble.com/tags/dashboard
- **Figma Community**: https://figma.com/community (search "dashboard")
- **Carbon Design System**: https://carbondesignsystem.com/ (IBM's design system)
- **Primer Design System**: https://primer.style/ (GitHub's design system)

### Color Tools
- **Coolors**: https://coolors.co/ (palette generator)
- **Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Color Hunt**: https://colorhunt.co/ (curated palettes)

### Typography
- **Google Fonts**: https://fonts.google.com/
- **Font Pair**: https://fontpair.co/ (font pairing suggestions)
- **Type Scale**: https://typescale.com/ (size hierarchy calculator)

---

**Last Updated**: February 2, 2026  
**Purpose**: Design thinking principles for PySide6 desktop applications
