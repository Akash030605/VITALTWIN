# utils/medication_modeler.py
# Layer 4: Medication effect modeling — finally uses Medications[] to adjust organ risks.
# Until now medications were silently discarded. This module:
#   1. Detects drug classes from free-text medication names
#   2. Applies evidence-based risk reductions per organ
#   3. Detects drug-organ interactions that INCREASE risk
#   4. Returns a structured audit trail
#
# Evidence base:
#   Statins (heart): CTT Collaboration, Lancet 2010 — 22% RRR per mmol/L LDL reduction
#   ACE inhibitors (kidney): Jafar et al. Ann Int Med 2001 — 30% CKD progression reduction
#   Metformin (heart): UKPDS 34, Lancet 1998 — 39% MI reduction in T2DM
#   Beta-blockers (heart): Ko et al. JAMA 2004 — 34% mortality reduction post-MI
#   NSAIDs (kidney): Zhang et al. KI 2008 — 58% higher AKI risk
#   Calcineurin inhibitors (kidney): Naesens et al. CJASN 2009 — nephrotoxicity
#   Alcohol + hepatotoxics (liver): FDA labeling; Larson et al. Hepatology 2005

from typing import Optional

# ── Drug class detection patterns ─────────────────────────────────────────────
# Each entry: (class_name, [substring patterns], organ_effects)
# organ_effects: {organ: (multiplier, direction, evidence_note)}
#   multiplier: fraction to multiply current_risk by (e.g. 0.80 = 20% reduction)
#   direction: 'reduce' or 'increase'

DRUG_CLASSES = [
    # ── Cardioprotective ──────────────────────────────────────────────────────
    {
        'class': 'Statin',
        'patterns': [
            'statin', 'atorvastatin', 'rosuvastatin', 'simvastatin',
            'lovastatin', 'pravastatin', 'fluvastatin', 'pitavastatin',
        ],
        'effects': {
            'heart': ('reduce', 0.80, 'Statins: 22% RRR per mmol/L LDL drop (CTT 2010)'),
            'brain':  ('reduce', 0.88, 'Statins: 16% stroke risk reduction (CTT 2010)'),
        }
    },
    {
        'class': 'ACE Inhibitor',
        'patterns': [
            'ace inhibitor', 'ramipril', 'enalapril', 'lisinopril',
            'perindopril', 'captopril', 'quinapril', 'trandolapril',
        ],
        'effects': {
            'heart':  ('reduce', 0.84, 'ACE-I: 23% CV event reduction (HOPE trial)'),
            'kidney': ('reduce', 0.82, 'ACE-I: 30% CKD progression reduction (Jafar 2001)'),
        }
    },
    {
        'class': 'ARB',
        'patterns': [
            'arb', 'losartan', 'valsartan', 'telmisartan', 'olmesartan',
            'irbesartan', 'candesartan', 'azilsartan',
        ],
        'effects': {
            'heart':  ('reduce', 0.86, 'ARB: comparable to ACE-I for CV protection (ONTARGET)'),
            'kidney': ('reduce', 0.84, 'ARB: 20–25% CKD progression reduction (RENAAL/IDNT)'),
        }
    },
    {
        'class': 'Beta-Blocker',
        'patterns': [
            'beta blocker', 'beta-blocker', 'metoprolol', 'bisoprolol',
            'carvedilol', 'atenolol', 'propranolol', 'nebivolol',
        ],
        'effects': {
            'heart': ('reduce', 0.78, 'Beta-blockers: 34% post-MI mortality reduction (Ko 2004)'),
        }
    },
    {
        'class': 'Antiplatelet',
        'patterns': [
            'aspirin', 'clopidogrel', 'ticagrelor', 'prasugrel',
            'antiplatelet', 'ecosprin', 'disprin',
        ],
        'effects': {
            'heart': ('reduce', 0.88, 'Antiplatelet: 25% reduction in recurrent MI (ATT 2009)'),
            'brain': ('reduce', 0.88, 'Antiplatelet: 22% stroke prevention (ATT 2009)'),
        }
    },
    # ── Diabetes ──────────────────────────────────────────────────────────────
    {
        'class': 'Metformin',
        'patterns': ['metformin', 'glucophage', 'glycomet'],
        'effects': {
            'heart':  ('reduce', 0.78, 'Metformin: 39% MI reduction in overweight T2DM (UKPDS 34)'),
            'liver':  ('reduce', 0.90, 'Metformin reduces hepatic steatosis (Tang 2013 meta-analysis)'),
            'kidney': ('reduce', 0.94, 'Metformin: modest renoprotective effect (Salvatore 2020)'),
        }
    },
    {
        'class': 'SGLT2 Inhibitor',
        'patterns': [
            'sglt2', 'empagliflozin', 'dapagliflozin', 'canagliflozin',
            'jardiance', 'farxiga', 'forxiga', 'invokana',
        ],
        'effects': {
            'heart':  ('reduce', 0.72, 'SGLT2i: 38% HF hospitalization reduction (EMPA-REG)'),
            'kidney': ('reduce', 0.70, 'SGLT2i: 39% CKD progression reduction (CREDENCE/DAPA-CKD)'),
        }
    },
    {
        'class': 'GLP-1 Agonist',
        'patterns': [
            'glp-1', 'glp1', 'semaglutide', 'liraglutide', 'dulaglutide',
            'exenatide', 'ozempic', 'wegovy', 'victoza', 'trulicity',
        ],
        'effects': {
            'heart':  ('reduce', 0.74, 'GLP-1: 26% MACE reduction (LEADER/SUSTAIN-6)'),
            'liver':  ('reduce', 0.82, 'GLP-1: 33% liver fat reduction in NAFLD (Armstrong 2016)'),
        }
    },
    {
        'class': 'Insulin',
        'patterns': ['insulin', 'lantus', 'glargine', 'detemir', 'novomix'],
        'effects': {
            # Insulin itself is neutral; mark presence for reference
        }
    },
    # ── Liver ─────────────────────────────────────────────────────────────────
    {
        'class': 'Antiviral (Hepatitis)',
        'patterns': [
            'entecavir', 'tenofovir', 'sofosbuvir', 'ledipasvir',
            'daclatasvir', 'hep b', 'hep c', 'hepatitis antiviral',
        ],
        'effects': {
            'liver': ('reduce', 0.72, 'HBV/HCV antivirals: SVR→ fibrosis regression in 60–80% (AASLD 2023)'),
        }
    },
    {
        'class': 'Ursodeoxycholic Acid (UDCA)',
        'patterns': ['ursodeoxycholic', 'udca', 'ursodiol', 'urso'],
        'effects': {
            'liver': ('reduce', 0.88, 'UDCA slows PBC progression and improves liver enzymes'),
        }
    },
    # ── Brain / Neuro ─────────────────────────────────────────────────────────
    {
        'class': 'Antidepressant',
        'patterns': [
            'ssri', 'snri', 'sertraline', 'escitalopram', 'fluoxetine',
            'paroxetine', 'venlafaxine', 'duloxetine', 'antidepressant',
        ],
        'effects': {
            # Treated depression → less brain accelerated aging
            'brain': ('reduce', 0.94, 'Treated depression lowers dementia risk by ~15% (Diniz 2013)'),
        }
    },
    # ── Lung ─────────────────────────────────────────────────────────────────
    {
        'class': 'Inhaled Corticosteroid',
        'patterns': [
            'fluticasone', 'budesonide', 'beclomethasone', 'mometasone',
            'ciclesonide', 'ics', 'inhaled corticosteroid',
        ],
        'effects': {
            'lungs': ('reduce', 0.85, 'ICS: reduces COPD exacerbation rate ~25% (TORCH trial)'),
        }
    },
    {
        'class': 'LABA/LAMA',
        'patterns': [
            'tiotropium', 'ipratropium', 'salmeterol', 'formoterol',
            'indacaterol', 'umeclidinium', 'glycopyrronium', 'lama', 'laba',
            'spiriva', 'onbrez', 'ultibro',
        ],
        'effects': {
            'lungs': ('reduce', 0.88, 'LAMA/LABA: 20–30% exacerbation reduction (UPLIFT/TORCH)'),
        }
    },
    # ── HARMFUL interactions ──────────────────────────────────────────────────
    {
        'class': 'NSAID',
        'patterns': [
            'nsaid', 'ibuprofen', 'naproxen', 'diclofenac', 'indomethacin',
            'piroxicam', 'ketorolac', 'mefenamic', 'brufen', 'voveran',
        ],
        'effects': {
            'kidney': ('increase', 1.15, 'NSAIDs: 58% higher AKI risk (Zhang KI 2008); avoid in CKD 3+'),
            'heart':  ('increase', 1.08, 'NSAIDs: modest CV risk increase (Bhala Lancet 2013)'),
        }
    },
    {
        'class': 'Calcineurin Inhibitor',
        'patterns': [
            'cyclosporine', 'tacrolimus', 'calcineurin', 'ciclosporin',
        ],
        'effects': {
            'kidney': ('increase', 1.20, 'Calcineurin inhibitors: nephrotoxicity, HTN (Naesens 2009)'),
        }
    },
    {
        'class': 'Long-term Corticosteroid',
        'patterns': [
            'prednisolone', 'prednisone', 'dexamethasone', 'hydrocortisone',
            'betamethasone', 'methylprednisolone', 'long-term steroid',
        ],
        'effects': {
            'liver':  ('increase', 1.10, 'Long-term steroids: increased NAFLD/hepatic steatosis risk'),
            'kidney': ('increase', 1.05, 'Steroids: fluid retention, HTN → kidney strain'),
            'heart':  ('increase', 1.08, 'Steroids: dyslipidemia, glucose intolerance → CV risk'),
        }
    },
    {
        'class': 'Antiretroviral (HIV)',
        'patterns': [
            'antiretroviral', 'art', 'tenofovir', 'efavirenz',
            'lopinavir', 'ritonavir', 'atazanavir', 'hiv treatment',
        ],
        'effects': {
            'kidney': ('increase', 1.10, 'Tenofovir: tubular toxicity, Fanconi syndrome risk'),
            'liver':  ('increase', 1.08, 'Some ARTs: hepatotoxicity, steatosis (DHHS 2022)'),
            'heart':  ('increase', 1.07, 'Protease inhibitors: dyslipidemia, atherosclerosis'),
        }
    },
]


def detect_drug_classes(medications: list) -> list:
    """
    Given a list of medication name strings, return detected drug class names.
    """
    meds_lower = [m.lower().strip() for m in medications if m]
    detected = []
    for drug in DRUG_CLASSES:
        for pattern in drug['patterns']:
            if any(pattern in med for med in meds_lower):
                detected.append(drug['class'])
                break
    return detected


def apply_medication_effects(
    medications: list,
    organ_results: dict,
    health: dict
) -> dict:
    """
    Adjust organ risk scores based on detected medications.
    Mutates organ_results in place (same pattern as consistency_checker).
    Returns structured audit of all medication effects applied.
    """
    if not medications:
        return {'classes_detected': [], 'effects_applied': [], 'interactions_flagged': []}

    meds_lower = [m.lower().strip() for m in medications if m]
    effects_applied = []
    interactions_flagged = []
    classes_detected = []

    for drug in DRUG_CLASSES:
        # Check if this drug class is present
        matched = False
        for pattern in drug['patterns']:
            if any(pattern in med for med in meds_lower):
                matched = True
                break
        if not matched:
            continue

        classes_detected.append(drug['class'])

        for organ, (direction, multiplier, evidence) in drug['effects'].items():
            result = organ_results.get(organ)
            if not isinstance(result, dict):
                continue

            original_risk = result.get('current_risk', 0.0)
            new_risk = original_risk * multiplier

            # Clamp
            if direction == 'reduce':
                # Don't let medication reduce risk below a physiological floor
                new_risk = max(new_risk, 0.05)
            else:
                # Don't let drug interaction push above 1.0
                new_risk = min(new_risk, 1.0)

            new_risk = round(new_risk, 3)

            if new_risk != original_risk:
                result['current_risk'] = new_risk
                result['risk_level'] = _risk_level(new_risk)
                result['health_score'] = max(0, int((1 - new_risk) * 100))

                entry = {
                    'drug_class': drug['class'],
                    'organ': organ,
                    'direction': direction,
                    'original_risk': round(original_risk, 3),
                    'adjusted_risk': new_risk,
                    'change': round(new_risk - original_risk, 3),
                    'evidence': evidence,
                }
                if direction == 'increase':
                    interactions_flagged.append(entry)
                    result.setdefault('possible_issues', [])
                    result['possible_issues'].append(
                        f"[Drug interaction] {drug['class']}: {evidence}"
                    )
                else:
                    effects_applied.append(entry)

    return {
        'classes_detected': classes_detected,
        'effects_applied': effects_applied,
        'interactions_flagged': interactions_flagged,
        'net_organ_changes': {
            organ: round(
                organ_results[organ].get('current_risk', 0) -
                organ_results[organ].get('_pre_med_risk', organ_results[organ].get('current_risk', 0)),
                3
            )
            for organ in organ_results if isinstance(organ_results[organ], dict)
        }
    }


def _risk_level(risk_score: float) -> str:
    if risk_score >= 0.60:
        return 'RED'
    elif risk_score >= 0.30:
        return 'YELLOW'
    return 'GREEN'
