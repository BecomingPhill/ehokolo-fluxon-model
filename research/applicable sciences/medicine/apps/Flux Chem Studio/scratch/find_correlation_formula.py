import json
import os
import numpy as np
import math

BASE_DIR = "/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio"
RESULTS_PATH = os.path.join(BASE_DIR, "data", "validation_results.json")
DATASET_PATH = os.path.join(BASE_DIR, "data", "validation_dataset.json")

with open(RESULTS_PATH, "r") as f:
    results_data = json.load(f)

with open(DATASET_PATH, "r") as f:
    dataset_data = json.load(f)

# Map pdb_id to dataset entry for quick lookup
dataset_dict = {entry["pdb_id"].lower(): entry for entry in dataset_data}

# Get atomic number mapping
element_charges = {"H": 1, "C": 6, "N": 7, "O": 8, "F": 9, "P": 15, "S": 16, "CL": 17, "BR": 35, "I": 53, "ZN": 30, "FE": 26, "CA": 20, "MG": 12, "NA": 11, "K": 19}

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

# Compile features for each entry
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

# Group data points by class
grouped_points = {}
for dp in data_points:
    grouped_points.setdefault(dp["target_class"], []).append(dp)

print(f"Total data points: {len(data_points)}")
for cls, pts in grouped_points.items():
    print(f"Class: {cls}, Count: {len(pts)}")

# Try different formulas and compute correlation for each class
formulas = {
    "raw_delta_E": lambda dp: -dp["delta_E"],
    "normalized_by_n_lig": lambda dp: -dp["delta_E"] / dp["n_lig"],
    "normalized_by_z_lig": lambda dp: -dp["delta_E"] / dp["z_lig"],
    "normalized_by_sqrt_z_lig": lambda dp: -dp["delta_E"] / math.sqrt(dp["z_lig"]),
    "E_ratio": lambda dp: dp["E_target"] / dp["E_complex"],
    "log_E_ratio": lambda dp: math.log(dp["E_target"] / dp["E_complex"]),
    "shifted_ratio": lambda dp: (dp["E_target"] - dp["E_complex"]) / (dp["E_target"] + 0.1),
    "size_corrected_delta": lambda dp: -dp["delta_E"] - 0.005 * dp["z_lig"],
    "size_corrected_ratio": lambda dp: (dp["E_target"] / dp["E_complex"]) * (dp["z_lig"] ** 0.1),
    "ligand_potential_scaled": lambda dp: -dp["delta_E"] * (dp["E_target"] / (dp["z_lig"] ** 0.5)),
}

for name, formula in formulas.items():
    print(f"\nEvaluating Formula: {name}")
    print("-" * 50)
    for cls, pts in sorted(grouped_points.items()):
        if len(pts) < 3:
            continue
        exp = np.array([dp["exp_pki"] for dp in pts])
        pred = np.array([formula(dp) for dp in pts])
        
        # Pearson
        mean_x = np.mean(exp)
        mean_y = np.mean(pred)
        cov = np.sum((exp - mean_x) * (pred - mean_y))
        std_x = np.sqrt(np.sum((exp - mean_x)**2))
        std_y = np.sqrt(np.sum((pred - mean_y)**2))
        
        r_val = cov / (std_x * std_y) if (std_x > 0 and std_y > 0) else 0.0
        print(f"  {cls:<25} | Pearson r: {r_val:+.4f}")
