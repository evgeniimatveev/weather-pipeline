"""
Post-pipeline data quality gate.
Reads weather.duckdb, validates results, writes GitHub Actions Job Summary.
"""
import os
import sys
from pathlib import Path

import duckdb

DB_PATH = Path("data/weather.duckdb")
EXPECTED_CITIES = 20
MIN_CITIES_WARN  = 17
MIN_CITIES_FAIL  = 15


def write_summary(md: str) -> None:
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(md + "\n")
    print(md)


def main() -> None:
    if not DB_PATH.exists():
        write_summary("## ❌ DB not found — pipeline may have failed")
        sys.exit(1)

    con = duckdb.connect(str(DB_PATH), read_only=True)

    # Latest pipeline run metadata
    run = con.execute("""
        SELECT run_id, started_at, duration_sec, cities_fetched, status
        FROM pipeline_runs
        ORDER BY started_at DESC
        LIMIT 1
    """).fetchone()

    if not run:
        write_summary("## ❌ No pipeline run found in DB")
        con.close()
        sys.exit(1)

    run_id, started_at, duration_sec, cities_fetched, run_status = run

    # Latest quality log for this run
    quality = con.execute("""
        SELECT total_rows, null_count, out_of_range, issues_count, status, details
        FROM data_quality_log
        WHERE run_id = ?
        LIMIT 1
    """, [run_id]).fetchone()

    # Cities in the latest run — join on run window instead of exact timestamp
    cities = con.execute("""
        SELECT city, temperature_c, temperature_f, comfort_index, best_city_score
        FROM weather_history
        WHERE fetched_at >= (SELECT started_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 1)
        ORDER BY best_city_score DESC NULLS LAST
    """).fetchall()

    city_count = len(cities)

    # Forecast rows for latest run
    forecast_rows = con.execute("""
        SELECT COUNT(*) FROM forecast_history
        WHERE fetched_at >= (SELECT started_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 1)
    """).fetchone()[0]

    # DB stats
    db_size_mb  = DB_PATH.stat().st_size / (1024 * 1024)
    total_rows  = con.execute("SELECT COUNT(*) FROM weather_history").fetchone()[0]

    con.close()

    # ── Status icons ──────────────────────────────────────────────
    city_icon   = "✅" if city_count >= MIN_CITIES_WARN else ("⚠️" if city_count >= MIN_CITIES_FAIL else "❌")
    null_val    = quality[1] if quality else "N/A"
    range_val   = quality[2] if quality else "N/A"
    qa_label    = quality[4] if quality else "unknown"
    qa_icon     = "✅" if qa_label == "pass" else ("⚠️" if qa_label == "warn" else "❌")
    duration_m  = f"{duration_sec / 60:.1f} min" if duration_sec else "N/A"
    started_str = str(started_at)[:16] if started_at else "N/A"

    # ── Build markdown ────────────────────────────────────────────
    md = f"""## 🌍 Weather Pipeline — Data Quality Summary

| Metric | Value |
|--------|-------|
| Run ID | `{run_id}` |
| Started | `{started_str}` UTC |
| Duration | `{duration_m}` |
| Cities loaded | {city_icon} **{city_count} / {EXPECTED_CITIES}** |
| Null values | **{null_val}** |
| Out-of-range | **{range_val}** |
| QA status | {qa_icon} **{qa_label}** |
| Forecast rows | **{forecast_rows}** |
| Total rows (all time) | **{total_rows}** |
| DB size | **{db_size_mb:.2f} MB** |
"""

    # Issues detail block
    if quality and quality[5]:
        md += f"\n### ⚠️ Issues\n```\n{quality[5]}\n```\n"

    # Top 5 cities by comfort score
    if cities:
        md += "\n### 🏆 Top 5 — Comfort Score\n\n"
        md += "| City | Temp °C | Temp °F | Comfort |\n"
        md += "|------|---------|---------|--------|\n"
        for city, tc, tf, comfort, _ in cities[:5]:
            md += f"| {city} | {tc:.1f} | {tf:.1f} | {comfort:.1f} |\n"

    write_summary(md)

    # ── Exit code (quality gate) ──────────────────────────────────
    if city_count < MIN_CITIES_FAIL:
        print(f"[FAIL] Only {city_count}/{EXPECTED_CITIES} cities — below threshold")
        sys.exit(1)
    elif city_count < MIN_CITIES_WARN:
        print(f"[WARN] {city_count}/{EXPECTED_CITIES} cities — degraded but acceptable")
    else:
        print(f"[OK] {city_count}/{EXPECTED_CITIES} cities — QA: {qa_label}")


if __name__ == "__main__":
    main()
