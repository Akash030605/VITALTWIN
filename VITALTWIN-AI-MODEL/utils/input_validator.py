# utils/input_validator.py
# Layer 1: Input Validation — clinical range checks + consistency cross-checks
# Rejects impossible values before they reach any organ model.
# Returns structured warnings (non-fatal) and errors (fatal) so the API can
# communicate exactly what was wrong to the caller.

from typing import Any

# ── Physiological plausible ranges ───────────────────────────────────────────
# (min_hard, min_warn, max_warn, max_hard, unit, source)
CLINICAL_RANGES = {
    # ProfileInfo
    'Age':              (1,   10,  110, 130,  'years',      'NHANES/ICD'),
    'Height':           (50,  100, 230, 260,  'cm',         'WHO growth'),
    'Weight':           (2,   20,  250, 300,  'kg',         'WHO/CDC'),
    'Bmi':              (10,  14,   55,  70,  'kg/m²',      'WHO'),

    # Vitals
    'SystolicBP':       (50,  80,  200, 240,  'mmHg',       'JNC8/ISH2020'),
    'DiastolicBP':      (30,  50,  130, 150,  'mmHg',       'JNC8/ISH2020'),

    # Lipids (mg/dL)
    'TotalCholesterol': (50,  100, 350, 500,  'mg/dL',      'ACC/AHA 2019'),
    'HDLCholesterol':   (10,  20,  120, 150,  'mg/dL',      'ACC/AHA 2019'),
    'LDLCholesterol':   (10,  30,  250, 400,  'mg/dL',      'ACC/AHA 2019'),
    'Triglycerides':    (20,  50,  500, 1000, 'mg/dL',      'ACC/AHA 2019'),

    # Glucose / HbA1c
    'FastingGlucose':   (30,  60,  400, 600,  'mg/dL',      'ADA 2023'),
    'HbA1c':            (3.0, 4.0, 15,  18,   '%',          'ADA 2023'),

    # Renal
    'SerumCreatinine':  (0.2, 0.4, 15,  20,   'mg/dL',      'CKD-EPI'),

    # Liver enzymes (U/L)
    'AST':              (5,   10,  500, 2000, 'U/L',        'AASLD'),
    'ALT':              (5,   10,  500, 2000, 'U/L',        'AASLD'),
    'GGT':              (5,   10,  500, 2000, 'U/L',        'AASLD'),
    'Albumin':          (1.0, 2.5, 5.5, 6.0,  'g/dL',       'AASLD'),
    'Platelets':        (20,  50,  600, 1000, '×10³/µL',    'ISTH'),

    # Spirometry
    'FEV1Percent':      (5,   10,  130, 150,  '% predicted','GOLD 2023'),

    # Sleep
    'Sleep':            (1,   3,   12,  16,   'hours',      'AASM'),

    # Pack-years
    'PackYears':        (0,   0,   200, 300,  'pack-years', 'GOLD'),

    # Smoking duration
    'YearsSmoking':     (0,   0,   80,  100,  'years',      'clinical'),
    'CigarettesPerDay': (0,   0,   100, 120,  'cigs/day',   'clinical'),
}

# ── Enum / categorical valid values ──────────────────────────────────────────
CATEGORICAL_VALUES = {
    'Smoking':      {'Never', 'Occasional', 'Daily', 'Ex-smoker'},
    'Alcohol':      {'Never', 'Occasional', 'Weekly', 'Daily'},
    'Stress':       {'Low', 'Medium', 'High', 'Very High'},
    'ActivityLevel':{'Sedentary', 'Light', 'Moderate', 'Active', 'Very Active'},
    'Diet':         {'Poor', 'Average', 'Good', 'Excellent'},
    'Gender':       {'Male', 'Female', 'Other'},
    'TobaccoType':  {'cigarette', 'bidi', 'hookah', 'pipe', 'smokeless', 'other'},
    'CookingFuel':  {'lpg', 'png', 'electric', 'kerosene', 'wood',
                     'dung', 'coal', 'crop_residue', 'biomass'},
}


def _check_numeric(field: str, value: Any, errors: list, warnings: list):
    """Validate a single numeric field against CLINICAL_RANGES."""
    if value is None:
        return  # Optional field — skip
    try:
        v = float(value)
    except (TypeError, ValueError):
        errors.append({
            'field': field,
            'value': value,
            'message': f"{field} must be a number, got '{value}'"
        })
        return

    if field not in CLINICAL_RANGES:
        return
    min_hard, min_warn, max_warn, max_hard, unit, source = CLINICAL_RANGES[field]

    if v < min_hard or v > max_hard:
        errors.append({
            'field': field,
            'value': v,
            'unit': unit,
            'message': (
                f"{field} = {v} {unit} is outside physiologically possible range "
                f"[{min_hard}–{max_hard}] ({source})"
            )
        })
    elif v < min_warn or v > max_warn:
        warnings.append({
            'field': field,
            'value': v,
            'unit': unit,
            'message': (
                f"{field} = {v} {unit} is unusual — verify input "
                f"(expected {min_warn}–{max_warn} {unit})"
            )
        })


def _check_categorical(field: str, value: Any, warnings: list):
    """Warn (not error) on unknown categorical values — allows future extension."""
    if value is None:
        return
    allowed = CATEGORICAL_VALUES.get(field, set())
    if allowed and str(value) not in allowed:
        warnings.append({
            'field': field,
            'value': value,
            'message': f"{field} = '{value}' is not a recognized value. Expected one of: {sorted(allowed)}"
        })


def _check_bp_consistency(health: dict, errors: list, warnings: list):
    """Diastolic must be lower than systolic; pulse pressure check."""
    sbp = health.get('SystolicBP')
    dbp = health.get('DiastolicBP')
    if sbp is None or dbp is None:
        return
    try:
        sbp, dbp = float(sbp), float(dbp)
    except (TypeError, ValueError):
        return

    if dbp >= sbp:
        errors.append({
            'field': 'DiastolicBP',
            'message': f"Diastolic BP ({dbp}) must be less than Systolic BP ({sbp})"
        })
    pulse_pressure = sbp - dbp
    if pulse_pressure < 15:
        warnings.append({
            'field': 'BP',
            'message': f"Pulse pressure too narrow ({pulse_pressure} mmHg) — verify values"
        })
    if pulse_pressure > 100:
        warnings.append({
            'field': 'BP',
            'message': f"Pulse pressure very wide ({pulse_pressure} mmHg) — isolated systolic hypertension or aortic regurgitation?"
        })


def _check_lipid_consistency(health: dict, warnings: list):
    """LDL ≈ TC - HDL - TG/5 (Friedewald). Flag large discrepancies."""
    tc  = health.get('TotalCholesterol')
    hdl = health.get('HDLCholesterol')
    ldl = health.get('LDLCholesterol')
    tg  = health.get('Triglycerides')

    if tc and hdl and tc <= hdl:
        warnings.append({
            'field': 'HDLCholesterol',
            'message': f"HDL ({hdl}) cannot exceed Total Cholesterol ({tc})"
        })

    if all(v is not None for v in [tc, hdl, ldl, tg]):
        try:
            friedewald_ldl = tc - hdl - (tg / 5)
            discrepancy = abs(ldl - friedewald_ldl)
            if discrepancy > 40:
                warnings.append({
                    'field': 'LDLCholesterol',
                    'message': (
                        f"Reported LDL ({ldl}) differs from Friedewald estimate "
                        f"({friedewald_ldl:.0f}) by {discrepancy:.0f} mg/dL — verify lab report"
                    )
                })
        except (TypeError, ValueError):
            pass


def _check_diabetes_consistency(health: dict, warnings: list):
    """HbA1c and fasting glucose should be concordant."""
    hba1c   = health.get('HbA1c')
    glucose = health.get('FastingGlucose')
    conditions = health.get('MedicalConditions', []) or []
    has_diabetes = any('diabet' in c.lower() for c in conditions)

    if hba1c and glucose:
        try:
            hba1c, glucose = float(hba1c), float(glucose)
            # Approximate: HbA1c 6.5% ≈ glucose 126 mg/dL (ADA)
            expected_glucose = (hba1c - 2.15) / 0.0307
            discrepancy = abs(glucose - expected_glucose)
            if discrepancy > 60:
                warnings.append({
                    'field': 'HbA1c/FastingGlucose',
                    'message': (
                        f"HbA1c ({hba1c}%) implies glucose ≈{expected_glucose:.0f} mg/dL; "
                        f"reported {glucose} mg/dL — large discrepancy, verify values"
                    )
                })
        except (TypeError, ValueError):
            pass

    if has_diabetes and hba1c and float(hba1c) < 5.0:
        warnings.append({
            'field': 'HbA1c',
            'message': f"HbA1c {hba1c}% is below diabetic range but Diabetes is listed as a condition — verify"
        })


def _check_smoking_consistency(health: dict, warnings: list):
    """If 'Never' smoker, pack-years and cigarettes/day should be absent."""
    smoking = health.get('Smoking', 'Never')
    py = health.get('PackYears')
    cpd = health.get('CigarettesPerDay')

    if smoking == 'Never':
        if py and float(py) > 0:
            warnings.append({
                'field': 'PackYears',
                'message': "PackYears > 0 but Smoking is 'Never' — verify smoking history"
            })
        if cpd and float(cpd) > 0:
            warnings.append({
                'field': 'CigarettesPerDay',
                'message': "CigarettesPerDay > 0 but Smoking is 'Never'"
            })

    years = health.get('YearsSmoking', 0) or 0
    age = health.get('_age', 30)  # injected by validator caller
    if years and years > age - 5:
        warnings.append({
            'field': 'YearsSmoking',
            'message': f"YearsSmoking ({years}) exceeds plausible smoking history for age {age}"
        })


def validate_inputs(profile: dict, health: dict) -> dict:
    """
    Main entry point. Returns:
    {
        'valid': bool,          # False only if hard errors exist
        'errors': [...],        # Fatal — should block prediction
        'warnings': [...],      # Non-fatal — should be logged / shown to user
        'sanitized_health': {}  # health dict with None-ified out-of-range hard errors
    }
    """
    errors = []
    warnings = []

    age = profile.get('Age', 30)
    # Inject age for cross-checks
    health_with_age = {**health, '_age': age}

    # ── Profile numeric checks ────────────────────────────────────────────────
    for field in ('Age', 'Height', 'Weight'):
        _check_numeric(field, profile.get(field), errors, warnings)

    _check_numeric('Bmi', health.get('Bmi'), errors, warnings)

    # ── Categorical checks ────────────────────────────────────────────────────
    for field in ('Smoking', 'Alcohol', 'Stress', 'Diet'):
        _check_categorical(field, health.get(field), warnings)
    _check_categorical('ActivityLevel', profile.get('ActivityLevel'), warnings)
    _check_categorical('Gender', profile.get('Gender'), warnings)
    _check_categorical('TobaccoType', health.get('TobaccoType'), warnings)
    _check_categorical('CookingFuel', health.get('CookingFuel'), warnings)

    # ── Clinical numeric checks ───────────────────────────────────────────────
    for field in (
        'SystolicBP', 'DiastolicBP', 'TotalCholesterol', 'HDLCholesterol',
        'LDLCholesterol', 'Triglycerides', 'FastingGlucose', 'HbA1c',
        'SerumCreatinine', 'AST', 'ALT', 'GGT', 'Albumin', 'Platelets',
        'FEV1Percent', 'Sleep', 'PackYears', 'YearsSmoking', 'CigarettesPerDay',
    ):
        _check_numeric(field, health.get(field), errors, warnings)

    # ── Cross-field consistency ───────────────────────────────────────────────
    _check_bp_consistency(health, errors, warnings)
    _check_lipid_consistency(health, warnings)
    _check_diabetes_consistency(health_with_age, warnings)
    _check_smoking_consistency(health_with_age, warnings)

    # ── Sanitize: null out hard-error fields so downstream models don't crash ─
    error_fields = {e['field'] for e in errors}
    sanitized = {
        k: (None if k in error_fields else v)
        for k, v in health.items()
    }

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'sanitized_health': sanitized,
        'error_count': len(errors),
        'warning_count': len(warnings),
    }
