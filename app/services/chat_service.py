import json
import uuid
from collections.abc import Iterator
from typing import Any

from app.agents.research_agent import ResearchAgent
from app.graph.nodes import (
    ask_user_node,
    cost_estimation_node,
    planning_node,
    requirement_node,
)
from app.graph.workflow import empty_state, graph

research_agent = ResearchAgent()

FIELD_LABELS = {
    "destination": "destination (where you want to go)",
    "origin": "departure city",
    "budget": "budget amount",
    "budget_currency": "budget currency (e.g. USD, INR)",
    "days": "trip duration in days",
    "travelers": "number of travelers",
}

AGENT_STATUS = {
    "requirement": "Requirement Agent: understanding your trip...",
    "research": "Research Agent: gathering destination intelligence...",
    "cost_estimation": "Cost Estimation Agent: building your trip budget...",
    "planning": "Planning Agent: composing the itinerary...",
}

_sessions: dict[str, dict[str, Any]] = {}


def _build_user_query(messages: list[dict[str, str]]) -> str:
    return "\n".join(
        message["content"]
        for message in messages
        if message["role"] == "user"
    )


def _format_missing_fields(missing_fields: list[str]) -> str:
    labels = [
        FIELD_LABELS.get(field, field.replace("_", " "))
        for field in missing_fields
    ]
    return "\n".join(f"- {label}" for label in labels)


def _format_list(title: str, items: list[str] | None) -> str:
    if not items:
        return ""
    lines = [f"**{title}**"]
    lines.extend(f"- {item}" for item in items)
    return "\n".join(lines)


def _format_travel_plan(plan: dict[str, Any], warnings: list[str] | None = None) -> str:
    sections = ["# Your Travel Plan\n"]

    itinerary = _format_list("Day-by-Day Itinerary", plan.get("itinerary", []))
    if itinerary:
        sections.append(itinerary)

    for title, key in [
        ("Recommended Attractions", "recommended_attractions"),
        ("Recommended Hotels", "recommended_hotels"),
        ("Recommended Restaurants", "recommended_restaurants"),
        ("Food Recommendations", "food_recommendations"),
        ("Travel Tips", "travel_tips"),
    ]:
        block = _format_list(title, plan.get(key, []))
        if block:
            sections.append(block)

    if plan.get("transportation"):
        sections.append(f"**Transportation**\n{plan['transportation']}")

    budget_lines = []
    for label, key in [
        ("Transport", "transport_budget"),
        ("Hotel", "hotel_budget"),
        ("Food", "food_budget"),
        ("Activities", "activity_budget"),
        ("Total", "total_estimated_budget"),
    ]:
        value = plan.get(key)
        if value:
            budget_lines.append(f"- {label}: {value}")

    if budget_lines:
        sections.append("**Budget Estimate**\n" + "\n".join(budget_lines))

    if plan.get("budget_status"):
        sections.append(f"**Budget Status:** {plan['budget_status']}")

    if plan.get("weather_notes"):
        sections.append(f"**Weather Notes**\n{plan['weather_notes']}")

    if plan.get("budget_notes"):
        sections.append(f"**Budget Notes**\n{plan['budget_notes']}")

    if warnings:
        sections.append(_format_list("Pipeline Notes", warnings))

    return "\n\n".join(sections)


def _create_session() -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "messages": [],
        "status": "need_info",
        "requirements": {},
        "missing_fields": [],
    }
    return session_id


def _get_session(
    session_id: str | None,
    history: list[dict[str, str]] | None = None,
) -> tuple[str, dict[str, Any]]:
    if session_id and session_id in _sessions:
        session = _sessions[session_id]
        if session["status"] == "complete":
            session_id = _create_session()
            session = _sessions[session_id]
    else:
        session_id = _create_session()
        session = _sessions[session_id]

    if history:
        session["messages"] = [
            {"role": message["role"], "content": message["content"]}
            for message in history
            if message.get("role") and message.get("content")
        ]
    return session_id, session


def reset_session(session_id: str) -> bool:
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def handle_chat(
    message: str,
    session_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    final_result = None
    error_message = None

    for event in handle_chat_stream(message, session_id, history=history):
        if event["type"] == "complete":
            final_result = event
        elif event["type"] == "error":
            error_message = event.get("message") or "Travel planning failed."

    if final_result is None:
        raise RuntimeError(error_message or "Travel planning failed.")

    return final_result


def handle_chat_stream(
    message: str,
    session_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> Iterator[dict[str, Any]]:
    try:
        session_id, session = _get_session(session_id, history=history)
        content = message.strip()
        last_message = session["messages"][-1] if session["messages"] else None
        if not last_message or last_message.get("content") != content:
            session["messages"].append({"role": "user", "content": content})

        yield {"type": "status", "message": AGENT_STATUS["requirement"]}

        state = empty_state(_build_user_query(session["messages"]))
        state["requirements"] = session.get("requirements") or {}
        state = requirement_node(state)

        session["requirements"] = state.get("requirements") or {}
        session["missing_fields"] = state.get("missing_fields") or []

        if state.get("missing_fields"):
            state = ask_user_node(state)
            collected = [
                f"- {FIELD_LABELS.get(key, key)}: {value}"
                for key, value in state.get("requirements", {}).items()
                if key in FIELD_LABELS and value not in (None, "", [])
            ]
            collected_block = (
                "Here's what I already have:\n"
                + "\n".join(collected)
                + "\n\n"
                if collected
                else ""
            )
            reply = (
                "I need a little more information before I can plan your trip:\n\n"
                f"{collected_block}"
                "Still missing:\n"
                f"{_format_missing_fields(state['missing_fields'])}\n\n"
                "Please share only the missing details and I'll continue planning."
            )
            session["messages"].append({"role": "assistant", "content": reply})
            session["status"] = "need_info"
            yield {
                "type": "complete",
                "session_id": session_id,
                "reply": reply,
                "status": "need_info",
                "missing_fields": state["missing_fields"],
            }
            return

        session["status"] = "planning"
        destination = state["requirements"].get("destination", "your destination")
        yield {
            "type": "status",
            "message": f"Research Agent: starting research for {destination}...",
        }

        research_data = None
        for event in research_agent.iter_run(state["requirements"]):
            if event["type"] == "status":
                yield event
            elif event["type"] == "research_complete":
                research_data = event["data"]

        state["research_data"] = research_data or {}
        state["warnings"] = (research_data or {}).get("warnings") or []

        yield {"type": "status", "message": AGENT_STATUS["cost_estimation"]}
        state = cost_estimation_node(state)

        yield {"type": "status", "message": AGENT_STATUS["planning"]}
        state = planning_node(state)

        reply = _format_travel_plan(
            state.get("travel_plan") or {},
            state.get("warnings") or [],
        )
        session["messages"].append({"role": "assistant", "content": reply})
        session["status"] = "complete"

        yield {
            "type": "complete",
            "session_id": session_id,
            "reply": reply,
            "status": "complete",
            "missing_fields": [],
        }
    except Exception as error:
        yield {
            "type": "error",
            "message": str(error),
        }


def run_demo_graph(user_query: str) -> dict[str, Any]:
    return graph.invoke(empty_state(user_query))


def stream_chat_events(
    message: str,
    session_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> Iterator[str]:
    for event in handle_chat_stream(message, session_id, history=history):
        yield f"data: {json.dumps(event)}\n\n"
