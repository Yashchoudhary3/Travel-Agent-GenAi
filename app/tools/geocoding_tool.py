import requests


BASE_URL = "https://nominatim.openstreetmap.org/search"


def get_coordinates(destination: str) -> dict | None:
    response = requests.get(
        BASE_URL,
        params={
            "q": destination,
            "format": "json",
            "limit": 1,
            "accept-language": "en",
        },
        headers={
            # Nominatim requires a User-Agent.
            "User-Agent": "AI-Travel-Planner/1.0"
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return None

    location = data[0]

    return {
        "latitude": float(location["lat"]),
        "longitude": float(location["lon"]),
        "display_name": location["display_name"],
    }