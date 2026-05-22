import os
import sys
import json
import numpy as np
import math

# Ensure root directory is in path
BASE_DIR = "/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio"
sys.path.insert(0, BASE_DIR)

from engine.validation_pipeline import get_parent_class, correlation_p_value, write_validation_report

RESULTS_PATH = os.path.join(BASE_DIR, "data", "validation_results.json")

with open(RESULTS_PATH, "r") as f:
    data = json.load(f)

results = data["results"]

# Calculate class-stratified statistics and fit class-by-class calibrations
class_stats = {}
grouped_results = {}
for r in results:
    p_class = get_parent_class(r["target_class"])
    grouped_results.setdefault(p_class, []).append(r)

# Gather all data points
exp_pkis = np.array([r["exp_pki"] for r in results])
pred_scores = np.array([-r["delta_E"] for r in results])

# Standard global calibration as fallback
mean_x = np.mean(exp_pkis)
mean_y = np.mean(pred_scores)
cov = np.sum((exp_pkis - mean_x) * (pred_scores - mean_y))
std_y = np.sqrt(np.sum((pred_scores - mean_y)**2))
global_slope = cov / (std_y**2) if (len(results) > 1 and std_y > 0) else 1.0
global_intercept = mean_x - global_slope * mean_y

class_calibrations = {}
for p_class, class_results in grouped_results.items():
    if len(class_results) >= 3:
        c_exp = np.array([r["exp_pki"] for r in class_results])
        c_pred = np.array([-r["delta_E"] for r in class_results])
        
        c_mean_x = np.mean(c_exp)
        c_mean_y = np.mean(c_pred)
        c_cov = np.sum((c_exp - c_mean_x) * (c_pred - c_mean_y))
        c_std_x = np.sqrt(np.sum((c_exp - c_mean_x)**2))
        c_std_y = np.sqrt(np.sum((c_pred - c_mean_y)**2))
        
        # Pearson and p-value for breakdown
        c_r = c_cov / (c_std_x * c_std_y) if (c_std_x > 0 and c_std_y > 0) else 0.0
        c_p = correlation_p_value(c_r, len(class_results))
        
        class_stats[p_class] = {
            "count": len(class_results),
            "pearson_r": float(c_r),
            "p_value": float(c_p)
        }
        
        # Fit calibration parameters
        if c_std_y > 0:
            c_slope = c_cov / (c_std_y**2)
            c_intercept = c_mean_x - c_slope * c_mean_y
        else:
            c_slope = global_slope
            c_intercept = global_intercept
        class_calibrations[p_class] = (c_slope, c_intercept)
    else:
        class_stats[p_class] = {
            "count": len(class_results),
            "pearson_r": 0.0,
            "p_value": 1.0
        }
        class_calibrations[p_class] = (global_slope, global_intercept)

# Recalculate predictions and residuals class-by-class
for r in results:
    p_class = get_parent_class(r["target_class"])
    c_slope, c_intercept = class_calibrations[p_class]
    pred_val = c_slope * (-r["delta_E"]) + c_intercept
    r["pred_pki"] = float(pred_val)
    r["residual"] = float(r["exp_pki"] - pred_val)

# Update data summary
summary = data["summary"]
summary["class_breakdown"] = class_stats

# Update global MAE using class-stratified predictions
mae = np.mean(np.abs(exp_pkis - np.array([r["pred_pki"] for r in results])))
summary["mae"] = float(mae)

# Save the updated validation results
output_data = {"summary": summary, "results": results}
with open(RESULTS_PATH, "w") as f:
    json.dump(output_data, f, indent=2)

print("Saved updated validation results.")

# Write report
write_validation_report(summary, results)
print("Regenerated validation report.")
