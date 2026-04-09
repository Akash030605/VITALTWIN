# models/kidney_model.py
# Primary (with creatinine): CKD-EPI 2021 eGFR equation (Inker et al., NEJM 2021)
# Secondary (no creatinine): Apollo CKD India ML (400 Tamil Nadu pts, AUC 0.991)
#                             kidney_ml.pkl — Soundarapandian P et al., UCI 2015
# Standard:                  KDIGO 2022 CKD staging

import pickle
from pathlib import Path
from .base_model import BaseOrganModel
from utils.district_priors import get_priors, kidney_prior_adjustment

# ── Load Apollo CKD India ML model ───────────────────────────────────────────
_KIDNEY_ML_PATH = Path(__file__).parent.parent / "models" / "kidney_ml.pkl"
_kidney_ml_bundle = None

def _load_kidney_ml():
    global _kidney_ml_bundle
    if _kidney_ml_bundle is None and _KIDNEY_ML_PATH.exists():
        try:
            with open(_KIDNEY_ML_PATH, "rb") as f:
                _kidney_ml_bundle = pickle.load(f)
            print(f"✅ Loaded kidney ML model (India, AUC {_kidney_ml_bundle.get('cv_auc_mean','?')})")
        except Exception as e:
            print(f"⚠️  Could not load kidney ML: {e}")
    return _kidney_ml_bundle


def ckd_epi_egfr(creatinine, age, gender):
    """
    CKD-EPI Creatinine 2021 Equation
    Inker LA et al., N Engl J Med 2021;385:1737-1749
    Gold standard for eGFR estimation. Validated internationally.

    Returns eGFR in mL/min/1.73m²

    KDIGO CKD Staging:
      G1:  ≥90    Normal or high
      G2:  60-89  Mildly decreased
      G3a: 45-59  Mildly-moderately decreased
      G3b: 30-44  Moderately-severely decreased
      G4:  15-29  Severely decreased
      G5:  <15    Kidney failure
    """
    try:
        scr = float(creatinine)
        age = float(age)
        if gender == "Female":
            kappa      = 0.7
            alpha      = -0.241
            sex_factor = 1.012
        else:
            kappa      = 0.9
            alpha      = -0.302
            sex_factor = 1.0

        ratio = scr / kappa
        egfr  = (142
                 * min(ratio, 1.0) ** alpha
                 * max(ratio, 1.0) ** (-1.200)
                 * 0.9938 ** age
                 * sex_factor)
        return round(egfr, 1)
    except Exception:
        return None


def egfr_to_risk(egfr, uacr=None):
    """
    Convert eGFR to 0-1 risk score using KDIGO staging.
    uacr = urine albumin-creatinine ratio (mg/g) — optional.
    """
    if egfr is None:
        return None
    if egfr >= 90:   base = 0.05
    elif egfr >= 60: base = 0.15
    elif egfr >= 45: base = 0.40
    elif egfr >= 30: base = 0.60
    elif egfr >= 15: base = 0.80
    else:            base = 0.95

    # UACR adds risk: A1 (<30) normal, A2 (30-300) moderately increased, A3 (>300) severely
    if uacr is not None:
        if uacr > 300:   base = min(1.0, base + 0.20)
        elif uacr > 30:  base = min(1.0, base + 0.08)
    return base


class KidneyModel(BaseOrganModel):
    def __init__(self):
        super().__init__("kidney")
        self.load_model()
        # Load Apollo CKD India ML (secondary, for when creatinine not available)
        self._kidney_ml = _load_kidney_ml()

    def calculate_risk(self, data):
        profile = data.get("ProfileInfo", {})
        health  = data.get("HealthInfo",  {})

        age     = int(profile.get("Age", 40))
        gender  = profile.get("Gender", "Male")
        bmi     = float(health.get("Bmi") or profile.get("Bmi") or 25.0)
        diet    = profile.get("Diet", "Average")

        conditions = health.get("MedicalConditions", [])

        # Absolute RED flags
        abs_red = ["dialysis","hemodialysis","peritoneal dialysis",
                   "kidney failure","renal failure","end-stage renal","esrd",
                   "kidney transplant","renal transplant"]
        if any(any(r in c.lower() for r in abs_red) for c in conditions):
            return self._build_result(0.92, age, health, profile,
                                      "absolute_override", None, None)

        # Lab values
        creatinine = health.get("SerumCreatinine")
        glucose    = health.get("FastingGlucose") or health.get("glucose")
        hba1c      = health.get("HbA1c")
        albumin    = health.get("Albumin")
        sbp        = int(health.get("SystolicBP") or health.get("systolic_bp") or 0)
        dbp        = int(health.get("DiastolicBP") or health.get("diastolic_bp") or 0)
        bp_treated = bool(health.get("BPOnMedication", False))
        fam_kidney = bool(health.get("FamilyHistoryKidney", False))

        diabetic   = self._is_diabetic(health)
        htn        = self._is_hypertensive(health, sbp, dbp, conditions)

        method_used = "rule_based"
        base_risk   = None
        egfr_val    = None

        # Strategy 1: CKD-EPI eGFR (gold standard)
        if creatinine:
            egfr_val = ckd_epi_egfr(creatinine, age, gender)
            if egfr_val is not None:
                base_risk   = egfr_to_risk(egfr_val)
                method_used = "ckd_epi_egfr"

        # Strategy 2: Apollo CKD India ML (400 Tamil Nadu pts, AUC 0.991)
        # Soundarapandian P et al., UCI 2015 — India-specific (Tamil Nadu Apollo Hospital)
        if base_risk is None and self._kidney_ml is not None:
            fv = self._extract_features(data, sbp, dbp, glucose, hba1c)
            if fv is not None:
                try:
                    ml_model = self._kidney_ml['model']
                    ml_risk  = float(ml_model.predict_proba([fv])[0][1])
                    base_risk   = round(ml_risk, 3)
                    method_used = "apollo_ckd_india_ml"
                except Exception:
                    pass

        # Strategy 3: Rule-based with actual BP numbers
        if base_risk is None:
            base_risk   = self._rule_based(age, gender, sbp, dbp, bmi,
                                           diabetic, htn, diet, conditions)
            method_used = "rule_based"

        # Diabetes penalty (diabetic nephropathy = #1 cause of CKD)
        dm_penalty = 0.0
        if diabetic:
            if (hba1c and float(hba1c) > 8.0) or (glucose and float(glucose) > 180):
                dm_penalty = 0.20   # Poorly controlled diabetes
            else:
                dm_penalty = 0.10   # Controlled diabetes still elevates risk

        # Chronic NSAID use (nephrotoxic)
        nsaid_penalty = 0.0
        meds = [m.lower() for m in (health.get("Medications") or [])]
        if any(n in m for n in ["nsaid","ibuprofen","naproxen","diclofenac","indomethacin"] for m in meds):
            nsaid_penalty = 0.08

        # Family history
        fam_penalty = 0.06 if fam_kidney else 0.0

        # Low albumin = protein wasting / nephrotic syndrome
        alb_penalty = 0.12 if (albumin and float(albumin) < 3.0) else 0.0

        # NFHS-5 district prior (subtle Bayesian adjustment for regional HTN/DM burden)
        district = health.get("District") or profile.get("District") or ""
        state    = health.get("State")    or profile.get("State")    or ""
        try:
            dist_priors = get_priors(district, state)
            prior_adj   = kidney_prior_adjustment(dist_priors, htn, diabetic)
        except Exception:
            prior_adj   = 0.0
            dist_priors = {}

        final_risk = min(1.0, base_risk + dm_penalty + nsaid_penalty +
                         fam_penalty + alb_penalty + prior_adj)

        return self._build_result(final_risk, age, health, profile,
                                  method_used, egfr_val, creatinine,
                                  prior_adj=prior_adj,
                                  dist_source=dist_priors.get('source','national_average'))

    def _build_result(self, final_risk, age, health, profile, method, egfr, creatinine,
                      prior_adj=0.0, dist_source='national_average'):
        risk_level = self.get_risk_level(final_risk)
        lf = {"diet": profile.get("Diet","Average"), "activity": profile.get("ActivityLevel","Moderate"),
              "sleep": health.get("Sleep",7), "stress": health.get("Stress","Medium")}
        confidence = (0.95 if method == "ckd_epi_egfr" else
                      0.88 if method == "apollo_ckd_india_ml" else  # AUC 0.991, India data
                      0.78 if method == "ml_model" else
                      0.55 if method == "rule_based" else 0.90)
        metrics = {}
        if egfr is not None:
            metrics["egfr"]       = egfr
            metrics["ckd_stage"]  = self._ckd_stage(egfr)
        if creatinine:
            metrics["creatinine"] = float(creatinine)
        sbp = health.get("SystolicBP") or health.get("systolic_bp")
        dbp = health.get("DiastolicBP") or health.get("diastolic_bp")
        if sbp: metrics["systolic_bp"]  = int(sbp)
        if dbp: metrics["diastolic_bp"] = int(dbp)
        if prior_adj:
            metrics["district_prior_adj"] = round(prior_adj, 4)
            metrics["district_source"]    = dist_source

        return {
            "current_risk":     round(final_risk, 3),
            "risk_level":       risk_level,
            "health_score":     self.get_health_score(final_risk),
            "method_used":      method,
            "model_confidence": round(confidence, 2),
            "metrics":          metrics,
            "risk_progression": self.project_risk_progression(final_risk, age, lf),
            "recommendations":  self._get_recommendations(risk_level, health, egfr),
            "possible_issues":  self._possible_issues(health, egfr, creatinine),
        }

    def _ckd_stage(self, egfr):
        if egfr >= 90:   return "G1 — Normal or high"
        elif egfr >= 60: return "G2 — Mildly decreased"
        elif egfr >= 45: return "G3a — Mildly to moderately decreased"
        elif egfr >= 30: return "G3b — Moderately to severely decreased"
        elif egfr >= 15: return "G4 — Severely decreased"
        else:            return "G5 — Kidney failure"

    def _is_diabetic(self, h):
        conds = [c.lower() for c in (h.get("MedicalConditions") or [])]
        g = h.get("FastingGlucose") or h.get("glucose")
        a = h.get("HbA1c")
        return (any("diabetes" in c for c in conds) or
                (g and float(g) >= 126) or (a and float(a) >= 6.5))

    def _is_hypertensive(self, h, sbp, dbp, conditions):
        conds = [c.lower() for c in conditions]
        return (any("hypertension" in c or "high bp" in c for c in conds) or
                sbp >= 140 or dbp >= 90 or bool(h.get("BPOnMedication")))

    def _extract_features(self, data, sbp, dbp, glucose, hba1c):
        """
        Build 24-feature vector matching kidney_features.json training order
        (Apollo Hospital Tamil Nadu CKD ARFF dataset):
        age, bp, sg, al, su, rbc, pc, pcc, ba, bgr, bu, sc,
        sod, pot, hemo, pcv, wbcc, rbcc, htn, dm, cad, appet, pe, ane

        Missing lab values use population medians from the training dataset.
        Model is used only when CKD-EPI creatinine method is unavailable.
        """
        try:
            p     = data.get("ProfileInfo", {})
            h     = data.get("HealthInfo",  {})
            conds = [c.lower() for c in (h.get("MedicalConditions") or [])]
            htn   = sbp >= 140 or dbp >= 90 or bool(h.get("BPOnMedication"))
            dm    = self._is_diabetic(h)
            gluc  = float(glucose) if glucose else (float(hba1c)*28.7 - 46.7 if hba1c else 99.0)
            creat = float(h.get("SerumCreatinine") or 0.9)
            hemo  = float(h.get("Hemoglobin") or 14.0)
            cad   = any("coronary" in c or "cad" in c or "ischaemic heart" in c or
                        "ischemic heart" in c for c in conds)
            edema = any("edema" in c or "oedema" in c or "swelling" in c for c in conds)
            anemia = any("anemia" in c or "anaemia" in c for c in conds)

            return [
                float(p.get("Age", 48)),    # age
                float(dbp or 76),           # bp  (diastolic mmHg — median from dataset)
                1.020,                      # sg  (urine specific gravity — normal default)
                0.0,                        # al  (urine albumin — 0=nil, normal default)
                0.0,                        # su  (urine sugar — 0=nil, normal default)
                1.0,                        # rbc (urine RBC — 1=normal)
                1.0,                        # pc  (pus cells — 1=normal)
                0.0,                        # pcc (pus cell clumps — 0=not present)
                0.0,                        # ba  (bacteria — 0=not present)
                float(gluc),               # bgr (blood glucose random)
                float(h.get("BUN") or 22), # bu  (blood urea mg/dL — normal default)
                float(creat),              # sc  (serum creatinine mg/dL)
                float(h.get("Sodium") or 137),    # sod (sodium mEq/L)
                float(h.get("Potassium") or 4.0), # pot (potassium mEq/L)
                float(hemo),               # hemo (hemoglobin g/dL)
                float(h.get("PCV") or 43), # pcv (packed cell volume %)
                float(h.get("WBC") or 7500),  # wbcc (WBC count cells/cmm)
                float(h.get("RBC") or 4.9),   # rbcc (RBC count millions/cmm)
                1.0 if htn else 0.0,        # htn
                1.0 if dm else 0.0,         # dm
                1.0 if cad else 0.0,        # cad
                1.0,                        # appet (appetite — 1=good, default normal)
                1.0 if edema else 0.0,      # pe (pedal edema)
                1.0 if anemia else 0.0,     # ane (anemia)
            ]
        except Exception:
            return None

    def _rule_based(self, age, gender, sbp, dbp, bmi, diabetic, htn, diet, conditions):
        """Rule-based using ACTUAL blood pressure numbers, not string matching."""
        risk = 0.0
        # BP using real numbers (critical change from old version)
        if sbp >= 160 or dbp >= 100:   risk += 0.30  # Stage 2 HTN
        elif sbp >= 140 or dbp >= 90:  risk += 0.18  # Stage 1 HTN
        elif sbp >= 130 or dbp >= 80:  risk += 0.07  # Elevated
        elif htn:                       risk += 0.12  # Condition only, no BP number

        if diabetic:                    risk += 0.25  # Diabetic nephropathy
        if bmi > 35:                    risk += 0.10
        elif bmi > 30:                  risk += 0.05
        if diet == "Poor":              risk += 0.08

        if age > 70:    risk += 0.18
        elif age > 60:  risk += 0.10
        elif age > 50:  risk += 0.05

        conds = [c.lower() for c in conditions]
        if any("lupus" in c or "sle" in c for c in conds):        risk += 0.20
        if any("polycystic kidney" in c or "pkd" in c for c in conds): risk += 0.30
        if any("glomerulonephritis" in c for c in conds):          risk += 0.25
        if any("kidney stone" in c for c in conds):                risk += 0.08
        if any("recurrent uti" in c for c in conds):               risk += 0.05

        return min(risk, 0.90)

    def _get_recommendations(self, risk_level, health, egfr):
        base = {
            "GREEN":  ["Drink 2-3 litres water daily",
                       "Target BP <130/80 mmHg — most important kidney protector",
                       "Annual creatinine + urine protein test after age 40"],
            "YELLOW": ["Control blood pressure strictly — target <130/80 mmHg",
                       "If diabetic, target HbA1c <7% to protect kidneys",
                       "Avoid NSAIDs (ibuprofen, naproxen) — nephrotoxic",
                       "Request serum creatinine + eGFR test from your doctor"],
            "RED":    ["URGENT: Refer to nephrologist for CKD management",
                       "Strict BP control — target <125/75 mmHg in CKD",
                       "Protein restriction (<0.8g/kg/day) reduces disease progression",
                       "Monitor potassium, bicarbonate, phosphorus levels"],
        }.get(risk_level, [])
        if egfr and egfr < 45:
            base.append(f"eGFR {egfr} mL/min — discuss renal replacement therapy options with nephrologist")
        if health.get("Alcohol") == "Daily":
            base.append("Reduce alcohol — worsens kidney function and hypertension")
        return base[:6]

    def _possible_issues(self, health, egfr, creatinine):
        issues = []
        if egfr is not None:
            if egfr < 60:
                issues.append(f"eGFR {egfr} mL/min/1.73m² — below normal threshold")
        if creatinine and float(creatinine) > 1.3:
            issues.append(f"Elevated creatinine ({creatinine} mg/dL)")
        sbp = health.get("SystolicBP") or health.get("systolic_bp")
        if sbp and int(sbp) >= 140:
            issues.append(f"Hypertension ({sbp} mmHg) — leading cause of CKD progression")
        if self._is_diabetic(health):
            issues.append("Diabetes present — accounts for 44% of new CKD cases")
        alb = health.get("Albumin")
        if alb and float(alb) < 3.5:
            issues.append(f"Low albumin ({alb} g/dL) — possible proteinuria or nephrotic syndrome")
        return issues
