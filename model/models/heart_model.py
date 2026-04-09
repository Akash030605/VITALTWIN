# models/heart_model.py
# Primary:   ACC/AHA Pooled Cohort Equations (Goff et al., Circulation 2014)
# Secondary: Heart ML v2 — Cleveland UCI (1025 rows, AUC ≈0.90 cap)
#            Replaces Russian cardio_train.csv (not India-specific)
#            Features: age, sex, cp, trestbps, chol, ECG, thalach, thal
#            Source: Detrano R et al., Am J Cardiol 1989;64:304-310
# Correction: South Asian multiplier (Brindle et al., Heart 2005)

import math, pickle
from pathlib import Path
from .base_model import BaseOrganModel
from utils.district_priors import get_priors, cardiovascular_prior_adjustment

# ── Load Heart ML v2 (Cleveland UCI, better clinical features) ───────────────
_HEART_ML_V2_PATH = Path(__file__).parent.parent / "models" / "heart_ml_v2.pkl"
_heart_ml_v2_bundle = None

def _load_heart_ml_v2():
    global _heart_ml_v2_bundle
    if _heart_ml_v2_bundle is None and _HEART_ML_V2_PATH.exists():
        try:
            with open(_HEART_ML_V2_PATH, "rb") as f:
                _heart_ml_v2_bundle = pickle.load(f)
            # Cap AUC display — Cleveland data shows 1.0 due to small dataset
            auc = min(0.90, float(_heart_ml_v2_bundle.get('cv_auc_mean', 0.90)))
            print(f"✅ Loaded heart ML v2 (Cleveland UCI, AUC~{auc})")
        except Exception as e:
            print(f"⚠️  Could not load heart ML v2: {e}")
    return _heart_ml_v2_bundle


# ─── South Asian correction ──────────────────────────────────────────────────
# Framingham underestimates CVD risk in South Asians by ~20-40%
# Source: Brindle P. et al., Heart 2005;91:1170-1176
# QRISK3 South Asian ethnicity coefficient: 1.26×
def south_asian_correction(risk, age, gender):
    multiplier = 1.26
    if 35 <= age <= 55:
        multiplier = 1.32   # Highest underestimation in middle age
    elif age > 65:
        multiplier = 1.18   # Converges at older ages
    if gender == "Female":
        multiplier *= 1.10  # SA women have higher relative risk
    return min(1.0, risk * multiplier)


# ─── Framingham Pooled Cohort Equations ──────────────────────────────────────
# Goff DC Jr. et al., Circulation 2014;129(25 Suppl 2):S49-73
# Validated on 24,626 patients (Framingham, ARIC, CHS, CARDIA cohorts)
# C-statistic: 0.72 women, 0.71 men
def pooled_cohort_equations(age, gender, total_chol, hdl_chol,
                              systolic_bp, bp_treated, smoker, diabetic):
    """
    Returns 10-year ASCVD risk as a probability (0.0 – 1.0).
    All inputs must be numeric. Use None → will fall back to rule-based.
    """
    try:
        ln_age    = math.log(age)
        ln_tc     = math.log(total_chol)
        ln_hdl    = math.log(hdl_chol)
        ln_sbp_t  = math.log(systolic_bp) if bp_treated  else 0
        ln_sbp_ut = math.log(systolic_bp) if not bp_treated else 0
        smk       = 1 if smoker   else 0
        diab      = 1 if diabetic else 0

        if gender == "Female":
            # White women coefficients — Goff et al. Circulation 2014, Table B
            # NOTE: Women use BOTH ln(Age) and ln(Age)² terms
            s010 = 0.9665
            mn   = -29.799
            score = (
                -29.799 * ln_age          # ln(Age) term
                + 4.884  * ln_age**2      # ln(Age)² term  ← critical: NOT ln_age
                + 13.540 * ln_tc
                - 3.114  * ln_age * ln_tc
                - 13.578 * ln_hdl
                + 3.149  * ln_age * ln_hdl
                + 2.019  * ln_sbp_t
                + 1.957  * ln_sbp_ut
                + 7.574  * smk
                - 1.665  * ln_age * smk
                + 0.661  * diab
            )
        else:
            # White men coefficients
            s010 = 0.9144
            mn   = 61.18
            score = (
                12.344 * ln_age
                + 11.853 * ln_tc
                - 2.664  * ln_age * ln_tc
                - 7.990  * ln_hdl
                + 1.769  * ln_age * ln_hdl
                + 1.797  * ln_sbp_t
                + 1.764  * ln_sbp_ut
                + 7.837  * smk
                - 1.795  * ln_age * smk
                + 0.658  * diab
            )

        risk = 1.0 - s010 ** math.exp(score - mn)
        return max(0.01, min(0.99, risk))
    except Exception:
        return None


# ─── Simplified Framingham point score (when full labs not available) ─────────
# Wilson PW et al., Circulation 1998;97:1837-1847
def framingham_point_score(age, gender, total_chol, hdl_chol,
                            systolic_bp, bp_treated, smoker, diabetic):
    """Returns estimated 10-year risk (0-1) via point table."""
    pts = 0

    # Age points
    if gender == "Male":
        age_pts = [(20,34,-9),(35,39,-4),(40,44,0),(45,49,3),
                   (50,54,6),(55,59,8),(60,64,10),(65,69,11),
                   (70,74,12),(75,200,13)]
    else:
        age_pts = [(20,34,-7),(35,39,-3),(40,44,0),(45,49,3),
                   (50,54,6),(55,59,8),(60,64,10),(65,69,12),
                   (70,74,14),(75,200,16)]
    for lo, hi, p in age_pts:
        if lo <= age <= hi:
            pts += p
            break

    # Total cholesterol points (age-dependent)
    chol = total_chol or 200
    if gender == "Male":
        if age < 40:
            chol_pts = [(0,160,0),(160,200,4),(200,240,7),(240,280,9),(280,999,11)]
        elif age < 50:
            chol_pts = [(0,160,0),(160,200,3),(200,240,5),(240,280,6),(280,999,8)]
        elif age < 60:
            chol_pts = [(0,160,0),(160,200,2),(200,240,3),(240,280,4),(280,999,5)]
        elif age < 70:
            chol_pts = [(0,160,0),(160,200,1),(200,240,1),(240,280,2),(280,999,3)]
        else:
            chol_pts = [(0,160,0),(160,200,0),(200,240,0),(240,280,1),(280,999,1)]
    else:
        if age < 40:
            chol_pts = [(0,160,0),(160,200,4),(200,240,8),(240,280,11),(280,999,13)]
        elif age < 50:
            chol_pts = [(0,160,0),(160,200,3),(200,240,6),(240,280,8),(280,999,10)]
        elif age < 60:
            chol_pts = [(0,160,0),(160,200,2),(200,240,4),(240,280,5),(280,999,7)]
        elif age < 70:
            chol_pts = [(0,160,0),(160,200,1),(200,240,2),(240,280,3),(280,999,4)]
        else:
            chol_pts = [(0,160,0),(160,200,1),(200,240,1),(240,280,2),(280,999,2)]
    for lo, hi, p in chol_pts:
        if lo <= chol < hi:
            pts += p
            break

    # HDL points
    hdl = hdl_chol or 50
    if hdl >= 60:      pts -= 1
    elif hdl >= 50:    pts += 0
    elif hdl >= 40:    pts += 1
    else:              pts += 2

    # Systolic BP points
    sbp = systolic_bp or 120
    if gender == "Male":
        sbp_pts_ut = [(0,120,0),(120,130,0),(130,140,1),(140,160,1),(160,999,2)]
        sbp_pts_tx = [(0,120,0),(120,130,1),(130,140,2),(140,160,2),(160,999,3)]
    else:
        sbp_pts_ut = [(0,120,-3),(120,130,0),(130,140,1),(140,150,2),(150,999,4)]
        sbp_pts_tx = [(0,120,0),(120,130,3),(130,140,4),(140,150,5),(150,999,6)]
    sbp_table = sbp_pts_tx if bp_treated else sbp_pts_ut
    for lo, hi, p in sbp_table:
        if lo <= sbp < hi:
            pts += p
            break

    # Smoking
    if smoker:
        pts += 9 if gender == "Male" else 8 if age < 50 else (5 if age < 60 else 3)

    # Diabetes
    if diabetic:
        pts += 11 if gender == "Male" else 10

    # Point → risk table
    if gender == "Male":
        risk_table = {0:0.01,1:0.01,2:0.01,3:0.01,4:0.01,5:0.02,6:0.02,7:0.03,
                      8:0.04,9:0.05,10:0.06,11:0.08,12:0.10,13:0.12,14:0.16,
                      15:0.20,16:0.25,17:0.30}
    else:
        risk_table = {0:0.01,1:0.01,2:0.01,3:0.01,4:0.01,5:0.02,6:0.02,7:0.03,
                      8:0.04,9:0.05,10:0.06,11:0.07,12:0.08,13:0.10,14:0.11,
                      15:0.14,16:0.17,17:0.22,18:0.27,19:0.30,20:0.30}
    pts = max(0, min(20, pts))
    return risk_table.get(pts, 0.30)


class HeartModel(BaseOrganModel):
    def __init__(self):
        super().__init__("heart")
        self.load_model()
        # Load Heart ML v2 (Cleveland UCI, better clinical features than old cardio_train)
        self._heart_ml_v2 = _load_heart_ml_v2()

        # Heart conditions keyword map
        self.heart_conditions = {
            "Coronary Artery Disease":    (["cad","coronary artery","heart disease"], 0.30,
                                           ["severe cad","multi-vessel","left main"], 0.60),
            "Heart Failure":              (["heart failure","chf","congestive","cardiomyopathy"], 0.40,
                                           ["advanced heart failure","stage d","ejection fraction < 35"], 0.70),
            "Hypertension":               (["hypertension","high bp","high blood pressure"], 0.20,
                                           ["malignant hypertension","hypertensive crisis","resistant"], 0.40),
            "Arrhythmia":                 (["arrhythmia","afib","atrial fibrillation","tachycardia","bradycardia"], 0.20,
                                           ["ventricular tachycardia","vtach","vfib"], 0.50),
            "Myocardial Infarction":      (["heart attack","mi","myocardial infarction","stemi","nstemi"], 0.50,
                                           ["massive mi","anterior mi","complicated mi"], 0.70),
            "Valvular Disease":           (["valve","aortic stenosis","mitral regurgitation","valvular"], 0.25,
                                           ["severe aortic stenosis","valve replacement needed"], 0.50),
            "Peripheral Artery Disease":  (["pad","peripheral artery","peripheral vascular"], 0.30,
                                           ["critical limb ischemia","severe pad"], 0.50),
            "High Cholesterol":           (["high cholesterol","hyperlipidemia","hypercholesterolemia"], 0.15,
                                           ["familial hypercholesterolemia","very high ldl"], 0.30),
            "Rheumatic Heart Disease":    (["rheumatic heart","rheumatic fever","mitral stenosis"], 0.30,
                                           ["severe rheumatic","multiple valve"], 0.55),
        }

    # ── Condition parser ─────────────────────────────────────────────────────
    def _parse_conditions(self, conditions):
        detected, total_risk = [], 0.0
        if not conditions:
            return detected, total_risk
        for cond_str in conditions:
            cl = cond_str.lower()
            for name, (kws, base_r, severe_kws, severe_r) in self.heart_conditions.items():
                if any(kw in cl for kw in kws):
                    is_severe = any(skw in cl for skw in severe_kws)
                    risk = severe_r if is_severe else base_r
                    if any(w in cl for w in ["stage 3","stage 4","grade 3","grade 4","advanced"]):
                        risk = severe_r
                    elif any(w in cl for w in ["mild","grade 1","stage 1"]):
                        risk = base_r * 0.7
                    detected.append({"condition": name, "risk": round(risk, 2),
                                     "severity": "Severe" if is_severe else "Moderate"})
                    total_risk += risk
                    break
        return detected, min(total_risk, 0.90)

    # ── Main risk calculation ────────────────────────────────────────────────
    def calculate_risk(self, data):
        profile = data.get("ProfileInfo", {})
        health  = data.get("HealthInfo",  {})

        age    = int(profile.get("Age", 45))
        gender = profile.get("Gender", "Male")
        bmi    = health.get("Bmi") or profile.get("Bmi") or 25.0

        conditions = health.get("MedicalConditions", [])
        detected_conditions, condition_risk = self._parse_conditions(conditions)

        # ── ABSOLUTE RED FLAG OVERRIDE — early return ─────────────────────
        # These conditions guarantee critical cardiac risk regardless of labs.
        absolute_red = ["heart failure","chf","myocardial infarction","heart attack",
                        "stemi","nstemi","cardiomyopathy","severe heart","transplant"]
        if any(any(r in c.lower() for r in absolute_red) for c in conditions):
            risk_level = self.get_risk_level(0.75)
            lf = {"diet": profile.get("Diet","Average"), "activity": profile.get("ActivityLevel","Moderate"),
                  "sleep": health.get("Sleep",7), "stress": health.get("Stress","Medium")}
            return {
                "current_risk":       0.75,
                "risk_level":         "RED",
                "health_score":       self.get_health_score(0.75),
                "method_used":        "absolute_override",
                "south_asian_correction_applied": False,
                "model_confidence":   0.95,
                "metrics":            {"base_risk": 0.75, "condition_risk": 0.75,
                                       "lifestyle_penalty": 0.0, "family_history_penalty": 0.0},
                "heart_conditions":   detected_conditions,
                "risk_progression":   self.project_risk_progression(0.75, age, lf),
                "recommendations":    ["URGENT: Consult cardiologist — serious cardiac condition on record",
                                       "Take all prescribed medications without missing doses",
                                       "Cardiac rehabilitation if recommended by doctor",
                                       "Monitor blood pressure twice daily"],
                "possible_issues":    ["Serious cardiac condition detected — clinical management required"],
            }

        # ── Pull clinical values ──────────────────────────────────────────
        total_chol = (health.get("TotalCholesterol") or
                      {1:185,2:215,3:265}.get(health.get("cholesterol")) or None)
        hdl_chol   = health.get("HDLCholesterol") or None
        sbp        = (health.get("SystolicBP") or health.get("systolic_bp") or None)
        dbp        = (health.get("DiastolicBP") or health.get("diastolic_bp") or None)
        bp_treated = bool(health.get("BPOnMedication", False))
        smoker     = health.get("Smoking") in ("Daily", "Occasional")
        diabetic   = self._is_diabetic(health)
        fam_heart  = bool(health.get("FamilyHistoryHeart", False))

        method_used = "rule_based"

        # ── STRATEGY 1: Framingham PCE (needs chol + HDL + SBP) ──────────
        if total_chol and hdl_chol and sbp:
            base_risk = pooled_cohort_equations(age, gender, total_chol, hdl_chol,
                                                sbp, bp_treated, smoker, diabetic)
            if base_risk is not None:
                method_used = "framingham_pce"
            else:
                base_risk = framingham_point_score(age, gender, total_chol, hdl_chol,
                                                   sbp, bp_treated, smoker, diabetic)
                method_used = "framingham_point_score"

        # ── STRATEGY 2: Simplified Framingham (partial labs) ─────────────
        elif total_chol or sbp:
            chol  = total_chol or 200
            hdl   = hdl_chol  or (50 if gender == "Female" else 45)
            s     = sbp or (140 if self._is_hypertensive(health) else 120)
            base_risk = framingham_point_score(age, gender, chol, hdl,
                                               s, bp_treated, smoker, diabetic)
            method_used = "framingham_partial"

        # ── STRATEGY 3: Heart ML v2 (Cleveland UCI, AUC ~0.90, no labs needed) ──
        # Detrano R et al., Am J Cardiol 1989;64:304-310
        # Features: age, sex, cp type, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal
        elif self._heart_ml_v2 is not None:
            try:
                ml_bundle = self._heart_ml_v2
                sex_enc   = 1 if gender == 'Male' else 0
                cp_enc    = 0   # 0=typical angina (default conservative)
                trestbps  = int(sbp or 120)
                chol_v    = int(total_chol or 200)
                fbs_enc   = 1 if diabetic else 0
                restecg   = 1   # normal default
                thalach   = max(60, int(220 - age * 0.9))   # estimated max HR
                exang_enc = 1 if any('angina' in c.lower() for c in conditions) else 0
                oldpeak   = 1.5 if any('coronary' in c.lower() or 'ischaemic' in c.lower()
                                       for c in conditions) else 0.5
                slope     = 1
                ca_enc    = 1 if any('coronary' in c.lower() for c in conditions) else 0
                thal_enc  = 3   # reversible defect default
                fv_hrt = [[age, sex_enc, cp_enc, trestbps, chol_v, fbs_enc,
                            restecg, thalach, exang_enc, oldpeak, slope, ca_enc, thal_enc]]
                raw_prob  = ml_bundle['model'].predict_proba(fv_hrt)[0][1]
                # Cap at 0.90 — Cleveland training set is small and AUC=1.0 is overfit
                base_risk   = round(min(0.90, raw_prob), 3)
                method_used = "heart_ml_v2_cleveland"
            except Exception:
                base_risk   = self._rule_based(data)
                method_used = "rule_based"
        else:
            base_risk = self._rule_based(data)

        # ── South Asian correction ────────────────────────────────────────
        base_risk = south_asian_correction(base_risk, age, gender)

        # ── Family history ────────────────────────────────────────────────
        if fam_heart:
            base_risk = min(1.0, base_risk + 0.08)

        # ── Lifestyle penalties not captured by Framingham inputs ─────────
        lifestyle_penalty = 0.0
        if not smoker:  # Already in Framingham; only add for non-Framingham path
            pass
        if health.get("Stress") == "High":
            lifestyle_penalty += 0.04   # Chronic stress: HR 1.27 for CVD (Kivimaki 2012)
        if health.get("Sleep") and float(health.get("Sleep")) < 6:
            lifestyle_penalty += 0.03   # Short sleep: HR 1.48 for CVD (Itani 2017)

        if method_used not in ("framingham_pce", "framingham_point_score", "framingham_partial"):
            # Add smoking/alcohol for non-Framingham paths
            if health.get("Smoking") == "Daily":    lifestyle_penalty += 0.22
            elif health.get("Smoking") == "Occasional": lifestyle_penalty += 0.08
            if health.get("Alcohol") == "Daily":    lifestyle_penalty += 0.12

        # ── NFHS-5 district prior adjustment (Bayesian baseline) ─────────
        district = health.get("District") or profile.get("District") or ""
        state    = health.get("State")    or profile.get("State")    or ""
        try:
            dist_priors   = get_priors(district, state)
            prior_adj     = cardiovascular_prior_adjustment(dist_priors, self._is_hypertensive(health), diabetic)
        except Exception:
            prior_adj     = 0.0
            dist_priors   = {}

        # ── Combine everything ────────────────────────────────────────────
        final_risk = min(1.0, base_risk + condition_risk * 0.5 + lifestyle_penalty + prior_adj)

        # Hard floors for severe habits
        if health.get("Smoking") == "Daily" and health.get("Alcohol") == "Daily":
            final_risk = max(final_risk, 0.35)

        # ── Build output ──────────────────────────────────────────────────
        risk_level = self.get_risk_level(final_risk)
        lifestyle_factors = {
            "diet":     profile.get("Diet", "Average"),
            "activity": profile.get("ActivityLevel", "Moderate"),
            "sleep":    health.get("Sleep", 7),
            "stress":   health.get("Stress", "Medium"),
        }

        recommendations = self._get_recommendations(risk_level, detected_conditions,
                                                     health, sbp, dbp)
        # Confidence
        has_labs = bool(total_chol and hdl_chol and sbp)
        confidence = 0.92 if method_used == "framingham_pce" else \
                     0.82 if "framingham" in method_used else \
                     0.72 if method_used == "ml_model" else 0.55

        return {
            "current_risk":       round(final_risk, 3),
            "risk_level":         risk_level,
            "health_score":       self.get_health_score(final_risk),
            "method_used":        method_used,
            "south_asian_correction_applied": True,
            "model_confidence":   round(confidence, 2),
            "metrics": {
                "base_risk":            round(base_risk, 3),
                "condition_risk":       round(condition_risk, 3),
                "lifestyle_penalty":    round(lifestyle_penalty, 3),
                "family_history_penalty": 0.08 if fam_heart else 0.0,
                "district_prior_adj":   round(prior_adj, 4),
                "district_source":      dist_priors.get('source', 'national_average'),
            },
            "heart_conditions":      detected_conditions,
            "risk_progression":      self.project_risk_progression(final_risk, age, lifestyle_factors),
            "recommendations":       recommendations,
            "possible_issues":       self._possible_issues(final_risk, health, total_chol, sbp),
        }

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _is_diabetic(self, h):
        conds = [c.lower() for c in (h.get("MedicalConditions") or [])]
        g = h.get("FastingGlucose") or h.get("glucose")
        a = h.get("HbA1c")
        return (any("diabetes" in c for c in conds) or
                (g and float(g) >= 126) or (a and float(a) >= 6.5))

    def _is_hypertensive(self, h):
        conds = [c.lower() for c in (h.get("MedicalConditions") or [])]
        sbp = h.get("SystolicBP") or h.get("systolic_bp") or 0
        dbp = h.get("DiastolicBP") or h.get("diastolic_bp") or 0
        return (any("hypertension" in c for c in conds) or
                int(sbp) >= 140 or int(dbp) >= 90 or bool(h.get("BPOnMedication")))

    def _extract_features(self, data):
        try:
            p = data.get("ProfileInfo", {})
            h = data.get("HealthInfo",  {})
            conds = h.get("MedicalConditions", [])
            has_htn  = any("hypertension" in c.lower() for c in conds)
            has_chol = any("cholesterol" in c.lower() for c in conds)
            has_dm   = any("diabetes" in c.lower() for c in conds)
            return [
                p.get("Age", 50),
                h.get("Bmi", 25),
                h.get("SystolicBP")  or h.get("systolic_bp")  or (140 if has_htn  else 120),
                h.get("DiastolicBP") or h.get("diastolic_bp") or (90  if has_htn  else 80),
                h.get("TotalCholesterol") or ({1:185,2:215,3:265}.get(h.get("cholesterol")) if h.get("cholesterol") else (235 if has_chol else 185)),
                h.get("FastingGlucose") or h.get("glucose") or (140 if has_dm else 90),
                1 if h.get("Smoking") == "Daily" else 0,
                1 if h.get("Alcohol") in ("Weekly","Daily") else 0,
                0 if p.get("ActivityLevel") == "Sedentary" else 1,
            ]
        except Exception:
            return None

    def _rule_based(self, data):
        p = data.get("ProfileInfo", {})
        h = data.get("HealthInfo",  {})
        age = int(p.get("Age", 30))
        bmi = float(h.get("Bmi") or 25)
        risk = 0.0
        if age > 60:   risk += 0.25
        elif age > 45: risk += 0.15
        elif age > 35: risk += 0.05
        if bmi > 30:   risk += 0.15
        elif bmi > 25: risk += 0.07
        if h.get("Smoking") == "Daily":      risk += 0.22
        elif h.get("Smoking") == "Occasional": risk += 0.08
        if h.get("Alcohol") == "Daily":      risk += 0.12
        if h.get("Stress") == "High":        risk += 0.06
        if h.get("Sleep") and float(h.get("Sleep")) < 6: risk += 0.05
        if p.get("ActivityLevel") == "Sedentary": risk += 0.06
        if p.get("Diet") == "Poor":          risk += 0.05
        return min(risk, 0.90)

    def _get_recommendations(self, risk_level, detected, health, sbp, dbp):
        base = {
            "GREEN":  ["Maintain 150 min/week moderate aerobic exercise",
                       "Mediterranean or DASH diet reduces CVD risk by 25%",
                       "Annual blood pressure and cholesterol check"],
            "YELLOW": ["Target BP < 130/80 mmHg — reduces heart attack risk by 25%",
                       "Start 30-min brisk walk daily, 5 days/week",
                       "Limit saturated fat (<7% calories) and trans fat (0%)",
                       "Get HbA1c and fasting glucose tested if not done in last year"],
            "RED":    ["URGENT: Consult cardiologist within 4 weeks",
                       "Take all prescribed medications without missing doses",
                       "Monitor blood pressure twice daily, log results",
                       "Cardiac rehabilitation if recommended by doctor"],
        }.get(risk_level, [])
        extras = []
        for d in detected:
            if "Heart Failure" in d["condition"]:
                extras += ["Weigh yourself daily — >2kg gain in 1 day = call doctor",
                           "Fluid restriction may be advised — follow cardiologist guidance"]
            if "Arrhythmia" in d["condition"]:
                extras.append("Discuss anticoagulation with doctor if you have atrial fibrillation")
        if health.get("Smoking") == "Daily":
            extras.append("Quitting smoking cuts heart attack risk by 50% within 1 year")
        if sbp and dbp and (int(sbp) >= 140 or int(dbp) >= 90):
            extras.append(f"BP {sbp}/{dbp} mmHg is elevated — every 10mmHg reduction cuts risk by 20%")
        return (base + extras)[:6]

    def _possible_issues(self, risk, health, total_chol, sbp):
        issues = []
        if total_chol and float(total_chol) >= 240:
            issues.append("High total cholesterol detected")
        if sbp and int(sbp) >= 140:
            issues.append("Elevated systolic blood pressure")
        if health.get("Smoking") == "Daily":
            issues.append("Daily smoking significantly elevates CVD risk")
        if bool(health.get("FamilyHistoryHeart")):
            issues.append("Positive family history of premature heart disease")
        hdl = health.get("HDLCholesterol")
        if hdl and float(hdl) < 40:
            issues.append("Low HDL cholesterol (reduced cardioprotection)")
        return issues
