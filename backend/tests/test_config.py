import pytest
from pydantic import ValidationError

from app.config import District, Hazard, load_client


def test_kerala_has_14_districts():
    assert len(load_client("kerala").districts) == 14


def test_district_ids_are_unique():
    ids = [d.id for d in load_client("kerala").districts]
    assert len(ids) == len(set(ids))


def test_languages_include_malayalam_and_english():
    langs = load_client("kerala").languages
    assert "ml" in langs and "en" in langs


def test_out_of_kerala_coordinates_rejected():
    with pytest.raises(ValidationError):
        District(
            id="x", name="X", name_ml="x",
            lat=28.6, lon=77.2,  # Delhi
            primary_hazard=Hazard.river_flood,
        )


def test_unknown_client_raises():
    with pytest.raises(FileNotFoundError):
        load_client("atlantis")