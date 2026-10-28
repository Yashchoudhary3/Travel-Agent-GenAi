from concurrent.futures import ThreadPoolExecutor

from tavily import TavilyClient

from app.config.settings import TAVILY_API_KEY
from app.utils.resilience import retry_call

client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

SEARCH_QUERIES = {
    "attractions": "Top tourist attractions in {destination}",
    "hotels": "Best {hotel_preference} hotels in {destination}",
    "restaurants": "Best {food_preference} restaurants in {destination}",
    "local_food": "Popular local food and famous dishes in {destination}",
    "transport": "Tourist transportation in {destination} using {transport_preference}",
    "travel_cost": "Average hotel, food, transport and sightseeing cost per day in {destination}",
    "travel_tips": "Travel tips for first time visitors to {destination}",
    "best_time": "Best time to visit {destination}",
}

SEARCH_STATUS = {
    "attractions": "Research Agent: searching top attractions...",
    "hotels": "Research Agent: finding hotels that match your preferences...",
    "restaurants": "Research Agent: looking for restaurants...",
    "local_food": "Research Agent: discovering local food...",
    "transport": "Research Agent: researching transport options...",
    "travel_cost": "Research Agent: checking typical travel costs...",
    "travel_tips": "Research Agent: gathering travel tips...",
    "best_time": "Research Agent: finding the best time to visit...",
}


def _search(query: str) -> list:
    if client is None:
        return []

    def _fetch() -> list:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=2,
        )
        return response.get("results", []) or []

    return retry_call(_fetch, retries=3, backoff=0.7, fallback=[])


def _build_query(
    template: str,
    destination: str,
    preferences: str,
    hotel_preference: str,
    food_preference: str,
    transport_preference: str,
    key: str,
) -> str:
    query = template.format(
        destination=destination,
        hotel_preference=hotel_preference or "any",
        food_preference=food_preference or "local",
        transport_preference=transport_preference or "any",
    )

    if preferences and key in {"attractions", "restaurants", "travel_tips"}:
        query += f". User interests: {preferences}"

    return query


def travel_search(
    destination: str,
    preferences: str,
    hotel_preference: str,
    food_preference: str,
    transport_preference: str,
) -> dict:
    results = {}

    with ThreadPoolExecutor() as executor:
        futures = {}

        for key, template in SEARCH_QUERIES.items():
            query = _build_query(
                template,
                destination,
                preferences,
                hotel_preference,
                food_preference,
                transport_preference,
                key,
            )
            futures[key] = executor.submit(_search, query)

        for key, future in futures.items():
            try:
                results[key] = future.result()
            except Exception:
                results[key] = []

    return results


def iter_travel_search(
    destination: str,
    preferences: str,
    hotel_preference: str,
    food_preference: str,
    transport_preference: str,
):
    if client is None:
        yield {
            "type": "status",
            "message": "Research Agent: web search unavailable, using fallback data...",
        }
        yield {"type": "results", "data": {key: [] for key in SEARCH_QUERIES}}
        return

    results = {}

    for key, template in SEARCH_QUERIES.items():
        yield {
            "type": "status",
            "message": SEARCH_STATUS[key],
        }

        query = _build_query(
            template,
            destination,
            preferences,
            hotel_preference,
            food_preference,
            transport_preference,
            key,
        )
        results[key] = _search(query)

    yield {
        "type": "results",
        "data": results,
    }
