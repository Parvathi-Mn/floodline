from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

CLIENTS_DIR = Path(__file__).resolve().parents[2] / "clients"

# Rough bounding box of Kerala
KERALA_LAT = (8.0, 13.0)
KERALA_LON = (74.8, 77.5)


class Hazard(str, Enum):
    river_flood = "river_flood"
    urban_flood = "urban_flood"
    backwater_flood = "backwater_flood"
    landslide = "landslide"
    coastal = "coastal"


class District(BaseModel):
    id: str
    name: str
    name_ml: str
    lat: float
    lon: float
    primary_hazard: Hazard
    secondary_hazards: list[Hazard] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_inside_kerala(self):
        if not (KERALA_LAT[0] <= self.lat <= KERALA_LAT[1]
                and KERALA_LON[0] <= self.lon <= KERALA_LON[1]):
            raise ValueError(f"{self.name}: coordinates are outside Kerala")
        return self


class EmergencyNumber(BaseModel):
    name: str
    number: str
    verified: bool = False


class Client(BaseModel):
    id: str
    name: str
    languages: list[str]
    emergency_numbers: list[EmergencyNumber]
    districts: list[District]

    @model_validator(mode="after")
    def check_unique_district_ids(self):
        ids = [d.id for d in self.districts]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate district ids")
        return self


def load_client(client_id: str) -> Client:
    path = CLIENTS_DIR / f"{client_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Unknown client: {client_id}")
    with path.open(encoding="utf-8") as f:
        return Client(**yaml.safe_load(f))