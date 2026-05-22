import os
import sys
import asyncio
import numpy as np

# Ensure project root is in path
sys.path.insert(0, "/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio")

from engine.api_client import BioChemAPIClient
from engine.server import run_evolution, EFMSolver, filter_and_center_atoms, find_smart_pocket_center, AtomData

async def main():
    client = BioChemAPIClient(cache_dir="/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio/data")
    pdb_content, _ = client.fetch_pdb_file("1HSG")
    target_atoms = client.parse_pdb_coords(pdb_content)
    target_atoms_no_h = [AtomData(**a) for a in target_atoms if a["element"].upper() != "H"]
    
    center = [16.87, 27.39, 3.31]
    target_filtered = filter_and_center_atoms(target_atoms_no_h, center, cutoff=15.0)
    
    solver = EFMSolver(grid_size=32, box_size=16.0)
    target_coords = [[a["x"], a["y"], a["z"]] for a in target_filtered]
    target_charges = [client.get_atomic_number(a["element"]) for a in target_filtered]
    V_target = solver.build_nuclear_potential(target_coords, target_charges)
    
    # Run target alone simulations
    for steps in [30, 100, 500]:
        psi_r, psi_i = solver.run_simulation(V_target, steps=steps)
        E_target = solver.calculate_specific_phase_friction(psi_r, psi_i)
        print(f"Target alone at {steps} steps: E_target = {E_target:.6f}")
        
    # Let's add a seed atom and complex
    # Seed at origin
    seed_sim = [0.0, 0.0, 0.0]
    complex_coords = target_coords + [[seed_sim[0] * solver.S_L, seed_sim[1] * solver.S_L, seed_sim[2] * solver.S_L]]
    complex_charges = target_charges + [6] # Carbon
    V_complex = solver.build_nuclear_potential(complex_coords, complex_charges)
    
    for steps in [30, 100, 500]:
        psi_r, psi_i = solver.run_simulation(V_complex, steps=steps)
        E_complex = solver.calculate_specific_phase_friction(psi_r, psi_i)
        print(f"Complex (Target + 1 Carbon) at {steps} steps: E_complex = {E_complex:.6f}")
        
if __name__ == "__main__":
    asyncio.run(main())
