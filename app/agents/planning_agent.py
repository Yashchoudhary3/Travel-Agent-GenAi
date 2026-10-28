from app.config.llm import llm
from app.models.travel_plan import TravelPlan
from app.utils.resilience import invoke_with_retry

structured_llm = llm.with_structured_output(TravelPlan)


def _join_lines(items: list[str] | None) -> str:
    return "\n".join(items or [])


class PlanningAgent:
    def run(
        self,
        requirements: dict,
        research_data: dict,
        cost_estimate: dict | None = None,
    ) -> dict:
        summary = (research_data or {}).get("research_summary") or {}
        weather = (research_data or {}).get("weather") or {}
        cost_estimate = cost_estimate or {}
        warnings = (research_data or {}).get("warnings") or []

        prompt = f"""
You are an expert travel planner working with a Requirement Agent, Research Agent, and Cost Estimation Agent.

Create a practical travel plan using ONLY the information below.

========================
TRIP REQUIREMENTS
========================

Destination: {requirements.get("destination")}
Origin: {requirements.get("origin")}
Duration: {requirements.get("days")} days
Travelers: {requirements.get("travelers")}
Budget: {requirements.get("budget")} {requirements.get("budget_currency")}
Preferred Transport: {requirements.get("transport_preference")}
Preferred Hotel: {requirements.get("hotel_preference")}
Food Preference: {requirements.get("food_preference")}
Additional Preferences: {", ".join(requirements.get("additional_preferences", [])) or "None"}

========================
CURRENT WEATHER
========================

Temperature: {weather.get("temperature", "Unknown")}
Wind Speed: {weather.get("wind_speed", "Unknown")}
Condition: {weather.get("condition", "Unknown")}

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

Food To Try
{_join_lines(summary.get("food_to_try"))}

Research warnings:
{_join_lines(warnings)}

========================
COST ESTIMATION AGENT
========================

Use these figures for every budget field. Do not invent different numbers.

Transport: {cost_estimate.get("transport_cost_display", "Not available")}
Hotel: {cost_estimate.get("hotel_cost_display", "Not available")}
Food: {cost_estimate.get("food_cost_display", "Not available")}
Activities: {cost_estimate.get("activity_cost_display", "Not available")}
Total: {cost_estimate.get("total_estimated_cost_display", "Not available")}
Budget status: {cost_estimate.get("budget_status", "Cannot determine")}
Notes:
{_join_lines(cost_estimate.get("assumptions", []))}
{_join_lines(cost_estimate.get("warnings", []))}

========================
OUTPUT
========================

Generate:
1. Day-wise itinerary
2. Recommended attractions
3. Recommended hotels
4. Recommended restaurants
5. Food recommendations
6. Transportation advice
7. Copy the Cost Estimation Agent budget fields exactly
8. Travel tips
9. Weather notes
10. Budget notes from the Cost Estimation Agent

========================
RULES
========================

- Use ONLY the supplied research.
- Respect every user preference.
- User preferences always override generic travel advice.
- Use attractions only from "Must Visit Places" when that list is not empty.
- Use hotels only from "Recommended Hotels" when that list is not empty.
- Use restaurants only from "Recommended Restaurants" when that list is not empty.
- Never recommend food that conflicts with the user's food preference.
- Keep the itinerary geographically realistic.
- Trips shorter than 6 days should normally include no more than two cities.
- Consider the current weather while planning.
- Never invent hotels, restaurants, attractions, transport options or prices.
- If research is thin, say so in travel_tips instead of fabricating details.
- Never copy the user's budget as the estimated trip cost.
- Keep all costs in {requirements.get("budget_currency")}.
"""

        try:
            response = invoke_with_retry(structured_llm, prompt)
            return response.model_dump()
        except Exception:
            return TravelPlan(
                itinerary=[
                    "Planning Agent could not finish the itinerary. Please try again."
                ],
                travel_tips=[
                    "A fallback response was returned after the language model failed."
                ],
                budget_status=cost_estimate.get("budget_status", "Cannot determine"),
                transport_budget=cost_estimate.get("transport_cost_display", "Not available"),
                hotel_budget=cost_estimate.get("hotel_cost_display", "Not available"),
                food_budget=cost_estimate.get("food_cost_display", "Not available"),
                activity_budget=cost_estimate.get("activity_cost_display", "Not available"),
                total_estimated_budget=cost_estimate.get(
                    "total_estimated_cost_display", "Not available"
                ),
            ).model_dump()
