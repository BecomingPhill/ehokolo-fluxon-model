import requests
import json

url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/indinavir/SDF?record_type=3d"
response = requests.get(url)
print("Status:", response.status_code)
if response.status_code == 200:
    print("SDF Length:", len(response.text))
    print(response.text[:200])
else:
    print("Error:", response.text)
