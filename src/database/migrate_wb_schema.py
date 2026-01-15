"""
New area-based topology schema for Water Balance.

This migration creates wb_* tables to register areas, structures,
and flow connections. It also seeds the UG2 North Decline Area topology.

Notes:
- This schema is topology-only. Monthly values remain in Excel.
- A measurement mapping table is included to link Excel series codes
  to structures or flow connections for calculations.
- Legacy tables are preserved; archiving can be handled separately.
"""

from pathlib import Path
import sqlite3
from typing import Optional


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "water_balance.db"


DDL_STATEMENTS = [
    # Areas
    """
    CREATE TABLE IF NOT EXISTS wb_areas (
        area_id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_code TEXT UNIQUE NOT NULL,
        area_name TEXT NOT NULL,
        description TEXT
    );
    """,

    # Structures (dams, reservoirs, plants, declines, buildings, tailings, etc.)
    """
    CREATE TABLE IF NOT EXISTS wb_structures (
        structure_id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_id INTEGER NOT NULL,
        structure_code TEXT UNIQUE NOT NULL,
        structure_name TEXT NOT NULL,
        structure_type TEXT NOT NULL, -- reservoir|storage_group|storage_member|treatment|decline|building|tsf|plant|stockpile
        is_group BOOLEAN DEFAULT 0,   -- true if this is a grouped storage (e.g., NDCD group)
        parent_structure_id INTEGER,  -- for storage members inside a group
        notes TEXT,
        FOREIGN KEY(area_id) REFERENCES wb_areas(area_id)
    );
    """,

    # Flow connections (topology edges)
    """
    CREATE TABLE IF NOT EXISTS wb_flow_connections (
        connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_structure_id INTEGER NOT NULL,
        to_structure_id INTEGER NOT NULL,
        flow_type TEXT NOT NULL,      -- clean|dirty|loss
        subcategory TEXT,             -- effluent|ug_return|runoff|dewatering|irrigation|septic|consumption|spill|dust|evaporation|losses
        is_bidirectional BOOLEAN DEFAULT 0,
        is_internal BOOLEAN DEFAULT 1, -- if true, internal circulation (not counted as area inflow/outflow)
        notes TEXT,
        FOREIGN KEY(from_structure_id) REFERENCES wb_structures(structure_id),
        FOREIGN KEY(to_structure_id) REFERENCES wb_structures(structure_id)
    );
    """,

    # Inflow sources (registration of boreholes, direct rainfall, etc.)
    """
    CREATE TABLE IF NOT EXISTS wb_inflow_sources (
        inflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_structure_id INTEGER NOT NULL, -- destination node (e.g., softening plant or reservoir)
        source_type TEXT NOT NULL,            -- borehole|rainfall
        source_code TEXT NOT NULL,            -- stable code used in Excel mapping
        source_name TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY(target_structure_id) REFERENCES wb_structures(structure_id)
    );
    """,

    # Outflow destinations (registration of where water leaves the area/system)
    """
    CREATE TABLE IF NOT EXISTS wb_outflow_destinations (
        outflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_structure_id INTEGER NOT NULL, -- node where outflow originates
        destination_type TEXT NOT NULL,       -- septic|consumption|losses|spill|dust|evaporation
        destination_code TEXT NOT NULL,       -- stable code used in Excel mapping
        destination_name TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY(source_structure_id) REFERENCES wb_structures(structure_id)
    );
    """,

    # Inter-area transfers (edges crossing areas for dirty/clean flows)
    """
    CREATE TABLE IF NOT EXISTS wb_inter_area_transfers (
        transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_area_id INTEGER NOT NULL,
        to_area_id INTEGER NOT NULL,
        from_structure_id INTEGER,
        to_structure_id INTEGER,
        flow_type TEXT NOT NULL,     -- clean|dirty|loss
        subcategory TEXT,            -- effluent|ug_return|runoff|dewatering|irrigation|dam_transfer|plant_discharge|trunk_feed
        is_bidirectional BOOLEAN DEFAULT 0, -- true if flow can go both directions (direction determined by Excel values)
        notes TEXT,
        FOREIGN KEY(from_area_id) REFERENCES wb_areas(area_id),
        FOREIGN KEY(to_area_id) REFERENCES wb_areas(area_id),
        FOREIGN KEY(from_structure_id) REFERENCES wb_structures(structure_id),
        FOREIGN KEY(to_structure_id) REFERENCES wb_structures(structure_id)
    );
    """,

    # Excel measurement mapping (links Excel series codes to topology elements)
    """
    CREATE TABLE IF NOT EXISTS wb_measurement_map (
        map_id INTEGER PRIMARY KEY AUTOINCREMENT,
        excel_series_code TEXT NOT NULL UNIQUE, -- e.g., NDGWA1_borehole_m3, offices_consumption_m3
        target_type TEXT NOT NULL,              -- structure|flow|inflow|outflow
        target_id INTEGER NOT NULL,             -- FK to respective table
        notes TEXT
    );
    """,

    # Indexes for performance
    """
    CREATE INDEX IF NOT EXISTS idx_wb_structures_area ON wb_structures(area_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_wb_flows_from_to ON wb_flow_connections(from_structure_id, to_structure_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_wb_inflows_target ON wb_inflow_sources(target_structure_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_wb_outflows_source ON wb_outflow_destinations(source_structure_id);
    """,
]


def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def migrate():
    conn = connect()
    try:
        cur = conn.cursor()
        for ddl in DDL_STATEMENTS:
            cur.executescript(ddl)
        conn.commit()
    finally:
        conn.close()


def seed_ug2_north_decline_area():
    """Seed topology for UG2 North Decline Area as per provided diagram.

    Structures:
    - Reservoir (area-scoped)
    - Guest House (building)
    - Offices (building)
    - Softening Plant (treatment)
    - Sewage Treatment (treatment)
    - North Decline Shaft Area (decline)
    - North Decline (decline)
    - NDCD Grouped Dam (storage_group: NDCD 1-2 + NDSWD 1)

    Flows (one-way unless noted):
    - Boreholes -> Softening Plant (clean)
    - Softening Plant -> Reservoir (clean)
    - Reservoir -> Guest House (clean)
    - Reservoir -> Offices (clean)
    - Offices -> Sewage Treatment (clean)
    - Sewage Treatment -> NDCD Group (dirty, effluent)
    - North Decline Shaft Area -> NDCD Group (dirty, runoff)
    - North Decline -> NDCD Group (dirty, dewatering)
    - NDCD Group -> North Decline (dirty, ug_return) [bidirectional with dewatering]

    Outflows attached to nodes:
    - Softening Plant: losses
    - Sewage Treatment: losses
    - NDCD Group: spill, evaporation, dust suppression
    - Guest House: consumption, septic, losses
    - Offices: consumption
    """

    conn = connect()
    try:
        cur = conn.cursor()

        # Insert area
        cur.execute(
            "INSERT OR IGNORE INTO wb_areas (area_code, area_name, description) VALUES (?, ?, ?)",
            ("UG2_NORTH", "UG2 North Decline Area", "UG2 North area topology")
        )
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("UG2_NORTH",))
        area_id = cur.fetchone()[0]

        # Insert structures
        structures = [
            ("UG2N_RES", "Reservoir", "reservoir", 0, None, "Area-scoped reservoir"),
            ("UG2N_GH", "Guest House", "building", 0, None, "Guest house building"),
            ("UG2N_OFF", "Offices", "building", 0, None, "Office building"),
            ("UG2N_SOFT", "Softening Plant", "treatment", 0, None, "Water softening plant"),
            ("UG2N_STP", "Sewage Treatment", "treatment", 0, None, "Sewage treatment plant"),
            ("UG2N_NDSA", "North Decline Shaft Area", "decline", 0, None, "Decline shaft area"),
            ("UG2N_ND", "North Decline", "decline", 0, None, "North decline"),
            ("UG2N_NDCDG", "NDCD Group (NDCD1-2 + NDSWD1)", "storage_group", 1, None, "Grouped dam node"),
        ]

        for code, name, s_type, is_group, parent_id, notes in structures:
            cur.execute(
                "INSERT OR IGNORE INTO wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (area_id, code, name, s_type, is_group, parent_id, notes)
            )

        # Helper to get structure_id by code
        def sid(code: str) -> int:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", (code,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Structure not found: {code}")
            return row[0]

        # Flow connections
        flows = [
            # Clean inflow chain
            (sid("UG2N_SOFT"), sid("UG2N_RES"), "clean", None, 0, 1, "Softening Plant -> Reservoir"),
            (sid("UG2N_RES"), sid("UG2N_GH"), "clean", None, 0, 1, "Reservoir -> Guest House"),
            (sid("UG2N_RES"), sid("UG2N_OFF"), "clean", None, 0, 1, "Reservoir -> Offices"),
            (sid("UG2N_OFF"), sid("UG2N_STP"), "clean", None, 0, 1, "Offices -> Sewage Treatment"),

            # Dirty water connections to NDCD group
            (sid("UG2N_STP"), sid("UG2N_NDCDG"), "dirty", "effluent", 0, 1, "STP effluent -> NDCD Group"),
            (sid("UG2N_NDSA"), sid("UG2N_NDCDG"), "dirty", "runoff", 0, 1, "Shaft Area runoff -> NDCD Group"),
            (sid("UG2N_ND"), sid("UG2N_NDCDG"), "dirty", "dewatering", 0, 1, "North Decline dewatering -> NDCD Group"),

            # Bidirectional UG Return: NDCD -> North Decline
            (sid("UG2N_NDCDG"), sid("UG2N_ND"), "dirty", "ug_return", 0, 1, "NDCD Group -> North Decline (UG Return)"),
        ]

        for f_from, f_to, f_type, subcat, bidir, internal, notes in flows:
            cur.execute(
                "INSERT INTO wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_from, f_to, f_type, subcat, bidir, internal, notes)
            )

        # Inflow sources registration (topology only; values in Excel)
        inflows = [
            # Boreholes feed Softening Plant
            (sid("UG2N_SOFT"), "borehole", "NDGWA_boreholes", "NDGWA Boreholes", "NDGWA 1-6 abstraction to softening"),
            # Direct rainfall to NDCD group (area reservoirs/dams receive rainfall)
            (sid("UG2N_NDCDG"), "rainfall", "UG2N_NDCD_rainfall", "Direct Rainfall to NDCD Group", "Rainfall onto NDCD/NDSWD surfaces"),
        ]

        for target_sid, s_type, s_code, s_name, notes in inflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (target_sid, s_type, s_code, s_name, notes)
            )

        # Outflow destinations registration
        outflows = [
            (sid("UG2N_SOFT"), "losses", "UG2N_SOFT_losses", "Softening Plant Losses", "Process losses at softening"),
            (sid("UG2N_STP"), "losses", "UG2N_STP_losses", "Sewage Treatment Losses", "Process losses at sewage treatment"),
            (sid("UG2N_GH"), "septic", "UG2N_GH_septic", "Guest House Septic Tank", "Septic tank outflow"),
            (sid("UG2N_GH"), "consumption", "UG2N_GH_consumption", "Guest House Consumption", "Water consumption"),
            (sid("UG2N_GH"), "losses", "UG2N_GH_losses", "Guest House Losses", "Guest house water losses"),
            (sid("UG2N_OFF"), "consumption", "UG2N_OFF_consumption", "Offices Consumption", "Offices water consumption"),
            (sid("UG2N_NDCDG"), "spill", "UG2N_NDCD_spill", "NDCD Group Spill", "Dam spill"),
            (sid("UG2N_NDCDG"), "evaporation", "UG2N_NDCD_evap", "NDCD Group Evaporation", "Evaporation from dam surfaces"),
            (sid("UG2N_NDCDG"), "dust", "UG2N_NDCD_dust", "NDCD Group Dust Suppression", "Dust suppression usage"),
        ]

        for source_sid, d_type, d_code, d_name, notes in outflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (source_sid, d_type, d_code, d_name, notes)
            )

        conn.commit()
    finally:
        conn.close()


def seed_merensky_north_area():
    """Seed topology for Merensky North Area.

    Structures:
    - Softening Plant (treatment)
    - Offices (building)
    - Merensky North Decline Shaft Area (decline)
    - Merensky North Decline (decline)
    - NDCD 3-4 & NDSWD 2 Group (storage_group)

    Flows:
    - Boreholes -> Softening Plant (clean)
    - Softening Plant -> Offices (clean, direct - no reservoir)
    - Offices -> UG2 North Sewage Treatment (dirty, inter-area)
    - Merensky North Decline Shaft Area -> NDCD 3-4 (dirty, runoff)
    - Merensky North Decline -> NDCD 3-4 (dirty, dewatering)
    - NDCD 3-4 -> Merensky North Decline (dirty, ug_return)
    - NDCD 3-4 -> Dirty Water Trunk (inter-area outflow)
    - NDCD 3-4 loop (dam_return - internal recirculation)

    Outflows:
    - Softening Plant: losses
    - Offices: consumption
    - NDCD 3-4: spill, evaporation, dust suppression
    """

    conn = connect()
    try:
        cur = conn.cursor()

        # Insert area
        cur.execute(
            "INSERT OR IGNORE INTO wb_areas (area_code, area_name, description) VALUES (?, ?, ?)",
            ("MER_NORTH", "Merensky North Area", "Merensky North area topology")
        )
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_NORTH",))
        area_id = cur.fetchone()[0]

        # Insert structures
        structures = [
            ("MERN_SOFT", "Softening Plant", "treatment", 0, None, "Water softening plant"),
            ("MERN_OFF", "Offices", "building", 0, None, "Office building"),
            ("MERN_NDSA", "Merensky North Decline Shaft Area", "decline", 0, None, "Decline shaft area"),
            ("MERN_ND", "Merensky North Decline", "decline", 0, None, "Merensky north decline"),
            ("MERN_NDCDG", "NDCD 3-4 & NDSWD 2 Group", "storage_group", 1, None, "Grouped dam node"),
        ]

        for code, name, s_type, is_group, parent_id, notes in structures:
            cur.execute(
                "INSERT OR IGNORE INTO wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (area_id, code, name, s_type, is_group, parent_id, notes)
            )

        # Helper to get structure_id by code
        def sid(code: str) -> int:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", (code,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Structure not found: {code}")
            return row[0]

        # Flow connections
        flows = [
            # Clean water chain
            (sid("MERN_SOFT"), sid("MERN_OFF"), "clean", None, 0, 1, "Softening Plant -> Offices (direct)"),

            # Dirty water connections to NDCD 3-4
            (sid("MERN_NDSA"), sid("MERN_NDCDG"), "dirty", "runoff", 0, 1, "Shaft Area runoff -> NDCD 3-4"),
            (sid("MERN_ND"), sid("MERN_NDCDG"), "dirty", "dewatering", 0, 1, "Merensky North Decline dewatering -> NDCD 3-4"),

            # Bidirectional UG Return
            (sid("MERN_NDCDG"), sid("MERN_ND"), "dirty", "ug_return", 0, 1, "NDCD 3-4 -> Merensky North Decline (UG Return)"),

            # Dam return loop (internal recirculation)
            (sid("MERN_NDCDG"), sid("MERN_NDCDG"), "clean", "dam_return", 0, 1, "NDCD 3-4 internal loop (recirculation)"),
        ]

        for f_from, f_to, f_type, subcat, bidir, internal, notes in flows:
            cur.execute(
                "INSERT INTO wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_from, f_to, f_type, subcat, bidir, internal, notes)
            )

        # Inflow sources
        inflows = [
            (sid("MERN_SOFT"), "borehole", "MOGWA_boreholes", "MOGWA Boreholes", "MOGWA 1-2 abstraction to softening"),
            (sid("MERN_NDCDG"), "rainfall", "MERN_NDCD_rainfall", "Direct Rainfall to NDCD 3-4", "Rainfall onto NDCD 3-4/NDSWD 2 surfaces"),
        ]

        for target_sid, s_type, s_code, s_name, notes in inflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (target_sid, s_type, s_code, s_name, notes)
            )

        # Outflow destinations
        outflows = [
            (sid("MERN_SOFT"), "losses", "MERN_SOFT_losses", "Softening Plant Losses", "Process losses at softening"),
            (sid("MERN_OFF"), "consumption", "MERN_OFF_consumption", "Offices Consumption", "Offices water consumption"),
            (sid("MERN_NDCDG"), "spill", "MERN_NDCD_spill", "NDCD 3-4 Spill", "Dam spill"),
            (sid("MERN_NDCDG"), "evaporation", "MERN_NDCD_evap", "NDCD 3-4 Evaporation", "Evaporation from dam surfaces"),
            (sid("MERN_NDCDG"), "dust", "MERN_NDCD_dust", "NDCD 3-4 Dust Suppression", "Dust suppression usage"),
        ]

        for source_sid, d_type, d_code, d_name, notes in outflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (source_sid, d_type, d_code, d_name, notes)
            )

        # Inter-area transfer: Offices -> UG2 North Sewage Treatment
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("UG2_NORTH",))
        ug2_north_area = cur.fetchone()
        if ug2_north_area:
            ug2_north_area_id = ug2_north_area[0]
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("UG2N_STP",))
            ug2n_stp = cur.fetchone()
            if ug2n_stp:
                ug2n_stp_id = ug2n_stp[0]
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, ug2_north_area_id, sid("MERN_OFF"), ug2n_stp_id, "dirty", "wastewater", 1, "Merensky North Offices wastewater -> UG2 North Sewage Treatment")
                )

        # Inter-area transfer: NDCD 3-4 group -> MPRWSD1 (dirty trunk)
        # This connects the Merensky North NDCD 3-4 grouped dam to the inter-area dirty line
        # UG2N_NDCDG -> MPRWSD1, by registering NDCD 3-4 -> MPRWSD1 directly.
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_PLANT",))
        mer_plant_area = cur.fetchone()
        if mer_plant_area:
            mer_plant_area_id = mer_plant_area[0]
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("MPRWSD1",))
            mprwsd1 = cur.fetchone()
            if mprwsd1:
                mprwsd1_id = mprwsd1[0]
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, mer_plant_area_id, sid("MERN_NDCDG"), mprwsd1_id, "dirty", "dam_transfer", 1, "NDCD 3-4 -> MPRWSD1 (dirty trunk connection)")
                )

        conn.commit()
    finally:
        conn.close()


def seed_stockpile_area():
    """Seed topology for Stockpile Area.

    Structures:
    - Stockpile Area (stockpile - surface area receiving rainfall, generating runoff/seepage)
    - Offices (building)
    - SPCD 1 (storage_group)
    - Septic Tank (treatment)

    Flows:
    - Boreholes -> Offices (clean)
    - Offices -> Septic Tank <-> SPCD 1 (bidirectional dirty water)
    - Direct Rainfall -> Stockpile Area
    - Direct Rainfall -> SPCD 1
    - Stockpile Area -> SPCD 1 (runoff)
    - Stockpile Area -> SPCD 1 (seepage)
    - Stockpile Area loop (internal recirculation)
    - SPCD 1 loop (dam return)

    Outflows:
    - Stockpile Area: evaporation
    - Offices: consumption
    - SPCD 1: evaporation, spill, dust suppression
    """

    conn = connect()
    try:
        cur = conn.cursor()

        # Insert area
        cur.execute(
            "INSERT OR IGNORE INTO wb_areas (area_code, area_name, description) VALUES (?, ?, ?)",
            ("STOCKPILE", "Stockpile Area", "Stockpile area topology")
        )
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("STOCKPILE",))
        area_id = cur.fetchone()[0]

        # Insert structures
        structures = [
            ("STP_STOCK", "Stockpile Area", "stockpile", 0, None, "Surface stockpile area - receives rainfall, generates runoff/seepage/evaporation"),
            ("STP_OFF", "Offices", "building", 0, None, "Office building"),
            ("STP_SPCD1", "SPCD 1", "storage_group", 1, None, "SPCD 1 dam"),
            ("STP_SEPTIC", "Septic Tank", "treatment", 0, None, "Septic tank treatment"),
        ]

        for code, name, s_type, is_group, parent_id, notes in structures:
            cur.execute(
                "INSERT OR IGNORE INTO wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (area_id, code, name, s_type, is_group, parent_id, notes)
            )

        # Helper to get structure_id by code
        def sid(code: str) -> int:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", (code,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Structure not found: {code}")
            return row[0]

        # Flow connections
        flows = [
            # Clean water
            # Boreholes go directly to Offices (registered as inflow below)

            # Dirty water: Offices -> Septic Tank <-> SPCD 1 (bidirectional)
            (sid("STP_OFF"), sid("STP_SEPTIC"), "dirty", "wastewater", 0, 1, "Offices -> Septic Tank"),
            (sid("STP_SEPTIC"), sid("STP_SPCD1"), "dirty", "effluent", 1, 1, "Septic Tank <-> SPCD 1 (bidirectional)"),

            # Stockpile Area dirty flows to SPCD 1
            (sid("STP_STOCK"), sid("STP_SPCD1"), "dirty", "runoff", 0, 1, "Stockpile runoff -> SPCD 1"),
            (sid("STP_STOCK"), sid("STP_SPCD1"), "dirty", "seepage", 0, 1, "Stockpile seepage -> SPCD 1"),

            # Internal recirculation loops
            (sid("STP_STOCK"), sid("STP_STOCK"), "dirty", "area_return", 0, 1, "Stockpile Area internal loop"),
            (sid("STP_SPCD1"), sid("STP_SPCD1"), "clean", "dam_return", 0, 1, "SPCD 1 dam return loop"),
        ]

        for f_from, f_to, f_type, subcat, bidir, internal, notes in flows:
            cur.execute(
                "INSERT INTO wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_from, f_to, f_type, subcat, bidir, internal, notes)
            )

        # Inflow sources
        inflows = [
            (sid("STP_OFF"), "borehole", "SPGWA_boreholes", "SPGWA Boreholes", "SPGWA 1-2 abstraction to offices"),
            (sid("STP_STOCK"), "rainfall", "STP_STOCK_rainfall", "Direct Rainfall to Stockpile", "Rainfall onto stockpile area"),
            (sid("STP_SPCD1"), "rainfall", "STP_SPCD1_rainfall", "Direct Rainfall to SPCD 1", "Rainfall onto SPCD 1 dam surface"),
        ]

        for target_sid, s_type, s_code, s_name, notes in inflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (target_sid, s_type, s_code, s_name, notes)
            )

        # Outflow destinations
        outflows = [
            (sid("STP_STOCK"), "evaporation", "STP_STOCK_evap", "Stockpile Area Evaporation", "Evaporation from stockpile surface"),
            (sid("STP_OFF"), "consumption", "STP_OFF_consumption", "Offices Consumption", "Offices water consumption"),
            (sid("STP_OFF"), "septic", "STP_OFF_septic", "Offices Septic Tank", "Septic tank outflow"),
            (sid("STP_SPCD1"), "evaporation", "STP_SPCD1_evap", "SPCD 1 Evaporation", "Evaporation from SPCD 1 dam"),
            (sid("STP_SPCD1"), "spill", "STP_SPCD1_spill", "SPCD 1 Spill", "SPCD 1 dam spill"),
            (sid("STP_SPCD1"), "dust", "STP_SPCD1_dust", "SPCD 1 Dust Suppression", "Dust suppression from SPCD 1"),
        ]

        for source_sid, d_type, d_code, d_name, notes in outflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (source_sid, d_type, d_code, d_name, notes)
            )

        conn.commit()
    finally:
        conn.close()


def seed_ug2_south_decline_area():
    """Seed topology for UG2 Main Decline Area.

    Structures:
    - Softening Plant (treatment)
    - Reservoir (reservoir)
    - Offices (building)
    - Sewage Treatment (treatment)
    - South Decline Shaft Area (decline)
    - South Decline (decline)
    - MDCD 1-4 (storage_group)

    Flows:
    - Boreholes -> Softening Plant (clean)
    - Softening Plant -> Reservoir (clean)
    - Reservoir -> Offices (clean)
    - Offices -> Sewage Treatment (clean) - wastewater
    - Sewage Treatment -> MDCD 1-4 (dirty, effluent)
    - South Decline Shaft Area -> MDCD 1-4 (dirty, runoff)
    - South Decline -> MDCD 1-4 (dirty, dewatering)
    - MDCD 1-4 -> South Decline (dirty, ug_return)
    - MDCD 1-4 loop (dam_return)
    - Inter-area: Runoff from another area -> MDCD 1-4
    - Inter-area: MDCD 1-4 -> Dirty water trunk (173,634)

    Outflows:
    - Softening Plant: losses
    - Sewage Treatment: losses
    - Offices: consumption
    - MDCD 1-4: spill, evaporation, dust suppression
    """

    conn = connect()
    try:
        cur = conn.cursor()

        # Insert area
        cur.execute(
            "INSERT OR IGNORE INTO wb_areas (area_code, area_name, description) VALUES (?, ?, ?)",
            ("UG2_SOUTH", "UG2 Main Decline Area", "UG2 South area topology")
        )
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("UG2_SOUTH",))
        area_id = cur.fetchone()[0]

        # Insert structures
        structures = [
            ("UG2S_SOFT", "Softening Plant", "treatment", 0, None, "Water softening plant"),
            ("UG2S_RES", "Reservoir", "reservoir", 0, None, "Area-scoped reservoir"),
            ("UG2S_OFF", "Offices", "building", 0, None, "Office building"),
            ("UG2S_STP", "Sewage Treatment", "treatment", 0, None, "Sewage treatment plant"),
            ("UG2S_SDSA", "South Decline Shaft Area", "decline", 0, None, "South decline shaft area"),
            ("UG2S_SD", "South Decline", "decline", 0, None, "South decline"),
            ("UG2S_MDCDG", "MDCD 1-4", "storage_group", 1, None, "MDCD 1-4 grouped dam"),
        ]

        for code, name, s_type, is_group, parent_id, notes in structures:
            cur.execute(
                "INSERT OR IGNORE INTO wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (area_id, code, name, s_type, is_group, parent_id, notes)
            )

        # Helper to get structure_id by code
        def sid(code: str) -> int:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", (code,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Structure not found: {code}")
            return row[0]

        # Flow connections
        flows = [
            # Clean water chain
            (sid("UG2S_SOFT"), sid("UG2S_RES"), "clean", None, 0, 1, "Softening Plant -> Reservoir"),
            (sid("UG2S_RES"), sid("UG2S_OFF"), "clean", None, 0, 1, "Reservoir -> Offices"),
            (sid("UG2S_OFF"), sid("UG2S_STP"), "clean", None, 0, 1, "Offices -> Sewage Treatment (wastewater)"),

            # Dirty water to MDCD 1-4
            (sid("UG2S_STP"), sid("UG2S_MDCDG"), "dirty", "effluent", 0, 1, "Sewage Treatment effluent -> MDCD 1-4"),
            (sid("UG2S_SDSA"), sid("UG2S_MDCDG"), "dirty", "runoff", 0, 1, "South Decline Shaft Area runoff -> MDCD 1-4"),
            (sid("UG2S_SD"), sid("UG2S_MDCDG"), "dirty", "dewatering", 0, 1, "South Decline dewatering -> MDCD 1-4"),

            # Bidirectional UG Return
            (sid("UG2S_MDCDG"), sid("UG2S_SD"), "dirty", "ug_return", 0, 1, "MDCD 1-4 -> South Decline (UG Return)"),

            # Dam return loop
            (sid("UG2S_MDCDG"), sid("UG2S_MDCDG"), "clean", "dam_return", 0, 1, "MDCD 1-4 dam return loop"),
        ]

        for f_from, f_to, f_type, subcat, bidir, internal, notes in flows:
            cur.execute(
                "INSERT INTO wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_from, f_to, f_type, subcat, bidir, internal, notes)
            )

        # Inflow sources
        inflows = [
            (sid("UG2S_SOFT"), "borehole", "MGDWA_boreholes", "MGDWA Boreholes", "MGDWA 1-6 abstraction to softening"),
            (sid("UG2S_MDCDG"), "rainfall", "UG2S_MDCD_rainfall", "Direct Rainfall to MDCD 1-4", "Rainfall onto MDCD 1-4 surfaces"),
        ]

        for target_sid, s_type, s_code, s_name, notes in inflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (target_sid, s_type, s_code, s_name, notes)
            )

        # Outflow destinations
        outflows = [
            (sid("UG2S_SOFT"), "losses", "UG2S_SOFT_losses", "Softening Plant Losses", "Process losses at softening"),
            (sid("UG2S_STP"), "losses", "UG2S_STP_losses", "Sewage Treatment Losses", "Process losses at sewage treatment"),
            (sid("UG2S_OFF"), "consumption", "UG2S_OFF_consumption", "Offices Consumption", "Offices water consumption"),
            (sid("UG2S_MDCDG"), "spill", "UG2S_MDCD_spill", "MDCD 1-4 Spill", "Dam spill"),
            (sid("UG2S_MDCDG"), "evaporation", "UG2S_MDCD_evap", "MDCD 1-4 Evaporation", "Evaporation from dam surfaces"),
            (sid("UG2S_MDCDG"), "dust", "UG2S_MDCD_dust", "MDCD 1-4 Dust Suppression", "Dust suppression usage"),
        ]

        for source_sid, d_type, d_code, d_name, notes in outflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (source_sid, d_type, d_code, d_name, notes)
            )

        # Inter-area transfer: MDCD 1-4 → MPRWSD1 (dirty trunk)
        # This connects UG2 South MDCD 1-4 to the dirty water trunk (same trunk as UG2N_NDCDG and MERN_NDCDG)
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_PLANT",))
        mer_plant_area = cur.fetchone()
        if mer_plant_area:
            mer_plant_area_id = mer_plant_area[0]
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("MPRWSD1",))
            mprwsd1 = cur.fetchone()
            if mprwsd1:
                mprwsd1_id = mprwsd1[0]
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, mer_plant_area_id, sid("UG2S_MDCDG"), mprwsd1_id, "dirty", "dam_transfer", 1, "MDCD 1-4 -> MPRWSD1 (dirty trunk connection)")
                )

        conn.commit()
    finally:
        conn.close()


def seed_merensky_south_area():
    """Seed topology for Merensky South Area.

    Structures:
    - Softening Plant (treatment)
    - Offices (building)
    - Merensky South Decline Shaft Area (decline)
    - Merensky South Decline (decline)
    - MDCD 5-6 (storage_group)

    Flows:
    - Boreholes -> Softening Plant -> Offices (clean, direct - no reservoir)
    - Merensky South Decline -> MDCD 5-6 (dirty, dewatering)
    - MDCD 5-6 -> Merensky South Decline (dirty, ug_return)
    - MDCD 5-6 loop (dam_return)
    
    Inter-area:
    - Offices -> UG2 South Sewage Treatment (983) - dirty wastewater
    - Merensky South Decline Shaft Area -> UG2 South MDCD 1-4 (1,832) - runoff
    - MDCD 5-6 -> UG2 South MDCD 1-4 (dirty water connection)
    - MDCD 5-6 -> Dirty water trunk (21,371)

    Outflows:
    - Softening Plant: losses
    - Offices: consumption
    - MDCD 5-6: spill, evaporation, dust suppression
    """

    conn = connect()
    try:
        cur = conn.cursor()

        # Insert area
        cur.execute(
            "INSERT OR IGNORE INTO wb_areas (area_code, area_name, description) VALUES (?, ?, ?)",
            ("MER_SOUTH", "Merensky South Area", "Merensky South area topology")
        )
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_SOUTH",))
        area_id = cur.fetchone()[0]

        # Insert structures
        structures = [
            ("MERS_SOFT", "Softening Plant", "treatment", 0, None, "Water softening plant"),
            ("MERS_OFF", "Offices", "building", 0, None, "Office building"),
            ("MERS_SDSA", "Merensky South Decline Shaft Area", "decline", 0, None, "Merensky south decline shaft area"),
            ("MERS_SD", "Merensky South Decline", "decline", 0, None, "Merensky south decline"),
            ("MERS_MDCDG", "MDCD 5-6", "storage_group", 1, None, "MDCD 5-6 grouped dam"),
        ]

        for code, name, s_type, is_group, parent_id, notes in structures:
            cur.execute(
                "INSERT OR IGNORE INTO wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (area_id, code, name, s_type, is_group, parent_id, notes)
            )

        # Helper to get structure_id by code
        def sid(code: str) -> int:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", (code,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Structure not found: {code}")
            return row[0]

        # Flow connections
        flows = [
            # Clean water chain
            (sid("MERS_SOFT"), sid("MERS_OFF"), "clean", None, 0, 1, "Softening Plant -> Offices (direct)"),

            # Dirty water: Merensky South Decline <-> MDCD 5-6
            (sid("MERS_SD"), sid("MERS_MDCDG"), "dirty", "dewatering", 0, 1, "Merensky South Decline dewatering -> MDCD 5-6"),
            (sid("MERS_MDCDG"), sid("MERS_SD"), "dirty", "ug_return", 0, 1, "MDCD 5-6 -> Merensky South Decline (UG Return)"),

            # Dam return loop
            (sid("MERS_MDCDG"), sid("MERS_MDCDG"), "clean", "dam_return", 0, 1, "MDCD 5-6 dam return loop"),
        ]

        for f_from, f_to, f_type, subcat, bidir, internal, notes in flows:
            cur.execute(
                "INSERT INTO wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_from, f_to, f_type, subcat, bidir, internal, notes)
            )

        # Inflow sources
        inflows = [
            (sid("MERS_SOFT"), "borehole", "MOGWA_boreholes_south", "MOGWA Boreholes (South)", "MOGWA 1-2 abstraction to softening"),
            (sid("MERS_MDCDG"), "rainfall", "MERS_MDCD_rainfall", "Direct Rainfall to MDCD 5-6", "Rainfall onto MDCD 5-6 surfaces"),
        ]

        for target_sid, s_type, s_code, s_name, notes in inflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (target_sid, s_type, s_code, s_name, notes)
            )

        # Outflow destinations
        outflows = [
            (sid("MERS_SOFT"), "losses", "MERS_SOFT_losses", "Softening Plant Losses", "Process losses at softening"),
            (sid("MERS_OFF"), "consumption", "MERS_OFF_consumption", "Offices Consumption", "Offices water consumption"),
            (sid("MERS_MDCDG"), "spill", "MERS_MDCD_spill", "MDCD 5-6 Spill", "Dam spill"),
            (sid("MERS_MDCDG"), "evaporation", "MERS_MDCD_evap", "MDCD 5-6 Evaporation", "Evaporation from dam surfaces"),
            (sid("MERS_MDCDG"), "dust", "MERS_MDCD_dust", "MDCD 5-6 Dust Suppression", "Dust suppression usage"),
        ]

        for source_sid, d_type, d_code, d_name, notes in outflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (source_sid, d_type, d_code, d_name, notes)
            )

        # Inter-area transfers
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("UG2_SOUTH",))
        ug2_south_area = cur.fetchone()
        if ug2_south_area:
            ug2_south_area_id = ug2_south_area[0]
            
            # Offices -> UG2 South Sewage Treatment
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("UG2S_STP",))
            ug2s_stp = cur.fetchone()
            if ug2s_stp:
                ug2s_stp_id = ug2s_stp[0]
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, ug2_south_area_id, sid("MERS_OFF"), ug2s_stp_id, "dirty", "wastewater", 1, "Merensky South Offices -> UG2 South Sewage Treatment")
                )
            
            # Merensky South Decline Shaft Area -> UG2 South MDCD 1-4 (runoff)
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("UG2S_MDCDG",))
            ug2s_mdcd = cur.fetchone()
            if ug2s_mdcd:
                ug2s_mdcd_id = ug2s_mdcd[0]
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, ug2_south_area_id, sid("MERS_SDSA"), ug2s_mdcd_id, "dirty", "runoff", 1, "Merensky South Decline Shaft Area runoff -> UG2 South MDCD 1-4")
                )
                
                # MDCD 5-6 -> MDCD 1-4 (dirty water connection)
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, ug2_south_area_id, sid("MERS_MDCDG"), ug2s_mdcd_id, "dirty", "dam_transfer", 1, "MDCD 5-6 -> MDCD 1-4 dirty water connection")
                )

        # Inter-area transfer: MDCD 5-6 → MPRWSD1 (dirty trunk)
        # This connects Merensky South MDCD 5-6 to the main dirty water trunk at MPRWSD1
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_PLANT",))
        mer_plant_area = cur.fetchone()
        if mer_plant_area:
            mer_plant_area_id = mer_plant_area[0]
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("MPRWSD1",))
            mprwsd1 = cur.fetchone()
            if mprwsd1:
                mprwsd1_id = mprwsd1[0]
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, mer_plant_area_id, sid("MERS_MDCDG"), mprwsd1_id, "dirty", "dam_transfer", 1, "MDCD 5-6 -> MPRWSD1 (dirty trunk connection)")
                )

        conn.commit()
    finally:
        conn.close()


def seed_old_tsf_area():
    """Seed topology for Old TSF Area including New TSF and return dams.

    Structures:
    - Offices (building)
    - Old TSF (tsf)
    - TRTD 1-2 (RWDs) (reservoir)
    - New TSF (tsf)
    - NT RWD 1&2 (reservoir)

    Flows:
    - Boreholes -> Offices (clean)
    - Offices -> Septic (dirty) and Offices consumption (clean outflow)

    Old TSF complex:
    - Rainfall & runoff -> Old TSF (dirty inflow)
    - TRTD 1-2 -> Old TSF (irrigation) [direction corrected]
    - Old TSF -> TRTD 1-2 (return)
    - Old TSF -> TRTD 1-2 (drainage)
    - TRTD 1-2 loop (-347) tagged as dam_return on Old TSF

    New TSF complex:
    - Rainfall & runoff -> New TSF (dirty inflow)
    - NT RWD 1&2 -> New TSF (irrigation) [direction corrected]
    - New TSF -> NT RWD 1&2 (return)
    - New TSF -> NT RWD 1&2 (drainage)
    - NT RWD 1&2 loop (68) tagged as dam_return on New TSF

    Inter-area:
    - TRTD 1-2 <-> MPRWSD 1 (bidirectional dirty line)
    - NT RWD 1&2 <-> MPRWSD 1 (bidirectional dirty line)
    - TRTD 1-2 outflow (469,877) to MPRWSD 1
    - NT RWD 1&2 outflow (2,415,778) joins inter-area dirty line to MPRWSD 1
    """

    conn = connect()
    try:
        cur = conn.cursor()

        # Insert area
        cur.execute(
            "INSERT OR IGNORE INTO wb_areas (area_code, area_name, description) VALUES (?, ?, ?)",
            ("OLD_TSF", "Old TSF Area", "Old and New TSF with return dams")
        )
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("OLD_TSF",))
        area_id = cur.fetchone()[0]

        # Insert structures
        structures = [
            ("OT_OFF", "Offices", "building", 0, None, "Office building"),
            ("OT_OLD_TSF", "Old Tailings Storage Facility", "tsf", 0, None, "Old TSF"),
            ("OT_TRTD", "TRTD 1-2 (RWDs)", "reservoir", 0, None, "Return water dams"),
            ("OT_NEW_TSF", "New Tailings Storage Facility", "tsf", 0, None, "New TSF"),
            ("OT_NT_RWD", "NT RWD 1&2", "reservoir", 0, None, "New TSF return water dams"),
        ]

        for code, name, s_type, is_group, parent_id, notes in structures:
            cur.execute(
                "INSERT OR IGNORE INTO wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (area_id, code, name, s_type, is_group, parent_id, notes)
            )

        # Helper to get structure_id by code
        def sid(code: str) -> int:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", (code,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Structure not found: {code}")
            return row[0]

        # Flow connections (dirty lines and corrected directions)
        flows = [
            # Offices to septic (dirty)
            (sid("OT_OFF"), sid("OT_OLD_TSF"), "dirty", "septic", 0, 1, "Offices -> Old TSF septic/dirty line"),

            # Old TSF complex
            (sid("OT_TRTD"), sid("OT_OLD_TSF"), "dirty", "irrigation", 0, 1, "TRTD -> Old TSF irrigation (corrected direction)"),
            (sid("OT_OLD_TSF"), sid("OT_TRTD"), "dirty", "return", 0, 1, "Old TSF return -> TRTD"),
            (sid("OT_OLD_TSF"), sid("OT_TRTD"), "dirty", "drainage", 0, 1, "Old TSF drainage -> TRTD"),

            # New TSF complex
            (sid("OT_NT_RWD"), sid("OT_NEW_TSF"), "dirty", "irrigation", 0, 1, "NT RWD -> New TSF irrigation (corrected direction)"),
            (sid("OT_NEW_TSF"), sid("OT_NT_RWD"), "dirty", "return", 0, 1, "New TSF return -> NT RWD"),
            (sid("OT_NEW_TSF"), sid("OT_NT_RWD"), "dirty", "drainage", 0, 1, "New TSF drainage -> NT RWD"),

            # Internal loops tagged at TSFs
            (sid("OT_OLD_TSF"), sid("OT_OLD_TSF"), "dirty", "dam_return", 0, 1, "Old TSF loop (-347)"),
            (sid("OT_NEW_TSF"), sid("OT_NEW_TSF"), "dirty", "dam_return", 0, 1, "New TSF loop (68)"),
        ]

        for f_from, f_to, f_type, subcat, bidir, internal, notes in flows:
            cur.execute(
                "INSERT INTO wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_from, f_to, f_type, subcat, bidir, internal, notes)
            )

        # Inflow sources (rainfall & runoff to TSFs and rainfall to RWDs)
        inflows = [
            (sid("OT_OLD_TSF"), "rainfall", "OT_OLD_TSF_rainrun", "Old TSF Rainfall & Runoff", "Rainfall and runoff to Old TSF"),
            (sid("OT_TRTD"), "rainfall", "OT_TRTD_rain", "TRTD 1-2 Direct Rainfall", "Rainfall to TRTD 1-2"),
            (sid("OT_NEW_TSF"), "rainfall", "OT_NEW_TSF_rainrun", "New TSF Rainfall & Runoff", "Rainfall and runoff to New TSF"),
            (sid("OT_NT_RWD"), "rainfall", "OT_NT_RWD_rain", "NT RWD 1&2 Direct Rainfall", "Rainfall to NT RWD 1&2"),
        ]

        for target_sid, s_type, s_code, s_name, notes in inflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (target_sid, s_type, s_code, s_name, notes)
            )

        # Outflow destinations (evaporation, interstitial storage, seepage, spill, consumption)
        outflows = [
            # Offices
            (sid("OT_OFF"), "septic", "OT_OFF_septic", "Offices Septic Tank", "Septic outflow"),
            (sid("OT_OFF"), "consumption", "OT_OFF_consumption", "Offices Consumption", "Clean water consumption"),

            # Old TSF
            (sid("OT_OLD_TSF"), "evaporation", "OT_OLD_TSF_evap", "Old TSF Evaporation", "Evaporation from Old TSF"),
            (sid("OT_OLD_TSF"), "interstitial", "OT_OLD_TSF_interstitial", "Old TSF Interstitial Storage", "Water trapped in tailings"),
            (sid("OT_OLD_TSF"), "seepage", "OT_OLD_TSF_seepage", "Old TSF Seepage", "Seepage losses from Old TSF"),

            # TRTD 1-2
            (sid("OT_TRTD"), "evaporation", "OT_TRTD_evap", "TRTD Evaporation", "Evaporation from TRTD"),
            (sid("OT_TRTD"), "spill", "OT_TRTD_spill", "TRTD Spill", "Spill from TRTD"),

            # New TSF
            (sid("OT_NEW_TSF"), "evaporation", "OT_NEW_TSF_evap", "New TSF Evaporation", "Evaporation from New TSF"),
            (sid("OT_NEW_TSF"), "interstitial", "OT_NEW_TSF_interstitial", "New TSF Interstitial Storage", "Water trapped in tailings"),
            (sid("OT_NEW_TSF"), "seepage", "OT_NEW_TSF_seepage", "New TSF Seepage", "Seepage losses from New TSF"),

            # NT RWD 1&2
            (sid("OT_NT_RWD"), "evaporation", "OT_NT_RWD_evap", "NT RWD Evaporation", "Evaporation from NT RWD"),
            (sid("OT_NT_RWD"), "spill", "OT_NT_RWD_spill", "NT RWD Spill", "Spill from NT RWD"),
        ]

        for source_sid, d_type, d_code, d_name, notes in outflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (source_sid, d_type, d_code, d_name, notes)
            )

        # Inter-area transfers (bidirectional dirty lines)
        # MPRWSD 1 is in Merensky Plant Area (not yet seeded) – create placeholders if present later.
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_PLANT",))
        mer_plant_area = cur.fetchone()
        if mer_plant_area:
            mer_plant_area_id = mer_plant_area[0]
            # Try to find MPRWSD 1 structure if already seeded
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("MPRWSD1",))
            dest = cur.fetchone()
            if dest:
                dest_id = dest[0]
                # TRTD <-> MPRWSD 1
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, mer_plant_area_id, sid("OT_TRTD"), dest_id, "dirty", "dam_transfer", 1, "TRTD 1-2 <-> MPRWSD 1")
                )
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (mer_plant_area_id, area_id, dest_id, sid("OT_TRTD"), "dirty", "dam_transfer", 1, "MPRWSD 1 <-> TRTD 1-2")
                )
                # NT RWD <-> MPRWSD 1
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, mer_plant_area_id, sid("OT_NT_RWD"), dest_id, "dirty", "dam_transfer", 1, "NT RWD 1&2 <-> MPRWSD 1")
                )
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (mer_plant_area_id, area_id, dest_id, sid("OT_NT_RWD"), "dirty", "dam_transfer", 1, "MPRWSD 1 <-> NT RWD 1&2")
                )

        conn.commit()
    finally:
        conn.close()

def seed_merensky_plant_area():
    """Seed topology for Merensky Plant Area.

    Structures:
    - Softening Plant (treatment)
    - Reservoir (reservoir)
    - Offices (building)
    - Sewage Treatment (treatment)
    - Merensky Concentrator Plant (plant)
    - MPRWSD 1 (reservoir) – process return dam
    - MPSWD 1-2 (reservoir) – process water storage dam

    Key flows per clarification:
    - Boreholes -> Softening -> Reservoir -> Offices
    - Offices -> Sewage Treatment (clean to wastewater)
    - Sewage Treatment -> MPSWD 1-2 (effluent)
    - MPSWD 1-2 <-> Merensky Plant (bidirectional clean process water)
    - MPSWD 1-2 loop (dam_return)
    - MPRWSD 1 -> Merensky Plant (dirty process water)
    - Inter-area: Plant -> Old TSF (dirty), NDCD group (UG2 North) -> MPRWSD 1 (dirty),
      TRTD/NT RWD (Old TSF) <-> MPRWSD 1 (dirty bidirectional – ensure here if Old TSF exists)
    - Rainfall: Direct rainfall to MPSWD 1-2
    - Outflows: Offices (losses, consumption), STP (losses), MPSWD 1-2 (spill, evaporation, dust),
      Plant (losses, water in concentrate)
    """

    conn = connect()
    try:
        cur = conn.cursor()

        # Insert area
        cur.execute(
            "INSERT OR IGNORE INTO wb_areas (area_code, area_name, description) VALUES (?, ?, ?)",
            ("MER_PLANT", "Merensky Plant Area", "Merensky concentrator plant and dams")
        )
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_PLANT",))
        area_id = cur.fetchone()[0]

        # Insert structures
        structures = [
            ("MERP_SOFT", "Softening Plant", "treatment", 0, None, "Water softening plant"),
            ("MERP_RES", "Reservoir", "reservoir", 0, None, "Area reservoir"),
            ("MERP_OFF", "Offices", "building", 0, None, "Office building"),
            ("MERP_STP", "Sewage Treatment", "treatment", 0, None, "Sewage treatment"),
            ("MERP_PLANT", "Merensky Concentrator Plant", "plant", 0, None, "Concentrator plant"),
            ("MPRWSD1", "MPRWSD 1", "reservoir", 0, None, "Process return water dam"),
            ("MPSWD12", "MPSWD 1-2", "reservoir", 0, None, "Process water storage dam"),
        ]

        for code, name, s_type, is_group, parent_id, notes in structures:
            cur.execute(
                "INSERT OR IGNORE INTO wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (area_id, code, name, s_type, is_group, parent_id, notes)
            )

        # Helper to get structure_id by code
        def sid(code: str) -> int:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", (code,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Structure not found: {code}")
            return row[0]

        # Flow connections
        flows = [
            # Clean chain: Softening -> Reservoir -> Offices
            (sid("MERP_SOFT"), sid("MERP_RES"), "clean", None, 0, 1, "Softening -> Reservoir"),
            (sid("MERP_RES"), sid("MERP_OFF"), "clean", None, 0, 1, "Reservoir -> Offices"),
            (sid("MERP_OFF"), sid("MERP_STP"), "clean", None, 0, 1, "Offices -> Sewage Treatment"),

            # Plant water exchanges
            (sid("MPSWD12"), sid("MERP_PLANT"), "clean", "process_supply", 0, 1, "MPSWD 1-2 -> Plant (clean process water)"),
            (sid("MERP_PLANT"), sid("MPSWD12"), "clean", "process_return", 0, 1, "Plant -> MPSWD 1-2 (clean return)"),
            (sid("MPSWD12"), sid("MPSWD12"), "clean", "dam_return", 0, 1, "MPSWD 1-2 loop"),

            # Dirty process from MPRWSD1 to Plant
            (sid("MPRWSD1"), sid("MERP_PLANT"), "dirty", "process_water", 0, 1, "MPRWSD 1 -> Plant (dirty process water)"),

            # Sewage effluent to MPSWD 1-2
            (sid("MERP_STP"), sid("MPSWD12"), "dirty", "effluent", 0, 1, "STP effluent -> MPSWD 1-2"),
        ]

        for f_from, f_to, f_type, subcat, bidir, internal, notes in flows:
            cur.execute(
                "INSERT INTO wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_from, f_to, f_type, subcat, bidir, internal, notes)
            )

        # Inflow sources
        inflows = [
            (sid("MERP_SOFT"), "borehole", "MPGWA_boreholes", "MPGWA Boreholes", "MPGWA 1-2 abstraction to softening"),
            (sid("MPSWD12"), "rainfall", "MPSWD12_rain", "Direct Rainfall to MPSWD 1-2", "Rainfall to MPSWD 1-2"),
            (sid("MERP_PLANT"), "ore_water", "MERP_ore_water", "Water in Ore", "Ore moisture to plant"),
            (sid("MPRWSD1"), "river", "MPRWSD1_rivers", "Raw Water Intake (Rivers)", "River intake to MPRWSD 1 (dirty trunk)"),
        ]

        for target_sid, s_type, s_code, s_name, notes in inflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (target_sid, s_type, s_code, s_name, notes)
            )

        # Outflow destinations
        outflows = [
            (sid("MERP_OFF"), "losses", "MERP_OFF_losses", "Offices Losses", "Losses from offices"),
            (sid("MERP_OFF"), "consumption", "MERP_OFF_consumption", "Offices Consumption", "Consumption at offices"),
            (sid("MERP_STP"), "losses", "MERP_STP_losses", "Sewage Treatment Losses", "STP losses"),
            (sid("MPSWD12"), "spill", "MPSWD12_spill", "MPSWD 1-2 Spill", "Spill from MPSWD 1-2"),
            (sid("MPSWD12"), "evaporation", "MPSWD12_evap", "MPSWD 1-2 Evaporation", "Evaporation from MPSWD 1-2"),
            (sid("MPSWD12"), "dust", "MPSWD12_dust", "MPSWD 1-2 Dust Suppression", "Dust suppression"),
            (sid("MERP_PLANT"), "losses", "MERP_PLANT_losses", "Plant Losses", "Process losses at plant"),
            (sid("MERP_PLANT"), "product_bound", "MERP_PLANT_product", "Water in Concentrate", "Water in concentrate (product bound)"),
        ]

        for source_sid, d_type, d_code, d_name, notes in outflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (source_sid, d_type, d_code, d_name, notes)
            )

        # Inter-area transfers per clarifications
        # Plant -> Old TSF (dirty)
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("OLD_TSF",))
        old_tsf_area = cur.fetchone()
        if old_tsf_area:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("OT_OLD_TSF",))
            dest = cur.fetchone()
            if dest:
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, old_tsf_area[0], sid("MERP_PLANT"), dest[0], "dirty", "plant_discharge", 1, "Plant -> Old TSF dirty discharge")
                )
            
            # Plant -> New TSF (dirty) - bidirectional connection to New TSF discharge line
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("OT_NEW_TSF",))
            new_tsf = cur.fetchone()
            if new_tsf:
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, old_tsf_area[0], sid("MERP_PLANT"), new_tsf[0], "dirty", "plant_discharge", 1, "Plant -> New TSF dirty discharge (bidirectional)")
                )

        # NDCD (UG2 North) -> MPRWSD1 (dirty)
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("UG2_NORTH",))
        ug2n_area = cur.fetchone()
        if ug2n_area:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("UG2N_NDCDG",))
            ndcd = cur.fetchone()
            if ndcd:
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (ug2n_area[0], area_id, ndcd[0], sid("MPRWSD1"), "dirty", "dam_transfer", 1, "UG2 North NDCD -> MPRWSD1")
                )

        # NDCD (Merensky North) -> MPRWSD1 (dirty) - added here for seeding order independence
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_NORTH",))
        mern_area = cur.fetchone()
        if mern_area:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("MERN_NDCDG",))
            mern_ndcd = cur.fetchone()
            if mern_ndcd:
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (mern_area[0], area_id, mern_ndcd[0], sid("MPRWSD1"), "dirty", "dam_transfer", 1, "Merensky North NDCD -> MPRWSD1")
                )

        # Ensure Old TSF <-> MPRWSD1 links exist if Old TSF already seeded
        if old_tsf_area:
            old_tsf_area_id = old_tsf_area[0]
            mprwsd1_id = sid("MPRWSD1")
            # TRTD
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("OT_TRTD",))
            trtd = cur.fetchone()
            if trtd:
                trtd_id = trtd[0]
                # TRTD -> MPRWSD1
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (old_tsf_area_id, area_id, trtd_id, mprwsd1_id, "dirty", "dam_transfer", 1, "TRTD 1-2 -> MPRWSD1")
                )
                # MPRWSD1 -> TRTD
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, old_tsf_area_id, mprwsd1_id, trtd_id, "dirty", "dam_transfer", 1, "MPRWSD1 -> TRTD 1-2")
                )
            # NT RWD
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("OT_NT_RWD",))
            nt_rwd = cur.fetchone()
            if nt_rwd:
                nt_rwd_id = nt_rwd[0]
                # NT RWD -> MPRWSD1
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (old_tsf_area_id, area_id, nt_rwd_id, mprwsd1_id, "dirty", "dam_transfer", 1, "NT RWD 1&2 -> MPRWSD1")
                )
                # MPRWSD1 -> NT RWD
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, old_tsf_area_id, mprwsd1_id, nt_rwd_id, "dirty", "dam_transfer", 1, "MPRWSD1 -> NT RWD 1&2")
                )

        conn.commit()
    finally:
        conn.close()


def seed_ug2_plant_area():
    """Seed topology for UG2 Plant Area per corrected diagram analysis.

    Structures:
    - CPRWSD 1 (reservoir) - Process return water storage dam (dirty)
    - CPPWT (treatment) - Process water treatment (receives from inter-area, internal to plant)
    - UG2 Concentrator Plant (plant)
    - UG2PCD 1 (reservoir) - Process clean dam
    - Softening Plant (treatment)
    - Reservoir (reservoir)
    - Offices (building)
    - Sewage Treatment (treatment)

    Key flows per corrections:
    - Raw Water Intake (Rivers) 3,097,458 -> CPRWSD 1
    - Water in Ore -> Plant
    - Direct Rainfall -> UG2PCD 1
    - Boreholes (CPGWA 1-4) -> Softening Plant
    - Softening -> Reservoir -> Offices
    - Offices -> Sewage Treatment (clean to wastewater)
    - Sewage Treatment -> UG2 Plant (1,848 effluent, dirty)
    - CPRWSD 1 -> Plant (3,889,500 dirty process water)
    - UG2PCD 1 <-> Plant (22,227 bidirectional clean process water)
    - UG2PCD 1 loop (36 dam_return)
    
    Inter-area connections:
    - 294,595 from inter-area line (MPRWSD 1 -> TRTD path) -> CPPWT
    - 3,961,796 from Plant -> inter-area line (Merensky Plant -> Old TSF path)
    - 497,448 from Plant -> inter-area line (MPRWSD 1 -> NDCD path)

    Outflows:
    - Softening Plant: 2,717 losses
    - Offices: 15,489 consumption
    - Sewage Treatment: 723 losses
    - UG2PCD 1: 37 spill, 166 evaporation, 1,548 dust
    - Plant: 108,847 losses, 11,747 water_in_concentrate
    """

    conn = connect()
    try:
        cur = conn.cursor()

        # Insert area
        cur.execute(
            "INSERT OR IGNORE INTO wb_areas (area_code, area_name, description) VALUES (?, ?, ?)",
            ("UG2_PLANT", "UG2 Plant Area", "UG2 concentrator plant and dams")
        )
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("UG2_PLANT",))
        area_id = cur.fetchone()[0]

        # Insert structures
        structures = [
            ("CPRWSD1", "CPRWSD 1", "reservoir", 0, None, "Process return water storage dam"),
            ("CPPWT", "CPPWT", "treatment", 0, None, "Process water treatment within plant"),
            ("UG2P_PLANT", "UG2 Concentrator Plant", "plant", 0, None, "UG2 concentrator plant"),
            ("UG2PCD1", "UG2PCD 1", "reservoir", 0, None, "Process clean dam"),
            ("UG2P_SOFT", "Softening Plant", "treatment", 0, None, "Water softening plant"),
            ("UG2P_RES", "Reservoir", "reservoir", 0, None, "Area reservoir"),
            ("UG2P_OFF", "Offices", "building", 0, None, "Office building"),
            ("UG2P_STP", "Sewage Treatment", "treatment", 0, None, "Sewage treatment"),
        ]

        for code, name, s_type, is_group, parent_id, notes in structures:
            cur.execute(
                "INSERT OR IGNORE INTO wb_structures (area_id, structure_code, structure_name, structure_type, is_group, parent_structure_id, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (area_id, code, name, s_type, is_group, parent_id, notes)
            )

        # Helper to get structure_id by code
        def sid(code: str) -> int:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", (code,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Structure not found: {code}")
            return row[0]

        # Flow connections
        flows = [
            # Clean water chain: Softening -> Reservoir -> Offices
            (sid("UG2P_SOFT"), sid("UG2P_RES"), "clean", None, 0, 1, "Softening -> Reservoir"),
            (sid("UG2P_RES"), sid("UG2P_OFF"), "clean", None, 0, 1, "Reservoir -> Offices"),
            (sid("UG2P_OFF"), sid("UG2P_STP"), "clean", None, 0, 1, "Offices -> Sewage Treatment"),

            # Sewage effluent to Plant (corrected: not to UG2PCD1)
            (sid("UG2P_STP"), sid("UG2P_PLANT"), "dirty", "effluent", 0, 1, "STP effluent -> Plant"),

            # Dirty process water from CPRWSD1 to Plant
            (sid("CPRWSD1"), sid("UG2P_PLANT"), "dirty", "process_water", 0, 1, "CPRWSD 1 -> Plant"),

            # UG2PCD1 <-> Plant (bidirectional dirty process return water)
            (sid("UG2PCD1"), sid("UG2P_PLANT"), "dirty", "process_return", 1, 1, "UG2PCD 1 <-> Plant (bidirectional dirty process return water)"),

            # UG2PCD1 loop
            (sid("UG2PCD1"), sid("UG2PCD1"), "dirty", "dam_return", 0, 1, "UG2PCD 1 loop"),

            # Plant discharge to CPPWT (treatment before inter-area transfer)
            (sid("UG2P_PLANT"), sid("CPPWT"), "dirty", "plant_discharge", 0, 1, "Plant -> CPPWT (discharge to treatment)"),

            # CPPWT internal (inter-area connection point, flows registered in inter-area transfers)
        ]

        for f_from, f_to, f_type, subcat, bidir, internal, notes in flows:
            cur.execute(
                "INSERT INTO wb_flow_connections (from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, is_internal, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_from, f_to, f_type, subcat, bidir, internal, notes)
            )

        # Inflow sources
        inflows = [
            (sid("CPRWSD1"), "river", "UG2P_rivers", "Raw Water Intake (Rivers)", "River intake to CPRWSD 1"),
            (sid("UG2P_SOFT"), "borehole", "CPGWA_boreholes", "CPGWA 1-4 Boreholes", "CPGWA 1-4 abstraction to softening"),
            (sid("UG2PCD1"), "rainfall", "UG2PCD1_rain", "Direct Rainfall to UG2PCD 1", "Rainfall to UG2PCD 1"),
            (sid("UG2P_PLANT"), "ore_water", "UG2P_ore_water", "Water in Ore", "Ore moisture to plant"),
        ]

        for target_sid, s_type, s_code, s_name, notes in inflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_inflow_sources (target_structure_id, source_type, source_code, source_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (target_sid, s_type, s_code, s_name, notes)
            )

        # Outflow destinations
        outflows = [
            (sid("UG2P_SOFT"), "losses", "UG2P_SOFT_losses", "Softening Plant Losses", "Losses from softening plant"),
            (sid("UG2P_OFF"), "consumption", "UG2P_OFF_consumption", "Offices Consumption", "Consumption at offices"),
            (sid("UG2P_STP"), "losses", "UG2P_STP_losses", "Sewage Treatment Losses", "STP losses"),
            (sid("UG2PCD1"), "spill", "UG2PCD1_spill", "UG2PCD 1 Spill", "Spill from UG2PCD 1"),
            (sid("UG2PCD1"), "evaporation", "UG2PCD1_evap", "UG2PCD 1 Evaporation", "Evaporation from UG2PCD 1"),
            (sid("UG2PCD1"), "dust", "UG2PCD1_dust", "UG2PCD 1 Dust Suppression", "Dust suppression"),
            (sid("UG2P_PLANT"), "losses", "UG2P_PLANT_losses", "Plant Losses", "Process losses at plant"),
            (sid("UG2P_PLANT"), "product_bound", "UG2P_PLANT_product", "Water in Concentrate", "Water in concentrate (product bound)"),
        ]

        for source_sid, d_type, d_code, d_name, notes in outflows:
            cur.execute(
                "INSERT OR IGNORE INTO wb_outflow_destinations (source_structure_id, destination_type, destination_code, destination_name, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (source_sid, d_type, d_code, d_name, notes)
            )

        # Inter-area transfers (placeholders for trunk connections)
        # 1. 294,595 from inter-area line (MPRWSD 1 -> TRTD path) -> CPPWT
        # This will be wired when we know the exact source structure in that path
        
        # 2a. Plant discharge -> Old TSF (bidirectional for easy redirection)
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("OLD_TSF",))
        old_tsf_area = cur.fetchone()
        if old_tsf_area:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("OT_OLD_TSF",))
            old_tsf_struct = cur.fetchone()
            if old_tsf_struct:
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, old_tsf_area[0], sid("UG2P_PLANT"), old_tsf_struct[0], "dirty", "plant_discharge", 1, "UG2 Plant -> Old TSF (bidirectional, can redirect to New TSF)")
                )

            # 2b. Plant discharge -> New TSF (alternative/additional discharge point)
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("OT_NEW_TSF",))
            new_tsf_struct = cur.fetchone()
            if new_tsf_struct:
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, old_tsf_area[0], sid("UG2P_PLANT"), new_tsf_struct[0], "dirty", "plant_discharge", 1, "UG2 Plant -> New TSF (bidirectional, alternative discharge)")
                )

        # 3. 497,448 from CPPWT -> MPRWSD1 trunk (connects to existing MPRWSD1 -> NDCD line)
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_PLANT",))
        mer_plant_for_trunk = cur.fetchone()
        if mer_plant_for_trunk:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("MPRWSD1",))
            mprwsd1_for_trunk = cur.fetchone()
            if mprwsd1_for_trunk:
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (area_id, mer_plant_for_trunk[0], sid("CPPWT"), mprwsd1_for_trunk[0], "dirty", "trunk_feed", 1, "CPPWT -> MPRWSD1 trunk (497,448 inter-area dirty)")
                )

        # Note: CPPWT receives 294,595 from MPRWSD1->TRTD trunk; will add reverse link if needed
        cur.execute("SELECT area_id FROM wb_areas WHERE area_code=?", ("MER_PLANT",))
        mer_plant_area = cur.fetchone()
        if mer_plant_area:
            cur.execute("SELECT structure_id FROM wb_structures WHERE structure_code=?", ("MPRWSD1",))
            mprwsd1_struct = cur.fetchone()
            if mprwsd1_struct:
                # MPRWSD1 path feeds CPPWT (294,595)
                cur.execute(
                    "INSERT OR IGNORE INTO wb_inter_area_transfers (from_area_id, to_area_id, from_structure_id, to_structure_id, flow_type, subcategory, is_bidirectional, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (mer_plant_area[0], area_id, mprwsd1_struct[0], sid("CPPWT"), "dirty", "trunk_feed", 1, "MPRWSD1 trunk -> CPPWT (294,595 inter-area dirty)")
                )

        conn.commit()
    finally:
        conn.close()


def main():
    migrate()
    seed_ug2_north_decline_area()
    seed_merensky_plant_area()  # Must be before Merensky North to create MER_PLANT area first
    seed_merensky_north_area()
    seed_stockpile_area()
    seed_old_tsf_area()
    seed_ug2_plant_area()
    seed_ug2_south_decline_area()
    seed_merensky_south_area()
    print("wb_* schema migrated. UG2 North, Merensky North, Stockpile, Old TSF, Merensky Plant, UG2 Plant, UG2 South, and Merensky South areas seeded.")


if __name__ == "__main__":
    main()
