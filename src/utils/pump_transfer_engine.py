"""
Pump Transfer Automation Engine

Handles automatic pump transfers between storage facilities based on:
- Pump start/stop levels
- Transfer destination priority
- Destination facility availability
- 5% increment transfer logic
"""

from datetime import date
from typing import Dict, List, Optional
from utils.app_logger import logger


class PumpTransferEngine:
    """Automates pump transfers between storage facilities"""
    
    # Transfer increment in percentage points
    TRANSFER_INCREMENT = 5.0
    
    def __init__(self, db, calculator):
        """Initialize pump transfer engine
        
        Args:
            db: DatabaseManager instance
            calculator: WaterBalanceCalculator instance
        """
        self.db = db
        self.calculator = calculator
        self._transfer_cache = {}
    
    def calculate_pump_transfers(self, calculation_date: date) -> Dict[str, Dict]:
        """Calculate automatic pump transfers for all facilities
        
        Returns dict of facility transfers (includes all with connections):
        {
            'NDCD1': {
                'current_level_pct': 75.0,
                'pump_start_level': 70.0,
                'is_at_pump_start': True,
                'transfers': [
                    {
                        'destination': 'PLANT_RWD',
                        'priority': 1,
                        'volume_m3': 12500,
                        'reason': 'Normal transfer at pump start'
                    },
                    ...
                ],
                'total_transfer_volume': 12500
            }
        }
        """
        self._transfer_cache.clear()
        all_facilities = self.db.get_storage_facilities()
        
        if not all_facilities:
            return {}
        
        transfers_report = {}
        
        for facility in all_facilities:
            if not facility.get('active'):
                continue
            
            facility_code = facility['facility_code']
            
            # Calculate current level percentage
            current_level_pct = self._get_facility_level_pct(facility)
            pump_start_level = facility.get('pump_start_level', 70.0)
            
            # Check if facility is at pump start level
            is_at_pump_start = current_level_pct >= pump_start_level
            
            # Check if facility has connections configured
            has_connections = bool(facility.get('feeds_to'))
            
            transfers = []
            total_volume = 0
            
            # Only process transfers if at pump start AND has connections
            if is_at_pump_start and has_connections:
                # Get destination facilities in priority order
                destination_codes = [
                    c.strip() for c in facility['feeds_to'].split(',') 
                    if c.strip()
                ]
                
                # Calculate transfers to each destination
                for priority, dest_code in enumerate(destination_codes, 1):
                    dest_facility = self._get_facility_by_code(dest_code, all_facilities)
                    
                    if not dest_facility:
                        logger.warning(f"Destination facility {dest_code} not found for {facility_code}")
                        continue
                    
                    if not dest_facility.get('active'):
                        logger.debug(f"Destination facility {dest_code} is inactive, skipping")
                        continue
                    
                    # Check if destination is full (above pump start level)
                    dest_level_pct = self._get_facility_level_pct(dest_facility)
                    dest_pump_start = dest_facility.get('pump_start_level', 70.0)
                    
                    if dest_level_pct >= dest_pump_start:
                        reason = f"Destination {dest_code} is full ({dest_level_pct:.1f}%), trying next"
                        logger.debug(f"{facility_code}: {reason}")
                        continue  # Skip to next destination
                    
                    # Calculate transfer volume
                    transfer_volume = self._calculate_transfer_volume(
                        facility, dest_facility, current_level_pct
                    )
                    
                    if transfer_volume > 0:
                        transfers.append({
                            'destination': dest_code,
                            'priority': priority,
                            'volume_m3': transfer_volume,
                            'destination_level_before': dest_level_pct,
                            'destination_level_after': self._calc_level_after_transfer(
                                dest_facility, transfer_volume
                            ),
                            'reason': 'Automatic pump transfer'
                        })
                        total_volume += transfer_volume
                        
                        # Only transfer to first non-full destination
                        break
            
            # IMPORTANT: Include ALL facilities with connections, even if no transfer happens
            # This allows users to see what's configured and why transfers didn't occur
            if has_connections:
                transfers_report[facility_code] = {
                    'current_level_pct': current_level_pct,
                    'pump_start_level': pump_start_level,
                    'is_at_pump_start': is_at_pump_start,
                    'transfers': transfers,
                    'total_transfer_volume': total_volume
                }
        
        self._transfer_cache = transfers_report
        return transfers_report
    
    def apply_transfers_to_balance(self, facility_code: str, balance: Dict) -> Dict:
        """Apply calculated transfers to facility water balance
        
        Args:
            facility_code: Code of facility to apply transfers for
            balance: Water balance dict to modify
        
        Returns:
            Modified balance dict
        """
        if facility_code not in self._transfer_cache:
            return balance
        
        transfer_data = self._transfer_cache[facility_code]
        total_transfer = transfer_data['total_transfer_volume']
        
        if total_transfer > 0:
            # Add to outflows
            if 'outflows' not in balance:
                balance['outflows'] = {}
            
            balance['outflows']['pump_transfer'] = total_transfer
            balance['outflows']['total'] = balance['outflows'].get('total', 0) + total_transfer
            
            # Store transfer details
            if 'transfer_details' not in balance:
                balance['transfer_details'] = []
            
            for transfer in transfer_data['transfers']:
                balance['transfer_details'].append(transfer)
        
        return balance
    
    def get_transfer_tracking(self, calculation_date: date) -> Dict:
        """Get human-readable transfer tracking report
        
        Returns:
            Dict with transfer information for all facilities
        """
        if not self._transfer_cache:
            self.calculate_pump_transfers(calculation_date)
        
        return self._transfer_cache
    
    def _get_facility_level_pct(self, facility: Dict) -> float:
        """Get current level percentage for a facility"""
        current_volume = facility.get('current_volume', 0)
        total_capacity = facility.get('total_capacity', 1)
        
        if total_capacity == 0:
            return 0
        
        return (current_volume / total_capacity) * 100
    
    def _get_facility_by_code(self, code: str, facilities: List[Dict]) -> Optional[Dict]:
        """Find facility by code"""
        for fac in facilities:
            if fac['facility_code'].upper() == code.upper():
                return fac
        return None
    
    def _calculate_transfer_volume(self, source: Dict, dest: Dict, source_level_pct: float) -> float:
        """Calculate transfer volume based on 5% increment logic
        
        Transfer down to pump_stop_level in 5% increments
        """
        pump_start = source.get('pump_start_level', 70.0)
        pump_stop = source.get('pump_stop_level', 20.0)
        source_capacity = source.get('total_capacity', 0)
        dest_capacity = dest.get('total_capacity', 0)
        
        if source_capacity == 0 or dest_capacity == 0:
            return 0
        
        # Calculate 5% of source capacity
        transfer_increment_volume = source_capacity * (self.TRANSFER_INCREMENT / 100.0)
        
        # Don't transfer below pump_stop_level
        min_level_pct = pump_stop
        min_level_volume = source_capacity * (min_level_pct / 100.0)
        
        current_volume = source.get('current_volume', 0)
        available_volume = max(0, current_volume - min_level_volume)
        
        # Transfer the lesser of: transfer increment or available volume
        transfer_volume = min(transfer_increment_volume, available_volume)
        
        # Don't overflow destination (leave 5% margin)
        dest_max_safe = dest_capacity * 0.95
        dest_current = dest.get('current_volume', 0)
        available_space = max(0, dest_max_safe - dest_current)
        
        transfer_volume = min(transfer_volume, available_space)
        
        return max(0, transfer_volume)
    
    def _calc_level_after_transfer(self, facility: Dict, transfer_volume: float) -> float:
        """Calculate facility level after receiving transfer"""
        current_volume = facility.get('current_volume', 0)
        total_capacity = facility.get('total_capacity', 1)
        
        new_volume = current_volume + transfer_volume
        return (new_volume / total_capacity) * 100 if total_capacity > 0 else 0
