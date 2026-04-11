# features/what_if_simulator.py

import copy
import json

class WhatIfSimulator:
    """
    Feature 7: What-If Lifestyle Simulator
    User can simulate improvements and see instant results
    This is your SECRET WEAPON!
    """
    
    def __init__(self, simulator_instance=None):
        """
        Initialize with simulator instance to avoid circular imports
        """
        self.simulator = simulator_instance
        self.scenarios = {
            'quit_smoking': {
                'name': 'Quit Smoking',
                'description': 'Stop smoking completely',
                'changes': {
                    'HealthInfo': {'Smoking': 'Never'}
                },
                'impact': 'high'
            },
            'better_sleep': {
                'name': 'Improve Sleep',
                'description': 'Sleep 8 hours per night',
                'changes': {
                    'HealthInfo': {'Sleep': 8}
                },
                'impact': 'medium'
            },
            'reduce_stress': {
                'name': 'Reduce Stress',
                'description': 'Practice stress management',
                'changes': {
                    'HealthInfo': {'Stress': 'Low'}
                },
                'impact': 'medium'
            },
            'increase_activity': {
                'name': 'Active Lifestyle',
                'description': 'Exercise 30 min daily',
                'changes': {
                    'ProfileInfo': {'ActivityLevel': 'Active'}
                },
                'impact': 'high'
            },
            'healthy_diet': {
                'name': 'Healthy Diet',
                'description': 'Balanced nutrition',
                'changes': {
                    'ProfileInfo': {'Diet': 'Good'}
                },
                'impact': 'medium'
            },
            'reduce_alcohol': {
                'name': 'Reduce Alcohol',
                'description': 'Limit to occasional',
                'changes': {
                    'HealthInfo': {'Alcohol': 'Occasional'}
                },
                'impact': 'medium'
            },
            'all_changes': {
                'name': 'Complete Transformation',
                'description': 'All healthy changes combined',
                'changes': {
                    'HealthInfo': {
                        'Smoking': 'Never',
                        'Sleep': 8,
                        'Stress': 'Low',
                        'Alcohol': 'Never'
                    },
                    'ProfileInfo': {
                        'ActivityLevel': 'Active',
                        'Diet': 'Good'
                    }
                },
                'impact': 'transformative'
            }
        }
    
    def set_simulator(self, simulator_instance):
        """Set simulator instance after creation"""
        self.simulator = simulator_instance
    
    def simulate(self, current_data, current_results):
        """
        Run what-if simulations for all scenarios
        
        Args:
            current_data: Original user data
            current_results: Original simulation results
        
        Returns:
            Comparison of all scenarios
        """
        if not self.simulator:
            return self._get_fallback_scenarios(current_results)
        
        scenarios = []
        
        # Always include current as baseline
        baseline = {
            'id': 'current',
            'name': 'Current Lifestyle',
            'description': 'Your current habits',
            'biological_age': current_results['biological_age']['biological_age'],
            'health_score': current_results['overall_health_score'],
            'risk_level': self._get_overall_risk(current_results),
            'is_current': True
        }
        scenarios.append(baseline)
        
        # Run each scenario
        for scenario_id, scenario in self.scenarios.items():
            # Create modified data
            modified_data = copy.deepcopy(current_data)
            
            # Apply changes
            self._apply_changes(modified_data, scenario['changes'])
            
            # Run simulation
            try:
                new_results = self.simulator.run_simulation(modified_data, include_what_if=False)
                
                # Calculate improvements
                bio_improvement = baseline['biological_age'] - new_results['biological_age']['biological_age']
                health_improvement = new_results['overall_health_score'] - baseline['health_score']
                
                # Determine if this is better than current
                is_better = (
                    new_results['biological_age']['biological_age'] < baseline['biological_age'] or
                    new_results['overall_health_score'] > baseline['health_score']
                )
                
                if is_better:
                    scenarios.append({
                        'id': scenario_id,
                        'name': scenario['name'],
                        'description': scenario['description'],
                        'biological_age': new_results['biological_age']['biological_age'],
                        'health_score': new_results['overall_health_score'],
                        'risk_level': self._get_overall_risk(new_results),
                        'improvements': {
                            'biological_age_reduction': round(bio_improvement, 1),
                            'health_score_increase': round(health_improvement, 1),
                            'years_gained': round(bio_improvement, 1)
                        },
                        'changes': self._format_changes(scenario['changes']),
                        'impact': scenario['impact'],
                        'is_current': False
                    })
            except Exception as e:
                print(f"[WARN] Error simulating {scenario_id}: {e}")
        
        # Sort by impact (best first)
        scenarios.sort(
            key=lambda x: (
                0 if x.get('is_current') is True else 1,
                -x.get('improvements', {}).get('health_score_increase', 0)
            )
        )
        
        return {
            'current': baseline,
            'scenarios': scenarios[1:4],  # Top 3 scenarios
            'best_case': self._find_best_case(scenarios),
            'quick_wins': self._find_quick_wins(scenarios)
        }
    
    def _get_fallback_scenarios(self, current_results):
        """Return fallback scenarios if simulator not available"""
        return {
            'current': {
                'id': 'current',
                'name': 'Current Lifestyle',
                'biological_age': current_results['biological_age']['biological_age'],
                'health_score': current_results['overall_health_score'],
                'is_current': "true"
            },
            'scenarios': [
                {
                    'id': 'quit_smoking',
                    'name': 'Quit Smoking',
                    'description': 'Would reduce biological age by 4 years',
                    'biological_age': current_results['biological_age']['biological_age'] - 4,
                    'health_score': current_results['overall_health_score'] + 8,
                    'improvements': {
                        'years_gained': 4,
                        'health_score_increase': 8
                    },
                    'is_current': "false"
                },
                {
                    'id': 'better_sleep',
                    'name': 'Improve Sleep',
                    'description': 'Would reduce biological age by 2 years',
                    'biological_age': current_results['biological_age']['biological_age'] - 2,
                    'health_score': current_results['overall_health_score'] + 5,
                    'improvements': {
                        'years_gained': 2,
                        'health_score_increase': 5
                    },
                    'is_current': "false"
                }
            ],
            'best_case': {
                'name': 'Quit Smoking',
                'gain': 8
            },
            'quick_wins': [
                {'name': 'Quit Smoking', 'gain': 8},
                {'name': 'Improve Sleep', 'gain': 5}
            ]
        }
    
    def simulate_custom(self, current_data, custom_changes):
        """
        Simulate a custom set of changes (for interactive demo)
        
        Args:
            current_data: Original user data
            custom_changes: Dict of changes to apply
        
        Returns:
            Simulation results with changes
        """
        if not self.simulator:
            return None
        
        modified_data = copy.deepcopy(current_data)
        self._apply_changes(modified_data, custom_changes)
        
        return self.simulator.run_simulation(modified_data, include_what_if=False)
    
    def _apply_changes(self, data, changes):
        """Apply changes to data structure"""
        for category, category_changes in changes.items():
            if category in data:
                for key, value in category_changes.items():
                    data[category][key] = value
    
    def _get_overall_risk(self, results):
        """Get overall risk level"""
        organs = results.get('organs', {})
        risk_levels = [o.get('risk_level', 'GREEN') for o in organs.values()]
        
        if 'RED' in risk_levels:
            return 'RED'
        elif 'YELLOW' in risk_levels:
            return 'YELLOW'
        else:
            return 'GREEN'
    
    def _format_changes(self, changes):
        """Format changes for display"""
        formatted = []
        for category, cat_changes in changes.items():
            for key, value in cat_changes.items():
                formatted.append(f"{key}: {value}")
        return formatted
    
    def _find_best_case(self, scenarios):
        """Find the best possible outcome"""
        best = None
        best_score = 0
        
        for s in scenarios:
            if s.get('is_current') == "true":
                continue
            score = s.get('health_score', 0)
            if score > best_score:
                best_score = score
                best = s
        
        return best
    
    def _find_quick_wins(self, scenarios):
        """Find changes with biggest impact"""
        quick_wins = []
        
        for s in scenarios[1:]:  # Skip current
            if s.get('impact') == 'high' and s.get('improvements', {}).get('health_score_increase', 0) > 5:
                quick_wins.append({
                    'name': s['name'],
                    'gain': s['improvements']['health_score_increase']
                })
        
        return quick_wins[:2]