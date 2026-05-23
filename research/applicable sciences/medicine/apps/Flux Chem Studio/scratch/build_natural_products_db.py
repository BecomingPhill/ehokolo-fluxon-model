import sqlite3
import os
import requests
import json

COMPOUNDS = [
    {
        "name": "Artemisinin",
        "source": "Artemisia annua",
        "area": "Antimalarial",
        "pubchem_name": "artemisinin"
    },
    {
        "name": "Quinine",
        "source": "Cinchona officinalis",
        "area": "Antimalarial",
        "pubchem_name": "quinine"
    },
    {
        "name": "Cryptolepine",
        "source": "Cryptolepis sanguinolenta",
        "area": "Antimalarial / Antimicrobial",
        "pubchem_name": "cryptolepine"
    },
    {
        "name": "Michellamine B",
        "source": "Ancistrocladus korupensis",
        "area": "Antiviral (HIV)",
        "pubchem_name": "michellamine b"
    },
    {
        "name": "Vincristine",
        "source": "Catharanthus roseus",
        "area": "Anticancer",
        "pubchem_name": "vincristine"
    },
    {
        "name": "Vinblastine",
        "source": "Catharanthus roseus",
        "area": "Anticancer",
        "pubchem_name": "vinblastine"
    },
    {
        "name": "Reserpine",
        "source": "Rauvolfia vomitoria",
        "area": "Antihypertensive",
        "pubchem_name": "reserpine"
    },
    {
        "name": "Combretastatin A-4",
        "source": "Combretum caffrum",
        "area": "Anticancer",
        "pubchem_name": "combretastatin a-4"
    },
    {
        "name": "Harpagoside",
        "source": "Harpagophytum procumbens",
        "area": "Anti-inflammatory",
        "pubchem_name": "harpagoside"
    },
    {
        "name": "Kolaflavanone",
        "source": "Garcinia kola",
        "area": "Antioxidant / Hepatoprotective",
        "pubchem_name": "kolaflavanone"
    },
    {
        "name": "Plumbagin",
        "source": "Plumbago zeylanica",
        "area": "Antimicrobial / Anticancer",
        "pubchem_name": "plumbagin"
    },
    {
        "name": "Pristimerin",
        "source": "Maytenus senegalensis",
        "area": "Anticancer / Anti-inflammatory",
        "pubchem_name": "pristimerin"
    },
    {
        "name": "Ursolic Acid",
        "source": "Prunus africana",
        "area": "Anticancer / Anti-inflammatory",
        "pubchem_name": "ursolic acid"
    },
    {
        "name": "Gingerol",
        "source": "Zingiber officinale",
        "area": "Anti-inflammatory",
        "pubchem_name": "gingerol"
    },
    {
        "name": "Shogaol",
        "source": "Zingiber officinale",
        "area": "Anti-inflammatory",
        "pubchem_name": "shogaol"
    }
]

def fetch_sdf(pubchem_name):
    print(f"Fetching {pubchem_name}...")
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{pubchem_name}/SDF?record_type=3d"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.text
    # Fallback to 2D if 3D is not available
    url_2d = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{pubchem_name}/SDF"
    r = requests.get(url_2d, timeout=10)
    if r.status_code == 200:
        return r.text
    raise Exception(f"Failed to fetch {pubchem_name}")

def main():
    db_path = "/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio/data/african_natural_products.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS natural_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            source_organism TEXT,
            therapeutic_area TEXT,
            sdf_content TEXT NOT NULL
        )
    """)
    
    for comp in COMPOUNDS:
        try:
            sdf = fetch_sdf(comp["pubchem_name"])
            cursor.execute("""
                INSERT OR REPLACE INTO natural_products (name, source_organism, therapeutic_area, sdf_content)
                VALUES (?, ?, ?, ?)
            """, (comp["name"], comp["source"], comp["area"], sdf))
            print(f"Successfully saved {comp['name']}.")
        except Exception as e:
            print(f"Error fetching/saving {comp['name']}: {e}")
            
    conn.commit()
    conn.close()
    print("Database build completed.")

if __name__ == "__main__":
    main()
