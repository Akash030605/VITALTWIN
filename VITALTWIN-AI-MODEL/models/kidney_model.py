# models/kidney_model.py

from .base_model import BaseOrganModel

class KidneyModel(BaseOrganModel):
    def __init__(self):
        super().__init__('kidney')
    
    def calculate_risk(self, data):
        profile = data.get('ProfileInfo', {})
        health = data.get('HealthInfo', {})
        
        age = profile.get('Age', 30)
        bmi = health.get('Bmi', profile.get('Bmi', 25))
        medical_conditions = health.get('MedicalConditions', [])
        diet = profile.get('Diet', 'Average')
        
        # Calculate risk
        bp_risk = 0.4 if 'Hypertension' in medical_conditions else 0.1
        diabetes_risk = 0.5 if 'Diabetes' in medical_conditions else 0.1
        diet_risk = {'Poor': 0.3, 'Average': 0.15, 'Good': 0.05}.get(diet, 0.15)
        bmi_risk = min(0.3, bmi / 70)
        age_risk = min(0.4, age / 150)
        
        risk = (
            bp_risk * 0.3 +
            diabetes_risk * 0.3 +
            diet_risk * 0.2 +
            bmi_risk * 0.1 +
            age_risk * 0.1
        )
        
        risk = min(risk, 1.0)
        
        metrics = {
            'bp_risk': bp_risk,
            'diabetes_risk': diabetes_risk,
            'diet_risk': diet_risk,
            'age_risk': round(age_risk, 2)
        }
        
        lifestyle_factors = {
            'diet': diet,
            'activity': profile.get('ActivityLevel', 'Moderate'),
            'sleep': health.get('Sleep', 7),
            'stress': health.get('Stress', 'Medium')
        }
        
        risk_progression = self.project_risk_progression(risk, age, lifestyle_factors)
        recommendations = self.get_static_recommendations(self.get_risk_level(risk))
        
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
            "Drink 2-3 liters water daily",
            "Reduce salt and processed foods",
            "Monitor blood pressure regularly",
            "Avoid NSAIDs when possible"
        ]
    
    def _yellow_recommendations(self):
        return [
            "Drink 2-3 liters water daily",
            "Reduce salt and processed foods",
            "Monitor blood pressure regularly",
            "Avoid NSAIDs when possible"
        ]
    
    def _red_recommendations(self):
        return [
            "IMMEDIATE: Consult nephrologist, strict BP control",
            "Regular kidney function monitoring, low-protein diet",
            "Avoid all nephrotoxic medications",
            "Monitor electrolytes regularly"
        ]