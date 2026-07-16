from pydantic import BaseModel, field_validator

from app.models.travel_models import _empty_list_if_null


class TravelPlan(BaseModel):

    itinerary: list[str] | None = None

    recommended_attractions: list[str] | None = None

    recommended_hotels: list[str] | None = None

    recommended_restaurants: list[str] | None = None

    food_recommendations: list[str] | None = None

    transportation: str | None = None

    transport_budget: str | None = None

    hotel_budget: str | None = None

    food_budget: str | None = None

    activity_budget: str | None = None

    total_estimated_budget: str | None = None

    budget_status: str | None = None

    travel_tips: list[str] | None = None

    weather_notes: str | None = None

    budget_notes: str | None = None

    @field_validator(
        "itinerary",
        "recommended_attractions",
        "recommended_hotels",
        "recommended_restaurants",
        "food_recommendations",
        "travel_tips",
        mode="before",
    )
    @classmethod
    def convert_string_to_list(cls, value):
        return _empty_list_if_null(value)

    @field_validator(
        "transportation",
        "transport_budget",
        "hotel_budget",
        "food_budget",
        "activity_budget",
        "total_estimated_budget",
        "budget_status",
        "weather_notes",
        "budget_notes",
        mode="before",
    )
    @classmethod
    def empty_string_if_null(cls, value):
        if value is None:
            return ""
        return value
