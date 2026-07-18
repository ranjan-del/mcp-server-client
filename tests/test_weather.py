"""Tests for the weather tool: deterministic offline stub."""

import pytest

from server.tools.weather import get_weather


def test_returns_stub_offline(monkeypatch):
    # Ensure no live key so we exercise the offline stub.
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    report = get_weather("London")
    assert report["city"] == "London"
    assert report["source"] == "offline-stub"
    assert set(report) >= {"temperature_c", "condition", "humidity_percent", "wind_kph"}


def test_deterministic(monkeypatch):
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    # Same city -> identical report every time.
    assert get_weather("Paris") == get_weather("Paris")


def test_case_insensitive(monkeypatch):
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    a = get_weather("Tokyo")
    b = get_weather("  tokyo ")
    # Temperature/condition are keyed off the normalised name, so they match.
    assert a["temperature_c"] == b["temperature_c"]
    assert a["condition"] == b["condition"]


def test_empty_city_rejected():
    with pytest.raises(ValueError):
        get_weather("")
