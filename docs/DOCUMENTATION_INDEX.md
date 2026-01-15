# Water Balance Application - Documentation Index

## Overview

This documentation covers the Water Balance Application, a Python/Tkinter desktop application for mine water balance calculations across 8 areas, featuring real-time calculations, flow diagrams, and comprehensive monitoring dashboards.

## Quick Navigation

**New Users**: Start with [README.md](../README.md) → [QUICK_REFERENCE_TODAY.md](#quick-reference-today)  
**Monitoring Data**: Start with [Monitoring Tabs Overview](#monitoring-data-dashboards)  
**Balance Calculations**: Start with [BALANCE_CHECK_README.md](#balance-check-documentation)  
**Flow Diagrams**: Start with [FLOW_DIAGRAM_GUIDE.md](#flow-diagram-documentation)

---

## Table of Contents

### Core Application Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [../README.md](../README.md) | Project overview, setup, quick start | All users |
| [QUICK_REFERENCE_TODAY.md](#quick-reference-today) | Today's date, common tasks at a glance | Daily users |
| [QUICK_REFERENCE.txt](#quick-referencetxt) | Text-based quick reference (printable) | Reference |

### Monitoring Data Dashboards

#### 🌊 PCD (Pollution Control Dam) Monitoring
**NEW - Fully Implemented**

| Document | Purpose | Audience |
|----------|---------|----------|
| [PCD_MONITORING_GUIDE.md](#pcd-monitoring-guide) | Complete feature guide with workflows | End users |
| [PCD_MONITORING_QUICK_REFERENCE.md](#pcd-monitoring-quick-reference) | At-a-glance reference (1-page printable) | Daily users |
| [PCD_MONITORING_VISUAL_GUIDE.md](#pcd-monitoring-visual-guide) | ASCII diagrams, layout, data flow | Visual learners |
| [PCD_MONITORING_IMPLEMENTATION_SUMMARY.md](#pcd-monitoring-implementation-summary) | Technical implementation details | Developers |

#### 🥾 Borehole Monitoring (Previously Implemented)

| Document | Purpose | Audience |
|----------|---------|----------|
| [Borehole Selector Guide](#borehole-monitoring) | How to filter by individual boreholes | End users |
| [Responsive Design Guide](#borehole-monitoring) | Adaptive UI for different screen sizes | Visual learners |

#### Static Tab (Borehole Water Levels)
- View historical water level trends
- Industry-standard professional charts (no moving average)
- Wide bar charts (56px width)

### Balance Check & Calculations

#### 📊 Balance Check Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [BALANCE_CHECK_README.md](#balance-check-readme) | How to interpret balance check results | End users |
| [BALANCE_CHECK_QUICK_REFERENCE.md](#balance-check-quick-reference) | Balance check parameters at a glance | Reference |
| [BALANCE_CHECK_PARAMETERS_COMPLETE_ANSWER.md](#balance-check-parameters-complete-answer) | Complete parameter definitions + explanations | Detailed users |
| [BALANCE_METRICS_GUIDE.md](#balance-metrics-guide) | Water balance metrics and indicators | Technical users |

### Flow Diagrams & Water Balance

| Document | Purpose | Audience |
|----------|---------|----------|
| [FLOW_DIAGRAM_GUIDE.md](#flow-diagram-guide) | Interactive flow diagram usage | End users |
| [FLOW_TYPES_LEGEND.md](#flow-types-legend) | Color-coded flow types and meanings | Reference |

### Data Reference

| Document | Purpose | Audience |
|----------|---------|----------|
| [EXCEL_COLUMN_LEGEND.md](#excel-column-legend) | Excel column names and their meanings | Data analysts |
| [CONSTANT_USAGE_MAP.md](#constant-usage-map) | Application constants and their usage | Developers |
| [DAILY_CONSUMPTION_SOURCE.md](#daily-consumption-source) | Where consumption data comes from | Data managers |

### Feature-Specific Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [TAILINGS_MOISTURE_USER_GUIDE.md](#tailings-moisture-user-guide) | Tailings moisture content tracking | End users |
| [TAILINGS_MOISTURE_IMPLEMENTATION.md](#tailings-moisture-implementation) | Technical implementation details | Developers |

### Session & Planning Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| [SESSION_COMPREHENSIVE_SUMMARY.md](#session-comprehensive-summary) | Latest session work summary | Project team |

---

## Detailed Document Descriptions

### Quick Reference Today
**File**: [QUICK_REFERENCE_TODAY.md](QUICK_REFERENCE_TODAY.md)
- Today's date and quick access links
- Common daily tasks
- Emergency contact/help
- Status indicators

### Quick Reference (Text)
**File**: [QUICK_REFERENCE.txt](QUICK_REFERENCE.txt)
- Plain text version (printable, compatible)
- Common shortcuts
- File locations
- Troubleshooting quick links

### PCD Monitoring Guide
**File**: [PCD_MONITORING_GUIDE.md](PCD_MONITORING_GUIDE.md)
- Complete feature overview
- Step-by-step workflows (3 examples)
- Excel file format requirements
- Parameter reference table (20+ water quality metrics)
- Troubleshooting guide
- Best practices
- Keyboard shortcuts
- Data deduplication explanation
- Performance notes

**Target Audience**: End users who work with water quality monitoring data

**Key Sections**:
1. Features (upload, preview, chart generation)
2. Workflows (compare dams, analyze trends, statistical analysis)
3. Excel format specifications
4. Common parameter meanings
5. Troubleshooting

### PCD Monitoring Quick Reference
**File**: [PCD_MONITORING_QUICK_REFERENCE.md](PCD_MONITORING_QUICK_REFERENCE.md)
- 1-page printable summary
- At-a-glance feature table
- Quick steps (3 main workflows)
- Common parameters table (abbreviated)
- Data quality warnings key
- Filter reference
- Chart type comparison
- Troubleshooting quick table
- Example scenarios (3 cases)
- Keyboard shortcuts

**Target Audience**: Daily users, quick lookup reference

### PCD Monitoring Visual Guide
**File**: [PCD_MONITORING_VISUAL_GUIDE.md](PCD_MONITORING_VISUAL_GUIDE.md)
- ASCII diagram of tab layout
- Upload & Preview sub-tab diagram
- Visualize sub-tab diagram
- Color-coding system (rows, chart lines)
- Data flow diagram (Excel → Parser → UI)
- User interaction flow (8-step process)
- Responsive design examples (3 screen sizes)
- Chart examples (Line, Bar, Box ASCII art)
- Information badge reference

**Target Audience**: Visual learners, UI/UX designers, new users

### PCD Monitoring Implementation Summary
**File**: [PCD_MONITORING_IMPLEMENTATION_SUMMARY.md](PCD_MONITORING_IMPLEMENTATION_SUMMARY.md)
- Architecture overview
- 13 core functions + 1 helper function
- Data flow (9-step process)
- Excel parser details (header detection, parameter extraction, date parsing)
- UI components breakdown
- Responsive design specifications
- Chart styling standards
- Caching strategy
- Performance optimizations
- Error handling table
- Feature checklist (✅ implemented)
- Testing performed
- Code quality assessment
- Comparison: Borehole vs PCD
- Known limitations (6 items)
- Future enhancement ideas

**Target Audience**: Developers, code reviewers, maintainers

### Balance Check README
**File**: [BALANCE_CHECK_README.md](BALANCE_CHECK_README.md)
- How balance check works
- Interpreting balance results
- Best practices
- Common issues and solutions

### Balance Check Quick Reference
**File**: [BALANCE_CHECK_QUICK_REFERENCE.md](BALANCE_CHECK_QUICK_REFERENCE.md)
- Key balance check parameters
- At-a-glance definitions
- Quick troubleshooting table

### Balance Check Parameters Complete Answer
**File**: [BALANCE_CHECK_PARAMETERS_COMPLETE_ANSWER.md](BALANCE_CHECK_PARAMETERS_COMPLETE_ANSWER.md)
- Complete parameter explanations
- Technical definitions
- Calculation methods
- Expected ranges
- How to fix when out of balance

### Balance Metrics Guide
**File**: [BALANCE_METRICS_GUIDE.md](BALANCE_METRICS_GUIDE.md)
- Water balance indicators
- Performance metrics
- How to interpret results
- KPI definitions

### Flow Diagram Guide
**File**: [FLOW_DIAGRAM_GUIDE.md](FLOW_DIAGRAM_GUIDE.md)
- Interactive flow diagram usage
- Edge mapping (flows between components)
- Custom waypoints
- Color-coding (clean/waste/underground flows)
- Zoom and pan controls
- Export diagrams

### Flow Types Legend
**File**: [FLOW_TYPES_LEGEND.md](FLOW_TYPES_LEGEND.md)
- Flow color meanings
- Line styles
- Component shapes
- Edge indicators

### Excel Column Legend
**File**: [EXCEL_COLUMN_LEGEND.md](EXCEL_COLUMN_LEGEND.md)
- All Excel column names
- Their purposes
- Expected data types
- Allowed values

### Constant Usage Map
**File**: [CONSTANT_USAGE_MAP.md](CONSTANT_USAGE_MAP.md)
- Application constants
- Where they're used
- How to modify them
- Impact of changes

### Daily Consumption Source
**File**: [DAILY_CONSUMPTION_SOURCE.md](DAILY_CONSUMPTION_SOURCE.md)
- Where consumption data comes from
- Update frequency
- Data validation rules
- Import process

### Tailings Moisture User Guide
**File**: [TAILINGS_MOISTURE_USER_GUIDE.md](TAILINGS_MOISTURE_USER_GUIDE.md)
- How to enter tailings moisture data
- Interpretation
- Impact on balance
- Best practices

### Tailings Moisture Implementation
**File**: [TAILINGS_MOISTURE_IMPLEMENTATION.md](TAILINGS_MOISTURE_IMPLEMENTATION.md)
- Technical implementation
- Database schema
- Calculation methods
- Integration points

### Session Comprehensive Summary
**File**: [SESSION_COMPREHENSIVE_SUMMARY.md](SESSION_COMPREHENSIVE_SUMMARY.md)
- Latest session work log
- Features implemented
- Bugs fixed
- Performance improvements
- Testing results
- Next steps

---

## Document Organization

### By User Role

#### End Users (No technical background)
1. Start: [../README.md](../README.md)
2. Learn: [QUICK_REFERENCE_TODAY.md](#quick-reference-today)
3. Monitor PCD Data: [PCD_MONITORING_GUIDE.md](#pcd-monitoring-guide)
4. Balance Calculations: [BALANCE_CHECK_README.md](#balance-check-readme)
5. Reference: [PCD_MONITORING_QUICK_REFERENCE.md](#pcd-monitoring-quick-reference)

#### Data Analysts
1. Start: [EXCEL_COLUMN_LEGEND.md](#excel-column-legend)
2. Flows: [FLOW_DIAGRAM_GUIDE.md](#flow-diagram-guide)
3. Monitoring: [PCD_MONITORING_GUIDE.md](#pcd-monitoring-guide)
4. Balance: [BALANCE_METRICS_GUIDE.md](#balance-metrics-guide)
5. Reference: [DAILY_CONSUMPTION_SOURCE.md](#daily-consumption-source)

#### Developers / Code Maintainers
1. Start: [../README.md](../README.md)
2. Implementation: [PCD_MONITORING_IMPLEMENTATION_SUMMARY.md](#pcd-monitoring-implementation-summary)
3. Architecture: [CONSTANT_USAGE_MAP.md](#constant-usage-map)
4. Technical Details: [BALANCE_CHECK_PARAMETERS_COMPLETE_ANSWER.md](#balance-check-parameters-complete-answer)
5. Latest Changes: [SESSION_COMPREHENSIVE_SUMMARY.md](#session-comprehensive-summary)

#### System Administrators
1. Setup: [../README.md](../README.md)
2. Configuration: [CONSTANT_USAGE_MAP.md](#constant-usage-map)
3. Data Sources: [DAILY_CONSUMPTION_SOURCE.md](#daily-consumption-source)
4. Monitoring: [PCD_MONITORING_GUIDE.md](#pcd-monitoring-guide)

### By Topic

#### Water Quality Monitoring
- [PCD_MONITORING_GUIDE.md](#pcd-monitoring-guide) - Complete guide
- [PCD_MONITORING_QUICK_REFERENCE.md](#pcd-monitoring-quick-reference) - Quick lookup
- [PCD_MONITORING_VISUAL_GUIDE.md](#pcd-monitoring-visual-guide) - Visual reference
- [PCD_MONITORING_IMPLEMENTATION_SUMMARY.md](#pcd-monitoring-implementation-summary) - Technical

#### Water Balance
- [BALANCE_CHECK_README.md](#balance-check-readme) - Interpretation guide
- [BALANCE_CHECK_QUICK_REFERENCE.md](#balance-check-quick-reference) - Quick reference
- [BALANCE_CHECK_PARAMETERS_COMPLETE_ANSWER.md](#balance-check-parameters-complete-answer) - Detailed parameters
- [BALANCE_METRICS_GUIDE.md](#balance-metrics-guide) - KPIs and metrics

#### Data Management
- [EXCEL_COLUMN_LEGEND.md](#excel-column-legend) - Column reference
- [DAILY_CONSUMPTION_SOURCE.md](#daily-consumption-source) - Data sources
- [CONSTANT_USAGE_MAP.md](#constant-usage-map) - Constants

#### Visualizations
- [FLOW_DIAGRAM_GUIDE.md](#flow-diagram-guide) - Interactive diagrams
- [FLOW_TYPES_LEGEND.md](#flow-types-legend) - Flow colors and types
- [PCD_MONITORING_VISUAL_GUIDE.md](#pcd-monitoring-visual-guide) - UI layouts

#### Features
- [TAILINGS_MOISTURE_USER_GUIDE.md](#tailings-moisture-user-guide) - Tailings moisture tracking
- [TAILINGS_MOISTURE_IMPLEMENTATION.md](#tailings-moisture-implementation) - Technical implementation

#### Reference & Quick Access
- [QUICK_REFERENCE_TODAY.md](#quick-reference-today) - Daily reference
- [QUICK_REFERENCE.txt](#quick-referencetxt) - Printable text version

#### Session History
- [SESSION_COMPREHENSIVE_SUMMARY.md](#session-comprehensive-summary) - Latest work

---

## Documentation Standards

### Naming Convention
- **User Guides**: `{FEATURE}_USER_GUIDE.md` or `{FEATURE}_GUIDE.md`
- **Quick References**: `{FEATURE}_QUICK_REFERENCE.md` or `QUICK_REFERENCE_{CONTEXT}.md`
- **Visual Guides**: `{FEATURE}_VISUAL_GUIDE.md`
- **Implementation Docs**: `{FEATURE}_IMPLEMENTATION_{CONTEXT}.md`
- **Technical Reference**: `{DESCRIPTION}.md` (e.g., `EXCEL_COLUMN_LEGEND.md`)

### Document Structure
1. **Title** (H1)
2. **Overview** (Brief intro)
3. **Table of Contents** (If >5 sections)
4. **Quick Navigation** (Links to common sections)
5. **Main Content** (Organized by H2 sections)
6. **Examples** (Practical scenarios)
7. **Troubleshooting** (Common issues & solutions)
8. **Related Topics** (Cross-links)
9. **Metadata** (Last updated, version, audience)

### Formatting Standards
- **Bold**: Feature names, important concepts
- **Code**: `function_names()`, file paths, commands
- **Links**: [Display Text](path/to/doc.md)
- **Lists**: Bullet points for conceptual; numbered for procedures
- **Tables**: For comparisons and reference data
- **ASCII Art**: For visual layouts and data flow
- **Code Blocks**: For configuration, SQL, or code examples

---

## Common Tasks & Where to Find Help

| Task | Where to Go |
|------|-------------|
| I'm new, where do I start? | [README.md](../README.md) then [QUICK_REFERENCE_TODAY.md](#quick-reference-today) |
| I need a quick summary of all tasks | [QUICK_REFERENCE.txt](#quick-referencetxt) (printable) |
| I want to analyze PCD water quality data | [PCD_MONITORING_GUIDE.md](#pcd-monitoring-guide) |
| I need a 1-page PCD reference | [PCD_MONITORING_QUICK_REFERENCE.md](#pcd-monitoring-quick-reference) (printable) |
| I want to understand the PCD UI layout | [PCD_MONITORING_VISUAL_GUIDE.md](#pcd-monitoring-visual-guide) |
| I'm a developer implementing PCD features | [PCD_MONITORING_IMPLEMENTATION_SUMMARY.md](#pcd-monitoring-implementation-summary) |
| I don't understand balance check results | [BALANCE_CHECK_README.md](#balance-check-readme) |
| I need balance check parameters | [BALANCE_CHECK_PARAMETERS_COMPLETE_ANSWER.md](#balance-check-parameters-complete-answer) |
| I need to find which Excel column is what | [EXCEL_COLUMN_LEGEND.md](#excel-column-legend) |
| I want to view water flow diagrams | [FLOW_DIAGRAM_GUIDE.md](#flow-diagram-guide) |
| I'm tracking tailings moisture | [TAILINGS_MOISTURE_USER_GUIDE.md](#tailings-moisture-user-guide) |
| I want to know what changed recently | [SESSION_COMPREHENSIVE_SUMMARY.md](#session-comprehensive-summary) |

---

## Archive & Previous Documentation

Historical documentation is stored in [archive/](archive/) for reference:
- Previous session logs
- Deprecated features
- Legacy implementation notes
- Old workflows

## Features Documentation

Feature-specific documentation is stored in [features/](features/) for in-depth coverage:
- Component rename system
- Automated pump transfers
- Database schema updates
- Advanced analysis workflows

---

## How to Update This Index

When adding new documentation:
1. Create `.md` file in `docs/` folder
2. Add entry to appropriate section in this index
3. Include brief description (1-2 sentences)
4. Add cross-references from related documents
5. Update "Common Tasks" table if applicable

---

## Feedback & Improvements

Found an issue or have a suggestion?
- Check related documents for updated information
- Review [SESSION_COMPREHENSIVE_SUMMARY.md](#session-comprehensive-summary) for latest changes
- Note the document title and section for feedback

---

**Last Updated**: 2025-01-11  
**Total Documents**: 20+  
**Coverage**: Complete (all major features documented)  
**Status**: Active (regularly updated)

