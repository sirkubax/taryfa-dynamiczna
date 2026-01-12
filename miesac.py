import csv
import re
import sys
import calendar
from datetime import date, timedelta

import requests
from lxml import html
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

URL = "https://tge.pl/energia-elektryczna-rdn-tge-base?date_start={d}&iframe=1"

def pl_number_to_float(s: str) -> float | None:
    s = s.strip()
    if s == "-" or s == "":
        return None
    # "3 759,20" -> 3759.20
    s = s.replace("\xa0", "").replace(" ", "").replace(",", ".")
    return float(s)

def fetch_day(d: date):
    url = URL.format(d=d.isoformat())
    print(f"Fetching: {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    
    tree = html.fromstring(r.content)
    
    # Znajdź tabelę z danymi godzinowymi
    table = tree.xpath('//table[@id="footable_kontrakty_godzinowe"]//tbody//tr')
    
    rows = []
    for tr in table:
        cells = tr.xpath('.//td')
        if len(cells) >= 3:
            # Pierwsza kolumna: czas (np. "0-1")
            time_text = cells[0].text_content().strip()
            time_match = re.match(r"(\d{1,2})-(\d{1,2})", time_text)
            if not time_match:
                continue
            h_from = int(time_match.group(1))
            h_to = int(time_match.group(2))
            
            # Druga kolumna: cena
            price_text = cells[1].text_content().strip()
            price = pl_number_to_float(price_text)
            
            # Trzecia kolumna: wolumen
            vol_text = cells[2].text_content().strip()
            vol = pl_number_to_float(vol_text)
            
            rows.append((h_from, h_to, price, vol))

    if len(rows) != 24:
        raise RuntimeError(f"{d}: expected 24 rows, got {len(rows)} (page format may have changed)")

    return rows

def daterange(d1: date, d2: date):
    d = d1
    while d <= d2:
        yield d
        d += timedelta(days=1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python miesac.py <miesiąc> [rok]")
        print("Przykład: python miesac.py 12")
        print("Przykład: python miesac.py 12 2025")
        sys.exit(1)
    
    month = int(sys.argv[1])
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
    
    if month < 1 or month > 12:
        print("Miesiąc musi być liczbą od 1 do 12")
        sys.exit(1)
    
    last_day = calendar.monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)
    
    month_name = calendar.month_name[month]
    month_str = f"{year}-{month:02d}"

    out_csv = f"tge_rdn_hourly_{month_str}.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "hour_from", "hour_to", "price_pln_per_mwh", "volume_mwh"])

        for d in daterange(start, end):
            day_rows = fetch_day(d)
            for h_from, h_to, price, vol in day_rows:
                w.writerow([d.isoformat(), h_from, h_to, price, vol])

    print(f"Saved: {out_csv}")

    # Generate heatmap
    df = pd.read_csv(out_csv)
    df['date'] = pd.to_datetime(df['date'])
    df['day'] = df['date'].dt.day
    
    # Pivot table: days as rows, hours as columns
    pivot = df.pivot(index='day', columns='hour_from', values='price_pln_per_mwh')
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(14, 10))
    
    im = ax.imshow(pivot.values, aspect='auto', cmap='RdYlGn_r')
    
    # Set labels
    ax.set_xticks(np.arange(24))
    ax.set_xticklabels([f'{h}-{h+1}' for h in range(24)])
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels([f'{month_name[:3]} {d}' for d in pivot.index])
    
    ax.set_xlabel('Hour')
    ax.set_ylabel('Day')
    ax.set_title(f'TGE RDN Hourly Prices - {month_name} {year} (PLN/MWh)')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Price (PLN/MWh)')
    
    # Add values in cells
    for i in range(len(pivot.index)):
        for j in range(24):
            val = pivot.values[i, j]
            if not np.isnan(val):
                text_color = 'white' if val > pivot.values.mean() else 'black'
                ax.text(j, i, f'{val:.0f}', ha='center', va='center', 
                       fontsize=6, color=text_color)
    
    plt.tight_layout()
    
    heatmap_file = f'tge_rdn_heatmap_{month_str}.png'
    plt.savefig(heatmap_file, dpi=150)
    print(f"Saved: {heatmap_file}")
    plt.close()

