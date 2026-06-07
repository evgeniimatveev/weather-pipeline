import os
import time
from pathlib import Path

from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

REPO_ID = os.environ["HF_DATASET_REPO"]
TOKEN   = os.environ.get("HF_TOKEN")

Path("data").mkdir(exist_ok=True)

RETRY_DELAYS = [15, 30, 60, 120]

for attempt, delay in enumerate(RETRY_DELAYS + [None], start=1):
    try:
        hf_hub_download(
            repo_id=REPO_ID,
            repo_type="dataset",
            filename="weather.duckdb",
            local_dir="data",
            token=TOKEN,
            force_download=True,
        )
        print(f"DB downloaded from {REPO_ID}")
        break
    except HfHubHTTPError as e:
        if e.response.status_code == 429 and delay is not None:
            print(f"[429] Rate limited — waiting {delay}s before retry {attempt}/{len(RETRY_DELAYS)}...")
            time.sleep(delay)
        else:
            print(f"No existing DB found ({e}) — starting fresh")
            break
    except Exception as e:
        print(f"No existing DB found ({e}) — starting fresh")
        break
