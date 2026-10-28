from app.config.llm import llm
from app.models.research_summary import ResearchSummary
from app.tools.geocoding_tool import get_coordinates
from app.tools.tavily_tool import iter_travel_search, travel_search
from app.tools.weather_tool import get_weather
from app.utils.resilience import invoke_with_retry

structured_llm = llm.with_structured_output(ResearchSummary)

EMPTY_RESEARCH = {
    "destination": "",
    "location": None,
    "weather": None,
    "research_summary": ResearchSummary().model_dump(),
    "warnings": [],
}


class ResearchAgent:
    def _search_web(self, requirements: dict) -> dict:
        return travel_search(
            destination=requirements["destination"],
            preferences=", ".join(requirements.get("additional_preferences", [])),
            hotel_preference=requirements.get("hotel_preference"),
            food_preference=requirements.get("food_preference"),
            transport_preference=requirements.get("transport_preference"),
        )

    def _format_search_results(self, search_results: dict) -> str:
        sections = []

        for category, results in (search_results or {}).items():
            section = [f"{category.replace('_', ' ').title()}:"]

            for item in results or []:
                title = item.get("title", "")
                content = item.get("content") or item.get("snippet", "")
                if title:
                    section.append(f"- {title}")
                if content:
                    section.append(content)

            if len(section) > 1:
                sections.append("\n".join(section))

        return "\n\n".join(sections)

    def _summarize_research(self, destination: str, formatted_research: str):
        if not formatted_research.strip():
            return ResearchSummary()

        prompt = f"""
You are a travel research analyst.

Destination:
{destination}

Research:
{formatted_research}

Extract the information into the provided schema.

Rules:
- Use ONLY the supplied research.
- Do NOT invent information.
- Ignore advertisements and promotional content.
- If information is unavailable, return null.

The following fields MUST ALWAYS be JSON arrays:
- must_visit_places
- travel_tips
- local_transport
- food_to_try
- recommended_restaurants
- recommended_hotels

All cost fields and best_time should be plain strings.
"""
        try:
            return invoke_with_retry(structured_llm, prompt)
        except Exception:
            return ResearchSummary()

    def _get_location(self, destination: str):
        try:
            return get_coordinates(destination)
        except Exception:
            return None

    def _get_weather(self, location: dict | None):
        if not location:
            return None
        try:
            return get_weather(
                latitude=location["latitude"],
                longitude=location["longitude"],
            )
        except Exception:
            return None

    def run(self, requirements: dict) -> dict:
        warnings: list[str] = []
        destination = requirements.get("destination") or ""

        location = self._get_location(destination)
        if not location:
            warnings.append("Could not geocode the destination; weather was skipped.")

        weather = self._get_weather(location)
        if location and not weather:
            warnings.append("Weather lookup failed; planning will continue without live weather.")

        try:
            search_results = self._search_web(requirements)
        except Exception:
            search_results = {}
            warnings.append("Web search failed; the plan will use limited destination knowledge.")

        formatted_research = self._format_search_results(search_results)
        if not formatted_research.strip():
            warnings.append("No usable web research was found.")

        research_summary = self._summarize_research(destination, formatted_research)

        return {
            "destination": destination,
            "location": location,
            "weather": weather,
            "research_summary": research_summary.model_dump(),
            "warnings": warnings,
        }

    def iter_run(self, requirements: dict):
        warnings: list[str] = []
        destination = requirements.get("destination") or ""
        preferences = ", ".join(requirements.get("additional_preferences", []))

        yield {
            "type": "status",
            "message": f"Research Agent: pinpointing {destination} on the map...",
        }
        location = self._get_location(destination)
        if not location:
            warnings.append("Could not geocode the destination; weather was skipped.")

        yield {
            "type": "status",
            "message": "Research Agent: checking current weather...",
        }
        weather = self._get_weather(location)
        if location and not weather:
            warnings.append("Weather lookup failed; planning will continue without live weather.")

        search_results = {}
        for event in iter_travel_search(
            destination=destination,
            preferences=preferences,
            hotel_preference=requirements.get("hotel_preference"),
            food_preference=requirements.get("food_preference"),
            transport_preference=requirements.get("transport_preference"),
        ):
            if event["type"] == "status":
                yield event
            else:
                search_results = event["data"]

        if not any(search_results.values()):
            warnings.append("No usable web research was found.")

        yield {
            "type": "status",
            "message": "Research Agent: summarizing findings...",
        }

        formatted_research = self._format_search_results(search_results)
        research_summary = self._summarize_research(destination, formatted_research)

        yield {
            "type": "research_complete",
            "data": {
                "destination": destination,
                "location": location,
                "weather": weather,
                "research_summary": research_summary.model_dump(),
                "warnings": warnings,
            },
        }
