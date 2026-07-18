"""Weather tool.

MEMORY.md checklist: MCP Server tools -> weather.

Offline-first design
--------------------
The default code path returns a **deterministic offline stub** so the tool (and
its tests) run with no network access and no API key. The stub derives its
numbers from a hash of the city name, which means the same city always yields
the same "weather" -- handy for reproducible tests and demos.

If the ``WEATHER_API_KEY`` environment variable is set, :func:`get_weather` will
instead try a real lookup against the free Open-Meteo-style flow. That path is
optional and never exercised by the test-suite.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict

# A small, fixed set of weather conditions the stub can pick from.
_CONDITIONS = ["Sunny", "Partly cloudy", "Cloudy", "Rainy", "Thunderstorm", "Snowy", "Foggy"]


def _deterministic_weather(city: str) -> Dict[str, Any]:
    """Return a stable, made-up weather report for ``city``.

    We hash the (lower-cased) city name to get a stable integer, then map slices
    of that integer onto a temperature, condition and humidity. Because the hash
    is deterministic, the same city always produces the same report -- so tests
    can assert on exact values without any flakiness.
    """
    normalized = city.strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    seed = int(digest, 16)

    # Map the seed onto plausible-looking ranges.
    temperature_c = (seed % 45) - 5           # -5 .. 39 C
    condition = _CONDITIONS[seed % len(_CONDITIONS)]
    humidity = 30 + (seed % 70)               # 30 .. 99 %
    wind_kph = seed % 40                       # 0 .. 39 kph

    return {
        "city": city,
        "source": "offline-stub",
        "temperature_c": temperature_c,
        "condition": condition,
        "humidity_percent": humidity,
        "wind_kph": wind_kph,
    }


def get_weather(city: str) -> Dict[str, Any]:
    """Return a weather report for ``city``.

    Uses the deterministic offline stub by default. If ``WEATHER_API_KEY`` is
    set the real-API branch is attempted, but any failure falls back to the stub
    so the tool never hard-crashes on a network hiccup.
    """
    if not isinstance(city, str) or not city.strip():
        raise ValueError("city must be a non-empty string")

    api_key = os.environ.get("WEATHER_API_KEY")
    if api_key:
        try:
            return _get_weather_live(city, api_key)
        except Exception:  # noqa: BLE001 - graceful degradation is intentional
            # Never fail the tool because of a live-API problem; fall back.
            pass

    return _deterministic_weather(city)


def _get_weather_live(city: str, api_key: str) -> Dict[str, Any]:
    """Optional real lookup (only used when WEATHER_API_KEY is set).

    Kept deliberately small and dependency-light. Uses ``httpx`` which is already
    an MCP dependency. This branch is never hit by the offline test-suite.
    """
    import httpx  # local import: only needed on the optional live path

    # WeatherAPI.com style current-weather endpoint. Any provider could be wired
    # here; the point is to show where a real integration would live.
    url = "https://api.weatherapi.com/v1/current.json"
    params = {"key": api_key, "q": city}
    resp = httpx.get(url, params=params, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    current = data["current"]
    return {
        "city": data["location"]["name"],
        "source": "weatherapi.com",
        "temperature_c": current["temp_c"],
        "condition": current["condition"]["text"],
        "humidity_percent": current["humidity"],
        "wind_kph": current["wind_kph"],
    }


def register(mcp) -> None:
    """Expose :func:`get_weather` as an MCP tool on the given FastMCP server."""

    @mcp.tool()
    def weather(city: str) -> Dict[str, Any]:
        """Get the current weather for a city.

        Returns a deterministic offline stub unless WEATHER_API_KEY is set, in
        which case a real weather API is queried.
        """
        return get_weather(city)
