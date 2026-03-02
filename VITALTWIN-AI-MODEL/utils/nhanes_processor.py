# utils/nhanes_processor.py

import pandas as pd
import numpy as np

class NHANESProcessor:
    """
    Process NHANES liver enzyme data
    """
    
    def __init__(self, filepath="../data/nhanes_liver_data.csv"):
        self.filepath = filepath
        self.df = None
    
    def load_data(self):
        """Load NHANES data"""
        self.df = pd.read_csv(self.filepath)
        print(f"✅ Loaded {len(self.df)} NHANES records")
        return self.df
    
    def analyze_patterns(self):
        """Find patterns in NHANES data"""
        if self.df is None:
            self.load_data()
        
        print("\n🔍 ANALYZING NHANES LIVER DATA")
        print("="*60)
        
        # Split by Liver_Risk_Score
        low_risk = self.df[self.df['Liver_Risk_Score'] == 0]
        high_risk = self.df[self.df['Liver_Risk_Score'] == 1]
        
        print(f"Low Risk Patients: {len(low_risk)}")
        print(f"High Risk Patients: {len(high_risk)}")
        
        # Analyze key enzymes
        enzymes = {
            'AST': 'LBXSATSI',
            'GGT': 'LBXSGTSI',
            'ALT': 'ALT_UL',
            'Age': 'RIDAGEYR'
        }
        
        print("\n📊 ENZYME LEVELS COMPARISON:")
        print("-" * 70)
        print(f"{'Enzyme':<10} {'Low Risk Avg':<15} {'High Risk Avg':<15} {'Diff':<10} {'Threshold'}")
        print("-" * 70)
        
        thresholds = {}
        
        for name, col in enzymes.items():
            if col in self.df.columns:
                low_avg = low_risk[col].mean() if len(low_risk) > 0 else 0
                high_avg = high_risk[col].mean() if len(high_risk) > 0 else 0
                diff = high_avg - low_avg
                
                # Suggest threshold (between averages)
                threshold = (low_avg + high_avg) / 2
                
                print(f"{name:<10} {low_avg:<15.1f} {high_avg:<15.1f} {diff:<10.1f} {threshold:.1f}")
                
                thresholds[name.lower()] = {
                    'threshold': round(threshold, 1),
                    'low_avg': round(low_avg, 1),
                    'high_avg': round(high_avg, 1)
                }
        
        return thresholds
    
    def get_reference_ranges(self):
        """Get medical reference ranges"""
        ranges = {
            'ast': {'normal': '10-40', 'high': '>40'},
            'alt': {'normal': '7-56', 'high': '>56'},
            'ggt': {'normal': '8-61', 'high': '>61'},
            'ast_alt_ratio': {'normal': '<1', 'alcohol': '>2', 'nash': '1-2'}
        }
        return ranges
    
    def merge_with_other_data(self, other_files):
        """Merge NHANES with Srishti's data"""
        if self.df is None:
            self.load_data()
        
        # Standardize columns
        nhanes_std = self.df.rename(columns={
            'RIDAGEYR': 'age',
            'RIAGENDR': 'gender',
            'LBXSATSI': 'ast',
            'ALT_UL': 'alt',
            'LBXSGTSI': 'ggt',
            'Liver_Risk_Score': 'has_disease'
        })
        
        return nhanes_std


if __name__ == "__main__":
    processor = NHANESProcessor()
    processor.load_data()
    thresholds = processor.analyze_patterns()
    
    print("\n📋 Suggested Thresholds from NHANES:")
    for enzyme, data in thresholds.items():
        print(f"  {enzyme}: > {data['threshold']} = high risk")