import pytest

from app.settings import SettingsError, load_settings

GOOD = {"LLM_API_KEY": "secret123", "LLM_MODEL": "some-model"}


def test_loads_required_values():
    s = load_settings(GOOD)
    assert s.llm_api_key.get_secret_value() == "secret123"
    assert s.llm_model == "some-model"


def test_secret_is_hidden_when_printed():
    s = load_settings(GOOD)
    assert "secret123" not in repr(s)
    assert "secret123" not in str(s)


def test_missing_key_raises_and_names_it():
    with pytest.raises(SettingsError) as err:
        load_settings({"LLM_MODEL": "some-model"})
    assert "LLM_API_KEY" in str(err.value)


def test_missing_model_raises_without_leaking_the_key():
    with pytest.raises(SettingsError) as err:
        load_settings({"LLM_API_KEY": "secret123"})
    assert "LLM_MODEL" in str(err.value)
    assert "secret123" not in str(err.value)


def test_blank_value_counts_as_missing():
    with pytest.raises(SettingsError):
        load_settings({"LLM_API_KEY": "   ", "LLM_MODEL": "some-model"})


def test_defaults():
    s = load_settings(GOOD)
    assert s.client_id == "kerala"
    assert s.prompt_version == "v1"


def test_optional_overrides():
    s = load_settings({**GOOD, "CLIENT_ID": "other", "PROMPT_VERSION": "v2"})
    assert s.client_id == "other"
    assert s.prompt_version == "v2"


def test_whitespace_is_stripped():
    s = load_settings({"LLM_API_KEY": "  secret123 ", "LLM_MODEL": " some-model "})
    assert s.llm_api_key.get_secret_value() == "secret123"
    assert s.llm_model == "some-model"