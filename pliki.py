Created [](file:///home/kuba/workspace/git2/taryfa-dynamiczna/archiwum)

Ran terminal command: ./myvenv/bin/python -c "
import requests
from lxml import html
import os

url = 'https://tge.pl/RDN_instrumenty_15'
r = requests.get(url, timeout=30)
tree = html.fromstring(r.content)

links = tree.xpath('//a[contains(@href, \".xlsx\") or contains(@href, \".xls\")]/@href')
base_url = 'https://tge.pl'
out_dir = 'archiwum'

for link in links:
    full_url = base_url + link
    filename = link.split('/')[-1]
    filepath = os.path.join(out_dir, filename)
    
    print(f'Pobieram: {filename}...', end=' ')
    try:
        resp = requests.get(full_url, timeout=30)
        resp.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(resp.content)
        print(f'OK ({len(resp.content)} bytes)')
    except Exception as e:
        print(f'BŁĄD: {e}')

print(f'\\nPobrano plików: {len(os.listdir(out_dir))}')
"

Pobrano 48 plików. Teraz sprawdzę strukturę plików Excel, żeby wiedzieć jak wyciągnąć dane godzinowe: 

Ran terminal command: ./myvenv/bin/python -c "
import pandas as pd

# Sprawdzam strukturę jednego pliku
file = 'archiwum/Raport_RDN_dzie_dostawy_delivery_day_2025_10_01.xlsx'
xl = pd.ExcelFile(file)
print('Arkusze:', xl.sheet_names)

# Wczytuję pierwszy arkusz bez nagłówka
df = pd.read_excel(file, sheet_name=0, header=None)
print(f'\\nRozmiar: {df.shape}')
print('\\nPierwsze 30 wierszy:')
print(df.head(30).to_string())
"
