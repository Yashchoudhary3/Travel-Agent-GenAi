from pydantic import BaseModel
from typing import List


class ResearchData(BaseModel):
    destination: str

    recommended_places: List[str]

    best_time_to_visit: List[str]

    travel_highlights: List[str]