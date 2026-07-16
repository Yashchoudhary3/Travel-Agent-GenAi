from concurrent.futures import ThreadPoolExecutor

from tavily import TavilyClient
from app.config.settings import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)

SEARCH_QUERIES = {
    "attractions":
        "Top tourist attractions in {destination}",

    "hotels":
        "Best {hotel_preference} hotels in {destination}",

    "restaurants":
        "Best {food_preference} restaurants in {destination}",

    "local_food":
        "Popular local food and famous dishes in {destination}",

    "transport":
        "Tourist transportation in {destination} using {transport_preference}",

    "travel_cost":
        "Average hotel, food, transport and sightseeing cost per day in {destination}",

    "travel_tips":
        "Travel tips for first time visitors to {destination}",

    "best_time":
        "Best time to visit {destination}",
}

SEARCH_STATUS = {
    "attractions": "Searching top attractions and must-visit places...",
    "hotels": "Finding hotels that match your preferences...",
    "restaurants": "Looking for restaurants you'll like...",
    "local_food": "Discovering local food and famous dishes...",
    "transport": "Researching local transport options...",
    "travel_cost": "Checking average hotel, food, and transport costs...",
    "travel_tips": "Gathering travel tips for your destination...",
    "best_time": "Finding the best time to visit...",
}


def _search(query: str):
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=2,
    )

    return response.get("results", [])


def travel_search(
    destination: str,
    preferences: str,
    hotel_preference: str,
    food_preference: str,
    transport_preference: str,
):

    results = {}

    with ThreadPoolExecutor() as executor:

        futures = {}

        for key, template in SEARCH_QUERIES.items():

            query = template.format(
                destination=destination,
                hotel_preference=hotel_preference,
                food_preference=food_preference,
                transport_preference=transport_preference,
            )

            if preferences and key in {
                "attractions",
                "restaurants",
                "travel_tips",
            }:
                query += f". User interests: {preferences}"

            futures[key] = executor.submit(
                _search,
                query,
            )

        for key, future in futures.items():
            results[key] = future.result()

    return results


def iter_travel_search(
    destination: str,
    preferences: str,
    hotel_preference: str,
    food_preference: str,
    transport_preference: str,
):
    results = {}

    for key, template in SEARCH_QUERIES.items():
        yield {
            "type": "status",
            "message": SEARCH_STATUS[key],
        }

        query = template.format(
            destination=destination,
            hotel_preference=hotel_preference,
            food_preference=food_preference,
            transport_preference=transport_preference,
        )

        if preferences and key in {
            "attractions",
            "restaurants",
            "travel_tips",
        }:
            query += f". User interests: {preferences}"

        results[key] = _search(query)

    yield {
        "type": "results",
        "data": results,
    }