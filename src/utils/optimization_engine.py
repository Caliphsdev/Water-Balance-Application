"""
Optimization Engine for Water Balance Planning
Suggests operational adjustments to meet target days of operation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List, Optional, Tuple
from datetime import date
import copy

from utils.app_logger import logger


class OptimizationEngine:
    """Optimizes water balance constants to achieve target operational days."""
    
    def __init__(self):
        self.max_iterations = 50
        self.convergence_threshold = 1.0  # days tolerance
    
    def optimize_for_target_days(self, 
                                 target_days: int,
                                 current_storage: float,
                                 daily_consumption: float,
                                 current_constants: Dict[str, float],
                                 constraints: Optional[Dict] = None,
                                 critical_threshold_pct: float = 0.25,
                                 total_capacity: Optional[float] = None) -> Dict:
        """
        Find optimal constant adjustments to achieve target days of operation.
        
        Args:
            target_days: Desired days until critical storage
            current_storage: Current total storage volume (m³)
            daily_consumption: Current daily consumption rate (m³/day)
            current_constants: Dictionary of current constant values
            constraints: Optional dict of {constant_name: (min_val, max_val)}
            critical_threshold_pct: Fraction of capacity considered unusable (default 25%)
            total_capacity: Optional total storage capacity (m³) for accurate thresholding
            
        Returns:
            {
                'achievable': bool,
                'recommended_changes': Dict[constant_name, new_value],
                'projected_days': int,
                'iterations': int,
                'adjustments_pct': Dict[constant_name, pct_change],
                'message': str
            }
        """
        # Ensure current_constants is a dictionary
        if not isinstance(current_constants, dict):
            current_constants = {}
            logger.warning("current_constants is not a dict, using empty dict")
        
        if constraints is None:
            constraints = self._get_default_constraints()
        
        # Calculate current days to critical using provided threshold
        if total_capacity and total_capacity > 0:
            critical_threshold = total_capacity * critical_threshold_pct
        else:
            critical_threshold = current_storage * critical_threshold_pct
        current_days = max(0, (current_storage - critical_threshold) / daily_consumption) if daily_consumption > 0 else 999
        
        # If already meeting target, no optimization needed
        if current_days >= target_days:
            return {
                'achievable': True,
                'recommended_changes': {},
                'projected_days': int(current_days),
                'iterations': 0,
                'adjustments_pct': {},
                'message': f"Current operations already meet target ({current_days:.0f} days available)"
            }
        
        # Initialize best solution
        best_constants = copy.deepcopy(current_constants)
        best_days = current_days
        iteration = 0
        
        # Adjustable constants and their impact on consumption
        adjustable = {
            'tailings_moisture_pct': {
                'impact': 'reduce_consumption',
                'current': current_constants.get('tailings_moisture_pct', 0.15),
                'step': -0.01,
                'direction': -1  # Decrease to reduce water locked in tailings (fraction of mass)
            },
        }
        
        # Gradient descent optimization
        while iteration < self.max_iterations:
            iteration += 1
            improved = False
            
            for const_name, config in adjustable.items():
                # Try adjusting this constant
                current_val = best_constants.get(const_name, config['current'])
                new_val = current_val + (config['step'] * config['direction'])
                
                # Check constraints
                min_val, max_val = self._get_constraint_bounds(const_name, config['current'], constraints)
                if new_val < min_val or new_val > max_val:
                    continue
                
                # Estimate impact on daily consumption
                test_consumption = self._estimate_consumption_impact(
                    daily_consumption, const_name, current_val, new_val, config
                )
                
                test_days = (current_storage - critical_threshold) / test_consumption if test_consumption > 0 else 999
                
                # Accept if improvement
                if test_days > best_days:
                    best_constants[const_name] = new_val
                    best_days = test_days
                    improved = True
                    logger.debug(f"Iteration {iteration}: Adjusted {const_name} to {new_val:.3f}, projected days: {test_days:.1f}")
            
            # Check convergence
            if abs(best_days - target_days) <= self.convergence_threshold:
                break
            
            # No improvement found
            if not improved:
                break
        
        # Calculate percentage changes
        adjustments_pct = {}
        recommended_changes = []
        for const_name, new_val in best_constants.items():
            original = current_constants.get(const_name, adjustable.get(const_name, {}).get('current', new_val))
            if abs(new_val - original) > 0.001:
                pct_change = ((new_val - original) / original * 100) if original != 0 else 0
                adjustments_pct[const_name] = pct_change
                recommended_changes.append({
                    'parameter': const_name,
                    'current': original,
                    'new': new_val,
                    'change_pct': pct_change
                })
        
        # Determine if achievable
        achievable = abs(best_days - target_days) <= target_days * 0.1  # Within 10%
        
        if achievable:
            message = f"Target achievable: {best_days:.0f} days (target {target_days})"
        elif best_days > current_days:
            message = f"Partial improvement: {best_days:.0f} days (target {target_days}, current {current_days:.0f})"
        else:
            message = f"Target not achievable with current constraints. Consider capital improvements (new boreholes, expanded storage)."
        
        return {
            'achievable': achievable,
            'recommended_changes': recommended_changes,
            'projected_days': int(best_days),
            'iterations': iteration,
            'adjustments_pct': adjustments_pct,
            'message': message
        }
    
    def suggest_water_saving_actions(self, 
                                     current_consumption: Dict[str, float],
                                     storage_level_pct: float) -> List[Dict]:
        """
        Generate rule-based water-saving recommendations.
        
        Args:
            current_consumption: Dict of consumption categories with values (m³)
            storage_level_pct: Current storage as percentage of capacity
            
        Returns:
            List of {action: str, category: str, potential_saving_m3: float, priority: str}
        """
        recommendations = []
        
        # Dust suppression optimization
        dust = current_consumption.get('dust_suppression', 0)
        if dust > 5000:
            recommendations.append({
                'action': 'Reduce dust suppression by 15% through targeted spraying and road surface improvements',
                'category': 'Dust Suppression',
                'potential_saving_m3': dust * 0.15,
                'priority': 'high' if storage_level_pct < 30 else 'medium'
            })
        
        # TSF return efficiency
        tsf_return = current_consumption.get('tsf_return', 0)
        plant_consumption = current_consumption.get('plant_consumption_gross', 0)
        if tsf_return < plant_consumption * 0.75:
            potential = plant_consumption * 0.80 - tsf_return
            recommendations.append({
                'action': 'Increase TSF recycling efficiency to 80% through decant system upgrades',
                'category': 'TSF Recycling',
                'potential_saving_m3': potential,
                'priority': 'high'
            })
        
        # Evaporation mitigation
        evaporation = current_consumption.get('evaporation', 0)
        if evaporation > 10000 and storage_level_pct < 40:
            recommendations.append({
                'action': 'Deploy floating covers on main storage dams to reduce evaporation by 30%',
                'category': 'Evaporation',
                'potential_saving_m3': evaporation * 0.30,
                'priority': 'high'
            })
        
        # Mining consumption
        mining_consumption = current_consumption.get('mining_consumption', 0)
        if mining_consumption > 3000:
            recommendations.append({
                'action': 'Optimize mining water usage through improved drilling practices',
                'category': 'Mining',
                'potential_saving_m3': mining_consumption * 0.10,
                'priority': 'medium'
            })
        
        # Discharge reduction (if any)
        discharge = current_consumption.get('discharge', 0)
        if discharge > 1000:
            recommendations.append({
                'action': 'Minimize controlled discharge - recycle or store for future use',
                'category': 'Discharge',
                'potential_saving_m3': discharge * 0.50,
                'priority': 'critical' if storage_level_pct < 25 else 'high'
            })
        
        # Sort by potential saving
        recommendations.sort(key=lambda x: x['potential_saving_m3'], reverse=True)
        
        return recommendations
    
    def _get_default_constraints(self) -> Dict:
        """Return default operational constraints."""
        return {
            'tailings_moisture_pct': {'min_pct': 80, 'max_pct': 100},        # Can reduce moisture to 80%
        }
    
    def _get_constraint_bounds(self, const_name: str, current_value: float, constraints: Dict) -> Tuple[float, float]:
        """Calculate min/max bounds for a constant based on constraints."""
        if const_name not in constraints:
            return (current_value * 0.7, current_value * 1.3)  # Default ±30%

        constraint = constraints[const_name]
        if isinstance(constraint, (tuple, list)) and len(constraint) == 2:
            return (float(constraint[0]), float(constraint[1]))

        min_val = current_value * (constraint.get('min_pct', 70) / 100)
        max_val = current_value * (constraint.get('max_pct', 130) / 100)

        return (min_val, max_val)
    
    def _estimate_consumption_impact(self, 
                                    current_consumption: float,
                                    const_name: str,
                                    old_value: float,
                                    new_value: float,
                                    config: Dict) -> float:
        """
        Estimate how changing a constant affects daily consumption.
        
        Simplified linear model - in production, this would use the full calculator.
        """
        if config['impact'] == 'reduce_consumption':
            # Estimate based on constant type
            if 'recovery' in const_name:
                # Higher recovery = less fresh water needed
                improvement_factor = (new_value - old_value) / old_value
                return current_consumption * (1 - improvement_factor * 0.5)  # 50% efficiency
            elif 'moisture' in const_name:
                # Lower moisture = less water locked in tailings
                reduction_factor = (old_value - new_value) / old_value
                return current_consumption * (1 - reduction_factor * 0.3)  # 30% efficiency
            elif 'evaporation' in const_name:
                # Lower mitigation factor = less evaporation
                reduction = (old_value - new_value) / old_value
                return current_consumption * (1 - reduction * 0.2)  # 20% of consumption is evaporation
        
        return current_consumption  # No change


# Singleton instance
_optimizer_instance = None


def get_optimization_engine() -> OptimizationEngine:
    """Get or create singleton optimization engine instance."""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = OptimizationEngine()
    return _optimizer_instance


def reset_optimization_engine():
    """Reset singleton instance (for testing)."""
    global _optimizer_instance
    _optimizer_instance = None
