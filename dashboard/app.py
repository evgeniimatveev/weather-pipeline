import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="US Weather Pipeline",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── DB helpers ──────────────────────────────────────────────────────────────

DB_PATH = Path("data/weather.duckdb")


def _ensure_db():
    if DB_PATH.exists():
        return
    repo = os.environ.get("HF_DATASET_REPO")
    token = os.environ.get("HF_TOKEN")
    if not repo:
        st.error("Set HF_DATASET_REPO env variable to load data.")
        st.stop()
    from huggingface_hub import hf_hub_download
    DB_PATH.parent.mkdir(exist_ok=True)
    hf_hub_download(
        repo_id=repo, repo_type="dataset",
        filename="weather.duckdb", local_dir="data", token=token,
    )


@st.cache_data(ttl=3600)
def load_latest() -> pd.DataFrame:
    _ensure_db()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("""
        SELECT * FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY city ORDER BY fetched_at DESC) AS rn
            FROM weather_history
        ) WHERE rn = 1
    """).df()
    con.close()
    return df


@st.cache_data(ttl=3600)
def load_history() -> pd.DataFrame:
    _ensure_db()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM weather_history ORDER BY fetched_at").df()
    con.close()
    return df


@st.cache_data(ttl=3600)
def load_with_delta() -> pd.DataFrame:
    """Latest snapshot enriched with 7-day average delta per city."""
    _ensure_db()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("""
        WITH latest AS (
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY city ORDER BY fetched_at DESC) AS rn
                FROM weather_history
            ) WHERE rn = 1
        ),
        avg7 AS (
            SELECT city,
                   AVG(temperature_c) AS avg_temp_7d
            FROM weather_history
            WHERE fetched_at >= NOW() - INTERVAL 7 DAY
            GROUP BY city
        )
        SELECT l.*, ROUND(l.temperature_c - a.avg_temp_7d, 1) AS delta_temp_7d
        FROM latest l
        LEFT JOIN avg7 a USING (city)
    """).df()
    con.close()
    return df


@st.cache_data(ttl=3600)
def load_pipeline_runs() -> pd.DataFrame:
    _ensure_db()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(
        "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 10"
    ).df()
    con.close()
    return df


# ─── Helpers ─────────────────────────────────────────────────────────────────

SEVERITY_COLOR = {
    (1, 3): "#4CAF50",   # green
    (3, 6): "#FF9800",   # orange
    (6, 10): "#F44336",  # red
}


def severity_label(score: float) -> str:
    if score < 3:
        return "Low"
    if score < 6:
        return "Moderate"
    return "High"


def comfort_label(score: float) -> str:
    if score >= 70:
        return "Comfortable"
    if score >= 40:
        return "Acceptable"
    return "Harsh"


# ─── UI ──────────────────────────────────────────────────────────────────────

st.title("🌤️ US Weather Pipeline")
st.caption("Live weather data · Open-Meteo API · Refreshed 2× daily via GitHub Actions + DuckDB")

try:
    df = load_with_delta()
    history = load_history()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

last_update = pd.to_datetime(df["fetched_at"]).max()
st.markdown(f"**Last pipeline run:** {last_update.strftime('%b %d, %Y %H:%M UTC')}")

# ─── KPI row ─────────────────────────────────────────────────────────────────

st.divider()
cols = st.columns(5)
kpis = [
    ("Hottest City", df.loc[df["temperature_f"].idxmax(), "city"],
     f"{df['temperature_f'].max():.0f}°F"),
    ("Coolest City", df.loc[df["temperature_f"].idxmin(), "city"],
     f"{df['temperature_f'].min():.0f}°F"),
    ("Most Comfortable", df.loc[df["comfort_index"].idxmax(), "city"],
     f"Score {df['comfort_index'].max():.0f}"),
    ("Harshest Conditions", df.loc[df["severity_score"].idxmax(), "city"],
     f"Severity {df['severity_score'].max():.1f}"),
    ("Avg Humidity", "", f"{df['humidity_pct'].mean():.0f}%"),
]
for col, (label, city, value) in zip(cols, kpis):
    with col:
        st.metric(label=label, value=value, delta=city if city else None)

# ─── US Map ──────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Temperature Map")

fig_map = px.scatter_geo(
    df,
    lat="lat",
    lon="lon",
    color="temperature_f",
    size="comfort_index",
    hover_name="city",
    hover_data={
        "temperature_f": ":.1f",
        "feels_like_f": ":.1f",
        "humidity_pct": ":.0f",
        "comfort_index": ":.1f",
        "severity_score": ":.1f",
        "lat": False,
        "lon": False,
    },
    color_continuous_scale="RdYlBu_r",
    size_max=30,
    scope="usa",
    labels={
        "temperature_f": "Temp (°F)",
        "feels_like_f": "Feels Like (°F)",
        "humidity_pct": "Humidity %",
        "comfort_index": "Comfort Index",
        "severity_score": "Severity Score",
    },
)
fig_map.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    coloraxis_colorbar={"title": "°F"},
    height=420,
)
st.plotly_chart(fig_map, use_container_width=True)

# ─── City cards ──────────────────────────────────────────────────────────────

st.divider()
st.subheader("Current Conditions")

card_cols = st.columns(5)
for i, row in df.sort_values("temperature_f", ascending=False).iterrows():
    col = card_cols[list(df.index).index(i) % 5]
    delta_str = (
        f"{row['delta_temp_7d']:+.1f}°C vs 7d avg"
        if pd.notna(row.get("delta_temp_7d")) else ""
    )
    with col:
        st.markdown(f"**{row['city']}**")
        st.metric(
            label=f"{row['temperature_f']:.0f}°F / {row['temperature_c']:.1f}°C",
            value=f"Feels {row['feels_like_f']:.0f}°F",
            delta=delta_str,
        )
        st.caption(
            f"💧 {row['humidity_pct']:.0f}%  "
            f"🌬️ {row['wind_speed_kmh']:.0f} km/h  "
            f"☔ {row['precipitation_prob_pct']:.0f}%  "
            f"☀️ UV {row['uv_index']:.1f}"
        )
        st.caption(
            f"Comfort: **{row['comfort_index']:.0f}** ({comfort_label(row['comfort_index'])})  |  "
            f"Severity: **{row['severity_score']:.1f}** ({severity_label(row['severity_score'])})"
        )

# ─── Trend charts ────────────────────────────────────────────────────────────

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Temperature Trends (°F)")
    if not history.empty:
        fig_trend = px.line(
            history,
            x="fetched_at",
            y="temperature_f",
            color="city",
            markers=True,
            labels={"fetched_at": "Time", "temperature_f": "Temp (°F)", "city": "City"},
        )
        fig_trend.update_layout(height=380, legend={"orientation": "h", "y": -0.2})
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Not enough history yet — run the pipeline a few times.")

with right:
    st.subheader("Comfort Index by City")
    df_sorted = df.sort_values("comfort_index", ascending=True)
    fig_comfort = px.bar(
        df_sorted,
        x="comfort_index",
        y="city",
        orientation="h",
        color="comfort_index",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        labels={"comfort_index": "Comfort Index (0–100)", "city": ""},
        text="comfort_index",
    )
    fig_comfort.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig_comfort.update_layout(height=380, coloraxis_showscale=False)
    st.plotly_chart(fig_comfort, use_container_width=True)

# ─── Severity + Wind ─────────────────────────────────────────────────────────

st.divider()
left2, right2 = st.columns(2)

with left2:
    st.subheader("Severity Score & Precipitation Risk")
    df_sev = df.sort_values("severity_score", ascending=False)[
        ["city", "severity_score", "precipitation_prob_pct", "wind_gusts_kmh", "uv_index"]
    ].rename(columns={
        "severity_score": "Severity (1–10)",
        "precipitation_prob_pct": "Precip % Risk",
        "wind_gusts_kmh": "Wind Gusts km/h",
        "uv_index": "UV Index",
    })

    def color_severity(val):
        if isinstance(val, float) and "Severity" in str(df_sev.columns):
            pass
        return ""

    st.dataframe(
        df_sev.style.background_gradient(subset=["Severity (1–10)"], cmap="YlOrRd"),
        use_container_width=True,
        hide_index=True,
    )

with right2:
    st.subheader("Wind Speed vs Gusts")
    fig_wind = px.scatter(
        df,
        x="wind_speed_kmh",
        y="wind_gusts_kmh",
        text="city",
        color="severity_score",
        color_continuous_scale="Reds",
        labels={
            "wind_speed_kmh": "Wind Speed (km/h)",
            "wind_gusts_kmh": "Wind Gusts (km/h)",
            "severity_score": "Severity",
        },
        size_max=20,
    )
    fig_wind.update_traces(textposition="top center")
    fig_wind.update_layout(height=380)
    st.plotly_chart(fig_wind, use_container_width=True)

# ─── Pipeline runs ───────────────────────────────────────────────────────────

st.divider()
st.subheader("Pipeline Runs Log")
st.caption("Every run is tracked: run ID, duration, rows inserted, status — production DE mindset.")

try:
    runs = load_pipeline_runs()
    if not runs.empty:
        runs["started_at"] = pd.to_datetime(runs["started_at"]).dt.strftime("%b %d %H:%M UTC")
        runs["status"] = runs["status"].apply(
            lambda s: "✅ success" if s == "success" else "❌ failed"
        )
        st.dataframe(
            runs[["run_id", "started_at", "duration_sec", "cities_fetched", "rows_inserted", "status", "error_message"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No runs logged yet.")
except Exception:
    st.info("Pipeline runs table not available yet.")

# ─── Footer ──────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "Stack: Open-Meteo API → GitHub Actions (2×/day) → DuckDB → Streamlit · "
    "Engineered features: Comfort Index, Severity Score, 7-day delta · "
    "Built by Evgenii Matveev"
)
