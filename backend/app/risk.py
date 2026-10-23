"""Rainfall-index risk levels, anchored to published numbers.

effective_rain = peak forecast day (mm) + 0.2 * rain over past 5 days (mm)

Levels use IMD's official 24h rainfall categories (64.5 / 115.6 / 204.5 mm).
The 0.2 factor is from Naidu et al. 2017 (Amboori, Kerala landslide threshold).
"low" does NOT mean safe.
"""
from pydantic import BaseModel

from .config import District, Hazard
from .weather import Rainfall

ANTECEDENT_FACTOR = 0.2
BANDS = [(204.5, "severe"), (115.6, "high"), (64.5, "moderate")]


class RiskResult(BaseModel):
    district_id: str
    level: str
    effective_rain_mm: float
    peak_forecast_day_mm: float
    past_5d_mm: float
    primary_hazard: Hazard


def level_for(effective_rain_mm: float) -> str:
    for lower_bound, level in BANDS:
        if effective_rain_mm >= lower_bound:
            return level
    return "low"


def compute_risk(district: District, rain: Rainfall) -> RiskResult:
    effective = rain.peak_forecast_day_mm + ANTECEDENT_FACTOR * rain.past_5d_mm
    return RiskResult(
        district_id=district.id,
        level=level_for(effective),
        effective_rain_mm=round(effective, 1),
        peak_forecast_day_mm=rain.peak_forecast_day_mm,
        past_5d_mm=rain.past_5d_mm,
        primary_hazard=district.primary_hazard,
    )