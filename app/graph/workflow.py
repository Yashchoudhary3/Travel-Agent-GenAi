from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    ask_user_node,
    cost_estimation_node,
    planning_node,
    requirement_node,
    research_node,
)
from app.graph.router import route_after_requirement
from app.graph.state import TravelState

builder = StateGraph(TravelState)

builder.add_node("requirement", requirement_node)
builder.add_node("ask_user", ask_user_node)
builder.add_node("research", research_node)
builder.add_node("cost_estimation", cost_estimation_node)
builder.add_node("planning", planning_node)

builder.add_edge(START, "requirement")
builder.add_conditional_edges(
    "requirement",
    route_after_requirement,
    {
        "ask_user": "ask_user",
        "research": "research",
    },
)
builder.add_edge("ask_user", END)
builder.add_edge("research", "cost_estimation")
builder.add_edge("cost_estimation", "planning")
builder.add_edge("planning", END)

graph = builder.compile()


def empty_state(user_query: str = "") -> dict:
    return {
        "user_query": user_query,
        "requirements": {},
        "missing_fields": [],
        "research_data": {},
        "cost_estimate": {},
        "travel_plan": {},
        "final_response": "",
        "warnings": [],
        "current_agent": "",
        "messages": [],
    }
