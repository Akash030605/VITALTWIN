# models/brain_model.py
# Primary:   CAIDE Dementia Risk Score (Kivipelto et al., Lancet Neurol 2006)
# Secondary: Framingham Stroke Risk Profile (D'Agostino et al., Stroke 1994)
# Validated: 1,449 Finns, 20-year follow-up (CAIDE)

from .base_model import BaseOrganModel


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

    # BMI
    if   bmi >= 30: pts += 2
    elif bmi >= 25: pts += 1   # Overweight adds some risk

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

    # Point → 20-year risk table
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
    # Scale: low (<4%) → 0.15, moderate (4-10%) → 0.35, high (>10%) → 0.55+
    if dementia_risk >= 0.164:   risk_score = 0.60 + min(0.30, (dementia_risk - 0.164) * 1.5)
    elif dementia_risk >= 0.074: risk_score = 0.40 + (dementia_risk - 0.074) / (0.164 - 0.074) * 0.20
    elif dementia_risk >= 0.042: risk_score = 0.25 + (dementia_risk - 0.042) / (0.074 - 0.042) * 0.15
    elif dementia_risk >= 0.019: risk_score = 0.15 + (dementia_risk - 0.019) / (0.042 - 0.019) * 0.10
    else:                        risk_score = 0.08

    return round(risk_score, 3), pts, round(dementia_risk * 100, 1)


def framingham_stroke_10yr(age, gender, systolic_bp, bp_treated,
                            diabetic, smoker, afib=False, lvh=False):
    """
    Framingham Stroke Risk Profile — D'Agostino RB et al., Stroke 1994;25:40-43
    Returns 10-year stroke probability (0-1).
    """
    pts = 0

    # Age points
    if gender == "Male":
        age_pts = [(54,0),(57,1),(60,2),(62,3),(65,4),(68,5),(71,6),(74,7),(100,8)]
    else:
        age_pts = [(56,0),(59,1),(62,2),(65,3),(68,4),(71,5),(74,6),(77,7),(100,8)]
    for threshold, p in age_pts:
        if age <= threshold:
            pts += p
            break

    # SBP points — D'Agostino et al. Stroke 1994, Table 2
    # Treated and untreated have separate point tables (not just a +1 offset)
    sbp = int(systolic_bp or 120)
    if gender == "Male":
        if bp_treated:
            # Treated SBP table (men)
            sbp_table = [(105,0),(115,2),(125,3),(135,4),(145,5),(155,6),(165,7),(175,8),(185,9),(200,10)]
        else:
            # Untreated SBP table (men)
            sbp_table = [(105,0),(115,1),(125,2),(135,3),(145,4),(155,5),(165,6),(175,7),(185,8),(200,9)]
        for threshold, p in sbp_table:
            if sbp <= threshold:
                pts += p
                break
        else:
            pts += 10
    else:
        if bp_treated:
            # Treated SBP table (women)
            sbp_table = [(105,0),(115,3),(125,5),(135,6),(145,8),(155,10),(165,11),(175,13),(185,15),(200,16)]
        else:
            # Untreated SBP table (women)
            sbp_table = [(105,0),(115,1),(125,2),(135,3),(145,5),(155,6),(165,7),(175,8),(185,9),(200,10)]
        for threshold, p in sbp_table:
            if sbp <= threshold:
                pts += p
                break
        else:
            pts += 16

    if diabetic: pts += 2
    if smoker:   pts += 3
    if afib:     pts += 4
    if lvh:      pts += 5 if gender == "Male" else 6

    # Point → 10-year risk
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
        # No trained ML model — CAIDE + Framingham are the validated algorithms

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

        conditions = health.get("MedicalConditions", [])

        # Absolute RED overrides
        abs_red = ["stroke","tia","transient ischaemic","dementia","alzheimer",
                   "vascular dementia","parkinson"]
        if any(any(r in c.lower() for r in abs_red) for c in conditions):
            return self._build_result(0.72, age, health, profile,
                                      "absolute_override", None, None, None, 0, 0)

        # Clinical inputs
        sbp          = int(health.get("SystolicBP") or health.get("systolic_bp") or 0)
        dbp          = int(health.get("DiastolicBP") or health.get("diastolic_bp") or 0)
        bp_treated   = bool(health.get("BPOnMedication", False))
        total_chol   = health.get("TotalCholesterol")
        smoker       = health.get("Smoking") in ("Daily", "Occasional")
        diabetic     = self._is_diabetic(health)
        physically_active = activity in ("Active", "Moderate")
        afib         = any("atrial fibrillation" in c.lower() or "afib" in c.lower()
                           for c in conditions)
        education_years = health.get("EducationYears") or profile.get("EducationYears")

        sbp_for_calc = sbp if sbp > 0 else (140 if self._is_hypertensive(health, sbp, conditions) else 120)

        # CAIDE score
        caide_risk, caide_pts, dementia_pct = caide_score(
            age, education_years, sbp_for_calc, bmi,
            total_chol, physically_active, sleep, diabetic
        )

        # Framingham Stroke score
        stroke_risk = framingham_stroke_10yr(
            age, gender, sbp_for_calc, bp_treated,
            diabetic, smoker, afib
        )

        # Combine: 60% dementia risk + 40% stroke risk
        base_risk = 0.60 * caide_risk + 0.40 * stroke_risk

        # Stress penalty (chronic stress → cortisol → hippocampal atrophy)
        # Johansson L et al., BMJ Open 2014 — HR 1.65 for dementia with high stress
        stress_penalty = {"Low": 0.0, "Medium": 0.03, "High": 0.08}.get(stress, 0.03)

        # Depression (strong bidirectional relationship with dementia)
        depression_conds = [c.lower() for c in conditions]
        depression_penalty = 0.06 if any("depression" in c or "anxiety" in c for c in depression_conds) else 0.0

        # Social isolation (meta-analysis: OR 1.58 for dementia — Holt-Lunstad 2015)
        # Proxy: sedentary + no social activity (poor diet as signal)
        isolation_penalty = 0.04 if (activity == "Sedentary" and diet == "Poor") else 0.0

        final_risk = min(1.0, base_risk + stress_penalty + depression_penalty + isolation_penalty)

        return self._build_result(final_risk, age, health, profile,
                                  "caide_framingham", caide_pts, dementia_pct,
                                  stroke_risk, stress_penalty, depression_penalty)

    def _build_result(self, final_risk, age, health, profile, method,
                      caide_pts, dementia_pct, stroke_risk, stress_pen, dep_pen):
        risk_level = self.get_risk_level(final_risk)
        lf = {"diet": profile.get("Diet","Average"), "activity": profile.get("ActivityLevel","Moderate"),
              "sleep": health.get("Sleep",7), "stress": health.get("Stress","Medium")}
        confidence = (0.82 if method == "caide_framingham" else
                      0.90 if method == "absolute_override" else 0.55)
        metrics = {}
        if caide_pts is not None:
            metrics["caide_points"]   = caide_pts
            metrics["dementia_20yr%"] = dementia_pct
        if stroke_risk is not None:
            metrics["stroke_10yr%"]   = round(stroke_risk * 100, 1)

        return {
            "current_risk":     round(final_risk, 3),
            "risk_level":       risk_level,
            "health_score":     self.get_health_score(final_risk),
            "method_used":      method,
            "model_confidence": round(confidence, 2),
            "metrics":          metrics,
            "risk_progression": self.project_risk_progression(final_risk, age, lf),
            "recommendations":  self._get_recommendations(risk_level, health, caide_pts),
            "possible_issues":  self._possible_issues(health, caide_pts),
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

    def _get_recommendations(self, risk_level, health, caide_pts):
        base = {
            "GREEN":  ["Physical exercise 150 min/week protects cognitive function",
                       "Mediterranean diet reduces dementia risk by 30-35%",
                       "Sleep 7-9 hours — brain clears amyloid during deep sleep",
                       "Keep learning: new languages, instruments, skills"],
            "YELLOW": ["Control blood pressure — every 10mmHg reduction cuts dementia risk by 20%",
                       "Treat depression promptly — untreated depression doubles dementia risk",
                       "Aim for 7-9h sleep — install blue-light filter after 8pm",
                       "Social engagement: join groups, volunteer — reduces isolation risk"],
            "RED":    ["Consult neurologist for cognitive assessment (MoCA test)",
                       "Strict BP and glucose control — most modifiable risk factors",
                       "Consider brain MRI if memory complaints persist",
                       "Cognitive stimulation therapy programs available at NIMHANS"],
        }.get(risk_level, [])
        extras = []
        if health.get("Stress") == "High":
            extras.append("High chronic stress elevates cortisol — damages hippocampus over time")
        if health.get("Sleep") and float(health.get("Sleep")) < 6:
            extras.append("Sleep <6h — brain cannot clear tau and amyloid protein during rest")
        if health.get("Smoking") == "Daily":
            extras.append("Smoking doubles dementia risk — quitting reduces risk within 2 years")
        return (base + extras)[:6]

    def _possible_issues(self, health, caide_pts):
        issues = []
        if caide_pts is not None and caide_pts >= 10:
            issues.append(f"CAIDE score {caide_pts} — elevated 20-year dementia risk")
        if health.get("Stress") == "High":
            issues.append("Chronic high stress — independently associated with cognitive decline")
        if health.get("Sleep") and float(health.get("Sleep")) < 6:
            issues.append("Insufficient sleep — impairs amyloid clearance from brain")
        sbp = health.get("SystolicBP") or health.get("systolic_bp")
        if sbp and int(sbp) >= 140:
            issues.append(f"Hypertension ({sbp} mmHg) — strongest modifiable dementia risk factor")
        conds = [c.lower() for c in (health.get("MedicalConditions") or [])]
        if any("atrial fibrillation" in c or "afib" in c for c in conds):
            issues.append("Atrial fibrillation — 5× increased stroke risk")
        return issues
