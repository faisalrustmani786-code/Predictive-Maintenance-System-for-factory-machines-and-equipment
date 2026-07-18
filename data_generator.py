import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_synthetic_data(n_machines=8, n_steps=3000, output_path="data/machine_sensor_log.csv"):
    """
    Generates synthetic sensor data for multiple machines to simulate
    normal operation, degradation, and sudden failure patterns.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    machine_types = [
        "Main Motor", "Air Compressor", "Water Pump", "Cooling Fan",
        "Conveyor Belt", "Robot Arm", "Power Generator", "Heating Unit"
    ]
    
    # Baseline normal operating ranges
    baselines = {
        "temperature_c": {"mean": 45.0, "std": 2.0},
        "vibration_mm_s": {"mean": 2.5, "std": 0.3},
        "pressure_bar": {"mean": 6.0, "std": 0.5},
        "current_a": {"mean": 15.0, "std": 1.0},
        "rpm": {"mean": 1500.0, "std": 10.0}
    }
    
    data = []
    start_time = datetime(2026, 7, 14, 8, 0, 0)
    
    print(f"Generating data for {n_machines} machines ({n_steps} steps each)...")
    
    for i in range(n_machines):
        machine_id = f"M{str(i+1).zfill(2)}"
        machine_type = machine_types[i % len(machine_types)]
        
        # Decide machine behavior pattern:
        # 0: Normal (50%), 1: Gradual Degradation (35%), 2: Sudden Failure (15%)
        behavior_rand = np.random.rand()
        if behavior_rand < 0.50:
            behavior = "normal"
        elif behavior_rand < 0.85:
            behavior = "degradation"
        else:
            behavior = "sudden_failure"
            
        # Initialize machine state
        state = {
            "temperature_c": np.random.normal(baselines["temperature_c"]["mean"], baselines["temperature_c"]["std"]),
            "vibration_mm_s": np.random.normal(baselines["vibration_mm_s"]["mean"], baselines["vibration_mm_s"]["std"]),
            "pressure_bar": np.random.normal(baselines["pressure_bar"]["mean"], baselines["pressure_bar"]["std"]),
            "current_a": np.random.normal(baselines["current_a"]["mean"], baselines["current_a"]["std"]),
            "rpm": np.random.normal(baselines["rpm"]["mean"], baselines["rpm"]["std"]),
        }
        
        runtime = 0.0
        rul_base = np.random.uniform(500, 1500) # Base remaining useful life in hours
        
        # Determine failure point if applicable
        if behavior == "degradation":
            failure_step = np.random.randint(int(n_steps * 0.5), int(n_steps * 0.9))
        elif behavior == "sudden_failure":
            failure_step = np.random.randint(int(n_steps * 0.2), int(n_steps * 0.8))
        else:
            failure_step = n_steps + 1000 # Won't fail during simulation
            
        for step in range(n_steps):
            timestamp = start_time + timedelta(minutes=step * 5)
            runtime += 5 / 60.0 # 5 minutes in hours
            
            # 1. Normal noise
            for key in state.keys():
                state[key] += np.random.normal(0, baselines[key]["std"] * 0.1)
                
            # Pull back slightly to mean (mean reversion for stability in normal mode)
            for key in state.keys():
                state[key] = state[key] * 0.95 + baselines[key]["mean"] * 0.05
                
            # 2. Apply degradation / failure patterns
            rul = rul_base - runtime
            health_label = "Normal"
            
            if behavior == "degradation" and step > failure_step - int(n_steps * 0.3):
                # Gradual degradation phase
                progress = (step - (failure_step - int(n_steps * 0.3))) / (int(n_steps * 0.3))
                state["vibration_mm_s"] += np.random.normal(0.01 * progress, 0.05)
                state["temperature_c"] += np.random.normal(0.05 * progress, 0.1)
                state["current_a"] += np.random.normal(0.02 * progress, 0.05)
                
                rul = max(0, ((failure_step - step) * 5) / 60.0)
                
                if progress > 0.7:
                    health_label = "Critical"
                elif progress > 0.3:
                    health_label = "Warning"
                    
            elif behavior == "sudden_failure" and step > failure_step - 20:
                # Sudden failure spike
                state["vibration_mm_s"] += np.random.normal(1.0, 0.5)
                state["pressure_bar"] -= np.random.normal(0.5, 0.1)
                state["temperature_c"] += np.random.normal(2.0, 1.0)
                
                rul = max(0, ((failure_step - step) * 5) / 60.0)
                
                if step > failure_step - 5:
                    health_label = "Critical"
                else:
                    health_label = "Warning"
                    
            if rul <= 0:
                health_label = "Critical"
                rul = 0.0
                # Machine is broken, values go wild or flatline
                state["rpm"] = np.random.normal(0, 10) # stopped
                state["current_a"] = np.random.normal(0, 0.5)
            
            # Ensure physical constraints
            state["rpm"] = max(0, state["rpm"])
            state["vibration_mm_s"] = max(0, state["vibration_mm_s"])
            state["current_a"] = max(0, state["current_a"])
            
            row = {
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "machine_id": machine_id,
                "machine_type": machine_type,
                "temperature_c": round(state["temperature_c"], 2),
                "vibration_mm_s": round(state["vibration_mm_s"], 3),
                "pressure_bar": round(state["pressure_bar"], 2),
                "current_a": round(state["current_a"], 2),
                "rpm": round(state["rpm"], 0),
                "runtime_hours": round(runtime, 1),
                "health_label": health_label,
                "rul_hours": round(rul, 1)
            }
            data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} rows. Saved to {output_path}")
    return df

if __name__ == "__main__":
    generate_synthetic_data()
