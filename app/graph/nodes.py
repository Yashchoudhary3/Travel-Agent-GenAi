from app.config.llm import llm
from app.models.travel_models import TravelRequirements
from app.graph.state import TravelState
from app.agents.requirement_agent import RequirementAgent

from app.config.llm import llm
from app.graph.state import TravelState
from app.agents.research_agent import ResearchAgent

from app.agents.planning_agent import PlanningAgent

planning_agent = PlanningAgent()

research_agent = ResearchAgent()


requirement_agent = RequirementAgent()

structured_llm = llm.with_structured_output(TravelRequirements)


def requirement_node(state):

    result = requirement_agent.run(
        state["user_query"]
    )

    state["requirements"] = result["requirements"]
    state["missing_fields"] = result["missing_fields"]

    return state

def ask_user_node(state: TravelState) -> TravelState:
    state["final_response"] = (
        "I need a little more information before planning your trip.\n\n"
        f"Missing: {', '.join(state['missing_fields'])}"
    )

    return state


def planning_node(state):

    response = planning_agent.run(
        state["requirements"],
        state["research_data"],
    )

    state["travel_plan"] = {
        "generated": True
    }

    state["final_response"] = response

    return state


def research_node(state):

    state["research_data"] = research_agent.run(
        state["requirements"]
    )
    print(state["research_data"],"==========")

    return state