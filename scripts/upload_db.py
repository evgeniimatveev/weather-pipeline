from huggingface_hub import HfApi
from pathlib import Path
import os

REPO_ID = os.environ["HF_DATASET_REPO"]
TOKEN = os.environ.get("HF_TOKEN")
DB_PATH = Path("data/weather.duckdb")

if not DB_PATH.exists():
    raise FileNotFoundError(f"{DB_PATH} not found — pipeline likely failed")

api = HfApi()
api.upload_file(
    path_or_fileobj=str(DB_PATH),
    path_in_repo="weather.duckdb",
    repo_id=REPO_ID,
    repo_type="dataset",
    token=TOKEN,
    commit_message="chore: update weather data",
)
print(f"DB uploaded to {REPO_ID}")
