import re

from app.config.llm import llm
from app.models.travel_models import TravelRequirements
from app.utils.resilience import invoke_with_retry

structured_llm = llm.with_structured_output(
    TravelRequirements,
    method="json_mode",
)

REQUIRED_FIELDS = (
    "destination",
    "origin",
    "budget",
    "budget_currency",
    "days",
    "travelers",
)

PREFERENCE_DEFAULTS = {
    "transport_preference": "any",
    "hotel_preference": "any",
    "food_preference": "any",
}

CURRENCY_ALIASES = {
    "usd": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "$": "USD",
    "inr": "INR",
    "rs": "INR",
    "rupee": "INR",
    "rupees": "INR",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "gbp": "GBP",
    "pound": "GBP",
    "pounds": "GBP",
}

SKIP_WORDS = {
    "plan", "trip", "travel", "budget", "duration", "days", "day",
    "person", "people", "travelers", "travellers", "city", "from",
    "to", "for", "and", "the", "a", "in", "is", "of", "my", "our",
}


def _clean_place(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"[^A-Za-z\s]", "", value).strip()
    if not value or value.lower() in SKIP_WORDS:
        return None
    return value.title()


def _merge_requirements(*sources: dict | None) -> dict:
    merged = TravelRequirements().model_dump()
    preferences: list[str] = []

    for source in sources:
        if not source:
            continue
        for key, value in source.items():
            if value in (None, "", []):
                continue
            if key == "additional_preferences":
                for item in value:
                    if item and item not in preferences:
                        preferences.append(item)
                continue
            merged[key] = value

    merged["additional_preferences"] = preferences
    return merged


def extract_from_text(text: str) -> dict:
    extracted: dict = {}
    if not text:
        return extracted

    origin_match = re.search(
        r"(?:from|origin|leaving|dep[a-z]*\s*(?:city)?)\s*(?:is|:)?\s*([A-Za-z]+)",
        text,
        re.I,
    )
    if origin_match:
        extracted["origin"] = _clean_place(origin_match.group(1))

    dest_match = re.search(
        r"(?:\bto\b|destination|visit(?:ing)?|going to)\s+(?:is\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)?)",
        text,
        re.I,
    )
    if dest_match:
        extracted["destination"] = _clean_place(dest_match.group(1))

    budget_match = re.search(
        r"(?:budget(?:\s*(?:is|of|:))?|cost)\s*\$?\s*(\d+(?:\.\d+)?)",
        text,
        re.I,
    ) or re.search(r"\$\s*(\d+(?:\.\d+)?)", text)
    if budget_match:
        extracted["budget"] = float(budget_match.group(1))

    currency_match = re.search(
        r"\b(USD|INR|EUR|GBP|dollars?|rupees?|euros?|pounds?|rs)\b",
        text,
        re.I,
    )
    if currency_match:
        extracted["budget_currency"] = CURRENCY_ALIASES.get(
            currency_match.group(1).lower(),
            currency_match.group(1).upper(),
        )

    days_match = re.search(
        r"(?:duration(?:\s+is)?\s*)?(\d+)\s*(?:-)?\s*days?",
        text,
        re.I,
    ) or re.search(r"duration(?:\s+is)?\s*(\d+)", text, re.I)
    if days_match:
        extracted["days"] = int(days_match.group(1))

    travelers_match = re.search(
        r"(\d+)\s*(?:people|persons?|travelers?|travellers?|pax)",
        text,
        re.I,
    ) or re.search(r"for\s+(\d+)", text, re.I)
    if travelers_match:
        extracted["travelers"] = int(travelers_match.group(1))

    if "destination" not in extracted:
        said_match = re.search(
            r"(?:said|going to|go to|visit(?:ing)?)\s+([A-Za-z]+)",
            text,
            re.I,
        )
        if said_match:
            extracted["destination"] = _clean_place(said_match.group(1))

    if "destination" not in extracted:
        filler = SKIP_WORDS | {"i", "said", "want", "go", "going", "please", "plan"}
        for line in text.splitlines():
            line = line.strip()
            if not line or re.search(r"\d", line):
                continue
            if re.search(r"dep[a-z]*|from|origin|budget|duration", line, re.I):
                continue
            tokens = [
                token.strip(".,!")
                for token in line.split()
                if token.lower().strip(".,!") not in filler
            ]
            if len(tokens) == 1:
                place = _clean_place(tokens[0])
                if place and place.lower() != (extracted.get("origin") or "").lower():
                    extracted["destination"] = place
                    break

    return extracted


class RequirementAgent:
    def _extract_with_llm(self, user_query: str) -> dict:
        prompt = f"""
Extract travel requirements from the full conversation below.
The user may give details across multiple short messages.
Combine ALL details. Do not drop information that was mentioned earlier.

Conversation:
{user_query}

Rules:
- destination: country or city they want to visit (example: Japan)
- origin: departure city (example: Delhi). "departed/deprted/departure city" means origin.
- budget: numeric amount only
- budget_currency: USD, INR, EUR, etc. "dollars" means USD
- days: trip length
- travelers: number of people
- If a field is not mentioned anywhere, leave it null
- additional_preferences must always be an array
"""
        result = invoke_with_retry(structured_llm, prompt)
        return result.model_dump()

    def run(self, user_query: str, previous: dict | None = None) -> dict:
        heuristic = extract_from_text(user_query)

        try:
            llm_result = self._extract_with_llm(user_query)
        except Exception:
            llm_result = {}

        requirements = _merge_requirements(previous, llm_result, heuristic)

        for field, default in PREFERENCE_DEFAULTS.items():
            if not requirements.get(field):
                requirements[field] = default

        missing_fields = [
            field
            for field in REQUIRED_FIELDS
            if requirements.get(field) in (None, "", [])
        ]

        return {
            "requirements": requirements,
            "missing_fields": missing_fields,
        }
