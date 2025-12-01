import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from database.db_manager import DatabaseManager
from utils.backup_manager import BackupManager
from utils.config_manager import config
from utils.alert_manager import alert_manager

class SettingsModule:
    """Settings & Configuration UI"""
    def __init__(self, parent, initial_tab=None):
        self.parent = parent
        self.container = ttk.Frame(parent)
        self.db = DatabaseManager()
        self.backup = BackupManager()
        self.initial_tab = initial_tab
        self.notebook = None

    def load(self):
        self.container.pack(fill='both', expand=True, padx=20, pady=20)
        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(self.container, text="Settings & Configuration", style='Heading1.TLabel')
        title.pack(anchor='w')
        subtitle = ttk.Label(self.container, text="Manage system constants and database backups", style='Body.TLabel')
        subtitle.pack(anchor='w', pady=(0,15))

        self.notebook = ttk.Notebook(self.container)
        self.notebook.pack(fill='both', expand=True)

        self.constants_frame = ttk.Frame(self.notebook)
        self.scenarios_frame = ttk.Frame(self.notebook)
        self.branding_frame = ttk.Frame(self.notebook)
        self.backup_frame = ttk.Frame(self.notebook)
        self.alerts_frame = ttk.Frame(self.notebook)
        self.data_quality_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.branding_frame, text='Branding')
        self.notebook.add(self.constants_frame, text='Constants')
        self.notebook.add(self.scenarios_frame, text='Scenarios')
        self.notebook.add(self.data_quality_frame, text='📊 Data Quality')
        self.notebook.add(self.alerts_frame, text='⚠️ Alerts')
        self.notebook.add(self.backup_frame, text='Backup & Restore')

        self._build_branding_tab()
        self._build_constants_tab()
        self._build_scenarios_tab()
        self._build_data_quality_tab()
        self._build_alerts_tab()
        self._build_backup_tab()
        
        # Switch to initial tab if specified
        if self.initial_tab == 'alerts':
            self.notebook.select(self.alerts_frame)
        elif self.initial_tab == 'data_quality':
            self.notebook.select(self.data_quality_frame)

    def _build_branding_tab(self):
        frame = ttk.LabelFrame(self.branding_frame, text='Report Branding', padding=15)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Company name
        ttk.Label(frame, text='Company Name:').grid(row=0, column=0, sticky='w', pady=5)
        self.company_name_entry = ttk.Entry(frame, width=40)
        self.company_name_entry.insert(0, config.get_company_name())
        self.company_name_entry.grid(row=0, column=1, sticky='w', pady=5)
        ttk.Button(frame, text='Save', command=self._save_company_name).grid(row=0, column=2, padx=5)
        
        # Logo
        ttk.Label(frame, text='Company Logo:').grid(row=1, column=0, sticky='w', pady=5)
        self.logo_path_label = ttk.Label(frame, text=config.get_logo_path() or 'No logo selected', 
                                         foreground='gray', wraplength=300)
        self.logo_path_label.grid(row=1, column=1, sticky='w', pady=5)
        
        logo_btn_frame = ttk.Frame(frame)
        logo_btn_frame.grid(row=2, column=1, sticky='w', pady=5)
        ttk.Button(logo_btn_frame, text='📁 Select Logo', command=self._select_logo).pack(side='left', padx=(0,5))
        ttk.Button(logo_btn_frame, text='❌ Remove Logo', command=self._remove_logo).pack(side='left')
        
        # Logo preview
        self.logo_preview_label = ttk.Label(frame, text='')
        self.logo_preview_label.grid(row=3, column=0, columnspan=3, pady=10)
        self._update_logo_preview()
        
        ttk.Label(frame, text='Recommended: PNG format, 200x80 pixels or similar aspect ratio', 
                 foreground='gray').grid(row=4, column=0, columnspan=3, sticky='w', pady=5)
    
    def _save_company_name(self):
        name = self.company_name_entry.get().strip()
        if name:
            config.set_company_name(name)
            messagebox.showinfo('Saved', f'Company name updated to: {name}')
    
    def _select_logo(self):
        filename = filedialog.askopenfilename(
            title='Select Company Logo',
            filetypes=[('Image files', '*.png *.jpg *.jpeg'), ('All files', '*.*')]
        )
        if filename:
            # Copy to branding folder
            import shutil
            from pathlib import Path
            dest_dir = Path(__file__).parent.parent.parent / 'config' / 'branding'
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / Path(filename).name
            shutil.copy2(filename, dest_file)
            
            config.set_logo_path(str(dest_file))
            self.logo_path_label.config(text=str(dest_file))
            self._update_logo_preview()
            messagebox.showinfo('Logo Set', f'Logo updated: {dest_file.name}')
    
    def _remove_logo(self):
        config.set_logo_path('')
        self.logo_path_label.config(text='No logo selected')
        self._update_logo_preview()
        messagebox.showinfo('Logo Removed', 'Logo has been removed from reports.')
    
    def _update_logo_preview(self):
        logo_path = config.get_logo_path()
        if logo_path and Path(logo_path).exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path)
                img.thumbnail((150, 60), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.logo_preview_label.config(image=photo, text='')
                self.logo_preview_label.image = photo  # Keep reference
            except Exception as ex:
                self.logo_preview_label.config(text=f'Preview unavailable: {ex}')
        else:
            self.logo_preview_label.config(text='No preview', image='')

    def _build_constants_tab(self):
        # Category filter
        filter_frame = ttk.Frame(self.constants_frame)
        filter_frame.pack(fill='x', pady=(0,10))
        ttk.Label(filter_frame, text='Category:').pack(side='left', padx=(0,5))
        self.category_filter = ttk.Combobox(filter_frame, values=['All', 'Plant', 'Evaporation', 'Operating'], state='readonly', width=15)
        self.category_filter.set('All')
        self.category_filter.pack(side='left')
        self.category_filter.bind('<<ComboboxSelected>>', lambda e: self._load_constants())

        top = ttk.Frame(self.constants_frame)
        top.pack(fill='both', expand=True)

        cols = ('Category', 'Key', 'Value', 'Unit', 'Range', 'Description')
        self.tree = ttk.Treeview(top, columns=cols, show='headings', height=10)
        widths = {'Category': 90, 'Key': 140, 'Value': 80, 'Unit': 80, 'Range': 100, 'Description': 180}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths[c], anchor='w')
        self.tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(top, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Load constants
        self._load_constants()

        # Edit form
        form = ttk.LabelFrame(self.constants_frame, text='Edit Selected Constant', padding=10)
        form.pack(fill='x', pady=10)
        
        ttk.Label(form, text='Key:').grid(row=0, column=0, sticky='w', padx=5)
        self.selected_key = ttk.Label(form, text='—', font=('TkDefaultFont', 9, 'bold'))
        self.selected_key.grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(form, text='Description:').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.selected_desc = ttk.Label(form, text='—', wraplength=400)
        self.selected_desc.grid(row=1, column=1, columnspan=3, sticky='w', padx=5)
        
        ttk.Label(form, text='New Value:').grid(row=2, column=0, sticky='w', padx=5)
        self.new_value = ttk.Entry(form, width=15)
        self.new_value.grid(row=2, column=1, sticky='w', padx=5)
        
        self.value_range_label = ttk.Label(form, text='', foreground='gray')
        self.value_range_label.grid(row=2, column=2, sticky='w', padx=5)
        
        update_btn = ttk.Button(form, text='Update Constant', command=self._update_constant)
        update_btn.grid(row=2, column=3, padx=10)
        
        # Export/Import actions
        actions_frame = ttk.Frame(self.constants_frame)
        actions_frame.pack(fill='x', pady=5)
        
        ttk.Button(actions_frame, text='📋 Export Constants to Excel', command=self._export_constants).pack(side='left', padx=5)
        ttk.Button(actions_frame, text='📜 View Change History', command=self._view_history).pack(side='left', padx=5)

        def on_select(event):
            sel = self.tree.selection()
            if not sel:
                return
            item = self.tree.item(sel[0])
            cat, key, value, unit, range_str, desc = item['values']
            self.selected_key.config(text=key)
            self.selected_desc.config(text=desc if desc else 'No description')
            self.value_range_label.config(text=f'({range_str})' if range_str != '—' else '')
            self.new_value.delete(0,'end')
            self.new_value.insert(0,str(value))
            # Store current metadata for validation
            self.current_constant = self._get_constant_metadata(key)
        self.tree.bind('<<TreeviewSelect>>', on_select)
        
        self.current_constant = None

    def _get_constant_metadata(self, key):
        """Get full constant metadata including validation ranges"""
        result = self.db.execute_query(
            'SELECT * FROM system_constants WHERE constant_key = ?', (key,)
        )
        return result[0] if result else None

    def _load_constants(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # Get category filter
        cat_filter = self.category_filter.get() if hasattr(self, 'category_filter') else 'All'
        
        # Load all constants with metadata
        query = 'SELECT constant_key, constant_value, unit, category, description, min_value, max_value FROM system_constants ORDER BY category, constant_key'
        results = self.db.execute_query(query)
        
        for row in results:
            key = row['constant_key']
            value = row['constant_value']
            unit = row.get('unit') or '—'
            category = row.get('category') or 'Other'
            desc = row.get('description') or ''
            min_val = row.get('min_value')
            max_val = row.get('max_value')
            
            # Apply category filter
            if cat_filter != 'All' and category != cat_filter:
                continue
            
            # Format range
            if min_val is not None and max_val is not None:
                range_str = f'{min_val} - {max_val}'
            else:
                range_str = '—'
            
            self.tree.insert('', 'end', values=(category, key, value, unit, range_str, desc))

        # Ensure EVAP_PAN_COEFF appears under Evaporation category filter mapping
        # Provide shortcut selection button if present
        if any(r['constant_key'] == 'EVAP_PAN_COEFF' for r in results):
            if not hasattr(self, 'evap_coeff_button'):
                btn_frame = ttk.Frame(self.constants_frame)
                btn_frame.pack(fill='x', pady=(0,5))
                self.evap_coeff_button = ttk.Button(btn_frame, text='Edit Evaporation Pan Coefficient', command=lambda: self._select_constant_row('EVAP_PAN_COEFF'))
                self.evap_coeff_button.pack(anchor='w')

    def _select_constant_row(self, key: str):
        for item in self.tree.get_children():
            vals = self.tree.item(item)['values']
            if vals and vals[1] == key:
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.event_generate('<<TreeviewSelect>>')
                break

    def _update_constant(self):
        key = self.selected_key.cget('text')
        if key == '—':
            messagebox.showwarning('No Selection','Please select a constant to update.')
            return
        
        try:
            value = float(self.new_value.get())
        except ValueError:
            messagebox.showerror('Invalid Value','Please enter a numeric value.')
            return
        
        # Validate against min/max if available
        if self.current_constant:
            min_val = self.current_constant.get('min_value')
            max_val = self.current_constant.get('max_value')
            unit = self.current_constant.get('unit') or ''
            
            if min_val is not None and value < min_val:
                messagebox.showerror('Validation Error', 
                    f'Value {value} is below minimum {min_val} {unit}.\nPlease enter a value between {min_val} and {max_val}.')
                return
            
            if max_val is not None and value > max_val:
                messagebox.showerror('Validation Error',
                    f'Value {value} exceeds maximum {max_val} {unit}.\nPlease enter a value between {min_val} and {max_val}.')
                return
        
        # Update with confirmation for critical constants
        critical = ['TSF_RETURN_RATE', 'MINING_WATER_RATE', 'SLURRY_DENSITY']
        if key in critical:
            confirm = messagebox.askyesno('Confirm Change',
                f'You are changing a critical constant: {key}\n\n'
                f'Old value: {self.current_constant["constant_value"]}\n'
                f'New value: {value}\n\n'
                f'This will affect all future calculations. Continue?')
            if not confirm:
                return
        
        self.db.update_constant(key, value, user='user')
        self._load_constants()
        messagebox.showinfo('Updated', f'Constant {key} updated to {value}.')

    def _export_constants(self):
        """Export constants to Excel file"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font
            from datetime import datetime
            
            filename = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel files', '*.xlsx')],
                initialfile=f'constants_export_{datetime.now().strftime("%Y%m%d")}.xlsx'
            )
            if not filename:
                return
            
            wb = Workbook()
            ws = wb.active
            ws.title = 'Constants'
            
            # Headers
            headers = ['Category', 'Key', 'Value', 'Unit', 'Min', 'Max', 'Description']
            ws.append(headers)
            for cell in ws[1]:
                cell.font = Font(bold=True)
            
            # Data
            query = 'SELECT category, constant_key, constant_value, unit, min_value, max_value, description FROM system_constants ORDER BY category, constant_key'
            results = self.db.execute_query(query)
            for row in results:
                ws.append([
                    row.get('category') or '',
                    row['constant_key'],
                    row['constant_value'],
                    row.get('unit') or '',
                    row.get('min_value') or '',
                    row.get('max_value') or '',
                    row.get('description') or ''
                ])
            
            wb.save(filename)
            messagebox.showinfo('Export Complete', f'Constants exported to:\n{filename}')
        except Exception as ex:
            messagebox.showerror('Export Error', str(ex))

    def _view_history(self):
        """Show audit log of constant changes"""
        history_window = tk.Toplevel(self.parent)
        history_window.title('Constants Change History')
        history_window.geometry('800x400')
        
        frame = ttk.Frame(history_window, padding=10)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text='Recent Changes', font=('TkDefaultFont', 10, 'bold')).pack(anchor='w')
        
        cols = ('Timestamp', 'Constant', 'Old Value', 'New Value', 'User')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=15)
        widths = {'Timestamp': 150, 'Constant': 180, 'Old Value': 100, 'New Value': 100, 'User': 80}
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=widths[c])
        tree.pack(fill='both', expand=True, pady=5)
        
        # Load audit log
        try:
            import json
            logs = self.db.execute_query(
                "SELECT * FROM audit_log WHERE table_name = 'system_constants' ORDER BY changed_at DESC LIMIT 50"
            )
            for log in logs:
                timestamp = log['changed_at']
                old_vals = json.loads(log['old_values']) if log['old_values'] else {}
                new_vals = json.loads(log['new_values']) if log['new_values'] else {}
                
                for key in new_vals:
                    old_val = old_vals.get(key, '—')
                    new_val = new_vals[key]
                    tree.insert('', 'end', values=(timestamp, key, old_val, new_val, log['changed_by']))
        except Exception as ex:
            ttk.Label(frame, text=f'Error loading history: {ex}').pack()
        
        ttk.Button(frame, text='Close', command=history_window.destroy).pack(pady=5)

    # ============ Alerts Tab ============
    def _build_alerts_tab(self):
        """Build the alerts dashboard and management UI"""
        # Summary section
        summary_frame = ttk.LabelFrame(self.alerts_frame, text='Alert Summary', padding=10)
        summary_frame.pack(fill='x', padx=10, pady=10)
        
        # Get current alert summary
        summary = alert_manager.get_alert_summary()
        
        # Create summary labels with colors
        sum_grid = ttk.Frame(summary_frame)
        sum_grid.pack(fill='x')
        
        # Critical alerts
        critical_frame = ttk.Frame(sum_grid)
        critical_frame.pack(side='left', padx=15)
        tk.Label(critical_frame, text='🚨 Critical', font=('TkDefaultFont', 10, 'bold'), 
                fg='#dc3545').pack()
        self.critical_count_label = tk.Label(critical_frame, text=str(summary['critical']), 
                                            font=('TkDefaultFont', 24, 'bold'), fg='#dc3545')
        self.critical_count_label.pack()
        
        # Warning alerts
        warning_frame = ttk.Frame(sum_grid)
        warning_frame.pack(side='left', padx=15)
        tk.Label(warning_frame, text='⚠️ Warning', font=('TkDefaultFont', 10, 'bold'), 
                fg='#ffc107').pack()
        self.warning_count_label = tk.Label(warning_frame, text=str(summary['warning']), 
                                           font=('TkDefaultFont', 24, 'bold'), fg='#ffc107')
        self.warning_count_label.pack()
        
        # Info alerts
        info_frame = ttk.Frame(sum_grid)
        info_frame.pack(side='left', padx=15)
        tk.Label(info_frame, text='ℹ️ Info', font=('TkDefaultFont', 10, 'bold'), 
                fg='#17a2b8').pack()
        self.info_count_label = tk.Label(info_frame, text=str(summary['info']), 
                                         font=('TkDefaultFont', 24, 'bold'), fg='#17a2b8')
        self.info_count_label.pack()
        
        # Active alerts list
        alerts_list_frame = ttk.LabelFrame(self.alerts_frame, text='Active Alerts', padding=10)
        alerts_list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Action buttons
        alert_actions = ttk.Frame(alerts_list_frame)
        alert_actions.pack(fill='x', pady=(0,10))
        ttk.Button(alert_actions, text='🔄 Refresh', command=self._refresh_alerts).pack(side='left', padx=5)
        ttk.Button(alert_actions, text='✅ Acknowledge Selected', command=self._acknowledge_alert).pack(side='left', padx=5)
        ttk.Button(alert_actions, text='✔️ Resolve Selected', command=self._resolve_alert).pack(side='left', padx=5)
        ttk.Button(alert_actions, text='🗑️ Clear All Resolved', command=self._clear_resolved).pack(side='left', padx=5)
        
        # Alerts table
        columns = ('Severity', 'Title', 'Message', 'Triggered', 'Status')
        self.alerts_tree = ttk.Treeview(alerts_list_frame, columns=columns, show='headings', height=8)
        
        widths = {'Severity': 80, 'Title': 180, 'Message': 300, 'Triggered': 150, 'Status': 100}
        for col in columns:
            self.alerts_tree.heading(col, text=col)
            self.alerts_tree.column(col, width=widths[col], anchor='w')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(alerts_list_frame, orient='vertical', command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=scrollbar.set)
        
        self.alerts_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Alert Rules section
        rules_frame = ttk.LabelFrame(self.alerts_frame, text='Alert Rules Configuration', padding=10)
        rules_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Rules action buttons
        rules_actions = ttk.Frame(rules_frame)
        rules_actions.pack(fill='x', pady=(0,10))
        ttk.Button(rules_actions, text='➕ Add Rule', command=self._add_alert_rule).pack(side='left', padx=5)
        ttk.Button(rules_actions, text='✏️ Edit Selected', command=self._edit_alert_rule).pack(side='left', padx=5)
        ttk.Button(rules_actions, text='🔄 Toggle Enable/Disable', command=self._toggle_rule).pack(side='left', padx=5)
        
        # Rules table
        rule_columns = ('Enabled', 'Name', 'Severity', 'Metric', 'Condition', 'Threshold', 'Notify')
        self.rules_tree = ttk.Treeview(rules_frame, columns=rule_columns, show='headings', height=8)
        
        rule_widths = {'Enabled': 70, 'Name': 180, 'Severity': 80, 'Metric': 150, 
                      'Condition': 80, 'Threshold': 100, 'Notify': 80}
        for col in rule_columns:
            self.rules_tree.heading(col, text=col)
            self.rules_tree.column(col, width=rule_widths[col], anchor='w')
        
        # Rules scrollbar
        rules_scrollbar = ttk.Scrollbar(rules_frame, orient='vertical', command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=rules_scrollbar.set)
        
        self.rules_tree.pack(side='left', fill='both', expand=True)
        rules_scrollbar.pack(side='right', fill='y')
        
        # Load data
        self._refresh_alerts()
        self._load_alert_rules()

    def _refresh_alerts(self):
        """Refresh the alerts list and summary"""
        # Update summary
        summary = alert_manager.get_alert_summary()
        self.critical_count_label.config(text=str(summary['critical']))
        self.warning_count_label.config(text=str(summary['warning']))
        self.info_count_label.config(text=str(summary['info']))
        
        # Clear and reload alerts table
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)
        
        # Load active alerts
        alerts = alert_manager.get_active_alerts(limit=50)
        for alert in alerts:
            severity_icon = {'critical': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}.get(alert['severity'], '•')
            status = 'Acknowledged' if alert.get('acknowledged_at') else 'Active'
            
            values = (
                f"{severity_icon} {alert['severity'].upper()}",
                alert['title'],
                alert['message'][:80] + '...' if len(alert['message']) > 80 else alert['message'],
                alert['triggered_at'],
                status
            )
            
            # Color code by severity
            tag = f"severity_{alert['severity']}"
            self.alerts_tree.insert('', 'end', values=values, iid=str(alert['alert_id']), tags=(tag,))
        
        # Configure tags for color coding
        self.alerts_tree.tag_configure('severity_critical', foreground='#dc3545')
        self.alerts_tree.tag_configure('severity_warning', foreground='#ffc107')
        self.alerts_tree.tag_configure('severity_info', foreground='#17a2b8')

    def _load_alert_rules(self):
        """Load alert rules into the rules table"""
        # Clear existing
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # Load rules
        rules = alert_manager.load_rules(include_disabled=True)
        for rule in rules:
            enabled = '✅' if rule.active else '❌'
            notify = '🔔' if rule.show_popup else '—'
            
            values = (
                enabled,
                rule.rule_name,
                rule.severity.upper(),
                rule.metric_name,
                rule.condition_operator,
                str(rule.threshold_value),
                notify
            )
            
            self.rules_tree.insert('', 'end', values=values, iid=str(rule.rule_id))

    def _acknowledge_alert(self):
        """Acknowledge the selected alert"""
        selection = self.alerts_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select an alert to acknowledge.')
            return
        
        alert_id = int(selection[0])
        alert_manager.acknowledge_alert(alert_id)
        self._refresh_alerts()
        self._trigger_badge_update()
        messagebox.showinfo('Alert Acknowledged', 'Alert has been acknowledged.')

    def _resolve_alert(self):
        """Manually resolve the selected alert"""
        selection = self.alerts_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select an alert to resolve.')
            return
        
        confirm = messagebox.askyesno('Confirm Resolution', 
                                     'Mark this alert as resolved? This cannot be undone.')
        if not confirm:
            return
        
        alert_id = int(selection[0])
        alert_manager.resolve_alert(alert_id)
        self._refresh_alerts()
        self._trigger_badge_update()
        messagebox.showinfo('Alert Resolved', 'Alert has been resolved.')

    def _clear_resolved(self):
        """Clear all resolved alerts from the database"""
        confirm = messagebox.askyesno('Confirm Clear', 
                                     'Clear all resolved alerts from history? This cannot be undone.')
        if not confirm:
            return
        
        # Delete resolved alerts
        query = "DELETE FROM alerts WHERE status = 'resolved'"
        self.db.execute(query)
        self._refresh_alerts()
        self._trigger_badge_update()
        messagebox.showinfo('Cleared', 'All resolved alerts have been removed from history.')
    
    def _trigger_badge_update(self):
        """Trigger main window badge update by posting a virtual event"""
        try:
            # Post a virtual event that the main window can listen for
            self.parent.event_generate('<<AlertsChanged>>')
        except:
            pass  # Silently fail if event generation doesn't work

    def _toggle_rule(self):
        """Toggle the selected rule's enabled status"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select a rule to toggle.')
            return
        
        rule_id = int(selection[0])
        
        # Get current status
        query = "SELECT active FROM alert_rules WHERE rule_id = ?"
        result = self.db.fetch_one(query, (rule_id,))
        current_status = result[0]
        new_status = 0 if current_status else 1
        
        # Update
        update_query = "UPDATE alert_rules SET active = ? WHERE rule_id = ?"
        self.db.execute(update_query, (new_status, rule_id))
        
        # Reload rules in alert manager
        alert_manager.load_rules()
        
        self._load_alert_rules()
        status_text = 'enabled' if new_status else 'disabled'
        messagebox.showinfo('Rule Updated', f'Alert rule has been {status_text}.')

    def _add_alert_rule(self):
        """Open dialog to add a new alert rule"""
        messagebox.showinfo('Coming Soon', 'Rule creation dialog will be added in the next update.')

    def _edit_alert_rule(self):
        """Open dialog to edit the selected rule"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select a rule to edit.')
            return
        
        messagebox.showinfo('Coming Soon', 'Rule editing dialog will be added in the next update.')

    def _build_backup_tab(self):
        frame = ttk.Frame(self.backup_frame)
        frame.pack(fill='both', expand=True, pady=10)

        btn_backup = ttk.Button(frame, text='Create Backup', command=self._create_backup)
        btn_backup.pack(anchor='w')

        btn_refresh = ttk.Button(frame, text='Refresh List', command=self._load_backups)
        btn_refresh.pack(anchor='w', pady=(5,0))

        self.backups_list = tk.Listbox(frame, height=10)
        self.backups_list.pack(fill='x', pady=10)

        btn_restore = ttk.Button(frame, text='Restore Selected', command=self._restore_selected)
        btn_restore.pack(anchor='w', pady=(0,10))

        self._load_backups()

    # ============ Scenarios Tab ============
    def _build_scenarios_tab(self):
        frame = ttk.LabelFrame(self.scenarios_frame, text='Calculation Scenarios', padding=10)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        actions = ttk.Frame(frame)
        actions.pack(fill='x', pady=(0,10))
        ttk.Button(actions, text='➕ Create Scenario', command=self._create_scenario).pack(side='left')
        ttk.Button(actions, text='✅ Apply Selected', command=self._apply_selected_scenario).pack(side='left', padx=5)
        ttk.Button(actions, text='🗑️ Delete Selected', command=self._delete_selected_scenario).pack(side='left', padx=5)
        ttk.Button(actions, text='✳️ Clear Active', command=self._clear_active_scenario).pack(side='left', padx=5)
        ttk.Button(actions, text='🔍 View Diff', command=self._view_selected_diff).pack(side='left', padx=5)

        # Comparison controls
        cmp_frame = ttk.Frame(frame)
        cmp_frame.pack(fill='x', pady=(0,5))
        ttk.Label(cmp_frame, text='Compare Scenario A (selected) with:').pack(side='left')
        self.compare_target = ttk.Combobox(cmp_frame, state='readonly', width=18)
        self.compare_target.pack(side='left', padx=5)
        ttk.Button(cmp_frame, text='📄 Comparison PDF', command=self._generate_comparison_pdf).pack(side='left')

        self.active_scenario_label = ttk.Label(frame, text='Active: None', foreground='gray')
        self.active_scenario_label.pack(anchor='w', pady=(0,5))

        cols = ('Name','Description','Created','Constants')
        self.scenario_tree = ttk.Treeview(frame, columns=cols, show='headings', height=10)
        widths = {'Name':160,'Description':280,'Created':140,'Constants':90}
        for c in cols:
            self.scenario_tree.heading(c, text=c)
            self.scenario_tree.column(c, width=widths[c], anchor='w')
        self.scenario_tree.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.scenario_tree.yview)
        self.scenario_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self._load_scenarios()
        self._refresh_compare_targets()

    def _load_scenarios(self):
        for i in self.scenario_tree.get_children():
            self.scenario_tree.delete(i)
        scenarios = self.db.list_scenarios()
        for sc in scenarios:
            const_count = len(self.db.get_scenario_constants(sc['scenario_id']))
            self.scenario_tree.insert('', 'end', iid=str(sc['scenario_id']), values=(sc['name'], sc.get('description',''), sc.get('created_at',''), const_count))
        # Active label
        active_id = config.get_active_scenario_id()
        if active_id:
            active = next((s for s in scenarios if s['scenario_id']==active_id), None)
            if active:
                self.active_scenario_label.config(text=f"Active: {active['name']} (ID {active_id})", foreground='green')
            else:
                self.active_scenario_label.config(text='Active: None', foreground='gray')
        else:
            self.active_scenario_label.config(text='Active: None', foreground='gray')
        self._refresh_compare_targets()

    def _refresh_compare_targets(self):
        scenarios = self.db.list_scenarios()
        names = ['(Base Constants)'] + [f"{s['scenario_id']}: {s['name']}" for s in scenarios]
        self.compare_target['values'] = names
        if not self.compare_target.get():
            self.compare_target.set('(Base Constants)')

    def _create_scenario(self):
        win = tk.Toplevel(self.parent); win.title('Create Scenario'); win.geometry('400x220')
        ttk.Label(win, text='Scenario Name:').pack(anchor='w', padx=10, pady=(10,2))
        name_entry = ttk.Entry(win); name_entry.pack(fill='x', padx=10)
        ttk.Label(win, text='Description:').pack(anchor='w', padx=10, pady=(10,2))
        desc_entry = ttk.Entry(win); desc_entry.pack(fill='x', padx=10)
        status_label = ttk.Label(win, text='', foreground='gray'); status_label.pack(anchor='w', padx=10, pady=5)

        def do_create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning('Validation','Name required.'); return
            try:
                sid = self.db.create_scenario(name, desc_entry.get().strip())
                status_label.config(text=f'Scenario created (ID {sid})', foreground='green')
                self._load_scenarios()
            except Exception as ex:
                messagebox.showerror('Create Error', str(ex))
        ttk.Button(win, text='Create', command=do_create).pack(pady=10)
        ttk.Button(win, text='Close', command=win.destroy).pack()

    def _apply_selected_scenario(self):
        sel = self.scenario_tree.selection()
        if not sel:
            messagebox.showwarning('No Selection','Select a scenario first.'); return
        scenario_id = int(sel[0])
        config.set_active_scenario(scenario_id)
        self._load_scenarios()
        messagebox.showinfo('Scenario Applied','Active scenario set. Calculations now use these constants.')

    def _clear_active_scenario(self):
        config.clear_active_scenario(); self._load_scenarios()
        messagebox.showinfo('Cleared','Active scenario cleared.')

    def _delete_selected_scenario(self):
        sel = self.scenario_tree.selection()
        if not sel:
            messagebox.showwarning('No Selection','Select a scenario first.'); return
        scenario_id = int(sel[0])
        confirm = messagebox.askyesno('Confirm Delete','Delete selected scenario? This cannot be undone.')
        if not confirm: return
        self.db.delete_scenario(scenario_id)
        self._load_scenarios()
        messagebox.showinfo('Deleted','Scenario removed.')

    def _view_selected_diff(self):
        sel = self.scenario_tree.selection()
        if not sel:
            messagebox.showwarning('No Selection','Select a scenario first.'); return
        scenario_id = int(sel[0])
        diffs = self.db.get_scenario_diff(scenario_id)
        win = tk.Toplevel(self.parent); win.title('Scenario Differences'); win.geometry('700x400')
        cols = ('Key','Base Value','Scenario Value','Delta','% Change')
        tree = ttk.Treeview(win, columns=cols, show='headings', height=15)
        widths = {'Key':170,'Base Value':110,'Scenario Value':120,'Delta':90,'% Change':100}
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=widths[c], anchor='w')
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        for d in diffs:
            pc = f"{d['percent_change']:.2f}%" if d['percent_change'] is not None else '—'
            tree.insert('', 'end', values=(d['constant_key'], d['base_value'], d['scenario_value'], d['delta'], pc))
        if not diffs:
            ttk.Label(win, text='No differences detected.', foreground='gray').pack(pady=5)
        ttk.Button(win, text='Close', command=win.destroy).pack(pady=5)

    def _generate_comparison_pdf(self):
        sel = self.scenario_tree.selection()
        if not sel:
            messagebox.showwarning('No Selection','Select scenario A first.'); return
        scenario_a = int(sel[0])
        # Parse target
        val = self.compare_target.get()
        scenario_b = None
        if val != '(Base Constants)' and ':' in val:
            scenario_b = int(val.split(':')[0])
        from datetime import date
        from utils.report_generator import ReportGenerator
        rg = ReportGenerator()
        start = date.today().replace(day=1)
        end = start
        try:
            path = rg.generate_scenario_comparison_pdf(scenario_a, start, end, scenario_b)
            messagebox.showinfo('Comparison PDF Generated', f'Report saved to:\n{path}')
        except Exception as ex:
            messagebox.showerror('Comparison Error', str(ex))

    def _create_backup(self):
        path = self.backup.create_backup()
        messagebox.showinfo('Backup Created', f'Backup saved: {path}')
        self._load_backups()

    def _load_backups(self):
        self.backups_list.delete(0,'end')
        for f in self.backup.list_backups():
            self.backups_list.insert('end', f.name)

    def _restore_selected(self):
        sel = self.backups_list.curselection()
        if not sel:
            messagebox.showwarning('No Selection','Select a backup first.')
            return
        name = self.backups_list.get(sel[0])
        backup_path = self.backup.backup_dir / name
        confirm = messagebox.askyesno('Confirm Restore', f'Restore backup {name}? This will overwrite current database.')
        if not confirm:
            return
        self.backup.restore_backup(backup_path)
        messagebox.showinfo('Restored', f'Restored from {name}.')
        # Reload constants if open
        self._load_constants()
    
    def _build_data_quality_tab(self):
        """Build the data quality management tab"""
        from ui.data_quality_manager import DataQualityManager
        
        # Create the data quality manager directly in the frame
        manager = DataQualityManager(self.data_quality_frame)
        manager.pack(fill='both', expand=True)
