"""Open-Meteo client (free, no API key). Returns rainfall totals in mm."""
from dataclasses import dataclass

import httpx

URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class Rainfall:
    past_72h_mm: float   # sum of the 3 days before today
    next_48h_mm: float   # today + tomorrow (forecast)


class WeatherError(Exception):
    pass


def fetch_rainfall(lat: float, lon: float, timeout: float = 10.0) -> Rainfall:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "past_days": 3,
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }
    try:
        r = httpx.get(URL, params=params, timeout=timeout)
        r.raise_for_status()
        days = [v or 0.0 for v in r.json()["daily"]["precipitation_sum"]]
    except (httpx.HTTPError, KeyError, ValueError) as e:
        raise WeatherError(str(e)) from e
    if len(days) != 5:
        raise WeatherError(f"expected 5 daily values, got {len(days)}")
    return Rainfall(past_72h_mm=sum(days[:3]), next_48h_mm=sum(days[3:]))