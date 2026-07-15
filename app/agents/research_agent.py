from app.tools.tavily_tool import travel_search
from app.tools.geocoding_tool import get_coordinates
from app.tools.weather_tool import get_weather

from app.config.llm import llm
from app.models.research_summary import ResearchSummary

structured_llm = llm.with_structured_output(
    ResearchSummary
)


class ResearchAgent:

    def _search_web(
        self,
        requirements: dict,
    ):

        destination = requirements["destination"]
        travel_style = requirements["travel_style"]

        preferences = ", ".join(
            requirements.get(
                "additional_preferences",
                [],
            )
        )

        return travel_search(
            destination=destination,
            travel_style=travel_style,
            preferences=preferences,
        )

    def _format_search_results(
        self,
        search_results: dict,
    ):

        sections = []

        for category, results in search_results.items():

            text = f"{category.replace('_', ' ').title()}:\n\n"

            for item in results:

                title = item.get("title", "")
                snippet = item.get("content") or item.get("snippet", "")

                if title:
                    text += f"- {title}\n"

                if snippet:
                    text += f"  {snippet}\n\n"

            sections.append(text)

        return "\n".join(sections)

    def _summarize_research(
        self,
        destination: str,
        formatted_research: str,
    ):

        prompt = f"""
You are a travel research analyst.

Read the retrieved travel information and extract only factual information.

Rules:
- Do not invent facts.
- Ignore advertisements and sponsored content.
- Ignore website names.
- Ignore article titles where possible.
- Prefer facts mentioned multiple times.
- If information is missing, leave the field empty.
- Keep responses concise.

Destination:
{destination}

Research:

{formatted_research}

Return the response using the provided structured schema.
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

        if location is None:
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

        location = self._get_location(destination)

        weather = self._get_weather(location)

        search_results = self._search_web(requirements)

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