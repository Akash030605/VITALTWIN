# utils/confidence_scorer.py
# Layer 2: Per-organ confidence scoring based on inputs actually provided.
# The more clinical data the user provides, the higher the confidence.
# This drives the UI "confidence badge" shown next to each organ score.

from typing import Optional

# ── Confidence contribution weights per organ ─────────────────────────────────
# Each field adds a confidence increment if present and valid.
# Base confidence starts from a minimum (rule-based floor) for all organs.

ORGAN_CONFIDENCE_CONFIG = {
    'heart': {
        'base': 0.45,          # pure rule-based minimum
        'fields': {
            'SystolicBP':        0.12,
            'TotalCholesterol':  0.10,
            'HDLCholesterol':    0.08,
            'LDLCholesterol':    0.04,
            'Triglycerides':     0.03,
            'FastingGlucose':    0.04,
            'HbA1c':             0.05,
            'FamilyHistoryHeart':0.05,
            'BPOnMedication':    0.02,
            'YearsSmoking':      0.02,
        },
        'max': 0.94,
    },
    'liver': {
        'base': 0.45,
        'fields': {
            'AST':               0.15,
            'ALT':               0.15,
            'Platelets':         0.12,   # FIB-4 requires this
            'GGT':               0.06,
            'Albumin':           0.05,
            'Bmi':               0.04,
            'FastingGlucose':    0.04,
            'TotalCholesterol':  0.03,
            'Triglycerides':     0.03,
        },
        'max': 0.92,
    },
    'kidney': {
        'base': 0.45,
        'fields': {
            'SerumCreatinine':   0.25,   # required for CKD-EPI
            'SystolicBP':        0.08,
            'HbA1c':             0.06,
            'FastingGlucose':    0.04,
            'FamilyHistoryKidney':0.05,
            'Albumin':           0.04,
        },
        'max': 0.96,
    },
    'brain': {
        'base': 0.45,
        'fields': {
            'SystolicBP':        0.10,
            'TotalCholesterol':  0.08,
            'Bmi':               0.06,
            'FastingGlucose':    0.06,
            'HbA1c':             0.05,
            'FamilyHistoryHeart':0.04,   # proxy for stroke family history
        },
        'max': 0.86,
    },
    'lungs': {
        'base': 0.45,
        'fields': {
            'FEV1Percent':       0.28,   # spirometry: highest impact
            'YearsSmoking':      0.06,
            'CigarettesPerDay':  0.06,
            'PackYears':         0.08,
            'TobaccoType':       0.03,
            'CookingFuel':       0.05,
        },
        'max': 0.96,
    },
    'biological_age': {
        'base': 0.50,
        'fields': {
            'SerumCreatinine':   0.08,
            'TotalCholesterol':  0.07,
            'HDLCholesterol':    0.06,
            'FastingGlucose':    0.06,
            'HbA1c':             0.06,
            'SystolicBP':        0.06,
            'Albumin':           0.05,
            'ALT':               0.05,
            'Triglycerides':     0.04,
            'Bmi':               0.04,
        },
        'max': 0.90,
    },
}

# ── Data quality tiers ────────────────────────────────────────────────────────
CONFIDENCE_TIERS = [
    (0.85, 'High',     'Results based on validated clinical formulas with lab data'),
    (0.70, 'Moderate', 'Results based on clinical proxies; lab data would improve accuracy'),
    (0.55, 'Low',      'Results are estimates based on lifestyle inputs only — provide lab values for accuracy'),
    (0.0,  'Minimal',  'Only basic inputs available; treat as screening estimate only'),
]

def score_organ_confidence(organ: str, health: dict, profile: dict) -> dict:
    """
    Score confidence for a single organ based on available inputs.
    Returns a confidence dict ready to attach to organ result.
    """
    config = ORGAN_CONFIDENCE_CONFIG.get(organ, {'base': 0.45, 'fields': {}, 'max': 0.80})

    score = config['base']
    contributing = []
    missing_key_fields = []

    all_inputs = {**health, **profile}

    for field, weight in config['fields'].items():
        val = all_inputs.get(field)
        if val is not None and val != '' and val is not False:
            # Boolean True fields still count (FamilyHistory etc.)
            if isinstance(val, bool) or (isinstance(val, (int, float)) and not isinstance(val, bool)):
                score += weight
                contributing.append(field)
            elif isinstance(val, str) and len(val) > 0:
                score += weight
                contributing.append(field)
        else:
            missing_key_fields.append(field)

    final_score = min(config['max'], round(score, 3))

    # Map to tier
    tier_label, tier_desc = 'Minimal', 'Only basic inputs available'
    for threshold, label, desc in CONFIDENCE_TIERS:
        if final_score >= threshold:
            tier_label, tier_desc = label, desc
            break

    return {
        'score': final_score,
        'tier': tier_label,
        'description': tier_desc,
        'fields_present': len(contributing),
        'fields_missing': missing_key_fields[:5],  # top 5 to guide user
    }


def score_all_organs(health: dict, profile: dict) -> dict:
    """
    Compute confidence for all organs + biological age.
    Returns dict keyed by organ name.
    """
    return {
        organ: score_organ_confidence(organ, health, profile)
        for organ in ORGAN_CONFIDENCE_CONFIG
    }


def overall_confidence(organ_confidences: dict) -> dict:
    """
    Aggregate organ confidences into a single overall report confidence.
    Weighted by organ importance for overall health assessment.
    """
    organ_weights = {
        'heart': 0.30,
        'kidney': 0.20,
        'liver': 0.18,
        'lungs': 0.17,
        'brain': 0.15,
    }
    total_weight = 0.0
    weighted_sum = 0.0
    for organ, weight in organ_weights.items():
        c = organ_confidences.get(organ, {}).get('score', 0.45)
        weighted_sum += c * weight
        total_weight += weight

    overall_score = round(weighted_sum / total_weight, 3) if total_weight > 0 else 0.50

    tier_label, tier_desc = 'Minimal', 'Only basic inputs available'
    for threshold, label, desc in CONFIDENCE_TIERS:
        if overall_score >= threshold:
            tier_label, tier_desc = label, desc
            break

    return {
        'score': overall_score,
        'tier': tier_label,
        'description': tier_desc,
        'message': (
            f"Report confidence: {tier_label} ({overall_score:.0%}). "
            f"{tier_desc}."
        )
    }
