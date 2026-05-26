from airflow.decorators import dag, task
from datetime import datetime, timedelta


@dag(
    dag_id="weather_pipeline",
    description="Fetch US weather from Open-Meteo and persist to DuckDB — 2x daily",
    schedule="0 13,1 * * *",  # ~8am ET + ~8pm ET (UTC)
    start_date=datetime(2026, 5, 26),
    catchup=False,
    default_args={
        "owner": "evgenii",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "email_on_failure": False,
    },
    tags=["weather", "open-meteo", "duckdb", "portfolio"],
)
def weather_pipeline():

    @task()
    def extract() -> list[dict]:
        from src.extract import extract_all
        return extract_all().to_dict(orient="records")

    @task()
    def transform(records: list[dict]) -> list[dict]:
        import pandas as pd
        from src.transform import transform as _transform
        return _transform(pd.DataFrame(records)).to_dict(orient="records")

    @task()
    def load(records: list[dict]) -> None:
        import time, uuid, pandas as pd
        from src.load import load as _load
        _load(pd.DataFrame(records), run_id=uuid.uuid4().hex[:8], start_time=time.time())

    load(transform(extract()))


weather_pipeline()
