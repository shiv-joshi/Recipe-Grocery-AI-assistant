from recipe_agent import build_recipe_agent
from grocery_agent import build_grocery_agent, get_raw_shopping_list, clear_shopping_list
from models import Context, RecipeResponse, GroceryResponse

def run():
    print("\n🍳  Recipe & Grocery Assistant  (type 'quit' to exit)\n")

    user_id = "1"
    context = Context(user_id=user_id)

    # Each agent gets its own config + thread so their memories are independent
    recipe_config = {"configurable": {"thread_id": f"recipe-session-{user_id}"}}
    grocery_config = {"configurable": {"thread_id": f"grocery-session-{user_id}"}}

    recipe_agent = build_recipe_agent()
    grocery_agent = build_grocery_agent()

    while True:
        user_input = input("What recipe are you looking for? (or 'done' to see your list / 'quit' to exit)\n> ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            _print_final_list(user_id)
            print("\nHappy cooking! 👋")
            break

        if user_input.lower() == "done":
            _print_final_list(user_id)
            clear_shopping_list(user_id)
            print("Shopping list cleared. Start fresh anytime! 👋\n")
            break

        if not user_input:
            continue

        # Find recipe
        print("\n⏳  Finding a recipe...\n")
        recipe_response = recipe_agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=recipe_config,
            context=context,
        )
        recipe_result: RecipeResponse = recipe_response["structured_response"]

        print("\n" + "─" * 60)
        print(recipe_result.recipe_presentation)
        if recipe_result.cooking_tip:
            print(f"\n💡 Tip: {recipe_result.cooking_tip}")
        print("─" * 60 + "\n")

        # Ask if the user wants to make it
        follow_up = input("Would you like to make this? (yes / no)\n> ").strip().lower()

        if follow_up not in ("yes", "y"):
            print("\nNo problem! Ask me for another recipe anytime.\n")
            continue

        # Handoff ingredients to the Grocery Agent 
        if not recipe_result.ingredients:
            print("\n⚠️  Couldn't extract ingredients from this recipe.\n")
            continue

        print("\n🛒  Updating your shopping list...\n")
        grocery_response = grocery_agent.invoke(
            {
                "messages": [{
                    "role": "user",
                    "content": (
                        f"I want to make {recipe_result.recipe_title}. "
                        f"Please add these ingredients to my shopping list: "
                        f"{recipe_result.ingredients}"
                    ),
                }]
            },
            config=grocery_config,
            context=context,
        )
        grocery_result: GroceryResponse = grocery_response["structured_response"]

        print(grocery_result.message)
        print("─" * 60 + "\n")

def _print_final_list(user_id: str):
    """Print the full shopping list directly from the store."""
    items = get_raw_shopping_list(user_id)
    print("\n" + "=" * 60)
    print("🛒  YOUR SHOPPING LIST")
    print("=" * 60)
    if items:
        for item in items:
            print(f"  • {item}")
    else:
        print("  Nothing added yet.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run()