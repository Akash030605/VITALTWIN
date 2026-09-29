# utils/data_analyzer.py

import pandas as pd
import json
import numpy as np
from pathlib import Path

class DataAnalyzer:
    """
    Analyzes ALL datasets:
    - Cardio dataset (BP, cholesterol)
    - Srishti's liver dataset (enzymes + fibrosis)
    - NHANES data (enzymes + liver risk score)
    """
    
    def __init__(self, data_dir="../data"):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.all_thresholds = {}
    
    def analyze_nhanes_data(self):
        """Analyze NHANES liver enzyme data"""
        print("\n🔬 ANALYZING NHANES LIVER DATA")
        print("="*60)
        
        nhanes_path = self.data_dir / "NHANES_Liver_Cleaned.csv"
        if not nhanes_path.exists():
            print("❌ NHANES data not found")
            return None
        
        df = pd.read_csv(nhanes_path)
        print(f"📊 Loaded {len(df)} NHANES records")
        
        # Split by liver risk
        low_risk = df[df['Liver_Risk_Score'] == 0]
        high_risk = df[df['Liver_Risk_Score'] == 1]
        
        if len(low_risk) == 0 or len(high_risk) == 0:
            print("⚠️ Need both low and high risk patients for comparison")
            return None
        
        print(f"   Low Risk: {len(low_risk)} patients")
        print(f"   High Risk: {len(high_risk)} patients")
        
        # Analyze enzymes
        enzymes = {
            'ast': 'LBXSATSI',
            'alt': 'ALT_UL',
            'ggt': 'LBXSGTSI',
            'age': 'RIDAGEYR'
        }
        
        thresholds = {}
        
        print("\n📈 ENZYME PATTERNS FROM NHANES:")
        print("-" * 80)
        print(f"{'Enzyme':<10} {'Low Risk Avg':<15} {'High Risk Avg':<15} {'Difference':<12} {'Threshold'}")
        print("-" * 80)
        
        for enzyme, col in enzymes.items():
            low_vals = low_risk[col].dropna()
            high_vals = high_risk[col].dropna()
            
            if len(low_vals) > 0 and len(high_vals) > 0:
                low_avg = low_vals.mean()
                high_avg = high_vals.mean()
                diff = high_avg - low_avg
                
                # Calculate optimal threshold (maximizing separation)
                all_vals = pd.concat([low_vals, high_vals])
                threshold = (low_avg + high_avg) / 2
                
                # Calculate how well this threshold separates the groups
                low_above = (low_vals > threshold).sum() / len(low_vals)
                high_above = (high_vals > threshold).sum() / len(high_vals)
                accuracy = (high_above + (1 - low_above)) / 2
                
                print(f"{enzyme:<10} {low_avg:<15.1f} {high_avg:<15.1f} {diff:<12.1f} {threshold:<8.1f} (acc: {accuracy:.2f})")
                
                thresholds[enzyme] = {
                    'threshold': round(threshold, 1),
                    'weight': round(min(0.4, diff / 100), 2),
                    'accuracy': round(accuracy, 2),
                    'source': 'NHANES'
                }
        
        return thresholds
    
    def analyze_srishti_data(self):
        """Analyze Srishti's liver dataset with fibrosis labels"""
        print("\n🔬 ANALYZING SRISHTI'S LIVER DATA")
        print("="*60)
        
        liver_path = self.data_dir / "liver_dataset.csv"
        if not liver_path.exists():
            print("❌ Srishti's data not found")
            return None
        
        df = pd.read_csv(liver_path)
        print(f"📊 Loaded {len(df)} liver records")
        
        # Find fibrosis column
        fibrosis_col = None
        for col in df.columns:
            if 'Fibrosis' in str(col) and 'status' not in str(col).lower():
                fibrosis_col = col
                break
        
        if not fibrosis_col:
            print("❌ No fibrosis column found")
            return None
        
        # Split by fibrosis
        healthy = df[df[fibrosis_col] == 0]
        diseased = df[df[fibrosis_col] >= 1]
        
        print(f"   Healthy (Fibrosis=0): {len(healthy)} patients")
        print(f"   Diseased (Fibrosis>=1): {len(diseased)} patients")
        
        # Liver enzymes in Srishti's data
        enzyme_cols = {
            'ast': 'AST',
            'alt': 'ALT',
            'ggt': 'GGT',
            'alp': 'ALP',
            'bmi': 'Body Mass Index',
            'glucose': 'Glucose'
        }
        
        thresholds = {}
        
        print("\n📈 ENZYME PATTERNS FROM SRISHTI'S DATA:")
        print("-" * 80)
        print(f"{'Marker':<10} {'Healthy Avg':<15} {'Diseased Avg':<15} {'Difference':<12} {'Threshold'}")
        print("-" * 80)
        
        for enzyme, col in enzyme_cols.items():
            if col in df.columns:
                h_vals = healthy[col].dropna()
                d_vals = diseased[col].dropna()
                
                if len(h_vals) > 0 and len(d_vals) > 0:
                    h_avg = h_vals.mean()
                    d_avg = d_vals.mean()
                    diff = d_avg - h_avg
                    
                    threshold = (h_avg + d_avg) / 2
                    
                    print(f"{enzyme:<10} {h_avg:<15.1f} {d_avg:<15.1f} {diff:<12.1f} {threshold:<8.1f}")
                    
                    thresholds[enzyme] = {
                        'threshold': round(threshold, 1),
                        'weight': round(min(0.4, diff / 100), 2),
                        'source': 'Srishti'
                    }
        
        return thresholds
    
    def analyze_cardio_data(self):
        """Analyze cardio dataset for metabolic patterns"""
        print("\n🔬 ANALYZING CARDIO DATA")
        print("="*60)
        
        cardio_path = self.data_dir / "cardio_dataset.csv"
        if not cardio_path.exists():
            print("❌ Cardio data not found")
            return None
        
        df = pd.read_csv(cardio_path)
        print(f"📊 Loaded {len(df)} cardio records")
        
        # Parse age
        def parse_age(age_str):
            try:
                parts = str(age_str).split()
                return int(parts[0])
            except:
                return 50
        
        df['age_num'] = df['age'].apply(parse_age)
        
        # Look at BMI and glucose patterns
        print("\n📈 METABOLIC PATTERNS FROM CARDIO DATA:")
        print("-" * 60)
        
        patterns = {
            'bmi': {
                'mean': df['bmi'].mean(),
                'std': df['bmi'].std(),
                'high_threshold': df['bmi'].quantile(0.75)
            },
            'age': {
                'mean': df['age_num'].mean(),
                'high_threshold': 45
            }
        }
        
        print(f"BMI - Mean: {patterns['bmi']['mean']:.1f}, High Risk > {patterns['bmi']['high_threshold']:.1f}")
        print(f"Age - High Risk > 45")
        
        return patterns
    
    def generate_unified_thresholds(self):
        """Combine insights from ALL datasets"""
        
        print("\n" + "="*70)
        print("🔄 GENERATING UNIFIED THRESHOLDS FROM ALL DATASETS")
        print("="*70)
        
        # Analyze each dataset
        nhanes = self.analyze_nhanes_data() or {}
        srishti = self.analyze_srishti_data() or {}
        cardio = self.analyze_cardio_data() or {}
        
        # Build unified liver thresholds
        liver_thresholds = {}
        liver_weights = {}
        
        # For each enzyme, take average from available datasets
        enzymes = ['ast', 'alt', 'ggt', 'bmi', 'glucose']
        
        for enzyme in enzymes:
            thresholds = []
            weights = []
            
            if enzyme in nhanes:
                thresholds.append(nhanes[enzyme]['threshold'])
                weights.append(nhanes[enzyme].get('weight', 0.3))
            
            if enzyme in srishti:
                thresholds.append(srishti[enzyme]['threshold'])
                weights.append(srishti[enzyme].get('weight', 0.3))
            
            if thresholds:
                liver_thresholds[enzyme] = round(sum(thresholds) / len(thresholds), 1)
                liver_weights[enzyme] = round(sum(weights) / len(weights) if weights else 0.2, 2)
        
        # Create final config
        config = {
            "liver": {
                "thresholds": liver_thresholds,
                "weights": liver_weights,
                "messages": {
                    "green": "✅ Liver enzymes normal. Low risk of fatty liver.",
                    "yellow": "⚠️ Moderate risk of NAFLD. Consider lifestyle changes.",
                    "red": "🔴 High risk of liver disease. Consult hepatologist."
                }
            },
            "heart": {
                "thresholds": {
                    "systolic_bp": 140,
                    "diastolic_bp": 90,
                    "bmi": cardio.get('bmi', {}).get('high_threshold', 30),
                    "age": 45,
                    "glucose": 110
                },
                "weights": {
                    "systolic_bp": 0.25,
                    "diastolic_bp": 0.2,
                    "bmi": 0.2,
                    "age": 0.2,
                    "glucose": 0.15
                }
            }
        }
        
        # Save to file
        output_path = Path(__file__).parent / "thresholds.json"
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\n✅ FINAL UNIFIED THRESHOLDS:")
        print(json.dumps(config["liver"]["thresholds"], indent=2))
        
        return config


if __name__ == "__main__":
    analyzer = DataAnalyzer()
    analyzer.generate_unified_thresholds()