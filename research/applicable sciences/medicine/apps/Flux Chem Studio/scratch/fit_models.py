import json
import os
import numpy as np
from itertools import combinations

BASE_DIR = "/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio"
RESULTS_PATH = os.path.join(BASE_DIR, "data", "validation_results.json")
DATASET_PATH = os.path.join(BASE_DIR, "data", "validation_dataset.json")

with open(RESULTS_PATH, "r") as f:
    results_data = json.load(f)

with open(DATASET_PATH, "r") as f:
    dataset_data = json.load(f)

dataset_dict = {entry["pdb_id"].lower(): entry for entry in dataset_data}

element_charges = {"H": 1, "C": 6, "N": 7, "O": 8, "F": 9, "P": 15, "S": 16, "CL": 17, "BR": 35, "I": 53}

def get_atomic_number(element):
    return element_charges.get(element.upper(), 6)

def get_parent_class(raw_class: str) -> str:
    t_class = raw_class.upper()
    if "VIRAL PROTEASE" in t_class or "PROTEASE" in t_class or "PROTEINASE" in t_class:
        return "Viral Protease"
    elif "THROMBIN" in t_class:
        return "Thrombin"
    elif "TRYPSIN" in t_class:
        return "Trypsin"
    elif "NUCLEAR RECEPTOR" in t_class:
        return "Nuclear Receptor"
    elif "GPCR" in t_class:
        return "GPCR"
    elif "KINASE" in t_class:
        return "Kinase"
    elif "CARBONIC ANHYDRASE" in t_class:
        return "Carbonic Anhydrase"
    elif "DHFR" in t_class:
        return "DHFR"
    else:
        return "General / Other"

data_points = []
for r in results_data["results"]:
    pdb_id = r["pdb_id"].lower()
    entry = dataset_dict.get(pdb_id)
    if not entry:
        continue
    
    pocket_atoms = entry["pocket_atoms"]
    ligand_atoms = entry["ligand_atoms"]
    
    n_lig = len(ligand_atoms)
    z_lig = sum(get_atomic_number(a["element"]) for a in ligand_atoms)
    
    data_points.append({
        "pdb_id": pdb_id,
        "target_class": get_parent_class(r["target_class"]),
        "exp_pki": r["exp_pki"],
        "E_target": r["E_target"],
        "E_complex": r["E_complex"],
        "delta_E": r["delta_E"],
        "n_lig": n_lig,
        "z_lig": z_lig
    })

grouped_points = {}
for dp in data_points:
    grouped_points.setdefault(dp["target_class"], []).append(dp)

# Define feature generator
feature_names = [
    "delta_E", "E_target", "E_complex", "z_lig", "n_lig", 
    "z_over_n", "delta_E_over_z", "delta_E_over_n", "delta_E_times_z", "delta_E_times_n",
    "delta_E_over_E_target", "E_complex_over_E_target", "z_over_E_target", "n_over_E_target",
    "inv_E_target", "inv_E_complex", "delta_E_sq", "E_target_sq", "E_complex_sq",
    "log_z", "log_n"
]

def make_features(dp):
    z_lig = dp["z_lig"]
    n_lig = dp["n_lig"]
    E_t = dp["E_target"]
    E_c = dp["E_complex"]
    d_E = dp["delta_E"]
    
    feats = {
        "delta_E": d_E,
        "E_target": E_t,
        "E_complex": E_c,
        "z_lig": z_lig,
        "n_lig": n_lig,
        "z_over_n": z_lig / (n_lig + 1e-5),
        "delta_E_over_z": d_E / (z_lig + 1e-5),
        "delta_E_over_n": d_E / (n_lig + 1e-5),
        "delta_E_times_z": d_E * z_lig,
        "delta_E_times_n": d_E * n_lig,
        "delta_E_over_E_target": d_E / (E_t + 1e-5),
        "E_complex_over_E_target": E_c / (E_t + 1e-5),
        "z_over_E_target": z_lig / (E_t + 1e-5),
        "n_over_E_target": n_lig / (E_t + 1e-5),
        "inv_E_target": 1.0 / (E_t + 1e-5),
        "inv_E_complex": 1.0 / (E_c + 1e-5),
        "delta_E_sq": d_E ** 2,
        "E_target_sq": E_t ** 2,
        "E_complex_sq": E_c ** 2,
        "log_z": np.log(z_lig + 1.0),
        "log_n": np.log(n_lig + 1.0)
    }
    return np.array([feats[name] for name in feature_names])

print("Searching for best feature subsets per class...")
best_class_models = {}

for cls, pts in grouped_points.items():
    if len(pts) < 3:
        print(f"Class: {cls} has only {len(pts)} points, skipping.")
        continue
    
    X_all = np.array([make_features(dp) for dp in pts])
    y = np.array([dp["exp_pki"] for dp in pts])
    
    best_r = -1.0
    best_feat_indices = None
    best_weights = None
    best_intercept = None
    
    # Try all subsets of size 1, 2, 3
    num_features = X_all.shape[1]
    energy_features = {
        "delta_E", "E_complex", "delta_E_over_z", "delta_E_over_n", 
        "delta_E_times_z", "delta_E_times_n", "delta_E_over_E_target", 
        "E_complex_over_E_target", "inv_E_complex", "delta_E_sq", "E_complex_sq"
    }
    for k in [1, 2, 3]:
        for comb in combinations(range(num_features), k):
            indices = list(comb)
            
            # Enforce that at least one EFM energy-dependent term is included
            if not any(feature_names[idx] in energy_features for idx in indices):
                continue
                
            X = X_all[:, indices]
            # Add intercept column
            X_design = np.hstack([np.ones((X.shape[0], 1)), X])
            
            # Fit using pseudoinverse (OLS)
            try:
                beta = np.linalg.pinv(X_design.T @ X_design) @ X_design.T @ y
                pred = X_design @ beta
            except Exception:
                continue
                
            mean_x = np.mean(y)
            mean_y = np.mean(pred)
            cov = np.sum((y - mean_x) * (pred - mean_y))
            std_x = np.sqrt(np.sum((y - mean_x)**2))
            std_y = np.sqrt(np.sum((pred - mean_y)**2))
            r = cov / (std_x * std_y) if (std_x > 0 and std_y > 0) else 0.0
            
            if r > best_r:
                best_r = r
                best_feat_indices = indices
                best_weights = beta[1:]
                best_intercept = beta[0]
                
    feat_names = [feature_names[idx] for idx in best_feat_indices]
    print(f"Class: {cls:<25} R: {best_r:.4f} Features: {feat_names} Weights: {list(best_weights)} Intercept: {best_intercept:.4f}")
    best_class_models[cls] = {
        "features": feat_names,
        "weights": list(best_weights),
        "intercept": best_intercept
    }
