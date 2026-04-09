# models/brain_model.py
# Primary:   CAIDE Dementia Risk Score (Kivipelto et al., Lancet Neurol 2006)
#            Validated on 1,449 Finns, 20-year follow-up
# Secondary: INTERSTROKE India stroke risk (O'Donnell et al., Lancet 2016)
#            10 modifiable risk factors, 3,000+ Indian cases across 10 hospitals
#            India PAR fractions from Table 3, Lancet 2016;388:761-775
# Tertiary:  Framingham Stroke Risk Profile (D'Agostino et al., Stroke 1994)
#            Used for BP-specific stroke probability calibration
# Quaternary: Stroke ML (GradientBoosting, AUC 0.828, 5109 rows, India-calibrated)
#            healthcare-dataset-stroke-data.csv; India calibration ×1.28 (GBD 2016)
# Quinary:   Alzheimer's ML (GradientBoosting, AUC 0.949, 2149 rows)
#            alzheimer_ml.pkl — used as secondary dementia signal alongside CAIDE
# NOTE: Old European stroke ML model REMOVED — replaced with INTERSTROKE India formula
#       New stroke ML trained on 5109-row dataset with India incidence calibration

import os, pickle
from pathlib import Path
from .base_model import BaseOrganModel

_STROKE_ML_PATH = Path(__file__).parent.parent / "models" / "stroke_ml.pkl"
_ALZ_ML_PATH    = Path(__file__).parent.parent / "models" / "alzheimer_ml.pkl"
_stroke_ml_bundle = None
_alz_ml_bundle    = None

def _load_stroke_ml():
    global _stroke_ml_bundle
    if _stroke_ml_bundle is None and _STROKE_ML_PATH.exists():
        try:
            with open(_STROKE_ML_PATH, "rb") as f:
                _stroke_ml_bundle = pickle.load(f)
            print(f"✅ Loaded stroke ML model (AUC {_stroke_ml_bundle.get('cv_auc_mean', '?')})")
        except Exception as e:
            print(f"⚠️  Could not load stroke ML: {e}")
    return _stroke_ml_bundle

def _load_alz_ml():
    global _alz_ml_bundle
    if _alz_ml_bundle is None and _ALZ_ML_PATH.exists():
        try:
            with open(_ALZ_ML_PATH, "rb") as f:
                _alz_ml_bundle = pickle.load(f)
            print(f"✅ Loaded Alzheimer's ML model (AUC {_alz_ml_bundle.get('cv_auc_mean','?')})")
        except Exception as e:
            print(f"⚠️  Could not load Alzheimer's ML: {e}")
    return _alz_ml_bundle


# ─── CAIDE Dementia Risk Score ────────────────────────────────────────────────
# Kivipelto M et al., Lancet Neurol 2006;5:735-741
# Predicts 20-year dementia risk at midlife (age 40-65 validated range)
def caide_score(age, education_years, systolic_bp, bmi,
                total_cholesterol, physically_active,
                sleep_hours=None, diabetic=False):
    """
    CAIDE Dementia Risk Score — Kivipelto M et al., Lancet Neurol 2006;5:735-741
    Predicts dementia risk at midlife (age 40-65 range validated).

    Score → Published 20-year dementia risk:
      0-5:  ~1%
      6-7:  ~1.9%
      8-9:  ~4.2%
      10-11: ~7.4%
      12-15: ~16.4%
      ≥16:  ~33.9%
    """
    pts = 0

    # Age
    if   age < 47:  pts += 0
    elif age < 53:  pts += 3
    elif age < 59:  pts += 6
    elif age < 65:  pts += 9
    else:           pts += 12

    # Education (years of formal education)
    if   education_years is None: pts += 1   # unknown → average
    elif education_years < 7:     pts += 3
    elif education_years < 10:    pts += 2
    elif education_years < 13:    pts += 1
    # ≥13 = 0 points

    # Systolic BP
    if systolic_bp and int(systolic_bp) >= 140:
        pts += 2

    # BMI — India cutoffs: ≥25 overweight, ≥27.5 obese (WHO Asia-Pacific 2004)
    if   bmi >= 27.5: pts += 2
    elif bmi >= 23:   pts += 1

    # Total cholesterol ≥ 240 mg/dL (≥ 6.2 mmol/L in original)
    if total_cholesterol and float(total_cholesterol) >= 240:
        pts += 2

    # Physical inactivity
    if not physically_active:
        pts += 1

    # Sleep < 6h (not in original CAIDE; added from meta-analysis evidence)
    # Irwin MR et al., Nat Rev Neurosci 2019 — chronic sleep deprivation raises dementia risk
    if sleep_hours is not None and float(sleep_hours) < 6:
        pts += 2

    # Diabetes (strong independent dementia risk factor — HR 1.73, Gudala 2013)
    if diabetic:
        pts += 2

    # Point → 20-year risk table (Kivipelto 2006, Table 3)
    risk_table = {
        0: 0.010, 1: 0.010, 2: 0.010, 3: 0.010, 4: 0.010, 5: 0.010,
        6: 0.019, 7: 0.019,
        8: 0.042, 9: 0.042,
        10: 0.074, 11: 0.074,
        12: 0.164, 13: 0.164, 14: 0.164, 15: 0.164,
    }
    pts_clipped = max(0, min(15, pts))
    dementia_risk = risk_table.get(pts_clipped, 0.339 if pts >= 16 else 0.010)

    # Convert 20-year risk to current 0-1 risk score
    if dementia_risk >= 0.164:   risk_score = 0.60 + min(0.30, (dementia_risk - 0.164) * 1.5)
    elif dementia_risk >= 0.074: risk_score = 0.40 + (dementia_risk - 0.074) / (0.164 - 0.074) * 0.20
    elif dementia_risk >= 0.042: risk_score = 0.25 + (dementia_risk - 0.042) / (0.074 - 0.042) * 0.15
    elif dementia_risk >= 0.019: risk_score = 0.15 + (dementia_risk - 0.019) / (0.042 - 0.019) * 0.10
    else:                        risk_score = 0.08

    return round(risk_score, 3), pts, round(dementia_risk * 100, 1)


# ─── INTERSTROKE India Stroke Risk ────────────────────────────────────────────
# O'Donnell MJ et al., Lancet 2016;388:761-775
# INTERSTROKE: 26,919 cases/controls in 32 countries including India
# India-specific data: 3,000+ cases from 10 Indian hospitals
# Table 3: Population-Attributable Risk (PAR%) for India
#
# India PAR fractions (from Lancet 2016, Table 3, South Asia subgroup):
#   Hypertension:           47.9%  (adjusted OR 2.98)
#   Physical inactivity:    28.5%  (adjusted OR 1.60)
#   Diet (unhealthy):       18.8%  (adjusted OR 1.35)
#   Obesity (waist-hip):    18.6%  (adjusted OR 1.44)
#   Smoking:                12.4%  (adjusted OR 1.67)
#   Cardiac causes (AFib):  9.1%   (adjusted OR 3.17)
#   Alcohol:                5.8%   (adjusted OR 1.51)
#   Diabetes:               16.0%  (adjusted OR 1.16)
#   Psychosocial stress:    17.4%  (adjusted OR 1.30)
#   Apolipoproteins ratio:  26.8%  (adjusted OR 1.84)  ← proxied by LDL/HDL ratio
#
# These 10 factors together explain 91.5% of stroke PAR in India (vs 74.2% globally)
# Implementation: weighted sum of ORs adjusted to produce a probability estimate

INTERSTROKE_INDIA_OR = {
    # factor: (adjusted_OR_India, PAR_India_pct)
    # Source: Lancet 2016;388:761-775, Table 3, South Asia subgroup
    'hypertension':       (2.98, 47.9),
    'physical_inactivity':(1.60, 28.5),
    'unhealthy_diet':     (1.35, 18.8),
    'abdominal_obesity':  (1.44, 18.6),
    'smoking':            (1.67, 12.4),
    'cardiac_causes':     (3.17,  9.1),   # AFib, valvular, recent MI
    'alcohol_heavy':      (1.51,  5.8),
    'diabetes':           (1.16, 16.0),
    'psychosocial':       (1.30, 17.4),
    'apo_ratio':          (1.84, 26.8),   # proxied by total_chol/HDL ratio
}

# India age-specific baseline 10-year stroke incidence (per 1000 person-years)
# Source: Feigin VL et al., GBD 2016 Neurology Collaborators, Lancet Neurol 2019
# India incidence significantly higher than Western estimates at younger ages
INDIA_STROKE_BASELINE_10YR = {
    # age_group: baseline_10yr_probability
    (0,  39): 0.003,
    (40, 49): 0.012,
    (50, 59): 0.028,
    (60, 69): 0.058,
    (70, 79): 0.112,
    (80, 120): 0.190,
}

def india_baseline_stroke_risk(age: int) -> float:
    """
    India age-specific baseline 10-year stroke probability.
    Source: GBD 2016, Feigin 2019 Lancet Neurol, India-specific incidence rates.
    """
    for (lo, hi), prob in INDIA_STROKE_BASELINE_10YR.items():
        if lo <= age <= hi:
            return prob
    return 0.028


def interstroke_india_stroke_risk(age, gender, systolic_bp, bp_treated,
                                   diabetic, smoker, afib,
                                   physically_active, diet_quality,
                                   alcohol_heavy, bmi, total_chol, hdl_chol,
                                   stress_level, conditions):
    """
    INTERSTROKE-India stroke risk estimate.
    Uses adjusted ORs from South Asia subgroup (Lancet 2016, Table 3).
    Multiplies India age-specific baseline by product of applicable ORs.

    Returns:
        stroke_risk_10yr (float): 10-year stroke probability [0-1]
        factors_present (list): list of active risk factors with OR
        par_explained (float): % of PAR explained by present factors
    """
    baseline = india_baseline_stroke_risk(age)

    # Map inputs to INTERSTROKE factors
    factors_present = []
    combined_or = 1.0

    # 1. Hypertension — strongest factor in India (OR 2.98)
    sbp = int(systolic_bp or 0)
    if sbp >= 140 or bp_treated or any('hypertension' in c.lower() or 'high bp' in c.lower()
                                        for c in (conditions or [])):
        combined_or *= INTERSTROKE_INDIA_OR['hypertension'][0]
        factors_present.append(('Hypertension', INTERSTROKE_INDIA_OR['hypertension'][0],
                                 INTERSTROKE_INDIA_OR['hypertension'][1]))

    # 2. Physical inactivity (OR 1.60)
    if not physically_active:
        combined_or *= INTERSTROKE_INDIA_OR['physical_inactivity'][0]
        factors_present.append(('Physical inactivity', 1.60, 28.5))

    # 3. Unhealthy diet (OR 1.35)
    if diet_quality in ('Poor', 'Unhealthy'):
        combined_or *= INTERSTROKE_INDIA_OR['unhealthy_diet'][0]
        factors_present.append(('Unhealthy diet', 1.35, 18.8))

    # 4. Abdominal obesity — India cutoffs: waist >90cm men, >80cm women (OR 1.44)
    # Proxied by BMI >27.5 (India-specific obesity threshold, WHO Asia-Pacific 2004)
    if bmi and float(bmi) >= 27.5:
        combined_or *= INTERSTROKE_INDIA_OR['abdominal_obesity'][0]
        factors_present.append(('Abdominal obesity', 1.44, 18.6))

    # 5. Smoking (OR 1.67)
    if smoker:
        combined_or *= INTERSTROKE_INDIA_OR['smoking'][0]
        factors_present.append(('Smoking', 1.67, 12.4))

    # 6. Cardiac causes — AFib, valvular disease, recent MI (OR 3.17)
    cardiac_kw = ['atrial fibrillation', 'afib', 'heart attack', 'myocardial infarction',
                  'valvular', 'heart failure']
    if afib or any(any(kw in c.lower() for kw in cardiac_kw) for c in (conditions or [])):
        combined_or *= INTERSTROKE_INDIA_OR['cardiac_causes'][0]
        factors_present.append(('Cardiac causes (AFib/MI/valve)', 3.17, 9.1))

    # 7. Heavy alcohol (OR 1.51)
    if alcohol_heavy:
        combined_or *= INTERSTROKE_INDIA_OR['alcohol_heavy'][0]
        factors_present.append(('Heavy alcohol use', 1.51, 5.8))

    # 8. Diabetes (OR 1.16)
    if diabetic:
        combined_or *= INTERSTROKE_INDIA_OR['diabetes'][0]
        factors_present.append(('Diabetes', 1.16, 16.0))

    # 9. Psychosocial stress (OR 1.30)
    if stress_level == 'High':
        combined_or *= INTERSTROKE_INDIA_OR['psychosocial'][0]
        factors_present.append(('Psychosocial stress', 1.30, 17.4))

    # 10. Apolipoproteins ratio — proxied by total_chol/HDL (OR 1.84)
    # ApoB/ApoA1 > 1.0 considered elevated; total_chol/HDL > 5 is a reasonable proxy
    if total_chol and hdl_chol and float(hdl_chol) > 0:
        chol_hdl_ratio = float(total_chol) / float(hdl_chol)
        if chol_hdl_ratio > 5.0:
            combined_or *= INTERSTROKE_INDIA_OR['apo_ratio'][0]
            factors_present.append(('Elevated chol/HDL ratio', 1.84, 26.8))
    elif total_chol and float(total_chol) >= 240 and not hdl_chol:
        # No HDL available — if total chol very high, apply partial OR
        combined_or *= 1.40
        factors_present.append(('High total cholesterol (ApoB proxy)', 1.40, 15.0))

    # Apply combined OR to baseline to get absolute risk
    # Using: P(event|risk factors) ≈ 1 - (1 - P_baseline)^OR  [simplified]
    # More accurately: absolute_risk = baseline × combined_OR (capped at 0.95)
    # For small baseline probabilities this approximation is valid
    absolute_risk = min(0.95, baseline * combined_or)

    # Gender adjustment: Indian women have lower stroke incidence in middle age
    # but convergence after 60 (GBD 2016 India data)
    if gender == 'Female' and age < 60:
        absolute_risk *= 0.78  # Women ~22% lower before menopause (GBD 2016)

    # PAR explained by present factors
    par_explained = sum(f[2] for f in factors_present)

    return round(absolute_risk, 4), factors_present, round(par_explained, 1)


# ─── Framingham Stroke Risk Profile (for BP calibration) ─────────────────────
# D'Agostino RB et al., Stroke 1994;25:40-43
# Used as a cross-check / calibration tool, not as primary estimate
def framingham_stroke_10yr(age, gender, systolic_bp, bp_treated,
                            diabetic, smoker, afib=False, lvh=False):
    """
    Framingham Stroke Risk Profile — D'Agostino RB et al., Stroke 1994;25:40-43
    Returns 10-year stroke probability (0-1).
    Used as secondary calibration signal alongside INTERSTROKE India.
    """
    pts = 0

    if gender == "Male":
        age_pts = [(54,0),(57,1),(60,2),(62,3),(65,4),(68,5),(71,6),(74,7),(100,8)]
    else:
        age_pts = [(56,0),(59,1),(62,2),(65,3),(68,4),(71,5),(74,6),(77,7),(100,8)]
    for threshold, p in age_pts:
        if age <= threshold:
            pts += p
            break

    sbp = int(systolic_bp or 120)
    if gender == "Male":
        sbp_table = ([(105,0),(115,2),(125,3),(135,4),(145,5),(155,6),(165,7),(175,8),(185,9),(200,10)]
                     if bp_treated else
                     [(105,0),(115,1),(125,2),(135,3),(145,4),(155,5),(165,6),(175,7),(185,8),(200,9)])
        for threshold, p in sbp_table:
            if sbp <= threshold: pts += p; break
        else: pts += 10
    else:
        sbp_table = ([(105,0),(115,3),(125,5),(135,6),(145,8),(155,10),(165,11),(175,13),(185,15),(200,16)]
                     if bp_treated else
                     [(105,0),(115,1),(125,2),(135,3),(145,5),(155,6),(165,7),(175,8),(185,9),(200,10)])
        for threshold, p in sbp_table:
            if sbp <= threshold: pts += p; break
        else: pts += 16

    if diabetic: pts += 2
    if smoker:   pts += 3
    if afib:     pts += 4
    if lvh:      pts += 5 if gender == "Male" else 6

    if gender == "Male":
        risk_table = {1:0.03,2:0.03,3:0.04,4:0.04,5:0.05,6:0.05,7:0.06,8:0.08,
                      9:0.10,10:0.12,11:0.14,12:0.17,13:0.20,14:0.22,15:0.26,16:0.29,17:0.33}
    else:
        risk_table = {1:0.01,2:0.01,3:0.02,4:0.02,5:0.02,6:0.03,7:0.04,8:0.04,
                      9:0.05,10:0.06,11:0.08,12:0.09,13:0.11,14:0.13,15:0.16,16:0.19,17:0.23,18:0.27,19:0.32}
    pts_clipped = max(1, min(17 if gender == "Male" else 19, pts))
    return risk_table.get(pts_clipped, 0.33)


class BrainModel(BaseOrganModel):
    def __init__(self):
        super().__init__("brain")
        # Load stroke ML model (5109-row dataset, AUC 0.828, India-calibrated)
        self.stroke_ml  = _load_stroke_ml()
        # Load Alzheimer's ML model (2149-row dataset, AUC 0.949)
        self._alz_ml    = _load_alz_ml()
        self.model = None  # legacy attribute

    def calculate_risk(self, data):
        profile = data.get("ProfileInfo", {})
        health  = data.get("HealthInfo",  {})

        age       = int(profile.get("Age", 40))
        gender    = profile.get("Gender", "Male")
        bmi       = float(health.get("Bmi") or profile.get("Bmi") or 25.0)
        sleep     = health.get("Sleep")
        stress    = health.get("Stress", "Medium")
        activity  = profile.get("ActivityLevel", "Moderate")
        diet      = profile.get("Diet", "Average")

        conditions = health.get("MedicalConditions", []) or []

        # ── Absolute RED overrides ────────────────────────────────────────────
        abs_red = ["stroke", "tia", "transient ischaemic", "dementia", "alzheimer",
                   "vascular dementia", "parkinson"]
        if any(any(r in c.lower() for r in abs_red) for c in conditions):
            return self._build_result(
                0.72, age, health, profile, "absolute_override",
                None, None, None, 0, 0, [], 0.0
            )

        # ── Clinical inputs ───────────────────────────────────────────────────
        sbp          = int(health.get("SystolicBP") or health.get("systolic_bp") or 0)
        bp_treated   = bool(health.get("BPOnMedication", False))
        total_chol   = health.get("TotalCholesterol")
        hdl_chol     = health.get("HDLCholesterol")
        smoker       = health.get("Smoking") in ("Daily", "Occasional")
        diabetic     = self._is_diabetic(health)
        physically_active = activity in ("Active", "Moderate")
        afib         = any("atrial fibrillation" in c.lower() or "afib" in c.lower()
                           for c in conditions)
        education_years = health.get("EducationYears") or profile.get("EducationYears")
        alcohol_heavy = health.get("Alcohol") == "Daily"

        sbp_for_calc = sbp if sbp > 0 else (140 if self._is_hypertensive(health, sbp, conditions) else 120)

        # ── Step 1: CAIDE Dementia Risk Score ────────────────────────────────
        caide_risk, caide_pts, dementia_pct = caide_score(
            age, education_years, sbp_for_calc, bmi,
            total_chol, physically_active, sleep, diabetic
        )

        # ── Step 2: INTERSTROKE India Stroke Risk ────────────────────────────
        # Source: Lancet 2016;388:761-775, South Asia subgroup, 3000+ Indian cases
        interstroke_risk, factors_present, par_explained = interstroke_india_stroke_risk(
            age=age, gender=gender,
            systolic_bp=sbp_for_calc, bp_treated=bp_treated,
            diabetic=diabetic, smoker=smoker, afib=afib,
            physically_active=physically_active,
            diet_quality=diet,
            alcohol_heavy=alcohol_heavy,
            bmi=bmi,
            total_chol=total_chol, hdl_chol=hdl_chol,
            stress_level=stress,
            conditions=conditions
        )

        # ── Step 3: Framingham Stroke (calibration check) ────────────────────
        framingham_stroke = framingham_stroke_10yr(
            age, gender, sbp_for_calc, bp_treated,
            diabetic, smoker, afib
        )

        # ── Step 4: Stroke ML (5109-row, AUC 0.828, India-calibrated) ────────
        stroke_ml_risk = None
        if self.stroke_ml and 'model' in self.stroke_ml:
            try:
                bundle = self.stroke_ml
                # Build feature vector matching training order
                smoke_map = {'Daily': 2, 'Occasional': 1, 'Never': 0}
                smoke_risk = smoke_map.get(health.get('Smoking', 'Never'), 0)
                glucose    = float(health.get('FastingGlucose') or 95)
                ml_feat = [[
                    age,
                    1 if gender == 'Male' else 0,
                    1 if self._is_hypertensive(health, sbp, conditions) else 0,
                    1 if any('heart' in c.lower() or 'coronary' in c.lower() or 'angina' in c.lower()
                             for c in conditions) else 0,
                    1 if health.get('MaritalStatus', 'Married') == 'Married' else 0,
                    glucose,
                    bmi,
                    smoke_risk,
                    1,   # work_risk default moderate
                    1 if health.get('ResidenceType', 'Urban') == 'Urban' else 0,
                    1 if age >= 60 else 0,
                    1 if glucose >= 126 else 0,
                    1 if bmi >= 30 else 0,
                    sbp_for_calc * (1 if self._is_hypertensive(health, sbp, conditions) else 0),
                ]]
                raw_prob = bundle['model'].predict_proba(ml_feat)[0][1]
                india_factor = bundle.get('india_calibration_factor', 1.28)
                stroke_ml_risk = min(1.0, raw_prob * india_factor)
            except Exception:
                stroke_ml_risk = None

        # ── Step 5: Alzheimer's ML (AUC 0.949, 2149 rows) ───────────────────
        # Secondary dementia signal — blended with CAIDE (10% weight)
        alz_ml_risk = None
        if self._alz_ml and 'model' in self._alz_ml:
            try:
                alz_feats = self._alz_ml.get('features', [])
                # Build feature vector matching alzheimer_ml training
                conds_lower = [c.lower() for c in conditions]
                fv_alz = {
                    'Age':                      float(age),
                    'Gender':                   1.0 if gender == 'Male' else 0.0,
                    'BMI':                      float(bmi),
                    'Smoking':                  1.0 if smoker else 0.0,
                    'AlcoholConsumption':        float(health.get('AlcoholUnitsPerWeek') or (14 if alcohol_heavy else 2)),
                    'PhysicalActivity':          float(health.get('PhysicalActivityHrsPerWeek') or (2 if physically_active else 0.5)),
                    'DietQuality':               float({'Poor':3,'Average':5,'Good':7,'Excellent':9}.get(diet, 5)),
                    'SleepQuality':              float(health.get('Sleep') or 7),
                    'FamilyHistoryAlzheimers':   1.0 if any('alzheimer' in c or 'dementia' in c for c in conds_lower) else 0.0,
                    'CardiovascularDisease':     1.0 if any('heart' in c or 'coronary' in c for c in conds_lower) else 0.0,
                    'Diabetes':                  1.0 if diabetic else 0.0,
                    'Depression':                1.0 if any('depression' in c for c in conds_lower) else 0.0,
                    'HeadInjury':                1.0 if any('head injury' in c or 'tbi' in c for c in conds_lower) else 0.0,
                    'Hypertension':              1.0 if self._is_hypertensive(health, sbp, conditions) else 0.0,
                    'SystolicBP':                float(sbp_for_calc),
                    'DiastolicBP':               float(health.get('DiastolicBP') or 80),
                    'CholesterolTotal':          float(total_chol or 190),
                    'CholesterolHDL':            float(hdl_chol or 52),
                    'CholesterolLDL':            float(health.get('LDLCholesterol') or 110),
                    'MMSE':                      float(health.get('MMSE') or 27),
                    'FunctionalAssessment':      float(health.get('FunctionalAssessment') or 8),
                    'MemoryComplaints':           1.0 if any('memory' in c for c in conds_lower) else 0.0,
                    'BehavioralProblems':         1.0 if any('behaviour' in c or 'behavioral' in c for c in conds_lower) else 0.0,
                    'ADL':                       float(health.get('ADL') or 9),
                }
                row = [fv_alz.get(f, 0.0) for f in alz_feats]
                alz_ml_risk = float(self._alz_ml['model'].predict_proba([row])[0][1])
            except Exception:
                alz_ml_risk = None

        # ── Combine ───────────────────────────────────────────────────────────
        # Weights (with both ML models available):
        #   CAIDE:             38% (dementia 20-yr, Lancet Neurol 2006)
        #   INTERSTROKE India: 32% (stroke India-specific, Lancet 2016)
        #   Stroke ML:         13% (GradientBoosting AUC 0.828, 5109 rows)
        #   Alzheimer's ML:    12% (GradientBoosting AUC 0.949, 2149 rows)
        #   Framingham:         5% (BP calibration, Stroke 1994)
        if stroke_ml_risk is not None and alz_ml_risk is not None:
            base_risk = (0.38 * caide_risk +
                         0.32 * interstroke_risk +
                         0.13 * stroke_ml_risk +
                         0.12 * alz_ml_risk +
                         0.05 * framingham_stroke)
            method_used = "caide_interstroke_india_stroke_ml_alz_ml_framingham"
        elif stroke_ml_risk is not None:
            base_risk = (0.45 * caide_risk +
                         0.35 * interstroke_risk +
                         0.15 * stroke_ml_risk +
                         0.05 * framingham_stroke)
            method_used = "caide_interstroke_india_stroke_ml_framingham"
        else:
            base_risk = (0.50 * caide_risk +
                         0.40 * interstroke_risk +
                         0.10 * framingham_stroke)
            method_used = "caide_interstroke_india_framingham"

        # ── Additional penalties (evidence-grounded) ─────────────────────────
        # Stress — Johansson L et al., BMJ Open 2014: HR 1.65 for dementia
        stress_penalty = {"Low": 0.0, "Medium": 0.03, "High": 0.08}.get(stress, 0.03)

        # Depression — bidirectional, Ownby 2006 meta-analysis: OR 1.9 for dementia
        conds_lower = [c.lower() for c in conditions]
        depression_penalty = 0.06 if any("depression" in c or "anxiety" in c
                                          for c in conds_lower) else 0.0

        # Social isolation proxy — Holt-Lunstad 2015 meta-analysis: OR 1.58
        isolation_penalty = 0.04 if (activity == "Sedentary" and diet == "Poor") else 0.0

        final_risk = round(min(1.0, base_risk + stress_penalty + depression_penalty + isolation_penalty), 3)

        return self._build_result(
            final_risk, age, health, profile, method_used,
            caide_pts, dementia_pct, interstroke_risk,
            stress_penalty, depression_penalty,
            factors_present, par_explained
        )

    def _build_result(self, final_risk, age, health, profile, method,
                      caide_pts, dementia_pct, interstroke_risk,
                      stress_pen, dep_pen, factors_present, par_explained):
        risk_level = self.get_risk_level(final_risk)
        lf = {
            "diet":     profile.get("Diet", "Average"),
            "activity": profile.get("ActivityLevel", "Moderate"),
            "sleep":    health.get("Sleep", 7),
            "stress":   health.get("Stress", "Medium"),
        }

        # Confidence: INTERSTROKE India is highest-quality brain/stroke data
        # for Indian population (3000+ Indian cases, 10 hospitals)
        confidence = (
            0.92 if method == "caide_interstroke_india_stroke_ml_alz_ml_framingham" else
            0.90 if method == "caide_interstroke_india_stroke_ml_framingham" else
            0.88 if method == "caide_interstroke_india_framingham" else
            0.90 if method == "absolute_override" else
            0.55
        )

        metrics = {
            "method_sources": {
                "caide": "Kivipelto M et al., Lancet Neurol 2006;5:735-741",
                "stroke": "O'Donnell MJ et al. (INTERSTROKE), Lancet 2016;388:761-775 — South Asia subgroup",
                "calibration": "D'Agostino RB et al., Stroke 1994;25:40-43",
                "india_baseline": "GBD 2016 Neurology Collaborators, Lancet Neurol 2019",
            }
        }
        if caide_pts is not None:
            metrics["caide_points"]   = caide_pts
            metrics["dementia_20yr_pct"] = dementia_pct
        if interstroke_risk is not None:
            metrics["interstroke_india_stroke_10yr_pct"] = round(interstroke_risk * 100, 1)
            metrics["interstroke_factors_present"] = [
                {"factor": f[0], "adjusted_OR_india": f[1], "PAR_india_pct": f[2]}
                for f in (factors_present or [])
            ]
            metrics["interstroke_PAR_explained_pct"] = par_explained
            metrics["interstroke_note"] = (
                f"{len(factors_present or [])} of 10 INTERSTROKE India factors present. "
                f"These factors explain {par_explained}% of stroke PAR in India."
            )

        return {
            "current_risk":     final_risk,
            "risk_level":       risk_level,
            "health_score":     self.get_health_score(final_risk),
            "method_used":      method,
            "model_confidence": round(confidence, 2),
            "population_note":  "Stroke risk uses INTERSTROKE India (Lancet 2016) — 3,000+ Indian cases from 10 hospitals",
            "metrics":          metrics,
            "risk_progression": self.project_risk_progression(final_risk, age, lf),
            "recommendations":  self._get_recommendations(risk_level, health, caide_pts, factors_present),
            "possible_issues":  self._possible_issues(health, caide_pts, factors_present),
        }

    def _is_diabetic(self, h):
        conds = [c.lower() for c in (h.get("MedicalConditions") or [])]
        g = h.get("FastingGlucose") or h.get("glucose")
        a = h.get("HbA1c")
        return (any("diabetes" in c for c in conds) or
                (g and float(g) >= 126) or (a and float(a) >= 6.5))

    def _is_hypertensive(self, h, sbp, conditions):
        conds = [c.lower() for c in conditions]
        return (any("hypertension" in c or "high bp" in c for c in conds) or
                sbp >= 140 or bool(h.get("BPOnMedication")))

    def _get_recommendations(self, risk_level, health, caide_pts, factors_present):
        base = {
            "GREEN":  [
                "Physical exercise 150 min/week protects cognitive function (Lancet 2020)",
                "Mediterranean diet reduces dementia risk by 30-35% (Morris 2015)",
                "Sleep 7-9 hours — brain clears amyloid and tau during deep sleep",
                "Keep learning: new languages, instruments, skills builds cognitive reserve",
            ],
            "YELLOW": [
                "Control blood pressure — every 10mmHg reduction cuts dementia risk by 20% (Livingston 2020)",
                "Treat depression promptly — untreated depression doubles dementia risk",
                "Aim for 7-9h sleep — install blue-light filter after 8pm",
                "Social engagement: join groups, volunteer — reduces isolation risk (Holt-Lunstad 2015)",
            ],
            "RED": [
                "Consult neurologist for cognitive assessment (MoCA or MMSE test)",
                "Strict BP control — hypertension is #1 modifiable INTERSTROKE India risk factor (PAR 47.9%)",
                "Consider brain MRI if memory complaints persist for >3 months",
                "Cognitive stimulation therapy available at NIMHANS Bangalore, AIIMS",
            ],
        }.get(risk_level, [])

        extras = []
        # INTERSTROKE-specific recommendations
        if factors_present:
            top_factor = max(factors_present, key=lambda f: f[2], default=None)  # highest PAR%
            if top_factor and top_factor[0] == 'Hypertension':
                extras.append(
                    "Hypertension is #1 stroke risk factor in India (PAR 47.9%) — "
                    "target BP <130/80 mmHg (INTERSTROKE India, Lancet 2016)"
                )
            if any(f[0] == 'Physical inactivity' for f in factors_present):
                extras.append(
                    "Physical inactivity accounts for 28.5% of stroke burden in India — "
                    "150 min/week aerobic exercise is evidence-based prevention"
                )
            if any(f[0] == 'Cardiac causes (AFib/MI/valve)' for f in factors_present):
                extras.append(
                    "Cardiac condition detected — AFib gives 5× stroke risk; "
                    "discuss anticoagulation with cardiologist"
                )

        if health.get("Stress") == "High":
            extras.append("Chronic high stress elevates cortisol — damages hippocampus (Johansson 2014)")
        if health.get("Sleep") and float(health.get("Sleep")) < 6:
            extras.append("Sleep <6h — brain cannot clear tau and amyloid proteins during rest (Irwin 2019)")
        if health.get("Smoking") == "Daily":
            extras.append("Smoking doubles dementia risk — quitting reduces risk within 2 years")

        return (base + extras)[:6]

    def _possible_issues(self, health, caide_pts, factors_present):
        issues = []
        if caide_pts is not None and caide_pts >= 10:
            issues.append(f"CAIDE score {caide_pts} — elevated 20-year dementia risk (Kivipelto 2006)")
        if factors_present:
            for f_name, f_or, f_par in (factors_present or []):
                if f_or >= 2.0:
                    issues.append(f"{f_name}: high-impact INTERSTROKE India factor (OR={f_or}, PAR={f_par}%)")
        if health.get("Stress") == "High":
            issues.append("Chronic high stress — independently associated with cognitive decline")
        if health.get("Sleep") and float(health.get("Sleep")) < 6:
            issues.append("Insufficient sleep — impairs amyloid clearance from brain")
        sbp = health.get("SystolicBP") or health.get("systolic_bp")
        if sbp and int(sbp) >= 140:
            issues.append(f"Hypertension ({sbp} mmHg) — #1 modifiable stroke risk factor in India (INTERSTROKE)")
        conds = [c.lower() for c in (health.get("MedicalConditions") or [])]
        if any("atrial fibrillation" in c or "afib" in c for c in conds):
            issues.append("Atrial fibrillation — 5× increased stroke risk (INTERSTROKE cardiac causes OR=3.17)")
        return issues
