from pydantic import BaseModel, Field


class TravelPlan(BaseModel):

    itinerary: list[str] = Field(
        description="Day-by-day itinerary."
    )

    recommended_attractions: list[str] = Field(
        description="Recommended attractions."
    )

    food_recommendations: list[str] = Field(
        description="Local food recommendations."
    )

    transportation: str = Field(
        description="Transportation advice."
    )

    travel_tips: list[str] = Field(
        description="Important travel tips."
    )

    weather_notes: str = Field(
        description="Weather considerations."
    )

    budget_notes: str = Field(
        description="Budget advice."
    )