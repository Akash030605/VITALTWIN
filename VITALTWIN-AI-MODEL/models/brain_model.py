# models/brain_model.py

from .base_model import BaseOrganModel

class BrainModel(BaseOrganModel):
    def __init__(self):
        super().__init__('brain')
        # No ML model for brain yet, using rule-based
    
    def calculate_risk(self, data):
        profile = data.get('ProfileInfo', {})
        health = data.get('HealthInfo', {})
        
        age = profile.get('Age', 30)
        stress = health.get('Stress', 'Medium')
        sleep = health.get('Sleep', 7)
        medical_conditions = health.get('MedicalConditions', [])
        
        # Calculate risk
        stress_map = {'Low': 0.1, 'Medium': 0.3, 'High': 0.5}
        stress_risk = stress_map.get(stress, 0.3)
        
        if sleep and sleep < 5:
            sleep_risk = 0.5
        elif sleep and sleep < 6:
            sleep_risk = 0.3
        elif sleep and sleep < 7:
            sleep_risk = 0.2
        else:
            sleep_risk = 0.1
        
        bp_risk = 0.3 if 'Hypertension' in medical_conditions else 0.1
        
        age_risk = min(0.4, age / 150)
        
        # Combine with weights - increase importance of stress and sleep
        risk = (
            stress_risk * 0.4 +
            sleep_risk * 0.35 +
            bp_risk * 0.15 +
            age_risk * 0.1
        )
        
        # Enforce minimum if both high stress and poor sleep
        if stress == 'High' and (sleep and sleep < 6):
            risk = max(risk, 0.25)
        
        risk = min(risk, 1.0)
        
        metrics = {
            'stress_risk': stress_risk,
            'sleep_risk': sleep_risk,
            'bp_risk': bp_risk,
            'age_risk': round(age_risk, 2)
        }
        
        lifestyle_factors = {
            'diet': profile.get('Diet', 'Average'),
            'activity': profile.get('ActivityLevel', 'Moderate'),
            'sleep': sleep,
            'stress': stress
        }
        
        risk_progression = self.project_risk_progression(risk, age, lifestyle_factors)
        recommendations = self.get_static_recommendations(self.get_risk_level(risk))
        # Personalized recommendations for high stress / poor sleep
        if stress == 'High':
            recommendations.append("Practice structured stress management: CBT or guided programs; reducing stress can lower brain risk notably")
        if sleep and sleep < 6:
            recommendations.append("Try magnesium 200-400mg before bed and establish sleep hygiene; may improve sleep quality within weeks")

        confidence = self.get_model_confidence()
         
        return {
            'current_risk': round(risk, 2),
            'risk_level': self.get_risk_level(risk),
            'health_score': self.get_health_score(risk),
            'metrics': metrics,
            'risk_progression': risk_progression,
            'recommendations': recommendations
        }
    
    def _green_recommendations(self):
        return [
            "Practice mindfulness 10 min daily",
            "Ensure 7-8 hours of quality sleep",
            "Include omega-3 rich foods in diet",
            "Engage in mentally stimulating activities"
        ]
    
    def _yellow_recommendations(self):
        return [
            "Practice mindfulness 10 min daily for stress reduction",
            "Ensure 7-8 hours of quality sleep",
            "Include omega-3 rich foods in diet",
            "Engage in mentally stimulating activities"
        ]
    
    def _red_recommendations(self):
        return [
            "Consult neurologist for cognitive assessment",
            "Strict stress management program",
            "Consider brain imaging if symptoms develop",
            "Regular cognitive therapy and monitoring"
        ]