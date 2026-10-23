import pytest

from app.config import load_client
from app.risk import compute_risk, level_for
from app.weather import Rainfall

WAYANAD = load_client("kerala").get_district("wayanad")


@pytest.mark.parametrize("mm, expected", [
    (0, "low"),
    (64.4, "low"),
    (64.5, "moderate"),
    (115.5, "moderate"),
    (115.6, "high"),
    (204.4, "high"),
    (204.5, "severe"),
])
def test_level_boundaries_follow_imd_categories(mm, expected):
    assert level_for(mm) == expected


def test_past_rain_counts_at_20_percent():
    r = compute_risk(WAYANAD, Rainfall(past_5d_mm=100, peak_forecast_day_mm=50))
    assert r.effective_rain_mm == 70.0
    assert r.level == "moderate"


def test_wet_ground_can_raise_the_level():
    dry = compute_risk(WAYANAD, Rainfall(past_5d_mm=0, peak_forecast_day_mm=60))
    wet = compute_risk(WAYANAD, Rainfall(past_5d_mm=100, peak_forecast_day_mm=60))
    assert dry.level == "low" and wet.level == "moderate"


def test_wayanad_july_2024_day_is_severe():
    assert compute_risk(WAYANAD, Rainfall(0, 372)).level == "severe"


def test_puthumala_2019_day_is_severe():
    assert compute_risk(WAYANAD, Rainfall(0, 244)).level == "severe"


def test_quiet_spell_is_low():
    assert compute_risk(WAYANAD, Rainfall(5, 10)).level == "low"


def test_result_keeps_hazard_type_for_the_agent():
    assert compute_risk(WAYANAD, Rainfall(0, 0)).primary_hazard.value == "landslide"