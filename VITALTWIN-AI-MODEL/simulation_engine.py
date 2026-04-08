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
from utils.input_validator import validate_inputs
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
        overall_score = self._calculate_overall_score(organ_results)
        vital = self.vital_score.calculate(
            overall_score,
            self._get_trend_data(future)
        )

        # ── Feature: What-If (optional) ───────────────────────────────────────
        what_if_results = None
        if include_what_if:
            what_if_results = self.what_if.simulate(
                safe_data,
                {'overall_health_score': overall_score, 'biological_age': bio_age, 'organs': organ_results}
            )

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

    def _load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except Exception:
            return {}


# Backward-compatible wrapper
def run_simulation(user_data):
    return VitalTwinSimulator().run_simulation(user_data)
