"""Open-Meteo weather retrieval with a safe demo fallback."""

from datetime import datetime
from typing import Any

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

_WEATHER_CODES: dict[int, tuple[str, str]] = {
    0: ("Sunny", "☀️"),
    1: ("Mostly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Heavy drizzle", "🌧️"),
    56: ("Freezing drizzle", "🌧️"),
    57: ("Freezing drizzle", "🌧️"),
    61: ("Rain", "🌧️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"),
    67: ("Freezing rain", "🌧️"),
    71: ("Snow", "❄️"),
    73: ("Snow", "❄️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Rain showers", "🌦️"),
    81: ("Rain showers", "🌦️"),
    82: ("Heavy rain showers", "🌧️"),
    85: ("Snow showers", "🌨️"),
    86: ("Heavy snow showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm", "⛈️"),
    99: ("Thunderstorm", "⛈️"),
}


def weather_condition(code: int) -> tuple[str, str]:
    """Map an Open-Meteo WMO weather code to readable text and an icon."""
    return _WEATHER_CODES.get(code, ("Unknown", "🌡️"))


def _search_queries(location: str) -> list[str]:
    """Try natural user input and a comma-separated variant."""
    cleaned = " ".join(location.strip().split())
    queries = [cleaned]
    if "," not in cleaned and len(cleaned.split()) > 1:
        queries.append(", ".join(cleaned.split()))
    return list(dict.fromkeys(query for query in queries if query))


def _location_score(query: str, result: dict[str, Any]) -> int:
    """Rank exact city/region matches above unrelated same-name locations."""
    normalized_query = " ".join(query.replace(",", " ").casefold().split())
    name = str(result.get("name", "")).casefold()
    region = str(result.get("admin1", "")).casefold()
    country = str(result.get("country", "")).casefold()
    query_terms = set(normalized_query.split())
    score = 0
    if name == normalized_query:
        score += 180
    if name in query_terms:
        score += 100
    if name and name in query.casefold():
        score += 40
    if region and any(term in region for term in query_terms):
        score += 35
    if country and any(term in country for term in query_terms):
        score += 25
    if result.get("country_code", "").casefold() == "in" and any(term in query_terms for term in {"india", "ranchi", "delhi", "mumbai", "patna", "kolkata", "bengaluru"}):
        score += 10
    return score


def search_locations(location: str, count: int = 5) -> list[dict[str, Any]]:
    """Return multiple structured location matches for a natural-language query."""
    matches: list[dict[str, Any]] = []
    seen: set[tuple[float, float]] = set()
    queries = _search_queries(location)
    for query in queries:
        response = requests.get(
            GEOCODING_URL,
            params={"name": query, "count": count, "language": "en", "format": "json"},
            timeout=8,
        )
        response.raise_for_status()
        for result in response.json().get("results", []):
            coordinates = (float(result["latitude"]), float(result["longitude"]))
            if coordinates in seen:
                continue
            seen.add(coordinates)
            matches.append(
                {
                    "name": result["name"],
                    "latitude": coordinates[0],
                    "longitude": coordinates[1],
                    "admin1": result.get("admin1", ""),
                    "country": result.get("country", ""),
                    "country_code": result.get("country_code", ""),
                }
            )
        if matches and len(matches) >= count:
            break
    return sorted(
        matches,
        key=lambda result: max(_location_score(query, result) for query in queries),
        reverse=True,
    )


def geocode_location(location: str) -> dict[str, Any]:
    """Resolve a city or location into coordinates using Open-Meteo geocoding."""
    matches = search_locations(location, count=5)
    if not matches:
        raise ValueError(f"No location found for {location!r}")
    return matches[0]


def get_current_weather(latitude: float, longitude: float) -> dict[str, Any]:
    """Retrieve current conditions and the nearest hourly rain probability."""
    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
            "hourly": "precipitation_probability",
            "timezone": "auto",
            "forecast_days": 5,
        },
        timeout=8,
    )
    response.raise_for_status()
    data = response.json()
    current = data["current"]
    hourly = data["hourly"]
    current_time = current["time"]
    nearest_index = min(
        range(len(hourly["time"])),
        key=lambda index: abs(
            datetime.fromisoformat(hourly["time"][index]).timestamp()
            - datetime.fromisoformat(current_time).timestamp()
        ),
    )
    condition, icon = weather_condition(int(current["weather_code"]))
    return {
        "weather_code": int(current["weather_code"]),
        "temperature": round(current["temperature_2m"]),
        "condition": condition,
        "icon": icon,
        "feels_like": round(current["apparent_temperature"]),
        "humidity": round(current["relative_humidity_2m"]),
        "wind_speed": round(current["wind_speed_10m"]),
        "rain_probability": round(hourly["precipitation_probability"][nearest_index]),
        "updated": datetime.fromisoformat(current_time).strftime("%d %b %Y, %H:%M"),
    }


def get_forecast(latitude: float, longitude: float) -> list[dict[str, Any]]:
    """Retrieve five days of daily forecast data."""
    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "timezone": "auto",
            "forecast_days": 5,
        },
        timeout=8,
    )
    response.raise_for_status()
    daily = response.json()["daily"]
    forecast = []
    for index, date_value in enumerate(daily["time"]):
        condition, icon = weather_condition(int(daily["weather_code"][index]))
        day = datetime.fromisoformat(date_value).strftime("%a")
        if index == 0:
            day = "Today"
        elif index == 1:
            day = "Tomorrow"
        forecast.append(
            {
                "day": day,
                "icon": icon,
                "condition": condition,
                "high": round(daily["temperature_2m_max"][index]),
                "low": round(daily["temperature_2m_min"][index]),
                "rain": round(daily["precipitation_probability_max"][index]),
                "weather_code": int(daily["weather_code"][index]),
            }
        )
    return forecast


def _demo_weather(location: str, error: str = "") -> dict[str, Any]:
    return {
        "location": location,
        "temperature": 29,
        "condition": "Partly cloudy",
        "icon": "⛅",
        "feels_like": 31,
        "humidity": 67,
        "wind_speed": 13,
        "rain_probability": 35,
        "updated": "Demo snapshot",
        "forecast": [
            {"day": "Today", "icon": "⛅", "condition": "Partly cloudy", "high": 31, "low": 24, "rain": 35},
            {"day": "Tomorrow", "icon": "🌦️", "condition": "Light rain", "high": 29, "low": 23, "rain": 60},
            {"day": "Wed", "icon": "🌤️", "condition": "Mostly clear", "high": 32, "low": 24, "rain": 20},
            {"day": "Thu", "icon": "⛈️", "condition": "Thunderstorms", "high": 30, "low": 23, "rain": 70},
            {"day": "Fri", "icon": "☀️", "condition": "Sunny", "high": 33, "low": 25, "rain": 10},
        ],
        "is_live": False,
        "error": error,
        "weather_code": 2,
    }


def get_weather(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """Resolve a location and return live weather, or clearly marked demo data."""
    try:
        place = (
            {"name": location, "latitude": latitude, "longitude": longitude}
            if latitude is not None and longitude is not None
            else geocode_location(location)
        )
        current = get_current_weather(place["latitude"], place["longitude"])
        forecast = get_forecast(place["latitude"], place["longitude"])
        display_location = location
        if latitude is None or longitude is None:
            display_location = ", ".join(
                part for part in (place["name"], place.get("admin1"), place.get("country")) if part
            )
        return {
            "location": display_location,
            **current,
            "forecast": forecast,
            "is_live": True,
            "error": "",
            "latitude": place["latitude"],
            "longitude": place["longitude"],
        }
    except (requests.RequestException, KeyError, TypeError, ValueError, IndexError) as error:
        return _demo_weather(location, str(error))
