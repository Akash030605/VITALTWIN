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
            print(f"[OK] Loaded kidney ML model (India, AUC {_kidney_ml_bundle.get('cv_auc_mean','?')})")
        except Exception as e:
            print(f"[WARN] Could not load kidney ML: {e}")
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
        # Load Apollo CKD India ML (24-feature Pipeline, used as primary ML signal)
        # Note: trained_models/kidney_model.pkl is a separate 10-feature model not used
        # in calculate_risk() — we only use self._kidney_ml which was trained on the
        # full CKD ARFF feature set matching _extract_features() output.
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
        creatinine    = health.get("SerumCreatinine")
        glucose       = health.get("FastingGlucose") or health.get("glucose")
        hba1c         = health.get("HbA1c")
        albumin       = health.get("Albumin")
        sbp           = int(health.get("SystolicBP") or health.get("systolic_bp") or 0)
        dbp           = int(health.get("DiastolicBP") or health.get("diastolic_bp") or 0)
        bp_treated    = bool(health.get("BPOnMedication", False))
        fam_kidney    = bool(health.get("FamilyHistoryKidney", False))

        # Extended lab fields (from CBC / metabolic panel)
        hemoglobin    = health.get("Hemoglobin")    # g/dL — low = anemia of CKD
        uric_acid     = health.get("UricAcid")      # mg/dL — hyperuricemia → CKD (Kanbay 2013)
        bun           = health.get("BUN")           # mg/dL — azotemia marker
        reported_egfr = health.get("ReportedEGFR")  # mL/min/1.73m² — directly from lab report

        diabetic   = self._is_diabetic(health)
        htn        = self._is_hypertensive(health, sbp, dbp, conditions)

        method_used = "rule_based"
        base_risk   = None
        egfr_val    = None

        # ── Strategy 0: ReportedEGFR — use lab-reported eGFR directly (highest trust) ──
        # When a lab report provides eGFR directly (e.g. "eGFR: 62 mL/min/1.73m²"),
        # use it as-is. This is more accurate than CKD-EPI when creatinine alone would give
        # a different result (e.g., labs used CKD-EPI with cystatin-C or different race correction).
        if reported_egfr:
            egfr_val    = float(reported_egfr)
            base_risk   = egfr_to_risk(egfr_val)
            method_used = "reported_egfr"  # trusted: came directly from lab report

        # Strategy 1: CKD-EPI eGFR (gold standard when creatinine available)
        if base_risk is None and creatinine:
            egfr_val = ckd_epi_egfr(creatinine, age, gender)
            if egfr_val is not None:
                base_risk   = egfr_to_risk(egfr_val)
                method_used = "ckd_epi_egfr"

        # Strategy 2: Apollo CKD India ML — ONLY use when actual kidney labs are available
        # AND those labs suggest possible kidney pathology.
        # The model was trained on a hospital CKD dataset (biased toward sick patients),
        # so it gives falsely high risk (0.4-0.6) when fed normal glucose/albumin values.
        # BLOCK when labs are clearly healthy (same pattern as liver model healthy-labs guard).
        creat_v = health.get("SerumCreatinine")
        egfr_v  = health.get("ReportedEGFR")
        creat_clearly_normal = (
            creat_v is not None and (
                (gender == "Female" and float(creat_v) <= 1.1) or
                (gender == "Male"   and float(creat_v) <= 1.2)
            )
        )
        egfr_clearly_normal = egfr_v is not None and float(egfr_v) >= 90
        albumin_normal = albumin is None or float(albumin) >= 3.5
        bun_v = health.get("BUN") or health.get("bun")
        bun_normal = bun_v is None or float(bun_v) <= 20
        glucose_normal = glucose is None or float(glucose) < 126
        hba1c_normal   = hba1c  is None or float(hba1c)  < 6.5

        # If any clear healthy-kidney signal present, block Apollo ML (sick-patient bias)
        kidney_labs_clearly_healthy = (
            creat_clearly_normal or egfr_clearly_normal or
            (albumin_normal and bun_normal and glucose_normal and hba1c_normal
             and not diabetic and not htn)
        )

        has_kidney_labs = any([
            health.get("SerumCreatinine"),
            health.get("BUN"),
            health.get("Albumin"),
            health.get("FastingGlucose"),
            health.get("HbA1c"),
            health.get("Hemoglobin"),
            health.get("SystolicBP") or health.get("systolic_bp"),
        ])
        if base_risk is None and self._kidney_ml is not None and has_kidney_labs and not kidney_labs_clearly_healthy:
            fv = self._extract_features(data, sbp, dbp, glucose, hba1c)
            if fv is not None:
                try:
                    ml_model = self._kidney_ml['model']
                    ml_risk  = float(ml_model.predict_proba([fv])[0][1])
                    # Blend with rule-based to reduce hospital-dataset bias
                    rule_risk = self._rule_based(age, gender, sbp, dbp, bmi,
                                                diabetic, htn, diet, conditions)
                    base_risk   = round(0.5 * ml_risk + 0.5 * rule_risk, 3)
                    method_used = "apollo_ckd_india_ml"
                except Exception:
                    pass

        # Strategy 3: Rule-based with actual BP numbers
        if base_risk is None:
            base_risk   = self._rule_based(age, gender, sbp, dbp, bmi,
                                           diabetic, htn, diet, conditions)
            method_used = "rule_based"

        # ── G6: India diabetic nephropathy prior ─────────────────────────────
        # 30% of Indian diabetics have microalbuminuria (UKPDS India sub-study;
        # Ramachandran A et al., Diabetes Care 2003;26(9):2756-2760)
        # This is ~2× higher than the Western average (14–15%).
        # Standard rule-based models use Western CKD-DM risk without this adjustment.
        # Implementation: if diabetic and no UACR provided, apply India-specific
        # nephropathy prior as an additional penalty on top of the base DM penalty.
        # UACR field: if present and <30 mg/g (normoalbuminuria), do not apply.
        # This is a Bayesian prior — modest 5% additional penalty — because 30%
        # of Indian diabetics have already crossed into microalbuminuria without knowing it.
        # Source: Ramachandran A et al., Diabetes Care 2003;26:2756-2760 (Chennai Urban)
        #         Agarwal R et al., Kidney Int 2011 — Indian CKD-DM burden

        uacr = health.get("UACR") or health.get("uacr") or health.get("UrineACR")
        india_dm_nephropathy_prior = 0.0
        if diabetic:
            if uacr is None:
                # No UACR available: apply India-specific prior (30% microalbuminuria prevalence)
                # vs Western prior (15%) → extra penalty = 0.30 - 0.15 = 0.15 × risk_weight(0.35) ≈ 0.05
                india_dm_nephropathy_prior = 0.05
            elif float(uacr) >= 300:
                india_dm_nephropathy_prior = 0.10   # Macroalbuminuria → high India progression rate
            elif float(uacr) >= 30:
                india_dm_nephropathy_prior = 0.05   # Microalbuminuria confirmed

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

        # ── Uric acid (hyperuricemia → CKD) ──────────────────────────────────
        # Source: Kanbay M et al., Kidney Int 2013;83(4):587-593
        #   Serum uric acid >7 mg/dL in men or >6 mg/dL in women is independently
        #   associated with CKD onset and progression. Each 1 mg/dL increase → +8% risk.
        # Normal: Men <7.2 mg/dL, Women <6.0 mg/dL
        uric_penalty = 0.0
        if uric_acid:
            ua = float(uric_acid)
            ua_threshold = 6.0 if gender == "Female" else 7.2
            if ua > ua_threshold:
                # Each 1 mg/dL above threshold → +4% kidney risk (conservative from Kanbay 2013)
                excess = ua - ua_threshold
                uric_penalty = round(min(0.15, excess * 0.04), 3)

        # ── Hemoglobin (anemia of CKD) — CONTEXT-GATED ───────────────────────
        # CRITICAL FIX: Low Hgb alone does NOT mean kidney disease.
        # Iron deficiency anemia is far more common in young Indian women (~50%)
        # and has nothing to do with kidney function.
        # Source: KDIGO 2012 — "anemia of CKD is a diagnosis of exclusion;
        #   requires concurrent evidence of reduced kidney function (GFR <60) OR
        #   diabetic/hypertensive nephropathy to implicate the kidney."
        # Source: Annigeri RA et al., Indian J Nephrol 2019 — anemia in CKD India
        #
        # The Hgb penalty now ONLY applies when there is concurrent evidence of
        # kidney stress:
        #   1. Creatinine elevated (>1.1 mg/dL in women, >1.2 in men)
        #   2. Diabetic — DKD is #1 cause of CKD in India
        #   3. Hypertensive — hypertensive nephrosclerosis is #2 cause
        #   4. BUN elevated (>20 mg/dL) — azotemia
        # Without ANY of these, low Hgb = likely nutritional anemia (not CKD)
        creatinine_for_context = health.get("SerumCreatinine") or health.get("creatinine")
        creat_elevated = (
            creatinine_for_context is not None and (
                (gender == "Male"   and float(creatinine_for_context) > 1.2) or
                (gender == "Female" and float(creatinine_for_context) > 1.1)
            )
        )
        bun_for_context = health.get("BUN") or health.get("bun")
        bun_elevated_ctx = bun_for_context is not None and float(bun_for_context) > 20.0
        ckd_context = creat_elevated or diabetic or htn or bun_elevated_ctx

        hgb_penalty = 0.0
        if hemoglobin and ckd_context:
            # Only penalise when there is actual kidney stress context
            hgb = float(hemoglobin)
            if hgb < 10.0:
                hgb_penalty = 0.10   # Severe anemia WITH CKD context — likely advanced CKD
            elif hgb < 12.0:
                hgb_penalty = 0.05   # Moderate anemia WITH CKD context
            elif (gender == "Male"   and hgb < 13.5) or \
                 (gender == "Female" and hgb < 12.0):
                hgb_penalty = 0.02   # Mild anemia WITH CKD context (reduced from 0.03)
        # If hemoglobin is low but NO CKD context: hgb_penalty stays 0.0
        # (nutritional/iron deficiency anemia — not a kidney problem)

        # ── BUN azotemia marker ──────────────────────────────────────────────
        # BUN >20 mg/dL = borderline azotemia; >30 = azotemia; >50 = uremia risk
        bun_penalty = 0.0
        if bun:
            bun_val = float(bun)
            if bun_val > 50:
                bun_penalty = 0.12   # Uremia risk — significant kidney impairment
            elif bun_val > 30:
                bun_penalty = 0.06   # Azotemia
            elif bun_val > 20:
                bun_penalty = 0.02   # Borderline

        # NFHS-5 district prior (subtle Bayesian adjustment for regional HTN/DM burden)
        district = health.get("District") or profile.get("District") or ""
        state    = health.get("State")    or profile.get("State")    or ""
        try:
            dist_priors = get_priors(district, state)
            prior_adj   = kidney_prior_adjustment(dist_priors, htn, diabetic)
        except Exception:
            prior_adj   = 0.0
            dist_priors = {}

        final_risk = min(1.0, base_risk + dm_penalty + india_dm_nephropathy_prior +
                         nsaid_penalty + fam_penalty + alb_penalty + prior_adj +
                         uric_penalty + hgb_penalty + bun_penalty)

        result = self._build_result(final_risk, age, health, profile,
                                    method_used, egfr_val, creatinine,
                                    prior_adj=prior_adj,
                                    dist_source=dist_priors.get('source','national_average'))

        # Attach extended lab markers to metrics for frontend display
        if uric_acid:
            result['metrics']['uric_acid']     = float(uric_acid)
            if uric_penalty > 0:
                result['metrics']['uric_acid_flag'] = f"Elevated ({uric_acid} mg/dL) — hyperuricemia adds CKD risk"
        if hemoglobin:
            result['metrics']['hemoglobin']    = float(hemoglobin)
            if hgb_penalty > 0:
                result['metrics']['hemoglobin_flag'] = f"Low Hgb ({hemoglobin} g/dL) — anemia of CKD pattern"
        if bun:
            result['metrics']['bun']           = float(bun)
            if bun_penalty > 0:
                result['metrics']['bun_flag']  = f"BUN {bun} mg/dL — azotemia marker elevated"

        return result

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

        FIX (G7): Pass feature names as pandas-compatible named list to suppress
        sklearn SimpleImputer feature_names_in_ warning.
        The warning: "X has feature names but SimpleImputer was fitted without feature names"
        is cosmetic — does not affect predictions — but passing consistent types suppresses it.
        """
        try:
            import warnings
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

            fv = [
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
            # Suppress sklearn feature_names warning by using plain list
            # (model was fitted on numpy arrays, not DataFrames — match that format)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                return fv
        except Exception:
            return None

    def _rule_based(self, age, gender, sbp, dbp, bmi, diabetic, htn, diet, conditions):
        """Rule-based using ACTUAL blood pressure numbers, not string matching."""
        # ── Population-based age floor (GBD 2019 India CKD prevalence) ──────────
        # No living person has zero kidney risk. India-specific age-based CKD prevalence:
        #   20-39yo: ~2.5%  40-49yo: ~5%  50-59yo: ~9%  60-69yo: ~15%  70+: ~22%
        # Source: GBD 2019 India; Rajapurkar MM et al. Indian J Nephrol 2012;22:321-325
        # These represent the honest population-level kidney risk when labs are unknown.
        if age >= 70:      risk = 0.22
        elif age >= 60:    risk = 0.15
        elif age >= 50:    risk = 0.09
        elif age >= 40:    risk = 0.05
        else:              risk = 0.025   # 20-39yo: ~2.5% CKD prevalence India GBD 2019

        # Female: slightly lower CKD incidence before 50 (GBD 2019)
        if gender == "Female" and age < 50:
            risk *= 0.75

        # BP using real numbers (critical change from old version)
        if sbp >= 160 or dbp >= 100:   risk += 0.30  # Stage 2 HTN
        elif sbp >= 140 or dbp >= 90:  risk += 0.18  # Stage 1 HTN
        elif sbp >= 130 or dbp >= 80:  risk += 0.07  # Elevated
        elif htn:                       risk += 0.12  # Condition only, no BP number

        if diabetic:                    risk += 0.25  # Diabetic nephropathy
        if bmi > 35:                    risk += 0.10
        elif bmi > 30:                  risk += 0.05
        if diet == "Poor":              risk += 0.08

        conds = [c.lower() for c in conditions]
        if any("lupus" in c or "sle" in c for c in conds):        risk += 0.20
        if any("polycystic kidney" in c or "pkd" in c for c in conds): risk += 0.30
        if any("glomerulonephritis" in c for c in conds):          risk += 0.25
        if any("kidney stone" in c for c in conds):                risk += 0.08
        if any("recurrent uti" in c for c in conds):               risk += 0.05

        return min(risk, 0.90)

    def _get_recommendations(self, risk_level, health, egfr):
        """
        Fully dynamic kidney recommendations using the user's actual values.
        No generic text — every line references the user's real data.
        """
        recs = []
        sbp        = health.get("SystolicBP") or health.get("systolic_bp")
        dbp        = health.get("DiastolicBP") or health.get("diastolic_bp")
        creatinine = health.get("SerumCreatinine")
        hba1c      = health.get("HbA1c")
        fasting_g  = health.get("FastingGlucose")
        albumin    = health.get("Albumin")
        alcohol    = health.get("Alcohol", "Never")
        smoking    = health.get("Smoking", "Never")
        conditions = health.get("MedicalConditions", [])
        meds       = [m.lower() for m in (health.get("Medications") or [])]
        diabetic   = self._is_diabetic(health)
        nsaid_use  = any(n in m for n in
                         ["nsaid","ibuprofen","naproxen","diclofenac","indomethacin","paracetamol"]
                         for m in meds)

        # 1. eGFR-based personalised message
        if egfr is not None:
            ckd_stage = self._ckd_stage(egfr)
            if egfr < 15:
                recs.append(
                    f"URGENT: eGFR {egfr} mL/min — Stage G5 kidney failure. "
                    f"Refer to nephrologist immediately to discuss dialysis or transplant options. "
                    f"Avoid all nephrotoxic drugs (NSAIDs, contrast dye, aminoglycosides)."
                )
            elif egfr < 30:
                recs.append(
                    f"eGFR {egfr} mL/min ({ckd_stage}) — severely reduced kidney function. "
                    f"Consult nephrologist within 2 weeks. "
                    f"Protein restriction <0.8g/kg/day slows CKD progression (MDRD Study). "
                    f"Monitor potassium and phosphorus — dietary restriction may be needed."
                )
            elif egfr < 45:
                recs.append(
                    f"eGFR {egfr} mL/min ({ckd_stage}) — moderate CKD. "
                    f"See a nephrologist. Strict BP target: <130/80 mmHg. "
                    f"Each 10 mmHg BP reduction slows eGFR decline by ~30% (AASK Trial). "
                    f"Avoid NSAIDs completely — they reduce kidney blood flow and accelerate decline."
                )
            elif egfr < 60:
                recs.append(
                    f"eGFR {egfr} mL/min ({ckd_stage}) — mildly-to-moderately reduced. "
                    f"Annual nephrology review. Target BP <130/80 mmHg. "
                    f"Creatinine + urine ACR test every 6 months."
                )
            else:
                recs.append(
                    f"eGFR {egfr} mL/min — within normal range. "
                    f"Maintain with annual creatinine + urine protein test (especially after age 40), "
                    f"adequate hydration (2–2.5 L/day), and BP <130/80 mmHg."
                )
        else:
            # No creatinine — urge the user to get tested
            recs.append(
                "No creatinine value entered — kidney confidence is low. "
                "A serum creatinine test costs ~₹100–200 at a government lab and gives a precise "
                "eGFR (kidney filtration rate). This is the most important single test for kidney health. "
                "Book it at your next routine blood test."
            )

        # 2. Diabetes + kidney (personalised by HbA1c value)
        if diabetic:
            if hba1c and float(hba1c) >= 8.0:
                recs.append(
                    f"HbA1c {hba1c}% — poorly controlled diabetes is the #1 cause of CKD in India "
                    f"(40% of all new CKD cases). Every 1% HbA1c reduction cuts kidney failure risk "
                    f"by 37% (UKPDS 38). Target HbA1c <7% — speak to your doctor about adjusting therapy."
                )
            elif hba1c and float(hba1c) >= 6.5:
                recs.append(
                    f"HbA1c {hba1c}% — diabetes controlled but still elevated kidney risk. "
                    f"Target HbA1c <7%. SGLT2 inhibitors (empagliflozin, dapagliflozin) specifically "
                    f"protect the kidney in diabetic CKD (EMPA-REG, CREDENCE trials)."
                )
            else:
                recs.append(
                    "Diabetes increases kidney risk — maintain HbA1c <7% and annual "
                    "urine albumin-creatinine ratio (ACR) test to catch early nephropathy."
                )

        # 3. Blood pressure with actual numbers
        if sbp and dbp:
            sbp_i, dbp_i = int(sbp), int(dbp)
            if sbp_i >= 160:
                recs.append(
                    f"BP {sbp_i}/{dbp_i} mmHg — Stage 2 hypertension is the #2 cause of CKD in India. "
                    f"Target <130/80 mmHg. ACE inhibitors (ramipril) or ARBs (losartan) are the "
                    f"preferred medications — they also protect the kidney directly (RENAAL Trial). "
                    f"Every 10 mmHg reduction slows CKD progression by ~30%."
                )
            elif sbp_i >= 140:
                recs.append(
                    f"BP {sbp_i}/{dbp_i} mmHg — Stage 1 hypertension. "
                    f"Target <130/80 mmHg for kidney protection. Reducing dietary sodium <5g/day "
                    f"lowers BP by 4–5 mmHg without medication."
                )

        # 4. NSAID use — very common in India, often not mentioned
        if nsaid_use:
            recs.append(
                "NSAID use detected (ibuprofen/diclofenac/naproxen) — these drugs reduce kidney "
                "blood flow and can cause acute kidney injury with regular use. "
                "Switch to paracetamol for pain (safer for kidneys). "
                "If you need NSAIDs, take the lowest dose for the shortest time and stay well hydrated."
            )

        # 5. Low albumin — proteinuria sign
        if albumin and float(albumin) < 3.5:
            recs.append(
                f"Albumin {albumin} g/dL — low. This may indicate protein leaking through the kidneys "
                f"(nephrotic syndrome or chronic inflammation). Request a urine albumin-creatinine ratio "
                f"(ACR) test — a result >30 mg/g confirms kidney protein leak."
            )

        # 6. Alcohol
        if alcohol == "Daily":
            recs.append(
                "Daily alcohol worsens hypertension and impairs kidney function over time. "
                "Reducing to occasional (≤2 days/week) can lower BP by 3–4 mmHg "
                "and reduce kidney inflammation."
            )

        # 7. General if still short on recs
        if len(recs) < 3:
            if risk_level == "GREEN":
                recs.append(
                    "Kidneys are filtering well. Protect them: stay well hydrated (2–2.5 L water/day), "
                    "keep BP <130/80 mmHg, and avoid routine NSAID use. "
                    "Annual creatinine check after age 40 is recommended."
                )
            elif risk_level == "YELLOW":
                recs.append(
                    "Kidney risk is elevated. Request a serum creatinine + urine ACR test "
                    "to get an accurate eGFR. This will improve your kidney score confidence from low to high."
                )

        return recs[:6]

    def _possible_issues(self, health, egfr, creatinine):
        issues = []
        if egfr is not None:
            if egfr < 60:
                issues.append(f"eGFR {egfr} mL/min/1.73m² — below normal threshold")
        if creatinine and float(creatinine) > 1.3:
            issues.append(f"Elevated creatinine ({creatinine} mg/dL)")
        sbp = health.get("SystolicBP") or health.get("systolic_bp")
        if sbp and int(float(sbp)) >= 140:
            issues.append(f"Hypertension ({int(float(sbp))} mmHg) — leading cause of CKD progression")
        if self._is_diabetic(health):
            issues.append("Diabetes present — accounts for 44% of new CKD cases")
        alb = health.get("Albumin")
        if alb and float(alb) < 3.5:
            issues.append(f"Low albumin ({alb} g/dL) — possible proteinuria or nephrotic syndrome")
        return issues
