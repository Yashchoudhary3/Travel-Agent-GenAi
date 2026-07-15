from app.config.llm import llm
from app.models.travel_models import TravelRequirements

structured_llm = llm.with_structured_output(TravelRequirements)


class RequirementAgent:

    def run(self, user_query: str):

        prompt = f"""
Extract travel requirements from the user's request.

Return structured data only.

User Request:
{user_query}
"""

        result = structured_llm.invoke(prompt)

        requirements = result.model_dump()

        missing_fields = [
            key
            for key, value in requirements.items()
            if value is None
        ]

        return {
            "requirements": requirements,
            "missing_fields": missing_fields,
        }