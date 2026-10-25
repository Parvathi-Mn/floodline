from app.agent.loop import execute_tool
from app.agent.models import ToolCall
from app.agent.tools import build_tools
from app.config import load_client
from app.weather import Rainfall, WeatherError


def fake_weather(lat, lon):
    return Rainfall(past_5d_mm=100.0, peak_forecast_day_mm=130.0)


def tools_by_name(weather=fake_weather):
    return {t.name: t for t in build_tools(load_client("kerala"), weather)}


def test_risk_tool_uses_the_risk_engine():
    call = ToolCall("get_district_risk", {"district_id": "wayanad"})
    out = execute_tool(call, tools_by_name())
    assert out["result"]["level"] == "high"
    assert out["result"]["effective_rain_mm"] == 150.0
    assert out["result"]["primary_hazard"] == "landslide"


def test_district_id_is_case_insensitive():
    call = ToolCall("get_district_risk", {"district_id": "Wayanad"})
    out = execute_tool(call, tools_by_name())
    assert out["result"]["district_id"] == "wayanad"


def test_unknown_district_returns_valid_ids():
    call = ToolCall("get_district_risk", {"district_id": "atlantis"})
    out = execute_tool(call, tools_by_name())
    assert "error" in out["result"]
    assert "wayanad" in out["result"]["valid_ids"]


def test_weather_failure_becomes_tool_error():
    def broken(lat, lon):
        raise WeatherError("down")

    call = ToolCall("get_district_risk", {"district_id": "wayanad"})
    out = execute_tool(call, tools_by_name(broken))
    assert out == {"error": "tool failed: WeatherError"}


def test_district_enum_matches_config():
    tool = tools_by_name()["get_district_risk"]
    enum = tool.parameters["properties"]["district_id"]["enum"]
    assert len(enum) == 14


def test_list_districts_includes_malayalam_names():
    out = execute_tool(ToolCall("list_districts"), tools_by_name())
    assert len(out["result"]) == 14
    assert all(d["name_ml"] for d in out["result"])