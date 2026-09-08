"""Deterministic, weather-based agriculture guidance."""

from typing import Any

RAIN_HIGH_THRESHOLD = 70
RAIN_MODERATE_THRESHOLD = 40
WIND_ADVISORY_THRESHOLD = 30
STRONG_WIND_THRESHOLD = 40
HIGH_TEMP_THRESHOLD = 40
LOW_TEMP_THRESHOLD = 5
THUNDERSTORM_CODES = {95, 96, 99}


def generate_agriculture_advisory(
    weather: dict[str, Any],
    risk_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build cautious farm guidance from the current location's weather."""
    forecast = weather.get("forecast") or []
    tomorrow = next((item for item in forecast if item.get("day") == "Tomorrow"), None)
    rain = tomorrow.get("rain") if tomorrow else weather.get("rain_probability")
    rain = rain if isinstance(rain, (int, float)) else None
    wind = weather.get("wind_speed")
    temperature_values = [weather.get("temperature")] + [
        item.get("high") for item in forecast
    ]
    temperatures = [value for value in temperature_values if isinstance(value, (int, float))]
    max_temp = max(temperatures, default=None)
    low_values = [weather.get("temperature")] + [item.get("low") for item in forecast]
    low_values = [value for value in low_values if isinstance(value, (int, float))]
    min_temp = min(low_values, default=None)
    thunderstorm = weather.get("weather_code") in THUNDERSTORM_CODES or any(
        item.get("weather_code") in THUNDERSTORM_CODES
        or "thunder" in str(item.get("condition", "")).lower()
        for item in forecast
    )

    recommendations: list[dict[str, str]] = []
    if rain is not None:
        if rain >= RAIN_HIGH_THRESHOLD:
            irrigation = "Consider delaying irrigation if sufficient rainfall is expected and crop/soil conditions permit."
            spraying = "Avoid spraying pesticides or foliar fertilizers immediately before expected rainfall."
            rain_advice = f"🌧️ High chance of rain tomorrow ({round(rain)}%). Plan field activities around the expected rainfall."
        elif rain >= RAIN_MODERATE_THRESHOLD:
            irrigation = "Monitor the forecast and soil moisture before deciding on irrigation."
            spraying = "Check the near-term forecast before spraying; rain may reduce effectiveness."
            rain_advice = f"🌦️ Moderate rain possibility tomorrow ({round(rain)}%)."
        else:
            irrigation = "Irrigation may be considered according to crop and soil needs."
            spraying = "Conditions appear more suitable for spraying, but follow product instructions and local guidance."
            rain_advice = f"☀️ Lower rain probability tomorrow ({round(rain)}%)."
        recommendations.extend([
            {"category": "🌧️ Rain", "advice": rain_advice},
            {"category": "💧 Irrigation", "advice": irrigation},
            {"category": "🧴 Spraying", "advice": spraying},
        ])
    if thunderstorm:
        recommendations.append({"category": "⛈️ Thunderstorm", "advice": "Avoid exposed field activities during thunderstorms and follow official local warnings."})
    if isinstance(wind, (int, float)) and wind >= WIND_ADVISORY_THRESHOLD:
        recommendations.append({"category": "💨 Wind", "advice": f"Wind is {round(wind)} km/h. Use caution with spraying, tall crops, temporary structures and exposed equipment."})
    if max_temp is not None and max_temp >= HIGH_TEMP_THRESHOLD:
        recommendations.append({"category": "🌡️ Temperature", "advice": f"Temperature may reach {round(max_temp)}°C. Consider heat-stress risks to crops, livestock and workers; provide adequate water."})
    elif min_temp is not None and min_temp <= LOW_TEMP_THRESHOLD:
        recommendations.append({"category": "🌡️ Temperature", "advice": f"Temperature may fall to {round(min_temp)}°C. Monitor sensitive crops and follow local cold-protection guidance."})

    suitable_day = None
    suitable_score = None
    for item in forecast:
        item_rain = item.get("rain")
        item_high = item.get("high")
        if not all(isinstance(value, (int, float)) for value in (item_rain, item_high)):
            continue
        score = item_rain + (max(0, item_high - 35) * 2) + (20 if item.get("weather_code") in THUNDERSTORM_CODES else 0)
        if suitable_score is None or score < suitable_score:
            suitable_day, suitable_score = item, score
    if suitable_day:
        recommendations.append({"category": "📅 Farm Planning", "advice": f"{suitable_day['day']} appears more suitable for outdoor field activities based on the available forecast ({round(suitable_day['rain'])}% rain)."})
    if risk_analysis:
        for risk in risk_analysis.get("risks", []):
            if risk.get("type") in {"high_rain_probability", "strong_wind", "extreme_heat", "cold_risk"}:
                recommendations.append({
                    "category": f"⚠️ {risk.get('title', 'Weather risk')}",
                    "advice": risk.get("recommendation", "Review weather conditions before field activities."),
                })

    if rain is not None and rain >= RAIN_HIGH_THRESHOLD:
        summary = f"🌾 Rain is likely tomorrow, so irrigation and spraying plans should be reviewed. {suitable_day['day'] if suitable_day else 'Another day'} may be more suitable for field activities."
    elif recommendations:
        summary = "🌾 Review the weather-based recommendations below when planning farm activities."
    else:
        summary = "🌾 No significant agricultural weather risk is indicated in the available forecast."
    return {
        "location": weather.get("location", "Selected location"),
        "summary": summary,
        "recommendations": recommendations,
        "forecast": forecast,
        "source": "Open-Meteo forecast" if weather.get("is_live") else "Demo weather data",
        "is_demo": not weather.get("is_live", False),
    }


def get_demo_advisory(question: str, location: str = "Patna, Bihar, India") -> dict[str, str]:
    """Backward-compatible response for callers outside the advisory page."""
    if "pesticide" in question.lower():
        return {"condition": "Moderate wind", "risk": "Medium", "recommendation": "Postpone spraying", "action": "Wait for a calmer window", "reason": f"Demo guidance for {location}: wind and possible rain can reduce spray effectiveness."}
    if "harvest" in question.lower():
        return {"condition": "Rain possible tomorrow", "risk": "High", "recommendation": "Plan harvest carefully", "action": "Prioritise ready crops", "reason": "Demo forecast suggests rainfall may affect field access and crop quality."}
    return {"condition": "Warm and partly cloudy", "risk": "Low to medium", "recommendation": "Irrigate only if soil is dry", "action": "Check soil moisture first", "reason": "Demo conditions do not indicate an urgent irrigation window."}
