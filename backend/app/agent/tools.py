"""Tools the agent may call. Facts come from here, never from the model's memory."""
from collections.abc import Callable

from app.agent.models import Tool
from app.config import Client
from app.risk import compute_risk
from app.weather import Rainfall, fetch_rainfall


def build_tools(
    client: Client,
    weather: Callable[[float, float], Rainfall] = fetch_rainfall,
) -> list[Tool]:
    """Build the tool list. `weather` can be swapped out in tests."""
    district_ids = [d.id for d in client.districts]

    def get_district_risk(district_id: str) -> dict:
        district = client.get_district(district_id)
        if district is None:
            return {
                "error": f"unknown district id: {district_id}",
                "valid_ids": district_ids,
            }
        result = compute_risk(district, weather(district.lat, district.lon))
        return {
            **result.model_dump(mode="json"),
            "district_name": district.name,
            "note": "Rainfall-based estimate only. 'low' does not mean safe.",
        }

    def list_districts() -> list[dict]:
        return [
            {"id": d.id, "name": d.name, "name_ml": d.name_ml}
            for d in client.districts
        ]

    return [
        Tool(
            name="get_district_risk",
            description=(
                "Get the current rainfall-based flood and landslide risk level "
                "for one Kerala district. Call this before telling the caller "
                "anything about risk."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "district_id": {
                        "type": "string",
                        "enum": district_ids,
                        "description": (
                            "The district the caller is in. Match the caller's "
                            "place name, in any language or spelling, to the "
                            "closest id. If unsure, ask the caller."
                        ),
                    }
                },
                "required": ["district_id"],
            },
            fn=get_district_risk,
        ),
        Tool(
            name="list_districts",
            description="List all 14 districts with English and Malayalam names.",
            parameters={"type": "object", "properties": {}},
            fn=list_districts,
        ),
    ]