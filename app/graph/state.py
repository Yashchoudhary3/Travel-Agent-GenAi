from typing import Any, Dict, List, TypedDict


class TravelState(TypedDict, total=False):
    user_query: str
    requirements: Dict[str, Any]
    missing_fields: List[str]
    research_data: Dict[str, Any]
    cost_estimate: Dict[str, Any]
    travel_plan: Dict[str, Any]
    final_response: str
    warnings: List[str]
    current_agent: str
    messages: List[Dict[str, str]]
