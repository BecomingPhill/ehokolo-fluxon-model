import sys
import os
import numpy as np

# Ensure engine path is available
sys.path.insert(0, "/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio")
from engine.api_client import BioChemAPIClient
from engine.server import detect_target_class, find_smart_pocket_center, parse_pdb_full_from_content, AtomData

client = BioChemAPIClient(cache_dir="/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio/data")

NTD_PDB_IDS = {
    "Malaria DHFR (P. falciparum)": "1J3J",
    "Tuberculosis InhA (M. tuberculosis)": "1ZID",
    "Malaria Kelch13 Propeller (P. falciparum)": "4XT7",
    "Sleeping Sickness Trypanothione Reductase (T. brucei)": "2W0C",
    "Leishmaniasis DHFR-TS (L. major)": "1D7A",
    "Schistosomiasis TGR (S. mansoni)": "2V6O"
}

def main():
    for name, pdb_id in NTD_PDB_IDS.items():
        try:
            content, path = client.fetch_pdb_file(pdb_id)
            dict_atoms = client.parse_pdb_coords(content)
            
            # Wrap in AtomData
            atoms = [AtomData(**a) for a in dict_atoms]
            
            # Use smart pocket center
            center = find_smart_pocket_center(atoms)
            print(f"Target: {name} (PDB: {pdb_id})")
            print(f"  Smart Pocket Center: [{center[0]:.4f}, {center[1]:.4f}, {center[2]:.4f}]")
            print(f"  Parsed Atoms count: {len(atoms)}")
            
        except Exception as e:
            print(f"Error checking {name} ({pdb_id}): {e}")

if __name__ == "__main__":
    main()
