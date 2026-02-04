#!/usr/bin/env python3
"""
Create sample monitoring data for testing the monitoring dashboard.

This script generates test Excel files with realistic borehole and PCD monitoring data.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Create directories
base_dir = Path(__file__).parent / "data" / "monitoring"
base_dir.mkdir(parents=True, exist_ok=True)

borehole_static_dir = base_dir / "borehole_static"
borehole_static_dir.mkdir(exist_ok=True)

# Sample borehole names
BOREHOLES = [
    "BH001 - Main North",
    "BH002 - East Wing",
    "BH003 - South Zone",
    "BH004 - Test Point",
    "BH005 - Backup",
]

PARAMETERS = {
    "Borehole ID": ["BH001", "BH002", "BH003", "BH004", "BH005"],
    "Borehole Name": BOREHOLES,
    "Aquifer": ["Aquifer A", "Aquifer B", "Aquifer A", "Aquifer C", "Aquifer B"],
}

# Generate static levels data
print("Creating sample borehole static levels data...")
dates = [datetime(2025, 1, 1) + timedelta(days=30*i) for i in range(12)]

rows = []
for date in dates:
    for i, bh_id in enumerate(PARAMETERS["Borehole ID"]):
        bh_name = PARAMETERS["Borehole Name"][i]
        aquifer = PARAMETERS["Aquifer"][i]
        
        # Realistic water level measurements (meters below surface)
        static_level = 15.5 + np.random.uniform(-0.5, 0.5)
        
        rows.append({
            "Borehole ID": bh_id,
            "Borehole Name": bh_name,
            "Aquifer": aquifer,
            "Date": date,
            "Static Level (m)": round(static_level, 2),
        })

df_static = pd.DataFrame(rows)

# Save to Excel
excel_file = borehole_static_dir / "borehole_static_levels_2025.xlsx"
df_static.to_excel(excel_file, index=False)
print(f"✓ Created {excel_file}")
print(f"  {len(df_static)} records, {len(BOREHOLES)} boreholes, {len(dates)} measurement dates")

# Generate borehole monitoring (water quality) data
print("\nCreating sample borehole monitoring (water quality) data...")
monitoring_dir = base_dir / "borehole_monitoring"
monitoring_dir.mkdir(exist_ok=True)

monitoring_rows = []
for date in dates:
    for i, bh_id in enumerate(PARAMETERS["Borehole ID"]):
        bh_name = PARAMETERS["Borehole Name"][i]
        aquifer = PARAMETERS["Aquifer"][i]
        
        # Realistic water quality parameters
        monitoring_rows.append({
            "Borehole": bh_name,
            "Aquifer": aquifer,
            "Date": date,
            "Calcium": round(np.random.uniform(20, 80), 1),
            "Chloride": round(np.random.uniform(10, 100), 1),
            "Magnesium": round(np.random.uniform(5, 30), 1),
            "Nitrate (No3)": round(np.random.uniform(0, 20), 1),
            "Potassium": round(np.random.uniform(5, 20), 1),
            "Sulphate": round(np.random.uniform(30, 150), 1),
            "Total Dissolved Solids": round(np.random.uniform(200, 500), 1),
            "Static Level": round(np.random.uniform(14, 17), 2),
            "Sodium": round(np.random.uniform(10, 50), 1),
        })

df_monitoring = pd.DataFrame(monitoring_rows)

monitoring_excel = monitoring_dir / "borehole_monitoring_2025.xlsx"
df_monitoring.to_excel(monitoring_excel, index=False)
print(f"✓ Created {monitoring_excel}")
print(f"  {len(df_monitoring)} records, {len(BOREHOLES)} boreholes")

# Generate PCD monitoring data
print("\nCreating sample PCD monitoring data...")
pcd_dir = base_dir / "pcd_monitoring"
pcd_dir.mkdir(exist_ok=True)

PCD_POINTS = ["PCD001", "PCD002", "PCD003"]

pcd_rows = []
for date in dates:
    for point_id in PCD_POINTS:
        pcd_rows.append({
            "Point": point_id,
            "Point Name": f"Perched Clay Dam - {point_id}",
            "Date": date,
            "Ph": round(np.random.uniform(6.5, 8.0), 2),
            "Electrical Conductivity": round(np.random.uniform(500, 2000), 0),
            "Turbidity": round(np.random.uniform(0.5, 5), 2),
            "Temperature": round(np.random.uniform(15, 28), 1),
        })

df_pcd = pd.DataFrame(pcd_rows)

pcd_excel = pcd_dir / "pcd_monitoring_2025.xlsx"
df_pcd.to_excel(pcd_excel, index=False)
print(f"✓ Created {pcd_excel}")
print(f"  {len(df_pcd)} records, {len(PCD_POINTS)} measurement points")

print("\n✅ Sample data created successfully!")
print("\nTo test the monitoring dashboard:")
print("1. Open the Monitoring Data Dashboard")
print("2. Click 'Select Folder' for each tab:")
print(f"   - Borehole Static Levels: {borehole_static_dir}")
print(f"   - Borehole Monitoring: {monitoring_dir}")
print(f"   - PCD Monitoring: {pcd_dir}")
print("3. Check if data loads and displays in tables")
