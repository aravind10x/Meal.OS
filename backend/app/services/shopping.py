"""Delta Shopping List Service — generates shopping list from approved plan.

Logic:
1. Extract all ingredients from the plan's recipes
2. Subtract vegetables marked as available
3. Subtract pantry staples
4. Categorize each ingredient: needed / likely_available / pantry_staple
5. Annotate with "for which dish"
"""


def generate_shopping_list(
    plan: dict,
    recipes: dict[str, dict],
    available_vegetables: list[str],
    pantry_staples: list[str],
) -> list[dict]:
    """Generate a delta shopping list from an approved meal plan.

    Args:
        plan: The approved plan dict with dishes list.
        recipes: Dict of recipe_id -> full recipe data.
        available_vegetables: Vegetables available (from check-in).
        pantry_staples: Pantry staples (assumed always stocked).

    Returns:
        List of shopping items, each: {name, quantity, category, for_dish}
        category is one of: "needed", "likely_available", "pantry_staple"
    """
    dishes = plan.get("dishes", [])

    # Normalize for case-insensitive matching
    available_lower = {v.lower() for v in available_vegetables}
    pantry_lower = {s.lower() for s in pantry_staples}

    items: list[dict] = []
    seen: dict[str, dict] = {}  # ingredient_name_lower -> item dict

    for dish in dishes:
        recipe_id = dish.get("recipe_id", "")
        dish_name = dish.get("name", recipe_id)
        recipe = recipes.get(recipe_id, {})

        if not recipe:
            continue

        ingredients = recipe.get("ingredients", [])
        for ing in ingredients:
            ing_name = ing.get("name", "")
            if not ing_name:
                continue

            ing_lower = ing_name.lower()
            quantity = ing.get("quantity", "")
            ing_category = ing.get("category", "pantry")

            # Determine shopping category
            if ing_lower in pantry_lower:
                shopping_category = "pantry_staple"
            elif ing_lower in available_lower:
                shopping_category = "likely_available"
            elif ing_category == "vegetable" and ing_lower in available_lower:
                shopping_category = "likely_available"
            else:
                shopping_category = "needed"

            # Merge with existing entry if same ingredient
            if ing_lower in seen:
                existing = seen[ing_lower]
                # Upgrade to "needed" if any reference needs it
                if shopping_category == "needed" and existing["category"] != "needed":
                    existing["category"] = "needed"
                # Append dish reference
                if dish_name not in existing["for_dish"]:
                    existing["for_dish"] += f", {dish_name}"
            else:
                item = {
                    "name": ing_name,
                    "quantity": quantity,
                    "category": shopping_category,
                    "for_dish": dish_name,
                }
                seen[ing_lower] = item
                items.append(item)

    # Sort: needed first, then likely_available, then pantry_staple
    category_order = {"needed": 0, "likely_available": 1, "pantry_staple": 2}
    items.sort(key=lambda x: (category_order.get(x["category"], 3), x["name"]))

    return items
