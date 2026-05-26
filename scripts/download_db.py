from huggingface_hub import hf_hub_download
from pathlib import Path
import os

REPO_ID = os.environ["HF_DATASET_REPO"]
TOKEN = os.environ.get("HF_TOKEN")

Path("data").mkdir(exist_ok=True)

try:
    hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename="weather.duckdb",
        local_dir="data",
        token=TOKEN,
    )
    print(f"DB downloaded from {REPO_ID}")
except Exception as e:
    print(f"No existing DB found ({e}) — starting fresh")
