# utils/input_completeness.py
# Input completeness scorer — tells users which key inputs are present/missing
# and how completeness affects model confidence.
#
# Design principle: users should know WHAT the model used and WHAT was assumed.
# "Your heart score is based on 6 of 9 key inputs. Missing: HDL, Fasting glucose."
#
# Tiers of inputs:
#   CRITICAL: inputs that directly feed clinical formulas (PCE, FIB-4, INTERSTROKE)
#   IMPORTANT: inputs that improve accuracy significantly
#   HELPFUL:   inputs that allow switching to a better method

ORGAN_INPUT_SPECS = {
    "heart": {
        "critical": [
            ("Age",             "ProfileInfo.Age",             "Age is required for Framingham PCE"),
            ("Gender",          "ProfileInfo.Gender",          "Gender required for sex-specific risk"),
            ("SystolicBP",      "HealthInfo.SystolicBP",       "Systolic BP is #1 modifiable CVD risk factor"),
            ("TotalCholesterol","HealthInfo.TotalCholesterol",  "Total cholesterol required for PCE"),
        ],
        "important": [
            ("HDL Cholesterol", "HealthInfo.HDLCholesterol",   "HDL improves PCE accuracy — assumed 45 mg/dL if missing"),
            ("Smoking status",  "HealthInfo.Smoking",          "Smoking doubles CVD risk"),
            ("Diabetes status", "HealthInfo.MedicalConditions","Diabetes multiplies CVD risk by 2-4×"),
        ],
        "helpful": [
            ("Fasting glucose", "HealthInfo.FastingGlucose",   "Direct diabetes detection"),
            ("HbA1c",           "HealthInfo.HbA1c",            "Average blood sugar over 3 months"),
            ("District",        "ProfileInfo.District",        "Enables NFHS-5 district prior adjustment"),
        ]
    },
    "brain": {
        "critical": [
            ("Age",             "ProfileInfo.Age",             "Age is the strongest CAIDE dementia factor"),
            ("SystolicBP",      "HealthInfo.SystolicBP",       "Hypertension is #1 INTERSTROKE India stroke factor (PAR 47.9%)"),
            ("Smoking",         "HealthInfo.Smoking",          "Smoking contributes 12.4% of stroke PAR in India"),
        ],
        "important": [
            ("BMI",             "HealthInfo.Bmi",              "Abdominal obesity is INTERSTROKE India factor (PAR 18.6%)"),
            ("Total cholesterol","HealthInfo.TotalCholesterol", "Cholesterol required for CAIDE score"),
            ("Sleep hours",     "HealthInfo.Sleep",            "Sleep <6h increases dementia risk"),
            ("Stress level",    "HealthInfo.Stress",           "High stress = INTERSTROKE India psychosocial factor (PAR 17.4%)"),
        ],
        "helpful": [
            ("Education years", "HealthInfo.EducationYears",   "Low education is CAIDE dementia risk factor"),
            ("Physical activity","ProfileInfo.ActivityLevel",  "Inactivity = 28.5% of stroke PAR in India"),
            ("HDL cholesterol", "HealthInfo.HDLCholesterol",   "Used for chol/HDL ratio (INTERSTROKE apo ratio proxy)"),
        ]
    },
    "liver": {
        "critical": [
            ("ALT",             "HealthInfo.ALT",              "ALT required for FIB-4 and ILPD Indian model"),
            ("AST",             "HealthInfo.AST",              "AST required for FIB-4 index"),
            ("Age",             "ProfileInfo.Age",             "Age required for FIB-4 formula"),
        ],
        "important": [
            ("Platelets",       "HealthInfo.Platelets",        "Platelets required for FIB-4 (completes formula)"),
            ("BMI",             "HealthInfo.Bmi",              "Required for NAFLD Liver Fat Score and lean NAFLD rule"),
            ("Alcohol use",     "HealthInfo.Alcohol",          "Alcohol is highest-impact modifiable liver risk"),
            ("Albumin",         "HealthInfo.Albumin",          "Low albumin indicates impaired liver function"),
        ],
        "helpful": [
            ("GGT",             "HealthInfo.GGT",              "GGT is alcohol and bile duct marker"),
            ("Total bilirubin", "HealthInfo.TotalBilirubin",   "Required for ILPD Indian model features"),
            ("Fasting glucose", "HealthInfo.FastingGlucose",   "Diabetes worsens NAFLD progression"),
        ]
    },
    "kidney": {
        "critical": [
            ("Serum creatinine","HealthInfo.SerumCreatinine",  "CKD-EPI 2021 requires creatinine for eGFR"),
            ("Age",             "ProfileInfo.Age",             "Age required for CKD-EPI equation"),
            ("Gender",          "ProfileInfo.Gender",          "Sex required for CKD-EPI equation"),
        ],
        "important": [
            ("Urine protein",   "HealthInfo.UrineProtein",     "Proteinuria is key CKD progression marker"),
            ("SystolicBP",      "HealthInfo.SystolicBP",       "Hypertension is #1 cause of CKD in India"),
            ("Diabetes",        "HealthInfo.MedicalConditions","Diabetic nephropathy = 40% of CKD in India"),
        ],
        "helpful": [
            ("HbA1c",           "HealthInfo.HbA1c",            "Glycaemic control predicts CKD progression"),
            ("Haemoglobin",     "HealthInfo.Haemoglobin",      "Anaemia is indicator of advanced CKD"),
            ("Uric acid",       "HealthInfo.UricAcid",         "Hyperuricaemia accelerates CKD"),
        ]
    },
    "lungs": {
        "critical": [
            ("Smoking status",  "HealthInfo.Smoking",          "Smoking is #1 COPD risk factor"),
            ("City",            "HealthInfo.City",             "Required for CPCB PM2.5 AQI lookup"),
        ],
        "important": [
            ("Pack-years",      "HealthInfo.PackYears",        "Pack-years required for GOLD staging"),
            ("Cooking fuel",    "HealthInfo.CookingFuel",      "Biomass cooking adds 22-25% lung risk (Balakrishnan 2019)"),
            ("TB history",      "HealthInfo.MedicalConditions","TB in conditions triggers post-TB lung risk"),
        ],
        "helpful": [
            ("FEV1%",           "HealthInfo.FEV1Percent",      "Spirometry enables GOLD staging (highest confidence)"),
            ("Activity level",  "ProfileInfo.ActivityLevel",   "Exercise improves FEV1 by 5-8% in COPD"),
            ("Tobacco type",    "HealthInfo.TobaccoType",      "Bidi = 1.5× cigarette-equivalent pack-years"),
        ]
    },
    "biological_age": {
        "critical": [
            ("Age",             "ProfileInfo.Age",             "Chronological age required for KDM"),
            ("BMI",             "HealthInfo.Bmi",              "BMI is a KDM biomarker"),
            ("SystolicBP",      "HealthInfo.SystolicBP",       "SBP is the strongest KDM biomarker"),
        ],
        "important": [
            ("Total cholesterol","HealthInfo.TotalCholesterol", "Key KDM biomarker"),
            ("Fasting glucose", "HealthInfo.FastingGlucose",   "KDM metabolic biomarker"),
            ("ALT",             "HealthInfo.ALT",              "KDM hepatic biomarker"),
            ("Triglycerides",   "HealthInfo.Triglycerides",    "KDM inflammatory proxy"),
        ],
        "helpful": [
            ("Waist circumference","HealthInfo.WaistCircumference","India-specific no-lab KDM biomarker (WHO Asia-Pacific 2004)"),
            ("Resting heart rate","HealthInfo.RestingHeartRate", "No-lab KDM biomarker (Carnethon 2014)"),
            ("Serum creatinine","HealthInfo.SerumCreatinine",  "Enables CKD-EPI eGFR — strong KDM biomarker"),
            ("HbA1c",           "HealthInfo.HbA1c",            "Average glycaemia — KDM metabolic biomarker"),
        ]
    }
}


def _get_value(data: dict, path: str):
    """Resolve ProfileInfo.X or HealthInfo.X from data dict."""
    parts = path.split(".")
    if len(parts) == 2:
        section, key = parts
        val = data.get(section, {}).get(key)
        if val is None:
            return None
        # MedicalConditions is a list — count as present if non-empty
        if isinstance(val, list):
            return val if len(val) > 0 else None
        return val
    return None


def score_completeness(data: dict, organ: str) -> dict:
    """
    Compute input completeness for a given organ.

    Returns:
      {
        "organ": str,
        "completeness_pct": float,           # 0-100
        "completeness_tier": str,            # "Minimal" / "Partial" / "Good" / "Excellent"
        "inputs_provided": int,
        "inputs_total": int,
        "critical_complete": bool,
        "critical_missing": [str],
        "important_missing": [str],
        "helpful_missing": [str],
        "confidence_impact": str,            # narrative
        "summary": str                       # "Your liver score is based on 5 of 10 key inputs"
      }
    """
    spec = ORGAN_INPUT_SPECS.get(organ, {})
    critical   = spec.get("critical",   [])
    important  = spec.get("important",  [])
    helpful    = spec.get("helpful",    [])

    all_inputs = critical + important + helpful
    total = len(all_inputs)

    provided_count  = 0
    critical_missing  = []
    important_missing = []
    helpful_missing   = []
    critical_provided = []

    for name, path, note in critical:
        if _get_value(data, path) is not None:
            provided_count += 1
            critical_provided.append(name)
        else:
            critical_missing.append({"input": name, "note": note})

    for name, path, note in important:
        if _get_value(data, path) is not None:
            provided_count += 1
        else:
            important_missing.append({"input": name, "note": note})

    for name, path, note in helpful:
        if _get_value(data, path) is not None:
            provided_count += 1
        else:
            helpful_missing.append({"input": name, "note": note})

    critical_complete = len(critical_missing) == 0
    pct = round((provided_count / total) * 100) if total > 0 else 0

    if pct >= 85:
        tier = "Excellent"
        confidence_impact = "All key inputs present — maximum model accuracy"
    elif pct >= 65:
        tier = "Good"
        confidence_impact = "Most inputs present — model accuracy is good"
    elif pct >= 40:
        tier = "Partial"
        confidence_impact = "Some inputs missing — model uses clinical defaults for missing values"
    else:
        tier = "Minimal"
        confidence_impact = "Many inputs missing — estimates use population averages, accuracy is limited"

    if not critical_complete:
        missing_names = [m["input"] for m in critical_missing]
        confidence_impact = f"Critical inputs missing ({', '.join(missing_names)}) — estimates use defaults"

    summary = (
        f"Your {organ} score is based on {provided_count} of {total} key inputs. "
        + (f"Missing critical: {', '.join(m['input'] for m in critical_missing)}. " if critical_missing else "")
        + (f"Improve by adding: {', '.join(m['input'] for m in important_missing[:2])}." if important_missing else "")
    ).strip()

    return {
        "organ":               organ,
        "completeness_pct":    pct,
        "completeness_tier":   tier,
        "inputs_provided":     provided_count,
        "inputs_total":        total,
        "critical_complete":   critical_complete,
        "critical_missing":    critical_missing,
        "important_missing":   important_missing[:3],   # top 3 most impactful
        "helpful_missing":     helpful_missing[:2],
        "confidence_impact":   confidence_impact,
        "summary":             summary,
    }


def score_all_organs(data: dict) -> dict:
    """
    Score completeness for all organs + biological age.
    Returns dict keyed by organ name.
    """
    organs = ["heart", "brain", "liver", "kidney", "lungs", "biological_age"]
    result = {}
    for organ in organs:
        result[organ] = score_completeness(data, organ)

    # Overall completeness
    all_pcts = [result[o]["completeness_pct"] for o in organs]
    overall = round(sum(all_pcts) / len(all_pcts))
    result["_overall"] = {
        "overall_completeness_pct": overall,
        "tier": (
            "Excellent" if overall >= 85 else
            "Good"      if overall >= 65 else
            "Partial"   if overall >= 40 else
            "Minimal"
        ),
        "recommendation": (
            "For highest accuracy: add lab values (cholesterol, glucose, liver enzymes)"
            if overall < 65 else
            "Good data quality — consider adding spirometry (FEV1%) and waist circumference"
            if overall < 85 else
            "Excellent data quality — all key clinical inputs are present"
        )
    }
    return result
