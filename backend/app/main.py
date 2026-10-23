from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from .config import Client, load_client
from .risk import RiskResult, compute_risk
from .weather import WeatherError, fetch_rainfall

app = FastAPI(title="Floodline API", version="0.2.0")


@lru_cache
def get_client() -> Client:
    return load_client("kerala")


def get_weather():
    return fetch_rainfall


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/districts")
def districts(client: Client = Depends(get_client)):
    return client.districts


@app.get("/api/risk/{district_id}", response_model=RiskResult)
def risk(
    district_id: str,
    client: Client = Depends(get_client),
    weather=Depends(get_weather),
):
    district = client.get_district(district_id)
    if district is None:
        raise HTTPException(404, f"Unknown district: {district_id}")
    try:
        rain = weather(district.lat, district.lon)
    except WeatherError as e:
        raise HTTPException(503, "Weather data unavailable; refer caller to 1077") from e
    return compute_risk(district, rain)