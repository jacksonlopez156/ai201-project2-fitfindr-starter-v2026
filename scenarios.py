"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it:

  1. A matching query completes all three tools → "matching query completes"
  2. An impossible query stops before the second tool → "impossible query stops early"
  3. State passes cleanly: selected_item matches what suggest_outfit received
     → any normal matching query works; what we check is the session
  4. The fit card mentions the item's price and platform every time
     → a matching query; run five times to get five real fit cards
  5. The empty-wardrobe path returns a non-empty outfit suggestion
     → a matching query with an empty wardrobe
"""

SCENARIOS = [
    {
        # Criterion 1: full three-tool run returns a fit card.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # Criterion 2: impossible query stops before suggest_outfit.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3: state passes cleanly — selected_item title appears in
        # the outfit suggestion string.
        "name": "state passes cleanly",
        "query": "90s track jacket",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4: fit card mentions the item's price and platform every
        # time.  Same query run 5 times to get 5 different model responses.
        "name": "fit card contains price and platform",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5: empty-wardrobe path returns a non-empty outfit
        # suggestion (at least 20 chars) and a non-empty fit card.
        "name": "empty wardrobe returns advice",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
