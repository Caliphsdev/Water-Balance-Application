import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import date
from tkcalendar import DateEntry
from pathlib import Path

from utils.report_generator import ReportGenerator
from utils.config_manager import config
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ReportsModule:
    """UI module for generating and exporting reports."""
    def __init__(self, parent):
        self.parent = parent
        self.container = ttk.Frame(parent)
        self.generator = ReportGenerator()

    def load(self):
        self.container.pack(fill='both', expand=True, padx=20, pady=20)
        self._build_ui()

    def _build_ui(self):
        bg_main = config.get_color('bg_main')
        top = ttk.Frame(self.container)
        top.pack(fill='x')

        title = ttk.Label(top, text="🌊 Water Balance Flow Diagram", style='Heading1.TLabel')
        title.pack(anchor='w')

        subtitle = ttk.Label(top, text="Visual representation of water flow with inputs, outputs, and processes", style='Body.TLabel')
        subtitle.pack(anchor='w', pady=(0,15))

        form = ttk.Frame(self.container)
        form.pack(fill='x', pady=(0, 15))

        # Month and Year selectors (like calculations module)
        ttk.Label(form, text="📅 Select Month:").grid(row=0, column=0, sticky='w', padx=(0,10), pady=5)
        
        self.year_var = tk.StringVar(master=form)
        self.month_var = tk.StringVar(master=form)
        
        # Default to current date
        default_year = date.today().year
        default_month = date.today().month
        
        # Year selector
        years = [str(y) for y in range(default_year - 6, default_year + 2)]
        ttk.Label(form, text="Year:").grid(row=0, column=1, sticky='w', padx=(0, 5))
        year_combo = ttk.Combobox(form, textvariable=self.year_var, values=years, width=8, state='readonly')
        year_combo.set(str(default_year))
        year_combo.grid(row=0, column=2, sticky='w', padx=(0, 20))
        
        # Month selector
        import calendar
        month_names = [calendar.month_abbr[m] for m in range(1, 13)]
        ttk.Label(form, text="Month:").grid(row=0, column=3, sticky='w', padx=(0, 5))
        month_combo = ttk.Combobox(form, textvariable=self.month_var, values=month_names, width=8, state='readonly')
        month_combo.set(calendar.month_abbr[default_month])
        month_combo.grid(row=0, column=4, sticky='w')

        # Actions
        actions = ttk.Frame(self.container)
        actions.pack(fill='x', pady=15)

        btn_flow = ttk.Button(actions, text="🌊 View Flow Diagram", command=self._view_flow_diagram, style='Accent.TButton')
        btn_flow.pack(side='left', padx=(0, 10))

        btn_export_flow = ttk.Button(actions, text="💾 Export to PNG", command=self._export_flow_png)
        btn_export_flow.pack(side='left')

        # Output log
        ttk.Label(self.container, text="Status:", style='Heading2.TLabel').pack(anchor='w', pady=(10, 5))
        self.output_text = tk.Text(self.container, height=8, wrap='word')
        self.output_text.pack(fill='both', expand=True, pady=(0,0))
        self.output_text.insert('end', "Ready to generate flow diagram.\nSelect a month and click 'View Flow Diagram' to visualize water balance.\n")
        self.output_text.config(state='disabled')

    def _log(self, message: str):
        self.output_text.config(state='normal')
        self.output_text.insert('end', message + '\n')
        self.output_text.see('end')
        self.output_text.config(state='disabled')

    def _get_dates(self):
        import calendar
        try:
            year = int(self.year_var.get())
            month = list(calendar.month_abbr).index(self.month_var.get())
            # Use first and last day of selected month
            first_day = date(year, month, 1)
            last_day = date(year, month, calendar.monthrange(year, month)[1])
            return first_day, last_day
        except Exception as e:
            messagebox.showerror("Invalid Date", f"Please select a valid month and year: {e}")
            return None, None

    def _view_flow_diagram(self):
        start, end = self._get_dates()
        if not start:
            return
        try:
            self._log("Generating interactive flow diagram...")
            data = self.generator.aggregate_range(start, end)
            # Use comprehensive flow diagram
            fig = self.generator.create_linear_flow_figure(data)
            win = tk.Toplevel(self.parent)
            win.title('Water Balance Flow Diagram - Detailed View')
            # Fullscreen window - maximize
            try:
                win.state('zoomed')  # Works on Windows
            except:
                try:
                    win.attributes('-zoomed', True)  # Works on some Linux window managers
                except:
                    # Fallback: set to screen dimensions
                    win.geometry(f"{win.winfo_screenwidth()}x{win.winfo_screenheight()}+0+0")
            canvas = FigureCanvasTkAgg(fig, master=win)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
            btn_frame = ttk.Frame(win)
            btn_frame.pack(pady=5)
            ttk.Button(btn_frame, text='Close', command=win.destroy).pack(side='left', padx=5)
            
            # Option to export this diagram
            def export_flow():
                filepath = filedialog.asksaveasfilename(
                    defaultextension='.png',
                    filetypes=[('PNG Image', '*.png'), ('All Files', '*.*')],
                    initialfile=f'water_flow_diagram_{start.strftime("%Y%m")}_{end.strftime("%Y%m")}.png'
                )
                if filepath:
                    fig.savefig(filepath, dpi=150, bbox_inches='tight')
                    messagebox.showinfo('Exported', f'Flow diagram saved to:\n{filepath}')
                    self._log(f"Flow diagram exported: {filepath}")
            
            ttk.Button(btn_frame, text='Export as PNG', command=export_flow).pack(side='left', padx=5)
            self._log("Flow diagram displayed successfully")
        except Exception as ex:
            messagebox.showerror('Diagram Error', str(ex))
            self._log(f"Flow diagram error: {ex}")
    
    def _export_flow_png(self):
        """Quick export of flow diagram to PNG"""
        start, end = self._get_dates()
        if not start:
            return
        try:
            self._log("Exporting flow diagram to PNG...")
            data = self.generator.aggregate_range(start, end)
            fig = self.generator.create_linear_flow_figure(data)
            
            filepath = filedialog.asksaveasfilename(
                defaultextension='.png',
                filetypes=[('PNG Image', '*.png'), ('All Files', '*.*')],
                initialfile=f'water_flow_diagram_{start.strftime("%Y%m")}_{end.strftime("%Y%m")}.png'
            )
            
            if filepath:
                fig.savefig(filepath, dpi=150, bbox_inches='tight')
                messagebox.showinfo('Exported', f'Flow diagram saved to:\n{filepath}')
                self._log(f"Flow diagram exported: {filepath}")
        except Exception as ex:
            messagebox.showerror('Export Error', str(ex))
            self._log(f"Export error: {ex}")
