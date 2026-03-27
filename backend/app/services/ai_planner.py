"""AI Planner Service — generates meal plan candidates using Azure OpenAI.

Architecture: AI proposes → Rules Engine validates → User approves.
"""

import json
import logging
from datetime import date

from openai import AsyncAzureOpenAI

from app.config import settings
from app.services.rules_engine import validate_plan

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Meal.OS, a meal planning assistant for an Indian household.

HOUSEHOLD RULES (MUST follow):
- Vegetarian + eggs household
- Roti/chapati must be included every day
- 5 eggs daily across the household — rotate style: boiled, omelette, scrambled, fried
- Simple salad (carrots + cucumbers) daily — always included, no need to list as a dish
- Some household members prefer roti over rice by default
- An optional curd rice side may be added when appropriate
- On full-roti days, include extra rotis for the higher-appetite household member
- Include kid adaptation notes for lower-spice portions when relevant
- Cook arrives at 6 AM, understands Hindi and Bengali

MEAL TEMPLATES:
{templates}

RECIPE LIBRARY (available dishes):
{recipes}

RECENT MEAL HISTORY (last 14 days):
{history}

LAST EGG STYLES (last 4 days):
{egg_styles}
"""

USER_PROMPT = """Vegetables available tomorrow ({plan_date}): {vegetables}
Use soon (expiring): {use_soon}
Leftovers: {leftovers}

Generate exactly 3 diverse meal plan options for tomorrow. Each plan must:
1. Follow the correct meal template structure for its cuisine type
2. Use available vegetables (prefer "use soon" items)
3. Incorporate leftovers intelligently if any
4. Not repeat main dishes from last 3 days
5. Rotate egg style from recent days
6. Include kid adaptation notes
7. Provide a short rationale (why this plan)
8. List any ingredients that would need to be purchased (missing_ingredients)

Ensure diversity across the 3 options (different cuisines if possible).
Soft-prefer higher protein-tier dishes.

Return ONLY valid JSON in this exact format (no markdown, no code fences):
{{
  "plans": [
    {{
      "template_id": "south_indian",
      "cuisine": "South Indian",
      "dishes": [
        {{"recipe_id": "sambar", "role": "main", "name": "Sambar"}},
        {{"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"}}
      ],
      "egg_style": "omelette",
      "include_curd_rice_side": false,
      "roti_count": "standard batch",
      "kid_notes": "Set aside plain dal for kid before adding sambar masala",
      "rationale": "Uses drumstick (use soon). Pairs well with beans poriyal. Different from yesterday's North Indian.",
      "missing_ingredients": ["Drumstick"]
    }}
  ]
}}
"""


def _build_system_prompt(
    templates: list[dict],
    recipes: list[dict],
    history: list[dict],
) -> str:
    """Build the system prompt with context data."""
    # Extract last 4 egg styles
    egg_styles = []
    for h in history[:4]:
        if h.get("egg_style"):
            egg_styles.append(f"{h.get('date', '?')}: {h['egg_style']}")

    # Compact recipe info for the prompt
    recipe_summaries = []
    for r in recipes:
        tags = r.get("cuisine_tags", [])
        pairings = r.get("preferred_side_pairings", [])
        is_side = r.get("is_side_dish", False)
        recipe_summaries.append(
            f"- {r['id']}: {r['name']} | {'side' if is_side else 'main'} | "
            f"cuisine={','.join(tags)} | protein={r.get('protein_tier', '?')} | "
            f"familiarity={r.get('cook_familiarity', '?')} | "
            f"pairings={','.join(pairings) if pairings else 'none'}"
        )

    # Compact template info
    template_summaries = []
    for t in templates:
        template_summaries.append(
            f"- {t['id']}: {t['name']} | "
            f"required: {json.dumps(t.get('required_components', []))} | "
            f"roti_rules: {json.dumps(t.get('roti_rules', {}))}"
        )

    # Compact history
    history_summaries = []
    for h in history[:14]:
        dishes = h.get("dishes_cooked", [])
        history_summaries.append(
            f"- {h.get('date', '?')}: {', '.join(dishes)} "
            f"(egg: {h.get('egg_style', '?')}, cuisine: {h.get('cuisine', '?')})"
        )

    return SYSTEM_PROMPT.format(
        templates="\n".join(template_summaries) or "No templates loaded",
        recipes="\n".join(recipe_summaries) or "No recipes loaded",
        history="\n".join(history_summaries) or "No history yet",
        egg_styles="\n".join(egg_styles) or "No egg history yet",
    )


def _build_user_prompt(
    plan_date: date,
    vegetables: list[str],
    use_soon: list[str],
    leftovers: list[dict],
) -> str:
    """Build the user prompt with today's check-in data."""
    leftover_text = "None"
    if leftovers:
        leftover_items = []
        for lo in leftovers:
            leftover_items.append(
                f"{lo.get('dish_name', '?')} ({lo.get('servings_estimate', '?')})"
            )
        leftover_text = ", ".join(leftover_items)

    return USER_PROMPT.format(
        plan_date=plan_date.isoformat(),
        vegetables=", ".join(vegetables) if vegetables else "None specified",
        use_soon=", ".join(use_soon) if use_soon else "None",
        leftovers=leftover_text,
    )


def _parse_ai_response(response_text: str) -> list[dict]:
    """Parse the AI response JSON into a list of plan dicts.

    Handles potential markdown code fences and whitespace.
    """
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last line (```json and ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}\nResponse: {text[:500]}")
        raise ValueError(f"AI returned invalid JSON: {e}")

    if "plans" not in data:
        raise ValueError("AI response missing 'plans' array")
    plans = data["plans"]
    if not isinstance(plans, list):
        raise ValueError("AI response 'plans' must be an array")

    return plans


async def generate_meal_plans(
    plan_date: date,
    vegetables: list[str],
    use_soon: list[str],
    leftovers: list[dict],
    templates: list[dict],
    recipes: list[dict],
    history: list[dict],
) -> list[dict]:
    """Generate 2-3 meal plan candidates using Azure OpenAI.

    Args:
        plan_date: The date to plan for (tomorrow).
        vegetables: Available vegetables.
        use_soon: Vegetables to use soon (expiring).
        leftovers: Active leftovers.
        templates: Meal templates from DB.
        recipes: Recipe summaries from DB.
        history: Recent meal history (last 14 days).

    Returns:
        List of candidate plan dicts, each validated by the rules engine.
    """
    system_prompt = _build_system_prompt(templates, recipes, history)
    user_prompt = _build_user_prompt(plan_date, vegetables, use_soon, leftovers)

    try:
        client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )

        response = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_completion_tokens=2000,
            response_format={"type": "json_object"},
        )

        response_text = response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Azure OpenAI call failed: {e}")
        raise

    # Parse the AI response
    plans = _parse_ai_response(response_text)

    # Validate each plan with the rules engine
    validated_plans = []
    for plan in plans:
        validation = validate_plan(plan, meal_history=history)
        plan["validation"] = {
            "is_valid": validation.is_valid,
            "violations": validation.violations,
        }
        validated_plans.append(plan)

    return validated_plans
