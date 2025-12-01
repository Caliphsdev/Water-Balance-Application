"""
Splash Screen for Water Balance Application
Shows during application initialization with progress updates
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading


class SplashScreen:
    """Professional splash screen with progress bar"""
    
    def __init__(self, app_version="1.0.0"):
        """Initialize splash screen"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide initially
        
        # Window configuration
        self.width = 600
        self.height = 400
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Center window
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')
        
        # Create main container with shadow effect
        self.container = tk.Frame(
            self.root,
            bg='#ffffff',
            relief='flat',
            borderwidth=0
        )
        self.container.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Add shadow border
        self.root.config(bg='#cccccc')
        
        # Header section with gradient-like effect
        header_frame = tk.Frame(self.container, bg='#1e3a8a', height=120)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # App title
        title_label = tk.Label(
            header_frame,
            text="Water Balance\nManagement System",
            font=('Segoe UI', 24, 'bold'),
            fg='white',
            bg='#1e3a8a',
            justify='center'
        )
        title_label.pack(expand=True)
        
        # Version label
        version_label = tk.Label(
            header_frame,
            text=f"Version {app_version}",
            font=('Segoe UI', 10),
            fg='#93c5fd',
            bg='#1e3a8a'
        )
        version_label.pack(side='bottom', pady=(0, 10))
        
        # Content area
        content_frame = tk.Frame(self.container, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=40, pady=30)
        
        # Status label
        self.status_label = tk.Label(
            content_frame,
            text="Initializing application...",
            font=('Segoe UI', 11),
            fg='#374151',
            bg='#ffffff',
            justify='center'
        )
        self.status_label.pack(pady=(20, 15))
        
        # Progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Splash.Horizontal.TProgressbar',
            troughcolor='#e5e7eb',
            background='#3b82f6',
            borderwidth=0,
            thickness=8
        )
        
        self.progress = ttk.Progressbar(
            content_frame,
            style='Splash.Horizontal.TProgressbar',
            mode='determinate',
            maximum=100,
            value=0
        )
        self.progress.pack(fill='x', pady=(0, 20))
        
        # Detail label (smaller text for sub-tasks)
        self.detail_label = tk.Label(
            content_frame,
            text="",
            font=('Segoe UI', 9),
            fg='#6b7280',
            bg='#ffffff',
            justify='center'
        )
        self.detail_label.pack(pady=(5, 10))
        
        # Footer
        footer_frame = tk.Frame(self.container, bg='#f9fafb', height=50)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(
            footer_frame,
            text="© 2025 Mine Water Management Solutions",
            font=('Segoe UI', 8),
            fg='#9ca3af',
            bg='#f9fafb'
        )
        footer_label.pack(expand=True)
        
        # Show window
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        
        # Update to ensure it's drawn
        self.root.update()
    
    def update_progress(self, value, status="", detail=""):
        """
        Update splash screen progress
        
        Args:
            value: Progress value (0-100)
            status: Main status message
            detail: Detail/sub-task message
        """
        try:
            if self.root.winfo_exists():
                self.progress['value'] = value
                
                if status:
                    self.status_label.config(text=status)
                
                if detail:
                    self.detail_label.config(text=detail)
                
                self.root.update()
        except:
            pass  # Window might have been destroyed
    
    def close(self):
        """Close the splash screen"""
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except:
            pass


class ThreadedLoader:
    """Handle application initialization in background thread"""
    
    def __init__(self, splash):
        """Initialize threaded loader"""
        self.splash = splash
        self.error = None
        self.completed = False
        
    def load(self, load_function):
        """
        Load application components with progress updates
        
        Args:
            load_function: Function that performs the actual loading
                          Should accept a callback: progress_callback(value, status, detail)
        """
        def worker():
            try:
                # Call the provided load function with progress callback
                load_function(self.splash.update_progress)
                self.completed = True
            except Exception as e:
                self.error = e
                self.completed = True
        
        # Start loading in background thread
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        
        # Wait for completion (keep splash responsive)
        while not self.completed:
            self.splash.root.update()
        
        # Small delay to show 100% completion
        if not self.error:
            self.splash.update_progress(100, "Ready!", "Starting application...")
            self.splash.root.after(500)
            self.splash.root.update()
        
        # Close splash
        self.splash.close()
        
        # Raise error if occurred
        if self.error:
            raise self.error


def show_splash_and_load(app_version, load_function):
    """
    Convenience function to show splash and load application
    
    Args:
        app_version: Application version string
        load_function: Function to call for loading (receives progress_callback)
    
    Returns:
        True if successful, False if error occurred
    
    Example:
        def my_loader(progress_callback):
            progress_callback(20, "Loading config...")
            # ... load config ...
            progress_callback(40, "Loading database...")
            # ... load database ...
            progress_callback(100, "Complete!")
        
        success = show_splash_and_load("1.0.0", my_loader)
    """
    try:
        splash = SplashScreen(app_version)
        loader = ThreadedLoader(splash)
        loader.load(load_function)
        return True
    except Exception as e:
        # Close splash if still open
        try:
            splash.close()
        except:
            pass
        raise e


if __name__ == "__main__":
    """Test splash screen"""
    import time
    
    def test_load(progress_callback):
        """Simulate loading"""
        steps = [
            (10, "Loading configuration...", "Reading config files"),
            (25, "Initializing database...", "Connecting to SQLite"),
            (45, "Loading modules...", "Importing UI components"),
            (65, "Preparing interface...", "Building main window"),
            (85, "Loading data...", "Caching frequently used data"),
            (100, "Ready!", "Starting application")
        ]
        
        for value, status, detail in steps:
            progress_callback(value, status, detail)
            time.sleep(0.5)
    
    show_splash_and_load("1.0.0", test_load)
    print("Splash screen test complete!")
