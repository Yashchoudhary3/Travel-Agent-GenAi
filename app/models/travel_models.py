from typing import Optional

from pydantic import BaseModel


class TravelRequirements(BaseModel):
    destination: Optional[str] = None
    origin: Optional[str] = None
    budget: Optional[int] = None
    days: Optional[int] = None
    travelers: Optional[int] = None
    travel_style: Optional[str] = None

    additional_preferences: list[str] = []