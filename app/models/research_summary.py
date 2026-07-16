from pydantic import BaseModel, Field, field_validator

from app.models.travel_models import _empty_list_if_null


class ResearchSummary(BaseModel):

    must_visit_places: list[str] | None = None
    best_time: str | None = None
    travel_tips: list[str] | None = None
    local_transport: list[str] | None = None
    food_to_try: list[str] | None = None

    recommended_restaurants: list[str] | None = None
    recommended_hotels: list[str] | None = None

    estimated_hotel_cost_per_night: str | None = None
    estimated_food_cost_per_day: str | None = None
    estimated_local_transport_cost_per_day: str | None = None
    estimated_daily_budget: str | None = None

    @field_validator(
        "must_visit_places",
        "travel_tips",
        "local_transport",
        "food_to_try",
        "recommended_restaurants",
        "recommended_hotels",
        mode="before",
    )
    @classmethod
    def convert_string_to_list(cls, value):
        return _empty_list_if_null(value)

    @field_validator(
        "best_time",
        "estimated_hotel_cost_per_night",
        "estimated_food_cost_per_day",
        "estimated_local_transport_cost_per_day",
        "estimated_daily_budget",
        mode="before",
    )
    @classmethod
    def empty_string_if_null(cls, value):
        if value is None:
            return ""
        return value
