from pydantic import BaseModel, Field


class CostEstimation(BaseModel):
    currency: str = "USD"

    hotel_rooms: int | None = None
    hotel_per_night: float | None = None
    food_per_day: float | None = None
    transport_per_day: float | None = None
    activity_per_day: float | None = None

    transport_cost: float | None = None
    hotel_cost: float | None = None
    food_cost: float | None = None
    activity_cost: float | None = None
    total_estimated_cost: float | None = None
    user_budget: float | None = None

    transport_cost_display: str = "Not available"
    hotel_cost_display: str = "Not available"
    food_cost_display: str = "Not available"
    activity_cost_display: str = "Not available"
    total_estimated_cost_display: str = "Not available"

    budget_status: str = "Cannot determine"
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    missing_cost_inputs: list[str] = Field(default_factory=list)
