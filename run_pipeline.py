import sys
import time
import uuid

from src.extract import extract_all, extract_forecast
from src.transform import transform
from src.validate import validate
from src.load import init_schema, load, load_forecast, log_quality


def main():
    run_id = uuid.uuid4().hex[:8]
    start  = time.time()
    print(f"[{run_id}] Pipeline starting — 20 global cities...")

    init_schema()

    # Extract
    df_raw = extract_all()
    if df_raw.empty:
        print(f"[{run_id}] FATAL: 0 cities extracted — API unavailable")
        sys.exit(1)

    # Transform
    df = transform(df_raw)

    # Validate
    print(f"[{run_id}] Validating data quality...")
    quality = validate(df, run_id)
    log_quality(quality)

    # Load current weather
    load(df, run_id, start)

    # Forecast
    print(f"[{run_id}] Fetching 7-day forecasts...")
    df_forecast = extract_forecast()
    load_forecast(df_forecast)

    elapsed = time.time() - start
    print(f"[{run_id}] Done — {len(df)} cities · {len(df_forecast)} forecast rows · {elapsed:.1f}s")


if __name__ == "__main__":
    main()
