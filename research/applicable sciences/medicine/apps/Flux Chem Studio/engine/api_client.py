import os
import requests
import json

class BioChemAPIClient:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def fetch_pdb_file(self, pdb_id):
        """Downloads a PDB file from RCSB PDB database and caches it."""
        pdb_id = pdb_id.lower().strip()
        local_path = os.path.join(self.cache_dir, f"{pdb_id}.pdb")
        
        if os.path.exists(local_path):
            with open(local_path, 'r') as f:
                return f.read(), local_path
                
        url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            with open(local_path, 'w') as f:
                f.write(content)
            return content, local_path
        else:
            raise Exception(f"PDB ID '{pdb_id}' not found in RCSB database.")
            
    def fetch_pubchem_sdf(self, compound_name):
        """Downloads a 3D SDF structure file for a compound from PubChem and caches it."""
        compound_name = compound_name.lower().strip()
        local_path = os.path.join(self.cache_dir, f"{compound_name}.sdf")
        
        if os.path.exists(local_path):
            with open(local_path, 'r') as f:
                return f.read(), local_path
                
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/SDF?record_type=3d"
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            with open(local_path, 'w') as f:
                f.write(content)
            return content, local_path
        else:
            # Fallback to 2D structure if 3D is not available
            url_2d = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/SDF"
            response_2d = requests.get(url_2d)
            if response_2d.status_code == 200:
                content = response_2d.text
                with open(local_path, 'w') as f:
                    f.write(content)
                return content, local_path
            raise Exception(f"Compound '{compound_name}' not found in PubChem.")

    def search_pdb(self, query_text):
        """Searches the RCSB PDB for protein structures matching a search term and fetches their metadata."""
        url = "https://search.rcsb.org/rcsbsearch/v2/query"
        query_json = {
            "query": {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "rcsb_entry_info.title",
                    "operator": "contains_phrase",
                    "value": query_text
                }
            },
            "return_type": "entry"
        }
        
        response = requests.post(url, json=query_json)
        if response.status_code != 200:
            return []
            
        results = response.json()
        entries = [item["identifier"] for item in results.get("result_set", [])]
        pdb_ids = entries[:15]  # Limit to top 15 results
        
        if not pdb_ids:
            return []
            
        # Bulk query metadata via GraphQL
        graphql_url = "https://data.rcsb.org/graphql"
        ids_str = ", ".join(f'"{pdb_id}"' for pdb_id in pdb_ids)
        graphql_query = f"""
        query {{
          entries(entry_ids: [{ids_str}]) {{
            rcsb_id
            struct {{
              title
            }}
            struct_keywords {{
              pdbx_keywords
            }}
            polymer_entities {{
              rcsb_entity_source_organism {{
                ncbi_scientific_name
              }}
            }}
          }}
        }}
        """
        
        metadata_map = {}
        try:
            gql_res = requests.post(graphql_url, json={"query": graphql_query}, timeout=10)
            if gql_res.status_code == 200:
                data = gql_res.json().get("data", {})
                for entry in data.get("entries", []):
                    rcsb_id = entry.get("rcsb_id")
                    if not rcsb_id:
                        continue
                    title = entry.get("struct", {}).get("title") if entry.get("struct") else None
                    keywords = entry.get("struct_keywords", {}).get("pdbx_keywords") if entry.get("struct_keywords") else None
                    
                    # Gather unique organisms
                    organisms = []
                    for pe in entry.get("polymer_entities", []) or []:
                        for org in pe.get("rcsb_entity_source_organism", []) or []:
                            name = org.get("ncbi_scientific_name")
                            if name and name not in organisms:
                                organisms.append(name)
                    organism = ", ".join(organisms) if organisms else None
                    
                    metadata_map[rcsb_id.upper()] = {
                        "pdb_id": rcsb_id,
                        "title": title or "N/A",
                        "classification": keywords or "N/A",
                        "organism": organism or "N/A"
                    }
        except Exception:
            pass # fallback to basic entries if GraphQL fails
            
        # Return in the original search order, filling in metadata
        final_results = []
        for pdb_id in pdb_ids:
            pdb_id_upper = pdb_id.upper()
            if pdb_id_upper in metadata_map:
                final_results.append(metadata_map[pdb_id_upper])
            else:
                final_results.append({
                    "pdb_id": pdb_id,
                    "title": "N/A",
                    "classification": "N/A",
                    "organism": "N/A"
                })
        return final_results

    def parse_pdb_coords(self, pdb_content):
        """
        Parses a PDB file to extract atomic coordinates and details.
        Returns a list of dicts: [{'element': 'C', 'x': 12.3, 'y': 4.5, 'z': -1.2, 'atom_name': 'CA', 'residue': 'ASP'}]
        """
        atoms = []
        for line in pdb_content.splitlines():
            if line.startswith("ATOM") or line.startswith("HETATM"):
                # PDB column formats are fixed-width:
                # 13-16: Atom name
                # 17-20: Residue name
                # 31-38: X coordinate
                # 39-46: Y coordinate
                # 47-54: Z coordinate
                # 77-78: Element symbol
                try:
                    atom_name = line[12:16].strip()
                    res_name = line[17:20].strip()
                    res_num = int(line[22:26].strip())
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip())
                    z = float(line[46:54].strip())
                    element = line[76:78].strip()
                    
                    if not element:
                        # Fallback if element column is empty: guess from atom name
                        element = atom_name[0]
                        if element in ['1', '2', '3', '4']:
                            element = atom_name[1]
                            
                    atoms.append({
                        "element": element,
                        "x": x,
                        "y": y,
                        "z": z,
                        "atom_name": atom_name,
                        "residue": res_name,
                        "residue_id": res_num
                    })
                except Exception:
                    continue
        return atoms

    def parse_sdf_coords(self, sdf_content):
        """
        Parses an SDF file to extract 3D coordinates.
        Returns a list of dicts: [{'element': 'O', 'x': 0.1, 'y': 1.4, 'z': 0.0}]
        """
        atoms = []
        lines = sdf_content.splitlines()
        if len(lines) < 4:
            return atoms
            
        # Parse counts line (line index 3) to get number of atoms
        counts_line = lines[3]
        try:
            num_atoms = int(counts_line[:3].strip())
            
            # Atom block starts at index 4
            for i in range(4, 4 + num_atoms):
                line = lines[i]
                # Coordinates are in columns: X (0-10), Y (10-20), Z (20-30), Element (31-34)
                x = float(line[0:10].strip())
                y = float(line[10:20].strip())
                z = float(line[20:30].strip())
                element = line[31:34].strip()
                
                atoms.append({
                    "element": element,
                    "x": x,
                    "y": y,
                    "z": z
                })
        except Exception:
            pass
            
        return atoms
        
    def get_atomic_number(self, element):
        """Maps an element symbol to its atomic number Z (used as charges in EFM)."""
        mapping = {
            'H': 1, 'HE': 2, 'LI': 3, 'BE': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'NE': 10,
            'NA': 11, 'MG': 12, 'AL': 13, 'SI': 14, 'P': 15, 'S': 16, 'CL': 17, 'AR': 18, 'K': 19,
            'CA': 20, 'FE': 26, 'CU': 29, 'ZN': 30, 'BR': 35, 'I': 53
        }
        return mapping.get(element.upper(), 6) # Default to Carbon (Z=6) if unknown
