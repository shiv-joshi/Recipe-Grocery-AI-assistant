from dataclasses import dataclass
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool, ToolRuntime
from langchain.agents.structured_output import ToolStrategy
from langgraph.checkpoint.memory import InMemorySaver
from models import Context, GroceryResponse

# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a helpful grocery assistant.
You manage a running shopping list across multiple recipes.
You have access to two tools:
- add_to_shopping_list: add ingredients to the shopping list
- get_shopping_list: retrieve the current shopping list

When given a list of ingredients:
1. Call get_shopping_list first to see what is already on the list
2. Clean each ingredient before adding it:
   - Keep only the quantity, unit, and ingredient name (e.g. "3 cups flour")
   - Strip all preparation instructions like "chopped", "grated", "divided", "minced", "sliced thinly", "plus more for rolling", "loosely packed", "at room temperature", etc.
   - Strip any parenthetical notes like "(may be omitted)" or "(optional)"
3. For any ingredient that already exists on the list, combine the quantities into a single entry using one consistent unit:
   - Convert all quantities to the same unit before combining (e.g. 2 tablespoons + 6 tablespoons = 1/2 cup)
   - Always convert to the larger unit when combining (e.g. tablespoons → cups, teaspoons → tablespoons)
   - The result should be a single clean entry like "3/4 cup olive oil", never "2 tablespoons + 3/4 cup olive oil"
4. Call add_to_shopping_list with only the resolved final ingredients
5. Confirm what was added and what was combined
"""

# ── In-memory shopping list store (key'd by user_id) ──────────────────────────────

_shopping_lists: dict[str, list[str]] = {}

# ── Tools ─────────────────────────────────────────────────────────────────────────

@tool
def add_to_shopping_list(ingredients: list[str], runtime: ToolRuntime[Context]) -> str:
    """Add a list of ingredients to the user's running shopping list.
    This tool does a simple append — all duplicate detection and quantity
    merging must be done by the agent BEFORE calling this tool.
    Each ingredient in the list should already be a fully resolved, combined entry."""
    user_id = runtime.context.user_id
    if user_id not in _shopping_lists:
        _shopping_lists[user_id] = []

    # Avoid exact duplicates
    existing = set(i.lower() for i in _shopping_lists[user_id])
    new_items = [i for i in ingredients if i.lower() not in existing]
    _shopping_lists[user_id].extend(new_items)

    return f"Added {len(new_items)} items. Skipped {len(ingredients) - len(new_items)} duplicates."

@tool
def get_shopping_list(runtime: ToolRuntime[Context]) -> str:
    """Retrieve the user's full current shopping list."""
    user_id = runtime.context.user_id
    items = _shopping_lists.get(user_id, [])
    if not items:
        return "The shopping list is currently empty."
    return "\n".join(f"- {item}" for item in items)

def get_raw_shopping_list(user_id: str) -> list[str]:
    """Helper for main.py to read the current list directly without invoking the agent."""
    return _shopping_lists.get(user_id, [])

def clear_shopping_list(user_id: str) -> None:
    """Helper for main.py to reset the list at the end of a session."""
    _shopping_lists[user_id] = []

# ── Agent builder ───────────────────────────────────────────────────────────────────
def build_grocery_agent():
    checkpointer = InMemorySaver()
    return create_agent(
        model=ChatGoogleGenerativeAI(model="gemini-2.5-pro"),
        system_prompt=SYSTEM_PROMPT,
        tools=[add_to_shopping_list, get_shopping_list],
        context_schema=Context,
        response_format=ToolStrategy(GroceryResponse),
        checkpointer=checkpointer,
    )