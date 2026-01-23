"""
Professional loading screen for Water Balance Application
Centered dialog with smooth animations - no freeze, no full-screen takeover
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from tkinter import ttk
import threading
import time


class LoadingScreen:
    """Professional loading screen with smooth progress animation - centered dialog"""
    
    def __init__(self, root=None):
        """Initialize loading screen as centered dialog (not full-screen).
        
        Args:
            root: Optional root window to use (required)
        """
        if root is None:
            # Create a hidden root window ONLY if none provided
            hidden_root = tk.Tk()
            hidden_root.withdraw()
            hidden_root.attributes('-alpha', 0.0)
            self.root = tk.Toplevel(hidden_root)
            self.hidden_root = hidden_root
            self.own_root = True
        else:
            # Use provided root (preferred approach)
            self.root = tk.Toplevel(root)
            self.hidden_root = None
            self.own_root = False
            
        # Modern color scheme
        self.bg_light = '#ffffff'
        self.bg_secondary = '#f5f6f7'
        self.accent = '#0066cc'
        self.text_primary = '#2c3e50'
        self.text_secondary = '#7f8c8d'
        self.border_color = '#e0e0e0'
        # Transparent color used to knock out square corners on Windows
        self.transparent_color = '#010101'
        
        # Set window properties
        self.root.configure(bg=self.transparent_color)
        self.root.resizable(False, False)
        self.root.overrideredirect(True)  # No title bar for clean look

        # Centered dialog: smaller footprint with rounded-corner illusion
        dialog_width, dialog_height = 560, 430
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        
        self.root.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')
        self.root.attributes('-topmost', True)
        try:
            # Make the transparent color fully see-through so the rounded path reads
            self.root.attributes('-transparentcolor', self.transparent_color)
        except tk.TclError:
            # Some platforms do not support transparent toplevels; fall back gracefully
            pass
        
        # Canvas container lets us draw a rounded backdrop while leaving corners transparent
        container_canvas = tk.Canvas(
            self.root,
            bg=self.transparent_color,
            highlightthickness=0,
            bd=0
        )
        container_canvas.pack(fill='both', expand=True)
        container_canvas.bind(
            '<Configure>',
            lambda event: self._redraw_rounded_background(
                container_canvas,
                event.width,
                event.height
            )
        )
        self.rounded_bg_id = None
        self.dialog_padding = 12
        self.dialog_width = dialog_width
        self.dialog_height = dialog_height
        
        # Inner content frame with white background anchored inside rounded canvas
        main_frame = tk.Frame(container_canvas, bg=self.bg_light)
        main_frame.place(
            x=self.dialog_padding,
            y=self.dialog_padding,
            width=dialog_width - (self.dialog_padding * 2),
            height=dialog_height - (self.dialog_padding * 2)
        )
        
        # Logo/Title section - compact for centered dialog
        title_frame = tk.Frame(main_frame, bg=self.bg_light)
        title_frame.pack(fill='x', pady=(24, 8))
        
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
            else:
                # Fallback to icon if logo not found
                company_label = tk.Label(
                    title_frame,
                    text="🏢",
                    font=('Segoe UI', 28),
                    fg=self.text_primary,
                    bg=self.bg_light
                )
                company_label.pack(pady=(0, 4))
        except Exception as e:
            # Fallback to icon if image loading fails
            company_label = tk.Label(
                title_frame,
                text="🏢",
                font=('Segoe UI', 28),
                fg=self.text_primary,
                bg=self.bg_light
            )
            company_label.pack(pady=(0, 4))
        
        title = tk.Label(
            title_frame,
            text="Water Balance System",
            font=('Segoe UI', 13, 'bold'),
            fg=self.text_primary,
            bg=self.bg_light
        )
        title.pack(pady=(0, 2))
        
        subtitle = tk.Label(
            title_frame,
            text="TransAfrica Resources",
            font=('Segoe UI', 9),
            fg=self.text_secondary,
            bg=self.bg_light
        )
        subtitle.pack()
        
        # Status text - shown early
        self.status_label = tk.Label(
            main_frame,
            text="Initializing application...",
            font=('Segoe UI', 9),
            fg=self.text_primary,
            bg=self.bg_light,
            wraplength=450
        )
        self.status_label.pack(pady=(8, 12))
        
        # Progress bar container - compact
        progress_container = tk.Frame(main_frame, bg=self.bg_light)
        progress_container.pack(pady=(6, 6), padx=40)
        
        # Custom progress bar background - smaller
        self.progress_bg = tk.Canvas(
            progress_container,
            width=300,
            height=6,
            bg='#e0e0e0',
            highlightthickness=0,
            bd=0
        )
        self.progress_bg.pack()
        
        # Progress bar fill
        self.progress_fill = self.progress_bg.create_rectangle(
            0, 0, 0, 6,
            fill=self.accent,
            outline=''
        )
        
        # Percentage label - smaller
        self.percent_label = tk.Label(
            main_frame,
            text="0%",
            font=('Segoe UI', 8),
            fg=self.text_secondary,
            bg=self.bg_light
        )
        self.percent_label.pack(pady=(3, 8))
        
        # Loading animation - smooth spinner (no freeze)
        self.animation_canvas = tk.Canvas(
            main_frame,
            width=50,
            height=50,
            bg=self.bg_light,
            highlightthickness=0
        )
        self.animation_canvas.pack(pady=(8, 24))
        
        # Spinning circle for animation
        self.spinner_angle = 0
        self.spinner_id = None
        self.running = False
        self.show_time = None
        self.min_display_time = 3500  # Extended: 3.5 seconds for app to prepare without rushing
        
        # Smooth progress animation
        self.target_progress = 0
        self.current_progress = 0
        self.progress_animation_id = None
        self.is_ready = False

    def _redraw_rounded_background(
        self,
        canvas: tk.Canvas,
        width: int,
        height: int
    ) -> None:
        """Redraw rounded rectangle backdrop to keep curved edges on resize.

        Args:
            canvas: Canvas hosting the rounded background polygon
            width: Current canvas width
            height: Current canvas height
        """
        # Delete old polygon so we can redraw the rounded path with new bounds
        if self.rounded_bg_id:
            canvas.delete(self.rounded_bg_id)

        # Small inset keeps the stroke fully visible when transparent corners are used
        inset = 2
        radius = 18
        self.rounded_bg_id = self._create_rounded_rectangle(
            canvas,
            inset,
            inset,
            max(inset + radius, width - inset),
            max(inset + radius, height - inset),
            radius=radius,
            fill=self.bg_light,
            outline=self.border_color
        )
    
    def set_geometry(self, geometry: str):
        """Set loading screen geometry (ignored for centered dialog)."""
        # Centered dialog maintains fixed size - no need to resize
        pass
        
    def set_status(self, status_text: str, progress: int = None):
        """Update status text and optional progress value - no freeze.
        
        Args:
            status_text: Text to display
            progress: Optional progress percentage (0-100)
        """
        try:
            self.status_label.config(text=status_text)
            if progress is not None:
                # Set target progress for smooth animation
                self.target_progress = max(0, min(100, progress))
                if not self.progress_animation_id:
                    self._animate_progress()
            
            # Process events once for smooth animation (no freeze)
            self.root.update_idletasks()
        except Exception:
            pass  # Silently fail if window is destroyed
    
    def _animate_progress(self):
        """Smoothly animate progress bar to target - reaches 100% well before loading completes."""
        try:
            if self.current_progress < self.target_progress:
                # Moderate increment: reaches 100% in ~3 seconds (leaves good buffer before screen closes at 3.5s)
                step = max(0.5, (self.target_progress - self.current_progress) / 70)
                self.current_progress = min(self.target_progress, self.current_progress + step)
                
                # Update progress bar
                width = int((self.current_progress / 100) * 300)
                self.progress_bg.coords(self.progress_fill, 0, 0, width, 6)
                self.percent_label.config(text=f"{int(self.current_progress)}%")
                
                # Continue animation with reasonable delay (no hang)
                self.progress_animation_id = self.root.after(30, self._animate_progress)
            else:
                self.progress_animation_id = None
        except:
            self.progress_animation_id = None
        
    def start_animation(self):
        """Start the loading spinner animation - smooth, no freeze."""
        self.running = True
        self._animate_spinner()
        
    def stop_animation(self):
        """Stop the loading animation cleanly."""
        self.running = False
        if self.spinner_id:
            self.root.after_cancel(self.spinner_id)
        if self.progress_animation_id:
            self.root.after_cancel(self.progress_animation_id)
        
    def _animate_spinner(self):
        """Animate the spinner - smooth arc rotation."""
        if self.running:
            try:
                self.animation_canvas.delete('all')
                
                # Draw spinning arc - smooth, compact
                self.animation_canvas.create_arc(
                    5, 5, 45, 45,
                    start=self.spinner_angle,
                    extent=100,
                    outline=self.accent,
                    width=4,
                    style='arc'
                )
                
                self.spinner_angle = (self.spinner_angle + 12) % 360
                self.spinner_id = self.root.after(50, self._animate_spinner)
            except:
                pass
    
    def show(self):
        """Display the loading screen."""
        import time
        self.show_time = time.time()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.start_animation()
        self.root.update()
        
    def close(self):
        """Close the loading screen with minimal delay - no unnecessary freeze."""
        # Calculate how long screen has been shown
        if self.show_time:
            import time
            current_time = time.time()
            elapsed_ms = (current_time - self.show_time) * 1000
            remaining_ms = max(0, self.min_display_time - elapsed_ms)
        else:
            remaining_ms = 0
        
        # Add only a tiny delay for visual polish (300ms, was 2500ms)
        total_delay = remaining_ms + 300
        
        # Schedule close
        def _fade_and_close():
            self.stop_animation()
            # Quick fade out (200ms)
            steps = 5
            for i in range(steps, 0, -1):
                try:
                    alpha = i / steps
                    self.root.attributes('-alpha', alpha)
                    self.root.update()
                    import time
                    time.sleep(0.04)
                except:
                    break
            
            try:
                if self.own_root:
                    self.root.destroy()
                    if self.hidden_root:
                        self.hidden_root.destroy()
                else:
                    self.root.withdraw()
            except:
                pass
        
        if total_delay > 0:
            self.root.after(int(total_delay), _fade_and_close)
        else:
            _fade_and_close()

    @staticmethod
    def _create_rounded_rectangle(
        canvas: tk.Canvas,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int = 16,
        **kwargs
    ) -> int:
        """Draw a rounded rectangle on the given canvas.

        Args:
            canvas: Target canvas
            x1: Left coordinate
            y1: Top coordinate
            x2: Right coordinate
            y2: Bottom coordinate
            radius: Corner radius in pixels
            **kwargs: Forwarded canvas styling options

        Returns:
            Canvas polygon ID for later updates
        """
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
            x1 + radius,
            y1
        ]
        return canvas.create_polygon(points, smooth=True, splinesteps=36, **kwargs)



def show_loading_screen_demo():
    """Demo the loading screen."""
    screen = LoadingScreen()
    screen.show()
    
    # Simulate loading steps
    steps = [
        ("Loading configuration...", 20),
        ("Initializing database...", 40),
        ("Loading templates...", 60),
        ("Connecting to data sources...", 80),
        ("Preparing UI components...", 95),
        ("Ready!", 100)
    ]
    
    for step, progress in steps:
        screen.set_status(step, progress)
        time.sleep(0.6)
    
    screen.close()


if __name__ == '__main__':
    show_loading_screen_demo()
