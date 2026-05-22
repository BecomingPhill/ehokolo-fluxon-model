import os
import sys
import numpy as np
import torch

# Add parent directory to path so we can import engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.solver import EFMSolver
from engine.api_client import BioChemAPIClient

def parse_pdb_full(pdb_content):
    """
    Parses PDB file content fully, including chain ID and residue index.
    """
    atoms = []
    for line in pdb_content.splitlines():
        if line.startswith("ATOM") or line.startswith("HETATM"):
            try:
                atom_name = line[12:16].strip()
                res_name = line[17:20].strip()
                chain = line[21]
                res_num = int(line[22:26].strip())
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
                element = line[76:78].strip()
                if not element:
                    element = atom_name[0]
                    if element in ['1', '2', '3', '4']:
                        element = atom_name[1]
                atoms.append({
                    "element": element,
                    "x": x, "y": y, "z": z,
                    "atom_name": atom_name,
                    "residue": res_name,
                    "chain": chain,
                    "res_num": res_num
                })
            except Exception:
                continue
    return atoms

def align_coordinates(ref_atoms, mob_atoms):
    """
    Calculates the Kabsch rotation matrix R and translation vector t
    to align mobile CA atoms to reference CA atoms.
    """
    # Extract CA atoms of reference (excluding ligand MK1)
    ref_ca = {}
    for a in ref_atoms:
        if a["residue"] != "MK1" and a["atom_name"] == "CA":
            ref_ca[(a["chain"], a["res_num"])] = np.array([a["x"], a["y"], a["z"]])
            
    # Extract CA atoms of mobile (excluding ligand ROC)
    mob_ca = {}
    for a in mob_atoms:
        if a["residue"] != "ROC" and a["atom_name"] == "CA":
            mob_ca[(a["chain"], a["res_num"])] = np.array([a["x"], a["y"], a["z"]])
            
    # Find matching CA atoms
    common_keys = sorted(list(set(ref_ca.keys()) & set(mob_ca.keys())))
    if len(common_keys) < 3:
        raise ValueError("Not enough matching CA atoms for alignment.")
        
    P = np.array([mob_ca[k] for k in common_keys])
    Q = np.array([ref_ca[k] for k in common_keys])
    
    # Calculate centroids
    centroid_P = np.mean(P, axis=0)
    centroid_Q = np.mean(Q, axis=0)
    
    P_centered = P - centroid_P
    Q_centered = Q - centroid_Q
    
    # SVD for rotation
    H = np.dot(P_centered.T, Q_centered)
    U, S, Vt = np.linalg.svd(H)
    R = np.dot(Vt.T, U.T)
    
    # Handle reflection
    if np.linalg.det(R) < 0:
        Vt[2,:] *= -1
        R = np.dot(Vt.T, U.T)
        
    t = centroid_Q - np.dot(R, centroid_P)
    return R, t

def main():
    print("=============================================================")
    print("Flux Chem Studio - Eholoko Fluxon Model (EFM) Benchmark Run")
    print("=============================================================")
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    client = BioChemAPIClient(cache_dir=DATA_DIR)
    
    # 1. Load PDB 1HSG (HIV-1 Protease)
    print("\n[1/4] Loading Target PDB: 1HSG...")
    try:
        pdb_content, pdb_path = client.fetch_pdb_file("1hsg")
        ref_atoms = parse_pdb_full(pdb_content)
        target_atoms = [a for a in ref_atoms if a["residue"] != "MK1"]
        crystal_indinavir = [a for a in ref_atoms if a["residue"] == "MK1"]
        print(f"Loaded 1HSG: {len(target_atoms)} protein atoms, {len(crystal_indinavir)} crystal Indinavir atoms.")
    except Exception as e:
        print(f"Error fetching 1HSG: {e}")
        return

    # Calculate active site pocket center (center of mass of crystal Indinavir)
    if len(crystal_indinavir) > 0:
        cx = sum(a["x"] for a in crystal_indinavir) / len(crystal_indinavir)
        cy = sum(a["y"] for a in crystal_indinavir) / len(crystal_indinavir)
        cz = sum(a["z"] for a in crystal_indinavir) / len(crystal_indinavir)
        pocket_center = [cx, cy, cz]
    else:
        pocket_center = [16.0, 14.0, 3.0] # Fallback standard center for 1hsg
        
    print(f"Computed Pocket Center (from crystal Indinavir): {pocket_center}")
    
    # 2. Extract/Load ligands from local PDBs or cache
    print("\n[2/4] Loading Ligand Coordinates...")
    ligands_to_test = {}
    
    # Ligand 1: Indinavir (from 1HSG)
    if len(crystal_indinavir) > 0:
        # Align: Indinavir is already aligned to 1HSG pocket, just needs to be centered relative to pocket_center
        indinavir_centered = []
        for a in crystal_indinavir:
            indinavir_centered.append({
                "element": a["element"],
                "x": a["x"] - pocket_center[0],
                "y": a["y"] - pocket_center[1],
                "z": a["z"] - pocket_center[2]
            })
        ligands_to_test["Indinavir (Crystal Ref)"] = indinavir_centered
        print(f"  -> Loaded Indinavir (Crystal Ref): {len(crystal_indinavir)} atoms.")
        
    # Ligand 2: Saquinavir (aligned from 3OXC using Kabsch algorithm)
    try:
        print("Loading and aligning Saquinavir from 3oxc...")
        content_3oxc, _ = client.fetch_pdb_file("3oxc")
        mob_atoms = parse_pdb_full(content_3oxc)
        saquinavir_atoms = [a for a in mob_atoms if a["residue"] == "ROC"]
        
        if len(saquinavir_atoms) > 0:
            # Align mobile protein 3oxc to reference protein 1hsg
            R, t = align_coordinates(ref_atoms, mob_atoms)
            
            # Apply transformation to Saquinavir atoms
            saquinavir_aligned = []
            for a in saquinavir_atoms:
                coord = np.array([a["x"], a["y"], a["z"]])
                coord_trans = np.dot(R, coord) + t
                # Center it in simulation box relative to pocket_center
                saquinavir_aligned.append({
                    "element": a["element"],
                    "x": coord_trans[0] - pocket_center[0],
                    "y": coord_trans[1] - pocket_center[1],
                    "z": coord_trans[2] - pocket_center[2]
                })
            ligands_to_test["Saquinavir (ROC - Aligned)"] = saquinavir_aligned
            print(f"  -> Aligned Saquinavir (ROC): {len(saquinavir_aligned)} atoms.")
        else:
            print("  -> Warning: Saquinavir (ROC) not found in 3oxc.")
    except Exception as e:
        print(f"  -> Error loading/aligning Saquinavir: {e}")
        
    # Ligand 3: Quinine (from local SDF)
    try:
        print("Loading Quinine from data/quinine.sdf...")
        with open(os.path.join(DATA_DIR, "quinine.sdf"), "r") as f:
            content_quinine = f.read()
        quinine_atoms = client.parse_sdf_coords(content_quinine)
        if len(quinine_atoms) > 0:
            # Shift relative to its own COM to place at pocket center
            l_cx = sum(a["x"] for a in quinine_atoms) / len(quinine_atoms)
            l_cy = sum(a["y"] for a in quinine_atoms) / len(quinine_atoms)
            l_cz = sum(a["z"] for a in quinine_atoms) / len(quinine_atoms)
            
            quinine_centered = []
            for a in quinine_atoms:
                quinine_centered.append({
                    "element": a["element"],
                    "x": a["x"] - l_cx,
                    "y": a["y"] - l_cy,
                    "z": a["z"] - l_cz
                })
            ligands_to_test["Quinine (QNN)"] = quinine_centered
            print(f"  -> Loaded Quinine (QNN): {len(quinine_atoms)} atoms.")
    except Exception as e:
        print(f"  -> Error loading Quinine: {e}")
        
    # Ligand 4: Artemether (from 6FGD)
    try:
        print("Loading Artemether from 6fgd...")
        content_6fgd, _ = client.fetch_pdb_file("6fgd")
        atoms_6fgd = parse_pdb_full(content_6fgd)
        artemether_atoms = [a for a in atoms_6fgd if a["residue"] == "D8Z"]
        if len(artemether_atoms) > 0:
            # Shift relative to its own COM to place at pocket center
            l_cx = sum(a["x"] for a in artemether_atoms) / len(artemether_atoms)
            l_cy = sum(a["y"] for a in artemether_atoms) / len(artemether_atoms)
            l_cz = sum(a["z"] for a in artemether_atoms) / len(artemether_atoms)
            
            artemether_centered = []
            for a in artemether_atoms:
                artemether_centered.append({
                    "element": a["element"],
                    "x": a["x"] - l_cx,
                    "y": a["y"] - l_cy,
                    "z": a["z"] - l_cz
                })
            ligands_to_test["Artemether (D8Z)"] = artemether_centered
            print(f"  -> Loaded Artemether (D8Z): {len(artemether_atoms)} atoms.")
        else:
            print("  -> Warning: Artemether (D8Z) not found in 6fgd.")
    except Exception as e:
        print(f"  -> Error loading Artemether: {e}")
        
    # Ligand 5: Steric Clash Control (Saquinavir shifted into protein core)
    if "Saquinavir (ROC - Aligned)" in ligands_to_test:
        clash_atoms = []
        for a in ligands_to_test["Saquinavir (ROC - Aligned)"]:
            clash_atoms.append({
                "element": a["element"],
                "x": a["x"] + 1.2,  # Shift significantly to force steric overlap
                "y": a["y"] + 1.2,
                "z": a["z"] + 1.2
            })
        ligands_to_test["Steric Clash Control"] = clash_atoms
        print(f"  -> Added Steric Clash Control: {len(clash_atoms)} atoms.")

    # 3. Setup EFM Solver
    print("\n[3/4] Initializing EFM Solver...")
    solver = EFMSolver(grid_size=32, box_size=16.0)
    
    # Filter target atoms within 15A cutoff of pocket center and shift to (0,0,0)
    target_filtered = []
    for a in target_atoms:
        dist = np.sqrt((a["x"] - pocket_center[0])**2 + (a["y"] - pocket_center[1])**2 + (a["z"] - pocket_center[2])**2)
        if dist <= 15.0:
            target_filtered.append({
                "element": a["element"],
                "x": a["x"] - pocket_center[0],
                "y": a["y"] - pocket_center[1],
                "z": a["z"] - pocket_center[2]
            })
            
    print(f"Active site pocket atoms (within 15A cutoff): {len(target_filtered)}")
    
    # Pre-compute Target Alone Potential & Relaxation
    print("Simulating Target Protein pocket alone (relaxation)...")
    target_coords = [[a["x"], a["y"], a["z"]] for a in target_filtered]
    target_charges = [client.get_atomic_number(a["element"]) for a in target_filtered]
    V_target = solver.build_nuclear_potential(target_coords, target_charges)
    psi_target_r, psi_target_i = solver.run_simulation(V_target, steps=500)
    E_target = solver.calculate_specific_phase_friction(psi_target_r, psi_target_i)
    print(f"Target Alone Phase Friction (E_target): {E_target:.6f}")
    
    # 4. Run screening for each ligand
    print("\n[4/4] Running EFM Screening Simulations...")
    results = []
    
    for name, lig_centered in ligands_to_test.items():
        if len(lig_centered) == 0:
            continue
            
        print(f"Simulating complex with {name}...")
        
        # Build complex potential
        complex_coords = target_coords + [[a["x"], a["y"], a["z"]] for a in lig_centered]
        complex_charges = target_charges + [client.get_atomic_number(a["element"]) for a in lig_centered]
        V_complex = solver.build_nuclear_potential(complex_coords, complex_charges)
        
        # Relax complex field
        psi_complex_r, psi_complex_i = solver.run_simulation(V_complex, steps=500)
        E_complex = solver.calculate_specific_phase_friction(psi_complex_r, psi_complex_i)
        
        # Shift
        delta_E = E_complex - E_target
        results.append({
            "name": name,
            "E_complex": E_complex,
            "delta_E": delta_E,
            "favorable": delta_E < 0
        })
        print(f"  -> {name} | E_complex: {E_complex:.6f} | delta_E: {delta_E:.6f} | Favorable: {delta_E < 0}")
        
    # Print comparison table
    print("\n" + "="*85)
    print(f"{'Ligand Candidate':<30} | {'E_complex':<12} | {'delta_E (Shift)':<16} | {'Status':<12}")
    print("="*85)
    
    # Sort results by delta_E (lower is better binding)
    results_sorted = sorted(results, key=lambda x: x["delta_E"])
    for r in results_sorted:
        status = "FAVORABLE" if r["favorable"] else "UNFAVORABLE"
        print(f"{r['name']:<30} | {r['E_complex']:<12.6f} | {r['delta_E']:<16.6f} | {status:<12}")
    print("="*85)
    print("Note: Under Eholoko Fluxon Model (EFM), more negative delta_E indicates lower phase friction,")
    print("which corresponds to higher electronic stability and stronger binding affinity.")
    print("=============================================================")

if __name__ == "__main__":
    main()
