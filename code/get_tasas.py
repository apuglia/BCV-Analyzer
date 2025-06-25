import requests
import os

url = "https://www.bcv.org.ve/cambiaria/export/tasas-informativas-sistema-bancario"
local_path = "../data/raw/tasas_sistema_bancario_full.xls"

os.makedirs(os.path.dirname(local_path), exist_ok=True)
headers = {
    "User-Agent": "Mozilla/5.0"
}
response = requests.get(url, headers=headers, verify=False)
if response.status_code == 200:
    with open(local_path, "wb") as f:
        f.write(response.content)
    print(f"File downloaded to {local_path}")
else:
    print(f"Failed to download file. Status code: {response.status_code}")