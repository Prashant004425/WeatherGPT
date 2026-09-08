"""Historical weather retrieval and transparent climate analysis helpers."""

from datetime import date, timedelta
from typing import Any

import requests

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
SOURCE_NAME = "Open-Meteo Historical Weather Data"
MONTH_NAMES = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _default_period() -> tuple[str, str]:
    end = date.today() - timedelta(days=5)
    start = end - timedelta(days=364)
    return start.isoformat(), end.isoformat()


def _period_value(value: str | date | None, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, date):
        return value.isoformat()
    parsed = date.fromisoformat(value)
    return parsed.isoformat()


def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
) -> dict[str, Any]:
    """Retrieve daily historical weather for the selected coordinates."""
    default_start, default_end = _default_period()
    result: dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "",
        "end_date": "",
        "records": [],
        "is_demo": False,
        "source": SOURCE_NAME,
        "error": "",
    }
    try:
        start = _period_value(start_date, default_start)
        end = _period_value(end_date, default_end)
        if date.fromisoformat(start) > date.fromisoformat(end):
            raise ValueError("start_date must not be after end_date")
        result["start_date"] = start
        result["end_date"] = end
        response = requests.get(
            ARCHIVE_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start,
                "end_date": end,
                "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
            },
            timeout=15,
        )
        response.raise_for_status()
        daily = response.json()["daily"]
        dates = daily["time"]
        means = daily["temperature_2m_mean"]
        maximums = daily["temperature_2m_max"]
        minimums = daily["temperature_2m_min"]
        precipitation = daily["precipitation_sum"]
        series = (dates, means, maximums, minimums, precipitation)
        if not all(isinstance(values, list) for values in series):
            raise ValueError("Historical response contains invalid daily series")
        if len({len(values) for values in series}) != 1:
            raise ValueError("Historical response contains incomplete daily series")
        records: list[dict[str, Any]] = []
        for values in zip(dates, means, maximums, minimums, precipitation):
            record_date = date.fromisoformat(values[0])
            if any(value is None for value in values[1:]):
                continue
            records.append(
                {
                    "date": values[0],
                    "year": record_date.year,
                    "month": record_date.month,
                    "month_name": MONTH_NAMES[record_date.month],
                    "temperature_avg": float(values[1]),
                    "temperature_max": float(values[2]),
                    "temperature_min": float(values[3]),
                    "precipitation": float(values[4]),
                }
            )
        result["records"] = records
        if not records:
            result["error"] = "Historical climate data is temporarily unavailable. Please try again later."
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError) as error:
        result["error"] = f"Historical climate data is temporarily unavailable. Please try again later. ({error})"
    return result


def _trend(values: list[float]) -> str:
    """Compare the first and second halves of a series without climate claims."""
    if len(values) < 4:
        return "Relatively stable"
    midpoint = len(values) // 2
    first = sum(values[:midpoint]) / midpoint
    second = sum(values[midpoint:]) / (len(values) - midpoint)
    difference = second - first
    threshold = max(0.5, abs(first) * 0.05)
    if abs(difference) <= threshold:
        return "Relatively stable"
    return "Increasing" if difference > 0 else "Decreasing"


def analyze_temperature_trend(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return monthly average temperature values and a simple transparent trend."""
    monthly: dict[tuple[int, int], list[float]] = {}
    for record in records:
        value = record.get("temperature_avg")
        if isinstance(value, (int, float)):
            key = (int(record["year"]), int(record["month"]))
            monthly.setdefault(key, []).append(float(value))
    values = [
        {
            "year": year,
            "month": month,
            "month_name": MONTH_NAMES[month],
            "label": f"{MONTH_NAMES[month]} {year}",
            "average": round(sum(items) / len(items), 1),
        }
        for (year, month), items in sorted(monthly.items())
    ]
    return {"monthly": values, "yearly": values, "trend": _trend([item["average"] for item in values])}


def analyze_rainfall_trend(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return monthly precipitation totals and a simple trend."""
    monthly: dict[tuple[int, int], float] = {}
    for record in records:
        value = record.get("precipitation", record.get("rainfall"))
        if isinstance(value, (int, float)):
            key = (int(record["year"]), int(record["month"]))
            monthly[key] = monthly.get(key, 0.0) + float(value)
    values = [
        {
            "year": year,
            "month": month,
            "month_name": MONTH_NAMES[month],
            "label": f"{MONTH_NAMES[month]} {year}",
            "precipitation": round(total, 1),
            "rainfall": round(total, 1),
        }
        for (year, month), total in sorted(monthly.items())
    ]
    return {"monthly": values, "trend": _trend([item["precipitation"] for item in values])}


def generate_climate_summary(historical: dict[str, Any]) -> dict[str, Any]:
    """Calculate factual summary metrics and rule-based insights."""
    records = historical.get("records", [])
    if not records:
        return {
            "available": False,
            "message": historical.get(
                "error",
                "Historical climate data is temporarily unavailable. Please try again later.",
            ),
            "source": historical.get("source", SOURCE_NAME),
            "is_demo": bool(historical.get("is_demo", False)),
        }

    temperatures = [record["temperature_avg"] for record in records]
    minimums = [record["temperature_min"] for record in records]
    maximums = [record["temperature_max"] for record in records]
    precipitation_values = [record["precipitation"] for record in records]
    temperature = analyze_temperature_trend(records)
    rainfall = analyze_rainfall_trend(records)
    wettest = max(rainfall["monthly"], key=lambda item: item["precipitation"])
    driest = min(rainfall["monthly"], key=lambda item: item["precipitation"])
    warmest = max(temperature["monthly"], key=lambda item: item["average"])
    coolest = min(temperature["monthly"], key=lambda item: item["average"])
    return {
        "available": True,
        "period": f"{records[0]['date']} to {records[-1]['date']}",
        "average_temperature": round(sum(temperatures) / len(temperatures), 1),
        "minimum_temperature": round(min(minimums), 1),
        "maximum_temperature": round(max(maximums), 1),
        "total_precipitation": round(sum(precipitation_values), 1),
        "average_precipitation": round(sum(precipitation_values) / len(precipitation_values), 1),
        "temperature_trend": temperature,
        "rainfall_trend": rainfall,
        "warmest_month": warmest,
        "coolest_month": coolest,
        "wettest_period": wettest,
        "driest_period": driest,
        "wettest_month": wettest,
        "insights": [
            f"Average temperature was {round(sum(temperatures) / len(temperatures), 1)}°C.",
            f"The warmest month was {warmest['label']} ({warmest['average']}°C average).",
            f"The coolest month was {coolest['label']} ({coolest['average']}°C average).",
            f"The highest precipitation occurred in {wettest['label']} ({wettest['precipitation']} mm).",
            f"The selected period shows a {temperature['trend'].lower()} temperature pattern.",
        ],
        "source": historical.get("source", SOURCE_NAME),
        "is_demo": bool(historical.get("is_demo", False)),
    }
