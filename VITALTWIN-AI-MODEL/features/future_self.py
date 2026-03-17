# features/future_self.py

class FutureSelfSimulator:
    """
    Feature 5: Future Self Timeline Simulator
    Shows how the user evolves over 1, 3, 5, 10 years
    """
    
    def __init__(self):
        self.progression_rates = {
            'heart': 0.03,
            'brain': 0.02,
            'liver': 0.04,
            'kidney': 0.025,
            'lungs': 0.02
        }
    
    def simulate(self, current_data, organ_results, health_info, biological_age):
        """
        Generate future self timeline
        
        Args:
            current_data: Original user data
            organ_results: Current organ risks
            health_info: Lifestyle data
            biological_age: Current biological age
        
        Returns:
            Timeline with visual evolution data
        """
        profile = current_data.get('ProfileInfo', {})
        age = profile.get('Age', 30)
        
        # Calculate lifestyle modifier
        lifestyle_modifier = self._get_lifestyle_modifier(health_info, profile)
        
        timeline = []
        years = [0, 1, 3, 5, 10]
        
        for year in years:
            if year == 0:
                # Today
                vitality_score = self._calculate_vitality_score(organ_results)
                bio_age = biological_age['biological_age']
                status = "Current"
                changes = []
                organ_status = {organ: r['risk_level'] for organ, r in organ_results.items()}
            else:
                # Future projection
                vitality_score, organ_status, changes = self._project_year(
                    organ_results, age, year, lifestyle_modifier
                )
                bio_age = biological_age['biological_age'] + (year * 0.5)
                status = f"{year} Year{'s' if year > 1 else ''}"
            
            timeline.append({
                'year': year,
                'label': 'Today' if year == 0 else f'{year} Year',
                'status': status,
                'vitality_score': vitality_score,
                'biological_age': round(bio_age),
                'organ_status': organ_status,
                'changes': changes,
                'visual_cues': self._get_visual_cues(organ_status, year)
            })
        
        return {
            'timeline': timeline,
            'overall_trajectory': self._get_trajectory(timeline)
        }
    
    def _project_year(self, organ_results, age, year, lifestyle_modifier):
        """Project health state for a specific future year"""
        vitality_score = 100
        organ_status = {}
        changes = []
        
        for organ, result in organ_results.items():
            current_risk = result['current_risk']
            rate = self.progression_rates.get(organ, 0.03)
            
            # Age multiplier
            age_multiplier = 1.0
            if age + year > 60:
                age_multiplier = 1.4
            elif age + year > 50:
                age_multiplier = 1.2
            
            # Projected risk
            projected_risk = current_risk + (year * rate * age_multiplier * lifestyle_modifier)
            projected_risk = min(projected_risk, 1.0)
            
            # Determine level
            if projected_risk < 0.3:
                level = "GREEN"
                if current_risk >= 0.3:
                    changes.append(f"{organ.title()} improving")
            elif projected_risk < 0.7:
                level = "YELLOW"
                if current_risk < 0.3:
                    changes.append(f"{organ.title()} showing early warning signs")
            else:
                level = "RED"
                if current_risk < 0.7:
                    changes.append(f"{organ.title()} at critical risk")
            
            organ_status[organ] = level
            vitality_score -= projected_risk * 20
        
        return round(max(vitality_score, 0)), organ_status, changes[:3]
    
    def _get_lifestyle_modifier(self, health_info, profile):
        """Calculate how lifestyle affects progression"""
        modifier = 1.0
        
        # Diet
        diet = profile.get('Diet', 'Average')
        if diet == 'Poor':
            modifier *= 1.2
        elif diet == 'Good':
            modifier *= 0.8
        
        # Activity
        activity = profile.get('ActivityLevel', 'Moderate')
        if activity == 'Sedentary':
            modifier *= 1.2
        elif activity == 'Active':
            modifier *= 0.8
        
        # Sleep
        sleep = health_info.get('Sleep', 7)
        if sleep and sleep < 6:
            modifier *= 1.1
        elif sleep and sleep > 8:
            modifier *= 0.95
        
        # Stress
        stress = health_info.get('Stress', 'Medium')
        if stress == 'High':
            modifier *= 1.15
        elif stress == 'Low':
            modifier *= 0.9
        
        return modifier
    
    def _calculate_vitality_score(self, organ_results):
        """Calculate current vitality score"""
        score = 100
        for result in organ_results.values():
            score -= result['current_risk'] * 20
        return round(max(score, 0))
    
    def _get_visual_cues(self, organ_status, year):
        """Get visual cues for 3D model - return strings, not booleans"""
        cues = []
        
        if year == 0:
            return cues
        
        for organ, level in organ_status.items():
            if level == 'RED' and year >= 1:
                cues.append(f"{organ}_pulsing")
            elif level == 'YELLOW' and year >= 3:
                cues.append(f"{organ}_warning_glow")
        
        return cues[:3]
    
    def _get_trajectory(self, timeline):
        """Determine overall health trajectory"""
        if len(timeline) < 2:
            return "stable"
        
        first_score = timeline[0]['vitality_score']
        last_score = timeline[-1]['vitality_score']
        
        if last_score > first_score + 5:
            return "improving"
        elif last_score < first_score - 10:
            return "declining_rapidly"
        elif last_score < first_score - 5:
            return "declining"
        else:
            return "stable"