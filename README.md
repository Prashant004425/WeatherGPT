🌦️ WeatherGPT

AI-powered conversational weather intelligence for forecasting, alerts, risk analysis, agriculture advisory, and climate information.

WeatherGPT is a conversational weather platform designed to make complex meteorological information simple, understandable, and actionable. It combines live weather data with AI-powered natural-language interaction and deterministic weather intelligence to help users understand current conditions, risks, alerts, agricultural implications, and historical climate trends.

🎯 Problem Statement

Weather information is often presented as complex data that can be difficult for users to interpret and apply to real-life decisions.

WeatherGPT addresses this by providing:

Simple conversational access to weather information

Location-based real-time weather data

Smart weather alerts and risk analysis

Weather-based agriculture advisory

Historical climate insights

Multilingual and voice interaction

AI-generated explanations grounded in available weather data

🚀 Key Features

🌤️ Real-Time Weather

Get current weather information for a selected location using live meteorological data.

🤖 Conversational AI

Ask weather-related questions naturally and receive understandable responses using Llama 3.1.

🔔 Smart Weather Alerts

Identifies important weather conditions and presents relevant alerts to the user.

⚠️ Weather Risk Intelligence

Analyzes weather conditions using deterministic rules to identify potential risks such as extreme temperature, heavy precipitation, strong winds, and other weather-related conditions.

🌾 Agriculture Advisory

Provides general weather-based recommendations that can help users consider weather conditions when planning agricultural activities.

📊 Climate Analysis

Provides historical weather analysis, including temperature and rainfall trends, through interactive visualizations.

🌍 Multilingual Support

Designed to make weather information more accessible through multiple languages, including English and Hindi.

🎙️ Voice Interaction

Supports voice-oriented interaction to improve accessibility and ease of use.

📍 Location-Based Intelligence

Users can search for and select locations to receive relevant weather information and recommendations.

🧠 AI & Data Architecture

WeatherGPT separates weather data, deterministic intelligence, and conversational AI.

User
  ↓
Streamlit Frontend
  ↓
Python Application
  ↓
Open-Meteo API ──→ Live Weather Data
  ↓
Weather Processing
  ├── Risk Engine
  ├── Alert Engine
  ├── Agriculture Advisory
  └── Climate Analysis
  ↓
Llama 3.1 via Ollama
  ↓
Natural-Language Response
  ↓
User

Main Components

Component

Purpose

Streamlit

Web application and user interface

Python

Core application logic and service integration

Open-Meteo

Live meteorological data

Llama 3.1

Conversational language generation

Ollama

Local runtime for Llama 3.1

Risk Engine

Rule-based weather risk analysis

Alert Engine

Weather condition alerts

Plotly

Interactive charts and climate visualization

🛠️ Technology Stack

Language: Python

Frontend: Streamlit

AI Model: Llama 3.1

LLM Runtime: Ollama

Weather Data: Open-Meteo API

Visualization: Plotly

Architecture: Modular Python services

📁 Project Structure

WeatherGPT/
│
├── app.py
├── requirements.txt
├── .env.example
├── README.md
│
├── services/
│   ├── __init__.py
│   ├── weather_service.py
│   ├── ai_service.py
│   ├── alert_service.py
│   ├── advisory_service.py
│   ├── climate_service.py
│   └── risk_service.py
│
├── data/
│   └── sample_alerts.json
│
├── utils/
│   ├── __init__.py
│   └── helpers.py
│
└── assets/

The exact project structure may change as additional modules and features are developed.

⚙️ Installation

1. Clone the repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd WeatherGPT

2. Create a virtual environment

python -m venv .venv

3. Activate the virtual environment

Windows PowerShell:

.\.venv\Scripts\Activate.ps1

Windows CMD:

.venv\Scripts\activate

Linux/macOS:

source .venv/bin/activate

4. Install dependencies

pip install -r requirements.txt

5. Optional: Install Ollama

For local conversational AI, install Ollama and make sure the required Llama 3.1 model is available in your local Ollama environment.

Example:

ollama pull llama3.1

If Ollama is unavailable, the application can use its configured fallback behavior where supported.

6. Run the application

streamlit run app.py

The application will open in your browser.

💬 Example Questions

Users can ask questions such as:

"What is the weather today?"

"Will it rain today?"

"Is it safe to travel in this weather?"

"What weather risks should I be aware of?"

"Is this weather suitable for farming activities?"

"How has the temperature changed historically?"

"Explain today's weather in simple language."

🔐 Reliability Approach

WeatherGPT does not rely on the LLM alone for weather risk decisions.

Open-Meteo provides meteorological information.

Python services process the data.

Risk and Alert engines use deterministic rules for important weather conditions.

Llama 3.1 converts available information into natural-language conversational responses.

This separation helps make important weather intelligence more predictable and explainable.

⚠️ Current Limitations

This project is currently a prototype/MVP. Some production-level capabilities are planned for future development.

Examples include:

Integration with additional meteorological data sources

More advanced numerical weather prediction models

Official warning and emergency alert integrations

More detailed crop-specific agricultural intelligence

Production-scale database and user management

Large-scale cloud deployment and monitoring

More advanced GIS and mapping capabilities

WeatherGPT's agricultural recommendations are general weather-based guidance and should not replace professional agricultural or emergency advice.

🔮 Future Scope

Potential future improvements include:

Integration with GFS/WRF and additional forecasting systems

Real-time weather event and warning data pipelines

Advanced machine-learning forecasting and anomaly detection

GIS-based weather risk maps

Personalized notifications

More Indian regional languages

Improved speech-to-text and text-to-speech

Scalable cloud and Kubernetes deployment

Historical climate and long-term climate intelligence

Integration with official meteorological warning systems

🏆 Project Goal

The long-term goal of WeatherGPT is to transform raw meteorological information into clear, personalized, multilingual, and actionable weather intelligence for everyday users, agriculture, safety, and planning.

👨‍💻 Project

Developed as an AI for Weather Forecasting, Alerts, and Climate Information project.
