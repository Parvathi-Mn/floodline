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


def fake_get(values):
    data = {"daily": {"precipitation_sum": values}}
    return lambda *a, **k: FakeResponse(data)


def test_sums_past_5_days_and_takes_peak_forecast_day(monkeypatch):
    monkeypatch.setattr(weather.httpx, "get", fake_get([10, 20, 30, 40, 50, 60, None]))
    rain = fetch_rainfall(9.5, 76.3)
    assert rain.past_5d_mm == 150
    assert rain.peak_forecast_day_mm == 60


def test_peak_can_be_tomorrow(monkeypatch):
    monkeypatch.setattr(weather.httpx, "get", fake_get([0, 0, 0, 0, 0, 5, 80]))
    assert fetch_rainfall(9.5, 76.3).peak_forecast_day_mm == 80


def test_network_error_becomes_weather_error(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("no internet")
    monkeypatch.setattr(weather.httpx, "get", boom)
    with pytest.raises(WeatherError):
        fetch_rainfall(9.5, 76.3)


def test_wrong_number_of_days_raises(monkeypatch):
    monkeypatch.setattr(weather.httpx, "get", fake_get([1, 2, 3, 4, 5]))
    with pytest.raises(WeatherError):
        fetch_rainfall(9.5, 76.3)