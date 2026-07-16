import re


class CostEstimationAgent:

    def _extract_average(self, value: str | None):

        if not value:
            return None

        numbers = re.findall(r"\d+(?:\.\d+)?", value)

        if not numbers:
            return None

        values = [float(number) for number in numbers]

        return sum(values) / len(values)

    def run(
        self,
        requirements: dict,
        research_summary: dict,
    ):

        days = requirements["days"]
        travelers = requirements["travelers"]
        budget = requirements["budget"]

        hotel_per_night = self._extract_average(
            research_summary.get(
                "estimated_hotel_cost_per_night"
            )
        )

        food_per_day = self._extract_average(
            research_summary.get(
                "estimated_food_cost_per_day"
            )
        )

        transport_per_day = self._extract_average(
            research_summary.get(
                "estimated_local_transport_cost_per_day"
            )
        )

        hotel_cost = (
            hotel_per_night * days
            if hotel_per_night
            else None
        )

        food_cost = (
            food_per_day * days * travelers
            if food_per_day
            else None
        )

        transport_cost = (
            transport_per_day * days * travelers
            if transport_per_day
            else None
        )

        activity_cost = None

        known_costs = [
            value
            for value in [
                hotel_cost,
                food_cost,
                transport_cost,
            ]
            if value is not None
        ]

        total_cost = (
            sum(known_costs)
            if known_costs
            else None
        )

        if total_cost is None:

            budget_status = "Unable to estimate."

        elif total_cost <= budget:

            budget_status = "Within budget."

        else:

            budget_status = "Over budget."

        return {

            "transport_cost": transport_cost,

            "hotel_cost": hotel_cost,

            "food_cost": food_cost,

            "activity_cost": activity_cost,

            "total_estimated_cost": total_cost,

            "budget_status": budget_status,

            "assumptions": [
                "Average values were used for price ranges.",
                "Flight, train and hotel live prices were unavailable.",
                "Activity costs were unavailable."
            ]
        }