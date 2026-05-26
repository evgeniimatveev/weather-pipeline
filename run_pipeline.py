import time
import uuid

from src.extract import extract_all
from src.transform import transform
from src.load import load


def main():
    run_id = uuid.uuid4().hex[:8]
    start = time.time()
    print(f"[{run_id}] Pipeline starting...")

    df_raw = extract_all()
    df = transform(df_raw)
    load(df, run_id, start)

    print(f"[{run_id}] Done — {len(df)} rows in {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
