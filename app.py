from datetime import date, timedelta
import hashlib

import streamlit as st
import plotly.graph_objects as go
import requests

from services.advisory_service import generate_agriculture_advisory
from services.ai_service import answer_weather_question
from services.alert_service import generate_weather_alerts
from services.risk_service import analyze_weather_risk, get_risk_summary
from services.weather_service import get_weather, search_locations
from services.climate_service import (
    analyze_rainfall_trend,
    analyze_temperature_trend,
    generate_climate_summary,
    get_historical_weather,
)
from services.language_service import SUPPORTED_LANGUAGES, language_locale
from services.voice_service import browser_speech_script, transcribe_audio

st.set_page_config(
    page_title="WeatherGPT | Weather Intelligence",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root {
        --bg-primary:#f5f9fc;
        --bg-secondary:#eaf5ff;
        --bg-card:#ffffff;
        --text-primary:#0b1f33;
        --text-secondary:#29445b;
        --text-muted:#536b7f;
        --border:#c7d9e6;
        --accent:#075dcc;
        --accent-soft:#dcecff;
        --success:#087a5a;
        --warning:#9a5b00;
        --danger:#b4232d;
        --info:#075dcc;
        --shadow:rgba(24,67,100,.12);
        color-scheme:light;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary:#101820;
            --bg-secondary:#172936;
            --bg-card:#1b2a38;
            --text-primary:#f2f7fb;
            --text-secondary:#d5e3ed;
            --text-muted:#b4c5d1;
            --border:#3c5668;
            --accent:#72b7ff;
            --accent-soft:#203e5b;
            --success:#65d5b0;
            --warning:#ffd166;
            --danger:#ff8f98;
            --info:#72b7ff;
            --shadow:rgba(0,0,0,.35);
            color-scheme:dark;
        }
    }
    html[data-theme="dark"],
    body[data-theme="dark"],
    [data-theme="dark"] {
        --bg-primary:#101820; --bg-secondary:#172936; --bg-card:#1b2a38;
        --text-primary:#f2f7fb; --text-secondary:#d5e3ed; --text-muted:#b4c5d1;
        --border:#3c5668; --accent:#72b7ff; --accent-soft:#203e5b;
        --success:#65d5b0; --warning:#ffd166; --danger:#ff8f98; --info:#72b7ff;
        --shadow:rgba(0,0,0,.35); color-scheme:dark;
    }
    * { font-family: 'DM Sans', sans-serif; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp { background:var(--bg-primary); color:var(--text-primary); }
    h1,h2,h3,h4,h5,h6,p,li,label,legend { color:var(--text-primary); }
    h1,h2,h3,h4,h5,h6 { font-family: 'Space Grotesk', sans-serif; }
    [data-testid="stSidebar"] { background:var(--bg-secondary); border-right:1px solid var(--border); }
    [data-testid="stSidebar"] * { color:var(--text-primary); }
    [data-testid="stSidebar"] .stRadio label { padding:.35rem .25rem; border-radius:8px; }
    [data-testid="stSidebar"] .stRadio label:hover,
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background:var(--accent-soft); }
    .brand { padding: 10px 0 24px; }
    .brand-mark { display:inline-flex; align-items:center; justify-content:center; width:42px; height:42px; border-radius:13px; background:var(--accent); font-size:24px; margin-right:10px; }
    .brand-title { font-family:'Space Grotesk'; font-size:23px; font-weight:700; vertical-align:middle; color:var(--text-primary); }
    .eyebrow { color:var(--accent); font-size:12px; text-transform:uppercase; letter-spacing:1.4px; font-weight:700; }
    .subtle, small, .stCaption { color:var(--text-muted); font-size:14px; }
    .hero { background:var(--bg-secondary); border:1px solid var(--border); border-radius:18px; padding:24px 28px; margin-bottom:18px; }
    .hero h1 { margin:5px 0 4px; font-size:34px; }
    .hero p { margin:0; color:var(--text-secondary); font-size:16px; }
    .card { background:var(--bg-card); color:var(--text-primary); border:1px solid var(--border); border-radius:16px; padding:20px; box-shadow:0 5px 18px var(--shadow); height:100%; }
    .card b, .card strong, .card p { color:var(--text-primary); }
    .metric-label { color:var(--text-secondary); font-size:13px; margin-bottom:4px; }
    .metric-value { color:var(--text-primary); font-size:22px; font-weight:700; }
    .temp { font-size:54px; line-height:1; font-weight:700; color:var(--text-primary); }
    .condition { font-size:18px; color:var(--text-secondary); margin-top:8px; }
    .demo { display:inline-block; color:var(--warning); background:var(--accent-soft); border:1px solid var(--border); border-radius:999px; padding:3px 9px; font-size:11px; font-weight:700; letter-spacing:.5px; }
    .section-title { margin:22px 0 10px; }
    .forecast-day { color:var(--text-secondary); font-size:13px; font-weight:600; }
    .forecast-icon { font-size:30px; margin:8px 0; }
    .forecast-temp { font-size:20px; font-weight:700; color:var(--text-primary); }
    .alert-card { border-left:5px solid var(--warning); background:var(--bg-card); color:var(--text-primary); border-radius:12px; padding:15px 18px; border-top:1px solid var(--border); border-right:1px solid var(--border); border-bottom:1px solid var(--border); margin-bottom:10px; }
    .alert-card.high { border-left-color:var(--danger); }
    .alert-card.medium { border-left-color:var(--warning); }
    .chat-user { background:var(--accent); color:#fff; padding:11px 15px; border-radius:15px 15px 3px 15px; margin:10px 0 8px 18%; }
    .chat-bot { background:var(--bg-card); border:1px solid var(--border); padding:11px 15px; border-radius:15px 15px 15px 3px; margin:0 18% 12px 0; color:var(--text-primary); }
    .stButton > button { border-radius:10px; font-weight:600; color:var(--text-primary); background:var(--bg-card); border:1px solid var(--border); }
    .stButton > button:hover { color:var(--text-primary); border-color:var(--accent); background:var(--accent-soft); }
    input, textarea, [data-baseweb="select"] > div, [data-testid="stChatInput"] > div { color:var(--text-primary) !important; background:var(--bg-card) !important; border-color:var(--border) !important; }
    input::placeholder, textarea::placeholder { color:var(--text-muted) !important; opacity:1; }
    [data-baseweb="popover"], [role="listbox"], [data-baseweb="menu"] { background:var(--bg-card); color:var(--text-primary); }
    [role="option"], [data-baseweb="menu"] * { color:var(--text-primary) !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stCaptionContainer"] { color:var(--text-primary); }
    [data-testid="stCaptionContainer"] { color:var(--text-muted); }
    [data-testid="stAlert"] p, [data-testid="stAlert"] span { color:var(--text-primary); }
    [data-testid="stExpander"] { background:var(--bg-card); border-color:var(--border); }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color:var(--text-primary) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def card_metric(label: str, value: str) -> None:
    st.markdown(f'<div class="metric-label">{label}</div><div class="metric-value">{value}</div>', unsafe_allow_html=True)


def _plotly_theme() -> dict[str, str]:
    """Use readable chart colors for the active Streamlit theme."""
    theme_type = getattr(st.context.theme, "type", None)
    if theme_type == "dark":
        return {
            "paper": "#101820",
            "plot": "#1b2a38",
            "text": "#f2f7fb",
            "grid": "#3c5668",
            "temperature": "#72b7ff",
            "precipitation": "#66c7e8",
        }
    return {
        "paper": "#f5f9fc",
        "plot": "#ffffff",
        "text": "#0b1f33",
        "grid": "#c7d9e6",
        "temperature": "#075dcc",
        "precipitation": "#1677a5",
    }


def _location_label(location: dict) -> str:
    admin1 = location.get("admin1", "")
    if location.get("name", "").lower() == "delhi" and "national capital territory" in admin1.lower():
        admin1 = ""
    return ", ".join(part for part in (location["name"], admin1, location.get("country")) if part)


def _set_selected_location(location: dict) -> None:
    st.session_state.selected_location = location
    st.session_state.location_query = _location_label(location)
    st.session_state.location_changed = True
    st.session_state.chat_input_version = st.session_state.get("chat_input_version", 0) + 1


def navigate_to(page: str) -> None:
    """Update navigation before the next rerun renders the radio widget."""
    st.session_state.navigation = page


def render_sidebar() -> tuple[str, dict, str]:
    if "selected_location" not in st.session_state:
        with st.spinner("🔎 Finding locations..."):
            default_matches = search_locations("Patna, Bihar, India")
        default = next(
            (item for item in default_matches if item["name"].lower() == "patna"),
            default_matches[0] if default_matches else {
                "name": "Patna", "admin1": "Bihar", "country": "India",
                "country_code": "IN", "latitude": 25.5941, "longitude": 85.1376,
            },
        )
        _set_selected_location(default)
    with st.sidebar:
        st.markdown('<div class="brand"><span class="brand-mark">🌦️</span><span class="brand-title">WeatherGPT</span></div>', unsafe_allow_html=True)
        st.caption("Conversational weather intelligence")
        st.markdown("**📍 Location**")
        query = st.text_input(
            "Search city, state or country...",
            value=st.session_state.location_query,
            placeholder="Search city, state or country...",
            label_visibility="collapsed",
        )
        st.session_state.location_query = query
        if query != st.session_state.get("last_location_query"):
            st.session_state.last_location_query = query
            if query.strip():
                with st.spinner("🔎 Finding locations..."):
                    try:
                        st.session_state.location_suggestions = search_locations(query)
                        st.session_state.location_search_error = not st.session_state.location_suggestions
                    except (requests.RequestException, ValueError, KeyError, TypeError):
                        st.session_state.location_suggestions = []
                        st.session_state.location_search_error = True
            else:
                st.session_state.location_suggestions = []
                st.session_state.location_search_error = False
        suggestions = st.session_state.get("location_suggestions", [])
        if st.session_state.get("location_search_error"):
            st.caption("📍 We couldn't find that location.")
            st.caption("Try searching with a city and state, for example: Ranchi, Jharkhand")
        elif suggestions:
            st.caption("Select a matching location:")
            for index, suggestion in enumerate(suggestions):
                if st.button(
                    f"📍 {_location_label(suggestion)}",
                    key=f"location_suggestion_{index}",
                    use_container_width=True,
                ):
                    _set_selected_location(suggestion)
                    st.session_state.location_suggestions = []
                    st.session_state.last_location_query = st.session_state.location_query
                    st.rerun()
        st.caption(f"📍 {_location_label(st.session_state.selected_location)}")
        st.markdown("**Popular locations**")
        popular_columns = st.columns(5)
        for column, popular in zip(popular_columns, ["Patna", "Ranchi", "Delhi", "Mumbai", "Kolkata"]):
            with column:
                if st.button(popular, key=f"popular_{popular}", use_container_width=True):
                    with st.spinner("🔎 Finding locations..."):
                        try:
                            matches = search_locations(popular)
                        except (requests.RequestException, ValueError, KeyError, TypeError):
                            matches = []
                    if matches:
                        _set_selected_location(matches[0])
                        st.session_state.location_suggestions = matches
                        st.session_state.last_location_query = st.session_state.location_query
                        st.rerun()
                    else:
                        st.warning("📍 We couldn't find that location.")
        page = st.radio(
            "Navigate",
            ["🏠 Dashboard", "💬 WeatherGPT", "🚨 Alerts", "🌾 Agriculture Advisory", "📊 Climate Analysis"],
            key="navigation",
            label_visibility="collapsed",
        )
        language = st.selectbox("Language", SUPPORTED_LANGUAGES)
        st.divider()
        st.markdown("### About WeatherGPT")
        st.caption("An SIH prototype for clear, conversational access to weather forecasts, alerts and climate information.")
        st.caption("Prototype status: DEMO MODE")
    return page, st.session_state.selected_location, language


def render_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><div class="eyebrow">WeatherGPT • SIH Prototype</div><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


@st.cache_data(ttl=600, show_spinner=False)
def get_cached_weather_for_coordinates(location: str, latitude: float, longitude: float) -> dict:
    return get_weather(location, latitude, longitude)


def render_dashboard(selected_location: dict) -> None:
    location = _location_label(selected_location)
    with st.spinner("🌤️ Fetching live weather..."):
        weather = get_cached_weather_for_coordinates(
            location,
            selected_location["latitude"],
            selected_location["longitude"],
        )
    alerts = generate_weather_alerts(weather)
    risk_analysis = analyze_weather_risk(weather)
    render_header("WeatherGPT", "Conversational AI for Weather Intelligence")
    status = "LIVE WEATHER" if weather["is_live"] else "DEMO / SAMPLE DATA"
    if not weather["is_live"]:
        status = "LIVE WEATHER UNAVAILABLE"
    st.markdown(f'<span class="demo">{status}</span> &nbsp; 📍 {weather["location"]}', unsafe_allow_html=True)
    if not weather["is_live"]:
        st.warning("Live weather data is temporarily unavailable. Showing demo data.", icon="⚠️")
    st.markdown('<div class="section-title"><h3>Current conditions</h3></div>', unsafe_allow_html=True)
    left, right = st.columns([1.35, 2])
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="eyebrow">Now • {weather["updated"]}</div><div class="temp">{weather["temperature"]}°C</div><div class="condition">{weather["icon"]} {weather["condition"]}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        a, b = st.columns(2)
        with a:
            card_metric("Feels like", f'{weather["feels_like"]}°C')
            card_metric("Humidity", f'{weather["humidity"]}%')
        with b:
            card_metric("Wind speed", f'{weather["wind_speed"]} km/h')
            card_metric("Rain probability", f'{weather["rain_probability"]}%')
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card"><div class="eyebrow">Today\'s summary</div><h3>Weather overview for your location</h3><p class="subtle">Use this live snapshot as a quick overview. Check official advisories before making safety or farming decisions.</p>', unsafe_allow_html=True)
        st.info("Forecast values are provided by Open-Meteo.", icon="ℹ️")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title"><h3>🚨 Important Weather Alerts</h3></div>', unsafe_allow_html=True)
    if alerts:
        for alert in alerts[:1]:
            render_alert(alert)
    else:
        st.success("✅ No significant weather alerts", icon="✅")
    st.markdown('<div class="section-title"><h3>⚠️ Weather Risk Intelligence</h3></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card"><b>Current Weather Risk: {risk_analysis["overall_level"]}</b><br>'
        f'Risk score: {risk_analysis["overall_score"]}/100 · {len(risk_analysis["risks"])} risk(s) detected</div>',
        unsafe_allow_html=True,
    )
    st.button(
        "View Weather Risks →",
        key="dashboard_risks",
        on_click=navigate_to,
        args=("🚨 Alerts",),
    )
    st.markdown('<div class="section-title"><h3>🌦️ Forecast</h3></div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for col, item in zip(cols, weather["forecast"]):
        with col:
            st.markdown(f'<div class="card"><div class="forecast-day">{item["day"]}</div><div class="forecast-icon">{item["icon"]}</div><div class="forecast-temp">{item["high"]}° / {item["low"]}°</div><div class="subtle">{item["condition"]}</div><br><div class="subtle">💧 {item["rain"]}% rain</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><h3>🤖 Ask WeatherGPT</h3></div>', unsafe_allow_html=True)
    question = st.text_input("Ask a quick weather question", placeholder="Will it rain tomorrow?  •  Is it safe to travel today?", label_visibility="collapsed")
    if question:
        answer, source = answer_weather_question(
            question,
            weather,
            st.session_state.get("language", "English"),
            alerts=alerts,
            risk_analysis=risk_analysis,
        )
        st.success(answer, icon="🤖")
        st.caption(source)
    st.markdown('<div class="section-title"><h3>🌾 Agriculture Advisory</h3></div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><b>Rain is possible.</b> Consider checking soil moisture before irrigation and protect harvested crops.<br><span class="subtle">Demo advisory preview — not professional agricultural advice.</span></div>', unsafe_allow_html=True)
    st.button(
        "View Agriculture Advisory →",
        key="dashboard_advisory",
        on_click=navigate_to,
        args=("🌾 Agriculture Advisory",),
    )
    st.markdown('<div class="section-title"><h3>📊 Climate & Historical Analysis</h3></div>', unsafe_allow_html=True)
    climate_preview = generate_climate_summary(
        get_cached_climate(*_climate_coordinates(selected_location))
    )
    st.markdown(
        f'<div class="card"><b>Temperature trend:</b> {climate_preview.get("temperature_trend", {}).get("trend", "Unavailable")} &nbsp;•&nbsp; <b>Precipitation pattern:</b> {climate_preview.get("rainfall_trend", {}).get("trend", "Unavailable")}<br><span class="subtle">{climate_preview.get("source", "Historical data")} for {location}</span></div>',
        unsafe_allow_html=True,
    )
    st.button(
        "View Climate Analysis →",
        key="dashboard_climate",
        on_click=navigate_to,
        args=("📊 Climate Analysis",),
    )


def render_alert(alert: dict) -> None:
    severity_class = "high" if alert["severity"].lower() in {"high", "critical"} else "medium"
    st.markdown(
        f'<div class="alert-card {severity_class}"><span class="demo">{"DEMO ALERT" if alert.get("is_demo") else "WEATHER DATA ALERT"}</span> <b>{alert["icon"]} {alert["alert_type"]}</b> &nbsp; <b>{alert["severity"]}</b><br><span class="subtle">📍 {alert["location"]} &nbsp; • &nbsp; {alert.get("timestamp", "")}</span><br><b>Expected:</b> {alert["condition"]}<br><b>Recommended:</b> {alert["action"]}<br><span class="subtle">Source: {alert.get("source", "Weather data")}</span></div>',
        unsafe_allow_html=True,
    )


def render_chat(selected_location: dict, language: str) -> None:
    location = _location_label(selected_location)
    location_key = (
        selected_location["name"],
        selected_location.get("admin1", ""),
        selected_location.get("country", ""),
        selected_location["latitude"],
        selected_location["longitude"],
    )
    previous_location_key = st.session_state.get("previous_chat_location")
    if previous_location_key is not None and previous_location_key != location_key:
        # The versioned widget discards only pending input; conversation history persists.
        st.session_state.pending_chat_prompt = None
        st.session_state.chat_input_version = st.session_state.get("chat_input_version", 0) + 1
        st.session_state.location_changed = True
    st.session_state.previous_chat_location = location_key
    render_header("Talk to WeatherGPT", "Ask questions in natural language and get clear, explainable guidance.")
    st.markdown("**Try asking:**")
    examples = ["🌧️ Will it rain tomorrow?", "🌡️ What's the temperature today?", "⛈️ Are thunderstorms expected?", "🌾 Is the weather suitable for farming?", "☀️ Is today good for outdoor activities?"]
    selected = st.columns(4)
    for col, example in zip(selected, examples[:4]):
        with col:
            if st.button(example, use_container_width=True):
                st.session_state.pending_chat_prompt = example
    st.markdown("### Voice and text")
    st.caption("Type a question below, or optionally record a short voice question.")
    audio = st.audio_input(
        "🎤 Speak",
        sample_rate=16000,
        key=f"weather_voice_input_{st.session_state.get('chat_input_version', 0)}",
    )
    if audio is not None:
        audio_bytes = audio.getvalue()
        audio_id = hashlib.sha256(audio_bytes).hexdigest()
        if audio_id != st.session_state.get("processed_audio_id"):
            st.session_state.processed_audio_id = audio_id
            voice_text, voice_error = transcribe_audio(audio, language_locale(language))
            if voice_text:
                st.session_state.pending_chat_prompt = voice_text
            elif voice_error:
                st.warning(voice_error)
    if st.session_state.get("pending_chat_prompt"):
        st.info(f"Voice transcript: {st.session_state['pending_chat_prompt']}")
    if "messages" not in st.session_state:
        st.session_state.messages = [("assistant", f"Hello! I'm WeatherGPT. Ask me about the weather in {location}.")]
    weather = get_cached_weather_for_coordinates(location, selected_location["latitude"], selected_location["longitude"])
    alerts = generate_weather_alerts(weather)
    risk_analysis = analyze_weather_risk(weather)
    advisory = generate_agriculture_advisory(weather, risk_analysis)
    climate = generate_climate_summary(
        get_cached_climate(*_climate_coordinates(selected_location))
    )
    for message_index, (role, message) in enumerate(st.session_state.messages):
        with st.chat_message("user" if role == "user" else "assistant"):
            st.markdown(message)
            if role == "assistant" and message != st.session_state.messages[0][1]:
                st.caption(st.session_state.get("last_ai_source", "Data source: Open-Meteo"))
                if st.button("🔊 Listen", key=f"listen_{message_index}"):
                    st.html(
                        browser_speech_script(message, language_locale(language)),
                        unsafe_allow_javascript=True,
                    )
    prompt = st.chat_input(
        "Ask WeatherGPT a question...",
        key=f"weather_chat_input_{st.session_state.get('chat_input_version', 0)}",
    )
    prompt = prompt or st.session_state.pop("pending_chat_prompt", None)
    if prompt:
        st.session_state.messages.append(("user", prompt))
        answer, source = answer_weather_question(prompt, weather, language, alerts, advisory, climate, risk_analysis)
        st.session_state.last_ai_source = source
        st.session_state.messages.append(("assistant", answer))
        st.rerun()


def render_alerts(location: str) -> None:
    render_header("Weather alerts", "Stay informed with clear, location-aware warning summaries.")
    selected_location = st.session_state.selected_location
    weather = get_cached_weather_for_coordinates(
        location,
        selected_location["latitude"],
        selected_location["longitude"],
    )
    alerts = generate_weather_alerts(weather)
    risk_analysis = analyze_weather_risk(weather)
    st.markdown('<div class="section-title"><h3>⚠️ Weather Risk Intelligence</h3></div>', unsafe_allow_html=True)
    st.markdown(
        f"**Overall Risk:** {risk_analysis['overall_level']}  \n"
        f"**Risk Score:** {risk_analysis['overall_score']}/100  \n"
        f"{get_risk_summary(risk_analysis, st.session_state.get('language', 'English'))}"
    )
    for risk in risk_analysis["risks"]:
        st.markdown(
            f'<div class="card"><b>{risk["title"]} — {risk["level"]}</b><br>'
            f'{risk["description"]}<br><b>Recommended action:</b> {risk["recommendation"]}'
            f'<br><span class="subtle">Source: {risk["source"]}</span></div>',
            unsafe_allow_html=True,
        )
    st.caption("WeatherGPT alerts are informational and should not replace official warnings from local meteorological or disaster management authorities.")
    if not alerts:
        st.success("✅ No significant weather alerts", icon="✅")
        st.caption(f"Current conditions and available forecast do not indicate a major weather risk. Source: {'Open-Meteo forecast' if weather['is_live'] else 'Demo weather data'}")
    for alert in alerts:
        render_alert(alert)


def render_advisory(location: str) -> None:
    render_header("Agriculture advisory", "Simple, explainable guidance for weather-sensitive farm decisions.")
    selected_location = st.session_state.selected_location
    weather = get_cached_weather_for_coordinates(
        location,
        selected_location["latitude"],
        selected_location["longitude"],
    )
    risk_analysis = analyze_weather_risk(weather)
    advisory = generate_agriculture_advisory(weather, risk_analysis)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<span class="demo">{"DEMO AGRICULTURE ADVISORY" if advisory["is_demo"] else "WEATHER-BASED ADVISORY"}</span>', unsafe_allow_html=True)
    st.markdown(f"### 📍 {advisory['location']}")
    st.markdown(f"**{advisory['summary']}**")
    for item in advisory["recommendations"]:
        st.markdown(f"**{item['category']}**  \n{item['advice']}")
    if not advisory["recommendations"]:
        st.info("No significant agricultural weather risk is indicated in the available forecast.")
    st.caption(f"Source: {advisory['source']}")
    st.markdown("</div>", unsafe_allow_html=True)
    st.info("WeatherGPT provides weather-based guidance only. Follow local agricultural and government advisories for crop-specific decisions.", icon="⚠️")
    st.markdown("### 📅 5-Day Farm Planning")
    for item in advisory["forecast"]:
        st.markdown(
            f'<div class="card"><b>{item["day"]}</b> &nbsp; 🌧️ Rain: {item.get("rain", "—")}% &nbsp; 🌡️ Temperature: {item.get("low", "—")}–{item.get("high", "—")}°C<br><span class="subtle">{item.get("condition", "Forecast unavailable")}</span></div>',
            unsafe_allow_html=True,
        )


def _climate_coordinates(selected_location: dict) -> tuple[float, float, str, str]:
    end = date.today() - timedelta(days=5)
    start = end - timedelta(days=364)
    return selected_location["latitude"], selected_location["longitude"], start.isoformat(), end.isoformat()


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_climate(latitude: float, longitude: float, start_date: str, end_date: str) -> dict:
    return get_historical_weather(latitude, longitude, start_date, end_date)


def render_climate(language: str) -> None:
    selected_location = st.session_state.selected_location
    location = _location_label(selected_location)
    historical = get_cached_climate(*_climate_coordinates(selected_location))
    summary = generate_climate_summary(historical)
    hindi = language == "हिंदी"
    render_header(
        "जलवायु विश्लेषण" if hindi else "Climate analysis",
        "चयनित स्थान के ऐतिहासिक मौसम रुझान देखें।"
        if hindi
        else "Explore historical weather trends for the selected location.",
    )
    status = "DEMO DATA" if summary.get("is_demo") else summary.get("source", "Historical data")
    st.markdown(f'<span class="demo">{status}</span> &nbsp; 📍 {location}', unsafe_allow_html=True)
    if not summary["available"]:
        st.warning(
            "ऐतिहासिक जलवायु डेटा अभी उपलब्ध नहीं है। कृपया बाद में प्रयास करें।"
            if hindi
            else summary["message"],
            icon="⚠️",
        )
        return
    st.markdown(
        f"**अवधि:** {summary['period']} &nbsp; • &nbsp; **स्रोत:** {summary['source']}"
        if hindi
        else f"**Period analyzed:** {summary['period']} &nbsp; • &nbsp; **Data Source:** {summary['source']}"
    )
    cards = st.columns(4)
    metrics = [
        ("📈 औसत तापमान" if hindi else "📈 Average Temperature", f"{summary['average_temperature']}°C"),
        ("🌡️ न्यूनतम तापमान" if hindi else "🌡️ Minimum Temperature", f"{summary['minimum_temperature']}°C"),
        ("🌡️ अधिकतम तापमान" if hindi else "🌡️ Maximum Temperature", f"{summary['maximum_temperature']}°C"),
        ("🌧️ कुल वर्षण" if hindi else "🌧️ Total Precipitation", f"{summary['total_precipitation']} mm"),
    ]
    for column, (label, value) in zip(cards, metrics):
        with column:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            card_metric(label, value)
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title"><h3>📈 तापमान रुझान</h3></div>'
        if hindi
        else '<div class="section-title"><h3>📈 Temperature Trend</h3></div>',
        unsafe_allow_html=True,
    )
    temperature = analyze_temperature_trend(historical["records"])
    chart_theme = _plotly_theme()
    figure = go.Figure(go.Scatter(
        x=[item["label"] for item in temperature["monthly"]],
        y=[item["average"] for item in temperature["monthly"]],
        mode="lines+markers", line=dict(color=chart_theme["temperature"], width=3), marker=dict(size=8),
    ))
    figure.update_layout(
        title="Monthly average temperature" if not hindi else "मासिक औसत तापमान",
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Month" if not hindi else "महीना",
        yaxis_title="Average temperature (°C)" if not hindi else "औसत तापमान (°C)",
        paper_bgcolor=chart_theme["paper"],
        plot_bgcolor=chart_theme["plot"],
        font=dict(color=chart_theme["text"]),
        xaxis=dict(gridcolor=chart_theme["grid"], linecolor=chart_theme["grid"]),
        yaxis=dict(gridcolor=chart_theme["grid"], linecolor=chart_theme["grid"]),
    )
    st.plotly_chart(figure, use_container_width=True)
    st.caption(f"रुझान: {temperature['trend']}" if hindi else f"Temperature trend: {temperature['trend']}")
    st.markdown(
        '<div class="section-title"><h3>🌧️ वर्षा / वर्षण</h3></div>'
        if hindi
        else '<div class="section-title"><h3>🌧️ Rainfall / Precipitation</h3></div>',
        unsafe_allow_html=True,
    )
    rainfall = analyze_rainfall_trend(historical["records"])
    rain_figure = go.Figure(go.Bar(
        x=[item["label"] for item in rainfall["monthly"]],
        y=[item["precipitation"] for item in rainfall["monthly"]],
        marker_color=chart_theme["precipitation"],
    ))
    rain_figure.update_layout(
        title="Monthly precipitation" if not hindi else "मासिक वर्षण",
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Month" if not hindi else "महीना",
        yaxis_title="Precipitation (mm)" if not hindi else "वर्षण (mm)",
        paper_bgcolor=chart_theme["paper"],
        plot_bgcolor=chart_theme["plot"],
        font=dict(color=chart_theme["text"]),
        xaxis=dict(gridcolor=chart_theme["grid"], linecolor=chart_theme["grid"]),
        yaxis=dict(gridcolor=chart_theme["grid"], linecolor=chart_theme["grid"]),
    )
    st.plotly_chart(rain_figure, use_container_width=True)
    st.caption(f"रुझान: {rainfall['trend']}" if hindi else f"Precipitation trend: {rainfall['trend']}")
    st.markdown(
        '<div class="section-title"><h3>🔎 जलवायु जानकारी</h3></div>'
        if hindi
        else '<div class="section-title"><h3>🔎 Climate Insights</h3></div>',
        unsafe_allow_html=True,
    )
    insights = summary["insights"]
    if hindi:
        insights = [
            f"औसत तापमान {summary['average_temperature']}°C था।",
            f"सबसे गर्म महीना {summary['warmest_month']['label']} था।",
            f"सबसे ठंडा महीना {summary['coolest_month']['label']} था।",
            f"सबसे अधिक वर्षण {summary['wettest_period']['label']} में हुआ।",
            f"चयनित अवधि में तापमान का रुझान {summary['temperature_trend']['trend'].lower()} रहा।",
        ]
    for insight in insights:
        st.markdown(f"- {insight}")
    st.caption(f"Data Source: {summary['source']}")


page, selected_location, language = render_sidebar()
st.session_state.language = language
location = _location_label(selected_location)
if page.startswith("🏠"):
    render_dashboard(selected_location)
elif page.startswith("💬"):
    render_chat(selected_location, language)
elif page.startswith("🚨"):
    render_alerts(location)
elif page.startswith("🌾"):
    render_advisory(location)
else:
    render_climate(language)
