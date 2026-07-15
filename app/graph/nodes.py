from app.config.llm import llm
from app.models.travel_models import TravelRequirements
from app.graph.state import TravelState


structured_llm = llm.with_structured_output(TravelRequirements)


def requirement_node(state: TravelState) -> TravelState:

    result = structured_llm.invoke(
        f"""
Extract the travel requirements from the user's request.

User Request:
{state["user_query"]}
"""
    )

    requirements = result.model_dump()

    state["requirements"] = requirements

    missing = [
        field
        for field, value in requirements.items()
        if value is None
    ]

    state["missing_fields"] = missing

    return state

def ask_user_node(state: TravelState) -> TravelState:
    state["final_response"] = (
        "I need a little more information before planning your trip.\n\n"
        f"Missing: {', '.join(state['missing_fields'])}"
    )

    return state

from app.tools.search_tool import web_search

from app.config.llm import llm
from app.graph.state import TravelState


def planning_node(state: TravelState) -> TravelState:

    prompt = f"""
You are an expert travel planner.

Requirements:
{state["requirements"]}

Research:
{state["research_data"]}

Additional Preferences:
{state["requirements"].get("additional_preferences", [])}

Create:

1. Short itinerary
2. Estimated budget
3. Travel tips
4. Best attractions
5. Important recommendations

Be concise.
"""

    response = llm.invoke(prompt)

    state["final_response"] = response.content

    state["travel_plan"] = {
        "generated": True
    }

    return state

def research_node(state: TravelState) -> TravelState:

    destination = state["requirements"]["destination"]

    attractions = web_search(
        f"Top tourist attractions in {destination}"
    )

    weather = web_search(
        f"Best season to visit {destination}"
    )

    state["research_data"] = {
        "attractions": attractions,
        "weather": weather
    }

    return state