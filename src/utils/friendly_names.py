#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flow Friendly Name Resolver

Converts technical flow IDs and column names to human-friendly labels.
Used for Excel column headers, UI displays, and reports.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache

# Path management
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.utils.app_logger import logger
except ImportError:
    # Fallback for standalone execution
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

_FRIENDLY_NAMES_PATH = Path("data/flow_friendly_names.json")
_friendly_names_cache: Optional[Dict] = None


def load_friendly_names() -> Dict:
    """Load friendly names from JSON file."""
    global _friendly_names_cache
    
    if _friendly_names_cache is not None:
        return _friendly_names_cache
    
    try:
        with open(_FRIENDLY_NAMES_PATH, 'r', encoding='utf-8') as f:
            _friendly_names_cache = json.load(f)
            logger.info(f"Loaded {len(_friendly_names_cache.get('node_friendly_names', {}))} friendly names")
            return _friendly_names_cache
    except Exception as e:
        logger.error(f"Failed to load friendly names: {e}")
        return {"node_friendly_names": {}, "flow_type_labels": {}}


def get_friendly_name(node_id: str) -> str:
    """
    Get human-friendly name for a node ID.
    
    Args:
        node_id: Technical node ID (e.g., 'ug2s_borehole')
    
    Returns:
        Friendly name (e.g., 'UG2 Main Borehole (MGDWA)')
        Falls back to formatted node_id if no mapping exists
    """
    names = load_friendly_names()
    node_id_lower = node_id.lower().strip()
    
    # Check direct mapping
    if node_id_lower in names.get("node_friendly_names", {}):
        return names["node_friendly_names"][node_id_lower]
    
    # Fallback: Format the technical ID
    # Convert underscores to spaces and title case
    formatted = node_id.replace('_', ' ').title()
    return formatted


def get_flow_type_label(flow_type: str) -> str:
    """
    Get human-friendly label for a flow type.
    
    Args:
        flow_type: Technical flow type (e.g., 'clean', 'dirty')
    
    Returns:
        Friendly label (e.g., 'Clean Water', 'Process Water')
    """
    names = load_friendly_names()
    flow_type_lower = flow_type.lower().strip()
    
    if flow_type_lower in names.get("flow_type_labels", {}):
        return names["flow_type_labels"][flow_type_lower]
    
    return flow_type.title()


def format_flow_column_name(from_node: str, to_node: str, flow_type: Optional[str] = None) -> str:
    """
    Format a flow column name with friendly labels.
    
    Args:
        from_node: Source node ID
        to_node: Target node ID
        flow_type: Optional flow type (e.g., 'clean', 'dirty')
    
    Returns:
        Formatted column name (e.g., 'Borehole → Softening Plant')
    
    Example:
        >>> format_flow_column_name('ug2s_borehole', 'ug2s_soft')
        'UG2 Main Borehole → UG2 Main Softening Plant'
    """
    from_friendly = get_friendly_name(from_node)
    to_friendly = get_friendly_name(to_node)
    
    if flow_type:
        flow_label = get_flow_type_label(flow_type)
        return f"{from_friendly} → {to_friendly} ({flow_label})"
    
    return f"{from_friendly} → {to_friendly}"


def parse_technical_column_name(column_name: str) -> Optional[Dict[str, str]]:
    """
    Parse a technical column name into components.
    
    Args:
        column_name: Column name like 'UG2S_BOREHOLE → UG2S_SOFT'
    
    Returns:
        Dict with 'from', 'to', and optional 'flow_type' keys
        None if parsing fails
    """
    if '→' not in column_name and '->' not in column_name:
        return None
    
    # Handle both → and -> arrows
    arrow = '→' if '→' in column_name else '->'
    parts = column_name.split(arrow)
    
    if len(parts) != 2:
        return None
    
    from_node = parts[0].strip()
    to_node = parts[1].strip()
    
    # Check if flow type is in parentheses
    flow_type = None
    if '(' in to_node and ')' in to_node:
        to_parts = to_node.rsplit('(', 1)
        to_node = to_parts[0].strip()
        flow_type = to_parts[1].rstrip(')').strip()
    
    return {
        'from': from_node,
        'to': to_node,
        'flow_type': flow_type
    }


def convert_column_to_friendly(column_name: str) -> str:
    """
    Convert a technical column name to friendly format.
    
    Args:
        column_name: Technical column name
    
    Returns:
        Human-friendly column name
    
    Example:
        >>> convert_column_to_friendly('UG2S_BOREHOLE → UG2S_SOFT')
        'UG2 Main Borehole → UG2 Main Softening Plant'
    """
    parsed = parse_technical_column_name(column_name)
    
    if not parsed:
        # Not a flow column, return as-is or format slightly
        return column_name.replace('_', ' ').title()
    
    return format_flow_column_name(
        parsed['from'],
        parsed['to'],
        parsed.get('flow_type')
    )


def add_friendly_name(node_id: str, friendly_name: str, save: bool = True) -> bool:
    """
    Add a new friendly name mapping.
    
    Args:
        node_id: Technical node ID
        friendly_name: Human-friendly name
        save: Whether to save to file immediately
    
    Returns:
        True if successful
    """
    try:
        names = load_friendly_names()
        
        # Update in memory
        if "node_friendly_names" not in names:
            names["node_friendly_names"] = {}
        
        names["node_friendly_names"][node_id.lower().strip()] = friendly_name
        
        # Update cache
        global _friendly_names_cache
        _friendly_names_cache = names
        
        # Save to file
        if save:
            with open(_FRIENDLY_NAMES_PATH, 'w', encoding='utf-8') as f:
                json.dump(names, f, indent=2, ensure_ascii=False)
            logger.info(f"Added friendly name: {node_id} -> {friendly_name}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to add friendly name: {e}")
        return False


def batch_convert_columns(column_names: list) -> Dict[str, str]:
    """
    Convert multiple column names to friendly format.
    
    Args:
        column_names: List of technical column names
    
    Returns:
        Dict mapping technical name to friendly name
    """
    return {
        col: convert_column_to_friendly(col)
        for col in column_names
    }


if __name__ == '__main__':
    # Test the friendly name converter
    print("Testing Friendly Name Converter")
    print("=" * 60)
    
    test_columns = [
        'UG2S_BOREHOLE → UG2S_SOFT',
        'BH_NDGWA → SOFTENING',
        'OLDTSF_OLD_TSF → OLDTSF_TRTD',
        'UG2PLANT_UG2P_PLANT → UG2PLANT_UG2PCD1',
    ]
    
    for col in test_columns:
        friendly = convert_column_to_friendly(col)
        print(f"\nTechnical: {col}")
        print(f"Friendly:  {friendly}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
