import streamlit as st
from recipe_agent import build_recipe_agent
from grocery_agent import build_grocery_agent, get_raw_shopping_list, clear_shopping_list
from models import Context, RecipeResponse, GroceryResponse

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Recipe Assistant",
    page_icon="🍳",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #FAFAF7;
    color: #1C1C1A;
}

.stApp {
    background-color: #FAFAF7;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Page title */
.app-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #1C1C1A;
    letter-spacing: -0.5px;
    margin-bottom: 0.1rem;
}
.app-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    color: #888880;
    margin-bottom: 2rem;
    font-weight: 300;
}

/* Recipe card */
.recipe-card {
    background: #FFFFFF;
    border: 1px solid #E8E8E2;
    border-radius: 16px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.recipe-card-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 600;
    color: #1C1C1A;
    margin-bottom: 0.3rem;
}
.recipe-meta {
    display: flex;
    gap: 1.2rem;
    margin-bottom: 1.2rem;
    flex-wrap: wrap;
}
.meta-pill {
    background: #F2F2EC;
    border-radius: 20px;
    padding: 0.25rem 0.8rem;
    font-size: 0.82rem;
    color: #555550;
    font-weight: 500;
}
.meta-pill span {
    color: #C17F3A;
    font-weight: 600;
}
.section-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #AAAAAA;
    margin-bottom: 0.6rem;
    margin-top: 1.2rem;
}
.step-row {
    display: flex;
    gap: 0.9rem;
    margin-bottom: 0.7rem;
    align-items: flex-start;
}
.step-num {
    background: #C17F3A;
    color: white;
    border-radius: 50%;
    min-width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 700;
    margin-top: 1px;
}
.step-text {
    font-size: 0.92rem;
    line-height: 1.6;
    color: #333330;
}
.ingredient-tag {
    display: inline-block;
    background: #FBF6EF;
    border: 1px solid #EDD9B8;
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    font-size: 0.82rem;
    color: #7A5C2E;
    margin: 0.2rem 0.2rem 0.2rem 0;
}
.tip-box {
    background: #FBF6EF;
    border-left: 3px solid #C17F3A;
    border-radius: 0 8px 8px 0;
    padding: 0.7rem 1rem;
    margin-top: 1rem;
    font-size: 0.88rem;
    color: #7A5C2E;
}

/* User message bubble */
.user-bubble {
    background: #1C1C1A;
    color: #FAFAF7;
    border-radius: 18px 18px 4px 18px;
    padding: 0.7rem 1.1rem;
    font-size: 0.92rem;
    display: inline-block;
    max-width: 75%;
    float: right;
    clear: both;
    margin-bottom: 1rem;
    font-family: 'DM Sans', sans-serif;
}
.bubble-wrap { overflow: hidden; margin-bottom: 0.5rem; }

/* Grocery list */
.grocery-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-weight: 600;
    color: #1C1C1A;
    margin-bottom: 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #E8E8E2;
}
.grocery-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.45rem 0;
    border-bottom: 1px solid #F0F0EA;
    font-size: 0.9rem;
    color: #333330;
}
.grocery-dot {
    width: 8px;
    height: 8px;
    background: #C17F3A;
    border-radius: 50%;
    flex-shrink: 0;
}
.grocery-empty {
    font-size: 0.88rem;
    color: #AAAAAA;
    font-style: italic;
    padding: 0.5rem 0;
}
.divider {
    border: none;
    border-top: 2px dashed #E8E8E2;
    margin: 2rem 0;
}

/* Confirm buttons */
div.stButton > button {
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 0.88rem;
    padding: 0.4rem 1.2rem;
    border: 1.5px solid #1C1C1A;
    background: transparent;
    color: #1C1C1A;
    transition: all 0.15s;
}
div.stButton > button:hover {
    background: #1C1C1A;
    color: #FAFAF7;
}
</style>
""", unsafe_allow_html=True)

# ── Fresh start on each new browser session ────────────────────────────────

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.recipe_agent = build_recipe_agent()
    st.session_state.grocery_agent = build_grocery_agent()
    st.session_state.chat_history = []
    st.session_state.pending_recipe = None
    st.session_state.user_id = "1"
    clear_shopping_list("1")

USER_ID = st.session_state.user_id
recipe_config = {"configurable": {"thread_id": f"recipe-session-{USER_ID}"}}
grocery_config = {"configurable": {"thread_id": f"grocery-session-{USER_ID}"}}
context = Context(user_id=USER_ID)

# ── Header ─────────────────────────────────────────────────────────────────────

st.markdown('<div class="app-title">🍳 Recipe Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Ask for any recipe. Build your grocery list as you go.</div>', unsafe_allow_html=True)

# ── Chat history ───────────────────────────────────────────────────────────────

for entry in st.session_state.chat_history:

    if entry["type"] == "user":
        st.markdown(f'<div class="bubble-wrap"><div class="user-bubble">{entry["content"]}</div></div>', unsafe_allow_html=True)

    elif entry["type"] == "recipe":
        r: RecipeResponse = entry["content"]
        card = f"""
        <div class="recipe-card">
            <div class="recipe-card-title">{r.recipe_title}</div>
            <div class="recipe-meta">
                {f'<div class="meta-pill">⏱ <span>{entry["meta"]["time"]} min</span></div>' if entry["meta"].get("time") else ""}
                {f'<div class="meta-pill">🍽 <span>{entry["meta"]["servings"]} servings</span></div>' if entry["meta"].get("servings") else ""}
                {f'<div class="meta-pill">🔥 <span>{entry["meta"]["calories"]} kcal</span></div>' if entry["meta"].get("calories") else ""}
                {f'<div class="meta-pill">💪 <span>{entry["meta"]["protein"]}g protein</span></div>' if entry["meta"].get("protein") else ""}
            </div>
        """
        if r.ingredients:
            card += '<div class="section-label">Ingredients</div>'
            card += "".join(f'<span class="ingredient-tag">{i}</span>' for i in r.ingredients)

        # Parse steps out of recipe_presentation
        if "1." in r.recipe_presentation:
            card += '<div class="section-label">Steps</div>'
            lines = r.recipe_presentation.split("\n")
            for line in lines:
                line = line.strip()
                if line and line[0].isdigit() and "." in line[:3]:
                    num, _, text = line.partition(".")
                    card += f'''
                    <div class="step-row">
                        <div class="step-num">{num.strip()}</div>
                        <div class="step-text">{text.strip()}</div>
                    </div>'''

        if r.cooking_tip:
            card += f'<div class="tip-box">💡 {r.cooking_tip}</div>'

        card += "</div>"
        st.markdown(card, unsafe_allow_html=True)

    elif entry["type"] == "grocery_confirm":
        st.markdown(f'<div style="font-size:0.88rem; color:#888880; margin-bottom:0.8rem;">✅ {entry["content"]}</div>', unsafe_allow_html=True)

# ── Pending yes/no confirmation ────────────────────────────────────────────────

if st.session_state.pending_recipe is not None:
    st.markdown("**Would you like to make this recipe?**")
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Yes, add to list"):
            recipe: RecipeResponse = st.session_state.pending_recipe
            grocery_response = st.session_state.grocery_agent.invoke(
                {"messages": [{"role": "user", "content": (
                    f"I want to make {recipe.recipe_title}. "
                    f"Please add these ingredients to my shopping list: {recipe.ingredients}"
                )}]},
                config=grocery_config,
                context=context,
            )
            g: GroceryResponse = grocery_response["structured_response"]
            st.session_state.chat_history.append({
                "type": "grocery_confirm",
                "content": f"Added {len(g.items_added)} ingredients for {recipe.recipe_title} to your list."
            })
            st.session_state.pending_recipe = None
            st.rerun()
    with col2:
        if st.button("No thanks"):
            st.session_state.pending_recipe = None
            st.rerun()

# ── Input bar ──────────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
with st.form("recipe_form", clear_on_submit=True):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            "recipe_input",
            placeholder="e.g. 'spicy chicken under 600 calories'",
            label_visibility="collapsed",
        )
    with col_btn:
        submitted = st.form_submit_button("Search")

if submitted and user_input.strip():
    st.session_state.chat_history.append({"type": "user", "content": user_input.strip()})

    with st.spinner("Finding a recipe..."):
        response = st.session_state.recipe_agent.invoke(
            {"messages": [{"role": "user", "content": user_input.strip()}]},
            config=recipe_config,
            context=context,
        )
    result: RecipeResponse = response["structured_response"]

    # Extract meta from recipe_presentation for the card pills
    meta = {}
    for line in result.recipe_presentation.split("\n"):
        l = line.lower()
        if "min" in l and any(c.isdigit() for c in l):
            import re
            nums = re.findall(r'\d+', l)
            if nums:
                meta["time"] = nums[0]
        if "serving" in l and any(c.isdigit() for c in l):
            import re
            nums = re.findall(r'\d+', l)
            if nums:
                meta["servings"] = nums[0]
        if "calori" in l and any(c.isdigit() for c in l):
            import re
            nums = re.findall(r'[\d.]+', l)
            if nums:
                meta["calories"] = nums[0]
        if "protein" in l and any(c.isdigit() for c in l):
            import re
            nums = re.findall(r'[\d.]+', l)
            if nums:
                meta["protein"] = nums[0]

    st.session_state.chat_history.append({
        "type": "recipe",
        "content": result,
        "meta": meta,
    })
    st.session_state.pending_recipe = result
    st.rerun()

# ── Divider ────────────────────────────────────────────────────────────────────

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Grocery list ───────────────────────────────────────────────────────────────

grocery_col, clear_col = st.columns([4, 1])
with grocery_col:
    st.markdown('<div class="grocery-header">🛒 Shopping List</div>', unsafe_allow_html=True)
with clear_col:
    if st.button("Clear list"):
        clear_shopping_list(USER_ID)
        st.rerun()

items = get_raw_shopping_list(USER_ID)
if items:
    items_html = "".join(
        f'<div class="grocery-item"><div class="grocery-dot"></div>{item}</div>'
        for item in items
    )
    st.markdown(items_html, unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.8rem; color:#AAAAAA; margin-top:0.6rem;">{len(items)} items</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="grocery-empty">No items yet — search for a recipe and say yes to add ingredients.</div>', unsafe_allow_html=True)