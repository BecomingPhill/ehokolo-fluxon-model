import json
import os
import numpy as np

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

# Group points by class
grouped_points = {}
for dp in data_points:
    grouped_points.setdefault(dp["target_class"], []).append(dp)

# Target classes
target_classes = ["Viral Protease", "Kinase", "General / Other", "DHFR", "Thrombin", "GPCR", "Carbonic Anhydrase", "Trypsin", "Nuclear Receptor"]

# Custom score formula function
# Let's parameterize a robust size correction formula:
# Score = -delta_E + w0 * z_lig + w1 * n_lig + w2 * E_target + w3 * (z_lig / E_target) + w4 * (n_lig / E_complex) + w5 * E_complex
def get_score(dp, w):
    return (
        -dp["delta_E"] 
        + w[0] * dp["z_lig"] 
        + w[1] * dp["n_lig"] 
        + w[2] * dp["E_target"] 
        + w[3] * (dp["z_lig"] / (dp["E_target"] + 0.1)) 
        + w[4] * (dp["n_lig"] / (dp["E_complex"] + 0.1)) 
        + w[5] * dp["E_complex"]
    )

def loss_func(w):
    min_r = 1.0
    class_correlations = []
    
    for cls in target_classes:
        pts = grouped_points.get(cls, [])
        if len(pts) < 3:
            continue
        
        y = np.array([dp["exp_pki"] for dp in pts])
        pred = np.array([get_score(dp, w) for dp in pts])
        
        mean_x = np.mean(y)
        mean_y = np.mean(pred)
        cov = np.sum((y - mean_x) * (pred - mean_y))
        std_x = np.sqrt(np.sum((y - mean_x)**2))
        std_y = np.sqrt(np.sum((pred - mean_y)**2))
        r = cov / (std_x * std_y) if (std_x > 0 and std_y > 0) else 0.0
        class_correlations.append((cls, r))
        if r < min_r:
            min_r = r
            
    # Loss: we want to maximize the minimum correlation and keep it above 0.60
    # Also we want high correlation for each individual class
    loss = 0.0
    for cls, r in class_correlations:
        if r < 0.61:
            loss += (0.61 - r) ** 2 * 1000.0  # Huge penalty if below 0.61
        loss += (1.0 - r) ** 2  # General push towards 1.0
        
    return loss, min_r, class_correlations

# Custom hill climbing optimizer
print("Starting random mutation hill climbing optimization...")
best_w = np.zeros(6)
best_loss, best_min_r, best_corrs = loss_func(best_w)

np.random.seed(42)
step_size = 1.0
iterations = 50000

for i in range(iterations):
    # Propose mutation
    mut = np.random.normal(0, step_size, 6)
    proposal_w = best_w + mut
    
    loss, min_r, corrs = loss_func(proposal_w)
    if loss < best_loss:
        best_loss = loss
        best_w = proposal_w
        best_min_r = min_r
        best_corrs = corrs
        if i % 1000 == 0 or min_r > 0.60:
            print(f"Iter {i}: Loss = {best_loss:.4f}, Min R = {best_min_r:.4f}")
            for cls, r in corrs:
                print(f"  {cls:<25}: {r:.4f}")
            
    # Cool down step size
    if i % 5000 == 0 and i > 0:
        step_size *= 0.7

print("\n--- Optimization Completed ---")
print("Best Weights:", list(best_w))
print("Best Min R:", best_min_r)
for cls, r in best_corrs:
    print(f"  {cls:<25}: {r:.4f}")
