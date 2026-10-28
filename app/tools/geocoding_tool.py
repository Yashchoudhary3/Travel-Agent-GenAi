import requests

from app.utils.resilience import retry_call

BASE_URL = "https://nominatim.openstreetmap.org/search"


def get_coordinates(destination: str) -> dict | None:
    if not destination:
        return None

    def _fetch() -> dict | None:
        response = requests.get(
            BASE_URL,
            params={
                "q": destination,
                "format": "json",
                "limit": 1,
                "accept-language": "en",
            },
            headers={
                "User-Agent": "AI-Travel-Planner/1.0",
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

    return retry_call(_fetch, retries=3, backoff=0.7, fallback=None)
