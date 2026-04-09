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

        # Strategy 2: ML ensemble (Turkish NASH 60% + ILPD Indian 40%)
        turkish_ml = None
        ilpd_ml    = None
        if self.model is not None and ast and alt:
            fv = self._extract_features(data, ast, alt, ggt, glucose, hba1c, albumin)
            if fv is not None:
                turkish_ml = self.predict_risk(fv)

        if ast and alt:
            ilpd_ml = self._ilpd_risk(data, age, bmi, ast, alt, albumin)

        # ── NHANES signal (9,473 rows, AUC 0.900) ────────────────────────────
        # Source: CDC NHANES — age, gender, albumin, AST/ALT ratio
        # Target: Liver_Risk_Score >= 2 (moderate-high disease, ~15% prevalence)
        nhanes_ml = None
        nhb = self._nhanes_bundle
        if nhb is not None and albumin:
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
        lpd_ml = None
        lpd_b  = self._lpd_bundle
        if lpd_b is not None and alt:
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
                lpd_ml = float(lpd_b['model'].predict_proba([fv_lpd])[0][1])
            except Exception:
                lpd_ml = None

        # ── Multi-model ensemble: Turkish + ILPD + LPD + NHANES ─────────────
        # Weights: Turkish 30% (biopsy-confirmed NASH), ILPD 20% (India 583),
        #          LPD 35% (India 30K, highest N), NHANES 15% (CDC 9K, demographics)
        # NHANES uses only age/gender/albumin/AST:ALT — available even without full labs
        n_models = sum(x is not None for x in [turkish_ml, ilpd_ml, lpd_ml, nhanes_ml])
        if n_models >= 3 and lpd_ml is not None:
            if turkish_ml is not None and ilpd_ml is not None and nhanes_ml is not None:
                combined_ml = 0.30*turkish_ml + 0.20*ilpd_ml + 0.35*lpd_ml + 0.15*nhanes_ml
                ml_tag = "turkish_ilpd_lpd_nhanes"
            elif nhanes_ml is not None:
                combined_ml = 0.38*turkish_ml + 0.24*ilpd_ml + 0.38*lpd_ml if (turkish_ml and ilpd_ml) else 0.50*lpd_ml + 0.50*nhanes_ml
                ml_tag = "lpd_nhanes_ensemble"
            else:
                combined_ml = 0.35*turkish_ml + 0.25*ilpd_ml + 0.40*lpd_ml if (turkish_ml and ilpd_ml) else lpd_ml
                ml_tag = "turkish_ilpd_lpd"
            if base_risk is not None:
                base_risk   = 0.60 * base_risk + 0.40 * combined_ml
                method_used = f"fib4_{ml_tag}_ensemble"
            else:
                base_risk   = combined_ml
                method_used = f"{ml_tag}_ensemble"
        elif turkish_ml is not None and ilpd_ml is not None:
            combined_ml = 0.60 * turkish_ml + 0.40 * ilpd_ml
            if nhanes_ml is not None:
                combined_ml = 0.50*turkish_ml + 0.30*ilpd_ml + 0.20*nhanes_ml
                ml_tag = "turkish_ilpd_nhanes"
            else:
                ml_tag = "turkish_ilpd"
            if base_risk is not None:
                base_risk   = 0.60 * base_risk + 0.40 * combined_ml
                method_used = f"fib4_{ml_tag}_ensemble"
            else:
                base_risk   = combined_ml
                method_used = f"{ml_tag}_ensemble"
        elif turkish_ml is not None:
            if base_risk is not None:
                base_risk   = 0.60 * base_risk + 0.40 * turkish_ml
                method_used = "fib4_ml_ensemble"
            else:
                base_risk   = turkish_ml
                method_used = "ml_model_turkish"
        elif ilpd_ml is not None:
            if base_risk is not None:
                base_risk   = 0.65 * base_risk + 0.35 * ilpd_ml
                method_used = "fib4_ilpd_ensemble"
            else:
                base_risk   = ilpd_ml
                method_used = "ml_model_ilpd_indian"
        elif nhanes_ml is not None and base_risk is None:
            base_risk   = nhanes_ml
            method_used = "nhanes_ml_only"

        # Strategy 3: NAFLD-LFS
        if base_risk is None:
            lfs_score = nafld_lfs(has_mets, diabetic, ast_alt, bmi)
            if lfs_score is not None:
                base_risk   = 0.32 if lfs_score > -0.64 else 0.10
                method_used = "nafld_lfs"

        # Strategy 4: rule-based
        if base_risk is None:
            base_risk   = self._rule_based(health, profile)
            method_used = "rule_based"

        # ── India-specific: Lean NAFLD check ─────────────────────────────────
        # Source: Duseja A et al., J Clin Exp Hepatol 2015;5:S9-S16
        # BMI<23 + ALT>40 → elevated risk (would be missed by standard BMI screening)
        is_lean_nafld, lean_nafld_penalty, lean_nafld_note = self._lean_nafld_check(bmi, alt)

        # Penalties
        alcohol_penalty  = {"Daily":0.28,"Weekly":0.10,"Occasional":0.03,"Never":0.0}.get(alcohol, 0.0)
        ggt_penalty      = 0.0
        if ggt:
            g = float(ggt)
            if g > 100:  ggt_penalty = 0.12
            elif g > 60: ggt_penalty = 0.07
            elif g > 48: ggt_penalty = 0.03
        albumin_penalty  = 0.15 if (albumin and float(albumin) < 3.5) else 0.0

        final_risk = min(1.0, base_risk + condition_risk * 0.4 +
                         alcohol_penalty + ggt_penalty + albumin_penalty + lean_nafld_penalty)

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
        base = {
            "GREEN":  ["Limit alcohol to <14 units/week (men), <7 units/week (women)",
                       "Maintain BMI 18.5-22.9 (Indian cutoffs)",
                       "Annual liver function test if BMI > 23 or diabetes present"],
            "YELLOW": ["Get LFT panel done: AST, ALT, GGT, albumin, bilirubin",
                       "Reduce alcohol to occasional or eliminate",
                       "7-10% weight loss reduces hepatic fat by 50% in NAFLD",
                       "Avoid paracetamol >2g/day; NSAIDs can worsen liver disease"],
            "RED":    ["URGENT: Consult gastroenterologist or hepatologist",
                       "Fibroscan or biopsy may be recommended to stage fibrosis",
                       "Eliminate alcohol completely — worsens fibrosis at any amount",
                       "6-monthly ultrasound + AFP for cirrhosis surveillance"],
        }.get(risk_level, [])
        extras = []
        for d in detected:
            if "Hepatitis B" in d["condition"]:
                extras.append("Monitor HBsAg + HBV DNA every 6 months; discuss antivirals")
            if "Hepatitis C" in d["condition"]:
                extras.append("DAA therapy achieves >95% cure — consult hepatologist urgently")
            if "Cirrhosis" in d["condition"]:
                extras.append("6-monthly AFP + ultrasound for hepatocellular carcinoma screening")
        if health.get("Alcohol") == "Daily":
            extras.append("Daily alcohol: most modifiable liver risk — discuss cessation support")
        return (base + extras)[:6]

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
