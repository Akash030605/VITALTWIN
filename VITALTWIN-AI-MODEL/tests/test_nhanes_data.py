# tests/test_nhanes_data.py

import sys
import os
import pandas as pd

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.liver_model import LiverModel

def test_with_nhanes():
    """Test liver model with NHANES data"""
    
    print("\n" + "="*70)
    print("🧪 TESTING LIVER MODEL WITH NHANES DATA")
    print("="*70)
    
    # Load NHANES data
    nhanes_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'nhanes_liver_data.csv')
    
    if not os.path.exists(nhanes_path):
        print(f"❌ NHANES data not found at {nhanes_path}")
        print("Please ensure nhanes_liver_data.csv is in the data/ folder")
        return
    
    df = pd.read_csv(nhanes_path)
    print(f"📊 Loaded {len(df)} NHANES patients")
    
    # Initialize model
    print("\n🔄 Initializing Liver Model...")
    model = LiverModel()
    
    # Test first 10 patients
    print("\n📋 FIRST 10 PREDICTIONS:")
    print("-" * 100)
    print(f"{'Patient':<10} {'Age':<6} {'AST':<6} {'ALT':<6} {'GGT':<6} {'Actual':<8} {'Predicted':<10} {'Risk Score':<10}")
    print("-" * 100)
    
    for idx in range(min(10, len(df))):
        patient = df.iloc[idx]
        
        # Prepare data
        data = {
            'age': patient['RIDAGEYR'],
            'ast': patient['LBXSATSI'],
            'alt': patient['ALT_UL'],
            'ggt': patient['LBXSGTSI']
        }
        
        # Get actual risk
        actual_risk = patient['Liver_Risk_Score']
        actual = "HIGH" if actual_risk == 1 else "LOW"
        
        # Predict
        result = model.calculate_risk(data)
        
        print(f"{idx+1:<10} {data['age']:<6} {data['ast']:<6} {data['alt']:<6} {data['ggt']:<6} {actual:<8} {result['level']:<10} {result['risk']:<10.2f}")
        
        # Show factors for first few
        if idx < 3 and result['factors']:
            print(f"  Factors: {', '.join(result['factors'])}")
    
    # Calculate accuracy on all patients
    print("\n" + "="*70)
    print("📊 ACCURACY ANALYSIS")
    print("="*70)
    
    correct = 0
    total = len(df)
    
    for idx, patient in df.iterrows():
        data = {
            'age': patient['RIDAGEYR'],
            'ast': patient['LBXSATSI'],
            'alt': patient['ALT_UL'],
            'ggt': patient['LBXSGTSI']
        }
        
        actual = patient['Liver_Risk_Score']
        result = model.calculate_risk(data)
        
        # Map our levels to binary
        predicted_high = 1 if result['level'] in ['RED', 'YELLOW'] else 0
        
        if predicted_high == actual:
            correct += 1
    
    accuracy = (correct / total) * 100
    print(f"✅ Overall Accuracy: {accuracy:.1f}% ({correct}/{total} patients)")
    
    # Analyze misclassifications
    false_pos = 0
    false_neg = 0
    
    for idx, patient in df.iterrows():
        data = {
            'age': patient['RIDAGEYR'],
            'ast': patient['LBXSATSI'],
            'alt': patient['ALT_UL'],
            'ggt': patient['LBXSGTSI']
        }
        
        actual = patient['Liver_Risk_Score']
        result = model.calculate_risk(data)
        predicted_high = 1 if result['level'] in ['RED', 'YELLOW'] else 0
        
        if actual == 0 and predicted_high == 1:
            false_pos += 1
        elif actual == 1 and predicted_high == 0:
            false_neg += 1
    
    print(f"   False Positives: {false_pos} (predicted high risk but actually low)")
    print(f"   False Negatives: {false_neg} (predicted low risk but actually high)")
    
    # Show some high-risk patients
    print("\n" + "="*70)
    print("🔴 EXAMPLE HIGH-RISK PATIENTS")
    print("="*70)
    
    high_risk_patients = df[df['Liver_Risk_Score'] == 1].head(3)
    for idx, patient in high_risk_patients.iterrows():
        data = {
            'age': patient['RIDAGEYR'],
            'ast': patient['LBXSATSI'],
            'alt': patient['ALT_UL'],
            'gt': patient['LBXSGTSI']
        }
        result = model.calculate_risk(data)
        print(f"\nPatient {idx}:")
        print(f"  Age: {data['age']}, AST: {data['ast']}, ALT: {data['alt']}, GGT: {data.get('ggt', 'N/A')}")
        print(f"  Model says: {result['level']} (Risk: {result['risk']})")
        if result['factors']:
            print(f"  Why: {', '.join(result['factors'])}")


if __name__ == "__main__":
    test_with_nhanes()