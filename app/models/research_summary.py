from pydantic import BaseModel, Field


class ResearchSummary(BaseModel):
    must_visit_places: list[str] = Field(
        description="Most important places tourists should visit."
    )

    best_time: str = Field(
        description="Best season or months to visit."
    )

    travel_tips: list[str] = Field(
        description="Important travel advice."
    )

    local_transport: str = Field(
        description="How tourists should travel locally."
    )

    food_to_try: list[str] = Field(
        description="Popular local foods."
    )