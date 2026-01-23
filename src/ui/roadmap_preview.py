"""
Roadmap Preview Tab - "Under Development" Features
Shows upcoming features as a selling point without disrupting current functionality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Dict, List

from utils.config_manager import config
from utils.app_logger import logger
from ui.mouse_wheel_support import enable_canvas_mousewheel


class RoadmapPreviewTab:
    """
    Display upcoming features from the 2026 roadmap as a professional preview.
    
    This tab:
    - Shows features organized by Quarter (Q2, Q3, Q4 2026)
    - Displays feature tiers (Standard, Professional, Enterprise)
    - Provides "Coming Soon" status indicators
    - Acts as a sales tool to show product roadmap
    - Does NOT implement any actual features (preview only)
    
    Data source: FUTURE_FEATURES_ROADMAP_2026.md in docs/
    """
    
    def __init__(self, parent):
        """
        Initialize the roadmap preview tab.
        
        Args:
            parent: Parent tkinter widget (typically a ttk.Notebook tab)
        """
        self.parent = parent
        self.container = tk.Frame(parent, bg='#f5f6f7')
        self.features_data = self._load_features_data()
        
    def load(self):
        """Load and display the roadmap preview UI."""
        self.container.pack(fill='both', expand=True)
        self._build_ui()
        
    def _build_ui(self):
        """Build the roadmap preview interface with modern card layout."""
        # Create scrollable container
        scroll_container = tk.Frame(self.container, bg='#f5f6f7')
        scroll_container.pack(fill='both', expand=True)
        
        # Canvas and scrollbar
        canvas = tk.Canvas(scroll_container, bg='#f5f6f7', highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f6f7')
        
        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mousewheel scrolling
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        scrollbar.pack(side='right', fill='y', padx=0, pady=20)
        
        container = scrollable_frame
        
        # Header card
        self._build_header(container)
        
        # Timeline preview
        self._build_timeline(container)
        
        # Feature cards by quarter
        self._build_q2_features(container)
        self._build_q3_features(container)
        self._build_q4_features(container)
        
        # Call to action footer
        self._build_footer(container)
        
    def _build_header(self, parent):
        """Build the header section with title and description."""
        header_card = tk.Frame(parent, bg='white', relief=tk.FLAT, bd=1, 
                              highlightbackground='#3498db', highlightthickness=2)
        header_card.pack(fill='x', pady=(0, 20))
        
        inner = tk.Frame(header_card, bg='white')
        inner.pack(fill='x', padx=30, pady=25)
        
        # Title with gradient-style icon
        title_frame = tk.Frame(inner, bg='white')
        title_frame.pack(anchor='w')
        
        tk.Label(title_frame, text='🚀', font=('Segoe UI', 32), bg='white').pack(side='left', padx=(0, 15))
        
        title_col = tk.Frame(title_frame, bg='white')
        title_col.pack(side='left', fill='x', expand=True)
        
        tk.Label(title_col, text='Future Features Roadmap', 
                font=('Segoe UI', 24, 'bold'), bg='white', fg='#2c3e50').pack(anchor='w')
        
        tk.Label(title_col, text='Transform from Calculator to Platform • Q2-Q4 2026', 
                font=('Segoe UI', 12), bg='white', fg='#3498db').pack(anchor='w', pady=(5, 0))
        
        # Description
        desc_frame = tk.Frame(inner, bg='#f0f8ff', relief=tk.FLAT, bd=1, 
                             highlightbackground='#3498db', highlightthickness=1)
        desc_frame.pack(fill='x', pady=(15, 0))
        
        desc_inner = tk.Frame(desc_frame, bg='#f0f8ff')
        desc_inner.pack(fill='x', padx=20, pady=15)
        
        tk.Label(desc_inner, 
                text="📋 Below are exciting features currently under development. These enhancements will "
                     "elevate the Water Balance Application from a powerful calculator to a comprehensive "
                     "environmental management platform.",
                font=('Segoe UI', 10), bg='#f0f8ff', fg='#2c3e50', 
                wraplength=800, justify='left').pack(anchor='w')
        
        # Status banner
        status_frame = tk.Frame(inner, bg='#fff3cd', relief=tk.FLAT, bd=1, 
                               highlightbackground='#ffc107', highlightthickness=1)
        status_frame.pack(fill='x', pady=(15, 0))
        
        status_inner = tk.Frame(status_frame, bg='#fff3cd')
        status_inner.pack(fill='x', padx=20, pady=12)
        
        tk.Label(status_inner, text='⏳', font=('Segoe UI', 16), bg='#fff3cd').pack(side='left', padx=(0, 10))
        tk.Label(status_inner, 
                text="PREVIEW MODE: Features shown below are in active development and not yet available in this version.",
                font=('Segoe UI', 10, 'bold'), bg='#fff3cd', fg='#856404').pack(side='left')
        
    def _build_timeline(self, parent):
        """Build visual timeline showing quarterly rollout."""
        timeline_card = tk.Frame(parent, bg='white', relief=tk.FLAT, bd=1, 
                                highlightbackground='#c5d3e6', highlightthickness=1)
        timeline_card.pack(fill='x', pady=(0, 20))
        
        inner = tk.Frame(timeline_card, bg='white')
        inner.pack(fill='x', padx=30, pady=20)
        
        tk.Label(inner, text='📅 2026 Release Timeline', 
                font=('Segoe UI', 14, 'bold'), bg='white', fg='#2c3e50').pack(anchor='w', pady=(0, 15))
        
        # Timeline visual (horizontal bars)
        timeline_visual = tk.Frame(inner, bg='white')
        timeline_visual.pack(fill='x', pady=(0, 0))
        
        quarters = [
            {'q': 'Q2 2026', 'label': 'Compliance & Alerts', 'color': '#28a745', 'features': 'Compliance Reporting • Alert System'},
            {'q': 'Q3 2026', 'label': 'Sustainability & Analytics', 'color': '#3498db', 'features': 'Air Quality • Advanced Analytics • Exports'},
            {'q': 'Q4 2026', 'label': 'Enterprise Features', 'color': '#6c3fb5', 'features': 'Multi-Site • API • Predictions • Custom Reports'},
        ]
        
        for quarter in quarters:
            q_frame = tk.Frame(timeline_visual, bg='white')
            q_frame.pack(fill='x', pady=8)
            
            # Quarter label
            tk.Label(q_frame, text=quarter['q'], font=('Segoe UI', 10, 'bold'), 
                    bg='white', fg='#2c3e50', width=10, anchor='w').pack(side='left', padx=(0, 10))
            
            # Progress bar
            bar_container = tk.Frame(q_frame, bg='#e8eef5', height=30, relief=tk.FLAT)
            bar_container.pack(side='left', fill='x', expand=True, padx=(0, 10))
            bar_container.pack_propagate(False)
            
            bar_fill = tk.Frame(bar_container, bg=quarter['color'], height=30)
            bar_fill.pack(side='left', fill='both', expand=True)
            
            tk.Label(bar_fill, text=quarter['label'], font=('Segoe UI', 10, 'bold'), 
                    bg=quarter['color'], fg='white', padx=15).pack(side='left', fill='y')
            
            # Feature list
            tk.Label(q_frame, text=quarter['features'], font=('Segoe UI', 9), 
                    bg='white', fg='#7f8c8d', anchor='w', width=60).pack(side='left')
        
    def _build_q2_features(self, parent):
        """Build Q2 2026 features (Compliance & Alerts)."""
        self._build_quarter_card(
            parent,
            quarter='Q2 2026 • May Launch',
            title='Compliance & Alerting',
            color='#28a745',
            features=[
                {
                    'name': 'Compliance Reporting System',
                    'tier': 'Professional',
                    'desc': 'Automated generation of regulatory compliance reports (DWS, NEMA) with audit trails. '
                           'Pre-built templates ensure all required data points are captured and formatted correctly.',
                    'benefits': [
                        'Save 10+ hours/month on manual report creation',
                        'Zero compliance violations due to automated checks',
                        'One-click PDF export for regulatory submissions'
                    ]
                },
                {
                    'name': 'Intelligent Alert System',
                    'tier': 'Standard',
                    'desc': 'Real-time monitoring of critical thresholds with customizable alerts via email, SMS, and in-app. '
                           'Smart escalation rules ensure the right people are notified at the right time.',
                    'benefits': [
                        'Prevent storage overflows with 24/7 monitoring',
                        'Reduce emergency response time by 80%',
                        'Configurable alert rules per facility'
                    ]
                }
            ]
        )
        
    def _build_q3_features(self, parent):
        """Build Q3 2026 features (Sustainability & Analytics)."""
        self._build_quarter_card(
            parent,
            quarter='Q3 2026 • August Launch',
            title='Sustainability & Advanced Analytics',
            color='#3498db',
            features=[
                {
                    'name': 'Air Quality Monitoring',
                    'tier': 'Professional',
                    'desc': 'Track dust suppression effectiveness and PM10/PM2.5 levels. Correlate water usage with '
                           'air quality metrics to optimize dust control operations.',
                    'benefits': [
                        'Meet air quality compliance standards',
                        'Optimize dust suppression water usage',
                        'Trend analysis with historical data'
                    ]
                },
                {
                    'name': 'Advanced Analytics Engine',
                    'tier': 'Professional',
                    'desc': 'Deep-dive analytics with trend forecasting, seasonal patterns, and facility comparisons. '
                           'Machine learning models identify anomalies and optimization opportunities.',
                    'benefits': [
                        'Identify water-saving opportunities worth 15%+ volume',
                        'Predict seasonal demand fluctuations',
                        'Benchmark facilities against each other'
                    ]
                },
                {
                    'name': 'Export & Import Suite',
                    'tier': 'Standard',
                    'desc': 'Export data to Excel, PDF, CSV with custom templates. Import meter readings from field devices. '
                           'Automated Excel integration eliminates manual data entry.',
                    'benefits': [
                        'Share reports with stakeholders in their preferred format',
                        'Import 1000s of meter readings in seconds',
                        'Custom export templates for specific use cases'
                    ]
                }
            ]
        )
        
    def _build_q4_features(self, parent):
        """Build Q4 2026 features (Enterprise Platform)."""
        self._build_quarter_card(
            parent,
            quarter='Q4 2026 • November Launch',
            title='Enterprise Platform Capabilities',
            color='#6c3fb5',
            features=[
                {
                    'name': 'Multi-Site Management',
                    'tier': 'Enterprise',
                    'desc': 'Manage water balance across multiple mining operations from a single dashboard. '
                           'Consolidated reporting, cross-site analytics, and centralized configuration.',
                    'benefits': [
                        'Unified view of all operations (up to 50 sites)',
                        'Cross-site water transfer optimization',
                        'Executive summary dashboards for leadership'
                    ]
                },
                {
                    'name': 'REST API & Integrations',
                    'tier': 'Enterprise',
                    'desc': 'RESTful API for integrating with SCADA, ERP, and BI systems. Webhooks for real-time data push. '
                           'Developer-friendly documentation with code samples.',
                    'benefits': [
                        'Connect to SAP, PI, OSIsoft, or custom systems',
                        'Automate data flows without manual intervention',
                        'Build custom integrations with your IT stack'
                    ]
                },
                {
                    'name': 'Predictive Analytics',
                    'tier': 'Enterprise',
                    'desc': 'Machine learning models predict storage levels, inflow demands, and maintenance needs. '
                           'What-if scenarios for operational planning.',
                    'benefits': [
                        'Forecast water demand 30 days ahead with 95% accuracy',
                        'Prevent unplanned shutdowns with predictive maintenance',
                        'Plan capex investments with scenario modeling'
                    ]
                },
                {
                    'name': 'Custom Report Builder',
                    'tier': 'Professional',
                    'desc': 'Drag-and-drop report designer with custom fields, formulas, and visualizations. '
                           'Save templates for recurring reports.',
                    'benefits': [
                        'Create reports tailored to your exact needs',
                        'No coding required - visual designer',
                        'Schedule automated delivery via email'
                    ]
                }
            ]
        )
        
    def _build_quarter_card(self, parent, quarter: str, title: str, color: str, features: List[Dict]):
        """
        Build a quarter card with features.
        
        Args:
            parent: Parent widget
            quarter: Quarter label (e.g., 'Q2 2026 • May Launch')
            title: Section title (e.g., 'Compliance & Alerting')
            color: Theme color for the quarter
            features: List of feature dicts with name, tier, desc, benefits
        """
        card = tk.Frame(parent, bg='white', relief=tk.FLAT, bd=1, 
                       highlightbackground=color, highlightthickness=2)
        card.pack(fill='x', pady=(0, 20))
        
        inner = tk.Frame(card, bg='white')
        inner.pack(fill='x', padx=30, pady=20)
        
        # Quarter header
        header_frame = tk.Frame(inner, bg=color, relief=tk.FLAT)
        header_frame.pack(fill='x', pady=(0, 20))
        
        header_inner = tk.Frame(header_frame, bg=color)
        header_inner.pack(fill='x', padx=20, pady=12)
        
        tk.Label(header_inner, text=quarter, font=('Segoe UI', 10, 'bold'), 
                bg=color, fg='white').pack(side='left')
        
        tk.Label(header_inner, text='•', font=('Segoe UI', 10, 'bold'), 
                bg=color, fg='white').pack(side='left', padx=10)
        
        tk.Label(header_inner, text=title, font=('Segoe UI', 14, 'bold'), 
                bg=color, fg='white').pack(side='left')
        
        tk.Label(header_inner, text='⏳ Under Development', font=('Segoe UI', 9, 'bold'), 
                bg=color, fg='white').pack(side='right')
        
        # Features
        for idx, feature in enumerate(features):
            self._build_feature_item(inner, feature, color, is_last=(idx == len(features) - 1))
            
    def _build_feature_item(self, parent, feature: Dict, color: str, is_last: bool):
        """
        Build a single feature item.
        
        Args:
            parent: Parent widget
            feature: Feature dict with name, tier, desc, benefits
            color: Theme color
            is_last: Whether this is the last feature in the section
        """
        feature_frame = tk.Frame(parent, bg='#f8f9fa', relief=tk.FLAT, bd=1, 
                                highlightbackground='#e8eef5', highlightthickness=1)
        feature_frame.pack(fill='x', pady=(0, 15 if not is_last else 0))
        
        feature_inner = tk.Frame(feature_frame, bg='#f8f9fa')
        feature_inner.pack(fill='x', padx=20, pady=15)
        
        # Feature name and tier
        title_frame = tk.Frame(feature_inner, bg='#f8f9fa')
        title_frame.pack(fill='x', pady=(0, 8))
        
        tk.Label(title_frame, text=feature['name'], font=('Segoe UI', 12, 'bold'), 
                bg='#f8f9fa', fg='#2c3e50').pack(side='left')
        
        # Tier badge
        tier_colors = {
            'Standard': '#28a745',
            'Professional': '#3498db',
            'Enterprise': '#6c3fb5'
        }
        tier_bg = tier_colors.get(feature['tier'], '#7f8c8d')
        
        tier_badge = tk.Frame(title_frame, bg=tier_bg, relief=tk.FLAT)
        tier_badge.pack(side='left', padx=(15, 0))
        
        tk.Label(tier_badge, text=feature['tier'], font=('Segoe UI', 9, 'bold'), 
                bg=tier_bg, fg='white', padx=12, pady=4).pack()
        
        # Description
        tk.Label(feature_inner, text=feature['desc'], font=('Segoe UI', 10), 
                bg='#f8f9fa', fg='#2c3e50', wraplength=800, justify='left').pack(anchor='w', pady=(0, 10))
        
        # Benefits
        benefits_frame = tk.Frame(feature_inner, bg='#f8f9fa')
        benefits_frame.pack(fill='x')
        
        tk.Label(benefits_frame, text='✨ Key Benefits:', font=('Segoe UI', 9, 'bold'), 
                bg='#f8f9fa', fg=color).pack(anchor='w', pady=(0, 5))
        
        for benefit in feature['benefits']:
            benefit_row = tk.Frame(benefits_frame, bg='#f8f9fa')
            benefit_row.pack(fill='x', pady=2)
            
            tk.Label(benefit_row, text='  ✓', font=('Segoe UI', 10), 
                    bg='#f8f9fa', fg=color).pack(side='left')
            
            tk.Label(benefit_row, text=benefit, font=('Segoe UI', 9), 
                    bg='#f8f9fa', fg='#2c3e50', wraplength=750, justify='left').pack(side='left', padx=(5, 0))
        
    def _build_footer(self, parent):
        """Build call-to-action footer."""
        footer_card = tk.Frame(parent, bg='#e7f3ff', relief=tk.FLAT, bd=2, 
                              highlightbackground='#3498db', highlightthickness=2)
        footer_card.pack(fill='x', pady=(0, 0))
        
        inner = tk.Frame(footer_card, bg='#e7f3ff')
        inner.pack(fill='x', padx=30, pady=25)
        
        # CTA message
        tk.Label(inner, text='💼 Interested in Early Access?', 
                font=('Segoe UI', 16, 'bold'), bg='#e7f3ff', fg='#004085').pack(anchor='w', pady=(0, 10))
        
        tk.Label(inner, 
                text="These features represent the future of environmental compliance and operational excellence. "
                     "Contact your account manager to discuss upgrade options, pilot programs, and custom feature requests.",
                font=('Segoe UI', 11), bg='#e7f3ff', fg='#004085', 
                wraplength=800, justify='left').pack(anchor='w', pady=(0, 15))
        
        # Action buttons
        btn_frame = tk.Frame(inner, bg='#e7f3ff')
        btn_frame.pack(fill='x')
        
        tk.Button(btn_frame, text='📧 Contact Sales', 
                 command=self._contact_sales,
                 font=('Segoe UI', 11, 'bold'), bg='#3498db', fg='white', 
                 relief=tk.FLAT, padx=20, pady=10, cursor='hand2',
                 activebackground='#2980b9', activeforeground='white').pack(side='left', padx=(0, 10))
        
        tk.Button(btn_frame, text='📄 View Full Roadmap', 
                 command=self._view_roadmap,
                 font=('Segoe UI', 11, 'bold'), bg='#28a745', fg='white', 
                 relief=tk.FLAT, padx=20, pady=10, cursor='hand2',
                 activebackground='#218838', activeforeground='white').pack(side='left', padx=(0, 10))
        
        tk.Button(btn_frame, text='💡 Request Feature', 
                 command=self._request_feature,
                 font=('Segoe UI', 11, 'bold'), bg='#6c3fb5', fg='white', 
                 relief=tk.FLAT, padx=20, pady=10, cursor='hand2',
                 activebackground='#5a2da1', activeforeground='white').pack(side='left')
        
    def _contact_sales(self):
        """Open contact sales dialog with real company contact info."""
        import webbrowser
        
        # Use real contact info from About section
        contact_info = (
            'Contact Information:\n\n'
            'Administrator: Ms Moloko Florence Morethe\n'
            'Email: mfmorethe@transafreso.com\n'
            'Phone: +27 83 870 6569\n\n'
            'Project Lead: Prof Caliphs Zvinowanda\n'
            'Email: caliphs@transafreso.com\n'
            'Phone: +27 82 355 8130\n\n'
            'Would you like to send an email inquiry about future features?'
        )
        
        result = messagebox.askyesno(
            'Contact Sales & Support',
            contact_info
        )
        
        if result:
            # Primary contact for sales inquiries
            webbrowser.open('mailto:mfmorethe@transafreso.com?cc=caliphs@transafreso.com&subject=Water Balance App - Future Features Inquiry')
        
    def _view_roadmap(self):
        """Open full roadmap documentation (works in both dev and built app)."""
        from utils.config_manager import get_resource_path
        
        # Use get_resource_path for PyInstaller compatibility
        roadmap_path = get_resource_path('docs/FUTURE_FEATURES_ROADMAP_2026.md')
        
        if roadmap_path and roadmap_path.exists():
            import subprocess
            import platform
            
            try:
                if platform.system() == 'Windows':
                    subprocess.run(['start', '', str(roadmap_path)], shell=True)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', str(roadmap_path)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(roadmap_path)])
                    
                logger.info(f"Opened roadmap document: {roadmap_path}")
            except Exception as ex:
                logger.error(f"Failed to open roadmap: {ex}")
                messagebox.showerror('Error', f'Failed to open roadmap document:\n{str(ex)}')
        else:
            # Fallback: show contact info if file not found
            messagebox.showinfo(
                'Roadmap Information',
                'For complete feature roadmap details, please contact:\n\n'
                'Ms Moloko Florence Morethe\n'
                'Email: mfmorethe@transafreso.com\n'
                'Phone: +27 83 870 6569'
            )
        
    def _request_feature(self):
        """Open feature request dialog."""
        dialog = tk.Toplevel(self.parent)
        dialog.title('Request a Custom Feature')
        dialog.geometry('600x450')
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Content
        content = tk.Frame(dialog, bg='white', padx=30, pady=20)
        content.pack(fill='both', expand=True)
        
        tk.Label(content, text='💡 Feature Request', 
                font=('Segoe UI', 16, 'bold'), bg='white', fg='#2c3e50').pack(anchor='w', pady=(0, 10))
        
        tk.Label(content, 
                text='Have a specific feature in mind that would benefit your operations? '
                     'We welcome custom feature requests from our valued customers.',
                font=('Segoe UI', 10), bg='white', fg='#2c3e50', 
                wraplength=540, justify='left').pack(anchor='w', pady=(0, 15))
        
        tk.Label(content, text='Feature Name:', font=('Segoe UI', 10, 'bold'), 
                bg='white', fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        
        name_entry = tk.Entry(content, font=('Segoe UI', 11), relief=tk.FLAT, bd=1, 
                             highlightbackground='#d9e6f4', highlightthickness=1)
        name_entry.pack(fill='x', ipady=6, pady=(0, 15))
        
        tk.Label(content, text='Description:', font=('Segoe UI', 10, 'bold'), 
                bg='white', fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        
        desc_text = tk.Text(content, font=('Segoe UI', 10), height=8, wrap='word', 
                           relief=tk.FLAT, bd=1, highlightbackground='#d9e6f4', highlightthickness=1)
        desc_text.pack(fill='both', expand=True, pady=(0, 15))
        
        tk.Label(content, text='Your Email:', font=('Segoe UI', 10, 'bold'), 
                bg='white', fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        
        email_entry = tk.Entry(content, font=('Segoe UI', 11), relief=tk.FLAT, bd=1, 
                              highlightbackground='#d9e6f4', highlightthickness=1)
        email_entry.pack(fill='x', ipady=6, pady=(0, 20))
        
        # Buttons
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(fill='x')
        
        def submit():
            name = name_entry.get().strip()
            desc = desc_text.get('1.0', 'end').strip()
            email = email_entry.get().strip()
            
            if not name or not desc or not email:
                messagebox.showwarning('Incomplete', 'Please fill in all fields.')
                return
            
            # In production, this would send to a backend API or email service
            messagebox.showinfo(
                'Request Submitted',
                f'Thank you for your feature request!\n\n'
                f'Feature: {name}\n\n'
                f'Your request has been logged. Our product team will review and contact you at {email}.\n\n'
                f'For immediate assistance, contact:\n'
                f'Ms Moloko Florence Morethe\n'
                f'Email: mfmorethe@transafreso.com\n'
                f'Phone: +27 83 870 6569'
            )
            
            logger.info(f"Feature request submitted: {name} by {email}")
            dialog.destroy()
        
        tk.Button(btn_frame, text='Submit Request', command=submit,
                 font=('Segoe UI', 10, 'bold'), bg='#3498db', fg='white', 
                 relief=tk.FLAT, padx=20, pady=8, cursor='hand2',
                 activebackground='#2980b9', activeforeground='white').pack(side='left', padx=(0, 10))
        
        tk.Button(btn_frame, text='Cancel', command=dialog.destroy,
                 font=('Segoe UI', 10), bg='#7f8c8d', fg='white', 
                 relief=tk.FLAT, padx=20, pady=8, cursor='hand2',
                 activebackground='#6c757d', activeforeground='white').pack(side='left')
        
    def _load_features_data(self) -> Dict:
        """
        Load features data from roadmap document.
        
        Returns:
            Dict with feature data organized by quarter
            
        Note: Currently returns hardcoded data; could be extended to parse
        FUTURE_FEATURES_ROADMAP_2026.md dynamically in future versions.
        """
        # Hardcoded for now; could parse from markdown file in future
        return {
            'q2_2026': [
                'Compliance Reporting System',
                'Intelligent Alert System'
            ],
            'q3_2026': [
                'Air Quality Monitoring',
                'Advanced Analytics Engine',
                'Export & Import Suite'
            ],
            'q4_2026': [
                'Multi-Site Management',
                'REST API & Integrations',
                'Predictive Analytics',
                'Custom Report Builder'
            ]
        }
