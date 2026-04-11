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
# ── Indoor radon exposure by Indian state (µBq/m³ → lung cancer risk) ─────────
# Source: Atomic Minerals Directorate & BARC India radiation surveys
#         WHO Indoor Radon Handbook 2009 (WHO/HTM/TDR/2009.6)
#         National average indoor radon: ~42 Bq/m³ (AMD/BARC 2011)
#         Elevated states: Kerala ~91, Rajasthan ~79, Jharkhand ~68, HP ~58
#         Each 100 Bq/m³ increase → +16% lung cancer risk (WHO/IARC)
INDIA_STATE_RADON_BQ = {
    "kerala":           91.0,
    "rajasthan":        79.0,
    "jharkhand":        68.0,
    "himachal pradesh": 58.0,
    "hp":               58.0,
    "uttarakhand":      52.0,
    "jammu and kashmir":48.0,
    "j&k":              48.0,
    "meghalaya":        47.0,
    "assam":            45.0,
    "karnataka":        44.0,
    "national_average": 42.0,   # default
    "maharashtra":      38.0,
    "gujarat":          36.0,
    "delhi":            34.0,
    "uttar pradesh":    32.0,
    "west bengal":      30.0,
    "tamil nadu":       29.0,
}
_RADON_NATIONAL_AVG = 42.0   # Bq/m³

def get_radon_risk(state: str) -> tuple:
    """
    Returns (radon_bq, risk_increment) for the given Indian state.
    Risk formula: WHO 2009 — 16% lung cancer risk increase per 100 Bq/m³.
    Above national average only (42 Bq/m³ = 0 extra risk).
    Source: WHO Indoor Radon Handbook 2009; AMD/BARC India 2011.
    """
    if not state:
        return _RADON_NATIONAL_AVG, 0.0
    key = state.strip().lower()
    bq = INDIA_STATE_RADON_BQ.get(key, _RADON_NATIONAL_AVG)
    excess_bq = max(0.0, bq - _RADON_NATIONAL_AVG)
    # +16% per 100 Bq/m³ above baseline, capped at +0.12
    risk_inc = round(min(0.12, (excess_bq / 100.0) * 0.16), 4)
    return bq, risk_inc


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


def jindal_fev1_predicted(age: int, height_cm: float, gender: str) -> float:
    """
    ── G5: Jindal 2012 Indian Spirometry Norms (DORMANT PATHWAY) ────────────
    Calculates predicted FEV1 (litres) for Indian adults using Indian-specific
    regression equations. Activates ONLY when height_cm and age are provided.

    Source: Jindal SK et al., Indian J Chest Dis Allied Sci 2012;54(2):93-98
            Validated on 6,994 healthy Indian adults (north + south India)
            These equations replace NHANES/GLI-2012 norms for Indian users.

    Why this matters: Indian lung volumes are 15–20% smaller than Western
    reference values at the same height/age (Glindmeyer 1999, Cotes 1993).
    Using Western norms falsely labels many healthy Indians as "mildly restricted".
    Jindal 2012 provides India-specific predicted normals.

    Equations (Jindal 2012, Table 2):
      Men:   FEV1 = 0.0348 × Height(cm) - 0.0204 × Age - 1.570
      Women: FEV1 = 0.0298 × Height(cm) - 0.0180 × Age - 1.145

    Returns predicted FEV1 in litres (lower limit of normal = predicted × 0.80).
    Returns None if height or age not available (field is optional/dormant).

    Usage in calculate_risk: if user provides Height_cm and FEV1_measured,
    compute fev1_pct_predicted = (FEV1_measured / jindal_fev1_predicted(...)) × 100
    and pass to fev1_copd_stage(). If Height_cm not provided, this function
    returns None and the Jindal pathway is silently skipped.
    """
    if not height_cm or not age or height_cm <= 0:
        return None
    try:
        h = float(height_cm)
        a = float(age)
        if gender.lower() in ('male', 'm', 'man'):
            predicted = 0.0348 * h - 0.0204 * a - 1.570
        else:
            predicted = 0.0298 * h - 0.0180 * a - 1.145
        return round(max(0.5, predicted), 3)   # floor at 0.5L (physiological minimum)
    except Exception:
        return None


class LungsModel(BaseOrganModel):
    def __init__(self):
        super().__init__('lungs')
        # Secondary ML signal comes from lung_cancer_ml.pkl (GradientBoosting, N=309)
        # trained_models/lungs_model.pkl is the same survey dataset — avoid double-counting.
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

        # ── G5: Jindal 2012 Indian spirometry norms (DORMANT pathway) ────────
        # Activates only when Height_cm + FEV1_measured_litres are provided.
        # Computes India-specific % predicted using Jindal equations instead of
        # NHANES/GLI-2012 Western norms (which over-diagnose restriction in Indians).
        # Source: Jindal SK et al., Indian J Chest Dis Allied Sci 2012;54(2):93-98
        height_cm    = health.get('Height_cm') or health.get('HeightCm') or profile.get('Height_cm')
        fev1_measured = health.get('FEV1_litres') or health.get('FEV1Litres')  # raw measured litres
        if height_cm and fev1_measured:
            jindal_pred = jindal_fev1_predicted(age, float(height_cm), gender)
            if jindal_pred and jindal_pred > 0:
                # Override FEV1% using India-specific norms instead of whatever % was provided
                health['FEV1Percent'] = round((float(fev1_measured) / jindal_pred) * 100, 1)
                health['_jindal_predicted_litres'] = jindal_pred
                health['_jindal_method'] = f"Jindal 2012 — predicted {jindal_pred:.2f}L for {gender} age {age} height {height_cm}cm"

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
            # Fallback: smoking-category estimate with age scaling.
            # A 60-year-old daily smoker likely has 20+ pack-years — use realistic baseline.
            age_smoke_scale = min(2.2, max(1.0, age / 30.0))  # age 30→1.0, age 45→1.5, age 60→2.0
            smoking_map = {
                'Never':      0.0,
                'Occasional': 0.12,
                'Daily':      0.38,   # realistic baseline for a current daily smoker
            }
            base_py = smoking_map.get(smoking, 0.0)
            py_risk = round(min(0.72, base_py * (age_smoke_scale if smoking == 'Daily' else 1.0)), 3)
            risk_components['smoking_category'] = py_risk
            method_used.append("Smoking-Category Heuristic")
            pack_years_val = None

        # 3. AQI exposure (CPCB city data) — NON-SMOKER CAP APPLIED
        # CRITICAL FIX: AQI is a population-level environmental risk, not individual disease.
        # Raw aqi_lung_risk() for Delhi (PM2.5=98.6) returns ~0.28 — this is the population
        # ATTRIBUTABLE RISK for COPD from outdoor air in the entire population of Delhi.
        # For a NON-SMOKER living in Delhi, the individual risk is much lower:
        #   - Non-smoker Delhi resident: HR ~1.3 for COPD vs clean-air area (Salvi 2009)
        #   - This represents ~0.08-0.12 individual risk contribution, NOT 0.28
        # For a SMOKER, the full AQI risk applies (smoking × air pollution synergistic)
        #
        # Source: Salvi SS & Barnes PJ, Lancet 2009;374:733-743
        #   "COPD in non-smokers — 25-45% of COPD in India occurs in non-smokers,
        #    primarily from biomass fuel + outdoor air pollution."
        #   "However, the individual risk for a non-smoker in polluted city is ~1.3×
        #    baseline, not 3-4× which is the smoker+pollution interaction."
        # Source: GBD 2019 — population attributable fraction for outdoor air:
        #   ~8% of COPD PAF from outdoor air alone (vs 70%+ from tobacco)
        pm25 = get_city_pm25(city)
        aqi_risk_raw = aqi_lung_risk(pm25)

        if current_smoker:
            # Smokers: full AQI risk (synergistic effect with tobacco smoke)
            aqi_risk = aqi_risk_raw
        else:
            # Non-smokers: cap AQI contribution at 0.12 (max individual risk from outdoor air alone)
            # This maps Delhi (worst case) to health_score drop of ~8-10 points, not 20+
            # Source: Salvi 2009 HR ~1.3 for non-smokers in high-pollution areas
            aqi_risk = min(0.12, aqi_risk_raw)

        risk_components['outdoor_aqi'] = aqi_risk
        if pm25 > 60:
            if current_smoker:
                possible_issues.append(f"High outdoor PM2.5 ({pm25:.0f} µg/m³) + smoking — synergistic COPD risk")
            else:
                possible_issues.append(f"Outdoor PM2.5 exposure ({pm25:.0f} µg/m³) — chronic airway inflammation (non-smoker: moderate risk)")
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

        # 9. Occupational dust/fume exposure
        # Silicosis (mining, stone cutting, construction) — OR 2.3–4.5 for COPD (Blanc 2009)
        # Byssinosis (textile, cotton) — 30–40% FEV1 decline (WHO cotton dust standard)
        # Coal dust — OR 2.1 for CWP (NIOSH/DGMS India)
        # ~60 million Indian workers in high-dust occupations (MoLE India 2020)
        # Source: Blanc PD et al., Eur Respir J 2009;33:298-306 (occupational COPD, pop-attributable 14%)
        occupational = health.get('OccupationalExposure') or health.get('Occupation', '')
        occ_risk = 0.0
        occ_note = None
        if occupational:
            occ_lower = occupational.lower()
            if any(k in occ_lower for k in ['mining', 'mine', 'quarry', 'stone cutting', 'stone cut',
                                             'silica', 'sandblasting', 'ceramics']):
                occ_risk = 0.25
                occ_note = f"Silica dust exposure ({occupational}) — Silicosis + COPD risk: OR 2.3–4.5 (Blanc 2009, DGMS India)"
            elif any(k in occ_lower for k in ['coal', 'colliery', 'coking']):
                occ_risk = 0.20
                occ_note = f"Coal dust exposure ({occupational}) — CWP risk: OR 2.1 (NIOSH)"
            elif any(k in occ_lower for k in ['textile', 'cotton', 'jute', 'weaving', 'spinning', 'byssin']):
                occ_risk = 0.18
                occ_note = f"Textile/cotton dust ({occupational}) — Byssinosis risk; FEV1 decline ~30–40% (WHO)"
            elif any(k in occ_lower for k in ['construction', 'cement', 'asbestos', 'demolition']):
                occ_risk = 0.16
                occ_note = f"Construction/cement dust ({occupational}) — Pneumoconiosis risk (DGMS India)"
            elif any(k in occ_lower for k in ['farming', 'agricultural', 'pesticide', 'crop dust']):
                occ_risk = 0.10
                occ_note = f"Agricultural dust ({occupational}) — Organic dust COPD risk (SWORD/SENSOR)"
            elif any(k in occ_lower for k in ['chemical', 'fume', 'welding', 'foundry', 'smelting', 'paint']):
                occ_risk = 0.12
                occ_note = f"Chemical fume exposure ({occupational}) — Occupational asthma + COPD risk"
        if occ_risk > 0:
            risk_components['occupational'] = occ_risk
            possible_issues.append(occ_note)
            method_used.append("Occupational Exposure (Blanc 2009 / DGMS India)")

        # 10. Indoor radon exposure by state (WHO Radon Handbook 2009 / BARC India)
        # Kerala 91 Bq/m³, Rajasthan 79, Jharkhand 68, Himachal Pradesh 58
        # +16% lung cancer risk per 100 Bq/m³ above national average (42 Bq/m³)
        radon_bq, radon_risk = get_radon_risk(state)
        if radon_risk > 0:
            risk_components['radon'] = radon_risk
            possible_issues.append(
                f"Elevated indoor radon — {state.title()} avg {radon_bq:.0f} Bq/m³ "
                f"(national avg 42 Bq/m³). Risk: +{radon_risk*100:.0f}% lung cancer "
                f"(WHO Radon Handbook 2009; BARC India 2011)"
            )
            method_used.append(f"Indoor Radon (BARC India / WHO 2009, {radon_bq:.0f} Bq/m³)")

        # ── Combine ───────────────────────────────────────────────────────────
        # Occupational + radon are additive to base risk (independent pathways)
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

        # Occupational dust/fume and radon are independent additive risks
        # (act via different biological pathways than smoking/AQI)
        base_risk = min(1.0, base_risk + occ_risk + radon_risk)

        # Inhaler/corticosteroid medications reduce effective risk
        meds_lower = [m.lower() for m in medications]
        if any('salbutamol' in m or 'albuterol' in m or 'bronchodilator' in m
               or 'tiotropium' in m or 'ipratropium' in m for m in meds_lower):
            base_risk *= 0.88
        if any('fluticasone' in m or 'budesonide' in m or 'beclomethasone' in m
               or 'inhaled corticosteroid' in m or 'ics' in m for m in meds_lower):
            base_risk *= 0.90

        # Hard floor: active smokers — floor scales with age, pack-years AND city AQI
        # Clinical rationale: A daily smoker in a high-pollution city has synergistic
        # lung damage regardless of age. GOLD 2023 + Salvi 2009: smoking × high PM2.5
        # gives multiplicative COPD risk (OR 3.2 vs either alone).
        # Source: Mannino DM et al., Lancet Respir Med 2022 — pack-years ≥20 at age ≥50:
        #   COPD prevalence 40%, lung cancer risk 10x baseline.
        # Fix: minimum floor for daily smoker in Delhi/NCR-level pollution is 0.35
        # (health_score ~65 = YELLOW) regardless of age — synergistic damage is real.
        if smoking == 'Daily':
            # Base floor by age, boosted by pack-years
            py_boost = min(0.15, (pack_years_val or 0) * 0.004) if pack_years_val else 0.0
            age_floor = min(0.65, 0.22 + max(0, (age - 35)) * 0.010 + py_boost)
            # City pollution boost: daily smoker in high-PM2.5 city gets higher floor
            # Delhi PM2.5=98.6 → aqi_risk_raw=0.44 → pollution_floor_boost=0.15 (cap)
            # Mumbai PM2.5=46  → aqi_risk_raw=0.18 → pollution_floor_boost=0.06
            pollution_floor_boost = min(0.15, aqi_risk_raw * 0.35)
            age_floor = min(0.68, age_floor + pollution_floor_boost)
            base_risk = max(base_risk, age_floor)
        elif smoking == 'Occasional':
            # Occasional smoker in high-pollution city: modest floor
            occ_floor = 0.15 + min(0.08, aqi_risk_raw * 0.20)
            base_risk = max(base_risk, occ_floor)

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

        # ── Recommendations — fully personalised with actual user values ──────
        recommendations = []
        tobacco_type = health.get('TobaccoType', 'cigarette')
        bidi = tobacco_type and 'bidi' in tobacco_type.lower()

        # 1. Smoking — most impactful, reference actual pack-years / duration
        if smoking == 'Daily':
            if pack_years_val and pack_years_val > 0:
                py_rounded = round(pack_years_val, 1)
                if py_rounded >= 40:
                    screen_msg = (
                        f" At {py_rounded} pack-years + age {age}, LDCT low-dose CT lung cancer "
                        f"screening is recommended (USPSTF 2021 Grade B — reduces lung cancer mortality by 20%)."
                    )
                elif py_rounded >= 20:
                    screen_msg = f" At {py_rounded} pack-years, COPD is likely — spirometry will confirm."
                else:
                    screen_msg = f" At {py_rounded} pack-years, early COPD risk is significant."
                bidi_note = " Bidi has 3× more tar than cigarettes — your actual lung damage risk is higher than pack-years alone suggest." if bidi else ""
                recommendations.append(
                    f"Quit smoking — you have {py_rounded} pack-years of exposure.{bidi_note}{screen_msg} "
                    f"Quitting now stops further irreversible FEV1 decline; NRT + varenicline doubles quit rates (Cochrane 2022)."
                )
            else:
                years_s = health.get('YearsSmoking', health.get('YearsSmoked', 0)) or 0
                duration = f"~{years_s} years" if years_s else "an unknown duration"
                bidi_note = " You smoke bidi — 3× the tar exposure of cigarettes." if bidi else ""
                recommendations.append(
                    f"Quit smoking — you have been smoking daily for {duration}.{bidi_note} "
                    f"Each year of continued smoking adds permanent lung capacity loss (~30 mL FEV1/year). "
                    f"NRT + varenicline doubles quit rates (Cochrane 2022)."
                )
        elif smoking == 'Occasional':
            recommendations.append(
                "Occasional smoking still accelerates FEV1 decline — there is no safe level. "
                "Even social smoking raises COPD risk by 30% over lifetime. "
                "NRT patches can help reduce frequency before quitting completely."
            )

        # 2. GOLD spirometry result — most actionable if available
        if gold_stage and fev1_pct:
            fev1_note = {
                "GOLD 1 (Mild)":      f"FEV1 {fev1_pct}% — mild obstruction. Bronchodilator inhaler and smoking cessation are first-line.",
                "GOLD 2 (Moderate)":  f"FEV1 {fev1_pct}% — moderate COPD. Long-acting bronchodilator (LABA/LAMA) therapy; pulmonary rehab.",
                "GOLD 3 (Severe)":    f"FEV1 {fev1_pct}% — severe COPD. Urgent pulmonologist referral; combination inhaler therapy; avoid exacerbation triggers.",
                "GOLD 4 (Very Severe)": f"FEV1 {fev1_pct}% — very severe COPD. Supplemental O₂ assessment; consider lung transplant evaluation.",
            }.get(gold_stage, f"FEV1 {fev1_pct}% — spirometry result: {gold_stage}.")
            recommendations.append(fev1_note)

        # 3. Cooking fuel — personalised to their actual fuel
        if fuel_risk >= 0.22:
            fuel_name = (cooking_fuel or 'biomass').title()
            recommendations.append(
                f"You use {fuel_name} for cooking — indoor PM2.5 is ~2.3× higher than LPG households "
                f"(Balakrishnan Lancet 2019). This is a leading cause of COPD in non-smokers in India. "
                f"Switching to LPG/PNG can reduce your lung risk score by ~8–12 points over 2 years. "
                f"Pradhan Mantri Ujjwala Yojana provides subsidised LPG connections — check eligibility."
            )

        # 4. AQI — personalised to their city with actual PM2.5 value
        if pm25 > 60:
            severity = "very high" if pm25 > 90 else "high"
            recommendations.append(
                f"You live in {city or 'a city'} with {severity} outdoor PM2.5 ({pm25:.0f} µg/m³ — "
                f"WHO safe limit is 5 µg/m³, India average is 45 µg/m³). "
                f"Wear an N95 mask during outdoor activities and peak traffic hours (7–9am, 5–8pm). "
                f"An indoor air purifier (HEPA filter) reduces indoor particulates by 80%."
            )
        elif pm25 > 40:
            recommendations.append(
                f"PM2.5 in {city or 'your city'} is {pm25:.0f} µg/m³ — above India's safe limit (40 µg/m³). "
                f"N95 mask during high-traffic outdoor exposure is advisable."
            )

        # 5. TB history — personalised by severity
        if tb_risk > 0:
            tb_note = "active TB" if tb_risk >= 0.35 else "past TB history"
            state_note = f" ({state} has elevated TB burden — state multiplier: {tb_state_mult:.2f}×)" if tb_state_mult > 1.05 else ""
            recommendations.append(
                f"Post-TB lung damage risk detected ({tb_note}{state_note}). "
                f"Up to 40% of TB survivors develop obstructive/restrictive lung patterns (Allwood IJTLD 2013). "
                f"Spirometry is strongly recommended to quantify any residual airflow obstruction. "
                f"Available at government chest hospitals."
            )

        # 6. LDCT screening — personalised by actual pack-years + age
        if screen_rec and pack_years_val:
            recommendations.append(
                f"LDCT lung cancer screening is indicated: you have {pack_years_val:.0f} pack-years and are age {age}. "
                f"This reduces lung cancer mortality by 20% (USPSTF 2021 Grade B recommendation). "
                f"Available at major government cancer hospitals (Tata Memorial, AIIMS)."
            )

        # 7. Asthma personalised
        if asthma:
            recommendations.append(
                "Asthma detected — ensure your rescue inhaler (salbutamol) is always accessible. "
                "Identify your personal triggers (dust, cold air, exercise, smoke). "
                "Annual spirometry tracks airway changes over time."
            )

        # 8. Activity for lung health
        if activity in ('Sedentary', 'Light'):
            recommendations.append(
                "Physical inactivity weakens respiratory muscles. "
                "Even 20-min daily walking improves FEV1 by 5–8% in COPD patients (GOLD 2023). "
                "Yoga pranayama (breathing exercises) is particularly effective for Indian patients."
            )

        # 9. Occupational risk personalised
        if occ_risk > 0 and occ_note:
            recommendations.append(
                f"Occupational lung risk: {occ_note}. "
                f"Use appropriate respirator (P100 filter) at work. "
                f"Annual spirometry for occupational lung disease monitoring (DGMS India mandate)."
            )

        # Fallback for perfectly healthy lungs
        if not recommendations:
            recommendations.append(
                "Lungs are healthy. Protect them: stay smoke-free, exercise regularly, "
                "use N95 in polluted environments, and get annual flu vaccine. "
                "Spirometry baseline at age 40 is recommended."
            )

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
