# simulation_engine.py
# Orchestrates the full prediction pipeline with 4 verification layers:
#   Layer 1 — Input validation (input_validator.py)
#   Layer 2 — Confidence scoring (confidence_scorer.py)
#   Layer 3 — Cross-organ consistency checks (consistency_checker.py)
#   Layer 4 — Medication effect modeling (medication_modeler.py)

import json
from datetime import datetime

# Organ models
from models.heart_model import HeartModel
from models.brain_model import BrainModel
from models.liver_model import LiverModel
from models.kidney_model import KidneyModel
from models.lungs_model import LungsModel

# Feature engines
from features.biological_age import BiologicalAgeEngine
from features.future_self import FutureSelfSimulator
from features.stress_heatmap import BodyStressHeatmap
from features.vital_score import VitalScoreGauge
from features.what_if_simulator import WhatIfSimulator

# Verification layers
from utils.clinical_inference import enrich_health_data
from utils.input_validator import validate_inputs
from utils.input_completeness import score_all_organs as score_input_completeness
from utils.confidence_scorer import score_all_organs, overall_confidence
from utils.consistency_checker import run_consistency_checks
from utils.medication_modeler import apply_medication_effects, detect_drug_classes


class VitalTwinSimulator:
    """
    VitalTwin Simulation Engine v3.0
    Clinically-grounded organ models + 4 verification layers.
    """

    def __init__(self, config=None):
        self.config = config or self._load_config()

        self.models = {
            'heart':  HeartModel(),
            'brain':  BrainModel(),
            'liver':  LiverModel(),
            'kidney': KidneyModel(),
            'lungs':  LungsModel(),
        }

        self.biological_age = BiologicalAgeEngine(self.config.get('biological_age', {}))
        self.future_self    = FutureSelfSimulator()
        self.stress_heatmap = BodyStressHeatmap()
        self.vital_score    = VitalScoreGauge()
        self.what_if        = WhatIfSimulator(self)

    def run_simulation(self, user_data, include_what_if=True):
        """
        Run complete health simulation.

        Pipeline:
          1. Validate + sanitize inputs          (Layer 1)
          2. Score confidence per organ          (Layer 2 — pre-model)
          3. Run all 5 organ models
          4. Apply medication effects            (Layer 4)
          5. Apply cross-organ consistency rules (Layer 3)
          6. Attach final confidence to results  (Layer 2 — post-model)
          7. Run feature engines (bio age, heatmap, future, vital score)
          8. Assemble and return output
        """
        profile = user_data.get('ProfileInfo', {})
        health  = user_data.get('HealthInfo', {})
        medications = health.get('Medications', []) or []

        # ── Layer 1: Input Validation ─────────────────────────────────────────
        validation = validate_inputs(profile, health)
        # Use sanitized health (hard-error fields set to None) downstream
        safe_health = validation['sanitized_health']

        # ── Layer 1b: Clinical Inference (no new inputs needed) ──────────────
        # Enriches safe_health with inferred pack-years, waist circumference,
        # BP from hypertension conditions, and HbA1c from diabetes conditions.
        safe_health = enrich_health_data(safe_health, profile)

        safe_data   = {**user_data, 'HealthInfo': safe_health}

        # ── Layer 2: Pre-model confidence scoring ────────────────────────────
        organ_confidences = score_all_organs(safe_health, profile)

        # ── Step 3: Run organ models ──────────────────────────────────────────
        organ_results = {}
        for organ_name, model in self.models.items():
            try:
                organ_results[organ_name] = model.calculate_risk(safe_data)
            except Exception as e:
                # Graceful degradation: return a marked low-confidence result
                organ_results[organ_name] = {
                    'current_risk':    0.30,
                    'risk_level':      'YELLOW',
                    'health_score':    70,
                    'metrics':         {},
                    'risk_progression':[],
                    'recommendations': [f"Data insufficient for {organ_name} analysis — consult physician"],
                    'model_confidence':0.20,
                    'method_used':     'error_fallback',
                    'possible_issues': [f"Model error: {str(e)[:120]}"],
                }

        # ── Layer 4: Medication effects ───────────────────────────────────────
        med_audit = apply_medication_effects(medications, organ_results, safe_health)

        # ── Layer 3: Cross-organ consistency ──────────────────────────────────
        consistency_audit = run_consistency_checks(safe_health, organ_results)

        # ── Layer 2 (post): Attach confidence to each organ result ────────────
        for organ, conf in organ_confidences.items():
            if organ in organ_results and isinstance(organ_results[organ], dict):
                # Blend: model's own confidence (method-based) vs input-based confidence
                model_conf = organ_results[organ].get('model_confidence', 0.55)
                blended = round(0.5 * model_conf + 0.5 * conf['score'], 3)
                organ_results[organ]['model_confidence'] = blended
                organ_results[organ]['data_confidence'] = conf

        # ── Feature: Biological Age (KDM) ─────────────────────────────────────
        bio_age = self.biological_age.calculate(
            real_age=profile.get('Age', 30),
            organ_results=organ_results,
            health_info=safe_health,
            profile_info=profile,
        )

        # ── Feature: Stress Heatmap ───────────────────────────────────────────
        heatmap = self.stress_heatmap.calculate(organ_results, safe_health, profile)

        # ── Feature: Future Self Timeline ─────────────────────────────────────
        future = self.future_self.simulate(safe_data, organ_results, safe_health, bio_age)

        # ── Feature: Vital Score Gauge ────────────────────────────────────────
        # Pass full organ_results so weighted scoring + RED penalty can apply.
        # overall_score kept for backward-compat fields.
        overall_score = self._calculate_overall_score(organ_results)
        vital = self.vital_score.calculate(
            organ_results,
            self._get_trend_data(future)
        )

        # ── Feature: What-If (optional) ───────────────────────────────────────
        what_if_results = None
        if include_what_if:
            what_if_results = self.what_if.simulate(
                safe_data,
                {'overall_health_score': vital.get('current', overall_score), 'biological_age': bio_age, 'organs': organ_results}
            )

        # ── Input completeness scoring ────────────────────────────────────────
        input_completeness = score_input_completeness(safe_data)

        # ── Enrich organ results with score_reason + factors ─────────────────
        self._enrich_organ_reasons(organ_results, safe_health, profile)

        # ── Priority recommendations ──────────────────────────────────────────
        priorities = self._get_priority_recommendations(organ_results, bio_age)

        # ── Overall confidence ────────────────────────────────────────────────
        report_confidence = overall_confidence(organ_confidences)

        # ── Build output ──────────────────────────────────────────────────────
        output = {
            'user_id':           profile.get('Userid', 'UNKNOWN'),
            'simulation_date':   datetime.utcnow().isoformat() + 'Z',

            # Core report fields
            'vital_score':       vital,
            'biological_age':    bio_age,
            'body_stress':       heatmap,
            'future_self':       future,
            'organs':            organ_results,
            'overall_health_score': overall_score,
            'priority_recommendations': priorities,

            # Verification layer audits (useful for debugging / UI trust indicator)
            'report_confidence': report_confidence,
            'system_confidence': report_confidence['score'],
            'verification': {
                'input_validation': {
                    'valid':         validation['valid'],
                    'errors':        validation['errors'],
                    'warnings':      validation['warnings'],
                },
                'medication_effects': med_audit,
                'consistency_adjustments': consistency_audit,
                'drug_classes_detected': detect_drug_classes(medications),
            },
            'clinical_methods': {
                organ: results.get('method_used', 'unknown')
                for organ, results in organ_results.items()
                if isinstance(results, dict)
            },
            'input_completeness': input_completeness,
        }

        if what_if_results:
            output['what_if_simulations'] = what_if_results

        return output

    def simulate_lifestyle_change(self, user_data, changes):
        return self.what_if.simulate_custom(user_data, changes)

    def _calculate_overall_score(self, organ_results):
        scores = [
            o['health_score']
            for o in organ_results.values()
            if isinstance(o, dict) and 'health_score' in o
        ]
        return round(sum(scores) / len(scores)) if scores else 70

    def _get_trend_data(self, future):
        try:
            return [point['vitality_score'] for point in future['timeline']]
        except (KeyError, TypeError):
            return []

    def _get_priority_recommendations(self, organ_results, bio_age):
        priorities = []

        if bio_age.get('age_gap', 0) > 7:
            priorities.append({
                'priority': 'CRITICAL',
                'category': 'biological_age',
                'action':   'Immediate lifestyle intervention needed — biological age significantly elevated',
                'impact':   'Could reduce biological age by 5–7 years with sustained changes',
            })

        for organ, result in organ_results.items():
            if not isinstance(result, dict):
                continue
            level = result.get('risk_level', 'GREEN')
            recs  = result.get('recommendations', [])

            if level == 'RED':
                priorities.append({
                    'priority': 'HIGH',
                    'category': organ,
                    'action':   recs[0] if recs else f"Consult {organ} specialist urgently",
                    'impact':   'Critical — address within 1 month',
                    'confidence': result.get('model_confidence', 0.55),
                })
            elif level == 'YELLOW' and len(priorities) < 5:
                priorities.append({
                    'priority': 'MEDIUM',
                    'category': organ,
                    'action':   recs[0] if recs else f"Monitor {organ} health",
                    'impact':   'Moderate — address within 3 months',
                    'confidence': result.get('model_confidence', 0.55),
                })

        return priorities[:5]

    def _enrich_organ_reasons(self, organ_results, health, profile):
        """
        Populate score_reason (string) and factors (list) for each organ
        so the UI can show 'Why this score' and 'Main causes / protectors'.
        Built entirely from data already computed by the organ models.
        """
        smoking  = str(health.get('Smoking') or 'Never')
        alcohol  = str(health.get('Alcohol') or 'Never')
        stress   = str(health.get('Stress') or 'Low')
        sleep    = float(health.get('Sleep') or 7)
        _bmi_raw = health.get('Bmi') or profile.get('Bmi')
        if not _bmi_raw:
            _h = float(profile.get('Height') or profile.get('height') or 0)
            _w = float(profile.get('Weight') or profile.get('weight') or 0)
            _bmi_raw = round(_w / ((_h / 100) ** 2), 1) if _h > 0 and _w > 0 else 25
        bmi      = float(_bmi_raw)
        age      = int(profile.get('Age') or profile.get('age') or 30)
        activity = str(profile.get('ActivityLevel') or profile.get('activity') or 'Moderate')
        diet     = str(profile.get('Diet') or profile.get('diet') or 'Average')
        conditions = [c.lower() for c in (health.get('MedicalConditions') or health.get('medical_conditions') or [])]

        def _smoking_factor():
            if smoking == 'Daily':   return {'factor': 'Daily smoking',    'impact': 'negative', 'detail': 'raises risk significantly'}
            if smoking == 'Occasional': return {'factor': 'Occasional smoking', 'impact': 'negative', 'detail': 'moderate risk elevation'}
            return {'factor': 'Non-smoker', 'impact': 'positive', 'detail': 'lowers risk'}

        def _alcohol_factor():
            if alcohol == 'Daily':   return {'factor': 'Daily alcohol use',   'impact': 'negative', 'detail': 'stresses multiple organs'}
            if alcohol == 'Weekly':  return {'factor': 'Weekly alcohol use',  'impact': 'negative', 'detail': 'moderate load'}
            return {'factor': 'Low/no alcohol', 'impact': 'positive', 'detail': 'protective'}

        def _bmi_factor():
            if bmi >= 30:  return {'factor': f'BMI {bmi:.1f} (Obese)',      'impact': 'negative', 'detail': 'increases organ load'}
            if bmi >= 25:  return {'factor': f'BMI {bmi:.1f} (Overweight)', 'impact': 'negative', 'detail': 'mild risk elevation'}
            return          {'factor': f'BMI {bmi:.1f} (Healthy)',          'impact': 'positive', 'detail': 'healthy weight range'}

        def _stress_factor():
            if stress in ('High', 'Very High'): return {'factor': f'{stress} stress', 'impact': 'negative', 'detail': 'chronic stress raises cortisol'}
            if stress == 'Medium': return {'factor': 'Moderate stress', 'impact': 'neutral', 'detail': 'manageable levels'}
            return {'factor': 'Low stress', 'impact': 'positive', 'detail': 'protective for all organs'}

        def _sleep_factor():
            if sleep < 6:  return {'factor': f'{sleep:.0f}h sleep (insufficient)', 'impact': 'negative', 'detail': '<6h increases all-cause risk'}
            if sleep > 9:  return {'factor': f'{sleep:.0f}h sleep (excess)',       'impact': 'negative', 'detail': '>9h associated with higher risk'}
            return          {'factor': f'{sleep:.0f}h sleep (healthy)',             'impact': 'positive', 'detail': '7-8h is optimal'}

        def _age_factor(threshold_warn=45, threshold_high=60):
            if age >= threshold_high: return {'factor': f'Age {age} (elevated baseline)', 'impact': 'negative', 'detail': 'age is the strongest risk factor'}
            if age >= threshold_warn: return {'factor': f'Age {age} (moderate baseline)', 'impact': 'negative', 'detail': 'risk rises from age 45'}
            return {'factor': f'Age {age} (low baseline)', 'impact': 'positive', 'detail': 'younger age is protective'}

        def _activity_factor():
            if activity == 'Sedentary': return {'factor': 'Sedentary lifestyle', 'impact': 'negative', 'detail': 'inactivity is a major risk factor'}
            if activity == 'Active':    return {'factor': 'Active lifestyle',    'impact': 'positive', 'detail': '150+ min/wk exercise is protective'}
            return {'factor': 'Moderate activity', 'impact': 'positive', 'detail': 'some exercise reduces risk'}

        def _diet_factor():
            if diet == 'Poor':    return {'factor': 'Poor diet',    'impact': 'negative', 'detail': 'processed food, high sodium/fat'}
            if diet == 'Good':    return {'factor': 'Healthy diet', 'impact': 'positive', 'detail': 'diet rich in vegetables/fibre'}
            return {'factor': 'Average diet', 'impact': 'neutral', 'detail': 'room for improvement'}

        for organ, result in organ_results.items():
            if not isinstance(result, dict):
                continue
            risk     = result.get('current_risk', 0.3)
            level    = result.get('risk_level', 'GREEN')
            method   = result.get('method_used', '')
            issues   = result.get('possible_issues', [])
            detected = result.get('heart_conditions', result.get('detected_conditions', []))
            metrics  = result.get('metrics', {})

            factors = []
            reason_parts = []

            # ── Organ-specific factors ────────────────────────────────────────
            if organ == 'heart':
                factors = [
                    _age_factor(45, 60),
                    _smoking_factor(),
                    _bmi_factor(),
                    _stress_factor(),
                    _sleep_factor(),
                    _activity_factor(),
                ]
                sbp = health.get('SystolicBP') or health.get('systolic_bp')
                tc  = health.get('TotalCholesterol')
                hdl = health.get('HDLCholesterol')
                if sbp and int(float(sbp)) >= 140:
                    factors.insert(0, {'factor': f'Blood pressure {int(float(sbp))} mmHg (high)', 'impact': 'negative', 'detail': 'high BP strains the heart and raises clot risk'})
                if tc and float(tc) >= 240:
                    factors.insert(0, {'factor': f'Cholesterol {tc} mg/dL (high)', 'impact': 'negative', 'detail': 'builds up plaque in arteries over time'})
                if hdl and float(hdl) >= 60:
                    factors.insert(0, {'factor': f'Good cholesterol (HDL {hdl})', 'impact': 'positive', 'detail': 'high HDL clears bad cholesterol — protective'})
                if any('diabetes' in c for c in conditions):
                    factors.insert(0, {'factor': 'Type 2 Diabetes', 'impact': 'negative', 'detail': 'doubles heart attack risk by damaging blood vessels'})
                # Build personal reason sentence
                bad = [f['factor'] for f in factors if f['impact'] == 'negative']
                good = [f['factor'] for f in factors if f['impact'] == 'positive']
                if bad:
                    reason_parts.append(f"Your heart risk is mainly driven by: {', '.join(bad[:3])}.")
                if good:
                    reason_parts.append(f"Protective factors: {', '.join(good)}.")

            elif organ == 'brain':
                factors = [
                    _age_factor(55, 65),
                    _sleep_factor(),
                    _stress_factor(),
                    _activity_factor(),
                    _smoking_factor(),
                    _alcohol_factor(),
                ]
                _sbp_brain = health.get('SystolicBP') or health.get('systolic_bp')
                if any('hypertension' in c for c in conditions) or (_sbp_brain and int(float(_sbp_brain)) >= 140):
                    factors.insert(0, {'factor': 'Hypertension', 'impact': 'negative', 'detail': 'high BP is the #1 cause of stroke and dementia'})
                if any('diabetes' in c for c in conditions):
                    factors.insert(0, {'factor': 'Type 2 Diabetes', 'impact': 'negative', 'detail': 'high blood sugar damages brain blood vessels'})
                bad = [f['factor'] for f in factors if f['impact'] == 'negative']
                good = [f['factor'] for f in factors if f['impact'] == 'positive']
                if bad:
                    reason_parts.append(f"Your brain health is being affected by: {', '.join(bad[:3])}.")
                if good:
                    reason_parts.append(f"Positive factors: {', '.join(good)}.")

            elif organ == 'liver':
                factors = [
                    _alcohol_factor(),
                    _bmi_factor(),
                    _diet_factor(),
                    _smoking_factor(),
                    _activity_factor(),
                ]
                alt = health.get('ALT') or health.get('alt')
                ggt = health.get('GGT') or health.get('ggt')
                if alt and float(alt) > 40:
                    factors.insert(0, {'factor': f'Elevated liver enzyme (ALT {alt})', 'impact': 'negative', 'detail': 'raised ALT signals liver inflammation or fat buildup'})
                if ggt and float(ggt) > 50:
                    factors.insert(0, {'factor': f'Elevated GGT ({ggt})', 'impact': 'negative', 'detail': 'high GGT is linked to alcohol use and fatty liver'})
                bad = [f['factor'] for f in factors if f['impact'] == 'negative']
                good = [f['factor'] for f in factors if f['impact'] == 'positive']
                if bad:
                    reason_parts.append(f"Your liver is under stress due to: {', '.join(bad[:3])}.")
                if good:
                    reason_parts.append(f"Protective habits: {', '.join(good)}.")

            elif organ == 'kidney':
                factors = [
                    _bmi_factor(),
                    _activity_factor(),
                    _diet_factor(),
                ]
                cr   = health.get('SerumCreatinine') or health.get('creatinine')
                egfr = metrics.get('egfr') or health.get('eGFR')
                if any('diabetes' in c for c in conditions):
                    factors.insert(0, {'factor': 'Type 2 Diabetes', 'impact': 'negative', 'detail': 'high blood sugar damages the kidney\'s tiny filters'})
                if any('hypertension' in c for c in conditions):
                    factors.insert(0, {'factor': 'Hypertension', 'impact': 'negative', 'detail': 'high BP scars and hardens kidney vessels over time'})
                if cr:
                    cr_f = float(cr)
                    imp  = 'negative' if cr_f > 1.2 else 'positive'
                    lbl  = 'Creatinine elevated' if cr_f > 1.2 else 'Creatinine normal'
                    det  = 'wastes not being filtered efficiently' if cr_f > 1.2 else 'kidneys are clearing waste well'
                    factors.insert(0, {'factor': f'{lbl} ({cr_f:.2f} mg/dL)', 'impact': imp, 'detail': det})
                if egfr:
                    egfr_f = float(egfr)
                    imp    = 'positive' if egfr_f >= 60 else 'negative'
                    lbl    = 'Good filtration rate' if egfr_f >= 60 else 'Low filtration rate'
                    det    = 'kidneys filtering at a healthy pace' if egfr_f >= 60 else 'kidneys not filtering enough — watch this'
                    factors.insert(0, {'factor': f'{lbl} (eGFR {egfr_f:.0f})', 'impact': imp, 'detail': det})
                bad  = [f['factor'] for f in factors if f['impact'] == 'negative']
                good = [f['factor'] for f in factors if f['impact'] == 'positive']
                if bad:
                    reason_parts.append(f"Your kidneys are being stressed by: {', '.join(bad[:3])}.")
                if good:
                    reason_parts.append(f"Positive factors: {', '.join(good)}.")

            elif organ == 'lungs':
                factors = [
                    _smoking_factor(),
                    _activity_factor(),
                    _age_factor(50, 65),
                ]
                city = profile.get('City', '')
                if city:
                    imp = 'negative' if risk > 0.3 else 'neutral'
                    factors.append({'factor': f'Air quality in {city}', 'impact': imp, 'detail': 'pollution adds to lung inflammation over years'})
                if any('tb' in c or 'tuberculosis' in c for c in conditions):
                    factors.insert(0, {'factor': 'History of TB', 'impact': 'negative', 'detail': 'TB scars the lung tissue and reduces capacity'})
                bad  = [f['factor'] for f in factors if f['impact'] == 'negative']
                good = [f['factor'] for f in factors if f['impact'] == 'positive']
                if bad:
                    reason_parts.append(f"Your lung health is being impacted by: {', '.join(bad[:3])}.")
                if good:
                    reason_parts.append(f"What's working for you: {', '.join(good)}.")

            # ── Build score_reason string (personal, human-readable) ──────────
            primary = " ".join(reason_parts).strip()
            if not primary:
                bad_f  = [f['factor'] for f in factors if f['impact'] == 'negative']
                good_f = [f['factor'] for f in factors if f['impact'] == 'positive']
                if level == 'GREEN':
                    if good_f:
                        primary = f"Your {organ} is in good shape. Key protective factors: {', '.join(good_f[:3])}."
                    else:
                        primary = f"Your {organ} risk factors are all within a healthy range — keep it up."
                elif level == 'YELLOW':
                    if bad_f:
                        primary = f"Your {organ} shows moderate risk. Main areas to improve: {', '.join(bad_f[:3])}."
                    else:
                        primary = f"Your {organ} shows moderate risk — some lifestyle changes would help."
                else:
                    if bad_f:
                        primary = f"Your {organ} risk is high. The biggest contributors are: {', '.join(bad_f[:3])}."
                    else:
                        primary = f"Your {organ} risk is elevated — please consult a specialist."

            result['score_reason'] = primary
            result['factors'] = factors[:6]   # cap at 6 for clean UI

    def _load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except Exception:
            return {}


# Backward-compatible wrapper
def run_simulation(user_data):
    return VitalTwinSimulator().run_simulation(user_data)
