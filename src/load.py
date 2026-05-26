import duckdb
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
import time

DB_PATH = Path("data/weather.duckdb")


def _con(read_only: bool = False):
    DB_PATH.parent.mkdir(exist_ok=True)
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def init_schema():
    con = _con()
    con.execute("""
        CREATE TABLE IF NOT EXISTS weather_history (
            city                   VARCHAR,
            fetched_at             TIMESTAMPTZ,
            local_time             VARCHAR,
            timezone               VARCHAR,
            temperature_c          FLOAT,
            feels_like_c           FLOAT,
            precipitation_mm       FLOAT,
            precipitation_prob_pct FLOAT,
            wind_speed_kmh         FLOAT,
            wind_gusts_kmh         FLOAT,
            humidity_pct           FLOAT,
            uv_index               FLOAT,
            lat                    FLOAT,
            lon                    FLOAT,
            temperature_f          FLOAT,
            feels_like_f           FLOAT,
            comfort_index          FLOAT,
            severity_score         FLOAT,
            best_city_score        FLOAT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS forecast_history (
            city                VARCHAR,
            fetched_at          TIMESTAMPTZ,
            forecast_date       DATE,
            temp_max_c          FLOAT,
            temp_min_c          FLOAT,
            temp_max_f          FLOAT,
            temp_min_f          FLOAT,
            precip_prob_max     FLOAT,
            wind_speed_max_kmh  FLOAT,
            uv_index_max        FLOAT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS data_quality_log (
            run_id         VARCHAR,
            checked_at     TIMESTAMPTZ,
            total_rows     INTEGER,
            null_count     INTEGER,
            out_of_range   INTEGER,
            issues_count   INTEGER,
            status         VARCHAR,
            details        VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id         VARCHAR PRIMARY KEY,
            started_at     TIMESTAMPTZ,
            finished_at    TIMESTAMPTZ,
            duration_sec   FLOAT,
            cities_fetched INTEGER,
            rows_inserted  INTEGER,
            status         VARCHAR,
            error_message  VARCHAR
        )
    """)
    con.close()


def load(df: pd.DataFrame, run_id: str, start_time: float):
    init_schema()
    con = _con()
    status, error, rows = "success", None, 0
    try:
        con.execute("INSERT INTO weather_history SELECT * FROM df")
        rows = len(df)
    except Exception as exc:
        status, error = "failed", str(exc)
        raise
    finally:
        now     = datetime.now(timezone.utc)
        started = datetime.fromtimestamp(start_time, tz=timezone.utc)
        con.execute(
            "INSERT OR REPLACE INTO pipeline_runs VALUES (?,?,?,?,?,?,?,?)",
            [run_id, started, now, round(time.time() - start_time, 2),
             len(df), rows, status, error],
        )
        con.close()


def load_forecast(df: pd.DataFrame):
    con = _con()
    try:
        df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True)
        df["forecast_date"] = pd.to_datetime(df["forecast_date"]).dt.date
        con.execute("INSERT INTO forecast_history SELECT * FROM df")
    finally:
        con.close()


def log_quality(result: dict):
    con = _con()
    try:
        con.execute(
            "INSERT INTO data_quality_log VALUES (?,?,?,?,?,?,?,?)",
            [result["run_id"], result["checked_at"], result["total_rows"],
             result["null_count"], result["out_of_range"], result["issues_count"],
             result["status"], result["details"]],
        )
    finally:
        con.close()
