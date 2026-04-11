"""
Diagnostic test for Aarju Singh's case.
Reproduces exact values from Thyrocare report to confirm which liver model path fires.

Profile:  19F, 152cm, 48kg, Diet=Poor, Activity=Sedentary, Alcohol=Never, Smoking=Never
Lab values from Thyrocare report (30 Mar 2026):
  AST (SGOT): 18.94 U/L
  ALT (SGPT): 9.25 U/L
  GGT: 12.1 U/L
  ALP: 55.8 U/L
  Bilirubin Total: 0.58 mg/dL
  Bilirubin Direct: 0.11 mg/dL
  Albumin: 4.91 g/dL
  Total Protein: 8.39 g/dL
  Platelets: 348 x10³/µL
  Hemoglobin: 11.5 g/dL
  Creatinine: 0.63 mg/dL
  eGFR: 131 mL/min/1.73m²
  Fasting Glucose: 76.2 mg/dL
  HbA1c: 4.7%
  Cholesterol: 177 mg/dL
  HDL: 66 mg/dL
  LDL: 99 mg/dL
  Triglycerides: 57 mg/dL
  TSH: 5.015 µIU/mL
  Vitamin B12: 209 pg/mL
  Vitamin D: 31.8 ng/mL
  Iron: 55.26 µg/dL
  Transferrin Saturation: 12.81%
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from models.liver_model import LiverModel

# ──────────────────────────────────────────────────────────────────────────────
# Test Case 1: FULL LABS (as extracted from PDF correctly)
# ──────────────────────────────────────────────────────────────────────────────
full_labs = {
    "ProfileInfo": {
        "Age": 19,
        "Gender": "Female",
        "Height": 152,
        "Weight": 48,
        "Diet": "Poor",
        "ActivityLevel": "Sedentary",
    },
    "HealthInfo": {
        "Smoking": "Never",
        "Alcohol": "Never",
        "Bmi": 20.8,
        # Liver labs
        "AST": 18.94, "ast": 18.94,
        "ALT": 9.25,  "alt": 9.25,
        "GGT": 12.1,  "ggt": 12.1,
        "ALP": 55.8,  "alp": 55.8,
        "TotalBilirubin": 0.58,
        "DirectBilirubin": 0.11,
        "Albumin": 4.91,
        "TotalProteins": 8.39,
        "Platelets": 348,
        "Hemoglobin": 11.5,
        # Metabolic
        "FastingGlucose": 76.2,
        "HbA1c": 4.7,
        "TotalCholesterol": 177,
        "HDLCholesterol": 66,
        "LDLCholesterol": 99,
        "Triglycerides": 57,
        # Kidney
        "SerumCreatinine": 0.63,
        "ReportedEGFR": 131,
        # Other
        "TSH": 5.015,
        "VitaminB12": 209,
        "VitaminD": 31.8,
        "Iron": 55.26,
        "TransferrinSaturation": 12.81,
        "MedicalConditions": [],
        "Medications": [],
    }
}

# ──────────────────────────────────────────────────────────────────────────────
# Test Case 2: PARTIAL LABS (albumin/bilirubin extracted but AST/ALT missing)
# This simulates a possible Groq extraction failure
# ──────────────────────────────────────────────────────────────────────────────
partial_labs_no_ast_alt = {
    "ProfileInfo": {
        "Age": 19,
        "Gender": "Female",
        "Height": 152,
        "Weight": 48,
        "Diet": "Poor",
        "ActivityLevel": "Sedentary",
    },
    "HealthInfo": {
        "Smoking": "Never",
        "Alcohol": "Never",
        "Bmi": 20.8,
        # NO AST / ALT
        "GGT": 12.1, "ggt": 12.1,
        "ALP": 55.8, "alp": 55.8,
        "TotalBilirubin": 0.58,
        "DirectBilirubin": 0.11,
        "Albumin": 4.91,
        "Platelets": 348,
        "Hemoglobin": 11.5,
        "FastingGlucose": 76.2,
        "HbA1c": 4.7,
        "TotalCholesterol": 177,
        "Triglycerides": 57,
        "SerumCreatinine": 0.63,
        "ReportedEGFR": 131,
        "MedicalConditions": [],
        "Medications": [],
    }
}

# ──────────────────────────────────────────────────────────────────────────────
# Test Case 3: NO LABS (just profile + lifestyle, no blood test uploaded)
# ──────────────────────────────────────────────────────────────────────────────
no_labs = {
    "ProfileInfo": {
        "Age": 19,
        "Gender": "Female",
        "Height": 152,
        "Weight": 48,
        "Diet": "Poor",
        "ActivityLevel": "Sedentary",
    },
    "HealthInfo": {
        "Smoking": "Never",
        "Alcohol": "Never",
        "Bmi": 20.8,
        "MedicalConditions": [],
        "Medications": [],
    }
}

# ──────────────────────────────────────────────────────────────────────────────
# Test Case 4: Ratio artifact (alt = 2.05 — as if Groq extracted the ratio)
# ──────────────────────────────────────────────────────────────────────────────
ratio_artifact = {
    "ProfileInfo": {
        "Age": 19,
        "Gender": "Female",
        "Height": 152,
        "Weight": 48,
        "Diet": "Poor",
        "ActivityLevel": "Sedentary",
    },
    "HealthInfo": {
        "Smoking": "Never",
        "Alcohol": "Never",
        "Bmi": 20.8,
        "AST": 18.94, "ast": 18.94,
        "ALT": 2.05,  "alt": 2.05,   # <-- BUG: ratio extracted as ALT
        "GGT": 12.1, "ggt": 12.1,
        "ALP": 55.8, "alp": 55.8,
        "TotalBilirubin": 0.58,
        "Albumin": 4.91,
        "Platelets": 348,
        "Hemoglobin": 11.5,
        "FastingGlucose": 76.2,
        "Triglycerides": 57,
        "MedicalConditions": [],
        "Medications": [],
    }
}


def run(label, data, model):
    try:
        r = model.calculate_risk(data)
        score   = r.get("health_score", "?")
        risk    = r.get("risk_score", "?")
        level   = r.get("risk_level", "?")
        method  = r.get("method_used", "?")
        print(f"\n{'='*60}")
        print(f"[{label}]")
        print(f"  Score:  {score}/100  |  Risk: {risk}  |  Level: {level}")
        print(f"  Method: {method}")
        h = data["HealthInfo"]
        ast = h.get("AST") or h.get("ast")
        alt = h.get("ALT") or h.get("alt")
        alb = h.get("Albumin")
        hgb = h.get("Hemoglobin")
        print(f"  Inputs: AST={ast}, ALT={alt}, Albumin={alb}, Hgb={hgb}")
        # Compute labs_clearly_healthy manually
        ast_v = float(ast) if ast else None
        alt_v = float(alt) if alt else None
        alb_v = float(alb) if alb else None
        lch = (ast_v is not None and alt_v is not None and
               ast_v <= 40 and alt_v <= 40 and
               (alb_v is None or alb_v >= 3.5))
        nla = (ast_v is None and alt_v is None and alb_v is None
               and not h.get("GGT") and not h.get("Platelets")
               and not h.get("TotalBilirubin"))
        print(f"  labs_clearly_healthy={lch}  no_labs_at_all={nla}")
    except Exception as e:
        print(f"\n[{label}] ERROR: {e}")
        import traceback; traceback.print_exc()


if __name__ == "__main__":
    import warnings; warnings.filterwarnings("ignore")
    m = LiverModel()

    run("CASE 1: Full labs (correct extraction)", full_labs, m)
    run("CASE 2: Partial labs (no AST/ALT extracted)", partial_labs_no_ast_alt, m)
    run("CASE 3: No labs at all (just profile)", no_labs, m)
    run("CASE 4: Ratio artifact (ALT=2.05 instead of 9.25)", ratio_artifact, m)

    print("\n")
    print("EXPECTED:")
    print("  Case 1 → score ~88-92 (healthy labs, all normal)")
    print("  Case 2 → score ~75-82 (partial labs, normal markers, some uncertainty)")
    print("  Case 3 → score ~75-82 (no labs, poor diet penalty)")
    print("  Case 4 → ??? (possible bug if this matches the 17/100 output)")
