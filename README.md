# WeatherGPT

WeatherGPT is a Smart India Hackathon prototype for conversational weather forecasting, alerts and climate information. It provides a clear dashboard for a live presentation while keeping provider integrations behind small service modules.

## Current prototype features

- Streamlit dashboard for Patna (or a user-entered location)
- Clearly labelled demo weather, forecast, alert and agriculture advisory data
- Conversational WeatherGPT page with transparent mock responses
- Plotly climate analysis using Open-Meteo historical weather data
- Optional OpenWeather current-conditions lookup when `WEATHER_API_KEY` is configured
- Friendly fallback when APIs, keys or internet access are unavailable
- WeatherGPT text chat in English, Hindi, Bengali, Marathi, Tamil and Telugu
- Optional microphone input through Streamlit audio capture and SpeechRecognition
- Optional browser text-to-speech with the per-message “Listen” control

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`SpeechRecognition` is used only for optional microphone transcription. Text
chat remains fully usable when microphone permissions, recognition, or network
services are unavailable. Browser speech synthesis provides optional read-aloud
without another Python audio dependency.

## Run

```bash
streamlit run app.py
```

The application works without an API key. Current weather and forecasts use Open-Meteo, while Climate Analysis uses the Open-Meteo Archive API for the selected location's approximately previous 12 months. If a historical request fails, the climate page clearly reports that the data is unavailable rather than presenting invented observations. Weather alerts and agriculture guidance remain informational and should not replace official warnings.

## Planned future integrations

- Real-time meteorological APIs and official warning systems
- GFS/WRF forecasting workflows
- Expanded multilingual LLM and voice integrations
- PostgreSQL persistence
- Docker/Kubernetes deployment
- MQTT/WIS2.0 data ingestion

The service layer is intentionally small so these integrations can be added without placing business logic in `app.py`.
