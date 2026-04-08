# app.py - Main FastAPI application

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from simulation_engine import VitalTwinSimulator

app = FastAPI(
    title="VITALTWIN ML Model API",
    description="Digital Twin of Human Body — Clinically Validated",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading VITALTWIN ML Models...")
try:
    simulator = VitalTwinSimulator()
    print("Models loaded successfully.")
except Exception as e:
    print(f"Error loading models: {e}")
    simulator = None


# ─────────────────────────────────────────────
# Request / Response Models
# ─────────────────────────────────────────────

class ProfileInfo(BaseModel):
    Userid:        Optional[str]   = "UNKNOWN"
    Age:           int
    Gender:        str             = "Male"
    Height:        Optional[float] = None       # cm
    Weight:        Optional[float] = None       # kg
    Diet:          Optional[str]   = "Average"  # Poor | Average | Good
    ActivityLevel: Optional[str]   = "Moderate" # Sedentary | Moderate | Active
    City:          Optional[str]   = None       # Indian city for AQI lookup
    State:         Optional[str]   = None       # Indian state for prevalence priors

class HealthInfo(BaseModel):
    # ── Core lifestyle (always collected) ──────────────────────────
    Smoking:           Optional[str]        = "Never"   # Never | Occasional | Daily
    Alcohol:           Optional[str]        = "Never"   # Never | Occasional | Weekly | Daily
    Sleep:             Optional[float]      = 7         # hours per night
    Stress:            Optional[str]        = "Medium"  # Low | Medium | High
    MedicalConditions: Optional[List[str]]  = []
    Medications:       Optional[List[str]]  = []        # NOW USED in medication modeler
    Bmi:               Optional[float]      = None

    # ── Smoking detail (unlock pack-years for lung model) ──────────
    YearsSmokedmoked:    Optional[int]   = None  # How many years smoked / smoking
    CigarettesPerDay:  Optional[int]   = None  # Average cigarettes per day
    TobaccoType:       Optional[str]   = "cigarette"  # cigarette | bidi | hookah | mixed | khaini
    CookingFuel:       Optional[str]   = None  # lpg | wood | dung | crop | kerosene | electric

    # ── Blood pressure (actual numbers) ───────────────────────────
    SystolicBP:        Optional[int]   = None  # mmHg  e.g. 130
    DiastolicBP:       Optional[int]   = None  # mmHg  e.g. 85
    BPOnMedication:    Optional[bool]  = False

    # ── Family history ─────────────────────────────────────────────
    FamilyHistoryHeart:    Optional[bool] = False
    FamilyHistoryDiabetes: Optional[bool] = False
    FamilyHistoryKidney:   Optional[bool] = False
    FamilyHistoryCancer:   Optional[bool] = False

    # ── Lab values (all optional — from blood test report) ─────────
    TotalCholesterol:  Optional[float] = None  # mg/dL   (<200 normal)
    HDLCholesterol:    Optional[float] = None  # mg/dL   (>60 protective)
    LDLCholesterol:    Optional[float] = None  # mg/dL   (<100 optimal)
    Triglycerides:     Optional[float] = None  # mg/dL   (<150 normal)
    FastingGlucose:    Optional[float] = None  # mg/dL   (<100 normal)
    HbA1c:            Optional[float] = None  # %       (<5.7 normal)
    SerumCreatinine:   Optional[float] = None  # mg/dL   (0.7-1.3 men)
    AST:               Optional[float] = None  # U/L     (<40 normal)
    ALT:               Optional[float] = None  # U/L     (<56 normal)
    GGT:               Optional[float] = None  # U/L     (<48 normal)
    Albumin:           Optional[float] = None  # g/dL    (3.5-5.0 normal)
    Platelets:         Optional[float] = None  # 10^9/L  (150-400 normal)

    # ── Legacy fields (keep for backward compat) ───────────────────
    ast:           Optional[float] = None
    alt:           Optional[float] = None
    ggt:           Optional[float] = None
    glucose:       Optional[float] = None
    systolic_bp:   Optional[int]   = None
    diastolic_bp:  Optional[int]   = None
    cholesterol:   Optional[int]   = None   # old categorical 1/2/3
    gluc:          Optional[int]   = None   # old categorical 1/2/3

    def effective_systolic(self):
        return self.SystolicBP or self.systolic_bp

    def effective_diastolic(self):
        return self.DiastolicBP or self.diastolic_bp

    def effective_ast(self):
        return self.AST or self.ast

    def effective_alt(self):
        return self.ALT or self.alt

    def effective_ggt(self):
        return self.GGT or self.ggt

    def effective_glucose(self):
        """Return best available glucose value in mg/dL."""
        if self.FastingGlucose:
            return self.FastingGlucose
        if self.glucose:
            return self.glucose
        # Estimate from HbA1c: glucose ≈ (HbA1c × 28.7) - 46.7
        if self.HbA1c:
            return round(self.HbA1c * 28.7 - 46.7, 1)
        return None

    def effective_cholesterol_mgdl(self):
        """Return total cholesterol in mg/dL."""
        if self.TotalCholesterol:
            return self.TotalCholesterol
        # Map old categorical: 1→185, 2→215, 3→265
        cat_map = {1: 185, 2: 215, 3: 265}
        return cat_map.get(self.cholesterol) if self.cholesterol else None

    def pack_years(self):
        """Calculate bidi-corrected pack-years."""
        years = self.YearsSmokedmoked or 0
        cpd   = self.CigarettesPerDay or (15 if self.Smoking == "Daily" else 5 if self.Smoking == "Occasional" else 0)
        raw   = (cpd / 20) * years
        multiplier = {"cigarette": 1.0, "bidi": 1.5, "hookah": 0.5,
                      "mixed": 1.2, "chutta": 1.3, "khaini": 0.2}.get(self.TobaccoType or "cigarette", 1.0)
        return round(raw * multiplier, 2)

    def is_diabetic(self):
        conds = [c.lower() for c in (self.MedicalConditions or [])]
        has_cond = any("diabetes" in c or "t2dm" in c or "t1dm" in c for c in conds)
        has_glucose = (self.effective_glucose() or 0) >= 126
        has_hba1c   = (self.HbA1c or 0) >= 6.5
        return has_cond or has_glucose or has_hba1c

    def is_hypertensive(self):
        conds = [c.lower() for c in (self.MedicalConditions or [])]
        has_cond = any("hypertension" in c or "high bp" in c or "high blood pressure" in c for c in conds)
        sbp = self.effective_systolic() or 0
        dbp = self.effective_diastolic() or 0
        return has_cond or sbp >= 140 or dbp >= 90 or bool(self.BPOnMedication)


class UserData(BaseModel):
    ProfileInfo: ProfileInfo
    HealthInfo:  HealthInfo

class WhatIfRequest(BaseModel):
    user_data: UserData
    changes:   Dict[str, Any]


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "VITALTWIN ML Model API v3",
        "status": "running",
        "models": [
            {"name": "Heart",  "method": "Framingham PCE + XGBoost + South Asian correction"},
            {"name": "Liver",  "method": "FIB-4 Index + NAFLD LFS + ML (biopsy-confirmed data)"},
            {"name": "Kidney", "method": "CKD-EPI 2021 eGFR + Rule-based fallback"},
            {"name": "Brain",  "method": "CAIDE Dementia Score + Framingham Stroke"},
            {"name": "Lungs",  "method": "Pack-years (bidi-corrected) + AQI + GOLD criteria"},
        ],
        "verification_layers": [
            "Input sanity validation",
            "Per-organ confidence scoring",
            "Clinical consistency cross-checks",
            "Medication effect modeling",
        ],
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy" if simulator else "degraded",
        "models_loaded": simulator is not None,
    }

@app.post("/predict")
def predict(user_data: UserData):
    if not simulator:
        raise HTTPException(status_code=503, detail="ML models not loaded")
    try:
        result = simulator.run_simulation(user_data.dict())
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/what-if")
def what_if(request: WhatIfRequest):
    if not simulator:
        raise HTTPException(status_code=503, detail="ML models not loaded")
    try:
        result = simulator.simulate_lifestyle_change(request.user_data.dict(), request.changes)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model-info")
def model_info():
    return {
        "heart":  {"method": "Framingham Pooled Cohort Equations (PCE) + ML fallback",
                   "south_asian_correction": True, "correction_factor": "1.26×"},
        "liver":  {"method": "FIB-4 index (if labs) + NAFLD-LFS (no labs) + ML",
                   "training_data": "604 biopsy-confirmed (Turkish NASH) + 583 Indian (ILPD)"},
        "kidney": {"method": "CKD-EPI 2021 eGFR equation (creatinine) + rule-based fallback",
                   "standard": "KDIGO 2022 CKD staging"},
        "brain":  {"method": "CAIDE Dementia Risk Score + Framingham Stroke Risk Profile",
                   "validated": "1,449 patients, 20-year follow-up (Kivipelto 2006)"},
        "lungs":  {"method": "Pack-years (bidi-corrected) + City AQI + GOLD criteria",
                   "india_specific": True},
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
