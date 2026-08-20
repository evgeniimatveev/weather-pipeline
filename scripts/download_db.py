import os
from pathlib import Path

from botocore.exceptions import ClientError

from r2_client import get_r2_client

BUCKET = os.environ["R2_BUCKET"]
KEY = "weather-pipeline/weather.duckdb"

Path("data").mkdir(exist_ok=True)

try:
    get_r2_client().download_file(BUCKET, KEY, "data/weather.duckdb")
    print(f"DB downloaded from r2://{BUCKET}/{KEY}")
except ClientError as e:
    print(f"No existing DB found ({e}) — starting fresh")
