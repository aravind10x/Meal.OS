"""Hindi Voice Script Generator — LLM-based conversational Hindi voice script.

Generates a natural, spoken-style Hindi voice script from an approved meal plan.
The script is intended to be sent as a WhatsApp voice note to the cook.

Architecture: Uses Azure OpenAI to generate the script, same pattern as ai_planner.py.
"""

import logging

from openai import AsyncAzureOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful assistant that generates Hindi voice scripts for a household cook.

You generate natural, conversational spoken-Hindi voice scripts for WhatsApp voice notes.
The cook understands Hindi and Bengali — use simple, everyday Hindi (not formal/literary).
The script should sound like someone naturally speaking to the cook, giving clear instructions.

IMPORTANT RULES:
- Use spoken Hindi (Romanized is fine in the output — the text will be converted to speech via TTS)
- Write in Devanagari Hindi script (not Romanized)
- Keep it concise but complete — target 30-60 seconds when spoken aloud
- Include: dish names, quantities, 2-3 critical steps per dish
- Include kid notes and leftover notes when present
- Start with a greeting like "नमस्ते!" or "सुनो,"
- Use a warm, friendly tone — like talking to someone you work with daily
- Don't say "aap" (formal) — use "tum" (informal) as is natural with household staff
- Mention the total egg count when eggs are included
- Always mention roti requirements
- Always mention salad (carrots + cucumber)
"""

USER_PROMPT_TEMPLATE = """Generate a Hindi voice script for tomorrow's meal plan:

DATE: {plan_date}
CUISINE: {cuisine}

MENU:
{menu_section}

ROTI: {roti_count}
EGGS: {egg_style} (5 total)
CURD RICE: {curd_rice}
SALAD: Carrots + Cucumber (daily)

{leftover_section}

{kid_section}

RECIPE DETAILS (for critical steps):
{recipe_details}

Generate a natural Hindi voice script (in Devanagari) that the cook can listen to as a voice note.
Keep it 30-60 seconds when spoken. Be specific about quantities and critical steps."""


def _build_voice_script_prompt(
    plan: dict,
    recipes: dict[str, dict],
    leftovers: list[dict] | None = None,
) -> str:
    """Build the user prompt for Hindi voice script generation.

    Args:
        plan: Approved meal plan dict.
        recipes: Dict of recipe_id -> recipe data.
        leftovers: Active leftovers if any.

    Returns:
        The formatted user prompt string.
    """
    dishes = plan.get("dishes", [])
    plan_date = plan.get("plan_date", "tomorrow")
    cuisine = plan.get("cuisine", "")
    egg_style = plan.get("egg_style", "boiled")
    roti_count = plan.get("roti_count", "standard batch")
    kid_notes = plan.get("kid_notes", "")
    include_curd_rice = plan.get("include_curd_rice_side", False)

    # Menu section
    menu_lines = []
    for dish in dishes:
        role = dish.get("role", "")
        name = dish.get("name", dish.get("recipe_id", "Unknown"))
        menu_lines.append(f"- {role}: {name}")
    menu_section = "\n".join(menu_lines) if menu_lines else "- No dishes specified"

    # Leftover section
    leftover_section = ""
    if leftovers:
        lo_lines = ["LEFTOVERS (mention to cook — no need to remake these):"]
        for lo in leftovers:
            dish_name = lo.get("dish_name", "Unknown")
            servings = lo.get("servings_estimate", "some")
            lo_lines.append(f"- {dish_name} ({servings} remaining)")
        leftover_section = "\n".join(lo_lines)
    else:
        leftover_section = "LEFTOVERS: None"

    # Kid section
    kid_section = ""
    if kid_notes:
        kid_section = f"KID NOTES (important — mention in script):\n{kid_notes}"
    else:
        kid_section = "KID NOTES: None specific today"

    # Recipe details for critical steps
    recipe_lines = []
    for dish in dishes:
        recipe_id = dish.get("recipe_id", "")
        recipe = recipes.get(recipe_id, {})
        if not recipe:
            continue

        name = recipe.get("name", recipe_id)
        critical_notes = recipe.get("critical_notes", "")
        ingredients = recipe.get("ingredients", [])
        steps = recipe.get("steps", [])
        kid_adapt = recipe.get("kid_adaptation", "")

        recipe_lines.append(f"\n{name}:")
        if ingredients:
            ing_text = ", ".join(
                f"{i.get('name', '')} ({i.get('quantity', '')})"
                for i in ingredients[:5]
            )
            recipe_lines.append(f"  Ingredients: {ing_text}")
        if critical_notes:
            recipe_lines.append(f"  Critical: {critical_notes}")

        # Include 2-3 critical/important steps
        critical_steps = [s for s in steps if s.get("is_critical")]
        if critical_steps:
            for s in critical_steps[:3]:
                recipe_lines.append(f"  Step: {s.get('instruction', '')}")
        elif steps:
            for s in steps[:2]:
                recipe_lines.append(f"  Step: {s.get('instruction', '')}")

        if kid_adapt:
            recipe_lines.append(f"  Kid note: {kid_adapt}")

    recipe_details = "\n".join(recipe_lines) if recipe_lines else "No recipe details"

    curd_rice = "Yes (optional side)" if include_curd_rice else "No"

    return USER_PROMPT_TEMPLATE.format(
        plan_date=plan_date,
        cuisine=cuisine,
        menu_section=menu_section,
        roti_count=roti_count,
        egg_style=egg_style,
        curd_rice=curd_rice,
        leftover_section=leftover_section,
        kid_section=kid_section,
        recipe_details=recipe_details,
    )


async def generate_voice_script(
    plan: dict,
    recipes: dict[str, dict],
    leftovers: list[dict] | None = None,
) -> str:
    """Generate a Hindi voice script using Azure OpenAI.

    Args:
        plan: Approved meal plan dict.
        recipes: Dict of recipe_id -> recipe data.
        leftovers: Active leftovers if any.

    Returns:
        Hindi voice script text (Devanagari).
    """
    user_prompt = _build_voice_script_prompt(plan, recipes, leftovers=leftovers)

    try:
        client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )

        response = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_completion_tokens=1000,
        )

        script_text = response.choices[0].message.content or ""
        return script_text.strip()
    except Exception as e:
        logger.error(f"Voice script generation failed: {e}")
        raise
