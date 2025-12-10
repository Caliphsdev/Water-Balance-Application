"""
Template Data Parser - Reads inflows, outflows, and dam recirculation from .txt templates
Provides data for balance check calculations without database writes
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from utils.app_logger import logger


@dataclass
class BalanceEntry:
    """Single balance entry (inflow/outflow/recirculation)"""
    code: str
    name: str
    area: str
    value_m3: float
    unit: str = "m³"
    
    def __repr__(self):
        return f"{self.code}: {self.name} ({self.value_m3:,.0f} {self.unit})"


class TemplateDataParser:
    """Parse and manage template data from .txt files"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize parser
        
        Args:
            project_root: Root path to project (defaults to parent of src)
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        
        self.project_root = project_root
        self.inflows_file = project_root / "INFLOW_CODES_TEMPLATE.txt"
        self.outflows_file = project_root / "OUTFLOW_CODES_TEMPLATE_CORRECTED.txt"
        self.recirculation_file = project_root / "DAM_RECIRCULATION_TEMPLATE.txt"
        
        self.inflows: List[BalanceEntry] = []
        self.outflows: List[BalanceEntry] = []
        self.recirculation: List[BalanceEntry] = []
        self.areas: set = set()
        
        self._load_all_templates()
    
    def _load_all_templates(self):
        """Load all template files"""
        self._load_inflows()
        self._load_outflows()
        self._load_recirculation()
        self._extract_areas()
    
    def _parse_line(self, line: str) -> Optional[Tuple[str, str, str, float]]:
        """Parse a single line from template file
        
        Format: CODE (type) = VALUE m³  # Description
        
        Returns:
            Tuple of (code, name, area, value) or None if invalid
        """
        line = line.strip()
        
        # Skip empty lines and header/separator lines
        if not line or line.startswith("=") or line.startswith("#") or len(line) < 5:
            return None
        
        # Skip emoji headers and structural lines
        if any(x in line for x in ["📍", "🗺️", "⬇️", "⛏️", "💧", "→", "Legend"]):
            if "=" not in line:  # But parse if it has a value
                return None
        
        try:
            # Look for = sign
            if "=" not in line:
                return None
            
            # Split on = to get value part
            parts = line.split("=")
            if len(parts) < 2:
                return None
            
            left = parts[0].strip()
            right_part = parts[1].strip()
            
            # Extract code (first token)
            code_match = left.split()[0] if left else ""
            if not code_match or len(code_match) < 1:
                return None
            
            code = code_match
            
            # Extract type/name from parentheses if available
            if "(" in left and ")" in left:
                name_start = left.find("(") + 1
                name_end = left.find(")")
                name = left[name_start:name_end].strip()
                if not name:
                    name = code
            else:
                name = code
            
            # Parse value from right side - get first number
            # Value format: "12345 m³" or "12 345 m³" or "123,456 m³"
            value_str = ""
            for char in right_part:
                if char.isdigit() or char in "., ":
                    value_str += char
                elif value_str:  # Stop at first non-numeric after starting
                    break
            
            value_str = value_str.replace(",", "").replace(" ", "").strip()
            if not value_str:
                return None
            
            value = float(value_str)
            
            # Return with empty area (will be filled from header context)
            return (code, name, "UNKNOWN", value)
            
        except Exception as e:
            logger.debug(f"Could not parse template line: {line} - {e}")
            return None
    
    def _extract_area_from_code(self, code: str) -> str:
        """Extract area name from code (backup method)"""
        code_upper = code.upper()
        
        # Map code prefixes to areas
        if any(x in code_upper for x in ["MERN", "NDCD", "MOGWA"]):
            return "NDCD1-4"
        elif any(x in code_upper for x in ["MERP", "NDSWD", "MPSWD"]):
            return "NDSWD1-2"
        elif any(x in code_upper for x in ["MERS", "MDCD"]):
            return "MDCD5-6"
        elif any(x in code_upper for x in ["MDSWD"]):
            return "MDSWD3-4"
        elif any(x in code_upper for x in ["OT_", "OLD_TSF", "NEW_TSF", "TRTD"]):
            return "OLD_TSF"
        elif any(x in code_upper for x in ["SPCD", "STOCK"]):
            return "STOCKPILE"
        elif any(x in code_upper for x in ["UG2", "NDGWA"]):
            return "UG2_NORTH"
        else:
            return "UNKNOWN"
    
    def _load_inflows(self):
        """Load inflows from template file"""
        if not self.inflows_file.exists():
            logger.warning(f"Inflows template not found: {self.inflows_file}")
            return
        
        try:
            with open(self.inflows_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            self.inflows = []
            current_area = "UNKNOWN"
            
            for line in lines:
                # Check if this is an area header
                if "📍" in line or "🗺️" in line:
                    # Extract area from header like "📍 NDCD1-4 - Merensky North Decline"
                    parts = line.split("-")
                    if len(parts) > 0:
                        header_part = parts[0].replace("📍", "").replace("🗺️", "").strip()
                        # Extract area code (usually first token after emoji)
                        tokens = header_part.split()
                        if tokens:
                            current_area = tokens[0]
                
                # Try to parse as data line
                parsed = self._parse_line(line)
                if parsed:
                    code, name, area_from_line, value = parsed
                    # Use detected area or fall back to area from line
                    area = current_area if current_area != "UNKNOWN" else area_from_line
                    self.inflows.append(BalanceEntry(code, name, area, value))
            
            logger.info(f"✅ Loaded {len(self.inflows)} inflow entries from template")
            
        except Exception as e:
            logger.error(f"Error loading inflows template: {e}")
    
    def _load_outflows(self):
        """Load outflows from template file"""
        if not self.outflows_file.exists():
            logger.warning(f"Outflows template not found: {self.outflows_file}")
            return
        
        try:
            with open(self.outflows_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            self.outflows = []
            current_area = "UNKNOWN"
            
            for line in lines:
                # Check if this is an area header
                if "📍" in line or "🗺️" in line:
                    parts = line.split("-")
                    if len(parts) > 0:
                        header_part = parts[0].replace("📍", "").replace("🗺️", "").strip()
                        tokens = header_part.split()
                        if tokens:
                            current_area = tokens[0]
                
                # Try to parse as data line
                parsed = self._parse_line(line)
                if parsed:
                    code, name, area_from_line, value = parsed
                    area = current_area if current_area != "UNKNOWN" else area_from_line
                    self.outflows.append(BalanceEntry(code, name, area, value))
            
            logger.info(f"✅ Loaded {len(self.outflows)} outflow entries from template")
            
        except Exception as e:
            logger.error(f"Error loading outflows template: {e}")
    
    def _load_recirculation(self):
        """Load dam recirculation from template file"""
        if not self.recirculation_file.exists():
            logger.warning(f"Recirculation template not found: {self.recirculation_file}")
            return
        
        try:
            with open(self.recirculation_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            self.recirculation = []
            current_area = "UNKNOWN"
            
            for line in lines:
                # Check if this is an area header
                if "📍" in line or "🗺️" in line:
                    parts = line.split("-")
                    if len(parts) > 0:
                        header_part = parts[0].replace("📍", "").replace("🗺️", "").strip()
                        tokens = header_part.split()
                        if tokens:
                            current_area = tokens[0]
                
                # Try to parse as data line
                parsed = self._parse_line(line)
                if parsed:
                    code, name, area_from_line, value = parsed
                    area = current_area if current_area != "UNKNOWN" else area_from_line
                    self.recirculation.append(BalanceEntry(code, name, area, value))
            
            logger.info(f"✅ Loaded {len(self.recirculation)} recirculation entries from template")
            
        except Exception as e:
            logger.error(f"Error loading recirculation template: {e}")
    
    def _extract_areas(self):
        """Extract unique areas from all entries"""
        self.areas = set()
        for entry in self.inflows + self.outflows + self.recirculation:
            if entry.area:
                self.areas.add(entry.area)
        
        logger.info(f"Found {len(self.areas)} areas: {sorted(self.areas)}")
    
    def get_total_inflows(self) -> float:
        """Get total inflows"""
        return sum(entry.value_m3 for entry in self.inflows)
    
    def get_total_outflows(self) -> float:
        """Get total outflows"""
        return sum(entry.value_m3 for entry in self.outflows)
    
    def get_total_recirculation(self) -> float:
        """Get total dam recirculation"""
        return sum(entry.value_m3 for entry in self.recirculation)
    
    def get_inflows_by_area(self, area: str) -> List[BalanceEntry]:
        """Get inflows for specific area"""
        return [e for e in self.inflows if e.area == area]
    
    def get_outflows_by_area(self, area: str) -> List[BalanceEntry]:
        """Get outflows for specific area"""
        return [e for e in self.outflows if e.area == area]
    
    def get_recirculation_by_area(self, area: str) -> List[BalanceEntry]:
        """Get recirculation for specific area"""
        return [e for e in self.recirculation if e.area == area]
    
    def get_areas(self) -> List[str]:
        """Get sorted list of areas"""
        return sorted(self.areas)
    
    def reload(self):
        """Reload all templates from files"""
        logger.info("Reloading template data...")
        self._load_all_templates()


# Singleton instance
_parser_instance = None


def get_template_parser() -> TemplateDataParser:
    """Get singleton parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = TemplateDataParser()
    return _parser_instance
