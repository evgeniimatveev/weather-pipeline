# US Weather Pipeline

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-1.5.3-FFF000?logo=duckdb&logoColor=black)
![Streamlit](https://img.shields.io/badge/Streamlit-1.57-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-6.7-3F4F75?logo=plotly&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2×/day-2088FF?logo=githubactions&logoColor=white)
[![HuggingFace](https://img.shields.io/badge/🤗_HuggingFace-Spaces-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/spaces/evgeniimatveevusa/weather-pipeline)

![Banner](assets/weather_banner_v1.png)

Production-grade live weather pipeline for **10 major US cities** — from API ingestion to engineered features, DuckDB storage, and a real-time Streamlit dashboard. Refreshed automatically **twice a day** via GitHub Actions.

> "Built an end-to-end data engineering pipeline with zero manual steps: API → transform → store → visualize → automate."

**[Live Demo → HuggingFace Spaces](https://huggingface.co/spaces/evgeniimatveevusa/weather-pipeline)**

---

## Screenshots

<details>
<summary>🌍 Temperature Map & KPI Row</summary>

![Overview](assets/overview.png)

</details>

<details>
<summary>🏙️ City Cards — Current Conditions</summary>

![Cities](assets/cities.png)

</details>

<details>
<summary>📈 Temperature Trends & Comfort Index</summary>

![Trends](assets/trends.png)

</details>

<details>
<summary>⚠️ Severity Score & Wind Analysis</summary>

![Severity](assets/severity.png)

</details>

<details>
<summary>🔁 Pipeline Runs Log</summary>

![Runs](assets/runs.png)

</details>

---

## Key Metrics (Live Data)

| Metric | Value |
|--------|-------|
| Cities tracked | **10 major US cities** |
| Pipeline frequency | **2× daily** — 8am ET + 8pm ET |
| Pipeline runtime | **~11 seconds** per run |
| Data fields per city | **10 raw + 4 engineered** |
| Engineered features | Comfort Index · Severity Score · 7-day delta |
| Hottest city (sample) | **Phoenix** → 93°F |
| Coolest city (sample) | **Seattle** → 55°F |
| Most comfortable | **Los Angeles** → Comfort Score 89 |
| Harshest conditions | **Miami** → Severity 3.6 |
| API cost | **$0** — Open-Meteo is free, no key required |
| Storage | DuckDB embedded — full history, zero ops |

---

## Architecture

```
Open-Meteo API (free · no key)
        ↓  httpx — async-style sequential fetch
   extract.py  ← 10 cities · 8 fields each
        ↓  pandas transforms
   transform.py  ← temperature_f · feels_like_f · comfort_index · severity_score
        ↓  duckdb INSERT
   data/weather.duckdb
        ├── weather_history   ← all runs appended
        └── pipeline_runs     ← audit log per run
        ↓  upload_db.py
   HuggingFace Dataset (evgeniimatveevusa/weather-db)
        ↓  Streamlit reads from HF at startup
   Dashboard (5 sections · Plotly)
        ↓  Docker
   HuggingFace Spaces (always-on · auto-rebuild)
        ↑
   GitHub Actions (cron 2×/day · workflow_dispatch)
```

---

## Engineered Features

This pipeline doesn't just store raw API data — it computes analytical features on every run:

| Feature | Formula | Range | Meaning |
|---------|----------|-------|---------|
| `temperature_f` | `(°C × 9/5) + 32` | — | US-standard temperature |
| `feels_like_f` | same conversion | — | Apparent temperature in °F |
| `comfort_index` | `100 - temp_penalty - humidity_penalty - wind_penalty` | 0–100 | Higher = more pleasant |
| `severity_score` | `1 + precip_risk + wind_gusts + UV_index` | 1–10 | Higher = harsher conditions |
| `delta_temp_7d` | `current_temp - 7d_avg` | — | Is today warmer or cooler than usual? |

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Data source | Open-Meteo API (free · no auth) |
| HTTP client | httpx |
| Database | DuckDB 1.5.3 (embedded, zero config) |
| DB storage | HuggingFace Dataset (binary file sync) |
| Transformation | pandas + custom feature engineering |
| Dashboard | Streamlit + Plotly |
| Containerization | Docker |
| Automation | GitHub Actions (cron schedule) |
| Deployment | HuggingFace Spaces (Docker SDK) |

---

## Dashboard Sections

**KPI Row** — Hottest / Coolest / Most Comfortable / Harshest / Avg Humidity — live snapshot across all 10 cities

**Temperature Map** — US scatter_geo with color scale (°F) + bubble size = Comfort Index

**City Cards** — Per-city metric grid: temp in °F + °C, feels-like, humidity, wind, precip %, UV — plus delta vs 7-day average

**Temperature Trends** — Multi-line chart across all cities over time (history grows with every pipeline run)

**Comfort Index** — Horizontal bar chart, ranked green → red (0–100 scale)

**Severity Score & Precipitation Risk** — Heatmap-styled table sorted by severity + Wind Speed vs Gusts scatter

**Pipeline Runs Log** — Every run tracked: run ID, timestamp, duration, rows inserted, status ✅/❌

---

## Quick Start

### Option A — Docker

```bash
git clone https://github.com/evgeniimatveev/weather-pipeline.git
cd weather-pipeline
docker build -t weather-pipeline .
docker run -p 7860:7860 \
  -e HF_DATASET_REPO=evgeniimatveevusa/weather-db \
  weather-pipeline
```
Open **http://localhost:7860**

### Option B — Python

```bash
git clone https://github.com/evgeniimatveev/weather-pipeline.git
cd weather-pipeline

pip install -r requirements.txt

# Run the pipeline once to populate the DB
python run_pipeline.py

# Launch dashboard locally
streamlit run dashboard/app.py
```

---

## Automation — GitHub Actions

The pipeline runs **fully automatically** — no manual steps required after deploy:

```yaml
on:
  schedule:
    - cron: "0 13 * * *"   # 8am ET every day
    - cron: "0 1  * * *"   # 8pm ET every day
  workflow_dispatch:        # manual trigger from GitHub UI
```

**Each run:**
1. Downloads latest `weather.duckdb` from HuggingFace Dataset
2. Fetches fresh weather for all 10 cities
3. Appends to `weather_history` + logs to `pipeline_runs`
4. Uploads updated DB back to HuggingFace Dataset
5. Dashboard on HF Spaces reads the updated file on next load

---

## Project Structure

```
weather-pipeline/
├── src/
│   ├── extract.py        # Open-Meteo API fetch — 10 cities, 8 fields
│   ├── transform.py      # Feature engineering — °F, comfort, severity, delta
│   └── load.py           # DuckDB write — weather_history + pipeline_runs
├── dashboard/
│   └── app.py            # Streamlit app — map, cards, trends, severity, runs log
├── scripts/
│   ├── upload_db.py      # DuckDB → HuggingFace Dataset
│   └── download_db.py    # HuggingFace Dataset → DuckDB
├── .github/
│   └── workflows/
│       └── pipeline.yml  # GitHub Actions cron automation
├── run_pipeline.py       # Orchestrator — extract → transform → load
├── Dockerfile            # HF Spaces compatible (port 7860)
├── requirements.txt
└── .gitignore            # data/ excluded — DB lives on HuggingFace
```

---

## Data Schema

**`weather_history`** — one row per city per pipeline run

| Column | Type | Description |
|--------|------|-------------|
| `city` | VARCHAR | City name |
| `fetched_at` | TIMESTAMPTZ | UTC timestamp of fetch |
| `temperature_c` / `_f` | FLOAT | Air temperature |
| `feels_like_c` / `_f` | FLOAT | Apparent temperature |
| `precipitation_mm` | FLOAT | Current precipitation |
| `precipitation_prob_pct` | FLOAT | Probability of rain (%) |
| `wind_speed_kmh` | FLOAT | Wind speed |
| `wind_gusts_kmh` | FLOAT | Wind gusts |
| `humidity_pct` | FLOAT | Relative humidity |
| `uv_index` | FLOAT | UV index |
| `comfort_index` | FLOAT | Engineered (0–100) |
| `severity_score` | FLOAT | Engineered (1–10) |

**`pipeline_runs`** — audit log

| Column | Description |
|--------|-------------|
| `run_id` | UUID (8-char hex) |
| `started_at` / `finished_at` | Run timestamps |
| `duration_sec` | Wall clock time |
| `rows_inserted` | Cities fetched |
| `status` | `success` / `failed` |
| `error_message` | Populated on failure |

---

## Insights from Live Data

**Phoenix dominates on heat** — consistently the hottest city in the dataset, often 15–20°F above the national average. UV index stays high even when cloud cover is moderate.

**Seattle is an outlier on comfort** — lower temperatures bring it toward the bottom of the comfort ranking, but minimal precipitation probability often offsets wind penalties.

**Miami scores high on severity despite low wind** — UV index combined with humidity pushes it to the top of the severity table even on calm days.

**The 7-day delta tells the real story** — raw temperature means little without context. The `delta_temp_7d` feature immediately shows whether a city is having an unusually hot or cool day versus its recent baseline.

---

## Skills Demonstrated

- **Data Engineering** — API ingestion pipeline, run-based append pattern, audit logging
- **Feature Engineering** — custom analytical metrics (comfort, severity, 7d delta)
- **SQL** — window functions (`ROW_NUMBER`, `PARTITION BY`), date arithmetic, CTEs
- **Python** — modular ETL (extract / transform / load), UUID run tracking
- **Automation** — GitHub Actions cron pipeline with secrets management
- **DevOps** — Docker containerization, HuggingFace Spaces deployment, DB sync via HF Dataset
- **Visualization** — Streamlit multi-section dashboard, Plotly geo map, line/bar/scatter charts

---

## Availability

| Layer | Detail |
|-------|--------|
| Hosting | HuggingFace Spaces (Docker SDK) |
| Uptime | 24/7 — HF Spaces does not sleep |
| Data freshness | Updated 2× daily via GitHub Actions |
| Database | DuckDB — downloaded from HF Dataset at startup |
| API cost | $0 — Open-Meteo is completely free |

---

*Data: Open-Meteo API · 10 US cities · Live, refreshed 2× daily · Built by Evgenii Matveev*
