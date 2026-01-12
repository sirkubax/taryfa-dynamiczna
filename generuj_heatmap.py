"""
Skrypt do generowania heatmapy z danych TGE RDN.

Użycie:
    python generuj_heatmap.py <plik_csv>

Przykłady:
    python generuj_heatmap.py tge_rdn_hourly_2025-03.csv
    python generuj_heatmap.py tge_rdn_hourly_2025-12.csv

Plik CSV powinien mieć kolumny:
    date, hour_from, hour_to, price_pln_per_mwh, volume_mwh
"""
import sys
import re

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import calendar


def generate_heatmap(csv_file: str):
    # Wczytaj dane
    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['date'])
    df['day'] = df['date'].dt.day
    
    # Wyciągnij rok i miesiąc z nazwy pliku lub danych
    year = df['date'].dt.year.iloc[0]
    month = df['date'].dt.month.iloc[0]
    month_name = calendar.month_name[month]
    month_str = f"{year}-{month:02d}"
    
    # Pivot table: days as rows, hours as columns
    pivot = df.pivot(index='day', columns='hour_from', values='price_pln_per_mwh')
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Niestandardowa paleta kolorów:
    # fioletowy (ujemne) -> zielony (0-400) -> żółty (400-600) -> czerwony (>600)
    from matplotlib.colors import LinearSegmentedColormap
    colors = [
        (0.5, 0.0, 0.5),    # fioletowy dla ujemnych (-100)
        (0.0, 0.5, 0.0),    # ciemnozielony (0)
        (0.0, 0.8, 0.0),    # zielony (200)
        (0.5, 1.0, 0.0),    # żółtozielony (400)
        (1.0, 1.0, 0.0),    # żółty (500)
        (1.0, 0.5, 0.0),    # pomarańczowy (600)
        (1.0, 0.0, 0.0),    # czerwony (800)
    ]
    # Pozycje kolorów w zakresie 0-1 (mapowane na -100 do 800)
    positions = [0.0, 0.111, 0.333, 0.556, 0.667, 0.778, 1.0]
    cmap = LinearSegmentedColormap.from_list('custom_rdn', list(zip(positions, colors)))
    
    im = ax.imshow(pivot.values, aspect='auto', cmap=cmap, vmin=-100, vmax=800)
    
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
                # Fioletowy (ujemne) - biały tekst
                # Zielony (0-400) - czarny tekst
                # Żółty (400-600) - czarny tekst
                # Pomarańczowy/czerwony (>600) - biały tekst
                if val < 0:
                    text_color = 'white'
                elif val > 600:
                    text_color = 'white'
                else:
                    text_color = 'black'
                ax.text(j, i, f'{val:.0f}', ha='center', va='center', 
                       fontsize=6, color=text_color)
    
    plt.tight_layout()
    
    heatmap_file = f'tge_rdn_heatmap_{month_str}.png'
    plt.savefig(heatmap_file, dpi=150)
    print(f"Saved: {heatmap_file}")
    plt.close()
    
    return heatmap_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    csv_file = sys.argv[1]
    generate_heatmap(csv_file)
