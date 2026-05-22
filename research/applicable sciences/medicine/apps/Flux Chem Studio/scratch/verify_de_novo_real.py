import os
import sys
import numpy as np
import asyncio

# Ensure project root is in path
sys.path.insert(0, "/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio")

from engine.api_client import BioChemAPIClient
from engine.server import run_evolution, EvolutionRequest, AtomData

async def verify_de_novo(pdb_id, pocket_center=None):
    client = BioChemAPIClient(cache_dir="/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio/data")
    print(f"\n--- Verifying De Novo Evolution for {pdb_id} ---")
    
    # 1. Fetch target pdb
    pdb_content, _ = client.fetch_pdb_file(pdb_id)
    target_atoms = client.parse_pdb_coords(pdb_content)
    print(f"Loaded {len(target_atoms)} target atoms.")
    
    # 2. Setup request
    req = EvolutionRequest(
        target_atoms=[AtomData(**a) for a in target_atoms],
        seed_atoms=[],
        mutations=[],
        pocket_center=pocket_center,
        simulation_steps=100,
        target_class="Viral Protease"
    )
    
    # 3. Run evolution
    res = await run_evolution(req)
    print("Evolution complete.")
    print("Best candidate:", res["best_candidate"])
    print("Predicted pKi:", res["predicted_pki"])
    
    # 4. Check clashes
    sdf_content = res["sdf_content"]
    lines = sdf_content.splitlines()
    atom_lines = lines[4:12] # Evolved 8 atoms
    
    evolved_coords = []
    for line in atom_lines:
        parts = line.split()
        if len(parts) >= 4:
            x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
            evolved_coords.append([x, y, z])
            
    # Calculate min distance of each evolved atom to any target atom (excluding H)
    target_atoms_no_h = [a for a in target_atoms if a["element"].upper() != "H"]
    
    all_min_dists = []
    for i, ec in enumerate(evolved_coords):
        min_dist = float('inf')
        closest_ta = None
        for ta in target_atoms_no_h:
            d = np.sqrt((ec[0] - ta["x"])**2 + (ec[1] - ta["y"])**2 + (ec[2] - ta["z"])**2)
            if d < min_dist:
                min_dist = d
                closest_ta = ta
        all_min_dists.append(min_dist)
        print(f"Evolved Atom {i} at {ec}: Min dist to target = {min_dist:.4f} A (Closest target atom: {closest_ta['element']} at [{closest_ta['x']}, {closest_ta['y']}, {closest_ta['z']}])")
        
    min_dist_overall = min(all_min_dists)
    print(f"Overall Minimum Distance to target: {min_dist_overall:.4f} A")
    
    # Also check self-clashes among evolved atoms
    self_clashes = []
    for i in range(len(evolved_coords)):
        for j in range(i + 1, len(evolved_coords)):
            c1 = evolved_coords[i]
            c2 = evolved_coords[j]
            d = np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2 + (c1[2] - c2[2])**2)
            if d < 1.1:
                self_clashes.append((i, j, d))
                print(f"Self-clash detected between atom {i} and {j}: {d:.4f} A")
                
    if self_clashes:
        print("FAIL: Self-clash detected!")
        return False
        
    if min_dist_overall < 1.0:
        print("FAIL: Target clash detected (< 1.0 A)!")
        return False
        
    print("SUCCESS: No clashes detected!")
    return True

async def main():
    # Verify 1HSG with center
    hsg_ok = await verify_de_novo("1HSG", pocket_center=[16.87, 27.39, 3.31])
    
    # Verify 1HIV with auto center
    hiv_ok = await verify_de_novo("1HIV")
    
    if hsg_ok and hiv_ok:
        print("\nALL DE NOVO CLASH VERIFICATIONS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\nSOME CLASH VERIFICATIONS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
