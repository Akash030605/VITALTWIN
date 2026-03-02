# models/lungs_model.py

from .base_model import BaseOrganModel

class LungsModel(BaseOrganModel):
    def __init__(self):
        super().__init__('lungs')
    
    def calculate_risk(self, data):
        profile = data.get('ProfileInfo', {})
        health = data.get('HealthInfo', {})
        
        age = profile.get('Age', 30)
        smoking = health.get('Smoking', 'Never')
        activity = profile.get('ActivityLevel', 'Moderate')
        medical_conditions = health.get('MedicalConditions', [])
        symptoms = health.get('Symptoms', [])
        
        # Adjusted smoking mapping: Occasional 0.2, Daily 0.35 minimum
        smoking_map = {'Never': 0.0, 'Occasional': 0.2, 'Daily': 0.35}
        smoking_risk = smoking_map.get(smoking, 0.0)
        
        activity_map = {'Sedentary': 0.25, 'Moderate': 0.15, 'Active': 0.05}
        activity_risk = activity_map.get(activity, 0.15)
        
        condition_risk = 0.35 if 'Asthma' in medical_conditions else 0.1
        age_risk = min(0.35, age / 120)
        
        # Symptoms impact: cough, breathlessness
        symptom_penalty = 0.0
        if any('cough' in s.lower() for s in symptoms):
            symptom_penalty += 0.1
        if any('breath' in s.lower() or 'dyspnea' in s.lower() for s in symptoms):
            symptom_penalty += 0.15
        
        # Combine with weights - emphasize smoking
        risk = (
            smoking_risk * 0.45 +
            activity_risk * 0.2 +
            condition_risk * 0.2 +
            age_risk * 0.1
        )
        
        # Add symptom penalty and cap
        risk = min(1.0, risk + symptom_penalty)
        
        # Ensure minimums for smokers
        if smoking == 'Daily':
            risk = max(risk, 0.35)
        elif smoking == 'Occasional':
            risk = max(risk, 0.2)
        
        # Add small compounding if multiple unhealthy habits
        habit_count = 0
        if smoking != 'Never':
            habit_count += 1
        if health.get('Alcohol') in ['Daily', 'Weekly']:
            habit_count += 1
        if profile.get('Diet') == 'Poor':
            habit_count += 1
        if habit_count > 1:
            risk = min(1.0, risk * (1 + 0.06 * (habit_count - 1)))
        
        metrics = {
            'smoking_risk': round(smoking_risk, 2),
            'exercise_risk': round(activity_risk, 2),
            'condition_risk': round(condition_risk, 2),
            'age_risk': round(age_risk, 2),
            'symptom_penalty': round(symptom_penalty, 2)
        }
        
        lifestyle_factors = {
            'diet': profile.get('Diet', 'Average'),
            'activity': activity,
            'sleep': health.get('Sleep', 7),
            'stress': health.get('Stress', 'Medium')
        }
        
        risk_progression = self.project_risk_progression(risk, age, lifestyle_factors)
        recommendations = self.get_static_recommendations(self.get_risk_level(risk))
        
        # Personalized recommendations for smokers/drinkers
        personal_recs = []
        if smoking == 'Daily':
            personal_recs.append("Consider nicotine replacement therapy or prescription aids; quitting can add ~5 years to life expectancy")
        elif smoking == 'Occasional':
            personal_recs.append("Reduce to social use only and consider behavioral support; quitting can add ~2-3 years")
        if health.get('Alcohol') == 'Daily':
            personal_recs.append("Reduce alcohol to weekends only to lower liver enzymes and inflammation")
        
        # Merge and deduplicate
        all_recs = recommendations.copy()
        for r in personal_recs:
            if r not in all_recs:
                all_recs.append(r)
        
        confidence = self.get_model_confidence()
        
        return {
            'current_risk': round(risk, 2),
            'risk_level': self.get_risk_level(risk),
            'health_score': self.get_health_score(risk),
            'metrics': metrics,
            'risk_progression': risk_progression,
            'recommendations': all_recs[:6],
            'model_confidence': round(confidence, 2)
        }
    
    def _green_recommendations(self):
        return [
            "Cardio exercise 3x weekly to improve lung capacity",
            "Avoid exposure to pollutants and smoke",
            "Practice deep breathing exercises",
            "Get flu vaccine annually"
        ]
    
    def _yellow_recommendations(self):
        return [
            "Cardio exercise 3x weekly to improve lung capacity",
            "Avoid exposure to pollutants and smoke",
            "Practice deep breathing exercises",
            "Get flu vaccine annually"
        ]
    
    def _red_recommendations(self):
        return [
            "IMMEDIATE: Quit smoking, consult pulmonologist",
            "Pulmonary rehabilitation program",
            "Regular spirometry, oxygen saturation monitoring",
            "Ongoing respiratory care, flu and pneumonia vaccines"
        ]