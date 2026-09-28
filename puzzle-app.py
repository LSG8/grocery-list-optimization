import itertools
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Beat the Greedy Shopper", layout="centered")

ITEMS = [
    ("Olive oil", 6, 1.0, 4),
    ("Milk", 1, 0.5, 2),
    ("Chicken", 6, 1.0, 9),
    ("Cereal", 4, 0.5, 8),
    ("Eggs", 3, 0.5, 7),
    ("Rice", 3, 1.0, 6),
    ("Pasta", 2, 0.5, 5),
    ("Detergent", 7, 2.0, 10),
    ("Fruit", 4, 1.0, 4),
]
NAMES = [i[0] for i in ITEMS]
INFO = {i[0]: i for i in ITEMS}
COST_LIMIT, WEIGHT_LIMIT = 20, 4.0

def totals(combination):
    cost = sum(INFO[n][1] for n in combination)
    weight = sum(INFO[n][2] for n in combination)
    urgency = sum(INFO[n][3] for n in combination)
    return cost, weight, urgency

def violations(combination):
    b = set(combination)
    cost, weight, _ = totals(b)
    problems = []
    if cost > COST_LIMIT:
        problems.append(f"Over budget: €{cost} > €{COST_LIMIT}")
    if weight > WEIGHT_LIMIT + 1e-9:
        problems.append(f"Too heavy: {weight:.1f} kg > {WEIGHT_LIMIT:.0f} kg")
    if "Cereal" in b and "Milk" not in b:
        problems.append("Cereal needs milk")
    if "Rice" in b and "Pasta" in b:
        problems.append("Rice and pasta can't both be bought")
    return problems


@st.cache_data
def brute_force_optimum():
    best, best_u = None, -1
    for mask in itertools.product([0, 1], repeat=len(NAMES)):
        combination = [n for n, m in zip(NAMES, mask) if m]
        if violations(combination):
            continue
        u = totals(combination)[2]
        if u > best_u:
            best, best_u = combination, u
    return best, best_u


def greedy_shopper():
    combination = []
    for name, *_ in sorted(ITEMS, key=lambda i: -i[3]):
        if name in combination:
            continue
        candidate = combination + [name]
        if name == "Cereal" and "Milk" not in combination:
            candidate.append("Milk")
        if not violations(candidate):
            combination = candidate
    return combination


GREEDY = greedy_shopper()
GREEDY_U = totals(GREEDY)[2]
OPT, OPT_U = brute_force_optimum()

# ---------------- State ----------------
st.session_state.setdefault("tries", 0)
st.session_state.setdefault("revealed", False)
st.session_state.setdefault("editor_version", 0)

# ---------------- Page ----------------
# Extra contrast: darker captions, bolder metrics
st.markdown(
    """
    <style>
    [data-testid="stCaptionContainer"], .stCaption { color: #000000 !important; }
    [data-testid="stMetricValue"] { font-weight: 700; color: #000000; }
    [data-testid="stMetricLabel"] p { color: #000000; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Beat the Greedy Shopper")
st.write(
    "A greedy shopper always grabs the most urgent item first. "
    "Can you build a better combination?"
)

st.markdown(
    f"""**Rules**
- Budget: **€{COST_LIMIT}**, carrying limit: **{WEIGHT_LIMIT:.0f} kg**
- Buying an item means buying exactly one unit
- Cereal needs milk
- Rice and pasta can't both be bought

**Goal:** maximize total urgency."""
)

st.info(
    f"The greedy shopper ends up with {', '.join(GREEDY)} - "
    f"urgency **{GREEDY_U}**. Can you beat it?"
)

st.subheader("Tick the items you want to buy")
table = pd.DataFrame(
    [(False, n, c, w, u) for n, c, w, u in ITEMS],
    columns=["Buy", "Item", "Cost (€)", "Weight (kg)", "Urgency"],
)
edited = st.data_editor(
    table,
    hide_index=True,
    width="stretch",
    row_height=26,
    height=(len(ITEMS) - 3) * 26,
    disabled=["Item", "Cost (€)", "Weight (kg)", "Urgency"],
    column_config={"Buy": st.column_config.CheckboxColumn("Buy")},
    key=f"editor_{st.session_state.editor_version}",
)
chosen = edited.loc[edited["Buy"], "Item"].tolist()

st.subheader("Your combination")
cost, weight, urgency = totals(chosen)
problems = violations(chosen)

m1, m2, m3 = st.columns(3)
m1.metric("Cost", f"€{cost} / {COST_LIMIT}")
m2.metric("Weight", f"{weight:.1f} / {WEIGHT_LIMIT:.0f} kg")
m3.metric("Urgency", urgency)

st.write("Selected: " + (", ".join(chosen) if chosen else "nothing yet"))

for p in problems:
    st.warning(p)

if st.button("Check my combination", type="primary"):
    st.session_state.tries += 1
    if not chosen:
        st.warning("Pick some items first.")
    elif problems:
        st.error("This combination breaks a rule. Fix it and try again.")
    elif urgency >= OPT_U:
        st.success(f"Optimal! Urgency {urgency}. You matched the best possible combination.")
        st.balloons()
    elif urgency > GREEDY_U:
        st.success(f"Nice, {urgency} beats greedy ({GREEDY_U}). But a better combination exists. Keep going!")
    elif urgency == GREEDY_U:
        st.info(f"{urgency}: same as greedy. Can you do better?")
    else:
        st.error(f"{urgency} is below greedy ({GREEDY_U}). Try again.")

tries = st.session_state.tries
if tries >= 3:
    if st.button("Reveal the optimum"):
        st.session_state.revealed = True
else:
    st.caption(f"Reveal unlocks after 3 checks (tries so far: {tries}).")

if st.session_state.revealed:
    oc, ow, ou = totals(OPT)
    st.success(
        f"**Optimum:** {', '.join(OPT)} - urgency **{ou}** "
        f"(€{oc}, {ow:.1f} kg). Greedy got {GREEDY_U}."
    )