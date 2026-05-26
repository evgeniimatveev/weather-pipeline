import httpx
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

CITIES = {
    # US
    "New York":     {"lat": 40.7128,  "lon": -74.0060,   "tz": "America/New_York"},
    "Chicago":      {"lat": 41.8781,  "lon": -87.6298,   "tz": "America/Chicago"},
    "Los Angeles":  {"lat": 34.0522,  "lon": -118.2437,  "tz": "America/Los_Angeles"},
    "Houston":      {"lat": 29.7604,  "lon": -95.3698,   "tz": "America/Chicago"},
    "Phoenix":      {"lat": 33.4484,  "lon": -112.0740,  "tz": "America/Phoenix"},
    "Miami":        {"lat": 25.7617,  "lon": -80.1918,   "tz": "America/New_York"},
    "Seattle":      {"lat": 47.6062,  "lon": -122.3321,  "tz": "America/Los_Angeles"},
    "Denver":       {"lat": 39.7392,  "lon": -104.9903,  "tz": "America/Denver"},
    "Boston":       {"lat": 42.3601,  "lon": -71.0589,   "tz": "America/New_York"},
    "Atlanta":      {"lat": 33.7490,  "lon": -84.3880,   "tz": "America/New_York"},
    # International
    "London":       {"lat": 51.5074,  "lon": -0.1278,    "tz": "Europe/London"},
    "Paris":        {"lat": 48.8566,  "lon": 2.3522,     "tz": "Europe/Paris"},
    "Berlin":       {"lat": 52.5200,  "lon": 13.4050,    "tz": "Europe/Berlin"},
    "Tokyo":        {"lat": 35.6762,  "lon": 139.6503,   "tz": "Asia/Tokyo"},
    "Singapore":    {"lat": 1.3521,   "lon": 103.8198,   "tz": "Asia/Singapore"},
    "Dubai":        {"lat": 25.2048,  "lon": 55.2708,    "tz": "Asia/Dubai"},
    "Sydney":       {"lat": -33.8688, "lon": 151.2093,   "tz": "Australia/Sydney"},
    "Toronto":      {"lat": 43.6532,  "lon": -79.3832,   "tz": "America/Toronto"},
    "Sao Paulo":    {"lat": -23.5505, "lon": -46.6333,   "tz": "America/Sao_Paulo"},
    "Mexico City":  {"lat": 19.4326,  "lon": -99.1332,   "tz": "America/Mexico_City"},
}

_BASE_URL = "https://api.open-meteo.com/v1/forecast"

_CURRENT_VARS = ",".join([
    "temperature_2m", "apparent_temperature", "precipitation",
    "precipitation_probability", "wind_speed_10m", "wind_gusts_10m",
    "relative_humidity_2m", "uv_index",
])

_DAILY_VARS = ",".join([
    "temperature_2m_max", "temperature_2m_min",
    "precipitation_probability_max", "wind_speed_10m_max", "uv_index_max",
])


def _local_time(tz: str) -> str:
    return datetime.now(ZoneInfo(tz)).strftime("%H:%M")


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
        "local_time": _local_time(tz),
        "timezone": tz,
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


def _fetch_forecast(city: str, lat: float, lon: float, tz: str) -> list[dict]:
    resp = httpx.get(
        _BASE_URL,
        params={
            "latitude": lat, "longitude": lon,
            "daily": _DAILY_VARS, "timezone": tz, "forecast_days": 7,
        },
        timeout=15,
    )
    resp.raise_for_status()
    daily = resp.json()["daily"]
    fetched_at = datetime.now(timezone.utc).isoformat()
    return [
        {
            "city": city,
            "fetched_at": fetched_at,
            "forecast_date": daily["time"][i],
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "temp_max_f": round(daily["temperature_2m_max"][i] * 9 / 5 + 32, 1),
            "temp_min_f": round(daily["temperature_2m_min"][i] * 9 / 5 + 32, 1),
            "precip_prob_max": daily["precipitation_probability_max"][i],
            "wind_speed_max_kmh": daily["wind_speed_10m_max"][i],
            "uv_index_max": daily["uv_index_max"][i],
        }
        for i in range(7)
    ]


def extract_all() -> pd.DataFrame:
    records = []
    for city, coords in CITIES.items():
        record = _fetch_city(city, coords["lat"], coords["lon"], coords["tz"])
        records.append(record)
        f = record["temperature_c"] * 9 / 5 + 32
        print(f"  + {city}: {f:.1f}°F ({record['temperature_c']}°C)  [{record['local_time']} local]")
    return pd.DataFrame(records)


def extract_forecast() -> pd.DataFrame:
    rows = []
    for city, coords in CITIES.items():
        rows.extend(_fetch_forecast(city, coords["lat"], coords["lon"], coords["tz"]))
    return pd.DataFrame(rows)
