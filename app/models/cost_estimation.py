from pydantic import BaseModel, Field


class CostEstimation(BaseModel):

    transport_cost: str = Field(
        description="Estimated transportation cost."
    )

    hotel_cost: str = Field(
        description="Estimated accommodation cost."
    )

    food_cost: str = Field(
        description="Estimated food cost."
    )

    activity_cost: str = Field(
        description="Estimated sightseeing cost."
    )

    total_estimated_cost: str = Field(
        description="Estimated total trip cost."
    )

    budget_status: str = Field(
        description="Whether the trip is within the user's budget."
    )

    assumptions: list[str] = Field(
        description="Assumptions made while estimating costs."
    )