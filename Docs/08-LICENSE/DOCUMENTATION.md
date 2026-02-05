# Email System Component Documentation

A reusable PySide6 email inbox component with SQLite backend, sliding drawer, and modern UI.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Dependencies](#dependencies)
3. [Quick Start](#quick-start)
4. [Database Layer](#database-layer)
5. [Data Model](#data-model)
6. [UI Components](#ui-components)
7. [Styling](#styling)
8. [Integration Guide](#integration-guide)
9. [API Reference](#api-reference)
10. [Book References](#book-references)

---

## Project Structure

```
email_app/
├── main.py              # Entry point (modify for your app)
├── database.py          # SQLite connection, CRUD operations
├── email_model.py       # Qt data model for email list
├── main_window.py       # Main window with message list + drawer
├── message_card.py      # Custom widget for email preview cards
├── drawer_panel.py      # Sliding panel for full message view
├── styles.py            # QSS stylesheet
├── emails.db            # SQLite database (auto-created)
└── DOCUMENTATION.md     # This file
```

---

## Dependencies

```bash
pip install PySide6
```

Minimum Python version: 3.9+

---

## Quick Start

### Standalone Usage

```python
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from database import get_database, seed_sample_data, close_database
from email_model import EmailListModel
from main_window import EmailMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    
    # Initialize database
    db = get_database()
    seed_sample_data(db)  # Optional: adds demo emails
    
    # Create model and window
    email_model = EmailListModel(db)
    window = EmailMainWindow(email_model)
    window.show()
    
    exit_code = app.exec()
    close_database()
    sys.exit(exit_code)
```

### Embedding in Another Application

```python
from email_app.database import get_database
from email_app.email_model import EmailListModel
from email_app.main_window import EmailMainWindow

# In your main application:
db = get_database()
email_model = EmailListModel(db)
email_widget = EmailMainWindow(email_model)

# Add to your layout
your_layout.addWidget(email_widget)
```

---

## Database Layer

### File: `database.py`

#### Connection Setup

```python
from database import get_database, close_database

# Get or create connection (singleton pattern)
db = get_database()

# Always close on app exit
close_database()
```

#### SQLite Optimizations Applied

| PRAGMA | Value | Purpose |
|--------|-------|---------|
| `journal_mode` | WAL | Crash recovery, concurrent reads |
| `synchronous` | NORMAL | Balance of safety vs speed |
| `cache_size` | -8000 | 8MB cache for faster queries |
| `foreign_keys` | ON | Referential integrity |
| `temp_store` | MEMORY | Faster temp operations |

#### Database Schema

```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT NOT NULL,
    sender_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    preview TEXT,
    body TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read INTEGER DEFAULT 0,
    is_starred INTEGER DEFAULT 0,
    folder TEXT DEFAULT 'inbox'
);

-- Indexes for performance
CREATE INDEX idx_emails_received ON emails(received_at DESC);
CREATE INDEX idx_emails_read ON emails(is_read);
CREATE INDEX idx_emails_folder ON emails(folder);
CREATE INDEX idx_emails_folder_date ON emails(folder, received_at DESC);
```

#### CRUD Operations

```python
from database import (
    insert_email,
    get_all_emails,
    mark_as_read,
    delete_email,
    get_email_count,
    get_unread_count,
    vacuum_database
)

# Insert email
email_id = insert_email(db, {
    "sender": "John Doe",
    "sender_email": "john@example.com",
    "subject": "Hello",
    "preview": "Quick message...",
    "body": "Full email content here",
    "received_at": datetime.now(),  # Optional, defaults to now
    "read": False
})

# Fetch emails with pagination
emails = get_all_emails(db, limit=50, offset=0)

# Mark as read
mark_as_read(db, email_id)

# Delete
delete_email(db, email_id)

# Counts
total = get_email_count(db)
unread = get_unread_count(db)

# Reclaim space (run periodically, not on every delete)
vacuum_database(db)
```

---

## Data Model

### File: `email_model.py`

The `EmailListModel` extends `QAbstractListModel` for Qt's Model/View architecture.

#### Custom Data Roles

```python
class EmailListModel(QAbstractListModel):
    IdRole = Qt.ItemDataRole.UserRole + 1
    SenderRole = Qt.ItemDataRole.UserRole + 2
    SenderEmailRole = Qt.ItemDataRole.UserRole + 3
    SubjectRole = Qt.ItemDataRole.UserRole + 4
    PreviewRole = Qt.ItemDataRole.UserRole + 5
    BodyRole = Qt.ItemDataRole.UserRole + 6
    ReceivedAtRole = Qt.ItemDataRole.UserRole + 7
    IsReadRole = Qt.ItemDataRole.UserRole + 8
    IsNewRole = Qt.ItemDataRole.UserRole + 9
    IsStarredRole = Qt.ItemDataRole.UserRole + 10
```

#### Signals

```python
# Emitted when email count changes
email_count_changed = Signal(int, int)  # (total, unread)
```

#### Key Methods

```python
model = EmailListModel(db)

# Get email data
email = model.get_email(row)           # By row index
email = model.get_email_by_id(email_id)  # By database ID

# Check if new (< 2 minutes old and unread)
is_new = model.is_new(row)

# Modify data
model.mark_as_read(row)
model.delete(row)
model.add_email(email_dict)

# Refresh from database
model.refresh()

# Access all emails
all_emails = model.emails
```

#### "NEW" Badge Logic

An email shows the NEW badge if:
1. `received_at` is less than 2 minutes ago
2. `is_read` is False

```python
NEW_MESSAGE_THRESHOLD = timedelta(minutes=2)

def is_new(self, row: int) -> bool:
    email = self._emails[row]
    age = datetime.now() - email["received_at"]
    return age < NEW_MESSAGE_THRESHOLD and not email["read"]
```

To change the threshold, modify `NEW_MESSAGE_THRESHOLD` in both:
- `email_model.py`
- `message_card.py`

---

## UI Components

### Main Window (`main_window.py`)

Layout structure:
```
┌─────────────────────────────────────────────────┐
│  QHBoxLayout (main)                             │
│  ┌──────────────┬───────────────────────────┐   │
│  │ Message List │  Drawer Panel (animated)  │   │
│  │ (scrollable) │  (slides from right)      │   │
│  │              │                           │   │
│  │  [Card 1]    │  Full message content     │   │
│  │  [Card 2]    │                           │   │
│  │  [Card 3]    │                           │   │
│  └──────────────┴───────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

#### Constructor

```python
class EmailMainWindow(QMainWindow):
    def __init__(self, email_model: EmailListModel):
        # Requires an EmailListModel instance
```

#### Animation Details

The drawer uses dual `QPropertyAnimation` for smooth sliding:

```python
# Animate both min and max width simultaneously
self._drawer_animation = QPropertyAnimation(self.drawer, b"minimumWidth")
self._drawer_max_animation = QPropertyAnimation(self.drawer, b"maximumWidth")

# Settings
duration = 300  # milliseconds
easing = QEasingCurve.Type.OutCubic
target_width = 450  # pixels when open
```

### Message Card (`message_card.py`)

A custom `QFrame` widget for email previews.

#### Constructor

```python
class MessageCard(QFrame):
    def __init__(self, email: dict, is_new: bool = False, parent=None):
        # email: Dictionary with sender, subject, preview, received_at
        # is_new: Whether to show NEW badge
```

#### Signals

```python
clicked = Signal()  # Emitted on left-click
```

#### Methods

```python
card.set_selected(True)   # Visual selection state
card.hide_new_badge()     # Hide NEW badge when read
card.is_selected()        # Check selection state
```

#### Email Dictionary Format

```python
{
    "id": int,
    "sender": str,           # Display name
    "sender_email": str,     # Email address
    "subject": str,
    "preview": str,          # First ~80 chars of body
    "body": str,             # Full message
    "received_at": datetime,
    "read": bool,
    "starred": bool,
    "folder": str            # 'inbox', 'sent', etc.
}
```

### Drawer Panel (`drawer_panel.py`)

Sliding panel showing full email content.

#### Constructor

```python
class DrawerPanel(QFrame):
    def __init__(self, parent=None):
```

#### Signals

```python
close_requested = Signal()  # Emitted when close button clicked
```

#### Methods

```python
drawer.set_email(email_dict)  # Update display content
```

---

## Styling

### File: `styles.py`

Returns a QSS (Qt Style Sheet) string via `get_stylesheet()`.

#### Color Scheme

| Element | Color | Hex |
|---------|-------|-----|
| Background | Dark gray | `#1a1a2e` |
| Card background | Slightly lighter | `#16213e` |
| Card hover | Blue tint | `#1a2744` |
| Card selected | Accent blue | `#0f3460` |
| NEW badge | Bright green | `#00d26a` |
| Text primary | White | `#ffffff` |
| Text secondary | Gray | `#8892a0` |
| Accent | Blue | `#4a9eff` |

#### Object Names (for QSS targeting)

| Widget | Object Name |
|--------|-------------|
| Message list container | `messageListContainer` |
| Scroll area | `messageScrollArea` |
| Message list | `messageList` |
| Inbox header | `inboxHeader` |
| Inbox title | `inboxTitle` |
| Message count | `messageCount` |
| Message card | `messageCard` |
| Sender label | `senderLabel` |
| Subject label | `subjectLabel` |
| Preview label | `previewLabel` |
| Time label | `timeLabel` |
| NEW badge | `newBadge` |
| Drawer panel | `drawerPanel` |
| Close button | `closeButton` |

#### Applying Custom Styles

```python
# Option 1: Modify styles.py directly
def get_stylesheet():
    return """
        /* Your custom styles */
    """

# Option 2: Override in your app
window.setStyleSheet(your_custom_stylesheet)
```

---

## Integration Guide

### Step 1: Copy Files

Copy these files to your project:
- `database.py`
- `email_model.py`
- `main_window.py`
- `message_card.py`
- `drawer_panel.py`
- `styles.py`

### Step 2: Adjust Database Path

In `database.py`, modify `DATABASE_PATH`:

```python
# Current (relative to module)
BASEDIR = os.path.dirname(__file__)
DATABASE_PATH = os.path.join(BASEDIR, "emails.db")

# Alternative (app data directory)
import platformdirs
DATABASE_PATH = os.path.join(
    platformdirs.user_data_dir("YourAppName"),
    "emails.db"
)
```

### Step 3: Initialize in Your App

```python
from your_email_module.database import get_database, close_database
from your_email_module.email_model import EmailListModel
from your_email_module.main_window import EmailMainWindow

class YourMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize email system
        self.db = get_database()
        self.email_model = EmailListModel(self.db)
        self.email_panel = EmailMainWindow(self.email_model)
        
        # Add to your layout
        self.setCentralWidget(self.email_panel)
        # OR: some_layout.addWidget(self.email_panel)
    
    def closeEvent(self, event):
        close_database()
        super().closeEvent(event)
```

### Step 4: Adding New Emails Programmatically

```python
from database import insert_email
from datetime import datetime

# When a new email arrives
new_email = {
    "sender": "System",
    "sender_email": "system@yourapp.com",
    "subject": "Notification",
    "preview": "You have a new notification...",
    "body": "Full notification text here.",
    "received_at": datetime.now(),
    "read": False
}

insert_email(self.db, new_email)
self.email_model.refresh()  # Reload the list
```

### Step 5: Customize the UI

#### Change Drawer Width
In `main_window.py`:
```python
def _open_drawer(self):
    target_width = 500  # Change from 450
```

#### Change NEW Badge Threshold
In both `email_model.py` and `message_card.py`:
```python
NEW_MESSAGE_THRESHOLD = timedelta(minutes=5)  # Change from 2
```

#### Change Card Height
In `message_card.py`:
```python
self.setFixedHeight(100)  # Change from 90
```

---

## API Reference

### database.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `get_database()` | - | `QSqlDatabase` | Get/create DB connection |
| `close_database()` | - | - | Close connection on exit |
| `insert_email(db, email)` | db, dict | int | Insert email, returns ID |
| `get_all_emails(db, limit, offset)` | db, int, int | list | Paginated fetch |
| `mark_as_read(db, email_id)` | db, int | - | Mark email read |
| `delete_email(db, email_id)` | db, int | - | Delete email |
| `get_email_count(db)` | db | int | Total email count |
| `get_unread_count(db)` | db | int | Unread email count |
| `vacuum_database(db)` | db | - | Reclaim disk space |
| `seed_sample_data(db)` | db | - | Add demo emails |

### email_model.py - EmailListModel

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `rowCount()` | - | int | Number of emails |
| `get_email(row)` | int | dict | Email at row |
| `get_email_by_id(id)` | int | dict | Email by DB ID |
| `is_new(row)` | int | bool | Check if < 2 min old |
| `mark_as_read(row)` | int | - | Mark read + notify |
| `delete(row)` | int | - | Delete + notify |
| `add_email(email)` | dict | - | Insert + refresh |
| `refresh()` | - | - | Reload from DB |

### message_card.py - MessageCard

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `set_selected(bool)` | bool | - | Set visual state |
| `is_selected()` | - | bool | Check selection |
| `hide_new_badge()` | - | - | Hide NEW badge |

### drawer_panel.py - DrawerPanel

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `set_email(email)` | dict | - | Display email content |

---

## Book References

This component follows patterns from **"Create GUI Applications with Python & Qt6"** by Martin Fitzpatrick:

| Topic | Pages | Usage |
|-------|-------|-------|
| QMainWindow | 12-17 | Main window structure |
| Signals & Slots | 18-27 | Event communication |
| Layouts | 56-85 | Nested layout structure |
| Custom Widgets | 387-414 | MessageCard, DrawerPanel |
| QSS Styling | 218-265 | Visual customization |
| Model/View | 266-331 | EmailListModel architecture |
| SQL Databases | 332-357 | SQLite with QSqlDatabase |
| Custom Signals | 565-574 | clicked, close_requested |

---

## Troubleshooting

### Database locked error
- Ensure only one connection is active
- Call `close_database()` before reopening

### Drawer not animating
- Check that both min and max width animations are running
- Verify initial width is set to 0

### Styles not applying
- Verify object names match QSS selectors
- Call `style().unpolish()` and `style().polish()` after property changes

### NEW badge not showing
- Check `received_at` is a `datetime` object, not string
- Verify time threshold in both model and card

---

## License

MIT License - Use freely in your projects.
