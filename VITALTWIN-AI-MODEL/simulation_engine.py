# simulation_engine.py

import json
from datetime import datetime

# Import models
from models.heart_model import HeartModel
from models.brain_model import BrainModel
from models.liver_model import LiverModel
from models.kidney_model import KidneyModel
from models.lungs_model import LungsModel

# Import features
from features.biological_age import BiologicalAgeEngine
from features.future_self import FutureSelfSimulator
from features.stress_heatmap import BodyStressHeatmap
from features.vital_score import VitalScoreGauge
from features.what_if_simulator import WhatIfSimulator

# Add to app.py and simulation_engine.py
import numpy as np
print(f"NumPy version: {np.__version__}")
print(f"NumPy path: {np.__file__}")

# Test if _core exists
try:
    from numpy import _core
    print("✓ numpy._core exists")
except ImportError:
    print("✗ numpy._core missing - using older NumPy")
    # This is actually GOOD - means you're using older NumPy
    

class VitalTwinSimulator:
    """
    Complete VITALTWIN Simulation Engine
    Includes all 8 winning features
    """
    
    def __init__(self, config=None):
        print("\n" + "="*70)
        print("🚀 VITALTWIN SIMULATION ENGINE v2.0")
        print("="*70)
        
        # Load config
        self.config = config or self._load_config()
        
        # Initialize organ models
        print("\n📦 Loading Organ Models...")
        self.models = {
            'heart': HeartModel(),
            'brain': BrainModel(),
            'liver': LiverModel(),
            'kidney': KidneyModel(),
            'lungs': LungsModel()
        }
        
        # Initialize ALL winning features
        print("\n✨ Initializing Winning Features...")
        self.biological_age = BiologicalAgeEngine(self.config.get('biological_age', {}))
        self.future_self = FutureSelfSimulator()
        self.stress_heatmap = BodyStressHeatmap()
        self.vital_score = VitalScoreGauge()
        
        # Initialize what-if simulator with self reference
        self.what_if = WhatIfSimulator(self)
        
        print("\n✅ All systems ready!")
        print("="*70)
    
    def run_simulation(self, user_data, include_what_if=True):
        """
        Run complete health simulation with all features
        
        Args:
            user_data: Input from frontend/backend
            include_what_if: Whether to run what-if simulations
        
        Returns:
            Complete output with all features
        """
        profile = user_data.get('ProfileInfo', {})
        health = user_data.get('HealthInfo', {})
        user_id = profile.get('Userid', 'UNKNOWN')
        
        # === Step 1: Calculate organ risks ===
        organ_results = {}
        for organ_name, model in self.models.items():
            organ_results[organ_name] = model.calculate_risk(user_data)
        
        # === Step 2: Calculate overall health score ===
        overall_score = self._calculate_overall_score(organ_results)
        
        # === Step 3: Feature 4 - Biological Age ===
        bio_age = self.biological_age.calculate(
            profile.get('Age', 30),
            organ_results,
            {**profile, **health}
        )
        
        # === Step 4: Feature 6 - Stress Heatmap ===
        heatmap = self.stress_heatmap.calculate(
            organ_results,
            health,
            profile
        )
        
        # === Step 5: Feature 5 - Future Self Timeline ===
        future = self.future_self.simulate(
            user_data,
            organ_results,
            health,
            bio_age
        )
        
        # === Step 6: Feature 8 - Vital Score Gauge ===
        vital = self.vital_score.calculate(
            overall_score,
            self._get_trend_data(future)
        )
        
        # === Step 7: Feature 7 - What-If Simulations (Optional) ===
        what_if_results = None
        if include_what_if:
            current_results = {
                'overall_health_score': overall_score,
                'biological_age': bio_age,
                'organs': organ_results
            }
            what_if_results = self.what_if.simulate(user_data, current_results)
        
        # === Step 8: Generate priority recommendations ===
        priorities = self._get_priority_recommendations(organ_results, bio_age)
        
        # === Build final output ===
        output = {
            # Basic info
            'user_id': user_id,
            'simulation_date': datetime.utcnow().isoformat() + 'Z',
            
            # Feature 8: Vital Score
            'vital_score': vital,
            
            # Feature 4: Biological Age
            'biological_age': bio_age,
            
            # Feature 6: Stress Heatmap
            'body_stress': heatmap,
            
            # Feature 5: Future Self
            'future_self': future,
            
            # Original organ data
            'organs': organ_results,
            'overall_health_score': overall_score,
            'priority_recommendations': priorities
        }
        
        # Add Feature 7: What-If Simulations (if requested)
        if what_if_results:
            output['what_if_simulations'] = what_if_results

        # Aggregate model confidences to produce system confidence
        model_confidences = [m.get('model_confidence', 0.85) for m in organ_results.values()]
        output['system_confidence'] = round(sum(model_confidences) / len(model_confidences), 2) if model_confidences else 0.85
        
        return output
    
    def simulate_lifestyle_change(self, user_data, changes):
        """
        Simulate a custom lifestyle change (for interactive demo)
        
        Args:
            user_data: Original user data
            changes: Dictionary of changes to apply
        
        Returns:
            New simulation results
        """
        return self.what_if.simulate_custom(user_data, changes)
    
    def _calculate_overall_score(self, organ_results):
        """Calculate overall health score"""
        scores = [o['health_score'] for o in organ_results.values()]
        return round(sum(scores) / len(scores))
    
    def _get_trend_data(self, future):
        """Extract trend data from future timeline"""
        return [point['vitality_score'] for point in future['timeline']]
    
    def _get_priority_recommendations(self, organ_results, bio_age):
        """Get top priority recommendations"""
        priorities = []
        
        # Check biological age gap
        if bio_age['age_gap'] > 7:
            priorities.append({
                'priority': 'CRITICAL',
                'category': 'biological_age',
                'action': 'Immediate lifestyle intervention needed',
                'impact': 'Could reduce biological age by 5-7 years'
            })
        
        # Check organ risks
        for organ, result in organ_results.items():
            risk = result['current_risk']
            level = result['risk_level']
            
            if level == 'RED':
                priorities.append({
                    'priority': 'HIGH',
                    'category': organ,
                    'action': result['recommendations'][0] if result['recommendations'] else f"Consult {organ} specialist",
                    'impact': 'Critical - address within 1 month'
                })
            elif level == 'YELLOW' and len(priorities) < 5:
                priorities.append({
                    'priority': 'MEDIUM',
                    'category': organ,
                    'action': result['recommendations'][0] if result['recommendations'] else f"Monitor {organ} health",
                    'impact': 'Moderate - address within 3 months'
                })
        
        return priorities[:5]
    
    def _load_config(self):
        """Load configuration"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except:
            return {}


# Standalone function for backward compatibility
def run_simulation(user_data):
    """Simple wrapper for backward compatibility"""
    simulator = VitalTwinSimulator()
    return simulator.run_simulation(user_data)