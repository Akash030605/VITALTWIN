# models/heart_model.py

from .base_model import BaseOrganModel
import numpy as np

class HeartModel(BaseOrganModel):
    def __init__(self):
        super().__init__('heart')
        self.load_model()
        
        # Define heart conditions and their severity keywords
        self.heart_conditions = {
            'Coronary Artery Disease': {
                'keywords': ['cad', 'coronary artery', 'heart disease', 'coronary heart'],
                'risk': 0.3,
                'severe_keywords': ['severe cad', 'multi-vessel', 'left main', 'unstable'],
                'severe_risk': 0.6
            },
            'Heart Failure': {
                'keywords': ['heart failure', 'chf', 'congestive', 'cardiomyopathy'],
                'risk': 0.4,
                'severe_keywords': ['advanced heart failure', 'stage d', 'refractory', 'ejection fraction < 35'],
                'severe_risk': 0.7
            },
            'Hypertension': {
                'keywords': ['hypertension', 'high bp', 'high blood pressure'],
                'risk': 0.2,
                'severe_keywords': ['malignant hypertension', 'hypertensive crisis', 'resistant hypertension'],
                'severe_risk': 0.4
            },
            'Arrhythmia': {
                'keywords': ['arrhythmia', 'afib', 'atrial fibrillation', 'tachycardia', 'bradycardia', 'palpitations'],
                'risk': 0.2,
                'severe_keywords': ['ventricular tachycardia', 'vtach', 'vfib', 'ventricular fibrillation', 'heart block'],
                'severe_risk': 0.5
            },
            'Valvular Disease': {
                'keywords': ['valve', 'aortic stenosis', 'mitral regurgitation', 'valvular'],
                'risk': 0.25,
                'severe_keywords': ['severe aortic stenosis', 'severe mitral', 'valve replacement needed'],
                'severe_risk': 0.5
            },
            'Myocardial Infarction': {
                'keywords': ['heart attack', 'mi', 'myocardial infarction', 'stemi', 'nstemi'],
                'risk': 0.5,
                'severe_keywords': ['massive mi', 'anterior mi', 'complicated mi'],
                'severe_risk': 0.7
            },
            'Cardiomyopathy': {
                'keywords': ['cardiomyopathy', 'dilated cardiomyopathy', 'hypertrophic', 'hcm'],
                'risk': 0.4,
                'severe_keywords': ['severe cardiomyopathy', 'end-stage', 'ejection fraction < 30'],
                'severe_risk': 0.7
            },
            'Peripheral Artery Disease': {
                'keywords': ['pad', 'peripheral artery', 'peripheral vascular'],
                'risk': 0.3,
                'severe_keywords': ['critical limb ischemia', 'severe pad', 'non-healing ulcer'],
                'severe_risk': 0.5
            },
            'Congenital Heart Disease': {
                'keywords': ['congenital', 'born with', 'heart defect', 'hole in heart'],
                'risk': 0.3,
                'severe_keywords': ['complex congenital', 'unrepaired', 'cyanotic'],
                'severe_risk': 0.6
            },
            'High Cholesterol': {
                'keywords': ['high cholesterol', 'hyperlipidemia', 'hypercholesterolemia', 'high lipids'],
                'risk': 0.15,
                'severe_keywords': ['familial hypercholesterolemia', 'very high ldl', 'statin intolerance'],
                'severe_risk': 0.3
            }
        }
    
    def _parse_medical_conditions(self, medical_conditions):
        """
        Parse medical conditions list to identify heart-specific conditions
        and their severity
        """
        detected_conditions = []
        total_condition_risk = 0.0
        
        if not medical_conditions:
            return detected_conditions, total_condition_risk
        
        for condition in medical_conditions:
            condition_lower = condition.lower()
            
            # Check each heart condition
            for cond_name, cond_info in self.heart_conditions.items():
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
                        
                        # Check for additional severity indicators
                        if any(word in condition_lower for word in ['stage 3', 'stage 4', 'grade 3', 'grade 4', 'advanced']):
                            risk = max(risk, cond_info.get('severe_risk', risk))
                            severity = "Severe"
                        elif any(word in condition_lower for word in ['mild', 'grade 1', 'stage 1']):
                            risk = min(risk, cond_info.get('risk', risk) * 0.7)
                            severity = "Mild"
                        
                        detected_conditions.append({
                            'condition': cond_name,
                            'severity': severity,
                            'risk': round(risk, 2),
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
        
        # Get medical conditions (using existing format)
        medical_conditions = health.get('MedicalConditions', [])
        
        # Parse conditions to get heart-specific risk
        detected_conditions, condition_risk = self._parse_medical_conditions(medical_conditions)
        
        # Extract features for ML model
        feature_vector = self._extract_features(data)
        
        # Use ML model if available
        if self.model is not None and feature_vector is not None:
            try:
                ml_risk = self.predict_risk(feature_vector)
                if ml_risk is not None:
                    base_risk = ml_risk
                else:
                    base_risk = self._rule_based_risk(data)
            except:
                base_risk = self._rule_based_risk(data)
        else:
            base_risk = self._rule_based_risk(data)
        
        # Combine risks (ML risk + condition risk, capped at 1.0)
        # Lifestyle penalties
        lifestyle_penalty = 0.0
        if health.get('Smoking') == 'Daily':
            lifestyle_penalty += 0.22
        elif health.get('Smoking') == 'Occasional':
            lifestyle_penalty += 0.08
        if health.get('Alcohol') == 'Daily':
            lifestyle_penalty += 0.15
        elif health.get('Alcohol') == 'Weekly':
            lifestyle_penalty += 0.06

        # Blood pressure impact
        bp_penalty = 0.0
        systolic = health.get('systolic_bp')
        diastolic = health.get('diastolic_bp')
        if systolic and diastolic:
            if systolic >= 140 or diastolic >= 90:
                bp_penalty += 0.2

        final_risk = min(1.0, (base_risk + condition_risk + lifestyle_penalty + bp_penalty))

        # Enforce minimums for combined daily smoking+alcohol
        if health.get('Smoking') == 'Daily' and health.get('Alcohol') == 'Daily':
            final_risk = max(final_risk, 0.35)
        elif health.get('Smoking') == 'Daily' or health.get('Alcohol') == 'Daily':
            final_risk = max(final_risk, 0.3)

        # Metrics for frontend
        metrics = {
            'blood_pressure_risk': self._get_hypertension_risk(medical_conditions),
            'cholesterol_risk': self._get_cholesterol_risk(medical_conditions),
            'cad_risk': self._get_condition_risk(detected_conditions, 'Coronary Artery Disease'),
            'heart_failure_risk': self._get_condition_risk(detected_conditions, 'Heart Failure'),
            'arrhythmia_risk': self._get_condition_risk(detected_conditions, 'Arrhythmia'),
            'age_risk': min(0.4, age / 150),
            'lifestyle_risk': self._calculate_lifestyle_risk(data),
            'condition_risk': round(condition_risk, 2)
        }

        # Risk progression
        lifestyle_factors = {
            'diet': profile.get('Diet', 'Average'),
            'activity': profile.get('ActivityLevel', 'Moderate'),
            'sleep': health.get('Sleep', 7),
            'stress': health.get('Stress', 'Medium')
        }

        risk_progression = self.project_risk_progression(final_risk, age, lifestyle_factors)
        recommendations = self._get_personalized_recommendations(self.get_risk_level(final_risk), detected_conditions)
        # Add personalized recommendations for smokers/drinkers and BP
        if health.get('Smoking') == 'Daily':
            if "Reduce" not in ''.join(recommendations):
                recommendations.append("Consider nicotine replacement therapy; quitting can add ~5 years to life expectancy")
        if health.get('Alcohol') == 'Daily':
            recommendations.append("Reduce alcohol to weekends only to lower risk; discuss with clinician about liver enzymes")
        if systolic and diastolic and (systolic >= 140 or diastolic >= 90):
            recommendations.append("High blood pressure detected: monitor daily and consult clinician; small reductions can lower heart risk substantially")

        return {
            'current_risk': round(final_risk, 2),
            'risk_level': self.get_risk_level(final_risk),
            'health_score': self.get_health_score(final_risk),
            'metrics': metrics,
            'risk_progression': risk_progression,
            'recommendations': recommendations,
            'heart_conditions': detected_conditions  # Send back for frontend display
        }
    
    def _get_condition_risk(self, detected_conditions, condition_name):
        """Extract risk for a specific condition type"""
        for condition in detected_conditions:
            if condition['condition'] == condition_name:
                return condition['risk']
        return 0.0
    
    def _get_hypertension_risk(self, medical_conditions):
        """Calculate hypertension risk from medical conditions"""
        for condition in medical_conditions:
            cond_lower = condition.lower()
            if 'hypertension' in cond_lower or 'high bp' in cond_lower:
                if any(word in cond_lower for word in ['malignant', 'crisis', 'severe', 'stage 2']):
                    return 0.5
                elif any(word in cond_lower for word in ['stage 1', 'mild']):
                    return 0.3
                return 0.4
        return 0.1
    
    def _get_cholesterol_risk(self, medical_conditions):
        """Calculate cholesterol risk from medical conditions"""
        for condition in medical_conditions:
            cond_lower = condition.lower()
            if 'cholesterol' in cond_lower or 'hyperlipidemia' in cond_lower:
                if any(word in cond_lower for word in ['familial', 'very high', 'severe']):
                    return 0.4
                elif any(word in cond_lower for word in ['borderline', 'mild']):
                    return 0.2
                return 0.3
        return 0.1
    
    def _get_personalized_recommendations(self, risk_level, detected_conditions):
        """Generate recommendations based on risk level and specific conditions"""
        
        # Base recommendations by risk level
        base_recs = {
            'GREEN': [
                "Maintain 30 min exercise 5x weekly",
                "Keep blood pressure in check",
                "Eat heart-healthy diet with fruits and vegetables",
                "Limit saturated fats and sodium"
            ],
            'YELLOW': [
                "Start with 30 min brisk walking daily",
                "Reduce salt intake to control blood pressure",
                "Get cholesterol checked annually",
                "Limit alcohol consumption"
            ],
            'RED': [
                "IMMEDIATE: Consult cardiologist within 1 month",
                "Take prescribed medications regularly",
                "Monitor blood pressure daily",
                "Attend cardiac rehabilitation if recommended"
            ]
        }
        
        # Add condition-specific recommendations
        condition_recs = []
        for condition in detected_conditions:
            cond_name = condition['condition']
            severity = condition['severity']
            
            if 'Coronary Artery Disease' in cond_name:
                condition_recs.append("Take aspirin if prescribed by doctor")
                if severity == 'Severe':
                    condition_recs.append("Consider cardiac catheterization evaluation")
                else:
                    condition_recs.append("Manage cholesterol and blood pressure aggressively")
            
            elif 'Heart Failure' in cond_name:
                condition_recs.append("Monitor weight daily for fluid retention")
                condition_recs.append("Limit fluid and salt intake")
                if severity == 'Severe':
                    condition_recs.append("Discuss advanced therapies with cardiologist")
            
            elif 'Hypertension' in cond_name:
                condition_recs.append("Monitor blood pressure daily at home")
                condition_recs.append("Limit sodium to <1500mg per day")
                if severity == 'Severe':
                    condition_recs.append("Take medications exactly as prescribed")
            
            elif 'Arrhythmia' in cond_name:
                if 'atrial fibrillation' in condition['original_text'].lower():
                    condition_recs.append("Discuss blood thinners with your doctor")
                condition_recs.append("Limit caffeine and alcohol")
                condition_recs.append("Learn to check your own pulse")
            
            elif 'Valvular' in cond_name:
                condition_recs.append("Regular echocardiograms as recommended")
                condition_recs.append("Watch for shortness of breath or chest pain")
                if severity == 'Severe':
                    condition_recs.append("Discuss valve replacement options")
            
            elif 'Myocardial Infarction' in cond_name or 'heart attack' in cond_name:
                condition_recs.append("Complete cardiac rehabilitation program")
                condition_recs.append("Take all medications as prescribed")
                condition_recs.append("Watch for chest pain - seek help immediately")
            
            elif 'Peripheral Artery Disease' in cond_name:
                condition_recs.append("Check feet daily for wounds or discoloration")
                condition_recs.append("Walking exercise can improve symptoms")
                condition_recs.append("Stop smoking immediately")
            
            elif 'High Cholesterol' in cond_name:
                condition_recs.append("Reduce saturated and trans fats")
                condition_recs.append("Increase soluble fiber (oats, beans, fruits)")
                if severity == 'Severe':
                    condition_recs.append("Take statins as prescribed")
        
        # Combine base recommendations with condition-specific ones (remove duplicates)
        all_recs = base_recs[risk_level].copy()
        for rec in condition_recs:
            if rec not in all_recs:
                all_recs.append(rec)
        
        return all_recs[:6]  # Return top 6 recommendations
    
    def _extract_features(self, data):
        """Extract feature vector for ML model"""
        try:
            profile = data.get('ProfileInfo', {})
            health = data.get('HealthInfo', {})
            medical_conditions = health.get('MedicalConditions', [])
            
            # Determine if hypertension/high cholesterol from conditions
            has_hypertension = any('hypertension' in c.lower() or 'high bp' in c.lower() for c in medical_conditions)
            has_high_cholesterol = any('cholesterol' in c.lower() or 'hyperlipidemia' in c.lower() for c in medical_conditions)
            has_diabetes = any('diabetes' in c.lower() for c in medical_conditions)
            
            # Features in order: age, bmi, systolic_bp, diastolic_bp, cholesterol, gluc, smoke, alco, active
            features = [
                profile.get('Age', 50),
                health.get('Bmi', profile.get('Bmi', 25)),
                health.get('systolic_bp', 140 if has_hypertension else 120),
                health.get('diastolic_bp', 90 if has_hypertension else 80),
                health.get('cholesterol', 3 if has_high_cholesterol else 2),
                health.get('gluc', 2 if has_diabetes else 1),
                1 if health.get('Smoking') == 'Daily' else 0,
                1 if health.get('Alcohol') in ['Weekly', 'Daily'] else 0,
                0 if profile.get('ActivityLevel') == 'Sedentary' else 1
            ]
            return features
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None
    
    def _rule_based_risk(self, data):
        """Fallback rule-based calculation"""
        profile = data.get('ProfileInfo', {})
        health = data.get('HealthInfo', {})
        medical_conditions = health.get('MedicalConditions', [])
        
        age = profile.get('Age', 30)
        bmi = health.get('Bmi', profile.get('Bmi', 25))
        
        risk = 0.0
        
        # Age
        if age > 60:
            risk += 0.3
        elif age > 45:
            risk += 0.2
        
        # BMI
        if bmi > 30:
            risk += 0.3
        elif bmi > 25:
            risk += 0.15
        
        # Lifestyle
        if health.get('Smoking') == 'Daily':
            risk += 0.3
        if health.get('Alcohol') == 'Daily':
            risk += 0.2
        
        # Medical conditions - detected by our parser will be added separately
        # This is just base rule-based risk
        
        return min(risk, 1.0)
    
    def _calculate_lifestyle_risk(self, data):
        health = data.get('HealthInfo', {})
        profile = data.get('ProfileInfo', {})
        
        risk = 0.0
        if health.get('Smoking') == 'Daily':
            risk += 0.3
        if health.get('Alcohol') == 'Daily':
            risk += 0.2
        if profile.get('ActivityLevel') == 'Sedentary':
            risk += 0.15
        if health.get('Stress') == 'High':
            risk += 0.1
        
        return min(risk, 0.5)