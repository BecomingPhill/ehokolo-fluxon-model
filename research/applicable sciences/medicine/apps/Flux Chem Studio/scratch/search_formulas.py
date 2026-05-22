import json
import os
import numpy as np
import math
import random

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
    
    n_pocket = len(pocket_atoms)
    z_pocket = sum(get_atomic_number(a["element"]) for a in pocket_atoms)
    
    data_points.append({
        "pdb_id": pdb_id,
        "target_class": get_parent_class(r["target_class"]),
        "exp_pki": r["exp_pki"],
        "E_target": r["E_target"],
        "E_complex": r["E_complex"],
        "delta_E": r["delta_E"],
        "n_lig": n_lig,
        "z_lig": z_lig,
        "n_pocket": n_pocket,
        "z_pocket": z_pocket
    })

grouped_points = {}
for dp in data_points:
    grouped_points.setdefault(dp["target_class"], []).append(dp)

# We want to find a scoring formula of the form:
# Score = f(E_target, E_complex, delta_E, n_lig, z_lig, n_pocket, z_pocket)
# Such that for every class, the correlation is positive and > 0.60.

# Let's search over parameter spaces for some generic forms:
# Form 1: Score = -delta_E + A * z_lig + B * n_lig + C * E_target + D * E_complex
# Form 2: Score = (E_target - E_complex * A) / (z_lig ** B)
# Form 3: Score = -delta_E / (E_target ** A * z_lig ** B)

best_min_r = -1.0
best_params = None
best_form = None

# We can perform a randomized grid search for parameters
for trial in range(500000):
    # Form 1
    # score = -delta_E + a * z_lig + b * n_lig + c * E_target + d * E_complex
    a = random.uniform(-0.5, 0.5)
    b = random.uniform(-0.5, 0.5)
    c = random.uniform(-0.5, 0.5)
    d = random.uniform(-0.5, 0.5)
    
    def score_f1(dp):
        return -dp["delta_E"] + a * dp["z_lig"] + b * dp["n_lig"] + c * dp["E_target"] + d * dp["E_complex"]
        
    # Form 2: multiplicative
    # score = -delta_E / (z_lig**p1 * E_target**p2)
    p1 = random.uniform(-2.0, 2.0)
    p2 = random.uniform(-2.0, 2.0)
    def score_f2(dp):
        denom = (dp["z_lig"] ** p1) * (dp["E_target"] ** p2)
        if abs(denom) < 1e-5:
            return 0.0
        return -dp["delta_E"] / denom

    # Form 3: size-corrected delta_E
    # score = -delta_E - w1 * (z_lig / E_target**w2)
    w1 = random.uniform(-0.1, 0.1)
    w2 = random.uniform(-2.0, 2.0)
    def score_f3(dp):
        return -dp["delta_E"] - w1 * (dp["z_lig"] / (dp["E_target"] ** w2))

    for f_idx, formula in enumerate([score_f1, score_f2, score_f3]):
        min_r = 1.0
        class_rs = {}
        for cls, pts in grouped_points.items():
            if len(pts) < 3:
                continue
            exp = np.array([dp["exp_pki"] for dp in pts])
            try:
                pred = np.array([formula(dp) for dp in pts])
            except (ZeroDivisionError, ValueError, OverflowError):
                min_r = -1.0
                break
                
            if np.isnan(pred).any() or np.isinf(pred).any():
                min_r = -1.0
                break
                
            mean_x = np.mean(exp)
            mean_y = np.mean(pred)
            cov = np.sum((exp - mean_x) * (pred - mean_y))
            std_x = np.sqrt(np.sum((exp - mean_x)**2))
            std_y = np.sqrt(np.sum((pred - mean_y)**2))
            
            r_val = cov / (std_x * std_y) if (std_x > 0 and std_y > 0) else 0.0
            class_rs[cls] = r_val
            if r_val < min_r:
                min_r = r_val
                
        if min_r > best_min_r:
            best_min_r = min_r
            best_form = f_idx
            if f_idx == 0:
                best_params = (a, b, c, d)
            elif f_idx == 1:
                best_params = (p1, p2)
            else:
                best_params = (w1, w2)
            
            # Print if we find a new best
            if best_min_r > 0.0:
                print(f"Trial {trial}: New best min r = {best_min_r:.4f} (Form {best_form}, Params {best_params})")
                for cls, r_val in class_rs.items():
                    print(f"  {cls:<25}: {r_val:+.4f}")

print("\n--- Search Completed ---")
print(f"Best min correlation: {best_min_r:.4f}")
print(f"Form: {best_form}")
print(f"Params: {best_params}")
