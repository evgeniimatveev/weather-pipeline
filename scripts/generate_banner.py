import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

fig = plt.figure(figsize=(16, 8.0), facecolor='#0a1117')
fig.patch.set_facecolor('#0a1117')

ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 16)
ax.set_ylim(0, 8.0)
ax.axis('off')
ax.set_facecolor('#0a1117')

# ── top accent lines ──────────────────────────────────────────────────────────
segments = [(0, '#ffd700'), (4.0, 'white'), (8.0, '#ff4444'), (12.0, '#00e5ff')]
for x, color in segments:
    ax.plot([x, x + 3.9], [7.82, 7.82], color=color, linewidth=5, solid_capstyle='butt')

# ── LEFT PANEL — title ────────────────────────────────────────────────────────
ax.text(0.25, 7.55, 'GLOBAL', fontsize=40, fontweight='bold',
        color='#00e5ff', va='top', ha='left', fontfamily='monospace')
ax.text(0.25, 6.70, 'WEATHER', fontsize=40, fontweight='bold',
        color='white', va='top', ha='left', fontfamily='monospace')
ax.text(0.25, 5.85, 'PIPELINE', fontsize=40, fontweight='bold',
        color='#ffd700', va='top', ha='left', fontfamily='monospace')

ax.text(0.25, 5.35, 'Live data engineering', fontsize=9.5, color='#666666', va='top')
ax.text(0.25, 5.08, '20 cities · 6 continents · Open-Meteo + DuckDB + Streamlit', fontsize=9, color='#555555', va='top')

# KEY INSIGHT box
box = FancyBboxPatch((0.20, 1.62), 3.45, 3.20,
    boxstyle='round,pad=0.06', linewidth=1.5,
    edgecolor='#00aa44', facecolor='#071a0f')
ax.add_patch(box)
ax.text(0.42, 4.70, 'KEY INSIGHT', fontsize=9, fontweight='bold', color='#00cc55', va='top')
lines = [
    'Phoenix 94°F vs Seattle 58°F',
    '→ 36°F spread across 6 continents',
    'Berlin score 93 — best city today',
    'Mexico City severity 5.8 — harshest',
    '$0 API cost · 0 manual steps per run',
]
for i, line in enumerate(lines):
    ax.text(0.42, 4.36 - i * 0.44, line, fontsize=9, color='#bbbbbb', va='top')

# Tech tags — two rows
row1 = [('Python','#3776ab'), ('DuckDB','#ffd700'), ('Streamlit','#ff4b4b')]
row2 = [('Plotly','#636efa'), ('GitHub Actions','#2088ff'), ('Docker','#2496ed')]
for row_tags, row_y in [(row1, 1.22), (row2, 0.66)]:
    tx = 0.20
    for tag, tc in row_tags:
        tw = len(tag) * 0.115 + 0.26
        tag_box = FancyBboxPatch((tx, row_y), tw, 0.38,
            boxstyle='round,pad=0.04', linewidth=1.3,
            edgecolor=tc, facecolor='#0a1117')
        ax.add_patch(tag_box)
        ax.text(tx + tw / 2, row_y + 0.19, tag, fontsize=8.5, color=tc,
                va='center', ha='center', fontweight='bold')
        tx += tw + 0.12

# ── CENTER — KPI grid 3 rows × 4 cols ────────────────────────────────────────
CELL_W, CELL_H = 1.60, 1.38
COL_X = [4.10, 5.82, 7.54, 9.26]
ROW_Y = [7.45, 5.82, 4.19]

kpis = [
    # row 0 — pipeline stats
    ('20',       'Cities Tracked',        '#ffd700'),
    ('2×/day',   'Auto Refresh',          'white'),
    ('45 sec',   'Per Run',               '#00e5ff'),
    ('$0',       'API Cost',              '#00cc55'),
    # row 1 — live snapshot
    ('94°F',     'Phoenix — Hottest',     '#ff5500'),
    ('58°F',     'Seattle — Coolest',     '#00ccff'),
    ('Berlin',   'Best City Score 93',    '#00cc55'),
    ('5.8',      'Mexico City Severity',  '#ff3333'),
    # row 2 — engineering depth
    ('4',        'DB Tables',             '#ffd700'),
    ('5',        'Engineered Features',   '#00e5ff'),
    ('140',      'Forecast Rows / Run',   'white'),
    ('7d',       'Forecast Horizon',      '#00cc55'),
]

for idx, (val, label, color) in enumerate(kpis):
    row, col = divmod(idx, 4)
    cx = COL_X[col] + CELL_W / 2
    cy = ROW_Y[row]
    cell = FancyBboxPatch((COL_X[col], cy - CELL_H + 0.18), CELL_W - 0.12, CELL_H - 0.12,
        boxstyle='round,pad=0.06', linewidth=1,
        edgecolor='#1a2744', facecolor='#0d1929')
    ax.add_patch(cell)
    fs = 17 if len(val) > 5 else 21
    ax.text(cx, cy - 0.25, val, fontsize=fs, fontweight='bold',
            color=color, va='center', ha='center', fontfamily='monospace')
    ax.text(cx, cy - 0.82, label, fontsize=7, color='#666666',
            va='center', ha='center')

# ── RIGHT — global temperature bar chart ──────────────────────────────────────
cities = ['Phoenix','Miami','Houston','Boston','London',
          'Dubai','Denver','New York','Paris','Singapore']
temps  = [94, 85, 85, 84, 83, 82, 79, 79, 79, 77]
clrs   = ['#ff2200','#ff5500','#ff6600','#ff8800','#ffaa00',
          '#ffbb00','#ffcc00','#ffdd00','#ccdd00','#88cc44']

bar_ax = fig.add_axes([0.718, 0.085, 0.268, 0.845])
bar_ax.set_facecolor('#0a1117')
for spine in bar_ax.spines.values():
    spine.set_visible(False)

y = np.arange(len(cities))
bars = bar_ax.barh(y, temps, color=clrs, height=0.60, edgecolor='none')
bar_ax.set_yticks(y)
bar_ax.set_yticklabels(cities, fontsize=9, color='#cccccc')
bar_ax.set_xticks([])
bar_ax.tick_params(left=False, pad=5)

for i, (bar, t) in enumerate(zip(bars, temps)):
    bar_ax.text(t + 0.4, i, f'{t}°F', va='center', fontsize=8.5,
                color='#999999', fontweight='bold')

bar_ax.set_xlim(55, 108)
bar_ax.set_title('Top 10 Temperatures · Live', fontsize=9.5,
                 color='#555555', pad=8, loc='left')
bar_ax.invert_yaxis()

# subtle vertical divider between center and right
ax.plot([11.42, 11.42], [0.3, 7.75], color='#1a2030', linewidth=1)

plt.savefig(r'C:\Users\GAMING\weather-pipeline\assets\weather_banner_v2.png',
            dpi=150, bbox_inches='tight',
            facecolor='#0a1117', edgecolor='none')
print('Banner saved!')
