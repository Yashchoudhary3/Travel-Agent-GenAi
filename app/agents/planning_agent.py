from app.config.llm import llm
from app.models.travel_plan import TravelPlan

structured_llm = llm.with_structured_output(
    TravelPlan
)

class PlanningAgent:

    def run(
        self,
        requirements: dict,
        research_data: dict,
    ):

        summary = research_data["research_summary"]
        weather = research_data["weather"]

        prompt = f"""
You are an expert travel planner.

Create a practical travel plan using the structured research below.

========================
TRIP REQUIREMENTS
========================

Destination:
{requirements["destination"]}

Origin:
{requirements["origin"]}

Duration:
{requirements["days"]} days

Travellers:
{requirements["travelers"]}

Budget:
{requirements["budget"]} {requirements["budget_currency"]}

Travel Style:
{requirements["travel_style"]}

User Preferences

Travel Style:
{requirements.get("travel_style")}

Additional Preferences:
{", ".join(requirements.get("additional_preferences", [])) or "None"}

These preferences are mandatory and must override generic travel advice.

========================
CURRENT WEATHER
========================

Temperature:
{weather["temperature"]}°C

Wind Speed:
{weather["wind_speed"]} km/h

Weather condition:
{weather["condition"]}

========================
RESEARCH SUMMARY
========================

Must Visit Places:
{chr(10).join(summary["must_visit_places"])}

Best Time:
{summary["best_time"]}

Travel Tips:
{chr(10).join(summary["travel_tips"])}

Local Transportation:
{summary["local_transport"]}

Food To Try:
{chr(10).join(summary["food_to_try"])}

========================
INSTRUCTIONS
========================

Generate:

1. Day-wise itinerary
2. Recommended attractions
3. Local food recommendations
4. Transportation advice
5. Travel tips
6. Weather considerations
7. Budget considerations

Rules:

- Stay within the user's budget.
- Never invent hotel, flight, train or attraction prices.
- If pricing is required, clearly mention that live booking data is needed.
- Only use the research provided.
- If some information is unavailable, explicitly mention that instead of guessing.

Planning Rules

- Respect every user requirement and preference.
- User preferences always have higher priority than generic travel recommendations.
- Never recommend food, activities, or places that conflict with the user's preferences.
- Minimize unnecessary travel between cities.
- For trips shorter than 6 days, recommend at most 2 cities unless there is a strong reason.
- Group nearby attractions on the same day.
- Keep the itinerary realistic. Do not require impossible travel within a single day.
- Use the current weather when giving recommendations.
- If research is insufficient, explicitly mention that instead of guessing.

Budget Rules

- Never change the user's budget currency.
- Never invent hotel, flight or attraction prices.
- If live prices are unavailable, clearly mention that booking data is required.
- Keep recommendations appropriate for the user's budget.
"""

        response = structured_llm.invoke(prompt)

        return response.model_dump()