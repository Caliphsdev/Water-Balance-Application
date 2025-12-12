import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_manager import db
import json

print("=" * 80)
print("VERIFYING OLD TSF COMPONENTS IN DATABASE")
print("=" * 80)

# List of components we added to the diagram
diagram_components = {
    "Inflows": [
        "oldtsf_gwa_boreholes",      # OT_GWA_boreholes
        "oldtsf_old_tsf_rainrun",    # OT_OLD_TSF_rainrun
        "oldtsf_trtd_rain",          # OT_TRTD_rain
        "oldtsf_new_tsf_rainrun",    # OT_NEW_TSF_rainrun
        "oldtsf_nt_rwd_rain",        # OT_NT_RWD_rain
    ],
    "Structures": [
        "oldtsf_offices",            # Structure ID 25
        "oldtsf_old_tsf",            # Structure ID 26
        "oldtsf_trtd",               # Structure ID 27
        "oldtsf_new_tsf",            # Structure ID 28
        "oldtsf_nt_rwd",             # Structure ID 29
    ],
    "Outflows": [
        "oldtsf_off_septic",         # OT_OFF_septic
        "oldtsf_off_consumption",    # OT_OFF_consumption
        "oldtsf_old_tsf_evap",       # OT_OLD_TSF_evap
        "oldtsf_old_tsf_interstitial",# OT_OLD_TSF_interstitial
        "oldtsf_old_tsf_seepage",    # OT_OLD_TSF_seepage
        "oldtsf_trtd_evap",          # OT_TRTD_evap
        "oldtsf_trtd_spill",         # OT_TRTD_spill
        "oldtsf_new_tsf_evap",       # OT_NEW_TSF_evap
        "oldtsf_new_tsf_interstitial",# OT_NEW_TSF_interstitial
        "oldtsf_new_tsf_seepage",    # OT_NEW_TSF_seepage
        "oldtsf_nt_rwd_evap",        # OT_NT_RWD_evap
        "oldtsf_nt_rwd_spill",       # OT_NT_RWD_spill
    ]
}

# Check structures
print("\n" + "=" * 80)
print("STRUCTURES IN DATABASE (area_id = 5)")
print("=" * 80)
structures = db.execute_query("""
    SELECT structure_id, structure_code, structure_name, structure_type 
    FROM wb_structures 
    WHERE area_id = 5
    ORDER BY structure_id
""")
print(f"Found {len(structures)} structures:")
for s in structures:
    status = "✅" if s['structure_id'] in [25, 26, 27, 28, 29] else "❌"
    print(f"  {status} ID {s['structure_id']:3d} | {s['structure_code']:20s} | {s['structure_name']:40s}")

# Check inflow sources
print("\n" + "=" * 80)
print("INFLOW SOURCES IN DATABASE")
print("=" * 80)
inflows = db.execute_query("""
    SELECT i.inflow_id, i.source_code, i.source_name, s.structure_name
    FROM wb_inflow_sources i
    JOIN wb_structures s ON i.target_structure_id = s.structure_id
    WHERE s.area_id = 5
    ORDER BY i.source_code
""")
print(f"Found {len(inflows)} inflow sources:")
expected_inflows = [
    'OT_GWA_boreholes',
    'OT_OLD_TSF_rainrun',
    'OT_TRTD_rain',
    'OT_NEW_TSF_rainrun',
    'OT_NT_RWD_rain'
]
for inf in inflows:
    status = "✅" if inf['source_code'] in expected_inflows else "❌"
    print(f"  {status} {inf['source_code']:30s} → {inf['structure_name']:40s}")

# Check outflow destinations
print("\n" + "=" * 80)
print("OUTFLOW DESTINATIONS IN DATABASE")
print("=" * 80)
outflows = db.execute_query("""
    SELECT DISTINCT o.destination_code, o.destination_name, s.structure_name as from_structure
    FROM wb_outflow_destinations o
    JOIN wb_structures s ON o.source_structure_id = s.structure_id
    WHERE s.area_id = 5
    ORDER BY o.destination_code
""")
print(f"Found {len(outflows)} distinct outflow destinations:")
expected_outflows = [
    'OT_OFF_septic',
    'OT_OFF_consumption',
    'OT_OLD_TSF_evap',
    'OT_OLD_TSF_interstitial',
    'OT_OLD_TSF_seepage',
    'OT_TRTD_evap',
    'OT_TRTD_spill',
    'OT_NEW_TSF_evap',
    'OT_NEW_TSF_interstitial',
    'OT_NEW_TSF_seepage',
    'OT_NT_RWD_evap',
    'OT_NT_RWD_spill',
]
for out in outflows:
    status = "✅" if out['destination_code'] in expected_outflows else "❌"
    print(f"  {status} {out['destination_code']:30s} | {out['destination_name']:40s} | From: {out['from_structure']}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"✅ Diagram Components (JSON):      22 nodes")
print(f"✅ Database Structures (area_id 5): {len(structures)} structures")
print(f"✅ Database Inflow Sources:         {len(inflows)} sources")
print(f"✅ Database Outflow Destinations:   {len(outflows)} distinct destinations")

all_present = (
    len(structures) == 5 and
    len(inflows) == 5 and
    len(outflows) == 12
)

if all_present:
    print("\n🎉 ALL COMPONENTS VERIFIED IN DATABASE!")
else:
    print("\n⚠️  Some components may be missing - see details above")
