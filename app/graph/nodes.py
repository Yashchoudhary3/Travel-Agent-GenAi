from app.agents.cost_estimation_agent import CostEstimationAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.requirement_agent import RequirementAgent
from app.agents.research_agent import EMPTY_RESEARCH, ResearchAgent
from app.graph.state import TravelState
from app.models.travel_plan import TravelPlan

requirement_agent = RequirementAgent()
research_agent = ResearchAgent()
cost_estimation_agent = CostEstimationAgent()
planning_agent = PlanningAgent()


def _merge_warnings(*groups: list[str] | None) -> list[str]:
    merged: list[str] = []
    seen = set()
    for group in groups:
        for warning in group or []:
            if warning and warning not in seen:
                seen.add(warning)
                merged.append(warning)
    return merged


def requirement_node(state: TravelState) -> TravelState:
    result = requirement_agent.run(
        state.get("user_query", ""),
        previous=state.get("requirements") or {},
    )
    return {
        **state,
        "current_agent": "requirement",
        "requirements": result["requirements"],
        "missing_fields": result["missing_fields"],
    }


def ask_user_node(state: TravelState) -> TravelState:
    missing = state.get("missing_fields") or []
    return {
        **state,
        "current_agent": "ask_user",
        "final_response": (
            "I need a little more information before planning your trip.\n\n"
            f"Missing: {', '.join(missing)}"
        ),
    }


def research_node(state: TravelState) -> TravelState:
    try:
        research_data = research_agent.run(state.get("requirements") or {})
    except Exception as error:
        research_data = {
            **EMPTY_RESEARCH,
            "destination": (state.get("requirements") or {}).get("destination", ""),
            "warnings": [f"Research Agent fallback: {error}"],
        }

    return {
        **state,
        "current_agent": "research",
        "research_data": research_data,
        "warnings": _merge_warnings(
            state.get("warnings"),
            research_data.get("warnings"),
        ),
    }


def cost_estimation_node(state: TravelState) -> TravelState:
    research_data = state.get("research_data") or {}
    try:
        cost_estimate = cost_estimation_agent.run(
            state.get("requirements") or {},
            research_data.get("research_summary") or {},
        )
    except Exception as error:
        cost_estimate = cost_estimation_agent.run(
            state.get("requirements") or {},
            {},
        )
        cost_estimate["warnings"] = _merge_warnings(
            cost_estimate.get("warnings"),
            [f"Cost Estimation Agent used a fallback: {error}"],
        )

    return {
        **state,
        "current_agent": "cost_estimation",
        "cost_estimate": cost_estimate,
        "warnings": _merge_warnings(
            state.get("warnings"),
            cost_estimate.get("warnings"),
        ),
    }


def planning_node(state: TravelState) -> TravelState:
    cost_estimate = state.get("cost_estimate") or {}
    try:
        travel_plan = planning_agent.run(
            state.get("requirements") or {},
            state.get("research_data") or {},
            cost_estimate,
        )
    except Exception as error:
        travel_plan = TravelPlan(
            itinerary=["Planning Agent fallback: could not build a full itinerary."],
            travel_tips=[str(error)],
        ).model_dump()

    travel_plan = cost_estimation_agent.apply_to_plan(travel_plan, cost_estimate)

    return {
        **state,
        "current_agent": "planning",
        "travel_plan": travel_plan,
        "final_response": "complete",
        "warnings": _merge_warnings(state.get("warnings"), cost_estimate.get("warnings")),
    }
