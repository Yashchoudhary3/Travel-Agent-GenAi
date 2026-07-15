from app.graph.state import TravelState


def route_after_requirement(state: TravelState) -> str:
    if state["missing_fields"]:
        return "ask_user"

    return "research"