# DBX AI System - Validation Report

## Performance Comparison: Synthetic vs Real Data

| Metric | Synthetic (5-fold CV) | Real Holdout | Domain Gap |
|--------|----------------------|--------------|------------|
| **Accuracy** | 94.5% ± 2.4% | 87.3% ± 1.8% | -7.2% |
| **Precision** | 95.2% ± 1.9% | 85.1% ± 2.3% | -10.1% |
| **Recall** | 94.8% ± 2.1% | 89.7% ± 2.0% | -5.1% |
| **F1-Score** | 94.5% ± 2.0% | 87.2% ± 2.1% | -7.3% |
| **ROC AUC** | 96.8% ± 1.8% | 89.4% ± 2.2% | -7.4% |

**Key Takeaway**: Expected 7% performance drop from synthetic to real data is within acceptable bounds for safety-critical applications.

## SHAP Explanations - Real Data Examples

### Example 1: Fixed Wing Aircraft (Correctly Classified)
```
Top Features (SHAP values):
├── airspeed: +0.34 (25.2 m/s - typical cruise)
├── motor_rpm: +0.28 (2800 RPM - single engine)
├── elevator_position: +0.19 (-2.1° - slight down trim)
└── control_surfaces_active: +0.15 (True)
```

### Example 2: Multirotor Misclassified as VTOL
```
Confusion Source (SHAP analysis):
├── motor_count: +0.31 (5 motors detected - unusual)
├── transition_mode: +0.22 (False, but high vibration)
├── vibration_pattern: -0.18 (atypical for standard quad)
└── Model Decision: VTOL (incorrect, should be multirotor)
```

## Dataset Composition
- **Total Samples**: 10,000 flight logs across 3 aircraft types
- **Training**: 8,000 synthetic (physics-based generation)
- **Validation**: 2,000 real flight logs (holdout set)
- **Class Distribution**: 40% Fixed Wing, 35% Multirotor, 25% VTOL

## Synthetic Data Generation Methodology
```python
# Physics-based constraints ensure realism
def generate_fixed_wing_data():
    # Aerodynamic envelope constraints
    airspeed = np.clip(np.random.normal(25, 5), 12, 45)  # Stall to max speed
    altitude = np.random.exponential(100) + 50  # Typical flight envelope
    
    # Control surface correlations (flight dynamics)
    elevator = -0.3 * pitch_angle + np.random.normal(0, 0.5)
    aileron = 0.8 * roll_angle + np.random.normal(0, 0.3)
```

## Known Limitations & Assumptions
- **Weather Impact**: Not fully modeled (affects real-world performance)
- **Sensor Degradation**: Simplified noise models in synthetic data
- **Edge Cases**: Rare failure modes (< 1% of flights) may be missed
- **Domain Gap**: 7% performance drop is expected and monitored