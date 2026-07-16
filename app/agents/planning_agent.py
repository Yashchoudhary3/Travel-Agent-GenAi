from app.config.llm import llm
from app.models.travel_plan import TravelPlan

structured_llm = llm.with_structured_output(
    TravelPlan,
)


def _join_lines(items: list[str] | None) -> str:
    return "\n".join(items or [])


class PlanningAgent:

    def run(
        self,
        requirements: dict,
        research_data: dict,
    ):

        summary = research_data["research_summary"]
        weather = research_data.get("weather") or {}

        prompt = f"""
You are an expert travel planner.

Create a practical travel plan using ONLY the information below.

========================
TRIP REQUIREMENTS
========================

Destination:
{requirements.get("destination")}

Origin:
{requirements.get("origin")}

Duration:
{requirements.get("days")} days

Travelers:
{requirements.get("travelers")}

Budget:
{requirements.get("budget")} {requirements.get("budget_currency")}

Preferred Transport:
{requirements.get("transport_preference")}

Preferred Hotel:
{requirements.get("hotel_preference")}

Food Preference:
{requirements.get("food_preference")}

Additional Preferences:
{", ".join(requirements.get("additional_preferences", [])) or "None"}

========================
CURRENT WEATHER
========================

Temperature:
{weather.get("temperature")}°C

Wind Speed:
{weather.get("wind_speed")} km/h

Condition:
{weather.get("condition")}

========================
RESEARCH SUMMARY
========================

Must Visit Places
{_join_lines(summary.get("must_visit_places"))}

Best Time
{summary.get("best_time") or ""}

Travel Tips
{_join_lines(summary.get("travel_tips"))}

Local Transport
{_join_lines(summary.get("local_transport"))}

Recommended Restaurants
{_join_lines(summary.get("recommended_restaurants"))}

Recommended Hotels
{_join_lines(summary.get("recommended_hotels"))}

Estimated Hotel Cost Per Night
{summary.get("estimated_hotel_cost_per_night") or ""}

Estimated Food Cost Per Day
{summary.get("estimated_food_cost_per_day") or ""}

Estimated Local Transport Cost Per Day
{summary.get("estimated_local_transport_cost_per_day") or ""}

Estimated Daily Budget
{summary.get("estimated_daily_budget") or ""}

Food To Try
{_join_lines(summary.get("food_to_try"))}

========================
OUTPUT
========================

OUTPUT

Generate:

1. Day-wise itinerary
2. Recommended attractions
3. Recommended hotels
4. Recommended restaurants
5. Food recommendations
6. Transportation advice
7. Transport budget (ONLY if available in research)
8. Hotel budget (ONLY if available in research)
9. Food budget (ONLY if available in research)
10. Activity budget (ONLY if available in research)
11. Total estimated budget (ONLY if calculable from research)
12. Budget status
13. Travel tips
14. Weather notes
15. Budget notes

========================
RULES
========================

- Use ONLY the supplied research.
- Respect every user preference.
- User preferences always override generic travel advice.
- Use attractions only from "Must Visit Places".
- Use hotels only from "Recommended Hotels".
- Use restaurants only from "Recommended Restaurants".
- Never recommend food that conflicts with the user's food preference.
- Respect the preferred transport and hotel type.
- Keep the itinerary geographically realistic.
- Trips shorter than 6 days should normally include no more than two cities.
- Consider the current weather while planning.
- Never invent hotels, restaurants, attractions, transport options or prices.
- Never estimate or invent any numeric cost.

If the research does not contain a cost:

- return "Not available" for that budget field.
- explain in budget_notes that live booking data is required.

 Budget status must be determined only from available research.

If total trip cost cannot be calculated from the available research,
set:

budget_status = "Cannot determine"

and explain why in budget_notes.

Only use prices explicitly present in the research summary.
- Never copy the user's budget as the estimated trip cost.
- Keep all costs in {requirements.get("budget_currency")}.
"""

        response = structured_llm.invoke(prompt)

        return response.model_dump()