# features/vital_score.py
# Vital Score — clinically weighted aggregate of 5 organ health scores.
#
# Weighting rationale:
#   Heart   30% — leading cause of death globally (WHO 2023); strongest mortality predictor
#   Brain   20% — stroke + dementia combined = #2 cause of death/disability
#   Kidney  20% — silent progression; once lost, irreversible (KDIGO 2022)
#   Liver   15% — significant disease often asymptomatic until late stage
#   Lungs   15% — COPD / lung disease; strong quality-of-life impact
#
# RED organ penalty:
#   Any single organ at RED (score < 40) applies a hard floor penalty to the
#   overall vital score. A user cannot have a "Good" vital score while one organ
#   is in critical range — this would be clinically misleading.
#
#   Penalty formula (per RED organ):
#     floor = max(floor, RED_organ_score * organ_weight * RED_DRAG_FACTOR)
#   RED_DRAG_FACTOR = 2.5 — empirically chosen so a single RED organ (score ~30)
#   with 30% weight pulls the overall score below 60 (out of "Good" category).
#
# References:
#   GBD 2019 — global cause-of-death rankings
#   KDIGO 2022 CKD guidelines — irreversibility of kidney function loss
#   WHO Global Health Estimates 2023

# Organ weights must sum to 1.0
ORGAN_WEIGHTS = {
    'heart':  0.30,
    'brain':  0.20,
    'kidney': 0.20,
    'liver':  0.15,
    'lungs':  0.15,
}

# A score below this threshold classifies an organ as RED
RED_THRESHOLD = 40

# How hard a RED organ drags down the total score.
# A RED organ (score ~30) with weight 0.30 → floor = 30 * 0.30 * 2.5 = 22.5
# meaning overall score cannot exceed ~45 when heart is RED.
RED_DRAG_FACTOR = 2.5


class VitalScoreGauge:
    """
    Clinically weighted vital score (0–100).

    Replaces the naive simple-average that allowed a RED heart to average
    out with healthy other organs into a misleadingly "Good" result.
    """

    def calculate(self, organ_results: dict, trend_data=None) -> dict:
        """
        Args:
            organ_results: dict of {organ_name: {'health_score': int, 'risk_level': str}}
            trend_data:    list of past vital scores (optional, for trend)

        Returns:
            Full vital score dict consumed by the frontend.
        """
        weighted_score, red_organs, missing = self._weighted_score(organ_results)
        penalised_score  = self._apply_red_penalty(weighted_score, organ_results)
        final_score      = round(max(0, min(100, penalised_score)))

        category, color, message = self._classify(final_score)
        trend         = self._calculate_trend(trend_data)        if trend_data else "stable"
        trend_percent = self._calculate_trend_percent(trend_data) if trend_data else 0

        return {
            'current':       final_score,
            'category':      category,
            'color':         color,
            'message':       message,
            'trend':         trend,
            'trend_percent': trend_percent,
            'red_organs':    red_organs,
            'gauge': {
                'value': final_score,
                'min':   0,
                'max':   100,
                'segments': [
                    {'from':  0, 'to': 39, 'color': '#EF4444', 'label': 'Critical'},
                    {'from': 40, 'to': 59, 'color': '#F59E0B', 'label': 'Fair'},
                    {'from': 60, 'to': 79, 'color': '#10B981', 'label': 'Good'},
                    {'from': 80, 'to': 100,'color': '#059669', 'label': 'Excellent'},
                ],
                'current_segment': self._get_segment(final_score),
                'needle': {'value': final_score, 'color': '#1E293B'},
            },
            'organ_contributions': self._contributions(organ_results),
            'interpretation': self._interpretation(final_score, red_organs),
        }

    # ── Core calculation ──────────────────────────────────────────────────────

    def _weighted_score(self, organ_results: dict):
        """Weighted average of organ health scores.

        Uncertainty penalty:
          When an organ uses rule_based (no labs) its score may be unrealistically
          high because it is only as reliable as the population average.
          We apply a cap of 80 for rule_based organs and 85 for partial-lab organs,
          so a score of 97 with zero clinical data doesn't inflate the vital score.
          Organs with real lab data (ckd_epi_egfr, framingham_pce, etc.) are
          not penalised — their score is the best available estimate.
        """
        # Methods that carry genuine lab-grounded confidence
        # These are based on validated clinical equations with real patient data
        HIGH_CONF_KEYWORDS = (
            'framingham_pce', 'ckd_epi', 'reported_egfr',
            'fib4', 'apri', 'nafld', 'apollo_ckd_india_ml',
            'gold_spirometry', 'absolute_override',
        )
        # Methods that use clinical formulas but without all required lab inputs
        MED_CONF_KEYWORDS = (
            'caide_interstroke', 'framingham_partial', 'framingham_point',
            'interheart', 'heart_ml_v2',
        )
        # Methods that are purely heuristic / lifestyle-based with no real labs
        LOW_CONF_KEYWORDS = ('rule_based',)
        # Semi-heuristic methods (smoking category, AQI lookup, etc.)
        HEURISTIC_KEYWORDS = ('smoking-category', 'heuristic', 'city aqi')

        total_weight = 0.0
        weighted_sum = 0.0
        red_organs   = []
        missing      = []

        for organ, weight in ORGAN_WEIGHTS.items():
            result = organ_results.get(organ)
            if not isinstance(result, dict) or 'health_score' not in result:
                missing.append(organ)
                # Missing organ: use conservative population average (65)
                weighted_sum += 65 * weight
                total_weight += weight
                continue

            score  = float(result['health_score'])
            method = str(result.get('method_used', '')).lower()

            # Apply uncertainty caps based on method quality:
            # The cap prevents unrealistically high scores when we have no real data.
            # Clinical rationale: a person with no lab results could have hidden disease —
            # we cannot responsibly say they are "Excellent" with zero objective data.
            if any(kw in method for kw in LOW_CONF_KEYWORDS):
                # Pure rule_based (no labs at all): cap at 78
                # Represents: "We think you're probably OK, but we can't confirm it"
                score = min(score, 72)
            elif any(kw in method for kw in HEURISTIC_KEYWORDS):
                # Smoking-category / AQI heuristics: cap at 78
                score = min(score, 78)
            elif any(kw in method for kw in MED_CONF_KEYWORDS):
                # Clinical formulas without full labs: cap at 85
                score = min(score, 85)
            # HIGH_CONF_KEYWORDS: no cap — lab-based result is the best estimate

            weighted_sum += score * weight
            total_weight += weight

            if score < RED_THRESHOLD or result.get('risk_level') == 'RED':
                red_organs.append(organ)

        if total_weight == 0:
            return 60.0, [], missing

        return weighted_sum / total_weight, red_organs, missing

    def _apply_red_penalty(self, weighted_score: float, organ_results: dict) -> float:
        """
        For each RED organ, compute a ceiling on the overall score.
        The sickest organ's contribution limits how high the total can go.
        This prevents "averaging away" a critical organ finding.
        """
        score = weighted_score

        for organ, weight in ORGAN_WEIGHTS.items():
            result = organ_results.get(organ)
            if not isinstance(result, dict):
                continue

            organ_score = float(result.get('health_score', 60))
            risk_level  = result.get('risk_level', 'GREEN')

            if organ_score < RED_THRESHOLD or risk_level == 'RED':
                # Hard ceiling: overall cannot exceed (organ_score + penalty_headroom)
                # Example: heart score=25, weight=0.30
                #   ceiling = 25 + (100 - 25) * (1 - 0.30 * RED_DRAG_FACTOR)
                #           = 25 + 75 * 0.25 = 43.75  → overall capped at 43
                penalty_headroom = (100 - organ_score) * (1 - weight * RED_DRAG_FACTOR)
                ceiling = organ_score + max(0, penalty_headroom)
                score = min(score, ceiling)

        return score

    # ── Classification ────────────────────────────────────────────────────────

    def _classify(self, score: int):
        if score >= 80:
            return "Excellent", "GREEN",  "Your overall health is excellent. Maintain your current habits."
        elif score >= 60:
            return "Good",      "GREEN",  "Good overall health. Some areas have room for improvement."
        elif score >= 40:
            return "Fair",      "YELLOW", "Moderate health concerns detected. Lifestyle changes recommended."
        elif score >= 20:
            return "Poor",      "RED",    "Significant health risks present. Consult a doctor soon."
        else:
            return "Critical",  "RED",    "Critical health status. Seek medical attention immediately."

    def _interpretation(self, score: int, red_organs: list) -> str:
        base = {
            range(80, 101): "Your vital signs are excellent across all organs.",
            range(60, 80):  "You're doing well overall, but a few areas need attention.",
            range(40, 60):  "Several health markers need attention. Focus on lifestyle changes.",
            range(20, 40):  "Significant health risks detected. Consult healthcare providers.",
            range(0, 20):   "Critical health status. Immediate medical attention recommended.",
        }
        text = next((v for k, v in base.items() if score in k), "")
        if red_organs:
            organs_str = ", ".join(o.capitalize() for o in red_organs)
            text += f" Critical risk detected in: {organs_str}."
        return text

    # ── Contributions breakdown ───────────────────────────────────────────────

    def _contributions(self, organ_results: dict) -> list:
        out = []
        for organ, weight in ORGAN_WEIGHTS.items():
            result = organ_results.get(organ, {})
            score  = float(result.get('health_score', 60)) if isinstance(result, dict) else 60
            out.append({
                'organ':       organ,
                'weight_pct':  round(weight * 100),
                'score':       round(score),
                'contribution': round(score * weight, 1),
                'risk_level':  result.get('risk_level', 'GREEN') if isinstance(result, dict) else 'UNKNOWN',
            })
        return sorted(out, key=lambda x: x['contribution'])

    # ── Trend helpers ─────────────────────────────────────────────────────────

    def _calculate_trend(self, trend_data: list) -> str:
        if not trend_data or len(trend_data) < 2:
            return "stable"
        delta = trend_data[-1] - trend_data[0]
        if delta > 5:   return "improving"
        if delta < -5:  return "declining"
        return "stable"

    def _calculate_trend_percent(self, trend_data: list) -> float:
        if not trend_data or len(trend_data) < 2 or trend_data[0] == 0:
            return 0.0
        return round(((trend_data[-1] - trend_data[0]) / trend_data[0]) * 100, 1)

    def _get_segment(self, score: int) -> dict:
        if score >= 80:   return {'color': '#059669', 'label': 'Excellent'}
        elif score >= 60: return {'color': '#10B981', 'label': 'Good'}
        elif score >= 40: return {'color': '#F59E0B', 'label': 'Fair'}
        else:             return {'color': '#EF4444', 'label': 'Critical'}
