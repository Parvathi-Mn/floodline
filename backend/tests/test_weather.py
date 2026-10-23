import httpx
import pytest

from app import weather
from app.weather import WeatherError, fetch_rainfall


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_sums_past_and_forecast(monkeypatch):
    data = {"daily": {"precipitation_sum": [10, 20, 30, 40, None]}}
    monkeypatch.setattr(weather.httpx, "get", lambda *a, **k: FakeResponse(data))
    rain = fetch_rainfall(9.5, 76.3)
    assert rain.past_72h_mm == 60
    assert rain.next_48h_mm == 40


def test_network_error_becomes_weather_error(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("no internet")
    monkeypatch.setattr(weather.httpx, "get", boom)
    with pytest.raises(WeatherError):
        fetch_rainfall(9.5, 76.3)


def test_wrong_number_of_days_raises(monkeypatch):
    data = {"daily": {"precipitation_sum": [1, 2, 3]}}
    monkeypatch.setattr(weather.httpx, "get", lambda *a, **k: FakeResponse(data))
    with pytest.raises(WeatherError):
        fetch_rainfall(9.5, 76.3)