# VitalTwin — Trust Framework
## How to Make This a Platform Doctors, Users, and Regulators Can Trust

Trust in a health platform has 6 layers. Break any one of them and the whole
thing collapses. This document covers all 6 — what needs to be built, said,
shown, and filed.

---

## The 6 Layers of Trust

```
Layer 1: Technical Honesty     — Does the model know what it doesn't know?
Layer 2: Clinical Accuracy     — Are outputs grounded in real medicine?
Layer 3: Explainability        — Can users see WHY the result was given?
Layer 4: Data Privacy          — Is personal health data protected?
Layer 5: Legal Compliance      — Does it meet India's regulatory requirements?
Layer 6: Institutional Trust   — Who vouches for it?
```

---

## Layer 1 — Technical Honesty (What the Model Knows vs. Doesn't)

### Problem
Most health apps show a number with false confidence. "Your heart score is 73."
Based on what? Calculated how? Verified by whom? Users can't tell.

### What to Build

#### 1A. Confidence Badges on Every Metric
Every organ score shows a confidence level based on how many real inputs were provided:

```
❤️ Heart Risk: 68%      [High Confidence ●●●●○]
   Based on: Framingham PCE + your BP + cholesterol + age + smoking history

🫀 Kidney Risk: 41%     [Medium Confidence ●●●○○]
   Based on: Rule-based estimate — add your creatinine for clinical accuracy

🧠 Brain Risk: 29%      [Low Confidence ●●○○○]
   Based on: CAIDE lifestyle factors only — no lab values provided
```

#### 1B. Uncertainty Ranges (not just a single number)
Instead of "Heart risk: 68%", show "Heart risk: 62–74%"

The range comes from the model's calibrated confidence interval:
```python
# In heart_model.py — return range alongside point estimate
from sklearn.utils import resample

def predict_with_uncertainty(model, X, n_bootstrap=100):
    """Bootstrap confidence interval for risk estimate."""
    predictions = []
    for _ in range(n_bootstrap):
        X_resampled = resample(X, random_state=None)
        pred = model.predict_proba(X_resampled)[0][1]
        predictions.append(pred)
    
    lower = round(np.percentile(predictions, 10), 3)
    upper = round(np.percentile(predictions, 90), 3)
    point = round(np.mean(predictions), 3)
    
    return {
        "estimate": point,
        "range_low": lower,
        "range_high": upper,
        "confidence_interval": "80%"
    }
```

#### 1C. Input Sensitivity Warning
When a key input is missing that would significantly change the result:
```
⚠️  Your liver risk could be GREEN or RED depending on your ALT/AST levels.
    We don't have your liver enzyme values.
    [Add blood test results →] or [Book a test →]
```

#### 1D. Explicit "Not a Diagnostic Tool" on Every Score Card
Not buried in a footer. Visible on the card:
```
This is a risk estimate, not a diagnosis.
Risk scores indicate probability, not certainty.
Consult a physician before making health decisions.
```

---

## Layer 2 — Clinical Accuracy (Grounded in Real Medicine)

### Problem
The current model's biological age formula uses "+6 years for daily smoking" —
a number invented during development, not from any study.
Users trust these numbers. They shouldn't — but they do.

### What to Build

#### 2A. Citation System — Every Formula Has a Source
Every calculation in the model maps to a published clinical study.
Show this in the UI on an expandable panel:

```
How was your heart risk calculated?

  Formula:    ACC/AHA Pooled Cohort Equations (PCE)
  Published:  Goff DC Jr. et al., Circulation 2014;129:S49-S73
  Validated:  24,626 patients — Framingham, ARIC, CHS, CARDIA cohorts
  Accuracy:   C-statistic 0.72 (women), 0.71 (men)
  
  Inputs used:
  ✓ Age (52)
  ✓ Total Cholesterol (218 mg/dL)
  ✓ HDL Cholesterol (48 mg/dL)
  ✓ Systolic BP (134 mmHg)
  ✓ BP Medication (No)
  ✓ Smoking (Former)
  ✗ Diabetes status (not provided — assumed No)
  
  South Asian correction applied: ×1.26
  Source: Brindle P. et al., Heart 2005;91:1170-1176
```

This is the single most powerful trust signal. It says:
"We didn't make this up. Here is the exact paper. Here are the exact inputs we used."

#### 2B. Risk Level Calibration Table
Show users what a given risk percentage means in real population terms:

```
Your 10-year cardiovascular risk: 18%

What this means in plain language:
  → In a group of 100 people with your profile, about 18 will have
    a heart attack or stroke in the next 10 years.
  → The average person your age: 9% (you are 2× average risk)
  → With optimal lifestyle: your risk could fall to ~10%

Clinical action threshold: Risk >7.5% = discuss statin therapy with a doctor
                            (ACC/AHA 2019 Guideline)
```

#### 2C. Clinical Advisory Panel
Before public launch, have 3–5 doctors review 50 test cases:
- MBBS + MD Internal Medicine (for general review)
- Cardiologist (for heart scores)
- Hepatologist or Gastroenterologist (liver)
- Nephrologist (kidney)
- Pulmonologist (lungs)

Their sign-off becomes a trust signal on the platform:
```
Clinically reviewed by:
Dr. [Name], MD, DM Cardiology, AIIMS Delhi
Dr. [Name], MD, DM Nephrology, PGI Chandigarh
```

#### 2D. Red Flag Overrides — Absolute Clinical Rules
Some conditions must always trigger RED regardless of model output:
```python
ABSOLUTE_RED_FLAGS = [
    # (condition_keywords, organ, reason)
    (["heart failure", "chf", "cardiomyopathy"], "heart", "Heart failure is RED by definition"),
    (["dialysis", "hemodialysis", "peritoneal dialysis"], "kidney", "Dialysis = end-stage CKD"),
    (["cirrhosis", "liver failure", "hepatic encephalopathy"], "liver", "Cirrhosis = RED"),
    (["copd gold 3", "copd gold 4", "severe copd"], "lungs", "Severe COPD = RED"),
    (["lung cancer", "mesothelioma"], "lungs", "Active lung malignancy = RED"),
    (["stroke", "tia"], "brain", "History of stroke = RED brain risk"),
    (["myocardial infarction", "heart attack", "stemi"], "heart", "Post-MI = RED minimum"),
]

def apply_absolute_overrides(organ_results, medical_conditions):
    conditions_lower = [c.lower() for c in medical_conditions]
    for keywords, organ, reason in ABSOLUTE_RED_FLAGS:
        if any(kw in cond for kw in keywords for cond in conditions_lower):
            if organ in organ_results:
                organ_results[organ]["risk_level"] = "RED"
                organ_results[organ]["current_risk"] = max(organ_results[organ]["current_risk"], 0.65)
                organ_results[organ]["override_reason"] = reason
    return organ_results
```

---

## Layer 3 — Explainability (Why Did You Get This Score?)

### Problem
A black-box number causes two failure modes:
1. User ignores it because they don't believe it
2. User panics because they don't understand it

### What to Build

#### 3A. SHAP Values — Show What Drove Your Score
SHAP (SHapley Additive exPlanations) explains every prediction.
For each user, it shows: "Your BMI added 8 points to heart risk. Smoking added 14 points."

```python
pip install shap

import shap

def explain_prediction(model, X_single, feature_names):
    """Generate SHAP explanation for one prediction."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_single)
    
    # For binary classifier, take class=1 SHAP values
    if isinstance(shap_values, list):
        shap_vals = shap_values[1][0]
    else:
        shap_vals = shap_values[0]
    
    explanation = []
    for feat, val, shap_val in zip(feature_names, X_single[0], shap_vals):
        direction = "increases" if shap_val > 0 else "decreases"
        explanation.append({
            "factor": feat,
            "your_value": val,
            "impact": round(abs(shap_val) * 100, 1),   # Convert to % points
            "direction": direction,
            "shap_raw": round(shap_val, 4)
        })
    
    # Sort by absolute impact
    explanation.sort(key=lambda x: x["impact"], reverse=True)
    return explanation[:5]   # Top 5 drivers

# Example output for heart risk:
# [
#   {"factor": "smoking", "your_value": 1, "impact": 14.2, "direction": "increases"},
#   {"factor": "systolic_bp", "your_value": 148, "impact": 11.8, "direction": "increases"},
#   {"factor": "age", "your_value": 52, "impact": 9.3, "direction": "increases"},
#   {"factor": "hdl_cholesterol", "your_value": 62, "impact": 5.1, "direction": "decreases"},
#   {"factor": "active", "your_value": 1, "impact": 3.4, "direction": "decreases"},
# ]
```

Show this in the UI as:

```
What's affecting your heart risk?

▲ Smoking history        +14.2%  [red bar ████████░░]
▲ High blood pressure    +11.8%  [red bar ██████░░░░]
▲ Age (52)               +9.3%   [amber bar █████░░░░░]
▼ Good HDL cholesterol   -5.1%   [green bar ███░░░░░░░]  (protective)
▼ Physically active      -3.4%   [green bar ██░░░░░░░░]  (protective)
```

This is the most powerful trust + engagement feature you can add.
Users understand their risk and know exactly what to change.

#### 3B. "How to Improve This Score" — Actionable, Quantified
Every recommendation must say: "If you do X, your score will change by approximately Y."

```
Current Heart Risk: 18%

If you quit smoking:        → estimated 13% risk  (-5 percentage points)
If you control BP to 120:   → estimated 14% risk  (-4 percentage points)
If you do both:             → estimated 9% risk   (-9 percentage points)
                              (below the 7.5% statin threshold)
```

These projections come from the What-If simulator — run the model with changed inputs
and show the delta. This is already built. Just surface the numbers.

#### 3C. Population Percentile Context
```
Your vital score: 61

You are healthier than 43% of Indians your age and gender.
Average for your profile: 67
Best possible with your genetics/age: ~85

[See how you compare →]
```

Uses NFHS-5 population data to generate percentile benchmarks by age + gender + region.

---

## Layer 4 — Data Privacy (Health Data is Intimate)

### Problem
Health data is the most sensitive personal data that exists. A user entering
their HIV status, psychiatric medications, or organ disease history into an app
needs to know it won't be sold, leaked, or used against them.

### What to Build

#### 4A. Data Minimization — Only Collect What's Used
Current state: `medications[]` is collected and discarded. This is a liability.
Every field collected must be used, stored securely, or not collected.

Audit every field:
```
Field             | Used by model? | Stored? | If stored: encrypted?
------------------|---------------|---------|---------------------
profile.name      | No (display)  | Yes     | Must be
profile.age       | Yes           | Yes     | Yes
input.medications | YES (after fix)| Yes     | Yes — sensitive
input.medical_conditions | Yes   | Yes     | Yes — very sensitive
lab values        | Yes           | Yes     | Yes — most sensitive
```

#### 4B. Local Processing Option
For users who don't want data sent to any server:
- Run a quantized version of the model in the browser using ONNX.js or TensorFlow.js
- All computation happens client-side
- Nothing leaves the device

This is a major trust differentiator. "Your data never leaves your phone."

```javascript
// Future implementation sketch
import * as ort from 'onnxruntime-web';

async function predictLocally(inputData) {
  const session = await ort.InferenceSession.create('/models/heart_model.onnx');
  const feeds = { input: new ort.Tensor('float32', inputData, [1, 9]) };
  const results = await session.run(feeds);
  return results.output.data[0];
}
```

#### 4C. Data Retention Policy (visible, not buried)
```
Your health data:
✓ Stored encrypted (AES-256) on servers in India
✓ Never sold to third parties
✓ Never shared with insurers without your explicit consent
✓ You can download all your data: [Export →]
✓ You can delete all your data: [Delete account →]
✓ Reports are auto-deleted after 2 years unless you opt to keep
```

#### 4D. Report Anonymization for Research
If you want to use aggregated data to improve models:
```
Help improve VitalTwin for India:
[ ] Allow anonymized health data to train future models
    (Your name and contact info are never included)
    (You can withdraw consent at any time)
```

This gives you a growing India-specific training dataset over time —
the most valuable asset a health platform can have.

#### 4E. Technical Security Requirements
```
Transport:    HTTPS only, HSTS headers, TLS 1.3
Storage:      AES-256 at rest, field-level encryption for PII + health data
Auth:         bcrypt passwords (cost 12), refresh token rotation, MFA option
API:          Rate limiting (100 req/min per IP), input sanitization
Logs:         No PII in application logs — log user_id hash only
Backups:      Daily encrypted backups, tested restore procedure quarterly
```

---

## Layer 5 — Legal Compliance (India-Specific)

### DPDP Act 2023 — Digital Personal Data Protection Act

India's new data protection law. Health data is classified as **"sensitive personal data"**.

Key obligations:
```
1. Consent: Must obtain explicit, granular consent before collecting health data
   → Show clear consent screen before Step 1 form
   → "I consent to VitalTwin processing my health data to generate a risk report"
   → Separate consent for: storage / research use / future contact

2. Data Principal Rights:
   → Right to access: User can download all their data (JSON/PDF export)
   → Right to correction: User can edit any stored data
   → Right to erasure: User can delete account + all data within 72 hours
   → Right to grievance: Named contact person for data complaints

3. Data Fiduciary obligations:
   → Appoint a Data Protection Officer (can be a founder initially)
   → Maintain records of all data processing activities
   → Report data breaches within 72 hours to DPDB

4. Children (under 18):
   → Do not allow children to create accounts without verifiable parental consent
   → Add age verification at signup
```

### CDSCO — Software as Medical Device Classification

The Central Drugs Standard Control Organisation regulates health software in India.

**Is VitalTwin a medical device?** It depends on the claim:

```
NOT a medical device (safe zone):
✓ "Understand your health risk factors"
✓ "Educational health assessment"
✓ "Wellness tracking and lifestyle insights"
✓ "Risk scoring based on published population research"

IS a medical device (requires CDSCO registration, avoid this):
✗ "Diagnose cardiovascular disease"
✗ "Detect kidney failure"
✗ "Used by doctors to make treatment decisions"
✗ "Clinical decision support tool"
```

**Current recommendation: Position as wellness/education, not diagnostic.**
Add to every screen: "VitalTwin is a wellness education tool, not a medical device.
Results are for informational purposes only."

When revenue and validation grows → pursue CDSCO SaMD (Software as Medical Device)
registration under Class A (lowest risk) to formally enter the clinical market.

### IT Act 2000 (Section 43A) + SPDI Rules 2011

Still enforceable for health data even alongside DPDP 2023:
```
→ Maintain reasonable security practices for sensitive personal data
→ Health information = "sensitive personal data or information" under SPDI Rules
→ Cannot share with third parties without explicit written consent
→ Must have a privacy policy visible on the site
→ Must have a link to "Privacy Policy" and "Terms of Service" on every page
```

### Insurance Regulatory Concern

IRDAI (Insurance Regulatory and Development Authority of India) explicitly prohibits
insurers from using non-clinical health app data to price or deny policies.

Add this statement to the platform:
```
"VitalTwin data is not shared with, and cannot be used by, insurance companies
to determine premium pricing or policy eligibility. This is prohibited by IRDAI regulations."
```

This is a major user anxiety. Addressing it directly builds significant trust.

---

## Layer 6 — Institutional Trust (Who Vouches for This?)

### The Credibility Gap
A user sees "Your heart risk is 18%." Their next thought is:
"Who are you? Why should I believe you?"

No technical feature solves this. It requires external endorsement.

### What to Pursue

#### 6A. Hospital/Clinic Integration Pilot
Approach 2-3 clinics (not AIIMS — too slow) with a proposal:
- Run VitalTwin alongside their standard intake questionnaire for 3 months
- Compare VitalTwin risk scores against clinical diagnosis for the same patients
- Publish results (even as a preprint on medRxiv)

Target: Apollo Spectra (accessible), Manipal Hospitals, or a medical college clinic
(MAMC, Grant Medical, KEM).

**Even one pilot with 50 patients gives you a validation you can cite.**

#### 6B. Academic Validation
Contact biomedical informatics / epidemiology departments:
- AIIMS Delhi (Dept of Biostatistics and Medical Informatics)
- IIT Bombay (Healthcare Analytics)
- CMC Vellore (Public Health)
- NIMHANS Bangalore (for brain/cognitive risk)

Proposal: "We've built an India-specific ML health risk model using ILPD, CKD-UCI,
NFHS-5, and LASI data. We'd like to validate it against your patient cohort."

Academic collaboration → co-authorship on a paper → credibility that no marketing can buy.

#### 6C. Medical Advisory Board
Recruit 3–5 doctors as formal advisors (compensated with equity/stipend):
- 1 cardiologist
- 1 diabetologist/endocrinologist (overlaps kidney + liver)
- 1 pulmonologist
- 1 general physician (primary care voice)

They review the model, sign off on recommendations, and their names appear on the platform:
```
Medical Advisory Board
Dr. _____, MD, DM Cardiology — Clinical validation, heart risk model
Dr. _____, MD, DM Endocrinology — Diabetes, kidney and liver risk
Dr. _____, MD, DNB Pulmonology — Lung risk, AQI impact
```

#### 6D. Certifications and Standards

**ISO 27001** — Information Security Management
- Industry standard for health data security
- Achievable for a startup in 6-9 months
- Shows insurers, hospitals, and enterprises you take data seriously

**NABH (National Accreditation Board for Hospitals)** — Health IT accreditation
- Has a pathway for health technology companies
- Signals clinical credibility in the India market

**SOC 2 Type II** (for enterprise/B2B sales later)
- Required by most corporates before deploying health tools for employees

#### 6E. Transparency Report (Publish Quarterly)
Like a tech company's transparency report but for model accuracy:

```
VitalTwin Model Accuracy Report — Q1 2025

Heart model (Framingham + XGBoost):
  Training data:   70,000 patients (cardio_dataset + NFHS-5)
  AUC-ROC:        0.824 (test set, n=14,000)
  Calibration:    0.97 (Brier score, lower is better)
  Last updated:   January 2025

Liver model (FIB-4 + XGBoost + SMOTE):
  Training data:   1,187 patients (ILPD India + Turkish NASH, biopsy-confirmed)
  AUC-ROC:        0.863 (test set, n=238)
  Last updated:   January 2025

Model limitations we are aware of:
  - Brain model: LASI cognitive data only available for ages 45+. Younger
    users receive rule-based estimates (confidence: Low)
  - Lung model: No spirometry data in training. FEV1/FVC predicted, not measured.
  - All models: Validated on Indian population only. Not tested on NRI or diaspora.
  
Data used in last 90 days:
  Prediction requests:     [number]
  Users who provided labs: [%]
  Average confidence score: [Medium/High]
  
Known issues / active improvements:
  - [list of things being worked on]
```

Publishing your limitations is what builds trust. Hiding them destroys it.

---

## The One Non-Negotiable

Every screen where a risk score appears must show, in readable text (not fine print):

```
⚕️  VitalTwin provides health risk estimates for educational purposes.
    This is not a medical diagnosis. Consult a qualified physician
    before making any health decisions.
```

And on every recommendation card:
```
This recommendation is based on published clinical guidelines.
Your doctor may have additional context that changes this advice.
```

---

## Trust Implementation Priority

Build these in this order:

```
Week 1–2   (Technical — no external dependency):
  ✓ Confidence badges on every organ score
  ✓ SHAP explanation panel ("What's affecting your score")
  ✓ Uncertainty ranges instead of single numbers
  ✓ Absolute RED flag overrides for known conditions
  ✓ DPDP consent screen before Step 1
  ✓ "Not a medical device" disclaimer on all score cards
  ✓ Citation panel ("How was this calculated" expandable)
  ✓ Data deletion / export functionality

Week 3–4   (Clinical — needs doctor review):
  ✓ South Asian correction applied to heart model
  ✓ India BMI cutoffs (23/25 not 25/30)
  ✓ Bidi correction for tobacco type
  ✓ City AQI as lung risk input
  ✓ Insurance data non-sharing statement

Month 2    (Institutional — takes time):
  → Approach 2 clinics for pilot
  → Recruit 2–3 medical advisors
  → Begin ISO 27001 readiness assessment
  → Publish model methodology page (not full code — methodology)

Month 3+   (Validation — publish findings):
  → Pilot results writeup (even informal blog post)
  → Academic outreach
  → CDSCO SaMD classification review
```

---

## What Trustable Looks Like in the UI

Every report should feel like it came from a careful doctor, not a quiz:

```
BEFORE (current):  "Your heart score is 68."

AFTER (trustable): "Heart Risk: Moderate (68/100)
                    10-year CVD risk: ~18%  [62%–74% range]
                    Confidence: High ●●●●○  (based on 7 of 9 key inputs)
                    
                    Primary drivers:
                    ▲ Systolic BP 148 mmHg   +11.8% risk
                    ▲ Former smoker (12 yrs)  +14.2% risk
                    ▼ Active lifestyle         -3.4% protective
                    
                    Formula: ACC/AHA Pooled Cohort Equations (2013)
                    South Asian correction: ×1.26 applied
                    
                    What this means: In 100 people like you, about 18
                    will have a heart attack or stroke in 10 years.
                    Average for your age/gender: 9%
                    
                    If you control your BP to 130: risk drops to ~13%
                    
                    ⚕️ Discuss this result with your doctor.
                       [Book a consultation →]  [Share report →]"
```

This is a platform doctors will refer patients to. The current version is not.
