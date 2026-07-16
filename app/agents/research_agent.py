from app.config.llm import llm
from app.models.research_summary import ResearchSummary

from app.tools.geocoding_tool import get_coordinates
from app.tools.tavily_tool import iter_travel_search, travel_search
from app.tools.weather_tool import get_weather


structured_llm = llm.with_structured_output(
    ResearchSummary,
)


class ResearchAgent:

    def _search_web(
        self,
        requirements: dict,
    ):

        return travel_search(
            destination=requirements["destination"],
            preferences=", ".join(
                requirements.get(
                    "additional_preferences",
                    []
                )
            ),
            hotel_preference=requirements.get(
                "hotel_preference"
            ),
            food_preference=requirements.get(
                "food_preference"
            ),
            transport_preference=requirements.get(
                "transport_preference"
            ),
        )

    def _format_search_results(
        self,
        search_results: dict,
    ):

        sections = []

        for category, results in search_results.items():

            section = [
                f"{category.replace('_', ' ').title()}:"
            ]

            for item in results:

                title = item.get("title", "")
                content = (
                    item.get("content")
                    or item.get("snippet", "")
                )

                if title:
                    section.append(f"- {title}")

                if content:
                    section.append(content)

            sections.append(
                "\n".join(section)
            )

        return "\n\n".join(sections)

    def _summarize_research(
    self,
    destination: str,
    formatted_research: str,
):

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

IMPORTANT:

The following fields MUST ALWAYS be JSON arrays, even if there is only ONE value:

- must_visit_places
- travel_tips
- local_transport
- food_to_try
- recommended_restaurants
- recommended_hotels

Correct:

must_visit_places = ["Tokyo", "Kyoto"]

Wrong:

must_visit_places = "Tokyo, Kyoto"

Never return comma-separated strings for list fields.

All cost fields and best_time should be plain strings.
"""

     return structured_llm.invoke(prompt)

    def _get_location(
        self,
        destination: str,
    ):
        return get_coordinates(destination)

    def _get_weather(
        self,
        location: dict,
    ):

        if not location:
            return None

        return get_weather(
            latitude=location["latitude"],
            longitude=location["longitude"],
        )

    def run(
        self,
        requirements: dict,
    ):

        destination = requirements["destination"]

        location = self._get_location(
            destination
        )

        weather = self._get_weather(
            location
        )

        search_results = self._search_web(
            requirements
        )

        formatted_research = self._format_search_results(
            search_results
        )

        research_summary = self._summarize_research(
            destination,
            formatted_research,
        )

        return {
            "destination": destination,
            "location": location,
            "weather": weather,
            "research_summary": research_summary.model_dump(),
        }

    def iter_run(
        self,
        requirements: dict,
    ):
        destination = requirements["destination"]
        preferences = ", ".join(
            requirements.get("additional_preferences", [])
        )

        yield {
            "type": "status",
            "message": f"Pinpointing {destination} on the map...",
        }

        location = self._get_location(destination)

        yield {
            "type": "status",
            "message": "Checking current weather at your destination...",
        }

        weather = self._get_weather(location)

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

        yield {
            "type": "status",
            "message": "Analyzing research and summarizing findings...",
        }

        formatted_research = self._format_search_results(
            search_results
        )

        research_summary = self._summarize_research(
            destination,
            formatted_research,
        )

        yield {
            "type": "research_complete",
            "data": {
                "destination": destination,
                "location": location,
                "weather": weather,
                "research_summary": research_summary.model_dump(),
            },
        }