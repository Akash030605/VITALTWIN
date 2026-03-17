# app.py - Main FastAPI application for Render deployment

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import os
import sys
from pathlib import Path

# Add to app.py and simulation_engine.py
import numpy as np
print(f"NumPy version: {np.__version__}")
print(f"NumPy path: {np.__file__}")

# Test if _core exists
try:
    from numpy import _core
    print("✓ numpy._core exists")
except ImportError:
    print("✗ numpy._core missing - using older NumPy")
    # This is actually GOOD - means you're using older NumPy
    
# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Import your simulation engine
from simulation_engine import VitalTwinSimulator

# Initialize FastAPI
app = FastAPI(
    title="VITALTWIN ML Model API",
    description="Digital Twin of Human Body for Disease Simulation",
    version="2.0.0"
)

# Enable CORS for all origins (for hackathon)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize simulator once (loads ML models)
print("🚀 Loading VITALTWIN ML Models...")
try:
    simulator = VitalTwinSimulator()
    print("✅ Models loaded successfully!")
except Exception as e:
    print(f"❌ Error loading models: {e}")
    simulator = None

# ========== Pydantic Models for Request/Response ==========

class ProfileInfo(BaseModel):
    Userid: Optional[str] = "TEST123"
    Age: int
    Gender: str
    Height: Optional[float] = None
    Weight: Optional[float] = None
    Diet: Optional[str] = "Average"
    ActivityLevel: Optional[str] = "Moderate"

class HealthInfo(BaseModel):
    Smoking: Optional[str] = "Never"
    Alcohol: Optional[str] = "Never"
    Sleep: Optional[int] = 7
    Stress: Optional[str] = "Medium"
    MedicalConditions: Optional[List[str]] = []
    Bmi: Optional[float] = None
    
    # Lab values (optional)
    ast: Optional[float] = None
    alt: Optional[float] = None
    ggt: Optional[float] = None
    glucose: Optional[float] = None
    
    # Cardio data (optional)
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    cholesterol: Optional[int] = None
    gluc: Optional[int] = None

class UserData(BaseModel):
    ProfileInfo: ProfileInfo
    HealthInfo: HealthInfo

class WhatIfRequest(BaseModel):
    user_data: UserData
    changes: Dict[str, Any]

# ========== API Endpoints ==========

@app.get("/")
def root():
    return {
        "service": "VITALTWIN ML Model",
        "version": "2.0.0",
        "status": "running",
        "models": [
            {"name": "Heart", "accuracy": "73.3%"},
            {"name": "Liver", "accuracy": "97.3%"}
        ],
        "features": [
            "Biological Age Engine ⭐",
            "Future Self Timeline ⭐⭐⭐",
            "Body Stress Heatmap ⭐",
            "What-If Lifestyle Simulator ⭐⭐⭐",
            "Vital Score Gauge"
        ],
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    if simulator:
        return {
            "status": "healthy",
            "models_loaded": True,
            "heart_model": "loaded",
            "liver_model": "loaded"
        }
    else:
        return {
            "status": "degraded",
            "models_loaded": False,
            "message": "Models failed to load"
        }

@app.post("/predict")
def predict(user_data: UserData):
    """
    Main prediction endpoint
    Returns complete health simulation with all 8 features
    """
    if not simulator:
        raise HTTPException(status_code=503, detail="ML models not loaded")
    
    try:
        # Convert to dict
        data_dict = user_data.dict()
        
        # Run simulation
        result = simulator.run_simulation(data_dict)
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/what-if")
def what_if(request: WhatIfRequest):
    """
    What-If simulation endpoint
    Test lifestyle changes and see instant results
    """
    if not simulator:
        raise HTTPException(status_code=503, detail="ML models not loaded")
    
    try:
        data_dict = request.user_data.dict()
        changes = request.changes
        
        # Run what-if simulation
        result = simulator.simulate_lifestyle_change(data_dict, changes)
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model-info")
def model_info():
    """Get detailed information about the ML models"""
    return {
        "heart_model": {
            "algorithm": "Random Forest",
            "trees": 100,
            "features": ["age", "bmi", "bp", "cholesterol", "lifestyle"],
            "accuracy": "73.3%",
            "training_samples": 70000
        },
        "liver_model": {
            "algorithm": "Random Forest",
            "trees": 100,
            "features": ["ast", "alt", "ggt", "bmi", "glucose"],
            "accuracy": "97.3%",
            "training_samples": 10071,
            "confusion_matrix": [
                [28, 11, 0, 0],
                [43, 1647, 0, 0],
                [0, 0, 213, 0],
                [0, 0, 0, 73]
            ]
        }
    }

# For local testing
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)