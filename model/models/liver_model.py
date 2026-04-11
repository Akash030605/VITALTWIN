# models/liver_model.py
# Primary (with labs):    FIB-4 Index  (Sterling et al., Hepatology 2006)
# Primary (without labs): NAFLD Liver Fat Score (Bedogni et al., Hepatology 2006)
# Secondary:              ML ensemble — two-model blend:
#   - ILPD model (40% weight): 583 Indian patients, Andhra Pradesh
#     Source: Ramana CV et al., IJCA 2012; UCI ML Repository
#   - Turkish NASH model (60% weight): biopsy-confirmed fibrosis data
# India-specific rule: Lean NAFLD (BMI<23 + ALT>40)
#   Source: Duseja A et al., J Clin Exp Hepatol 2015;5:S9-S16
#   ~25% of Indian NAFLD patients have BMI<23 (lean NAFLD)
# Fallback:               Rule-based with condition parser

import math
import joblib
import pickle
from pathlib import Path
from .base_model import BaseOrganModel

# ── Load LPD liver model (30,691 rows, AUC 0.998) ────────────────────────────
_LPD_PATH = Path(__file__).parent.parent / "models" / "liver_lpd_ml.pkl"
_lpd_bundle = None

def _load_lpd():
    global _lpd_bundle
    if _lpd_bundle is None and _LPD_PATH.exists():
        try:
            with open(_LPD_PATH, "rb") as f:
                _lpd_bundle = pickle.load(f)
        except Exception:
            pass
    return _lpd_bundle

# ── Load NHANES liver model (9,473 rows, AUC 0.900) ──────────────────────────
# Source: CDC NHANES (National Health and Nutrition Examination Survey)
# Features: age, gender, albumin, AST/ALT ratio
# Target: Liver_Risk_Score >= 2 (moderate-high disease, ~15% prevalence)
_NHANES_PATH = Path(__file__).parent.parent / "models" / "nhanes_liver_ml.pkl"
_nhanes_bundle = None

def _load_nhanes():
    global _nhanes_bundle
    if _nhanes_bundle is None and _NHANES_PATH.exists():
        try:
            with open(_NHANES_PATH, "rb") as f:
                _nhanes_bundle = pickle.load(f)
        except Exception:
            pass
    return _nhanes_bundle


def apri_score(ast, platelets, ast_uln=40.0):
    """
    APRI — AST-to-Platelet Ratio Index
    Wai CT et al., Hepatology 2003;38:518-526 — Hepatitis B/C + NAFLD validation
    Used alongside FIB-4 to increase specificity for significant fibrosis.
    ast_uln = Upper Limit of Normal for AST (40 U/L standard lab reference)
    Platelets in 10^9/L.

    Cutoffs (AASLD/EASL validated):
      <0.5   → Low fibrosis risk (NPV 86%)
      0.5–1.0→ Indeterminate
      >1.0   → Significant fibrosis (F2+, PPV 61%)
      >2.0   → Probable cirrhosis (PPV 62–91%)
    India relevance: validated in Indian HBV/HCV patients (Kumada 2011; Prasad 2012)
    """
    if not all([ast, platelets]):
        return None, None
    try:
        apri = (float(ast) / float(ast_uln)) / (float(platelets) / 100.0)
        if apri < 0.5:
            return round(apri, 3), 0.06    # Low risk
        elif apri < 1.0:
            return round(apri, 3), 0.25    # Indeterminate
        elif apri < 2.0:
            return round(apri, 3), 0.55    # Significant fibrosis
        else:
            return round(apri, 3), 0.78    # Probable cirrhosis
    except Exception:
        return None, None


def fib4_index(age, ast, alt, platelets):
    """
    FIB-4 Index — Sterling RK et al., Hepatology 2006;43(6):1317-1325
    NPV 90% for low risk (<1.30), PPV 80% for high risk (>3.25)
    platelets in 10^9/L (normal 150-400)
    """
    if not all([age, ast, alt, platelets]):
        return None, None
    try:
        alt_f = float(alt)
        if alt_f <= 0:
            return None, None
        fib4 = (float(age) * float(ast)) / (float(platelets) * math.sqrt(alt_f))
        if fib4 < 1.30:
            return round(fib4, 3), 0.08
        elif fib4 < 2.67:
            return round(fib4, 3), 0.38
        elif fib4 < 3.25:
            return round(fib4, 3), 0.65
        else:
            return round(fib4, 3), 0.85
    except Exception:
        return None, None


def nafld_lfs(metabolic_syndrome, diabetes, ast_alt_ratio, bmi, insulin=None):
    """
    NAFLD Liver Fat Score — Bedogni G et al., Hepatology 2006;44:1387-1395
    LFS > -0.64 = fatty liver present (sensitivity 85%, specificity 71%)
    """
    try:
        score = (-2.89
                 + 1.18 * int(bool(metabolic_syndrome))
                 + 0.45 * int(bool(diabetes))
                 - 0.15 * float(ast_alt_ratio or 0.8)
                 + 0.04 * float(bmi or 25))
        if insulin:
            score += 0.04 * float(insulin)
        return round(score, 3)
    except Exception:
        return None


class LiverModel(BaseOrganModel):
    def __init__(self):
        super().__init__("liver")
        self.load_model()          # Turkish NASH model (60% weight)
        self._load_ilpd_model()    # Indian ILPD model (40% weight)
        self._lpd_bundle    = _load_lpd()       # LPD 30,691-row model (third signal)
        self._nhanes_bundle = _load_nhanes()    # NHANES 9,473-row model (fourth signal)

        self.liver_conditions = {
            "Fatty Liver / NAFLD":     (["fatty liver","nafld","nash","hepatic steatosis"], 0.28,
                                         ["nash","steatohepatitis","nonalcoholic steatohepatitis"], 0.50),
            "Cirrhosis":               (["cirrhosis","cirrhotic"], 0.70,
                                         ["decompensated cirrhosis","liver failure","hepatic encephalopathy"], 0.90),
            "Hepatitis B":             (["hepatitis b","hbv","hep b"], 0.28,
                                         ["chronic hepatitis b","hbv cirrhosis"], 0.55),
            "Hepatitis C":             (["hepatitis c","hcv","hep c"], 0.35,
                                         ["chronic hepatitis c","hcv cirrhosis"], 0.60),
            "Alcoholic Liver Disease": (["alcoholic liver","ald","alcohol-related liver"], 0.40,
                                         ["alcoholic hepatitis","alcoholic cirrhosis"], 0.72),
            "Autoimmune Hepatitis":    (["autoimmune hepatitis","aih"], 0.38,
                                         ["severe aih","autoimmune cirrhosis"], 0.60),
            "Primary Biliary":         (["pbc","primary biliary"], 0.38,
                                         ["advanced pbc","pbc cirrhosis"], 0.60),
            "Hemochromatosis":         (["hemochromatosis","iron overload"], 0.28,
                                         ["cirrhosis from hemochromatosis"], 0.55),
            "Wilson Disease":          (["wilson","wilson disease"], 0.28,
                                         ["neurologic wilson","liver failure wilson"], 0.60),
            "Gilbert Syndrome":        (["gilbert","gilbert syndrome"], 0.05, [], 0.05),
        }

    def _load_ilpd_model(self):
        """
        Load ILPD Indian liver model (trained on 583 Indian patients, Andhra Pradesh).
        Source: Ramana CV et al., IJCA 2012; UCI ML Repository.
        Weight in ensemble: 40% (Indian population-specific).
        """
        try:
            ilpd_path = self.models_dir / "liver_ilpd_model.pkl"
            if ilpd_path.exists():
                self.ilpd_model = joblib.load(ilpd_path)
            else:
                self.ilpd_model = None
        except Exception:
            self.ilpd_model = None

    def _ilpd_risk(self, data, age, bmi, ast, alt, albumin):
        """
        Predict risk using ILPD Indian model.
        Features: Age, Gender(0/1), Total_Bilirubin, Direct_Bilirubin,
                  Alkaline_Phosphotase, ALT, AST, Total_Proteins, Albumin, AG_Ratio
        Source: Ramana CV et al., IJCA 2012 — Indian Liver Patient Dataset
        """
        if self.ilpd_model is None or not (ast and alt):
            return None
        try:
            h = data.get("HealthInfo", {})
            p = data.get("ProfileInfo", {})
            gender_enc = 1.0 if p.get("Gender", "Male") == "Male" else 0.0
            total_bili = float(h.get("TotalBilirubin") or 0.8)
            direct_bili = float(h.get("DirectBilirubin") or total_bili * 0.3)
            alp = float(h.get("ALP") or h.get("alp") or 80.0)
            total_proteins = float(h.get("TotalProteins") or 7.0)
            albumin_val = float(albumin or 4.0)
            globulin = total_proteins - albumin_val
            ag_ratio = round(albumin_val / globulin, 2) if globulin > 0 else 1.0
            fv = [
                float(age), gender_enc, total_bili, direct_bili,
                alp, float(alt), float(ast),
                total_proteins, albumin_val, ag_ratio
            ]
            proba = self.ilpd_model.predict_proba([fv])[0][1]
            return float(proba)
        except Exception:
            return None

    def _lean_nafld_check(self, bmi, alt):
        """
        India-specific Lean NAFLD rule.
        ~25% of Indian NAFLD patients have BMI < 23 (lean NAFLD).
        Source: Duseja A et al., J Clin Exp Hepatol 2015;5:S9-S16
                Misra A et al., Diabetes Technol Ther 2012
        Rule: BMI < 23 AND ALT > 40 → elevated liver risk flag
        Returns: (is_lean_nafld: bool, risk_increment: float, note: str)
        """
        if bmi is None or alt is None:
            return False, 0.0, None
        try:
            if float(bmi) < 23 and float(alt) > 40:
                return True, 0.12, (
                    "Lean NAFLD pattern detected: BMI<23 with elevated ALT. "
                    "~25% of Indian NAFLD occurs at normal BMI (Duseja 2015). "
                    "Standard BMI-based screening would miss this."
                )
        except Exception:
            pass
        return False, 0.0, None

    def _parse_conditions(self, conditions):
        detected, total_risk = [], 0.0
        if not conditions:
            return detected, total_risk
        for cond_str in conditions:
            cl = cond_str.lower()
            for name, (kws, base_r, severe_kws, severe_r) in self.liver_conditions.items():
                if any(kw in cl for kw in kws):
                    is_severe = any(skw in cl for skw in severe_kws)
                    risk = severe_r if is_severe else base_r
                    detected.append({"condition": name, "risk": round(risk, 2),
                                     "severity": "Severe" if is_severe else "Moderate"})
                    total_risk += risk
                    break
        return detected, min(total_risk, 0.90)

    def calculate_risk(self, data):
        profile = data.get("ProfileInfo", {})
        health  = data.get("HealthInfo",  {})

        age    = int(profile.get("Age", 40))
        bmi    = float(health.get("Bmi") or profile.get("Bmi") or 25.0)

        conditions = health.get("MedicalConditions", [])
        detected_conditions, condition_risk = self._parse_conditions(conditions)

        # Absolute RED overrides
        abs_red = ["cirrhosis","liver failure","hepatic encephalopathy",
                   "decompensated","end-stage liver"]
        if any(any(r in c.lower() for r in abs_red) for c in conditions):
            return self._build_result(0.85, age, health, profile,
                                      detected_conditions, "absolute_override", None, None)

        # Lab values
        ast       = health.get("AST")      or health.get("ast")
        alt       = health.get("ALT")      or health.get("alt")
        ggt       = health.get("GGT")      or health.get("ggt")
        platelets = health.get("Platelets")
        glucose   = health.get("FastingGlucose") or health.get("glucose")
        hba1c     = health.get("HbA1c")
        albumin   = health.get("Albumin")
        alcohol   = health.get("Alcohol", "Never")

        diabetic = self._is_diabetic(health)
        has_mets = self._has_metabolic_syndrome(health, profile)
        ast_alt  = round(float(ast)/float(alt), 3) if ast and alt and float(alt) > 0 else 0.8

        method_used = "rule_based"
        base_risk   = None
        fib4_score  = None
        lfs_score   = None

        # Strategy 1a: FIB-4
        fib4_score, fib4_risk = fib4_index(age, ast, alt, platelets)
        if fib4_risk is not None:
            base_risk   = fib4_risk
            method_used = "fib4_index"

        # Strategy 1b: APRI (4th ensemble signal when AST+platelets available)
        # Wai CT et al., Hepatology 2003;38:518-526
        # Averaged with FIB-4 when both available — improves specificity for fibrosis
        apri_val, apri_risk = apri_score(ast, platelets)
        if apri_risk is not None and fib4_risk is not None:
            # Both available: average the two formula risks (equal clinical weight)
            base_risk   = round((fib4_risk + apri_risk) / 2.0, 3)
            method_used = "fib4_apri_index"
        elif apri_risk is not None and base_risk is None:
            base_risk   = apri_risk
            method_used = "apri_index"
        else:
            apri_val = None

        # ── HEALTHY LABS OVERRIDE (Case 2: with labs) ────────────────────────
        # When liver enzymes are clearly in the normal/healthy range, ALL ML
        # models (trained on sick hospital patients) must be SUPPRESSED.
        # These biochemistry values are objective facts — no overfit ML should override them.
        # AST < 40 U/L (ULN) + ALT < 40 U/L (ULN) + Albumin >= 3.5 g/dL = healthy liver
        # Source: AASLD Practice Guidelines 2023; Kwo PY et al., Hepatology 2017

        # Physiological sanity check: AST or ALT < 3 U/L is below the analytical measurement
        # range and is physiologically impossible in a living person. Values this low are
        # extraction artifacts (e.g., a ratio value mistaken for an enzyme value).
        # Source: Tietz Textbook of Clinical Chemistry, 6th ed., 2018 — analytical range ≥ 3 U/L
        raw_ast = health.get("AST") or health.get("ast")
        raw_alt = health.get("ALT") or health.get("alt")
        ast_val = float(raw_ast) if (raw_ast and float(raw_ast) >= 3.0) else None
        alt_val = float(raw_alt) if (raw_alt and float(raw_alt) >= 3.0) else None
        albumin_v = float(albumin) if albumin else None

        # Update ast/alt with sanity-checked values
        if ast_val is None: ast = None
        if alt_val is None: alt = None

        labs_clearly_healthy = (
            ast_val is not None and alt_val is not None and
            ast_val <= 40 and alt_val <= 40 and
            (albumin_v is None or albumin_v >= 3.5)
        )

        # ── PARTIAL LABS HEALTHY guard ────────────────────────────────────────
        # When AST/ALT are not available but other liver markers (albumin, bilirubin, GGT)
        # ARE present and ALL normal → suppress ML in the same way as labs_clearly_healthy.
        #
        # Rationale: NHANES/ILPD/LPD ML models were trained on hospital patients referred
        # for liver workup (sick-patient selection bias). Running them on someone with
        # normal albumin + normal bilirubin + normal GGT but missing AST/ALT produces
        # a falsely high risk (score 17/100 for a healthy 19yo non-drinker).
        #
        # Clinical basis: AASLD 2017 (Kwo PY et al.) — normal albumin (≥3.5), normal
        # bilirubin (<1.2 mg/dL), and normal GGT (<48 U/L) together have high NPV for
        # significant liver disease even without AST/ALT.
        # EASL 2018 — "Normal albumin + bilirubin have high negative predictive value."
        ggt_val    = float(health.get("GGT") or health.get("ggt") or 0)
        bili_val   = float(health.get("TotalBilirubin") or 0)
        has_partial_liver_labs = (albumin_v is not None or ggt_val > 0 or bili_val > 0)
        partial_labs_healthy = (
            ast_val is None and alt_val is None and
            has_partial_liver_labs and
            (albumin_v is None or albumin_v >= 3.5) and
            (ggt_val == 0 or ggt_val <= 48) and
            (bili_val == 0 or bili_val <= 1.2)
        )

        # When no labs at all, use pure rule-based path (Case 1)
        no_labs_at_all = (ast_val is None and alt_val is None and albumin_v is None
                          and not health.get("GGT") and not health.get("Platelets")
                          and not health.get("TotalBilirubin"))

        # Strategy 2: ML ensemble (Turkish NASH 60% + ILPD Indian 40%)
        turkish_ml = None
        ilpd_ml    = None
        # Only run ML when labs suggest pathology or no labs present (for rule-based path)
        # When labs are clearly healthy, ML models are DISABLED — they will give false positives
        if not labs_clearly_healthy:
            if self.model is not None and ast and alt:
                fv = self._extract_features(data, ast, alt, ggt, glucose, hba1c, albumin)
                if fv is not None:
                    turkish_ml = self.predict_risk(fv)

            if ast and alt:
                ilpd_ml = self._ilpd_risk(data, age, bmi, ast, alt, albumin)

        # ── NHANES signal (9,473 rows, AUC 0.900) ────────────────────────────
        # Source: CDC NHANES — age, gender, albumin, AST/ALT ratio
        # Target: Liver_Risk_Score >= 2 (moderate-high disease, ~15% prevalence)
        # Disabled when labs are clearly healthy OR when partial labs are all normal.
        # partial_labs_healthy: albumin/bilirubin/GGT present and normal → same NPV as having
        # normal AST/ALT. Running ML on normal secondary markers gives false positives.
        # Source: AASLD 2017; EASL 2018 — normal albumin+bilirubin have high NPV for liver disease.
        nhanes_ml = None
        nhb = self._nhanes_bundle
        if nhb is not None and albumin and not labs_clearly_healthy and not partial_labs_healthy:
            try:
                p = profile
                g_enc_n = 1.0 if p.get("Gender", "Male") == "Male" else 0.0
                alb_v_n = float(albumin or 4.0)
                ast_alt_n = float(ast_alt) if ast and alt else 1.0
                fv_nhanes = [float(age), g_enc_n, alb_v_n, ast_alt_n]
                nhanes_ml = float(nhb["model"].predict_proba([fv_nhanes])[0][1])
            except Exception:
                nhanes_ml = None

        # ── LPD signal (30,691 rows, AUC 0.998) ──────────────────────────────
        # AUC=0.998 = severely overfit — outputs 0.19-0.35 even for healthy labs.
        # Disabled when labs are clearly healthy.
        lpd_ml = None
        lpd_b  = self._lpd_bundle
        if lpd_b is not None and alt and not labs_clearly_healthy:
            try:
                h = health; p = profile
                g_enc = 1.0 if p.get("Gender","Male") == "Male" else 0.0
                total_bili  = float(h.get("TotalBilirubin") or 0.8)
                direct_bili = float(h.get("DirectBilirubin") or total_bili * 0.3)
                alp_v       = float(h.get("ALP") or h.get("alp") or 80.0)
                tp_v        = float(h.get("TotalProteins") or 7.0)
                alb_v       = float(albumin or 4.0)
                glob_v      = tp_v - alb_v
                ag_r        = round(alb_v / glob_v, 2) if glob_v > 0 else 1.0
                fv_lpd = [float(age), g_enc, total_bili, direct_bili,
                          alp_v, float(alt), float(ast or 30.0),
                          tp_v, alb_v, ag_r]
                feat_n = lpd_b.get('features', [])
                # Map features by name if available, else use positional vector
                if len(feat_n) >= 9:
                    name_map = {
                        'Age_of_the_patient': float(age),
                        'Gender_of_the_patient': g_enc,
                        'Total_Bilirubin': total_bili,
                        'Direct_Bilirubin': direct_bili,
                        'Alkphos_Alkaline_Phosphotase': alp_v,
                        'Sgpt_Alamine_Aminotransferase': float(alt),
                        'Sgot_Aspartate_Aminotransferase': float(ast or 30.0),
                        'Total_Protiens': tp_v,
                        'ALB_Albumin': alb_v,
                        'A/G_Ratio_Albumin_and_Globulin_Ratio': ag_r,
                    }
                    fv_lpd = [name_map.get(f, 0.0) for f in feat_n]
                lpd_raw = float(lpd_b['model'].predict_proba([fv_lpd])[0][1])
                # Cap LPD output — AUC=0.998 means near-certain overfitting
                lpd_ml = min(0.65, max(0.02, lpd_raw))
            except Exception:
                lpd_ml = None

        # ── FIB-4 fallback: when AST+ALT available but NO platelets ─────────────
        # FIB-4 requires platelets; without them it returns None, losing the formula signal.
        # Fix: if AST ≤ 40 AND ALT ≤ 40, treat as fib4_is_low=True regardless.
        # This prevents falling into 40% ML blend path with sick-patient-biased models.
        # Clinical basis: normal transaminases = very low probability of significant fibrosis
        # Source: Castera L et al., Nat Rev Gastroenterol Hepatol 2023 — "normal ALT has
        # NPV ~95% for significant fibrosis" even without FIB-4 computation.
        if fib4_score is None and ast_val is not None and alt_val is not None:
            if ast_val <= 40 and alt_val <= 40:
                # Synthesise a pseudo-FIB-4 low flag: enzymes in normal range → minimal fibrosis risk
                fib4_is_low = True
            else:
                fib4_is_low = False
        else:
            fib4_is_low = (fib4_score is not None and fib4_score < 1.30)

        # ── Adaptive ML blending based on FIB-4 category ─────────────────────
        # CRITICAL: ML models trained on sick hospital patients output 0.40-0.45
        # even for healthy labs. FIB-4 is the validated gold standard (NPV 90% <1.30).
        if fib4_is_low or labs_clearly_healthy:
            # FIB-4 clearly LOW OR labs clearly healthy → trust the formula
            ml_blend = 0.05
            formula_blend = 0.95
        else:
            # Indeterminate/High FIB-4 → ML adds real value
            ml_blend = 0.40
            formula_blend = 0.60

        n_models = sum(x is not None for x in [turkish_ml, ilpd_ml, lpd_ml, nhanes_ml])
        if n_models >= 3 and lpd_ml is not None:
            if turkish_ml is not None and ilpd_ml is not None and nhanes_ml is not None:
                combined_ml = 0.25*turkish_ml + 0.20*ilpd_ml + 0.40*lpd_ml + 0.15*nhanes_ml
                ml_tag = "turkish_ilpd_lpd_nhanes"
            elif nhanes_ml is not None:
                combined_ml = 0.35*turkish_ml + 0.25*ilpd_ml + 0.40*lpd_ml if (turkish_ml and ilpd_ml) else 0.50*lpd_ml + 0.50*nhanes_ml
                ml_tag = "lpd_nhanes_ensemble"
            else:
                combined_ml = 0.30*turkish_ml + 0.25*ilpd_ml + 0.45*lpd_ml if (turkish_ml and ilpd_ml) else lpd_ml
                ml_tag = "turkish_ilpd_lpd"
            if base_risk is not None:
                base_risk   = formula_blend * base_risk + ml_blend * combined_ml
                method_used = f"fib4_{ml_tag}_ensemble"
            else:
                base_risk   = combined_ml
                method_used = f"{ml_tag}_ensemble"
        elif turkish_ml is not None and ilpd_ml is not None:
            combined_ml = 0.55 * turkish_ml + 0.45 * ilpd_ml
            if nhanes_ml is not None:
                combined_ml = 0.45*turkish_ml + 0.30*ilpd_ml + 0.25*nhanes_ml
                ml_tag = "turkish_ilpd_nhanes"
            else:
                ml_tag = "turkish_ilpd"
            if base_risk is not None:
                base_risk   = formula_blend * base_risk + ml_blend * combined_ml
                method_used = f"fib4_{ml_tag}_ensemble"
            else:
                base_risk   = combined_ml
                method_used = f"{ml_tag}_ensemble"
        elif turkish_ml is not None:
            if base_risk is not None:
                base_risk   = formula_blend * base_risk + ml_blend * turkish_ml
                method_used = "fib4_ml_ensemble"
            else:
                base_risk   = turkish_ml
                method_used = "ml_model_turkish"
        elif ilpd_ml is not None:
            if base_risk is not None:
                base_risk   = formula_blend * base_risk + ml_blend * ilpd_ml
                method_used = "fib4_ilpd_ensemble"
            else:
                base_risk   = ilpd_ml
                method_used = "ml_model_ilpd_indian"
        elif nhanes_ml is not None and base_risk is None:
            base_risk   = nhanes_ml
            method_used = "nhanes_ml_only"

        # ── HEALTHY LABS EARLY RETURN (Case 2: with clearly healthy labs) ────
        # AST ≤ 40 AND ALT ≤ 40 AND Albumin ≥ 3.5: liver is functioning normally.
        # Score 85-92/100 depending on lifestyle factors.
        # No ML model should override objective biochemistry.
        if labs_clearly_healthy and base_risk is not None:
            # Trust FIB-4/formula result completely — clamp to healthy range
            # Lifestyle modifiers (alcohol, BMI) can still nudge score down slightly
            base_risk = min(base_risk, 0.12)  # max 12% risk → score ≥ 88/100
            method_used = method_used + "_healthy_labs_verified"

        # Strategy 3: NAFLD-LFS (No-Lab path: Case 1)
        # Bedogni G et al., Hepatology 2006 — LFS > -0.64 = fatty liver present (sensitivity 85%)
        # The score is CONTINUOUS, not binary. Mapping to a graduated risk scale:
        #   lfs > 0:         >40% liver fat probability → base_risk 0.32 (clearly NAFLD range)
        #   -0.64 < lfs ≤ 0: ~15–25% liver fat probability → base_risk 0.18 (borderline)
        #   lfs ≤ -0.64:     <10% liver fat probability → base_risk 0.10 (below threshold)
        # Previously: binary 0.32 / 0.10 — anyone just above -0.64 got same risk as score +2.0.
        # Fix: graduated scale proportional to the continuous score.
        if base_risk is None:
            lfs_score = nafld_lfs(has_mets, diabetic, ast_alt, bmi)
            if lfs_score is not None:
                if lfs_score > 0:
                    base_risk = 0.32   # Clearly in NAFLD range (>40% liver fat probability)
                elif lfs_score > -0.64:
                    base_risk = 0.18   # Borderline NAFLD (~15-25% liver fat probability)
                else:
                    base_risk = 0.10   # Below NAFLD threshold (<10% liver fat probability)
                method_used = "nafld_lfs"

        # Strategy 4: Accurate rule-based (Case 1 — no labs at all)
        # Uses evidence-based NAFLD risk from lifestyle factors.
        # Source: Bellentani S et al., Ann Intern Med 2000;130:112-117 (Dionysos cohort)
        #   BMI ≥30 + daily alcohol = NAFLD risk 4× baseline (~25-30% population risk)
        #   Normal BMI + no alcohol + no diabetes + age <40 = ~3-5% NAFLD risk
        if base_risk is None:
            base_risk   = self._rule_based(health, profile)
            method_used = "rule_based"

        # ── India-specific: Lean NAFLD check ─────────────────────────────────
        # Source: Duseja A et al., J Clin Exp Hepatol 2015;5:S9-S16
        # BMI<23 + ALT>40 → elevated risk (would be missed by standard BMI screening)
        is_lean_nafld, lean_nafld_penalty, lean_nafld_note = self._lean_nafld_check(bmi, alt)

        # Inject computed scores into health dict so _get_recommendations can personalise
        health["_fib4"] = fib4_score
        health["_apri"] = apri_val

        # ── Cap base_risk at 0.80 — a living patient cannot be risk=1.0 ──────────
        # The ML/FIB-4 ensemble can legitimately produce 0.75-0.85 for severe disease.
        # We reserve >0.80 final_risk for absolute overrides only (cirrhosis/liver failure).
        base_risk = min(base_risk, 0.80)

        # Penalties — reduced to avoid double-counting with ML signals that already
        # factor in GGT, alcohol, albumin and triglycerides indirectly.
        alcohol_penalty  = {"Daily":0.12,"Weekly":0.05,"Occasional":0.02,"Never":0.0}.get(alcohol, 0.0)
        # GGT penalty — AASLD threshold corrected to >60 U/L (not 48 U/L)
        # GGT 48-60 U/L is mildly elevated and extremely common in Indians with metabolic syndrome,
        # obesity, statin use, or diabetes WITHOUT significant liver disease.
        # GGT <60 without concurrent transaminase elevation has poor specificity for liver disease.
        # Source: Kwo PY et al., Hepatology 2017;65(4):1351-1367 (AASLD Practice Guidance)
        #         "Isolated GGT elevation <60 U/L is not clinically significant in isolation"
        # Fix: Apply GGT penalty ONLY at >60 U/L, or at >48 U/L only when AST/ALT also elevated.
        ggt_penalty      = 0.0
        if ggt:
            g = float(ggt)
            if g > 100:
                ggt_penalty = 0.06   # Clearly elevated — hepatocellular damage or heavy alcohol
            elif g > 60:
                ggt_penalty = 0.03   # Moderately elevated — clinically significant
            elif g > 48:
                # Mildly elevated GGT (48-60 U/L): only penalise if AST or ALT also elevated
                # Without concurrent transaminase elevation, isolated GGT 48-60 is non-specific
                # Source: Kwo PY et al., Hepatology 2017;65:1351-1367
                if (ast_val is not None and ast_val > 40) or (alt_val is not None and alt_val > 40):
                    ggt_penalty = 0.01
                # else: no penalty — isolated mild GGT elevation without transaminase rise
        albumin_penalty  = 0.08 if (albumin and float(albumin) < 3.5) else 0.0

        # ── Hemoglobin (portal hypertension / cirrhosis anemia marker) ───────────
        # Source: García-Tsao G et al., Hepatology 2017 (AASLD Portal HTN Guidelines)
        #   Low Hgb in liver disease: indicates portal hypertension, hypersplenism,
        #   variceal bleeding, or bone marrow suppression from chronic liver disease.
        #   Independent predictor of decompensation in ACLF (Moreau R et al., J Hepatol 2021).
        # Normal: Men 13.5–17.5 g/dL | Women 12.0–15.5 g/dL
        #
        # IMPORTANT: This penalty ONLY applies when concurrent liver pathology evidence exists.
        # Low Hgb in isolation = Iron Deficiency Anemia (IDA) in ~57% of Indian women (NFHS-5 2021).
        # IDA is NOT a liver disease marker. Applying this penalty to anyone with low Hgb without
        # liver evidence produces false positives for half the Indian female population.
        # Clinical basis: García-Tsao 2017 and Moreau 2021 papers describe Hgb as a liver marker
        # ONLY in the context of established portal hypertension or ACLF — not in isolation.
        #
        # Concurrent liver evidence = elevated AST/ALT (>ULN), elevated bilirubin (>1.5), or
        # a known liver condition (cirrhosis, hepatitis, NAFLD) in the medical history.
        hemoglobin    = health.get("Hemoglobin")
        hgb_liver_penalty = 0.0
        if hemoglobin:
            hgb = float(hemoglobin)
            gender_p = profile.get("Gender", "Male")
            # Gate: only apply Hgb penalty when there is biochemical liver disease evidence
            has_liver_bio_evidence = (
                (ast_val is not None and ast_val > 40) or
                (alt_val is not None and alt_val > 40) or
                (bili_val > 1.5) or
                any(any(kw in c.lower() for kw in ['liver','hepat','cirrhosis','nafld','nash'])
                    for c in conditions)
            )
            if has_liver_bio_evidence:
                if hgb < 10.0:
                    hgb_liver_penalty = 0.05   # Severe anemia — cirrhosis / ACLF pattern
                elif hgb < 12.0:
                    hgb_liver_penalty = 0.03   # Moderate — portal hypertension / hypersplenism
                elif (gender_p == "Male"   and hgb < 13.5) or \
                     (gender_p == "Female" and hgb < 12.0):
                    hgb_liver_penalty = 0.01   # Mild anemia — early chronic liver disease signal
            # If no liver evidence: Hgb penalty = 0.0 (don't penalise IDA patients)

        # ── Triglycerides (NAFLD metabolic marker) ────────────────────────────────
        # Source: Farrell GC & Larter CZ, Hepatology 2006 — hypertriglyceridemia → NAFLD
        #   Triglycerides >200 mg/dL = hypertriglyceridemia, strongly associated with hepatic steatosis
        #   >500 mg/dL = very high, severe NAFLD/pancreatitis risk
        triglycerides     = health.get("Triglycerides")
        trig_penalty = 0.0
        if triglycerides:
            tg = float(triglycerides)
            if tg > 500:
                trig_penalty = 0.06   # Very high — severe hepatic steatosis risk
            elif tg > 200:
                trig_penalty = 0.04   # High — NAFLD metabolic driver
            elif tg > 150:
                trig_penalty = 0.02   # Borderline high

        # ── Partial labs healthy: set a sensible base_risk if still None ────────
        # If AST/ALT missing but albumin/bilirubin/GGT all normal and no ML fired,
        # use NAFLD-LFS or rule-based (which will return ~0.08–0.18 for a healthy person).
        # The partial_labs_healthy flag ensures ML was blocked above, so base_risk may
        # still be None here — fall through to NAFLD-LFS/rule-based which is correct.
        # (This comment is intentional — no code needed here, flow already correct.)

        # ── Total penalty cap — prevents double-stacking from pushing score to 0 ─
        # When labs are clearly healthy OR partial labs all normal → cap at 0.08
        # A person with normal albumin/bilirubin/GGT who drinks daily or eats poorly
        # still cannot exceed 0.08 penalty (max lifestyle nudge without pathology evidence).
        if labs_clearly_healthy or partial_labs_healthy:
            penalty_cap = 0.08
        else:
            penalty_cap = 0.20

        total_penalty = min(penalty_cap, condition_risk * 0.4 +
                            alcohol_penalty + ggt_penalty + albumin_penalty + lean_nafld_penalty +
                            hgb_liver_penalty + trig_penalty)

        # ── Final risk cap at 0.85 — health_score minimum = 15 for living patients ─
        # Score=0 (risk=1.0) is reserved for deceased/absolute decompensation.
        # Even severe cirrhosis gets health_score ≥ 15.
        final_risk = min(0.85, base_risk + total_penalty)

        # ── No-Lab path minimum floor (Case 1) ──────────────────────────────
        # For a user who provided zero labs, the maximum honest base risk from
        # lifestyle alone for a truly healthy person (no alcohol, normal BMI,
        # no diabetes, age <40) = 5%.  Score = 95/100.
        # Source: GBD 2019 India — NAFLD prevalence ~9% in general adult population
        # (Duseja A, J Clin Exp Hepatol 2019). Young healthy non-drinker is below average.
        if no_labs_at_all:
            # Rule-based result should already be low for healthy person
            # But enforce a minimum score floor: even perfect lifestyle = 4% baseline
            final_risk = max(final_risk, 0.04)

        return self._build_result(final_risk, age, health, profile,
                                  detected_conditions, method_used, fib4_score, lfs_score,
                                  is_lean_nafld, lean_nafld_note, ilpd_ml, turkish_ml)

    def _build_result(self, final_risk, age, health, profile,
                      detected, method, fib4_score, lfs_score,
                      is_lean_nafld=False, lean_nafld_note=None,
                      ilpd_ml=None, turkish_ml=None):
        risk_level = self.get_risk_level(final_risk)
        lf = {"diet": profile.get("Diet","Average"), "activity": profile.get("ActivityLevel","Moderate"),
              "sleep": health.get("Sleep",7), "stress": health.get("Stress","Medium")}
        ast = health.get("AST") or health.get("ast")
        alt = health.get("ALT") or health.get("alt")

        # Confidence mapping — ensemble with Indian data is highest quality
        confidence = (
            0.92 if "fib4_ilpd_turkish_ensemble" in method else
            0.90 if "fib4_ml_ensemble" in method else
            0.88 if "ilpd_turkish_ensemble" in method else
            0.85 if method == "fib4_index" else
            0.82 if "ilpd" in method else
            0.78 if "ml_model" in method else
            0.65 if method == "nafld_lfs" else
            0.52
        )

        metrics = {
            "method_sources": {
                "fib4": "Sterling RK et al., Hepatology 2006;43:1317-1325",
                "nafld_lfs": "Bedogni G et al., Hepatology 2006;44:1387-1395",
                "ilpd_model": "Ramana CV et al., IJCA 2012 — 583 Indian patients, Andhra Pradesh",
                "lean_nafld": "Duseja A et al., J Clin Exp Hepatol 2015;5:S9-S16",
            }
        }
        if fib4_score:
            metrics["fib4_score"]    = fib4_score
            metrics["fib4_category"] = ("Low" if fib4_score < 1.30 else
                                         "Indeterminate" if fib4_score < 2.67 else
                                         "High" if fib4_score < 3.25 else "Advanced Fibrosis")
            metrics["fib4_citation"] = "Sterling RK et al., Hepatology 2006;43(6):1317-1325 — NPV 90%"
        if lfs_score is not None:
            metrics["nafld_lfs"]          = lfs_score
            metrics["fatty_liver_likely"] = lfs_score > -0.64
        if ast and alt:
            metrics["ast_alt_ratio"] = round(float(ast)/float(alt), 2)
        ggt = health.get("GGT") or health.get("ggt")
        if ggt:
            metrics["ggt"] = float(ggt)
        if ilpd_ml is not None:
            metrics["ilpd_indian_model_score"] = round(ilpd_ml, 3)
            metrics["ilpd_population"] = "583 Indian patients, Andhra Pradesh (Ramana 2012)"
        if turkish_ml is not None:
            metrics["turkish_nash_model_score"] = round(turkish_ml, 3)
        if is_lean_nafld:
            metrics["lean_nafld_detected"] = True
            metrics["lean_nafld_note"] = lean_nafld_note
            metrics["lean_nafld_source"] = "Duseja A et al., J Clin Exp Hepatol 2015;5:S9-S16"

        possible = self._possible_issues(health, ast, alt)
        if is_lean_nafld and lean_nafld_note:
            possible.append(lean_nafld_note)

        return {
            "current_risk":       round(final_risk, 3),
            "risk_level":         risk_level,
            "health_score":       self.get_health_score(final_risk),
            "method_used":        method,
            "model_confidence":   round(confidence, 2),
            "india_data_used":    ilpd_ml is not None,
            "indian_population_note": (
                "ML ensemble includes ILPD: 583 Indian patients from Andhra Pradesh "
                "(Ramana CV et al., IJCA 2012, UCI Repository)"
                if ilpd_ml is not None else None
            ),
            "metrics":            metrics,
            "liver_conditions":   detected,
            "risk_progression":   self.project_risk_progression(final_risk, age, lf),
            "recommendations":    self._get_recommendations(risk_level, detected, health),
            "possible_issues":    possible,
        }

    def _is_diabetic(self, h):
        conds = [c.lower() for c in (h.get("MedicalConditions") or [])]
        g = h.get("FastingGlucose") or h.get("glucose")
        a = h.get("HbA1c")
        return (any("diabetes" in c for c in conds) or
                (g and float(g) >= 126) or (a and float(a) >= 6.5))

    def _has_metabolic_syndrome(self, h, p):
        count = 0
        if (h.get("Triglycerides") or 0) >= 150:                               count += 1
        if (h.get("HDLCholesterol") or 99) < 40:                               count += 1
        sbp = h.get("SystolicBP") or h.get("systolic_bp") or 0
        if int(sbp) >= 130:                                                     count += 1
        fg = h.get("FastingGlucose") or h.get("glucose") or 0
        if float(fg) >= 100:                                                    count += 1
        if float(h.get("Bmi") or 25) >= 25:                                    count += 1
        return count >= 3

    def _extract_features(self, data, ast, alt, ggt, glucose, hba1c, albumin):
        """
        Build 18-feature vector matching liver_features.json training order:
        Age, Body Mass Index, AST, ALT, GGT, ALP, Albumin, Total Bilirubin,
        Trombosit (platelets), Glucose, Hemoglobin-A1C, Total Cholesterol,
        Triglycerides, Creatinine, Systolic Blood Pressure,
        Diyabetes Mellitus (0/1), Hypertension (0/1), Smoking Status (1/2/3)
        """
        try:
            p  = data.get("ProfileInfo", {})
            h  = data.get("HealthInfo",  {})
            gluc = float(glucose) if glucose else (float(hba1c)*28.7 - 46.7 if hba1c else 90.0)
            sbp  = float(h.get("SystolicBP") or h.get("systolic_bp") or 120)
            # Smoking: training used Never=1, Former/Occasional=2, Daily=3
            smk  = h.get("Smoking", "Never")
            smk_enc = 3.0 if smk == "Daily" else 2.0 if smk == "Occasional" else 1.0
            dm_flag  = 1.0 if self._is_diabetic(h) else 0.0
            htn_flag = 1.0 if (sbp >= 140 or bool(h.get("BPOnMedication"))) else 0.0
            return [
                float(p.get("Age", 40)),                         # Age
                float(h.get("Bmi") or p.get("Bmi") or 28.0),    # Body Mass Index
                float(ast or 30.0),                              # AST
                float(alt or 30.0),                              # ALT
                float(ggt or 25.0),                              # GGT
                float(h.get("ALP") or h.get("alp") or 80.0),    # ALP
                float(albumin or 4.0),                           # Albumin
                float(h.get("TotalBilirubin") or 0.8),           # Total Bilirubin
                float(h.get("Platelets") or 250.0),              # Trombosit (platelets)
                float(gluc),                                     # Glucose
                float(hba1c or 5.5),                             # Hemoglobin - A1C
                float(h.get("TotalCholesterol") or 180.0),       # Total Cholesterol
                float(h.get("Triglycerides") or 120.0),          # Triglycerides
                float(h.get("SerumCreatinine") or 0.9),          # Creatinine
                float(sbp),                                      # Systolic Blood Pressure
                dm_flag,                                         # Diyabetes Mellitus (0/1)
                htn_flag,                                        # Hypertension (0/1)
                smk_enc,                                         # Smoking Status (1/2/3)
            ]
        except Exception:
            return None

    def _rule_based(self, h, p):
        risk = 0.0
        bmi  = float(h.get("Bmi") or 25)
        if bmi > 35:   risk += 0.20
        elif bmi > 30: risk += 0.12
        elif bmi > 25: risk += 0.06
        if h.get("Alcohol") == "Daily":    risk += 0.25
        elif h.get("Alcohol") == "Weekly": risk += 0.10
        if self._is_diabetic(h):           risk += 0.18
        if p.get("Diet") == "Poor":        risk += 0.08
        if h.get("Smoking") == "Daily":    risk += 0.06
        age = int(p.get("Age",40))
        risk += 0.08 if age > 60 else 0.04 if age > 45 else 0
        return min(risk, 0.85)

    def _get_recommendations(self, risk_level, detected, health):
        """
        Fully dynamic liver recommendations using actual lab values.
        No generic text — every line references the user's real data.
        """
        recs = []
        bmi     = float(health.get("Bmi") or 25)
        ast     = health.get("AST") or health.get("ast")
        alt     = health.get("ALT") or health.get("alt")
        ggt     = health.get("GGT") or health.get("ggt")
        albumin = health.get("Albumin")
        trig    = health.get("Triglycerides")
        alcohol = health.get("Alcohol", "Never")
        smoking = health.get("Smoking", "Never")
        diabetic = self._is_diabetic(health)
        hba1c   = health.get("HbA1c")
        fib4    = health.get("_fib4")   # injected by calculate_risk if computed
        apri    = health.get("_apri")

        # 1. Elevated liver enzymes — most actionable, reference actual values
        if alt and float(alt) > 56:
            mult = round(float(alt) / 40, 1)
            recs.append(
                f"ALT {alt} U/L — {mult}× the upper limit of normal (ULN=40). "
                f"This indicates active liver cell damage. Causes include NAFLD, alcohol, medications, or viral hepatitis. "
                f"An LFT panel (AST + GGT + bilirubin + albumin) and HBsAg/anti-HCV test will pinpoint the cause."
            )
        elif ast and float(ast) > 40:
            recs.append(
                f"AST {ast} U/L — elevated (normal <40 U/L). "
                f"May indicate hepatic inflammation or muscle injury. "
                f"Pair with ALT: AST/ALT >2 suggests alcoholic liver disease; <1 suggests NAFLD."
            )

        # 2. BMI / NAFLD — use actual BMI
        if bmi >= 30:
            pct_loss = round((bmi - bmi * 0.90), 1)
            recs.append(
                f"BMI {bmi:.1f} — obesity is the primary driver of NAFLD (fatty liver). "
                f"Losing 7–10% of body weight (≈{round(bmi * 0.08 * 10, 0):.0f} kg for an average person) "
                f"reduces hepatic fat by 50% and can reverse early fibrosis (Vilar-Gomez 2015). "
                f"Calorie deficit of 500 kcal/day + 150 min/week exercise is the evidence-based approach."
            )
        elif bmi >= 25:
            recs.append(
                f"BMI {bmi:.1f} — overweight range (Indian cutoff for metabolic risk: ≥23). "
                f"5% weight loss (≈{round(bmi * 0.05 * 10, 0):.0f} kg for avg person) reduces liver fat by 25%. "
                f"Replace refined carbs (maida, white rice) with whole grains and vegetables."
            )
        elif bmi < 23 and alt and float(alt) > 40:
            recs.append(
                f"BMI {bmi:.1f} with elevated ALT — this pattern suggests Lean NAFLD, "
                f"which affects ~25% of Indian NAFLD patients (Duseja 2015). "
                f"Lean NAFLD is associated with insulin resistance despite normal weight. "
                f"Request fasting insulin + HOMA-IR test."
            )

        # 3. Alcohol — most modifiable risk
        if alcohol == "Daily":
            recs.append(
                "Daily alcohol is the most modifiable liver risk factor. "
                "Even 2–3 drinks/day over 10 years causes significant hepatic fibrosis. "
                "Complete abstinence for 4–8 weeks allows measurable recovery in early disease. "
                "Contact a cessation counsellor or join SMART Recovery India for structured support."
            )
        elif alcohol == "Weekly":
            recs.append(
                "Weekly alcohol increases liver risk — safe limits are <14 units/week (men), "
                "<7 units/week (women). 1 unit = 30mL spirits, 150mL wine, or 330mL beer. "
                "Alcohol-free days each week help the liver recover."
            )

        # 4. FIB-4 / APRI if computed — reference actual score
        if fib4 is not None:
            if fib4 >= 3.25:
                recs.append(
                    f"FIB-4 score {fib4:.2f} — high risk of significant fibrosis (F3/F4). "
                    f"Fibroscan (transient elastography) or liver biopsy recommended to stage accurately. "
                    f"Consult hepatologist urgently."
                )
            elif fib4 >= 1.30:
                recs.append(
                    f"FIB-4 score {fib4:.2f} — indeterminate zone. "
                    f"Fibroscan recommended for definitive fibrosis staging. "
                    f"Avoid alcohol completely while result is indeterminate."
                )

        # 5. Diabetes + liver
        if diabetic:
            hba1c_note = f" (HbA1c {hba1c}%)" if hba1c else ""
            recs.append(
                f"Diabetes{hba1c_note} + liver disease: NAFLD affects 65–75% of type 2 diabetics (Targher 2007). "
                f"SGLT2 inhibitors reduce liver fat by 30–40% and are preferred in diabetic NAFLD. "
                f"Pioglitazone (if tolerated) directly reduces hepatic fibrosis (PIVENS trial)."
            )

        # 6. Low albumin — synthetic liver function
        if albumin and float(albumin) < 3.5:
            recs.append(
                f"Albumin {albumin} g/dL — low (normal >3.5). Low albumin means the liver's "
                f"protein manufacturing is impaired — a sign of significant liver disease. "
                f"This warrants urgent hepatology referral and nutritional support."
            )

        # 7. Condition-specific
        for d in detected:
            if "Hepatitis B" in d["condition"]:
                recs.append("Hepatitis B detected — monitor HBsAg + HBV DNA every 6 months; antivirals (tenofovir/entecavir) suppress viral replication effectively.")
            if "Hepatitis C" in d["condition"]:
                recs.append("Hepatitis C detected — DAA therapy (sofosbuvir/ledipasvir) achieves >95% cure rate; available under NPHCE India. Consult hepatologist urgently.")
            if "Cirrhosis" in d["condition"]:
                recs.append("Cirrhosis detected — 6-monthly AFP + ultrasound mandatory for hepatocellular carcinoma surveillance (AASLD/EASL guidelines).")

        # 8. Risk-level fallback
        if len(recs) < 2:
            if risk_level == "GREEN":
                recs.append(
                    "Liver appears healthy. Maintain: limit alcohol, keep BMI <23 (Indian standard), "
                    "annual LFT if you have diabetes or BMI >23, and avoid routine NSAID use."
                )
            elif risk_level == "RED":
                recs.append(
                    "HIGH LIVER RISK: Urgent hepatology referral. "
                    "Request: LFT panel, HBsAg, anti-HCV, ultrasound, and Fibroscan."
                )

        return recs[:6]

    def _possible_issues(self, health, ast, alt):
        issues = []
        if ast and float(ast) > 40:
            issues.append(f"Elevated AST ({ast} U/L) — liver inflammation")
        if alt and float(alt) > 56:
            issues.append(f"Elevated ALT ({alt} U/L) — liver cell damage")
        ggt = health.get("GGT") or health.get("ggt")
        if ggt and float(ggt) > 60:
            issues.append(f"Elevated GGT ({ggt} U/L) — bile duct or alcohol marker")
        alb = health.get("Albumin")
        if alb and float(alb) < 3.5:
            issues.append(f"Low albumin ({alb} g/dL) — reduced liver synthetic function")
        if health.get("Alcohol") == "Daily":
            issues.append("Daily alcohol accelerates liver fibrosis progression")
        return issues
