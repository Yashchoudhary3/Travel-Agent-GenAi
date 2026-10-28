import requests

from app.utils.resilience import retry_call

BASE_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    95: "Thunderstorm",
}


def get_weather(latitude: float, longitude: float) -> dict | None:
    if latitude is None or longitude is None:
        return None

    def _fetch() -> dict:
        response = requests.get(
            BASE_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": [
                    "temperature_2m",
                    "wind_speed_10m",
                    "weather_code",
                ],
            },
            timeout=10,
        )
        response.raise_for_status()

        current = response.json()["current"]
        return {
            "temperature": current["temperature_2m"],
            "wind_speed": current["wind_speed_10m"],
            "condition": WEATHER_CODES.get(
                current["weather_code"],
                "Unknown",
            ),
        }

    return retry_call(_fetch, retries=3, backoff=0.6, fallback=None)
