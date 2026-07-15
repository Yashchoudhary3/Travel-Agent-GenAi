from concurrent.futures import ThreadPoolExecutor

from tavily import TavilyClient
from app.config.settings import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)

SEARCH_QUERIES = {
    "attractions": (
        "Best tourist attractions in {destination} "
        "for {travel_style} travelers {preferences}"
    ),

    "food": (
        "Best food options in {destination} "
        "for travelers who prefer {preferences}"
    ),

    "transport": (
        "Public transportation in {destination} for tourists"
    ),

    "travel_tips": (
        "Travel tips for {travel_style} travelers visiting {destination}"
    ),

    "best_time": (
        "Best time to visit {destination}"
    ),
}


def _search(query: str):
    response = client.search(
        query=query,
        max_results=3,
        search_depth="basic",
    )

    return response["results"]


def travel_search(
    destination: str,
    travel_style: str = "",
    preferences: str = "",
):

    results = {}

    queries = {
        "attractions":
            f"Best tourist attractions in {destination} for {travel_style}. {preferences}",

        "food":
            f"Best food in {destination}. User preferences: {preferences}",

        "transport":
            f"Public transportation in {destination} for tourists",

        "travel_tips":
            f"Travel tips for first time visitors to {destination}. Preferences: {preferences}",

        "best_time":
            f"Best time to visit {destination}",
    }

    with ThreadPoolExecutor() as executor:

        futures = {
        key: executor.submit(
        _search,
        query.format(
            destination=destination,
            travel_style=travel_style,
            preferences=preferences,
        ),
    )
        for key, query in SEARCH_QUERIES.items()
}

        for key, future in futures.items():
            results[key] = future.result()

    return results