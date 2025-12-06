#!/usr/bin/env python3
"""Comprehensive topology analysis for duplicates, incomplete connections, and scientific validity."""
import sqlite3
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(__file__).parent.parent / "data" / "water_balance.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=" * 100)
print("COMPREHENSIVE TOPOLOGY ANALYSIS")
print("=" * 100)

# 1. Check for duplicate inter-area transfers
print("\n1️⃣  DUPLICATE INTER-AREA TRANSFERS CHECK")
print("-" * 100)
cur.execute("""
    SELECT 
        a1.area_code, s1.structure_code,
        a2.area_code, s2.structure_code,
        iat.flow_type, iat.subcategory,
        COUNT(*) as count,
        GROUP_CONCAT(iat.transfer_id) as ids
    FROM wb_inter_area_transfers iat
    JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
    JOIN wb_areas a2 ON iat.to_area_id = a2.area_id
    JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
    JOIN wb_structures s2 ON iat.to_structure_id = s2.structure_id
    GROUP BY a1.area_code, s1.structure_code, a2.area_code, s2.structure_code, iat.flow_type, iat.subcategory
    HAVING count > 1
    ORDER BY count DESC
""")
duplicates = cur.fetchall()
if duplicates:
    print(f"⚠️  FOUND {len(duplicates)} DUPLICATE INTER-AREA TRANSFER PATTERNS:\n")
    for row in duplicates:
        print(f"  {row[0]}/{row[1]} → {row[2]}/{row[3]} | {row[4]} ({row[5]}) - {row[6]} copies (IDs: {row[7]})")
else:
    print("✅ No duplicate inter-area transfers found")

# 2. Check for duplicate flow connections
print("\n\n2️⃣  DUPLICATE FLOW CONNECTIONS CHECK")
print("-" * 100)
cur.execute("""
    SELECT 
        s1.structure_code, s2.structure_code,
        fc.flow_type, fc.subcategory,
        COUNT(*) as count,
        GROUP_CONCAT(fc.connection_id) as ids
    FROM wb_flow_connections fc
    JOIN wb_structures s1 ON fc.from_structure_id = s1.structure_id
    JOIN wb_structures s2 ON fc.to_structure_id = s2.structure_id
    WHERE fc.is_internal = 1
    GROUP BY s1.structure_code, s2.structure_code, fc.flow_type, fc.subcategory
    HAVING count > 1
    ORDER BY count DESC
""")
flow_dups = cur.fetchall()
if flow_dups:
    print(f"⚠️  FOUND {len(flow_dups)} DUPLICATE FLOW CONNECTION PATTERNS:\n")
    for row in flow_dups:
        print(f"  {row[0]} → {row[1]} | {row[2]} ({row[3]}) - {row[4]} copies (IDs: {row[5]})")
else:
    print("✅ No duplicate flow connections found")

# 3. Check for bidirectional transfers that have both directions registered
print("\n\n3️⃣  BIDIRECTIONAL INTER-AREA TRANSFERS ANALYSIS")
print("-" * 100)
cur.execute("""
    SELECT 
        a1.area_code, s1.structure_code,
        a2.area_code, s2.structure_code,
        iat.flow_type, iat.is_bidirectional, iat.notes,
        COUNT(*) as count
    FROM wb_inter_area_transfers iat
    JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
    JOIN wb_areas a2 ON iat.to_area_id = a2.area_id
    JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
    JOIN wb_structures s2 ON iat.to_structure_id = s2.structure_id
    WHERE iat.is_bidirectional = 1
    GROUP BY a1.area_code, s1.structure_code, a2.area_code, s2.structure_code, iat.flow_type
    ORDER BY a1.area_code, s1.structure_code
""")
bidirectional = cur.fetchall()
print(f"Found {len(bidirectional)} bidirectional inter-area transfers:")
for row in bidirectional:
    print(f"  {row[0]}/{row[1]} ↔ {row[2]}/{row[3]} | {row[4]} (is_bidirectional={row[5]}) | {row[6]}")

# 4. Check for incomplete connections (one-way where there should be two-way)
print("\n\n4️⃣  POTENTIAL INCOMPLETE BIDIRECTIONAL CONNECTIONS")
print("-" * 100)
cur.execute("""
    SELECT 
        a1.area_code, s1.structure_code,
        a2.area_code, s2.structure_code,
        iat.flow_type,
        COUNT(DISTINCT CASE 
            WHEN iat.from_area_id = a1.area_id AND iat.to_area_id = a2.area_id THEN 1 
            ELSE NULL 
        END) as forward,
        COUNT(DISTINCT CASE 
            WHEN iat.from_area_id = a2.area_id AND iat.to_area_id = a1.area_id THEN 1 
            ELSE NULL 
        END) as backward
    FROM wb_inter_area_transfers iat
    JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
    JOIN wb_areas a2 ON iat.to_area_id = a2.area_id
    JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
    JOIN wb_structures s2 ON iat.to_structure_id = s2.structure_id
    WHERE iat.is_bidirectional = 1
    GROUP BY a1.area_code, s1.structure_code, a2.area_code, s2.structure_code, iat.flow_type
    HAVING forward = 1 XOR backward = 1
    ORDER BY a1.area_code, a2.area_code
""")
incomplete = cur.fetchall()
if incomplete:
    print(f"⚠️  FOUND {len(incomplete)} POTENTIALLY INCOMPLETE BIDIRECTIONAL CONNECTIONS:\n")
    for row in incomplete:
        dir_status = "→ only (missing ←)" if row[5] == 1 else "← only (missing →)"
        print(f"  {row[0]}/{row[1]} {dir_status} {row[2]}/{row[3]} | {row[4]}")
else:
    print("✅ All bidirectional connections have both directions registered")

# 5. Check each area's mass balance structure
print("\n\n5️⃣  AREA-BY-AREA INFLOW/OUTFLOW CONNECTIVITY ANALYSIS")
print("-" * 100)
cur.execute("SELECT area_id, area_code FROM wb_areas ORDER BY area_code")
areas = cur.fetchall()

for area_id, area_code in areas:
    print(f"\n📍 AREA: {area_code}")
    print("   " + "-" * 80)
    
    # Get structures in this area
    cur.execute("""
        SELECT structure_id, structure_code, structure_type
        FROM wb_structures
        WHERE area_id = ?
        ORDER BY structure_code
    """, (area_id,))
    structures = cur.fetchall()
    
    struct_map = {s[0]: (s[1], s[2]) for s in structures}
    
    # Check connectivity for each structure
    issues = []
    for struct_id, struct_code, struct_type in structures:
        # Get inflows (internal + external + inter-area)
        cur.execute("""
            SELECT COUNT(*) FROM wb_flow_connections 
            WHERE to_structure_id = ? AND is_internal = 1
        """, (struct_id,))
        internal_in = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) FROM wb_inflow_sources 
            WHERE target_structure_id = ?
        """, (struct_id,))
        external_in = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) FROM wb_inter_area_transfers 
            WHERE to_structure_id = ? AND to_area_id = ?
        """, (struct_id, area_id))
        interarea_in = cur.fetchone()[0]
        
        # Get outflows
        cur.execute("""
            SELECT COUNT(*) FROM wb_flow_connections 
            WHERE from_structure_id = ? AND is_internal = 1
        """, (struct_id,))
        internal_out = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) FROM wb_outflow_destinations 
            WHERE source_structure_id = ?
        """, (struct_id,))
        external_out = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) FROM wb_inter_area_transfers 
            WHERE from_structure_id = ? AND from_area_id = ?
        """, (struct_id, area_id))
        interarea_out = cur.fetchone()[0]
        
        total_in = internal_in + external_in + interarea_in
        total_out = internal_out + external_out + interarea_out
        
        # Flag issues
        if struct_type in ['reservoir', 'plant', 'treatment']:
            if total_in == 0 and total_out > 0:
                issues.append((struct_code, struct_type, f"⚠️  NO INFLOW but has {total_out} outflows"))
            if total_out == 0 and total_in > 0:
                issues.append((struct_code, struct_type, f"⚠️  NO OUTFLOW but has {total_in} inflows"))
        elif struct_type == 'building':
            if total_in == 0 and external_out == 0:
                issues.append((struct_code, struct_type, f"⚠️  ISOLATED - no inflow/outflow"))
    
    if issues:
        for code, stype, msg in issues:
            print(f"   {msg} | {code} ({stype})")
    else:
        print(f"   ✅ All structures have proper inflow/outflow connectivity")

# 6. Check dirty water trunk routing
print("\n\n6️⃣  DIRTY WATER TRUNK ANALYSIS (MPRWSD1 Hub)")
print("-" * 100)
cur.execute("""
    SELECT 
        a1.area_code, s1.structure_code,
        a2.area_code, s2.structure_code,
        iat.subcategory, iat.notes
    FROM wb_inter_area_transfers iat
    JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
    JOIN wb_areas a2 ON iat.to_area_id = a2.area_id
    JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
    JOIN wb_structures s2 ON iat.to_structure_id = s2.structure_id
    WHERE s2.structure_code = 'MPRWSD1' AND iat.flow_type = 'dirty'
    ORDER BY a1.area_code
""")
trunk_inputs = cur.fetchall()
print(f"MPRWSD1 receives dirty water from {len(trunk_inputs)} sources:")
for row in trunk_inputs:
    print(f"  ← {row[0]}/{row[1]} | {row[4]} | {row[5]}")

cur.execute("""
    SELECT 
        a1.area_code, s1.structure_code,
        a2.area_code, s2.structure_code,
        iat.subcategory, iat.notes
    FROM wb_inter_area_transfers iat
    JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
    JOIN wb_areas a2 ON iat.to_area_id = a2.area_id
    JOIN wb_structures s1 ON iat.from_structure_id = s1.structure_id
    JOIN wb_structures s2 ON iat.to_structure_id = s2.structure_id
    WHERE s1.structure_code = 'MPRWSD1' AND iat.flow_type = 'dirty'
    ORDER BY a2.area_code
""")
trunk_outputs = cur.fetchall()
print(f"\nMPRWSD1 discharges dirty water to {len(trunk_outputs)} destinations:")
for row in trunk_outputs:
    print(f"  → {row[2]}/{row[3]} | {row[4]} | {row[5]}")

# 7. Check for orphaned structures (no connections)
print("\n\n7️⃣  ORPHANED STRUCTURES CHECK")
print("-" * 100)
cur.execute("""
    SELECT 
        a.area_code,
        s.structure_code,
        s.structure_type,
        (SELECT COUNT(*) FROM wb_flow_connections fc 
         WHERE fc.from_structure_id = s.structure_id OR fc.to_structure_id = s.structure_id) as internal_connections,
        (SELECT COUNT(*) FROM wb_inflow_sources WHERE target_structure_id = s.structure_id) as inflow_count,
        (SELECT COUNT(*) FROM wb_outflow_destinations WHERE source_structure_id = s.structure_id) as outflow_count,
        (SELECT COUNT(*) FROM wb_inter_area_transfers 
         WHERE from_structure_id = s.structure_id OR to_structure_id = s.structure_id) as interarea_count
    FROM wb_structures s
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE (SELECT COUNT(*) FROM wb_flow_connections fc 
           WHERE fc.from_structure_id = s.structure_id OR fc.to_structure_id = s.structure_id) = 0
    AND (SELECT COUNT(*) FROM wb_inflow_sources WHERE target_structure_id = s.structure_id) = 0
    AND (SELECT COUNT(*) FROM wb_outflow_destinations WHERE source_structure_id = s.structure_id) = 0
    AND (SELECT COUNT(*) FROM wb_inter_area_transfers 
         WHERE from_structure_id = s.structure_id OR to_structure_id = s.structure_id) = 0
    ORDER BY a.area_code, s.structure_code
""")
orphaned = cur.fetchall()
if orphaned:
    print(f"⚠️  FOUND {len(orphaned)} ORPHANED STRUCTURES (no connections):\n")
    for row in orphaned:
        print(f"  {row[0]}/{row[1]} ({row[2]})")
else:
    print("✅ No orphaned structures found")

# 8. Check for double-counting risk (same water passing through multiple paths)
print("\n\n8️⃣  DOUBLE-COUNTING RISK ANALYSIS")
print("-" * 100)

# Check if any structure receives from same source via multiple paths
cur.execute("""
    SELECT 
        s_target.structure_code as target,
        s_from.structure_code as source,
        COUNT(*) as path_count,
        GROUP_CONCAT(DISTINCT fc.flow_type) as flow_types
    FROM wb_flow_connections fc
    JOIN wb_structures s_from ON fc.from_structure_id = s_from.structure_id
    JOIN wb_structures s_target ON fc.to_structure_id = s_target.structure_id
    WHERE fc.is_internal = 1
    GROUP BY s_target.structure_code, s_from.structure_code
    HAVING COUNT(*) > 1
    ORDER BY path_count DESC
""")
multi_paths = cur.fetchall()
if multi_paths:
    print(f"⚠️  FOUND {len(multi_paths)} MULTIPLE PATHS BETWEEN SAME STRUCTURES:\n")
    for row in multi_paths:
        print(f"  {row[1]} ⇉ {row[0]} has {row[2]} paths (flow types: {row[3]})")
else:
    print("✅ No multiple paths between same structures (good - prevents double-counting)")

# 9. Check inter-area transfer matrix for consistency
print("\n\n9️⃣  INTER-AREA TRANSFER MATRIX")
print("-" * 100)
cur.execute("""
    SELECT 
        a1.area_code,
        a2.area_code,
        COUNT(*) as transfer_count,
        SUM(CASE WHEN iat.flow_type = 'dirty' THEN 1 ELSE 0 END) as dirty_count,
        SUM(CASE WHEN iat.flow_type = 'clean' THEN 1 ELSE 0 END) as clean_count,
        SUM(CASE WHEN iat.flow_type = 'loss' THEN 1 ELSE 0 END) as loss_count
    FROM wb_inter_area_transfers iat
    JOIN wb_areas a1 ON iat.from_area_id = a1.area_id
    JOIN wb_areas a2 ON iat.to_area_id = a2.area_id
    GROUP BY a1.area_code, a2.area_code
    ORDER BY a1.area_code, a2.area_code
""")
transfers = cur.fetchall()
matrix_data = defaultdict(dict)
for row in transfers:
    from_area, to_area = row[0], row[1]
    matrix_data[from_area][to_area] = (row[2], row[3], row[4], row[5])

all_areas = sorted(set([row[0] for row in areas]))
all_areas_codes = sorted([row[1] for row in areas])

print(f"\nTransfers between areas (total, dirty, clean, loss):")
print(f"FROM \\ TO      | {' | '.join(f'{a:12}' for a in all_areas_codes)}")
print("               " + "|" + "-" * 12 * len(all_areas_codes))
for from_area in all_areas_codes:
    row_data = []
    for to_area in all_areas_codes:
        if from_area == to_area:
            row_data.append("   -      ")
        elif (from_area, to_area) in [(r[0], r[1]) for r in transfers]:
            for transfer_row in transfers:
                if transfer_row[0] == from_area and transfer_row[1] == to_area:
                    count = transfer_row[2]
                    row_data.append(f" T:{count}  ")
                    break
        else:
            row_data.append("   -      ")
    print(f"{from_area:12} | {' | '.join(row_data)}")

# 10. Summary statistics
print("\n\n🔟 SUMMARY STATISTICS")
print("-" * 100)
cur.execute("SELECT COUNT(*) FROM wb_areas")
area_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM wb_structures")
struct_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM wb_flow_connections")
flow_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM wb_inter_area_transfers")
interarea_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM wb_inflow_sources")
inflow_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM wb_outflow_destinations")
outflow_count = cur.fetchone()[0]

print(f"Total Areas: {area_count}")
print(f"Total Structures: {struct_count}")
print(f"Total Flow Connections: {flow_count}")
print(f"Total Inter-area Transfers: {interarea_count}")
print(f"Total Inflow Sources: {inflow_count}")
print(f"Total Outflow Destinations: {outflow_count}")

cur.execute("SELECT COUNT(*) FROM wb_inter_area_transfers WHERE is_bidirectional = 1")
bidi_count = cur.fetchone()[0]
print(f"Bidirectional Inter-area Transfers: {bidi_count}")

cur.execute("SELECT COUNT(*) FROM wb_inter_area_transfers WHERE flow_type = 'dirty'")
dirty_count = cur.fetchone()[0]
print(f"Dirty inter-area transfers: {dirty_count} (all bidirectional: {dirty_count == bidi_count})")

print("\n" + "=" * 100)
print("END OF ANALYSIS")
print("=" * 100)

conn.close()
