#!/usr/bin/env python3
# api/simple_wrapper.py

import sys
import json
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation_engine import VitalTwinSimulator

def main():
    """Read input from Spring Boot and output results"""
    try:
        # Initialize simulator once (for performance)
        simulator = VitalTwinSimulator()
        
        # Read input
        if len(sys.argv) > 1:
            input_json = sys.argv[1]
        else:
            input_json = sys.stdin.read()
        
        user_data = json.loads(input_json)
        
        # Run simulation with all features
        results = simulator.run_simulation(user_data, include_what_if=True)
        
        # Output results
        print(json.dumps(results))
        
    except Exception as e:
        import traceback
        error_result = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "status": "failed"
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()