import os
import time
from pathlib import Path

from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

REPO_ID  = os.environ["HF_DATASET_REPO"]
TOKEN    = os.environ.get("HF_TOKEN")
DB_PATH  = Path("data/weather.duckdb")

if not DB_PATH.exists():
    raise FileNotFoundError(f"{DB_PATH} not found — pipeline likely failed")

api = HfApi()

RETRY_DELAYS = [30, 60, 120, 180]

for attempt, delay in enumerate(RETRY_DELAYS + [None], start=1):
    try:
        api.upload_file(
            path_or_fileobj=str(DB_PATH),
            path_in_repo="weather.duckdb",
            repo_id=REPO_ID,
            repo_type="dataset",
            token=TOKEN,
            commit_message="chore: update weather data",
        )
        print(f"DB uploaded to {REPO_ID}")
        break
    except HfHubHTTPError as e:
        if e.response.status_code == 429 and delay is not None:
            print(f"[429] Rate limited — waiting {delay}s before retry {attempt}/{len(RETRY_DELAYS)}...")
            time.sleep(delay)
        else:
            raise
