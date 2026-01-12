Ran terminal command: ./myvenv/bin/python -c "
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import calendar
from matplotlib.colors import LinearSegmentedColormap

# Wczytaj dane dla wszystkich miesięcy
all_data = {}
files = {
    1: 'tge_rdn_hourly_2025-01.csv',
    2: 'tge_rdn_hourly_2025-02.csv',
    3: 'tge_rdn_hourly_2025-03.csv',
    4: 'tge_rdn_hourly_2025-04.csv',
    5: 'tge_rdn_hourly_2025-05.csv',
    6: 'tge_rdn_hourly_2025-06.csv',
    7: 'tge_rdn_hourly_2025-07.csv',
    8: 'tge_rdn_hourly_2025-08.csv',
    9: 'tge_rdn_hourly_2025-09.csv',
    10: 'tge_rdn_hourly_2025-10.xlsx.csv',
    11: 'tge_rdn_hourly_2025-11.csv',
    12: 'tge_rdn_hourly_2025-12.csv',
}

for month, file in files.items():
    df = pd.read_csv(file)
    df['date'] = pd.to_datetime(df['date'])
    df['day'] = df['date'].dt.day
    df = df.groupby(['day', 'hour_from'], as_index=False).agg({'price_pln_per_mwh': 'mean'})
    pivot = df.pivot(index='day', columns='hour_from', values='price_pln_per_mwh')
    all_data[month] = pivot

# Paleta kolorów
colors = [
    (0.5, 0.0, 0.5),    # fioletowy dla ujemnych (-100)
    (0.0, 0.5, 0.0),    # ciemnozielony (0)
    (0.0, 0.8, 0.0),    # zielony (200)
    (0.5, 1.0, 0.0),    # żółtozielony (400)
    (1.0, 1.0, 0.0),    # żółty (500)
    (1.0, 0.5, 0.0),    # pomarańczowy (600)
    (1.0, 0.0, 0.0),    # czerwony (800)
]
positions = [0.0, 0.111, 0.333, 0.556, 0.667, 0.778, 1.0]
cmap = LinearSegmentedColormap.from_list('custom_rdn', list(zip(positions, colors)))

# Utwórz figurę 12x1 (1 kolumna)
fig, axes = plt.subplots(12, 1, figsize=(20, 70))
fig.suptitle('TGE RDN Hourly Prices - 2025 (PLN/MWh)', fontsize=24, fontweight='bold', y=0.995)

for idx, month in enumerate(range(1, 13)):
    ax = axes[idx]
    
    pivot = all_data[month]
    month_name = calendar.month_name[month]
    
    im = ax.imshow(pivot.values, aspect='auto', cmap=cmap, vmin=-100, vmax=800)
    
    ax.set_xticks(np.arange(24))
    ax.set_xticklabels([f'{h}' for h in range(24)], fontsize=8)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels([f'{d}' for d in pivot.index], fontsize=7)
    
    ax.set_xlabel('Hour', fontsize=10)
    ax.set_ylabel('Day', fontsize=10)
    ax.set_title(f'{month_name} 2025', fontsize=14, fontweight='bold')
    
    # Wartości w komórkach
    for i in range(len(pivot.index)):
        for j in range(24):
            val = pivot.values[i, j]
            if not np.isnan(val):
                if val < 0:
                    text_color = 'white'
                elif val > 600:
                    text_color = 'white'
                else:
                    text_color = 'black'
                ax.text(j, i, f'{val:.0f}', ha='center', va='center', 
                       fontsize=5, color=text_color)

# Colorbar na dole
cbar = fig.colorbar(im, ax=axes, orientation='horizontal', fraction=0.01, pad=0.02, aspect=50)
cbar.set_label('Price (PLN/MWh)', fontsize=12)

plt.tight_layout(rect=[0, 0.01, 1, 0.995])
plt.savefig('tge_rdn_heatmap_2025_column.png', dpi=150)
print('Saved: tge_rdn_heatmap_2025_column.png')
"

Ran terminal command: ls -lh tge_rdn_heatmap_2025_column.png
