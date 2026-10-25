import pytest
from fastapi.testclient import TestClient

from app.main import app, get_weather
from app.weather import Rainfall, WeatherError

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def fake_weather(rain=None, error=None):
    def fetch(lat, lon):
        if error:
            raise error
        return rain
    app.dependency_overrides[get_weather] = lambda: fetch


def test_districts_lists_all_14():
    res = client.get("/api/districts")
    assert res.status_code == 200 and len(res.json()) == 14


def test_risk_returns_level_and_inputs():
    fake_weather(Rainfall(past_5d_mm=100, peak_forecast_day_mm=60))
    res = client.get("/api/risk/wayanad")
    body = res.json()
    assert res.status_code == 200
    assert body["level"] == "moderate"        # 60 + 0.2*100 = 80
    assert body["effective_rain_mm"] == 80.0
    assert body["primary_hazard"] == "landslide"


def test_district_lookup_ignores_case():
    fake_weather(Rainfall(0, 0))
    assert client.get("/api/risk/Wayanad").status_code == 200


def test_unknown_district_returns_404():
    assert client.get("/api/risk/narnia").status_code == 404


def test_weather_failure_returns_503():
    fake_weather(error=WeatherError("down"))
    assert client.get("/api/risk/kollam").status_code == 503