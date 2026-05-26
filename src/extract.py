import httpx
import pandas as pd
from datetime import datetime, timezone

CITIES = {
    "New York":    {"lat": 40.7128,  "lon": -74.0060,  "tz": "America/New_York"},
    "Chicago":     {"lat": 41.8781,  "lon": -87.6298,  "tz": "America/Chicago"},
    "Los Angeles": {"lat": 34.0522,  "lon": -118.2437, "tz": "America/Los_Angeles"},
    "Houston":     {"lat": 29.7604,  "lon": -95.3698,  "tz": "America/Chicago"},
    "Phoenix":     {"lat": 33.4484,  "lon": -112.0740, "tz": "America/Phoenix"},
    "Miami":       {"lat": 25.7617,  "lon": -80.1918,  "tz": "America/New_York"},
    "Seattle":     {"lat": 47.6062,  "lon": -122.3321, "tz": "America/Los_Angeles"},
    "Denver":      {"lat": 39.7392,  "lon": -104.9903, "tz": "America/Denver"},
    "Boston":      {"lat": 42.3601,  "lon": -71.0589,  "tz": "America/New_York"},
    "Atlanta":     {"lat": 33.7490,  "lon": -84.3880,  "tz": "America/New_York"},
}

_BASE_URL = "https://api.open-meteo.com/v1/forecast"
_CURRENT_VARS = ",".join([
    "temperature_2m",
    "apparent_temperature",
    "precipitation",
    "precipitation_probability",
    "wind_speed_10m",
    "wind_gusts_10m",
    "relative_humidity_2m",
    "uv_index",
])


def _fetch_city(city: str, lat: float, lon: float, tz: str) -> dict:
    resp = httpx.get(
        _BASE_URL,
        params={"latitude": lat, "longitude": lon, "current": _CURRENT_VARS, "timezone": tz},
        timeout=15,
    )
    resp.raise_for_status()
    cur = resp.json()["current"]
    return {
        "city": city,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "temperature_c": cur["temperature_2m"],
        "feels_like_c": cur["apparent_temperature"],
        "precipitation_mm": cur["precipitation"],
        "precipitation_prob_pct": cur["precipitation_probability"],
        "wind_speed_kmh": cur["wind_speed_10m"],
        "wind_gusts_kmh": cur["wind_gusts_10m"],
        "humidity_pct": cur["relative_humidity_2m"],
        "uv_index": cur["uv_index"],
        "lat": lat,
        "lon": lon,
    }


def extract_all() -> pd.DataFrame:
    records = []
    for city, coords in CITIES.items():
        record = _fetch_city(city, coords["lat"], coords["lon"], coords["tz"])
        records.append(record)
        f = record['temperature_c'] * 9 / 5 + 32
        print(f"  + {city}: {f:.1f}°F ({record['temperature_c']}°C)")
    return pd.DataFrame(records)
