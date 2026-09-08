"""Deterministic, explainable weather risk analysis."""

from typing import Any

LOW = "LOW"
MODERATE = "MODERATE"
HIGH = "HIGH"
EXTREME = "EXTREME"

# These are application-level thresholds, not official government warnings.
RAIN_PROBABILITY_THRESHOLDS = ((90, EXTREME), (70, HIGH), (50, MODERATE))
WIND_THRESHOLDS = ((70, EXTREME), (50, HIGH), (30, MODERATE))
HEAT_THRESHOLDS = ((45, EXTREME), (40, HIGH), (35, MODERATE))
COLD_THRESHOLDS = ((0, EXTREME), (5, HIGH), (10, MODERATE))
LEVEL_SCORES = {LOW: 15, MODERATE: 35, HIGH: 65, EXTREME: 90}
LEVEL_ORDER = {LOW: 0, MODERATE: 1, HIGH: 2, EXTREME: 3}


def _level(value: float, thresholds: tuple[tuple[float, str], ...]) -> str | None:
    for threshold, level in thresholds:
        matches = value <= threshold if thresholds is COLD_THRESHOLDS else value >= threshold
        if matches:
            return level
    return None


def _risk(
    risk_type: str,
    level: str,
    title: str,
    description: str,
    recommendation: str,
    source: str,
) -> dict[str, Any]:
    return {
        "type": risk_type,
        "level": level,
        "score": LEVEL_SCORES[level],
        "title": title,
        "description": description,
        "recommendation": recommendation,
        "source": source,
    }


def _tomorrow(weather: dict[str, Any]) -> dict[str, Any] | None:
    forecast = weather.get("forecast")
    if not isinstance(forecast, list):
        return None
    return next((item for item in forecast if item.get("day") == "Tomorrow"), None)


def analyze_weather_risk(weather: dict[str, Any]) -> dict[str, Any]:
    """Analyze only measurements available in the current weather payload."""
    source = "Open-Meteo" if weather.get("is_live") else "Demo weather data"
    risks: list[dict[str, Any]] = []
    tomorrow = _tomorrow(weather)
    rain_probability = tomorrow.get("rain") if tomorrow else weather.get("rain_probability")
    if isinstance(rain_probability, (int, float)):
        level = _level(float(rain_probability), RAIN_PROBABILITY_THRESHOLDS)
        if level:
            risks.append(_risk(
                "high_rain_probability",
                level,
                "High Rain Probability",
                f"Rain probability is {round(rain_probability)}% for the highest-risk available period.",
                "Plan outdoor activities carefully and review irrigation or spraying plans.",
                source,
            ))

    weather_code = weather.get("weather_code")
    thunderstorm = weather_code in {95, 96, 99} or any(
        isinstance(item, dict)
        and (item.get("weather_code") in {95, 96, 99} or "thunder" in str(item.get("condition", "")).lower())
        for item in (weather.get("forecast") or [])
    )
    if thunderstorm:
        risks.append(_risk(
            "thunderstorm",
            HIGH,
            "Thunderstorm",
            "A thunderstorm condition is indicated by the available WMO weather code or forecast.",
            "Avoid exposed outdoor areas and monitor official local advisories.",
            source,
        ))

    wind = weather.get("wind_speed")
    if isinstance(wind, (int, float)):
        level = _level(float(wind), WIND_THRESHOLDS)
        if level:
            risks.append(_risk(
                "strong_wind",
                level,
                "Strong Wind",
                f"Wind speed is {round(wind)} km/h, above the application-level threshold.",
                "Secure loose objects and use caution with travel, spraying and exposed equipment.",
                source,
            ))

    temperatures = [weather.get("temperature")]
    temperatures.extend(
        item.get("high") for item in (weather.get("forecast") or []) if isinstance(item, dict)
    )
    valid_temperatures = [float(value) for value in temperatures if isinstance(value, (int, float))]
    if valid_temperatures:
        maximum = max(valid_temperatures)
        level = _level(maximum, HEAT_THRESHOLDS)
        if level:
            risks.append(_risk(
                "extreme_heat",
                level,
                "Extreme Heat",
                f"Available temperatures reach {round(maximum)}°C, above the application-level threshold.",
                "Limit prolonged heat exposure, stay hydrated and consider crop or livestock heat stress.",
                source,
            ))

    low_temperatures = [item.get("low") for item in (weather.get("forecast") or []) if isinstance(item, dict)]
    valid_lows = [float(value) for value in low_temperatures if isinstance(value, (int, float))]
    if valid_lows:
        minimum = min(valid_lows)
        level = _level(minimum, COLD_THRESHOLDS)
        if level:
            risks.append(_risk(
                "cold_risk",
                level,
                "Cold Risk",
                f"Forecast minimum temperature may reach {round(minimum)}°C.",
                "Protect people, livestock and temperature-sensitive crops from cold exposure.",
                source,
            ))

    agricultural_risks = [
        risk for risk in risks
        if risk["type"] in {"high_rain_probability", "strong_wind", "extreme_heat", "cold_risk"}
    ]
    if agricultural_risks:
        strongest = max(agricultural_risks, key=lambda item: LEVEL_ORDER[item["level"]])
        risks.append(_risk(
            "agricultural_weather",
            strongest["level"],
            "Agricultural Weather Risk",
            "Rain, wind or temperature conditions may affect weather-sensitive farm activities.",
            "Use the Agriculture Advisory for general weather-based planning; follow local agricultural guidance.",
            source,
        ))

    scored_risks = [risk for risk in risks if risk["type"] != "agricultural_weather"]
    overall_score = min(
        100,
        max((risk["score"] for risk in scored_risks), default=0)
        + max(0, len(scored_risks) - 1) * 5,
    )
    if overall_score >= 75:
        overall_level = EXTREME
    elif overall_score >= 50:
        overall_level = HIGH
    elif overall_score >= 25:
        overall_level = MODERATE
    else:
        overall_level = LOW
    return {
        "overall_score": overall_score,
        "overall_level": overall_level,
        "risks": sorted(risks, key=lambda item: (-LEVEL_ORDER[item["level"]], item["title"])),
        "source": source,
        "is_demo": not bool(weather.get("is_live")),
    }


def get_risk_summary(risk_analysis: dict[str, Any], language: str = "English") -> str:
    """Return a short localized summary without adding new meteorological facts."""
    level = risk_analysis.get("overall_level", LOW)
    count = len(risk_analysis.get("risks", []))
    if language == "हिंदी":
        if count:
            return f"{count} मौसम जोखिम पाए गए। समग्र जोखिम स्तर {level} है। बाहर की गतिविधियों में सावधानी बरतें और अनुशंसित कार्रवाई देखें।"
        return "कोई महत्वपूर्ण मौसम जोखिम नहीं पाया गया।"
    if count:
        return f"{count} weather risk(s) detected. Overall risk is {level}. Plan outdoor activities with caution and review the recommended actions."
    return "No significant weather risks detected in the available data."
