"""Conversational weather intelligence with optional Ollama support."""

import os
from typing import Any

import requests

from services.language_service import SUPPORTED_LANGUAGES

SYSTEM_PROMPT = """You are WeatherGPT, a conversational weather intelligence assistant.
Answer only from the supplied meteorological context. Never invent weather values or alerts.
Be concise, friendly and actionable. For safety questions, recommend official local advisories.
Do not present demo alerts as official warnings. Answer in the requested language."""


def build_weather_context(weather: dict[str, Any]) -> dict[str, Any]:
    """Keep only useful, structured weather facts for the response layer."""
    return {
        "location": weather.get("location", ""),
        "coordinates": {
            "latitude": weather.get("latitude"),
            "longitude": weather.get("longitude"),
        },
        "live": bool(weather.get("is_live")),
        "current": {
            "temperature_c": weather.get("temperature"),
            "feels_like_c": weather.get("feels_like"),
            "humidity_percent": weather.get("humidity"),
            "wind_kmh": weather.get("wind_speed"),
            "rain_probability_percent": weather.get("rain_probability"),
            "condition": weather.get("condition"),
            "icon": weather.get("icon"),
        },
        "forecast": [
            {
                "day": item.get("day"),
                "max_c": item.get("high"),
                "min_c": item.get("low"),
                "rain_probability_percent": item.get("rain"),
                "condition": item.get("condition"),
            }
            for item in weather.get("forecast", [])
        ],
    }


def _intent(question: str) -> str:
    text = question.lower()
    if any(word in text for word in ("climate", "historical", "trend", "rainfall pattern", "which month", "जलवायु", "ऐतिहासिक", "জলবায়ু", "ঐতিহাসিক", "हवामान", "ऐतिहासिक", "வானிலை வரலாறு", "காலநிலை", "వాతావరణం", "చారిత్రక")):
        return "CLIMATE"
    if any(word in text for word in ("thunder", "lightning")):
        return "THUNDERSTORM"
    if any(word in text for word in ("alert", "warning", "risk", "careful")):
        return "ALERTS"
    if any(word in text for word in ("irrigat", "crop", "farm", "spray", "harvest", "सिंचाई", "फसल", "खेती", "সেচ", "ফসল", "শস্য", "पिक", "शेती", "பயிர்", "விவசாய", "నీటిపారుదల", "పంట")):
        return "AGRICULTURE"
    if any(word in text for word in ("umbrella", "travel", "outdoor", "outside", "safe", "सुरक्षित", "बाहर", "छाता", "নিরাপদ", "বাইরে", "छत्री", "सुरक्षित", "வெளியே", "பாதுகாப்பான", "బయట", "సురక్షితం")):
        return "OUTDOOR_ACTIVITY"
    if any(word in text for word in ("rain", "precipitation", "umbrella", "बारिश", "वर्षा")):
        return "RAIN"
    if any(word in text for word in ("temperature", "hot", "cold", "heat", "तापमान", "गर्मी", "ঠান্ডা", "তাপমাত্রা", "उष्ण", "थंडी", "तापमान", "வெப்பநிலை", "சூடு", "చల్లని", "ఉష్ణోగ్రత")):
        return "TEMPERATURE"
    if any(word in text for word in ("wind", "वारा", "हवा", "বাতাস", "காற்று", "గాలి")):
        return "WIND"
    if any(word in text for word in ("humid", "आर्द्रता", "আর্দ্রতা", "आर्द्र", "ஈரப்பதம்", "తేమ")):
        return "HUMIDITY"
    if any(word in text for word in ("tomorrow", "forecast", "weekend", "next few days", "उद्या", "कल", "আগামীকাল", "நாளை", "రేపు")):
        return "FORECAST"
    if any(word in text for word in ("weather", "right now", "today", "मौसम", "आज", "আবহাওয়া", "आज", "வானிலை", "இன்று", "వాతావరణం", "ఈ రోజు")):
        return "CURRENT_WEATHER"
    return "GENERAL_WEATHER"


def _english_fallback(question: str, context: dict[str, Any]) -> str:
    location = context["location"]
    current = context["current"]
    forecast = context["forecast"]
    tomorrow = next((item for item in forecast if item["day"] == "Tomorrow"), forecast[1] if len(forecast) > 1 else None)
    intent = _intent(question)
    if intent == "RAIN" and tomorrow:
        return f"{tomorrow['condition']} is expected tomorrow in {location}, with a {tomorrow['rain_probability_percent']}% chance of rain."
    if intent == "THUNDERSTORM":
        thunder = next((item for item in forecast if "thunder" in str(item["condition"]).lower()), None)
        return f"⛈️ Thunderstorms are {'possible' if thunder else 'not indicated'} in the available forecast for {location}." + (" Check official advisories before travelling." if thunder else "")
    if intent == "ALERTS":
        alerts = context.get("alerts", [])
        if alerts:
            return "🚨 " + " ".join(
                f"{alert.get('title')}: {alert.get('message')}" for alert in alerts[:2]
            ) + " Monitor official local advisories."
        return f"✅ No significant weather risks are indicated in the available forecast for {location}."
    if intent == "CLIMATE":
        climate = context.get("climate_analysis")
        if climate:
            return f"📊 Based on available historical weather data for {location}, the temperature trend is {climate['temperature_trend']} and precipitation is highest in {climate['wettest_month']}."
        return "Historical climate analysis is not available in the current context."
    if intent == "TEMPERATURE":
        return f"🌡️ It is {current['temperature_c']}°C in {location}, feeling like {current['feels_like_c']}°C."
    if intent == "WIND":
        return f"💨 Wind speed is {current['wind_kmh']} km/h in {location}."
    if intent == "HUMIDITY":
        return f"💧 Relative humidity is {current['humidity_percent']}% in {location}."
    if intent == "OUTDOOR_ACTIVITY":
        risk = context.get("weather_risk", {})
        advice = (
            f"The deterministic weather risk level is {risk['overall_level']}; "
            "avoid unnecessary travel during the highest-risk period and check official advisories."
            if risk.get("overall_level") in {"HIGH", "EXTREME"}
            else "Conditions look generally manageable, but check official advisories before travelling."
        )
        return f"☀️ For outdoor plans in {location}: {advice}"
    if intent == "AGRICULTURE":
        advisory = context.get("agriculture_advisory")
        if advisory and advisory.get("summary"):
            return f"{advisory['summary']} This is weather-based guidance, not professional agricultural advice."
        rain = tomorrow["rain_probability_percent"] if tomorrow else current["rain_probability_percent"]
        return f"🌾 Rain probability is {rain}%. Irrigation or spraying decisions should also consider soil and crop conditions; this is weather-based guidance, not professional agricultural advice."
    if intent in {"CURRENT_WEATHER", "FORECAST"}:
        return f"{current['icon'] if 'icon' in current else '🌤️'} {location} is currently {current['condition']} at {current['temperature_c']}°C. Tomorrow: {tomorrow['condition'] if tomorrow else 'unavailable'}, {tomorrow['min_c']}–{tomorrow['max_c']}°C." 
    return "I'm WeatherGPT, so I can help with weather, forecasts, alerts, climate and weather-based advisories."


def _hindi_fallback(_question: str, context: dict[str, Any]) -> str:
    current = context["current"]
    forecast = context["forecast"]
    tomorrow = next((item for item in forecast if item["day"] == "Tomorrow"), forecast[1] if len(forecast) > 1 else None)
    if _intent(_question) == "CLIMATE":
        climate = context.get("climate_analysis")
        if climate:
            return f"📊 उपलब्ध ऐतिहासिक मौसम डेटा के अनुसार तापमान का रुझान {climate['temperature_trend']} है और सबसे अधिक वर्षण {climate['wettest_month']} में हुआ।"
        return "ऐतिहासिक जलवायु विश्लेषण अभी उपलब्ध नहीं है।"
    if _intent(_question) == "RAIN" and tomorrow:
        return f"🌧️ कल {tomorrow['rain_probability_percent']}% बारिश की संभावना है। तापमान {tomorrow['min_c']}°C से {tomorrow['max_c']}°C के बीच रह सकता है।"
    if _intent(_question) == "TEMPERATURE":
        return f"🌡️ अभी तापमान {current['temperature_c']}°C है और महसूस होने वाला तापमान {current['feels_like_c']}°C है।"
    if _intent(_question) == "AGRICULTURE":
        return f"🌾 बारिश की संभावना {tomorrow['rain_probability_percent'] if tomorrow else current['rain_probability_percent']}% है। सिंचाई या छिड़काव से पहले मिट्टी और फसल की स्थिति भी देखें।"
    return f"🌤️ अभी मौसम {current['condition']} है और तापमान {current['temperature_c']}°C है। अधिक जानकारी के लिए अपना मौसम संबंधी प्रश्न पूछें।"


def _localized_fallback(question: str, context: dict[str, Any], language: str) -> str:
    """Provide deterministic common answers when an LLM is unavailable."""
    if language not in SUPPORTED_LANGUAGES or language in {"English", "हिंदी"}:
        return _hindi_fallback(question, context) if language == "हिंदी" else _english_fallback(question, context)
    current = context["current"]
    forecast = context["forecast"]
    tomorrow = next((item for item in forecast if item["day"] == "Tomorrow"), forecast[1] if len(forecast) > 1 else None)
    intent = _intent(question)
    temperature = current["temperature_c"]
    feels_like = current["feels_like_c"]
    rain = tomorrow["rain_probability_percent"] if tomorrow else current["rain_probability_percent"]
    location = context["location"]
    translations = {
        "বাংলা": {
            "temperature": f"🌡️ {location}-এ এখন তাপমাত্রা {temperature}°C, অনুভূত হচ্ছে {feels_like}°C।",
            "rain": f"🌧️ আগামীকাল বৃষ্টির সম্ভাবনা {rain}%।",
            "agriculture": f"🌾 আগামীকাল বৃষ্টির সম্ভাবনা {rain}%। সেচ বা স্প্রে করার আগে মাটি ও ফসলের অবস্থা দেখুন।",
            "general": f"🌤️ {location}-এর বর্তমান আবহাওয়া {current['condition']} এবং তাপমাত্রা {temperature}°C।",
            "forecast": f"🌤️ {location}-এ এখন {current['condition']}, {temperature}°C। আগামীকাল: {tomorrow['condition'] if tomorrow else 'তথ্য নেই'}।",
            "outdoor": "☀️ বাইরে যাওয়ার আগে পূর্বাভাস ও সরকারি পরামর্শ দেখুন।",
        },
        "मराठी": {
            "temperature": f"🌡️ {location} येथे सध्याचे तापमान {temperature}°C असून जाणवणारे तापमान {feels_like}°C आहे.",
            "rain": f"🌧️ उद्या पावसाची शक्यता {rain}% आहे.",
            "agriculture": f"🌾 उद्या पावसाची शक्यता {rain}% आहे. सिंचन किंवा फवारणीपूर्वी माती आणि पिकांची स्थिती तपासा.",
            "general": f"🌤️ {location} येथील सध्याचे हवामान {current['condition']} आणि तापमान {temperature}°C आहे.",
            "forecast": f"🌤️ {location} येथे सध्या {current['condition']}, {temperature}°C. उद्या: {tomorrow['condition'] if tomorrow else 'माहिती उपलब्ध नाही'}.",
            "outdoor": "☀️ बाहेर जाण्यापूर्वी अंदाज आणि अधिकृत सूचना तपासा.",
        },
        "தமிழ்": {
            "temperature": f"🌡️ {location} தற்போதைய வெப்பநிலை {temperature}°C; உணரப்படும் வெப்பநிலை {feels_like}°C.",
            "rain": f"🌧️ நாளை மழைக்கான வாய்ப்பு {rain}%.",
            "agriculture": f"🌾 நாளை மழைக்கான வாய்ப்பு {rain}%. பாசனம் அல்லது தெளிப்புக்கு முன் மண் மற்றும் பயிர் நிலையைப் பாருங்கள்.",
            "general": f"🌤️ {location} தற்போதைய வானிலை {current['condition']}, வெப்பநிலை {temperature}°C.",
            "forecast": f"🌤️ {location} தற்போது {current['condition']}, {temperature}°C. நாளை: {tomorrow['condition'] if tomorrow else 'தகவல் இல்லை'}.",
            "outdoor": "☀️ வெளியே செல்லும் முன் முன்னறிவிப்பு மற்றும் அதிகாரப்பூர்வ அறிவுரைகளைப் பாருங்கள்.",
        },
        "తెలుగు": {
            "temperature": f"🌡️ {location}లో ప్రస్తుత ఉష్ణోగ్రత {temperature}°C, అనిపించే ఉష్ణోగ్రత {feels_like}°C.",
            "rain": f"🌧️ రేపు వర్షం పడే అవకాశం {rain}%.",
            "agriculture": f"🌾 రేపు వర్షం పడే అవకాశం {rain}%. నీటిపారుదల లేదా పిచికారీకి ముందు నేల, పంట పరిస్థితిని పరిశీలించండి.",
            "general": f"🌤️ {location}లో ప్రస్తుత వాతావరణం {current['condition']}, ఉష్ణోగ్రత {temperature}°C.",
            "forecast": f"🌤️ {location}లో ప్రస్తుతం {current['condition']}, {temperature}°C. రేపు: {tomorrow['condition'] if tomorrow else 'సమాచారం లేదు'}.",
            "outdoor": "☀️ బయటకు వెళ్లే ముందు సూచన మరియు అధికారిక సలహాలను పరిశీలించండి.",
        },
    }[language]
    if intent == "TEMPERATURE":
        return translations["temperature"]
    if intent == "RAIN":
        return translations["rain"] + (f" ఉష్ణోగ్రత {tomorrow['min_c']}°C నుండి {tomorrow['max_c']}°C వరకు ఉండవచ్చు." if language == "తెలుగు" and tomorrow else "")
    if intent == "AGRICULTURE":
        return translations["agriculture"]
    if intent == "OUTDOOR_ACTIVITY":
        return translations["outdoor"]
    if intent in {"CURRENT_WEATHER", "FORECAST"}:
        return translations["forecast"]
    return translations["general"]


def _ollama_response(question: str, context: dict[str, Any], language: str) -> str | None:
    if os.getenv("OLLAMA_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        return None
    payload = {
        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Language: {language}\nWeather context: {context}\nQuestion: {question}"},
        ],
    }
    try:
        response = requests.post(
            f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434').rstrip('/')}/api/chat",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
        message = response.json().get("message", {}).get("content")
        return message.strip() if isinstance(message, str) and message.strip() else None
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return None


def answer_weather_question(
    question: str,
    weather: dict[str, Any],
    language: str = "English",
    alerts: list[dict[str, Any]] | None = None,
    advisory: dict[str, Any] | None = None,
    climate: dict[str, Any] | None = None,
    risk_analysis: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Answer from live/fallback weather data and return the source indicator."""
    context = build_weather_context(weather)
    if alerts:
        context["alerts"] = [
            {"title": alert.get("title"), "severity": alert.get("severity"), "message": alert.get("message")}
            for alert in alerts
        ]
    if advisory:
        context["agriculture_advisory"] = {
            "summary": advisory.get("summary"),
            "recommendations": advisory.get("recommendations", []),
        }
    if climate:
        context["climate_analysis"] = {
            "temperature_trend": climate.get("temperature_trend", {}).get("trend"),
            "wettest_month": climate.get("wettest_period", {}).get("label"),
        }
    if risk_analysis:
        context["weather_risk"] = {
            "overall_level": risk_analysis.get("overall_level"),
            "overall_score": risk_analysis.get("overall_score"),
            "risks": [
                {
                    "title": risk.get("title"),
                    "level": risk.get("level"),
                    "recommendation": risk.get("recommendation"),
                }
                for risk in risk_analysis.get("risks", [])
            ],
        }
    answer = _ollama_response(question, context, language)
    if answer is None:
        answer = _localized_fallback(question, context, language)
        source = "AI unavailable — using weather-data response."
    else:
        source = "Data source: Open-Meteo" if weather.get("is_live") else "Data source: Demo weather data"
    return answer, source


def get_demo_response(_question: str, location: str = "Patna, Bihar, India") -> str:
    """Backward-compatible response used by non-weather prototype surfaces."""
    _question = _question.strip()
    return f"I'm WeatherGPT, ready to answer weather questions for {location}."
