import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

fig = plt.figure(figsize=(14, 7.2), facecolor='#0a1628')
fig.patch.set_facecolor('#0a1628')

ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 14)
ax.set_ylim(0, 7.2)
ax.axis('off')
ax.set_facecolor('#0a1628')

# ── top accent lines ──────────────────────────────────────────────────────────
for x, color in [(0, '#ffd700'), (3.5, 'white'), (7.0, '#ff4444'), (10.5, '#ffd700')]:
    ax.plot([x, x + 3.4], [7.05, 7.05], color=color, linewidth=4, solid_capstyle='butt')

# ── LEFT PANEL ────────────────────────────────────────────────────────────────
ax.text(0.22, 6.65, 'US', fontsize=38, fontweight='bold',
        color='#00e5ff', va='top', ha='left', fontfamily='monospace')
ax.text(0.22, 5.88, 'WEATHER', fontsize=38, fontweight='bold',
        color='white', va='top', ha='left', fontfamily='monospace')
ax.text(0.22, 5.10, 'PIPELINE', fontsize=38, fontweight='bold',
        color='#ffd700', va='top', ha='left', fontfamily='monospace')

ax.text(0.22, 4.62, 'Live data engineering', fontsize=9, color='#888888', va='top')
ax.text(0.22, 4.37, '10 cities  ·  Open-Meteo + DuckDB + Streamlit', fontsize=9, color='#888888', va='top')

# KEY INSIGHT box
box = FancyBboxPatch((0.18, 1.55), 3.1, 2.65,
    boxstyle='round,pad=0.05', linewidth=1.5,
    edgecolor='#00aa44', facecolor='#0d2a1a')
ax.add_patch(box)
ax.text(0.38, 4.08, 'KEY INSIGHT', fontsize=8.5, fontweight='bold',
        color='#00cc55', va='top')
lines = [
    'Phoenix 93°F vs Seattle 55°F',
    '→ 38°F spread across 10 cities',
    'LA comfort score 89 — best in US',
    'Automated: 0 manual steps per run',
    '$0 API cost — Open-Meteo is free',
]
for i, line in enumerate(lines):
    ax.text(0.38, 3.78 - i * 0.42, line, fontsize=8.8, color='#cccccc', va='top')

# Tech tags — two fixed rows
row1 = [('Python','#3776ab'), ('DuckDB','#ffd700'), ('Streamlit','#ff4b4b')]
row2 = [('Plotly','#636efa'), ('GitHub Actions','#2088ff'), ('Docker','#2496ed')]
for row_tags, row_y in [(row1, 1.18), (row2, 0.65)]:
    tx = 0.18
    for tag, tc in row_tags:
        tw = len(tag) * 0.108 + 0.22
        tag_box = FancyBboxPatch((tx, row_y), tw, 0.36,
            boxstyle='round,pad=0.04', linewidth=1.2,
            edgecolor=tc, facecolor='#0a1628')
        ax.add_patch(tag_box)
        ax.text(tx + tw / 2, row_y + 0.18, tag, fontsize=8, color=tc,
                va='center', ha='center', fontweight='bold')
        tx += tw + 0.1

# ── CENTER — KPI grid (2 rows × 4 cols) ──────────────────────────────────────
CELL_W, CELL_H = 1.52, 1.35
COL_X = [3.68, 5.32, 6.96, 8.60]
ROW_Y = [5.55, 3.95, 2.35]

kpis = [
    # row 0
    ('10',      'Cities Tracked',       '#ffd700'),
    ('2×/day',  'Auto Refresh',         'white'),
    ('11 sec',  'Per Run',              '#00e5ff'),
    ('$0',      'API Cost',             '#00cc55'),
    # row 1
    ('93°F',    'Phoenix — Hottest',    '#ff5500'),
    ('55°F',    'Seattle — Coolest',    '#00ccff'),
    ('89',      'LA Comfort Score',     '#00cc55'),
    ('3.6',     'Miami Severity',       '#ff3333'),
    # row 2
    ('14',      'Fields / City',        '#ffd700'),
    ('4',       'Engineered Features',  '#00e5ff'),
    ('2',       'DB Tables',            'white'),
    ('7d',      'Delta Tracking',       '#00cc55'),
]

for idx, (val, label, color) in enumerate(kpis):
    row, col = divmod(idx, 4)
    cx = COL_X[col] + CELL_W / 2
    cy = ROW_Y[row]
    cell = FancyBboxPatch((COL_X[col], cy - CELL_H + 0.15), CELL_W - 0.1, CELL_H - 0.1,
        boxstyle='round,pad=0.05', linewidth=1,
        edgecolor='#1e3050', facecolor='#0d1e35')
    ax.add_patch(cell)
    ax.text(cx, cy - 0.22, val, fontsize=20, fontweight='bold',
            color=color, va='center', ha='center', fontfamily='monospace')
    ax.text(cx, cy - 0.75, label, fontsize=7.2, color='#777777',
            va='center', ha='center')

# ── RIGHT — temperature bar chart ─────────────────────────────────────────────
cities  = ['Phoenix','Houston','Miami','Boston','Atlanta',
           'New York','Denver','Chicago','Los Angeles','Seattle']
temps   = [93, 85, 84, 84, 79, 80, 80, 77, 65, 55]
clrs    = ['#ff2200','#ff5500','#ff6600','#ff8800','#ffaa00',
           '#ffbb00','#ffcc00','#ffe000','#88cc44','#00aaff']

bar_ax = fig.add_axes([0.749, 0.10, 0.235, 0.80])
bar_ax.set_facecolor('#0a1628')
for spine in bar_ax.spines.values():
    spine.set_visible(False)

y  = np.arange(len(cities))
bars = bar_ax.barh(y, temps, color=clrs, height=0.62, edgecolor='none')
bar_ax.set_yticks(y)
bar_ax.set_yticklabels(cities, fontsize=8.5, color='#cccccc')
bar_ax.set_xticks([])
bar_ax.tick_params(left=False, pad=4)

for i, (bar, t) in enumerate(zip(bars, temps)):
    bar_ax.text(t + 0.5, i, f'{t}°F', va='center', fontsize=8,
                color='#aaaaaa', fontweight='bold')

bar_ax.set_xlim(40, 106)
bar_ax.set_title('Current Temperatures', fontsize=9,
                 color='#666666', pad=6, loc='left')
bar_ax.invert_yaxis()

plt.savefig(r'C:\Users\GAMING\weather_banner_v1.png',
            dpi=150, bbox_inches='tight',
            facecolor='#0a1628', edgecolor='none')
print('Saved!')
