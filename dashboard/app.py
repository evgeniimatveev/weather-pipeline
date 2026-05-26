import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Global Weather Pipeline",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_PATH = Path("data/weather.duckdb")


def _ensure_db():
    if DB_PATH.exists():
        return
    repo  = os.environ.get("HF_DATASET_REPO")
    token = os.environ.get("HF_TOKEN")
    if not repo:
        st.error("Set HF_DATASET_REPO env variable to load data.")
        st.stop()
    from huggingface_hub import hf_hub_download
    DB_PATH.parent.mkdir(exist_ok=True)
    hf_hub_download(repo_id=repo, repo_type="dataset",
                    filename="weather.duckdb", local_dir="data", token=token)


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
def load_with_delta() -> pd.DataFrame:
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
            SELECT city, AVG(temperature_c) AS avg_temp_7d
            FROM weather_history
            WHERE fetched_at >= NOW() - INTERVAL 7 DAY
            GROUP BY city
        )
        SELECT l.*, ROUND(l.temperature_c - a.avg_temp_7d, 1) AS delta_temp_7d
        FROM latest l LEFT JOIN avg7 a USING (city)
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
def load_forecast() -> pd.DataFrame:
    _ensure_db()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("""
        SELECT * FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY city, forecast_date ORDER BY fetched_at DESC
            ) AS rn
            FROM forecast_history
        ) WHERE rn = 1
        ORDER BY city, forecast_date
    """).df()
    con.close()
    return df


@st.cache_data(ttl=3600)
def load_quality_log() -> pd.DataFrame:
    _ensure_db()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(
        "SELECT * FROM data_quality_log ORDER BY checked_at DESC LIMIT 10"
    ).df()
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


def severity_label(s):
    return "Low" if s < 3 else ("Moderate" if s < 6 else "High")

def comfort_label(s):
    return "Comfortable" if s >= 70 else ("Acceptable" if s >= 40 else "Harsh")

def anomaly_flag(d):
    if pd.isna(d): return ""
    return "🔥 Hot Anomaly" if d > 5 else ("🧊 Cold Anomaly" if d < -5 else "")


# ─── Header ──────────────────────────────────────────────────────────────────
st.title("🌍 Global Weather Pipeline")
st.caption("Live weather · 20 global cities · Open-Meteo API · Refreshed 2× daily · DuckDB + GitHub Actions")

try:
    df   = load_with_delta()
    hist = load_history()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

last_update = pd.to_datetime(df["fetched_at"]).max()
st.markdown(f"**Last pipeline run:** {last_update.strftime('%b %d, %Y %H:%M UTC')}  ·  **{len(df)} cities tracked**")

# ─── KPI row ─────────────────────────────────────────────────────────────────
st.divider()
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    hot = df.loc[df["temperature_f"].idxmax()]
    st.metric("Hottest City", f"{hot['temperature_f']:.0f}°F", hot["city"])
with c2:
    cool = df.loc[df["temperature_f"].idxmin()]
    st.metric("Coolest City", f"{cool['temperature_f']:.0f}°F", cool["city"])
with c3:
    best = df.loc[df["best_city_score"].idxmax()]
    st.metric("Best City Right Now", best["city"], f"Score {best['best_city_score']:.0f}")
with c4:
    harsh = df.loc[df["severity_score"].idxmax()]
    st.metric("Harshest Conditions", harsh["city"], f"Severity {harsh['severity_score']:.1f}")
with c5:
    st.metric("Avg Humidity", f"{df['humidity_pct'].mean():.0f}%",
              f"{len(df)} cities")

# ─── World Map ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("🗺️ World Temperature Map")
fig_map = px.scatter_geo(
    df, lat="lat", lon="lon",
    color="temperature_f", size="comfort_index",
    hover_name="city",
    hover_data={
        "temperature_f": ":.1f", "feels_like_f": ":.1f",
        "humidity_pct": ":.0f", "comfort_index": ":.1f",
        "severity_score": ":.1f", "local_time": True,
        "lat": False, "lon": False,
    },
    color_continuous_scale="RdYlBu_r",
    size_max=35, scope="world",
    labels={"temperature_f": "Temp (°F)", "comfort_index": "Comfort",
            "local_time": "Local Time"},
)
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                      coloraxis_colorbar={"title":"°F"}, height=460)
st.plotly_chart(fig_map, use_container_width=True)

# ─── Best City Ranking ───────────────────────────────────────────────────────
st.divider()
st.subheader("🏆 Best City to Be In Right Now")
st.caption("Composite score: Comfort Index (40%) + Low Severity (30%) + No Rain (20%) + UV Safety (10%)")

medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
top5   = df.nlargest(5, "best_city_score").reset_index(drop=True)
cols   = st.columns(5)
for i, (col, (_, row)) in enumerate(zip(cols, top5.iterrows())):
    with col:
        st.markdown(f"### {medals[i]} {row['city']}")
        st.metric("Score", f"{row['best_city_score']:.0f}",
                  f"{row['temperature_f']:.0f}°F · {row['local_time']} local")
        st.caption(f"Comfort {row['comfort_index']:.0f} · Severity {row['severity_score']:.1f} · "
                   f"Rain {row['precipitation_prob_pct']:.0f}%")

# ─── City Cards ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("🏙️ Current Conditions — All 20 Cities")

card_cols = st.columns(4)
for i, (_, row) in enumerate(df.sort_values("temperature_f", ascending=False).iterrows()):
    col = card_cols[i % 4]
    delta_str = (f"{row['delta_temp_7d']:+.1f}°C vs 7d avg"
                 if pd.notna(row.get("delta_temp_7d")) else "")
    flag = anomaly_flag(row.get("delta_temp_7d"))
    with col:
        header = f"**{row['city']}** {flag}"
        st.markdown(header)
        st.caption(f"🕐 {row['local_time']} local time")
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

# ─── Forecast Tab ────────────────────────────────────────────────────────────
st.divider()
st.subheader("📅 7-Day Forecast")

try:
    fc = load_forecast()
    if not fc.empty:
        fc["forecast_date"] = pd.to_datetime(fc["forecast_date"])
        all_cities = sorted(fc["city"].unique())
        selected = st.multiselect(
            "Select cities to compare:",
            options=all_cities,
            default=["New York", "London", "Tokyo", "Dubai", "Sydney"],
        )
        if selected:
            fc_sel = fc[fc["city"].isin(selected)]
            left, right = st.columns(2)
            with left:
                st.markdown("**Max Temperature (°F)**")
                fig_fc = px.line(
                    fc_sel, x="forecast_date", y="temp_max_f", color="city",
                    markers=True,
                    labels={"forecast_date": "Date", "temp_max_f": "Max Temp (°F)", "city": "City"},
                )
                fig_fc.update_layout(height=360, legend={"orientation":"h","y":-0.25})
                st.plotly_chart(fig_fc, use_container_width=True)
            with right:
                st.markdown("**Precipitation Probability (%)**")
                fig_rain = px.bar(
                    fc_sel, x="forecast_date", y="precip_prob_max",
                    color="city", barmode="group",
                    labels={"forecast_date": "Date", "precip_prob_max": "Rain %", "city": "City"},
                )
                fig_rain.update_layout(height=360, legend={"orientation":"h","y":-0.25})
                st.plotly_chart(fig_rain, use_container_width=True)
    else:
        st.info("Forecast data loads after the next pipeline run.")
except Exception:
    st.info("Forecast tab available after first full pipeline run.")

# ─── Trends + Comfort ────────────────────────────────────────────────────────
st.divider()
left, right = st.columns(2)

with left:
    st.subheader("📈 Temperature Trends (°F)")
    if not hist.empty:
        fig_trend = px.line(
            hist, x="fetched_at", y="temperature_f", color="city",
            markers=True,
            labels={"fetched_at": "Time", "temperature_f": "Temp (°F)", "city": "City"},
        )
        fig_trend.update_layout(height=380, legend={"orientation":"h","y":-0.3})
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("History grows with every pipeline run.")

with right:
    st.subheader("😊 Comfort Index by City")
    df_sorted = df.sort_values("comfort_index", ascending=True)
    fig_comfort = px.bar(
        df_sorted, x="comfort_index", y="city", orientation="h",
        color="comfort_index", color_continuous_scale="RdYlGn",
        range_color=[0, 100], text="comfort_index",
        labels={"comfort_index": "Comfort (0–100)", "city": ""},
    )
    fig_comfort.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig_comfort.update_layout(height=600, coloraxis_showscale=False)
    st.plotly_chart(fig_comfort, use_container_width=True)

# ─── Severity + Wind ─────────────────────────────────────────────────────────
st.divider()
left2, right2 = st.columns(2)

with left2:
    st.subheader("⚠️ Severity Score & Precipitation Risk")
    df_sev = df.sort_values("severity_score", ascending=False)[
        ["city", "severity_score", "precipitation_prob_pct", "wind_gusts_kmh", "uv_index"]
    ].rename(columns={
        "severity_score": "Severity (1–10)",
        "precipitation_prob_pct": "Precip % Risk",
        "wind_gusts_kmh": "Wind Gusts km/h",
        "uv_index": "UV Index",
    })
    st.dataframe(
        df_sev.style.background_gradient(subset=["Severity (1–10)"], cmap="YlOrRd"),
        use_container_width=True, hide_index=True,
    )

with right2:
    st.subheader("🌬️ Wind Speed vs Gusts")
    fig_wind = px.scatter(
        df, x="wind_speed_kmh", y="wind_gusts_kmh", text="city",
        color="severity_score", color_continuous_scale="Reds",
        labels={"wind_speed_kmh": "Wind Speed (km/h)",
                "wind_gusts_kmh": "Wind Gusts (km/h)",
                "severity_score": "Severity"},
    )
    fig_wind.update_traces(textposition="top center")
    fig_wind.update_layout(height=500)
    st.plotly_chart(fig_wind, use_container_width=True)

# ─── Data Quality Log ────────────────────────────────────────────────────────
st.divider()
st.subheader("✅ Data Quality Log")
st.caption("Schema validation · null checks · range checks — logged on every pipeline run.")
try:
    dq = load_quality_log()
    if not dq.empty:
        dq["checked_at"] = pd.to_datetime(dq["checked_at"]).dt.strftime("%b %d %H:%M UTC")
        dq["status"] = dq["status"].apply(
            lambda s: "✅ pass" if s == "pass" else ("⚠️ warn" if s == "warn" else "❌ fail")
        )
        st.dataframe(dq[["run_id","checked_at","total_rows","null_count",
                          "out_of_range","issues_count","status","details"]],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No quality logs yet.")
except Exception:
    st.info("Quality log available after first pipeline run.")

# ─── Pipeline Runs Log ───────────────────────────────────────────────────────
st.divider()
st.subheader("🔁 Pipeline Runs Log")
st.caption("Every run tracked: run ID, duration, rows inserted, status — production DE mindset.")
try:
    runs = load_pipeline_runs()
    if not runs.empty:
        runs["started_at"] = pd.to_datetime(runs["started_at"]).dt.strftime("%b %d %H:%M UTC")
        runs["status"] = runs["status"].apply(
            lambda s: "✅ success" if s == "success" else "❌ failed"
        )
        st.dataframe(
            runs[["run_id","started_at","duration_sec","cities_fetched",
                  "rows_inserted","status","error_message"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No runs logged yet.")
except Exception:
    st.info("Pipeline runs table not available yet.")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Stack: Open-Meteo API → GitHub Actions (2×/day) → DuckDB → Streamlit · "
    "Features: Comfort Index · Severity Score · Best City Score · 7-day Delta · Anomaly Detection · Data Quality · 7-day Forecast · "
    "Built by Evgenii Matveev"
)
