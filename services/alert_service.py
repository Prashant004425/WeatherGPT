"""Deterministic weather alerts generated from current forecast data."""

import json
from pathlib import Path
from typing import Any

RAIN_WARNING_THRESHOLD = 70
RAIN_ADVISORY_THRESHOLD = 50
STRONG_WIND_THRESHOLD = 40
HIGH_WIND_THRESHOLD = 60
HIGH_TEMPERATURE_THRESHOLD = 40
LOW_TEMPERATURE_THRESHOLD = 5
THUNDERSTORM_CODES = {95, 96, 99}

_SEVERITY_ORDER = {"SEVERE": 0, "WARNING": 1, "ADVISORY": 2, "INFO": 3}


def _alert(
    alert_type: str,
    severity: str,
    title: str,
    icon: str,
    message: str,
    recommendation: str,
    weather: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": alert_type,
        "alert_type": title,
        "severity": severity,
        "title": title,
        "icon": icon,
        "message": message,
        "condition": message,
        "recommendation": recommendation,
        "action": recommendation,
        "location": weather.get("location", "Selected location"),
        "source": "Open-Meteo forecast" if weather.get("is_live") else "Demo weather data",
        "is_demo": not weather.get("is_live", False),
        "timestamp": weather.get("updated", ""),
    }


def generate_weather_alerts(weather: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate every applicable alert from one location's weather snapshot."""
    alerts: list[dict[str, Any]] = []
    forecast = weather.get("forecast") or []
    tomorrow = next((item for item in forecast if item.get("day") == "Tomorrow"), None)
    rain_probability = tomorrow.get("rain") if tomorrow else weather.get("rain_probability")
    if isinstance(rain_probability, (int, float)):
        if rain_probability >= RAIN_WARNING_THRESHOLD:
            alerts.append(_alert("rain", "WARNING", "Heavy Rain Risk", "🌧️", f"High probability of rain tomorrow: {round(rain_probability)}%.", "Carry rain protection and be cautious around waterlogged areas.", weather))
        elif rain_probability >= RAIN_ADVISORY_THRESHOLD:
            alerts.append(_alert("rain", "ADVISORY", "Rain Advisory", "🌦️", f"Rain is possible tomorrow, with a {round(rain_probability)}% probability.", "Plan outdoor activities with rain protection available.", weather))

    thunderstorm = weather.get("weather_code") in THUNDERSTORM_CODES or any(
        item.get("weather_code") in THUNDERSTORM_CODES
        or "thunder" in str(item.get("condition", "")).lower()
        for item in forecast
    )
    if thunderstorm:
        alerts.append(_alert("thunderstorm", "WARNING", "Thunderstorm Alert", "⛈️", "Thunderstorms are indicated in the available forecast.", "Avoid exposed outdoor areas and monitor official weather advisories.", weather))

    wind = weather.get("wind_speed")
    if isinstance(wind, (int, float)) and wind >= STRONG_WIND_THRESHOLD:
        severity = "WARNING" if wind >= HIGH_WIND_THRESHOLD else "ADVISORY"
        title = "High Wind Alert" if wind >= HIGH_WIND_THRESHOLD else "Strong Wind Advisory"
        alerts.append(_alert("wind", severity, title, "💨", f"Wind speed is currently {round(wind)} km/h.", "Secure loose objects and use caution outdoors.", weather))

    temperatures = [weather.get("temperature")]
    temperatures.extend(
        item.get("high") for item in forecast if isinstance(item.get("high"), (int, float))
    )
    temperatures.extend(
        item.get("low") for item in forecast if isinstance(item.get("low"), (int, float))
    )
    max_temperature = max((value for value in temperatures if isinstance(value, (int, float))), default=None)
    min_temperature = min((value for value in temperatures if isinstance(value, (int, float))), default=None)
    if max_temperature is not None and max_temperature >= HIGH_TEMPERATURE_THRESHOLD:
        alerts.append(_alert("temperature", "WARNING", "High Temperature Alert", "🌡️", f"Temperature may reach {round(max_temperature)}°C.", "Stay hydrated and avoid prolonged exposure to heat.", weather))
    if min_temperature is not None and min_temperature <= LOW_TEMPERATURE_THRESHOLD:
        alerts.append(_alert("temperature", "ADVISORY", "Low Temperature Advisory", "🥶", f"Temperature may fall to {round(min_temperature)}°C.", "Protect people, livestock and temperature-sensitive crops.", weather))
    return sorted(alerts, key=lambda item: _SEVERITY_ORDER.get(item["severity"], 99))


def get_alerts(location: str) -> list[dict]:
    """Backward-compatible demo alerts for non-weather-service callers."""
    data_path = Path(__file__).parent.parent / "data" / "sample_alerts.json"
    try:
        with data_path.open(encoding="utf-8") as alerts_file:
            alerts = json.load(alerts_file)
        return [dict(alert, location=location, is_demo=True, source="Demo alert data") for alert in alerts]
    except (OSError, json.JSONDecodeError):
        return []
