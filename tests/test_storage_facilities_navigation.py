"""
Quick test script to check if storage facilities page loads on first and second navigation.

Run: python test_storage_facilities_navigation.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt, QTimer
import logging

# Configure logging to show all messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')

from ui.dashboards.storage_facilities_dashboard import StorageFacilitiesPage

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storage Facilities Navigation Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget with layout
        central = QWidget()
        layout = QVBoxLayout()
        
        # Create button bar
        btn_layout = QVBoxLayout()
        btn_show = QPushButton("Show Storage Facilities Page")
        btn_hide = QPushButton("Hide Storage Facilities Page")
        btn_layout.addWidget(btn_show)
        btn_layout.addWidget(btn_hide)
        
        # Create stacked widget for pages
        self.pages = QStackedWidget()
        self.storage_page = StorageFacilitiesPage()
        self.pages.addWidget(self.storage_page)
        
        # Add to main layout
        layout.addLayout(btn_layout)
        layout.addWidget(self.pages)
        
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Connect buttons
        btn_show.clicked.connect(self.show_storage_page)
        btn_hide.clicked.connect(self.hide_storage_page)
        
        self.click_count = 0
    
    def show_storage_page(self):
        self.click_count += 1
        print(f"\n{'='*80}")
        print(f"CLICK #{self.click_count}: Showing storage facilities page")
        print(f"{'='*80}")
        self.pages.setCurrentWidget(self.storage_page)
        self.storage_page.show()
    
    def hide_storage_page(self):
        self.click_count += 1
        print(f"\n{'='*80}")
        print(f"CLICK #{self.click_count}: Hiding storage facilities page")
        print(f"{'='*80}")
        self.pages.setCurrentIndex(-1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    # Automatically show page first time after app starts
    QTimer.singleShot(500, window.show_storage_page)
    
    print("Window opened. Click 'Show Storage Facilities Page' button to test navigation.")
    print("Click 'Hide Storage Facilities Page' to hide it (simulating navigation away).")
    print("Then click 'Show' again to test second load.")
    
    sys.exit(app.exec())
