# features/stress_heatmap.py

class BodyStressHeatmap:
    """
    Feature 6: Body Stress Heatmap
    Overlay on 3D body showing which systems are under strain
    """
    
    def __init__(self):
        self.stress_factors = {
            'cardiovascular': ['heart', 'blood_pressure'],
            'metabolic': ['liver', 'pancreas', 'glucose'],
            'sleep_debt': ['brain', 'stress'],
            'lifestyle': ['activity', 'diet', 'smoking']
        }
    
    def calculate(self, organ_results, health_info, profile):
        """
        Calculate stress levels for different body systems
        
        Returns:
            Heatmap data for 3D visualization
        """
        # Calculate individual system stresses
        cardiovascular_stress = self._calculate_cardiovascular_stress(organ_results, health_info)
        metabolic_stress = self._calculate_metabolic_stress(organ_results, health_info)
        sleep_debt_stress = self._calculate_sleep_stress(health_info)
        lifestyle_stress = self._calculate_lifestyle_stress(health_info, profile)
        
        # Overall stress
        overall_stress = (
            cardiovascular_stress * 0.3 +
            metabolic_stress * 0.3 +
            sleep_debt_stress * 0.2 +
            lifestyle_stress * 0.2
        )
        
        # Per-organ heatmap zones
        heatmap_zones = []
        for organ, result in organ_results.items():
            strain = result['current_risk']
            
            # Adjust strain based on system contributions
            if organ == 'heart':
                strain = max(strain, cardiovascular_stress)
            elif organ in ['liver']:
                strain = max(strain, metabolic_stress)
            elif organ == 'brain':
                strain = max(strain, sleep_debt_stress)
            
            # Determine color
            if strain < 0.3:
                color = "GREEN"
                intensity = 0.3
            elif strain < 0.7:
                color = "YELLOW"
                intensity = 0.6
            else:
                color = "RED"
                intensity = 0.9
            
            heatmap_zones.append({
                'organ': organ,
                'strain': round(strain, 2),
                'color': color,
                'intensity': intensity,
                'glow': "true" if strain > 0.5 else "false"  # String instead of bool
            })
        
        return {
            'overall_stress': round(overall_stress, 2),
            'overall_level': self._get_stress_level(overall_stress),
            'systems': {
                'cardiovascular': {
                    'stress': round(cardiovascular_stress, 2),
                    'level': self._get_stress_level(cardiovascular_stress),
                    'color': self._get_color(cardiovascular_stress)
                },
                'metabolic': {
                    'stress': round(metabolic_stress, 2),
                    'level': self._get_stress_level(metabolic_stress),
                    'color': self._get_color(metabolic_stress)
                },
                'sleep_debt': {
                    'stress': round(sleep_debt_stress, 2),
                    'level': self._get_stress_level(sleep_debt_stress),
                    'color': self._get_color(sleep_debt_stress)
                },
                'lifestyle': {
                    'stress': round(lifestyle_stress, 2),
                    'level': self._get_stress_level(lifestyle_stress),
                    'color': self._get_color(lifestyle_stress)
                }
            },
            'heatmap_zones': heatmap_zones,
            'visual_overlay': {
                'type': 'gradient',
                'opacity': 0.4,
                'blend_mode': 'multiply'
            }
        }
    
    def _calculate_cardiovascular_stress(self, organ_results, health_info):
        """Calculate cardiovascular system stress"""
        stress = 0.0
        
        # Heart risk
        if 'heart' in organ_results:
            stress += organ_results['heart']['current_risk'] * 0.6
        
        # Blood pressure (from medical conditions)
        if 'Hypertension' in health_info.get('MedicalConditions', []):
            stress += 0.3
        
        return min(stress, 1.0)
    
    def _calculate_metabolic_stress(self, organ_results, health_info):
        """Calculate metabolic system stress"""
        stress = 0.0
        
        # Liver risk
        if 'liver' in organ_results:
            stress += organ_results['liver']['current_risk'] * 0.5
        
        # Diabetes
        if 'Diabetes' in health_info.get('MedicalConditions', []):
            stress += 0.4
        
        # BMI
        bmi = health_info.get('Bmi') or 25
        if bmi > 30:
            stress += 0.3
        elif bmi > 25:
            stress += 0.1
        
        return min(stress, 1.0)
    
    def _calculate_sleep_stress(self, health_info):
        """Calculate sleep debt stress"""
        sleep = health_info.get('Sleep', 7)
        
        if sleep and sleep < 5:
            return 0.9
        elif sleep and sleep < 6:
            return 0.6
        elif sleep and sleep < 7:
            return 0.3
        elif sleep and sleep > 9:
            return 0.2
        else:
            return 0.1
    
    def _calculate_lifestyle_stress(self, health_info, profile):
        """Calculate lifestyle stress"""
        stress = 0.0
        
        # Smoking
        if health_info.get('Smoking') == 'Daily':
            stress += 0.4
        elif health_info.get('Smoking') == 'Occasional':
            stress += 0.2
        
        # Alcohol
        if health_info.get('Alcohol') == 'Daily':
            stress += 0.3
        elif health_info.get('Alcohol') == 'Weekly':
            stress += 0.1
        
        # Activity
        if profile.get('ActivityLevel') == 'Sedentary':
            stress += 0.2
        
        # Diet
        if profile.get('Diet') == 'Poor':
            stress += 0.2
        
        return min(stress, 1.0)
    
    def _get_stress_level(self, stress):
        """Convert stress to level"""
        if stress < 0.3:
            return "LOW"
        elif stress < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _get_color(self, stress):
        """Get color for stress level"""
        if stress < 0.3:
            return "GREEN"
        elif stress < 0.7:
            return "YELLOW"
        else:
            return "RED"