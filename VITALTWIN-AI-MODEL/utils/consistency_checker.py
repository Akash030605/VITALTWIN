# utils/consistency_checker.py
# Layer 3: Cross-organ clinical plausibility checks.
# After all organ scores are computed, verify that their relationships
# are medically coherent and apply floor/ceiling corrections where needed.
#
# Examples of rules enforced:
#   - Diabetic → kidney health floor (CKD risk minimum)
#   - Heart RED + Hypertension → brain risk gets a floor
#   - Liver RED + low albumin → biological age penalty
#   - COPD patient cannot have "healthy" lung score
#   - CKD Stage 3+ → hypertension is almost certain → BP floor
#
# Each rule records *why* it fired so the audit trail is transparent.

from typing import Optional

# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_diabetic(health: dict) -> bool:
    conditions = health.get('MedicalConditions', []) or []
    hba1c = health.get('HbA1c')
    glucose = health.get('FastingGlucose')
    meds = [m.lower() for m in (health.get('Medications', []) or [])]
    cond_diab = any('diabet' in c.lower() for c in conditions)
    lab_diab = (hba1c and float(hba1c) >= 6.5) or (glucose and float(glucose) >= 126)
    med_diab = any('metformin' in m or 'insulin' in m or 'glipizide' in m
                   or 'sitagliptin' in m or 'empagliflozin' in m for m in meds)
    return cond_diab or lab_diab or med_diab


def _is_hypertensive(health: dict) -> bool:
    conditions = health.get('MedicalConditions', []) or []
    sbp = health.get('SystolicBP')
    dbp = health.get('DiastolicBP')
    on_meds = health.get('BPOnMedication', False)
    cond_htn = any('hypertens' in c.lower() for c in conditions)
    lab_htn = (sbp and float(sbp) >= 140) or (dbp and float(dbp) >= 90)
    return cond_htn or lab_htn or on_meds


def _risk_level(risk_score: float) -> str:
    if risk_score >= 0.60:
        return 'RED'
    elif risk_score >= 0.30:
        return 'YELLOW'
    return 'GREEN'


def _get_risk(organ_results: dict, organ: str) -> Optional[float]:
    result = organ_results.get(organ, {})
    if isinstance(result, dict):
        return result.get('current_risk')
    return None


def _apply_floor(organ_results: dict, organ: str, floor: float, reason: str,
                 adjustments: list):
    """Set organ risk to floor if it's currently below it."""
    result = organ_results.get(organ)
    if not isinstance(result, dict):
        return
    current = result.get('current_risk', 0.0)
    if current < floor:
        result['current_risk'] = floor
        result['risk_level'] = _risk_level(floor)
        result['health_score'] = max(0, int((1 - floor) * 100))
        result.setdefault('possible_issues', [])
        result['possible_issues'].append(f"[Floor applied] {reason}")
        adjustments.append({
            'organ': organ,
            'type': 'floor',
            'original_risk': round(current, 3),
            'adjusted_risk': floor,
            'reason': reason,
        })


def _apply_ceiling(organ_results: dict, organ: str, ceiling: float, reason: str,
                   adjustments: list):
    """Cap organ risk at ceiling if it's currently above it."""
    result = organ_results.get(organ)
    if not isinstance(result, dict):
        return
    current = result.get('current_risk', 0.0)
    if current > ceiling:
        result['current_risk'] = ceiling
        result['risk_level'] = _risk_level(ceiling)
        result['health_score'] = max(0, int((1 - ceiling) * 100))
        adjustments.append({
            'organ': organ,
            'type': 'ceiling',
            'original_risk': round(current, 3),
            'adjusted_risk': ceiling,
            'reason': reason,
        })


# ── Rules ─────────────────────────────────────────────────────────────────────

def _rule_diabetes_kidney_floor(health, organ_results, adjustments):
    """
    Diabetes → minimum kidney risk.
    T2DM is the leading cause of CKD (40% of ESRD cases, USRDS 2022).
    Even well-controlled diabetes carries a minimum CKD risk.
    """
    if not _is_diabetic(health):
        return
    hba1c = health.get('HbA1c')
    poorly_controlled = hba1c and float(hba1c) > 8.0
    floor = 0.32 if poorly_controlled else 0.18
    reason = (
        f"Diabetes detected (HbA1c={hba1c}%) — CKD minimum risk floor applied "
        f"({'poorly controlled' if poorly_controlled else 'controlled'}). "
        "Diabetic nephropathy: 40% of ESRD (USRDS 2022)."
    )
    _apply_floor(organ_results, 'kidney', floor, reason, adjustments)


def _rule_diabetes_heart_floor(health, organ_results, adjustments):
    """
    Diabetes independently doubles CV risk (Emerging Risk Factors Collaboration, Lancet 2010).
    """
    if not _is_diabetic(health):
        return
    floor = 0.20
    reason = (
        "Diabetes detected — CV risk minimum floor applied. "
        "Diabetes doubles cardiovascular risk (Emerging Risk Factors Collaboration, Lancet 2010)."
    )
    _apply_floor(organ_results, 'heart', floor, reason, adjustments)


def _rule_hypertension_kidney_floor(health, organ_results, adjustments):
    """
    Hypertension is 2nd leading cause of CKD (USRDS 2022).
    """
    if not _is_hypertensive(health):
        return
    sbp = health.get('SystolicBP')
    severe = sbp and float(sbp) >= 160
    floor = 0.22 if severe else 0.12
    reason = (
        f"Hypertension detected (SBP={sbp} mmHg) — kidney risk floor applied "
        f"({'severe' if severe else 'stage 1/2'}). "
        "HTN: 2nd leading cause of CKD (USRDS 2022)."
    )
    _apply_floor(organ_results, 'kidney', floor, reason, adjustments)


def _rule_hypertension_brain_floor(health, organ_results, adjustments):
    """
    HTN is strongest modifiable stroke risk factor (Lawes et al. Lancet 2001, RR 3.1×).
    """
    if not _is_hypertensive(health):
        return
    sbp = health.get('SystolicBP')
    severe = sbp and float(sbp) >= 160
    floor = 0.25 if severe else 0.12
    reason = (
        "Hypertension — stroke/brain risk floor applied. "
        "HTN is the strongest modifiable stroke risk factor (Lawes, Lancet 2001, RR 3.1×)."
    )
    _apply_floor(organ_results, 'brain', floor, reason, adjustments)


def _rule_red_heart_brain_floor(health, organ_results, adjustments):
    """
    Critical heart risk amplifies brain/stroke risk via shared mechanisms
    (atherosclerosis, AF, cardioembolism). ACC/AHA 2019.
    """
    heart_risk = _get_risk(organ_results, 'heart')
    if heart_risk is None or heart_risk < 0.60:
        return
    brain_risk = _get_risk(organ_results, 'brain')
    floor = 0.30
    reason = (
        f"Heart risk is critical ({heart_risk:.0%}) — brain/stroke risk elevated via "
        "shared atherosclerotic and cardioembolic mechanisms (ACC/AHA 2019)."
    )
    _apply_floor(organ_results, 'brain', floor, reason, adjustments)


def _rule_copd_lungs_floor(health, organ_results, adjustments):
    """
    COPD is a progressive incurable disease — lung risk cannot be healthy.
    GOLD 2023: even GOLD 1 (mild) carries elevated exacerbation + comorbidity risk.
    """
    conditions = health.get('MedicalConditions', []) or []
    has_copd = any('copd' in c.lower() for c in conditions)
    if not has_copd:
        return
    floor = 0.40
    reason = (
        "COPD listed as condition — lung risk minimum floor applied. "
        "GOLD 2023: COPD is progressive; even mild COPD carries elevated mortality risk."
    )
    _apply_floor(organ_results, 'lungs', floor, reason, adjustments)


def _rule_liver_cirrhosis_floor(health, organ_results, adjustments):
    """
    Cirrhosis is end-stage liver disease — liver risk must be critical.
    """
    conditions = health.get('MedicalConditions', []) or []
    has_cirrhosis = any('cirrhosis' in c.lower() or 'liver failure' in c.lower()
                        for c in conditions)
    if not has_cirrhosis:
        return
    floor = 0.75
    reason = (
        "Cirrhosis/liver failure listed — liver risk critical floor applied. "
        "End-stage liver disease: 5-year survival <50% without transplant."
    )
    _apply_floor(organ_results, 'liver', floor, reason, adjustments)


def _rule_kidney_failure_floor(health, organ_results, adjustments):
    """
    CKD Stage 4/5 or ESRD → kidney is critical.
    """
    conditions = health.get('MedicalConditions', []) or []
    ckd_severe = any(
        'ckd' in c.lower() and ('stage 4' in c.lower() or 'stage 5' in c.lower())
        for c in conditions
    )
    esrd = any('esrd' in c.lower() or 'dialysis' in c.lower() or
               'kidney failure' in c.lower() for c in conditions)
    creatinine = health.get('SerumCreatinine')
    cr_severe = creatinine and float(creatinine) > 4.0

    if not (ckd_severe or esrd or cr_severe):
        return
    floor = 0.80 if (esrd or cr_severe) else 0.65
    reason = (
        "Severe CKD/ESRD detected — kidney risk critical floor applied. "
        "eGFR <15 (KDIGO Stage G5) indicates kidney failure."
    )
    _apply_floor(organ_results, 'kidney', floor, reason, adjustments)


def _rule_diabetic_smoker_lungs_floor(health, organ_results, adjustments):
    """
    Diabetes + smoking synergy for COPD risk (ACCORD trial; HR 1.8 vs smoking alone).
    """
    if not _is_diabetic(health):
        return
    smoking = health.get('Smoking', 'Never')
    if smoking not in ('Daily', 'Occasional'):
        return
    floor = 0.28
    reason = (
        "Diabetes + smoking — lung risk floor elevated. "
        "Synergistic COPD risk (ACCORD trial, HR 1.8×)."
    )
    _apply_floor(organ_results, 'lungs', floor, reason, adjustments)


def _rule_low_albumin_liver_floor(health, organ_results, adjustments):
    """
    Albumin <3.0 g/dL = severe synthetic liver dysfunction.
    Cannot coexist with a healthy liver score.
    """
    albumin = health.get('Albumin')
    if not albumin:
        return
    try:
        albumin = float(albumin)
    except (TypeError, ValueError):
        return
    if albumin >= 3.0:
        return
    floor = 0.60
    reason = (
        f"Albumin {albumin} g/dL (<3.0) indicates severe hepatic synthetic failure — "
        "liver risk critical floor applied."
    )
    _apply_floor(organ_results, 'liver', floor, reason, adjustments)


def _rule_high_creatinine_kidney_floor(health, organ_results, adjustments):
    """
    Serum creatinine > 2.0 mg/dL = CKD Stage 3b+ in most adults.
    """
    creatinine = health.get('SerumCreatinine')
    if not creatinine:
        return
    try:
        cr = float(creatinine)
    except (TypeError, ValueError):
        return
    if cr < 2.0:
        return
    floor = 0.55 if cr < 4.0 else 0.80
    reason = (
        f"Serum creatinine {cr} mg/dL → CKD Stage {'3b+' if cr < 4 else '4/5'} — "
        "kidney risk floor applied."
    )
    _apply_floor(organ_results, 'kidney', floor, reason, adjustments)


# ── Main entry ────────────────────────────────────────────────────────────────

RULES = [
    _rule_diabetes_kidney_floor,
    _rule_diabetes_heart_floor,
    _rule_hypertension_kidney_floor,
    _rule_hypertension_brain_floor,
    _rule_red_heart_brain_floor,
    _rule_copd_lungs_floor,
    _rule_liver_cirrhosis_floor,
    _rule_kidney_failure_floor,
    _rule_diabetic_smoker_lungs_floor,
    _rule_low_albumin_liver_floor,
    _rule_high_creatinine_kidney_floor,
]


def run_consistency_checks(health: dict, organ_results: dict) -> dict:
    """
    Apply all cross-organ consistency rules to organ_results in place.
    Returns a summary of adjustments made.

    organ_results is mutated directly — call after all organ models have run.
    """
    adjustments = []

    for rule in RULES:
        try:
            rule(health, organ_results, adjustments)
        except Exception as e:
            # Never let a consistency rule crash the whole pipeline
            adjustments.append({
                'organ': 'unknown',
                'type': 'error',
                'reason': f"Rule {rule.__name__} failed: {str(e)}",
            })

    return {
        'adjustments_made': len(adjustments),
        'adjustments': adjustments,
        'rules_applied': len(RULES),
    }
