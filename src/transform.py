import pandas as pd


def _to_f(c: pd.Series) -> pd.Series:
    return (c * 9 / 5 + 32).round(1)


def _comfort_index(df: pd.DataFrame) -> pd.Series:
    temp_pen = (df["temperature_c"] - 22).abs() * 2.0
    hum_pen  = (df["humidity_pct"] - 50).clip(lower=0) * 0.3
    wind_pen = df["wind_speed_kmh"] * 0.4
    return (100 - temp_pen - hum_pen - wind_pen).clip(0, 100).round(1)


def _severity_score(df: pd.DataFrame) -> pd.Series:
    precip = (df["precipitation_prob_pct"] / 100) * 4
    wind   = (df["wind_gusts_kmh"] / 80).clip(0, 3)
    uv     = (df["uv_index"] / 11 * 3).clip(0, 3)
    return (1 + precip + wind + uv).clip(1, 10).round(1)


def _best_city_score(df: pd.DataFrame) -> pd.Series:
    # Higher = better place to be right now
    comfort  = df["comfort_index"] * 0.40
    safety   = (10 - df["severity_score"]) * 10 * 0.30
    no_rain  = (100 - df["precipitation_prob_pct"]) * 0.20
    uv_safe  = (100 - (df["uv_index"] / 11 * 100).clip(0, 100)) * 0.10
    return (comfort + safety + no_rain + uv_safe).clip(0, 100).round(1)


def _anomaly_flag(df: pd.DataFrame) -> pd.Series:
    delta = df.get("delta_temp_7d", pd.Series([None] * len(df)))
    return delta.apply(
        lambda d: "🔥 Hot Anomaly" if pd.notna(d) and d > 5
        else ("🧊 Cold Anomaly" if pd.notna(d) and d < -5 else "")
    )


def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["temperature_f"]  = _to_f(df["temperature_c"])
    df["feels_like_f"]   = _to_f(df["feels_like_c"])
    df["comfort_index"]  = _comfort_index(df)
    df["severity_score"] = _severity_score(df)
    df["best_city_score"] = _best_city_score(df)
    df["fetched_at"]     = pd.to_datetime(df["fetched_at"], utc=True)
    return df
