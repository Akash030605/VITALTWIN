# models/liver_model.py

from .base_model import BaseOrganModel
import numpy as np
import json
from pathlib import Path

class LiverModel(BaseOrganModel):
    def __init__(self):
        super().__init__('liver')
        self.class_mapping = None
        self.load_model()
        self._load_class_mapping()
        
        # Define liver conditions and their severity keywords
        self.liver_conditions = {
            'Fatty Liver': {
                'keywords': ['fatty liver', 'nafld', 'nash', 'hepatic steatosis'],
                'risk': 0.3,
                'severe_keywords': ['nash', 'steatohepatitis'],
                'severe_risk': 0.5
            },
            'Cirrhosis': {
                'keywords': ['cirrhosis', 'cirrhotic'],
                'risk': 0.6,
                'severe_keywords': ['decompensated cirrhosis', 'liver failure'],
                'severe_risk': 0.8
            },
            'Hepatitis B': {
                'keywords': ['hepatitis b', 'hbv'],
                'risk': 0.3,
                'severe_keywords': ['chronic hepatitis b', 'hbv cirrhosis'],
                'severe_risk': 0.5
            },
            'Hepatitis C': {
                'keywords': ['hepatitis c', 'hcv'],
                'risk': 0.4,
                'severe_keywords': ['chronic hepatitis c', 'hcv cirrhosis'],
                'severe_risk': 0.6
            },
            'Alcoholic Liver Disease': {
                'keywords': ['alcoholic liver', 'ald'],
                'risk': 0.4,
                'severe_keywords': ['alcoholic hepatitis', 'alcoholic cirrhosis'],
                'severe_risk': 0.7
            },
            'Gilbert Syndrome': {
                'keywords': ['gilbert', 'gilbert syndrome'],
                'risk': 0.1,
                'severe_keywords': [],
                'severe_risk': 0.1
            },
            'Autoimmune Hepatitis': {
                'keywords': ['autoimmune hepatitis', 'aih'],
                'risk': 0.4,
                'severe_keywords': ['severe aih', 'autoimmune cirrhosis'],
                'severe_risk': 0.6
            },
            'Primary Biliary Cholangitis': {
                'keywords': ['pbc', 'primary biliary', 'biliary cirrhosis'],
                'risk': 0.4,
                'severe_keywords': ['advanced pbc', 'pbc cirrhosis'],
                'severe_risk': 0.6
            },
            'Hemochromatosis': {
                'keywords': ['hemochromatosis', 'iron overload'],
                'risk': 0.3,
                'severe_keywords': ['cirrhosis from hemochromatosis'],
                'severe_risk': 0.5
            },
            'Wilson Disease': {
                'keywords': ['wilson', 'wilson disease', 'copper accumulation'],
                'risk': 0.3,
                'severe_keywords': ['neurologic wilson', 'liver failure'],
                'severe_risk': 0.6
            }
        }
    
    def _load_class_mapping(self):
        """Load class mapping if available"""
        class_path = self.models_dir / "liver_classes.json"
        if class_path.exists():
            with open(class_path, 'r') as f:
                self.class_mapping = json.load(f)
    
    def _parse_medical_conditions(self, medical_conditions):
        """
        Parse medical conditions list to identify liver-specific conditions
        and their severity
        """
        detected_conditions = []
        total_condition_risk = 0.0
        
        if not medical_conditions:
            return detected_conditions, total_condition_risk
        
        for condition in medical_conditions:
            condition_lower = condition.lower()
            
            # Check each liver condition
            for cond_name, cond_info in self.liver_conditions.items():
                # Check if this condition matches any keywords
                for keyword in cond_info['keywords']:
                    if keyword in condition_lower:
                        # Check if it's severe
                        is_severe = False
                        for severe_kw in cond_info['severe_keywords']:
                            if severe_kw in condition_lower:
                                is_severe = True
                                break
                        
                        # Add risk based on severity
                        if is_severe:
                            risk = cond_info['severe_risk']
                            severity = "Severe"
                        else:
                            risk = cond_info['risk']
                            severity = "Moderate"
                        
                        detected_conditions.append({
                            'condition': cond_name,
                            'severity': severity,
                            'risk': risk,
                            'original_text': condition
                        })
                        
                        total_condition_risk += risk
                        break  # Found match, move to next condition
        
        return detected_conditions, min(total_condition_risk, 0.9)
    
    def calculate_risk(self, data):
        profile = data.get('ProfileInfo', {})
        health = data.get('HealthInfo', {})
        
        age = profile.get('Age', 30)
        bmi = health.get('Bmi', profile.get('Bmi', 25))
        gender = profile.get('Gender', 'Male')
        
        # Get medical conditions (using existing format)
        medical_conditions = health.get('MedicalConditions', [])
        diet = profile.get('Diet', 'Average')
        alcohol = health.get('Alcohol', 'Never')
        smoking = health.get('Smoking', 'Never')
        
        # Parse conditions to get liver-specific risk
        detected_conditions, condition_risk = self._parse_medical_conditions(medical_conditions)
        
        # Feature vector for ML
        feature_vector = self._extract_features(data)
        
        # === AGE-SPECIFIC BASELINE (20-30: 5-10%) ===
        if 20 <= age <= 30:
            baseline = 0.07
        elif 31 <= age <= 40:
            baseline = 0.08
        elif 41 <= age <= 50:
            baseline = 0.12
        elif 51 <= age <= 60:
            baseline = 0.18
        else:
            baseline = 0.25
        
        # Use ML risk if available
        if self.model is not None and feature_vector is not None:
            ml_risk = self._get_ml_risk(feature_vector)
            base_risk = ml_risk if ml_risk is not None else self._rule_based_risk_fixed(data, baseline)
        else:
            base_risk = self._rule_based_risk_fixed(data, baseline)
        
        # === Estimate AST/ALT if not provided (simple medically-inspired heuristic) ===
        ast = health.get('ast')
        alt = health.get('alt')
        if ast is None or alt is None:
            # Baseline liver enzymes
            est_ast = 20 + max(0, (bmi - 25) * 1.5)
            est_alt = 22 + max(0, (bmi - 25) * 1.5)
            if alcohol == 'Daily':
                est_ast += 12
                est_alt += 15
            ast = ast or est_ast
            alt = alt or est_alt
        
        # === Lifestyle impacts (MEDICALLY-REALISTIC) ===
        lifestyle_penalty = 0.0
        habit_count = 0
        if alcohol == 'Daily':
            lifestyle_penalty += 0.18  # Daily drinking adds 15-20%
            habit_count += 1
        elif alcohol == 'Weekly':
            lifestyle_penalty += 0.08
            habit_count += 1
        elif alcohol == 'Occasional':
            lifestyle_penalty += 0.03
            habit_count += 1
        
        if smoking == 'Daily':
            lifestyle_penalty += 0.05
            habit_count += 1
        elif smoking == 'Occasional':
            lifestyle_penalty += 0.02
            habit_count += 1
        
        if diet == 'Poor':
            lifestyle_penalty += 0.03
            habit_count += 1
        
        # Fatty liver auto-detection: BMI>27 + any alcohol or poor diet => YELLOW
        if bmi > 27 and (alcohol != 'Never' or diet == 'Poor'):
            # Ensure a fatty liver condition is recorded
            if not any(c['condition'] == 'Fatty Liver' for c in detected_conditions):
                detected_conditions.append({
                    'condition': 'Fatty Liver',
                    'severity': 'Moderate',
                    'risk': 0.3,
                    'original_text': 'BMI>27 and lifestyle'
                })
            condition_risk = max(condition_risk, 0.25)
        
        # Combine base risk + condition risk + lifestyle, compound slightly for multiple habits
        compound_multiplier = 1.0 + (0.08 * max(0, habit_count - 1))
        final_risk = min(1.0, (base_risk + condition_risk + lifestyle_penalty) * compound_multiplier)
        
        # Enforce minimums for daily alcohol
        if alcohol == 'Daily':
            final_risk = max(final_risk, 0.4)
        
        # Age capping for younger users: don't allow unrealistic low risks
        if 20 <= age <= 30:
            final_risk = max(final_risk, baseline)
        
        # Override for extremely healthy individuals
        if (bmi < 25 and alcohol in ['Never', 'Occasional'] and len(detected_conditions) == 0 and age < 40):
            final_risk = min(final_risk, 0.12)
        
        # Metrics for frontend
        metrics = {
            'bmi_risk': self._calculate_bmi_risk(bmi),
            'alcohol_risk': self._alcohol_risk(alcohol),
            'diet_risk': self._diet_risk(diet),
            'metabolic_risk': 0.3 if 'Diabetes' in medical_conditions else 0.1,
            'condition_risk': round(condition_risk, 2),
            'age_baseline': round(baseline, 2),
            'ast': round(ast, 1) if ast else None,
            'alt': round(alt, 1) if alt else None
        }
        
        lifestyle_factors = {
            'diet': diet,
            'activity': profile.get('ActivityLevel', 'Moderate'),
            'sleep': health.get('Sleep', 7),
            'stress': health.get('Stress', 'Medium')
        }
        
        risk_progression = self.project_risk_progression(final_risk, age, lifestyle_factors)
        recommendations = self._get_personalized_recommendations(self.get_risk_level(final_risk), detected_conditions)
        
        # Confidence indicator (helps justify high accuracy claim)
        confidence = self.get_model_confidence()
        
        return {
            'current_risk': round(final_risk, 2),
            'risk_level': self.get_risk_level(final_risk),
            'health_score': self.get_health_score(final_risk),
            'metrics': metrics,
            'risk_progression': risk_progression,
            'recommendations': recommendations,
            'liver_conditions': detected_conditions,
            'model_confidence': round(confidence, 2)
        }
    
    def _calculate_bmi_risk(self, bmi):
        """Calculate BMI risk with proper gradation"""
        if bmi > 35:
            return 0.5
        elif bmi > 30:
            return 0.35
        elif bmi > 27:
            return 0.2
        elif bmi > 25:
            return 0.1
        elif bmi > 18.5:
            return 0.02
        else:
            return 0.05
    
    def _rule_based_risk_fixed(self, data, baseline):
        """Fixed rule-based calculation with proper scaling"""
        profile = data.get('ProfileInfo', {})
        health = data.get('HealthInfo', {})
        
        bmi = health.get('Bmi', profile.get('Bmi', 25))
        alcohol = health.get('Alcohol', 'Never')
        
        risk = baseline
        
        if bmi > 35:
            risk += 0.25
        elif bmi > 30:
            risk += 0.15
        elif bmi > 27:
            risk += 0.08
        elif bmi > 25:
            risk += 0.03
        
        if alcohol == 'Daily':
            risk += 0.3
        elif alcohol == 'Weekly':
            risk += 0.15
        elif alcohol == 'Occasional':
            risk += 0.05
        
        diet = profile.get('Diet', 'Average')
        if diet == 'Poor':
            risk += 0.1
        elif diet == 'Good':
            risk -= 0.02
        
        return max(0.02, min(risk, 1.0))
    
    def _get_personalized_recommendations(self, risk_level, detected_conditions):
        """Generate recommendations based on risk level and specific conditions"""
        
        base_recs = {
            'GREEN': [
                "Maintain healthy BMI",
                "Limit alcohol to occasional",
                "Eat balanced diet with limited processed foods",
                "Stay hydrated"
            ],
            'YELLOW': [
                "Reduce alcohol to occasional",
                "Limit fatty and processed foods",
                "Lose 5-10% body weight to reduce fatty liver",
                "Get liver enzyme tests annually"
            ],
            'RED': [
                "IMMEDIATE: Consult hepatologist",
                "Stop alcohol completely",
                "Follow strict liver-friendly diet",
                "Get regular liver function tests"
            ]
        }
        
        condition_recs = []
        for condition in detected_conditions:
            cond_name = condition['condition']
            
            if 'Fatty Liver' in cond_name:
                condition_recs.append("Reduce sugar and refined carbs intake")
                if condition['severity'] == 'Severe':
                    condition_recs.append("Consider vitamin E supplementation (consult doctor)")
            
            elif 'Cirrhosis' in cond_name:
                condition_recs.append("Get screened for varices and liver cancer every 6 months")
                condition_recs.append("Avoid ALL alcohol and NSAIDs")
            
            elif 'Hepatitis' in cond_name:
                condition_recs.append("Consult hepatologist for antiviral treatment")
                condition_recs.append("Get vaccinated for hepatitis A and B")
            
            elif 'Alcoholic Liver' in cond_name:
                condition_recs.append("Complete alcohol cessation required")
                condition_recs.append("Consider addiction counseling and support groups")
            
            elif 'Autoimmune Hepatitis' in cond_name:
                condition_recs.append("Take immunosuppressive medications as prescribed")
                condition_recs.append("Regular monitoring of liver enzymes required")
            
            elif 'PBC' in cond_name or 'Primary Biliary' in cond_name:
                condition_recs.append("Take ursodeoxycholic acid (UDCA) if prescribed")
                condition_recs.append("Monitor for fatigue and itching symptoms")
            
            elif 'Hemochromatosis' in cond_name:
                condition_recs.append("Regular therapeutic phlebotomy as recommended")
                condition_recs.append("Avoid iron supplements and vitamin C")
            
            elif 'Wilson' in cond_name:
                condition_recs.append("Take copper chelation therapy as prescribed")
                condition_recs.append("Avoid copper-rich foods (shellfish, nuts, chocolate)")
        
        all_recs = base_recs.get(risk_level, base_recs['GREEN']).copy()
        for rec in condition_recs:
            if rec not in all_recs:
                all_recs.append(rec)
        
        return all_recs[:6]
    
    def _get_ml_risk(self, feature_vector):
        """Get risk from ML model (handles multiclass)"""
        if self.model is not None:
            try:
                proba = self.model.predict_proba([feature_vector])[0]
                
                if len(proba) > 2:
                    risk = sum(proba[1:])
                else:
                    risk = proba[1] if len(proba) > 1 else proba[0]
                
                return risk
            except:
                return None
        return None
    
    def _extract_features(self, data):
        """Extract feature vector for ML model"""
        try:
            profile = data.get('ProfileInfo', {})
            health = data.get('HealthInfo', {})
            
            features = [
                profile.get('Age', 50),
                health.get('Bmi', profile.get('Bmi', 25)),
                health.get('ast', 30),
                health.get('alt', 30),
                health.get('ggt', 30),
                health.get('glucose', 100)
            ]
            return features
        except:
            return None
    
    def _alcohol_risk(self, alcohol):
        mapping = {'Never': 0.0, 'Occasional': 0.05, 'Weekly': 0.15, 'Daily': 0.3}
        return mapping.get(alcohol, 0.0)
    
    def _diet_risk(self, diet):
        mapping = {'Poor': 0.1, 'Average': 0.0, 'Good': -0.02}
        return mapping.get(diet, 0.0)