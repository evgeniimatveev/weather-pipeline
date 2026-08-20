import os
from pathlib import Path

from r2_client import get_r2_client

BUCKET = os.environ["R2_BUCKET"]
KEY = "weather-pipeline/weather.duckdb"
DB_PATH = Path("data/weather.duckdb")

if not DB_PATH.exists():
    raise FileNotFoundError(f"{DB_PATH} not found — pipeline likely failed")

get_r2_client().upload_file(str(DB_PATH), BUCKET, KEY)
print(f"DB uploaded to r2://{BUCKET}/{KEY}")
