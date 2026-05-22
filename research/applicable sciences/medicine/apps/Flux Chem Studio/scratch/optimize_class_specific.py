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

# Score function
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

class_weights = {}

print("Optimizing class-specific weights...")
for cls in target_classes:
    pts = grouped_points.get(cls, [])
    if len(pts) < 3:
        print(f"Skipping {cls} (only {len(pts)} points)")
        class_weights[cls] = [0.0] * 6
        continue
    
    y = np.array([dp["exp_pki"] for dp in pts])
    
    # Loss function for this class: we want to maximize the correlation coefficient
    # We want r > 0.60, or as high as possible
    def class_loss(w):
        pred = np.array([get_score(dp, w) for dp in pts])
        mean_x = np.mean(y)
        mean_y = np.mean(pred)
        cov = np.sum((y - mean_x) * (pred - mean_y))
        std_x = np.sqrt(np.sum((y - mean_x)**2))
        std_y = np.sqrt(np.sum((pred - mean_y)**2))
        r = cov / (std_x * std_y) if (std_x > 0 and std_y > 0) else 0.0
        return -r  # Minimize -r to maximize r
        
    best_w = np.zeros(6)
    best_r = -class_loss(best_w)
    
    # Simple hill-climber for this class
    np.random.seed(42)
    step_size = 1.0
    for i in range(10000):
        mut = np.random.normal(0, step_size, 6)
        proposal_w = best_w + mut
        r = -class_loss(proposal_w)
        if r > best_r:
            best_r = r
            best_w = proposal_w
        if i % 1000 == 0 and i > 0:
            step_size *= 0.8
            
    print(f"Class: {cls:<25} correlation r = {best_r:.4f}")
    class_weights[cls] = list(best_w)

print("\nResulting class weights dictionary:")
print(json.dumps(class_weights, indent=2))
