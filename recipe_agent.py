import os
import json
import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool, ToolRuntime
from langchain.agents.structured_output import ToolStrategy
from langgraph.checkpoint.memory import InMemorySaver

from models import Context, RecipeResponse

load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
SPOONACULAR_BASE_URL = "https://api.spoonacular.com"

# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a warm and enthusiastic cooking assistant.
You have access to two tools:
- search_recipe: find a recipe matching the user's request
- get_recipe_instructions: fetch step-by-step instructions using the recipe ID from search_recipe

When a user asks for a recipe:
1. Call search_recipe with their query
2. Call get_recipe_instructions with the returned recipe ID
3. Present the recipe clearly: title, prep time, servings, calories, protein, and numbered steps
4. Populate the ingredients field with a clean list of ingredient strings (e.g. "2 cups flour", "1 tsp salt")
"""

# ── Tools ───────────────────────────────────────────────────────────────────
@tool
def search_recipe(query: str, max_calories: int | None = None) -> str:
    """Search for a recipe by name or ingredients using the Spoonacular API.
    Optionally filter by maximum calories per serving."""
    url = f"{SPOONACULAR_BASE_URL}/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": query,
        "number": 1,
        "addRecipeInformation": True,
        "fillIngredients": True,
        "addRecipeNutrition": True,
    }
    if max_calories:
        params["maxCalories"] = max_calories

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if not data.get("results"):
        return json.dumps({"error": f"No recipes found for '{query}'."})

    recipe = data["results"][0]

    nutrients = recipe.get("nutrition", {}).get("nutrients", [])
    calories = next((n["amount"] for n in nutrients if n["name"] == "Calories"), None)
    protein = next((n["amount"] for n in nutrients if n["name"] == "Protein"), None)

    ingredients = [
        i.get("original", i.get("name", ""))
        for i in recipe.get("extendedIngredients", [])
    ]

    return json.dumps({
        "id": recipe["id"],
        "title": recipe["title"],
        "ready_in_minutes": recipe.get("readyInMinutes"),
        "servings": recipe.get("servings"),
        "calories_per_serving": calories,
        "protein_per_serving": protein,
        "ingredients": ingredients,
    })

@tool
def get_recipe_instructions(recipe_id: int, runtime: ToolRuntime[Context]) -> str:
    """Fetch step-by-step cooking instructions for a recipe given its ID."""
    url = f"{SPOONACULAR_BASE_URL}/recipes/{recipe_id}/analyzedInstructions"
    params = {"apiKey": SPOONACULAR_API_KEY}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if not data:
        return json.dumps({"error": "No instructions found for this recipe."})

    steps = [
        {"step_number": s["number"], "instruction": s["step"]}
        for s in data[0].get("steps", [])
    ]
    return json.dumps({"steps": steps})

# ── Agent builder ───────────────────────────────────────────────────────────────────
def build_recipe_agent():
    checkpointer = InMemorySaver()
    return create_agent(
        model=ChatGoogleGenerativeAI(model="gemini-2.5-flash"),
        system_prompt=SYSTEM_PROMPT,
        tools=[search_recipe, get_recipe_instructions],
        context_schema=Context,
        response_format=ToolStrategy(RecipeResponse),
        checkpointer=checkpointer,
    )