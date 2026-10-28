import math
import re

from app.models.cost_estimation import CostEstimation


class CostEstimationAgent:
    def _extract_average(self, value: str | None) -> float | None:
        if not value or value.lower() in {"not available", "n/a", "none", "null"}:
            return None

        numbers = [
            float(number)
            for number in re.findall(r"\d+(?:\.\d+)?", str(value))
        ]
        if not numbers:
            return None

        return sum(numbers) / len(numbers)

    def _money(self, value: float | None, currency: str) -> str:
        if value is None:
            return "Not available"
        return f"{currency} {value:,.0f}"

    def _room_count(self, travelers: int, hotel_preference: str | None) -> int:
        if travelers <= 0:
            return 1
        if (hotel_preference or "").lower() == "hostel":
            return travelers
        return math.ceil(travelers / 2)

    def run(
        self,
        requirements: dict,
        research_summary: dict | None = None,
    ) -> dict:
        research_summary = research_summary or {}
        currency = (requirements.get("budget_currency") or "USD").upper()
        days = int(requirements.get("days") or 0)
        travelers = int(requirements.get("travelers") or 0)
        budget = requirements.get("budget")
        hotel_preference = requirements.get("hotel_preference")

        warnings: list[str] = []
        missing: list[str] = []
        assumptions = [
            "Price ranges from research were averaged.",
            "Long-distance tickets (flights/trains) are not live booking prices.",
        ]

        hotel_per_night = self._extract_average(
            research_summary.get("estimated_hotel_cost_per_night")
        )
        food_per_day = self._extract_average(
            research_summary.get("estimated_food_cost_per_day")
        )
        transport_per_day = self._extract_average(
            research_summary.get("estimated_local_transport_cost_per_day")
        )
        daily_budget = self._extract_average(
            research_summary.get("estimated_daily_budget")
        )

        rooms = self._room_count(travelers, hotel_preference) if travelers else None

        if hotel_per_night is None:
            missing.append("hotel")
        if food_per_day is None:
            missing.append("food")
        if transport_per_day is None:
            missing.append("local transport")

        hotel_cost = (
            hotel_per_night * days * rooms
            if hotel_per_night and days and rooms
            else None
        )
        food_cost = (
            food_per_day * days * travelers
            if food_per_day and days and travelers
            else None
        )
        transport_cost = (
            transport_per_day * days * travelers
            if transport_per_day and days and travelers
            else None
        )

        activity_per_day = None
        activity_cost = None
        if daily_budget and days and travelers:
            implied_activity = daily_budget - sum(
                part for part in [
                    hotel_per_night / travelers if hotel_per_night and travelers else 0,
                    food_per_day or 0,
                    transport_per_day or 0,
                ]
            )
            if implied_activity > 0:
                activity_per_day = implied_activity
                activity_cost = implied_activity * days * travelers
                assumptions.append(
                    "Activity cost was inferred from estimated daily budget minus known daily costs."
                )

        if hotel_preference == "hostel":
            assumptions.append("Hostel stay assumed as one bed per traveler.")
        elif rooms:
            assumptions.append(f"Hotel rooms estimated as {rooms} for {travelers} traveler(s).")

        known_costs = [
            value
            for value in [hotel_cost, food_cost, transport_cost, activity_cost]
            if value is not None
        ]
        total_cost = sum(known_costs) if known_costs else None

        if missing:
            warnings.append(
                "Incomplete research prices for: " + ", ".join(missing) + "."
            )
            assumptions.append(
                "Missing categories were left as Not available instead of inventing numbers."
            )

        if total_cost is None or budget is None:
            budget_status = "Cannot determine"
            warnings.append(
                "Budget status needs both a user budget and at least one researched cost."
            )
        elif total_cost <= float(budget):
            remaining = float(budget) - total_cost
            budget_status = f"Within budget ({currency} {remaining:,.0f} remaining)"
        else:
            over = total_cost - float(budget)
            budget_status = f"Over budget by {currency} {over:,.0f}"

        if total_cost is not None:
            assumptions.append(
                "Total excludes live international transport fares unless present in research."
            )

        estimate = CostEstimation(
            currency=currency,
            hotel_rooms=rooms,
            hotel_per_night=hotel_per_night,
            food_per_day=food_per_day,
            transport_per_day=transport_per_day,
            activity_per_day=activity_per_day,
            transport_cost=transport_cost,
            hotel_cost=hotel_cost,
            food_cost=food_cost,
            activity_cost=activity_cost,
            total_estimated_cost=total_cost,
            user_budget=float(budget) if budget is not None else None,
            transport_cost_display=self._money(transport_cost, currency),
            hotel_cost_display=self._money(hotel_cost, currency),
            food_cost_display=self._money(food_cost, currency),
            activity_cost_display=self._money(activity_cost, currency),
            total_estimated_cost_display=self._money(total_cost, currency),
            budget_status=budget_status,
            assumptions=assumptions,
            warnings=warnings,
            missing_cost_inputs=missing,
        )
        return estimate.model_dump()

    def apply_to_plan(self, plan: dict, cost_estimate: dict | None) -> dict:
        if not cost_estimate:
            return plan

        plan["transport_budget"] = cost_estimate.get(
            "transport_cost_display", "Not available"
        )
        plan["hotel_budget"] = cost_estimate.get(
            "hotel_cost_display", "Not available"
        )
        plan["food_budget"] = cost_estimate.get(
            "food_cost_display", "Not available"
        )
        plan["activity_budget"] = cost_estimate.get(
            "activity_cost_display", "Not available"
        )
        plan["total_estimated_budget"] = cost_estimate.get(
            "total_estimated_cost_display", "Not available"
        )
        plan["budget_status"] = cost_estimate.get(
            "budget_status", "Cannot determine"
        )

        notes = []
        if cost_estimate.get("assumptions"):
            notes.extend(cost_estimate["assumptions"])
        if cost_estimate.get("warnings"):
            notes.extend(cost_estimate["warnings"])
        plan["budget_notes"] = "\n".join(f"- {note}" for note in notes)
        return plan
