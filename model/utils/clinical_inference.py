# utils/clinical_inference.py
"""
Clinical Inference Layer
Enriches health data using already-collected fields (no new user inputs needed).

Improvements implemented:
  A. Smoking duration → pack-years inference (age + smoking status → GATS India onset curve)
  B. Height + Weight → waist circumference proxy (Dudeja 2001 Asia-Pacific formula)
  C. Medical conditions → BP numeric inference (Hypertension stage labels → SBP/DBP)
  D. Medical conditions → HbA1c proxy (Diabetes severity labels → HbA1c estimate)
"""

import math


# ──────────────────────────────────────────────────────────────────────────────
# A. SMOKING DURATION → PACK-YEARS INFERENCE
# Source: GATS India 2009-10, mean smoking initiation age by gender:
#   Male: 19.4 yr  Female: 21.2 yr  (Global Adult Tobacco Survey India)
# Bidi users: 3× tar multiplier per Jindal SK (Chest 2006)
# ──────────────────────────────────────────────────────────────────────────────
_GATS_ONSET_MALE   = 19.4
_GATS_ONSET_FEMALE = 21.2
_GATS_ONSET_OTHER  = 20.0

def infer_pack_years(health: dict, profile: dict) -> dict:
    """
    If pack_years is already provided and >0, return as-is.
    Otherwise infer from age + smoking status + gender.
    Returns enriched health dict (copy, not mutated).
    """
    enriched = dict(health)

    # Already have numeric pack years? Skip.
    existing = float(enriched.get('PackYears') or enriched.get('pack_years') or 0)
    if existing > 0:
        return enriched

    smoking = str(enriched.get('SmokingStatus') or enriched.get('smoking') or 'Never')
    if smoking in ('Never', '', 'Non-smoker'):
        return enriched

    age    = float(profile.get('Age') or profile.get('age') or 40)
    gender = str(profile.get('Gender') or profile.get('gender') or 'Other')

    if 'male' in gender.lower() and 'fe' not in gender.lower():
        onset = _GATS_ONSET_MALE
    elif 'female' in gender.lower():
        onset = _GATS_ONSET_FEMALE
    else:
        onset = _GATS_ONSET_OTHER

    duration = max(0.0, age - onset)

    # Cigarettes per day by status (GATS India medians)
    cpd_map = {
        'Daily':      10,   # median daily smoker GATS India
        'Occasional':  2,   # ~2 cigs/day equivalent
    }
    cpd = cpd_map.get(smoking, 5)

    # Bidi flag: 3× tar multiplier expressed as pack-year equivalent
    smoke_type = str(enriched.get('SmokeType') or enriched.get('smoke_type') or 'Cigarette')
    bidi_mult  = 3.0 if 'bidi' in smoke_type.lower() else 1.0

    pack_years = round((cpd / 20.0) * duration * bidi_mult, 1)

    enriched['PackYears']  = pack_years
    enriched['pack_years'] = pack_years
    enriched['_inferred_pack_years'] = True  # audit flag
    return enriched


# ──────────────────────────────────────────────────────────────────────────────
# B. BMI → WAIST CIRCUMFERENCE PROXY
# Source: Dudeja V et al. (2001) J Assoc Physicians India; Asia-Pacific formula
#   Waist ≈ 0.53 × height_cm  for males (adjusted for Indian visceral adiposity)
#   Waist ≈ 0.51 × height_cm  for females
# Also flag abdominal obesity by IDF South Asia cut-offs (M≥90, F≥80 cm)
# ──────────────────────────────────────────────────────────────────────────────
def infer_waist_circumference(health: dict, profile: dict) -> dict:
    """
    Infer waist circumference if not explicitly provided.
    Sets WaistCircumference, AbdominalObesity (bool), and WaistHipRatio proxy.
    """
    enriched = dict(health)

    # Already have waist? Keep it.
    existing_waist = float(enriched.get('WaistCircumference') or 0)
    if existing_waist > 0:
        return enriched

    height_cm = float(profile.get('Height') or profile.get('height') or 0)
    weight_kg  = float(profile.get('Weight') or profile.get('weight') or 0)
    if height_cm <= 0 or weight_kg <= 0:
        return enriched

    gender = str(profile.get('Gender') or profile.get('gender') or 'Other')
    is_female = 'female' in gender.lower()

    # Asia-Pacific regression coefficient (Dudeja 2001)
    coeff = 0.51 if is_female else 0.53

    # BMI correction: add 1 cm per BMI unit above 23 (South Asian threshold)
    bmi = weight_kg / ((height_cm / 100) ** 2)
    bmi_excess = max(0.0, bmi - 23.0)
    waist = round(coeff * height_cm + bmi_excess * 1.0, 1)

    # IDF South Asia abdominal obesity cut-offs
    abdominal_obesity_threshold = 80.0 if is_female else 90.0
    abdominal_obesity = waist >= abdominal_obesity_threshold

    enriched['WaistCircumference']   = waist
    enriched['AbdominalObesity']     = abdominal_obesity
    enriched['_inferred_waist']      = True  # audit flag
    return enriched


# ──────────────────────────────────────────────────────────────────────────────
# C. MEDICAL CONDITIONS → BP NUMERIC INFERENCE
# Source: JNC 8 / AHA 2017 stage definitions
#   Normal BP: SBP<120 DBP<80
#   Elevated:  SBP 120-129
#   Stage 1:   SBP 130-139  DBP 80-89
#   Stage 2:   SBP ≥140     DBP ≥90
#   Crisis:    SBP >180     DBP >120
# Use midpoint of each range as the inference value.
# ──────────────────────────────────────────────────────────────────────────────
_CONDITION_BP_MAP = {
    # Hypertension staging
    'hypertension stage 1':      (134, 84),
    'hypertension stage 2':      (155, 96),
    'hypertension crisis':       (185, 122),
    # Heart conditions that carry HTN
    'heart failure stage c':     (150, 92),
    'heart failure stage d':     (158, 98),
    'coronary artery disease - moderate': (140, 88),
    'coronary artery disease - severe':   (148, 94),
    # Kidney conditions with HTN comorbidity rates >70%
    'ckd stage 3':               (140, 88),
    'ckd stage 4':               (148, 92),
    'ckd stage 5':               (155, 96),
    'diabetic nephropathy':      (145, 90),
    'hypertensive nephropathy':  (155, 95),
}

def infer_blood_pressure(health: dict) -> dict:
    """
    If SystolicBP is missing or 0, scan medical_conditions for hypertension labels
    and inject a medically-grounded SBP/DBP estimate.
    Takes the HIGHEST stage found (most conservative = safest for risk estimation).
    """
    enriched = dict(health)

    existing_sbp = float(enriched.get('SystolicBP') or enriched.get('systolic_bp') or 0)
    if existing_sbp > 0:
        return enriched

    conditions = enriched.get('MedicalConditions') or enriched.get('medical_conditions') or []
    if not conditions:
        return enriched

    best_sbp, best_dbp = 0, 0
    matched = []
    for cond in conditions:
        key = cond.strip().lower()
        for pattern, (sbp, dbp) in _CONDITION_BP_MAP.items():
            if pattern in key:
                if sbp > best_sbp:
                    best_sbp, best_dbp = sbp, dbp
                    matched.append(cond)

    if best_sbp > 0:
        enriched['SystolicBP']          = best_sbp
        enriched['DiastolicBP']         = best_dbp
        enriched['systolic_bp']         = best_sbp
        enriched['diastolic_bp']        = best_dbp
        enriched['_inferred_bp']        = True   # audit flag
        enriched['_bp_source_condition'] = matched[-1] if matched else ''
    return enriched


# ──────────────────────────────────────────────────────────────────────────────
# D. MEDICAL CONDITIONS → HbA1c PROXY
# Source: ADA Standards of Care 2024
#   Normal:      HbA1c < 5.7%
#   Prediabetes: 5.7–6.4%  → use 6.1% midpoint
#   T2DM controlled: ~7.5% (ADA target ≤7.0%, mean poorly-controlled 9.5%)
#   T2DM uncontrolled: 9.5%
#   T1DM: treated ~7.8%
#   Gestational DM: 5.5% (lower range, typically early detection)
# For Indian population: add +0.3% offset (Gupta 2019, glycation gap India)
# ──────────────────────────────────────────────────────────────────────────────
_CONDITION_HBA1C_MAP = {
    'prediabetes':         6.1,
    'gestational diabetes': 5.8,
    'type 1 diabetes':     7.8,
    'type 2 diabetes':     8.2,   # +0.3 India offset on 7.9 ADA mean
    'metabolic syndrome':  6.3,
    'diabetic nephropathy': 9.0,  # late-stage implies poor glycaemic control
}

_INDIA_GLYCATION_OFFSET = 0.3  # Gupta S et al. Int J Diabetes Dev Ctries 2019

def infer_hba1c(health: dict) -> dict:
    """
    If HbA1c is missing or 0, scan conditions for diabetes labels
    and inject a conservative HbA1c estimate.
    Takes the HIGHEST HbA1c found (worst-case = safest for risk estimation).
    """
    enriched = dict(health)

    existing = float(enriched.get('HbA1c') or enriched.get('hba1c') or 0)
    if existing > 0:
        return enriched

    conditions = enriched.get('MedicalConditions') or enriched.get('medical_conditions') or []
    if not conditions:
        return enriched

    best_hba1c = 0.0
    matched_cond = ''
    for cond in conditions:
        key = cond.strip().lower()
        for pattern, val in _CONDITION_HBA1C_MAP.items():
            if pattern in key:
                if val > best_hba1c:
                    best_hba1c  = val
                    matched_cond = cond

    if best_hba1c > 0:
        enriched['HbA1c']               = round(best_hba1c, 1)
        enriched['hba1c']               = round(best_hba1c, 1)
        enriched['_inferred_hba1c']     = True
        enriched['_hba1c_source_condition'] = matched_cond
    return enriched


# ──────────────────────────────────────────────────────────────────────────────
# MASTER ENRICHMENT FUNCTION  (call this once before models run)
# ──────────────────────────────────────────────────────────────────────────────
def enrich_health_data(health: dict, profile: dict) -> dict:
    """
    Apply all 4 clinical inferences in order.
    Returns a new dict — original is never mutated.
    """
    h = infer_pack_years(health, profile)
    h = infer_waist_circumference(h, profile)
    h = infer_blood_pressure(h)
    h = infer_hba1c(h)
    return h
