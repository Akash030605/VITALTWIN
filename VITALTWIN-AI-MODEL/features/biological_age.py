# features/biological_age.py

class BiologicalAgeEngine:
    """
    Feature 4: Calculate biological age vs real age
    Displays aging gap with color-coded result
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.red_risk_years = self.config.get('red_risk_years', 5)
        self.yellow_risk_years = self.config.get('yellow_risk_years', 2)
    
    def calculate(self, real_age, organ_results, health_info):
        """
        Calculate biological age based on health markers
        """
        bio_age = real_age
        
        # === Add years for organ risks ===
        organ_impact = {
            'heart': 3, 'brain': 2, 'liver': 3,
            'kidney': 2, 'lungs': 2
        }
        
        # Compute a combined risk factor from organ results
        combined_risk_factor = 0.0
        for organ, result in organ_results.items():
            # Handle both string and dict formats
            if isinstance(result, dict):
                risk = result.get('current_risk', 0)
                risk_level = result.get('risk_level', self._risk_from_score(risk))
            else:
                # assume a numeric risk
                risk = float(result)
                risk_level = self._risk_from_score(risk)
            
            combined_risk_factor += risk
            # Add direct organ impact based on risk level
            if risk_level == 'RED':
                bio_age += organ_impact.get(organ, 2)
            elif risk_level == 'YELLOW':
                bio_age += organ_impact.get(organ, 1)
        
        # === Lifestyle factors that ADD years (BASE YEARS) ===
        # Use explicit year penalties rather than flat increments
        smoking = health_info.get('Smoking', 'Never')
        sleep = health_info.get('Sleep', 7)
        stress = health_info.get('Stress', 'Medium')
        activity = health_info.get('ActivityLevel', 'Moderate')
        diet = health_info.get('Diet', 'Average')
        
        # Base additions
        if smoking == 'Daily':
            base_smoke = 6
        elif smoking == 'Occasional':
            base_smoke = 2
        else:
            base_smoke = 0
        
        if health_info.get('Alcohol') == 'Daily':
            base_drink = 5
        elif health_info.get('Alcohol') == 'Weekly':
            base_drink = 2
        else:
            base_drink = 0
        
        if sleep and sleep < 6:
            if sleep < 5:
                base_sleep = 3
            else:
                base_sleep = 2
        else:
            base_sleep = 0
        
        base_stress = 2 if stress == 'High' else 0
        base_poor_diet = 2 if diet == 'Poor' else 0
        
        # Compound multiple factors: multiplicative factor on total added years
        base_added = base_smoke + base_drink + base_sleep + base_stress + base_poor_diet
        if base_added > 0:
            # compound factor increases with number of factors
            num_factors = sum(1 for v in [base_smoke, base_drink, base_sleep, base_stress, base_poor_diet] if v > 0)
            compound_factor = 1 + (0.12 * (num_factors - 1))
            bio_age += int(base_added * compound_factor)
        
        # Ensure biological age isn't less than real age for unhealthy people
        if combined_risk_factor > 0.15 or base_added > 0:
            bio_age = max(real_age, int(bio_age))
        else:
            bio_age = max(real_age, int(bio_age))
        
        # Calculate gap
        age_gap = bio_age - real_age
        
        # Determine gap level
        if age_gap <= 0:
            gap_level = "GREEN"
            message = "✅ Your body is aging normally or better than your age!"
        elif age_gap <= 3:
            gap_level = "YELLOW"
            message = f"⚠️ Your body is aging {age_gap} years faster than your real age"
        elif age_gap <= 7:
            gap_level = "ORANGE"
            message = f"⚠️⚠️ Your body is aging {age_gap} years faster! Time for changes"
        else:
            gap_level = "RED"
            message = f"🔴 CRITICAL: Your body is aging {age_gap} years faster! Immediate action needed"
        
        return {
            'real_age': real_age,
            'biological_age': round(bio_age),
            'age_gap': age_gap,
            'gap_level': gap_level,
            'message': message,
            'factors': self._get_factors(organ_results, health_info)
        }

    def _get_factors(self, organ_results, health_info):
        """Get list of factors affecting biological age"""
        factors = []
        
        # Organ risks
        for organ, result in organ_results.items():
            if isinstance(result, dict):
                risk_level = result.get('risk_level', 'GREEN')
            else:
                risk_level = result
                
            if risk_level == 'RED':
                factors.append(f"High {organ} risk (+{self.red_risk_years})")
            elif risk_level == 'YELLOW':
                factors.append(f"Moderate {organ} risk (+{self.yellow_risk_years})")
        
        # Lifestyle
        if health_info.get('Smoking') == 'Daily':
            factors.append("Daily smoking (+6)")
        
        sleep = health_info.get('Sleep', 7)
        if sleep and sleep < 6:
            factors.append("Poor sleep (+2)")
        
        if health_info.get('Stress') == 'High':
            factors.append("High stress (+2)")
        
        if health_info.get('ActivityLevel') == 'Sedentary':
            factors.append("Sedentary lifestyle (+2)")
        
        return factors[:5]  # Top 5 factors
    
    def _risk_from_score(self, score):
        """Map numeric risk score (0-1) to risk level string using same thresholds as BaseOrganModel."""
        try:
            r = float(score)
        except:
            r = 0.0
        if r < 0.25:
            return 'GREEN'
        elif r <= 0.6:
            return 'YELLOW'
        else:
            return 'RED'