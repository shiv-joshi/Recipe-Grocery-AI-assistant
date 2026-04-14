from dataclasses import dataclass, field

@dataclass
class Context:
    """Runtime context passed to tools — shared across both agents."""
    user_id: str

@dataclass
class RecipeResponse:
    """Structured response schema for the recipe agent."""
    recipe_presentation: str
    recipe_title: str
    # Ingredient list extracted from the recipe — passed to grocery agent on handoff
    ingredients: list[str]
    asked_to_cook: bool
    cooking_tip: str | None = None

@dataclass
class GroceryResponse:
    """Structured response schema for the grocery agent."""
    # Conversational reply to show the user
    message: str
    # Full current shopping list after this update
    current_list: list[str]
    # Items just added in this turn
    items_added: list[str]