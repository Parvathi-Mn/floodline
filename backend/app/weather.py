"""Open-Meteo client (free, no API key). Returns rainfall figures in mm."""
from dataclasses import dataclass

import httpx

URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class Rainfall:
    past_5d_mm: float            # total rain over the 5 days before today
    peak_forecast_day_mm: float  # wettest of today and tomorrow (forecast)


class WeatherError(Exception):
    pass


def fetch_rainfall(lat: float, lon: float, timeout: float = 10.0) -> Rainfall:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "past_days": 5,
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }
    try:
        r = httpx.get(URL, params=params, timeout=timeout)
        r.raise_for_status()
        days = [v or 0.0 for v in r.json()["daily"]["precipitation_sum"]]
    except (httpx.HTTPError, KeyError, ValueError) as e:
        raise WeatherError(str(e)) from e
    if len(days) != 7:
        raise WeatherError(f"expected 7 daily values, got {len(days)}")
    return Rainfall(
        past_5d_mm=round(sum(days[:5]), 1),
        peak_forecast_day_mm=round(max(days[5:]), 1),
    )