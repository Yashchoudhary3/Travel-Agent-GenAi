from langgraph.graph import START, END, StateGraph

from app.graph.state import TravelState
from app.graph.nodes import (
    requirement_node,
    research_node,
    planning_node,
    ask_user_node
)
from app.graph.router import route_after_requirement


builder = StateGraph(TravelState)

builder.add_node("requirement", requirement_node)
builder.add_node("research", research_node)
builder.add_node("planning", planning_node)
builder.add_node("ask_user", ask_user_node)

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
builder.add_edge("research", "planning")
builder.add_edge("planning", END)

graph = builder.compile()