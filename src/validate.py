import pandas as pd
from datetime import datetime, timezone


RULES = {
    "temperature_c":        (-60.0, 60.0),
    "feels_like_c":         (-70.0, 70.0),
    "humidity_pct":         (0.0,   100.0),
    "uv_index":             (0.0,   20.0),
    "wind_speed_kmh":       (0.0,   300.0),
    "precipitation_prob_pct": (0.0, 100.0),
}


def validate(df: pd.DataFrame, run_id: str) -> dict:
    issues = []

    # Null check
    nulls = df[list(RULES.keys())].isnull().sum()
    null_total = int(nulls.sum())
    if null_total:
        issues.append(f"Nulls: {nulls[nulls > 0].to_dict()}")

    # Range checks
    out_of_range = 0
    for col, (lo, hi) in RULES.items():
        if col not in df.columns:
            continue
        bad = df[(df[col] < lo) | (df[col] > hi)]
        if not bad.empty:
            out_of_range += len(bad)
            issues.append(f"{col} out of [{lo},{hi}]: {bad['city'].tolist()}")

    # Row count check
    if len(df) < 20:
        issues.append(f"Expected 20 rows, got {len(df)}")

    status = "pass" if not issues else ("warn" if out_of_range == 0 else "fail")

    if issues:
        print(f"  [WARN] Data quality [{status}]: {'; '.join(issues)}")
    else:
        print(f"  [OK] Data quality: all {len(df)} rows passed")

    return {
        "run_id":          run_id,
        "checked_at":      datetime.now(timezone.utc).isoformat(),
        "total_rows":      len(df),
        "null_count":      null_total,
        "out_of_range":    out_of_range,
        "issues_count":    len(issues),
        "status":          status,
        "details":         "; ".join(issues) if issues else None,
    }
