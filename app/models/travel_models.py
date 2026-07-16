from pydantic import BaseModel, Field, field_validator


def _empty_list_if_null(value):
    if value is None:
        return []

    if isinstance(value, str):
        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    return value


class TravelRequirements(BaseModel):
    destination: str | None = None
    origin: str | None = None

    budget: float | None = None
    budget_currency: str | None = None

    days: int | None = None
    travelers: int | None = None

    additional_preferences: list[str] = Field(default_factory=list)

    transport_preference: str | None = None

    hotel_preference: str | None = None

    food_preference: str | None = None

    @field_validator("additional_preferences", mode="before")
    @classmethod
    def normalize_preferences(cls, value):
        return _empty_list_if_null(value)

    @field_validator("transport_preference", mode="before")
    @classmethod
    def normalize_transport(cls, value):
        if value is None:
            return None

        value = value.lower().strip()

        mapping = {
            "flight": "flight",
            "flights": "flight",
            "plane": "flight",
            "planes": "flight",
            "train": "train",
            "trains": "train",
            "bus": "bus",
            "buses": "bus",
            "car": "car",
            "cars": "car",
            "any": "any",
        }

        return mapping.get(value, value)

    @field_validator("hotel_preference", mode="before")
    @classmethod
    def normalize_hotel(cls, value):
        if value is None:
            return None

        value = value.lower().strip()

        mapping = {
            "budget": "budget",
            "budget hotel": "budget",
            "cheap": "budget",
            "mid range": "mid-range",
            "mid-range": "mid-range",
            "3 star": "mid-range",
            "3 stars": "mid-range",
            "4 star": "mid-range",
            "4 stars": "mid-range",
            "luxury": "luxury",
            "luxury hotel": "luxury",
            "5 star": "luxury",
            "5 stars": "luxury",
            "hostel": "hostel",
            "any": "any",
        }

        return mapping.get(value, value)
