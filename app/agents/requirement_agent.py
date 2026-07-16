from app.config.llm import llm
from app.models.travel_models import TravelRequirements

structured_llm = llm.with_structured_output(
    TravelRequirements,
)

OPTIONAL_FIELDS = {""}


class RequirementAgent:

    def run(
        self,
        user_query: str,
    ):

        prompt = f"""
Extract the travel requirements from the user's request.

Return the result using the provided schema.

User Request:
{user_query}

Guidelines:

- Extract only information explicitly mentioned.
- If a field is not mentioned, leave it null.

Exception:
additional_preferences must ALWAYS be an array.

If there are no hobbies, interests or special requests, return:

additional_preferences: []

Never return null for additional_preferences.
- additional_preferences must be an empty array [] when no hobbies or interests are mentioned.
- additional_preferences should contain only hobbies, interests or special requests.
- Do not invent or assume information.
"""

        result = structured_llm.invoke(prompt)

        requirements = result.model_dump()

        missing_fields = [
            key
            for key, value in requirements.items()
            if value is None and key not in OPTIONAL_FIELDS
        ]

        return {
            "requirements": requirements,
            "missing_fields": missing_fields,
        }