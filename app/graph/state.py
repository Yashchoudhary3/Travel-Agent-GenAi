from typing import TypedDict, List, Dict, Any


class TravelState(TypedDict):
    user_query: str

    requirements: Dict[str, Any]

    missing_fields: List[str]

    research_data: Dict[str, Any]

    travel_plan: Dict[str, Any]

    final_response: str

    messages: List[Dict[str, str]]