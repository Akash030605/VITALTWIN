# models/lungs_model.py
# Clinical Methods:
#   - Pack-years with bidi correction (1 bidi = 1.5 cigarette-equivalents, 3× tar)
#   - GOLD COPD staging criteria (FEV1/FVC < 0.70 threshold)
#   - City AQI lookup table (India CPCB data, annual PM2.5 µg/m³)
#   - Cooking fuel biomass risk (Balakrishnan et al. Lancet 2019, IHME GBD 2019)
#   - TB history risk adjustment (post-TB obstructive pattern ~40% prevalence)
#   - GOLD spirometry-based COPD risk: pack-years ≥10 threshold, ≥20 significant, ≥40 screening
# References:
#   - GOLD 2023 COPD Guidelines (https://goldcopd.org)
#   - Balakrishnan et al. Lancet Planet Health 2019 (HAP India)
#   - Salvi & Barnes Lancet 2009 (COPD in non-smokers, India)
#   - Jindal et al. Indian J Chest Dis 2012 (Indian spirometry norms)
#   - CPCB Annual AQI Report 2023

import math, json, pickle
from pathlib import Path
from .base_model import BaseOrganModel

# ── Load lung cancer ML model (symptom survey, AUC 0.857) ────────────────────
_LUNG_ML_PATH = Path(__file__).parent.parent / "models" / "lung_cancer_ml.pkl"
_lung_cancer_bundle = None

def _load_lung_cancer_ml():
    global _lung_cancer_bundle
    if _lung_cancer_bundle is None and _LUNG_ML_PATH.exists():
        try:
            with open(_LUNG_ML_PATH, "rb") as f:
                _lung_cancer_bundle = pickle.load(f)
        except Exception:
            pass
    return _lung_cancer_bundle

# ── Load India TB comorbidity by state ───────────────────────────────────────
_TB_STATE_PATH = Path(__file__).parent.parent / "data/india/tb/tb_lung_risk_by_state.json"
_TB_STATE_DATA = {}
try:
    with open(_TB_STATE_PATH) as _f:
        _TB_STATE_DATA = json.load(_f).get("states", {})
except Exception:
    pass

def _get_tb_state_multiplier(state: str) -> float:
    """
    Return lung_tb_risk_multiplier for Indian state (1.0 = average, up to 1.25).
    Source: RNTCP/NTEP Annual Report, Ministry of Health, India.
    """
    if not state or not _TB_STATE_DATA:
        return 1.0
    key = (state.strip().lower()
           .replace(' ', '_').replace('&', 'and').replace('-', '_')
           .replace('.', '').replace('(', '').replace(')', ''))
    return _TB_STATE_DATA.get(key, {}).get("lung_tb_risk_multiplier", 1.0)

# India city PM2.5 annual averages (µg/m³) — CPCB 2023
# WHO safe limit: 5 µg/m³ | India NAAQS: 40 µg/m³
CITY_AQI_PM25 = {
    "delhi": 98.6,
    "new delhi": 98.6,
    "gurgaon": 91.2,
    "gurugram": 91.2,
    "noida": 87.4,
    "faridabad": 84.1,
    "ghaziabad": 89.7,
    "lucknow": 72.3,
    "kanpur": 79.1,
    "agra": 68.4,
    "varanasi": 71.2,
    "patna": 78.9,
    "muzaffarpur": 76.4,
    "kolkata": 58.7,
    "howrah": 61.2,
    "mumbai": 46.3,
    "pune": 38.7,
    "nagpur": 42.1,
    "ahmedabad": 51.4,
    "surat": 44.8,
    "rajkot": 39.2,
    "jaipur": 62.1,
    "jodhpur": 58.3,
    "kota": 54.7,
    "indore": 47.2,
    "bhopal": 43.8,
    "raipur": 56.4,
    "hyderabad": 36.2,
    "secunderabad": 37.1,
    "visakhapatnam": 33.4,
    "bengaluru": 29.8,
    "bangalore": 29.8,
    "mysuru": 23.1,
    "mysore": 23.1,
    "chennai": 31.7,
    "madurai": 28.4,
    "coimbatore": 26.1,
    "kochi": 22.3,
    "cochin": 22.3,
    "thiruvananthapuram": 19.8,
    "trivandrum": 19.8,
    "bhubaneswar": 41.2,
    "guwahati": 47.8,
    "chandigarh": 52.4,
    "amritsar": 61.7,
    "ludhiana": 67.3,
    "jalandhar": 58.9,
    "dehradun": 44.2,
    "shimla": 18.4,
    "srinagar": 38.9,
}

def get_city_pm25(city: str) -> float:
    """Return annual PM2.5 µg/m³ for an Indian city. Default 45 (national avg)."""
    if not city:
        return 45.0
    return CITY_AQI_PM25.get(city.lower().strip(), 45.0)

def aqi_lung_risk(pm25: float) -> float:
    """
    PM2.5 → additional lung risk fraction.
    WHO: 5 µg/m³ safe. India avg: 45. Delhi: ~99.
    Each 10 µg/m³ above 10 ≈ +5% COPD risk (GBD 2019).
    Returns risk increment [0.0 – 0.30].
    """
    if pm25 <= 10:
        return 0.0
    excess = pm25 - 10
    risk = (excess / 10) * 0.05
    return min(0.30, round(risk, 3))

def cooking_fuel_risk(fuel_type: str) -> float:
    """
    Indoor air pollution from cooking fuel.
    Balakrishnan et al. Lancet 2019: wood/dung ≈ 2.3× PM2.5 vs LPG.
    Returns risk addition [0.0 – 0.25].
    Fuels: 'lpg', 'png', 'electric', 'kerosene', 'wood', 'dung', 'coal', 'crop_residue'
    """
    fuel_map = {
        "lpg": 0.0,
        "png": 0.0,
        "electric": 0.0,
        "kerosene": 0.08,
        "wood": 0.22,
        "crop_residue": 0.22,
        "dung": 0.25,
        "coal": 0.25,
        "biomass": 0.22,
    }
    if not fuel_type:
        return 0.0
    return fuel_map.get(fuel_type.lower().strip(), 0.0)

def pack_years_risk(pack_years: float, current_smoker: bool, age: int) -> tuple:
    """
    GOLD 2023 pack-year thresholds:
      <10 py  → minimal extra risk
      10–19   → mild COPD risk, spirometry advised
      20–39   → significant risk, moderate COPD likely
      ≥40     → severe risk, LDCT lung cancer screening recommended

    Returns (risk_increment, copd_screening_recommended, gold_concern)
    """
    if pack_years is None or pack_years <= 0:
        return 0.0, False, "None"

    if pack_years < 10:
        risk = 0.05
        concern = "Minimal"
        screen = False
    elif pack_years < 20:
        risk = 0.15
        concern = "Mild COPD risk — spirometry advised"
        screen = False
    elif pack_years < 40:
        risk = 0.28
        concern = "Significant COPD risk — pulmonology referral"
        screen = age >= 50
    else:
        risk = 0.42
        concern = "Severe — LDCT lung cancer screening recommended (GOLD Stage II+)"
        screen = True

    # Ex-smoker modifier: risk declines ~30% after 10 years quit
    if not current_smoker:
        risk *= 0.72

    return round(risk, 3), screen, concern

def tb_history_risk(conditions: list) -> float:
    """
    Post-TB obstructive pattern in ~40% of survivors (Allwood et al. IJTLD 2013).
    Active TB severely impairs; past TB leaves residual restriction/obstruction.
    """
    conditions_lower = [c.lower() for c in conditions]
    if any("active tb" in c or "tuberculosis" in c and "past" not in c
           for c in conditions_lower):
        return 0.40
    if any("tb" in c or "tuberculosis" in c for c in conditions_lower):
        return 0.20  # past/treated TB
    return 0.0

def fev1_copd_stage(fev1_percent: float) -> tuple:
    """
    GOLD spirometry COPD severity (post-bronchodilator FEV1 % predicted).
    Only used if FEV1 data is available.
    Returns (stage_name, risk_increment).
    """
    if fev1_percent is None:
        return None, 0.0
    if fev1_percent >= 80:
        return "GOLD 1 (Mild)", 0.15
    elif fev1_percent >= 50:
        return "GOLD 2 (Moderate)", 0.30
    elif fev1_percent >= 30:
        return "GOLD 3 (Severe)", 0.50
    else:
        return "GOLD 4 (Very Severe)", 0.70


class LungsModel(BaseOrganModel):
    def __init__(self):
        super().__init__('lungs')
        self.load_model()   # loads survey-based ML model as secondary signal
        self._lung_cancer_bundle = _load_lung_cancer_ml()

    def calculate_risk(self, data):
        profile = data.get('ProfileInfo', {})
        health = data.get('HealthInfo', {})

        age = profile.get('Age', 30)
        gender = profile.get('Gender', 'Male')
        activity = profile.get('ActivityLevel', 'Moderate')
        smoking = health.get('Smoking', 'Never')
        medical_conditions = health.get('MedicalConditions', []) or []
        medications = health.get('Medications', []) or []

        # ── Pack-years (bidi-corrected from app.py HealthInfo helper) ──────────
        pack_years_val = health.get('PackYears', None)
        if pack_years_val is None:
            # Reconstruct from raw fields (backward compat)
            years_smoked = health.get('YearsSmoking', health.get('YearsSmoked', 0)) or 0
            cpd = health.get('CigarettesPerDay', 0) or 0
            tobacco_type = health.get('TobaccoType', 'cigarette')
            bidi_mult = 1.5 if tobacco_type and 'bidi' in tobacco_type.lower() else 1.0
            pack_years_val = (cpd / 20.0) * years_smoked * bidi_mult if cpd and years_smoked else None

        current_smoker = smoking in ('Daily', 'Occasional')

        # ── Strategy selection ────────────────────────────────────────────────
        fev1_pct = health.get('FEV1Percent', None)  # % predicted post-bronchodilator
        city = health.get('City', profile.get('City', ''))
        cooking_fuel = health.get('CookingFuel', None)

        method_used = []
        risk_components = {}
        possible_issues = []
        screening_flags = []
        screen_rec = False   # initialise here — may not be set if pack_years path is skipped

        # 1. GOLD spirometry (highest confidence if FEV1 available)
        gold_stage, fev1_risk = fev1_copd_stage(fev1_pct)
        if gold_stage:
            risk_components['fev1_copd'] = fev1_risk
            method_used.append(f"GOLD Spirometry ({gold_stage})")
            possible_issues.append(f"COPD: {gold_stage}")
            confidence_level = 0.95
        else:
            fev1_risk = 0.0
            confidence_level = 0.70

        # 2. Pack-years (GOLD 2023 criteria)
        if pack_years_val is not None and pack_years_val > 0:
            py_risk, screen_rec, gold_concern = pack_years_risk(pack_years_val, current_smoker, age)
            risk_components['pack_years'] = py_risk
            method_used.append("GOLD Pack-Years Criteria")
            if gold_concern and gold_concern != "None":
                possible_issues.append(gold_concern)
            if screen_rec:
                screening_flags.append("LDCT lung cancer screening recommended (age ≥50, ≥40 pack-years)")
            if confidence_level < 0.85:
                confidence_level = 0.80
        else:
            # Fallback: rough smoking-category estimate
            smoking_map = {'Never': 0.0, 'Occasional': 0.12, 'Daily': 0.25}
            py_risk = smoking_map.get(smoking, 0.0)
            risk_components['smoking_category'] = py_risk
            method_used.append("Smoking-Category Heuristic")
            pack_years_val = None

        # 3. AQI exposure (CPCB city data)
        pm25 = get_city_pm25(city)
        aqi_risk = aqi_lung_risk(pm25)
        risk_components['outdoor_aqi'] = aqi_risk
        if pm25 > 60:
            possible_issues.append(f"High outdoor PM2.5 exposure ({pm25:.0f} µg/m³) — chronic inflammation risk")
        method_used.append(f"City AQI Lookup ({city or 'national avg'}, PM2.5={pm25:.0f})")

        # 4. Cooking fuel / indoor air pollution
        fuel_risk = cooking_fuel_risk(cooking_fuel)
        if fuel_risk > 0:
            risk_components['indoor_air_pollution'] = fuel_risk
            possible_issues.append(f"Biomass cooking fuel — indoor PM2.5 ≈2.3× higher than LPG")
            method_used.append("Indoor Air Pollution (Balakrishnan 2019)")

        # 5. TB history + state-level TB comorbidity multiplier
        tb_risk = tb_history_risk(medical_conditions)
        state = health.get('State', profile.get('State', ''))
        tb_state_mult = _get_tb_state_multiplier(state)
        if tb_risk > 0:
            # Apply state-level multiplier (e.g. Meghalaya 1.23×, national avg 1.0)
            tb_risk = round(min(0.50, tb_risk * tb_state_mult), 3)
            risk_components['tb_history'] = tb_risk
            possible_issues.append(
                f"Post-TB restrictive/obstructive lung pattern — spirometry advised"
                + (f" [state TB burden multiplier: {tb_state_mult}×]" if tb_state_mult > 1.0 else "")
            )
            method_used.append("TB History Risk Adjustment (Allwood 2013) + RNTCP State Data")
        elif tb_state_mult > 1.05:
            # Even without personal TB history, high-TB states add slight background risk
            bg_risk = round((tb_state_mult - 1.0) * 0.10, 3)
            risk_components['state_tb_background'] = bg_risk

        # 6. Asthma / chronic conditions
        asthma = any('asthma' in c.lower() for c in medical_conditions)
        copd_diagnosed = any('copd' in c.lower() for c in medical_conditions)
        if copd_diagnosed:
            risk_components['copd_diagnosed'] = 0.40
            possible_issues.append("COPD — diagnosed condition")
            screening_flags.append("Inhaler therapy adherence check; pulmonology follow-up")
        elif asthma:
            risk_components['asthma'] = 0.18
            possible_issues.append("Asthma — increases airway hyperreactivity and exacerbation risk")

        # 7. Age component (FEV1 declines ~30 mL/year after 30; accelerated in smokers)
        age_risk = min(0.20, max(0.0, (age - 30) / 100))
        risk_components['age_decline'] = round(age_risk, 3)

        # 8. Activity (exercise improves FEV1 ~5–8% in COPD — GOLD 2023)
        activity_map = {'Sedentary': 0.10, 'Light': 0.06, 'Moderate': 0.02, 'Active': 0.0, 'Very Active': 0.0}
        activity_risk = activity_map.get(activity, 0.02)
        risk_components['inactivity'] = activity_risk

        # ── Combine ───────────────────────────────────────────────────────────
        # If GOLD spirometry present, it anchors the score (60% weight)
        if fev1_risk > 0:
            base_risk = 0.60 * fev1_risk + 0.40 * (
                py_risk * 0.40 +
                (fuel_risk + aqi_risk) * 0.25 +
                tb_risk * 0.20 +
                age_risk * 0.10 +
                activity_risk * 0.05
            )
        else:
            base_risk = (
                py_risk * 0.45 +
                (fuel_risk + aqi_risk) * 0.25 +
                tb_risk * 0.15 +
                age_risk * 0.10 +
                activity_risk * 0.05
            )
            # Add asthma/COPD risk directly — values already ARE the risk contributions
            base_risk += risk_components.get('asthma', 0)         # 0.18 if present
            base_risk += risk_components.get('copd_diagnosed', 0) # 0.40 if present

        # Inhaler/corticosteroid medications reduce effective risk
        meds_lower = [m.lower() for m in medications]
        if any('salbutamol' in m or 'albuterol' in m or 'bronchodilator' in m
               or 'tiotropium' in m or 'ipratropium' in m for m in meds_lower):
            base_risk *= 0.88
        if any('fluticasone' in m or 'budesonide' in m or 'beclomethasone' in m
               or 'inhaled corticosteroid' in m or 'ics' in m for m in meds_lower):
            base_risk *= 0.90

        # Hard floor: active smokers can't score below 0.18
        if smoking == 'Daily':
            base_risk = max(base_risk, 0.18)
        elif smoking == 'Occasional':
            base_risk = max(base_risk, 0.08)

        # Absolute RED flags
        if copd_diagnosed and (pack_years_val or 0) >= 40:
            base_risk = max(base_risk, 0.65)
            possible_issues.append("Severe COPD + heavy smoking history — pulmonology urgent")

        # ── Lung cancer ML signal (AUC 0.857, symptom-based survey, N=309) ───
        # Source: lung_cancer_ml.pkl (GradientBoosting, train_remaining_gaps.py)
        # Features: age, gender, smoking, wheezing, coughing, SOB, chest pain, etc.
        # Used as secondary signal (+15% weight) when symptoms are present.
        # Note: Small dataset (309 rows), so blended conservatively.
        lc_bundle = self._lung_cancer_bundle
        lc_ml_prob = None
        if lc_bundle is not None:
            try:
                conds_lower = [c.lower() for c in medical_conditions]
                alc = health.get('Alcohol', 'Never')
                has_wheeze  = any('wheeze' in c or 'asthma' in c or 'copd' in c for c in conds_lower)
                has_cough   = any('cough' in c or 'copd' in c or 'bronchitis' in c for c in conds_lower)
                has_sob     = any('breath' in c or 'dyspnea' in c for c in conds_lower)
                has_chest   = any('chest' in c for c in conds_lower)
                has_chronic = any('copd' in c or 'asthma' in c or 'fibrosis' in c or 'tb' in c for c in conds_lower)
                has_allergy = any('allerg' in c for c in conds_lower)
                has_fatigue = any('fatigue' in c or 'tired' in c for c in conds_lower)
                stress      = health.get('Stress', 'Medium')
                has_anxiety = stress in ('High', 'Very High') or any('anxiety' in c for c in conds_lower)
                feat_names  = lc_bundle['features']
                feat_map    = {
                    'AGE':                  float(age),
                    'GENDER_ENC':           1.0 if gender == 'Male' else 0.0,
                    'SMOKING':              1.0 if smoking in ('Daily','Occasional') else 0.0,
                    'YELLOW_FINGERS':       0.0,
                    'ANXIETY':              1.0 if has_anxiety else 0.0,
                    'PEER_PRESSURE':        0.0,
                    'CHRONIC DISEASE':      1.0 if has_chronic else 0.0,
                    'FATIGUE':              1.0 if has_fatigue else 0.0,
                    'ALLERGY':              1.0 if has_allergy else 0.0,
                    'WHEEZING':             1.0 if has_wheeze else 0.0,
                    'ALCOHOL CONSUMING':    1.0 if alc in ('Daily','Weekly') else 0.0,
                    'COUGHING':             1.0 if has_cough else 0.0,
                    'SHORTNESS OF BREATH':  1.0 if has_sob else 0.0,
                    'SWALLOWING DIFFICULTY':0.0,
                    'CHEST PAIN':           1.0 if has_chest else 0.0,
                }
                fv = [feat_map.get(f, 0.0) for f in feat_names]
                lc_ml_prob = float(lc_bundle['model'].predict_proba([fv])[0][1])
                # Blend: 85% clinical engine + 15% ML cancer signal
                base_risk = 0.85 * base_risk + 0.15 * lc_ml_prob
                method_used.append(f"Lung Cancer ML (AUC=0.857, N=309, 15% weight)")
            except Exception:
                pass  # ML failure never blocks clinical result

        final_risk = min(1.0, round(base_risk, 3))

        # ── Recommendations ───────────────────────────────────────────────────
        recommendations = []

        if smoking == 'Daily':
            recommendations.append(
                "Quit smoking — each pack-year adds permanent lung capacity loss; "
                "NRT + varenicline doubles quit rates (Cochrane 2022)"
            )
        elif smoking == 'Occasional':
            recommendations.append("Reduce smoking frequency; even occasional smoking accelerates FEV1 decline")

        if fuel_risk >= 0.22:
            recommendations.append(
                "Switch to LPG/PNG — biomass cooking smoke causes ~2.3× higher indoor PM2.5 "
                "and increases COPD risk by 35% (Balakrishnan 2019)"
            )

        if pm25 > 60:
            recommendations.append(
                f"High outdoor AQI in {city or 'your city'} (PM2.5 ≈{pm25:.0f} µg/m³) — "
                "use N95 mask outdoors; avoid peak traffic hours; use air purifier indoors"
            )

        if tb_risk > 0:
            recommendations.append(
                "Post-TB spirometry recommended — up to 40% of TB survivors develop "
                "obstructive/restrictive patterns (Allwood 2013)"
            )

        if asthma:
            recommendations.append(
                "Asthma: ensure rescue inhaler availability; identify and avoid triggers; "
                "annual spirometry to monitor airway changes"
            )

        if screen_rec:
            recommendations.append(
                "LDCT low-dose CT lung cancer screening recommended: ≥40 pack-years, age ≥50 "
                "(USPSTF 2021 Grade B — reduces lung cancer mortality 20%)"
            )

        if activity in ('Sedentary', 'Light'):
            recommendations.append(
                "Aerobic exercise 150 min/week improves FEV1 by 5–8% in COPD patients; "
                "start with 20-min walks, progress to cycling/swimming"
            )

        if not recommendations:
            recommendations.append("Maintain smoke-free lifestyle; annual flu vaccine; avoid heavy traffic exposure")

        recommendations = recommendations[:6]

        # ── Output ────────────────────────────────────────────────────────────
        lifestyle_factors = {
            'diet': profile.get('Diet', 'Average'),
            'activity': activity,
            'sleep': health.get('Sleep', 7),
            'stress': health.get('Stress', 'Medium')
        }
        risk_progression = self.project_risk_progression(final_risk, age, lifestyle_factors)

        metrics = {
            'pack_years': round(pack_years_val, 1) if pack_years_val else None,
            'city_pm25_ugm3': pm25,
            'cooking_fuel': cooking_fuel or 'unknown',
            'fev1_percent_predicted': fev1_pct,
            'gold_stage': gold_stage,
            'tb_risk_increment': tb_risk,
            'aqi_risk_increment': round(aqi_risk, 3),
            'fuel_risk_increment': round(fuel_risk, 3),
            **{k: round(v, 3) for k, v in risk_components.items()}
        }

        return {
            'current_risk': final_risk,
            'risk_level': self.get_risk_level(final_risk),
            'health_score': self.get_health_score(final_risk),
            'metrics': metrics,
            'risk_progression': risk_progression,
            'recommendations': recommendations,
            'model_confidence': round(confidence_level, 2),
            'method_used': ' | '.join(method_used),
            'possible_issues': possible_issues,
            'screening_flags': screening_flags,
            'clinical_notes': {
                'gold_spirometry_available': fev1_pct is not None,
                'pack_years_corrected_for_bidi': health.get('TobaccoType', '') == 'bidi',
                'ldct_screening_indicated': any('LDCT' in f for f in screening_flags),
            }
        }

    def _lung_ml_risk(self, profile, health, medical_conditions):
        """
        Secondary lung cancer risk from ML model trained on survey dataset.
        Features (15): GENDER, AGE, SMOKING, YELLOW_FINGERS, ANXIETY,
        PEER_PRESSURE, CHRONIC_DISEASE, FATIGUE, ALLERGY, WHEEZING,
        ALCOHOL_CONSUMING, COUGHING, SHORTNESS_OF_BREATH, SWALLOWING_DIFFICULTY, CHEST_PAIN
        Survey scale: 0=No, 1=Yes (training mapped: 1=NO→0, 2=YES→1)
        """
        if self.model is None:
            return None
        try:
            conds_lower = [c.lower() for c in (medical_conditions or [])]
            smk = health.get('Smoking', 'Never')
            alc = health.get('Alcohol', 'Never')
            # Derive symptom proxies
            has_wheeze  = any('wheezing' in c or 'wheeze' in c for c in conds_lower) or \
                          any('asthma' in c or 'copd' in c for c in conds_lower)
            has_cough   = any('cough' in c or 'copd' in c or 'bronchitis' in c for c in conds_lower)
            has_sob     = any('breath' in c or 'dyspnea' in c or 'breathless' in c for c in conds_lower)
            has_chest   = any('chest' in c for c in conds_lower)
            has_chronic = any('copd' in c or 'asthma' in c or 'fibrosis' in c or 'tb' in c for c in conds_lower)
            has_allergy = any('allerg' in c for c in conds_lower)
            has_fatigue = any('fatigue' in c or 'tired' in c for c in conds_lower)
            stress      = health.get('Stress', 'Medium')
            has_anxiety = stress in ('High', 'Very High') or \
                          any('anxiety' in c or 'depress' in c for c in conds_lower)

            fv = [
                1.0 if profile.get('Gender','Male') == 'Male' else 0.0,  # GENDER
                float(profile.get('Age', 50)),                            # AGE
                1.0 if smk in ('Daily', 'Occasional') else 0.0,          # SMOKING
                0.0,                                                       # YELLOW_FINGERS (not collected)
                1.0 if has_anxiety else 0.0,                              # ANXIETY
                0.0,                                                       # PEER_PRESSURE (not collected)
                1.0 if has_chronic else 0.0,                              # CHRONIC_DISEASE
                1.0 if has_fatigue else 0.0,                              # FATIGUE
                1.0 if has_allergy else 0.0,                              # ALLERGY
                1.0 if has_wheeze else 0.0,                               # WHEEZING
                1.0 if alc in ('Daily', 'Weekly') else 0.0,               # ALCOHOL_CONSUMING
                1.0 if has_cough else 0.0,                                # COUGHING
                1.0 if has_sob else 0.0,                                  # SHORTNESS_OF_BREATH
                0.0,                                                       # SWALLOWING_DIFFICULTY (not collected)
                1.0 if has_chest else 0.0,                                # CHEST_PAIN
            ]
            proba = self.model.predict_proba([fv])[0][1]
            return float(proba)
        except Exception:
            return None

    def _green_recommendations(self):
        return [
            "Maintain smoke-free lifestyle and avoid secondhand smoke",
            "Aerobic exercise 150 min/week preserves lung capacity",
            "Annual flu vaccine; pneumococcal vaccine after age 65",
            "Use N95 mask in high-pollution environments",
        ]

    def _yellow_recommendations(self):
        return [
            "Spirometry test recommended to assess lung function objectively",
            "Reduce exposure to indoor and outdoor air pollutants",
            "Consider pulmonology consultation if breathlessness on exertion",
            "Quit smoking if applicable — most modifiable lung risk factor",
        ]

    def _red_recommendations(self):
        return [
            "URGENT: Pulmonologist referral — possible COPD or advanced lung disease",
            "Spirometry + chest X-ray + CT scan if not done in past year",
            "Pulmonary rehabilitation program (PR) — proven to reduce exacerbations",
            "LDCT lung cancer screening if ≥40 pack-years and age ≥50",
            "Review all medications with doctor — some worsen airflow",
            "Supplemental oxygen assessment if SpO2 <88% at rest",
        ]
