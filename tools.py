"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Matches case-insensitively against whole tokens only —
                     "M" matches "M" or "S/M" but not "XL" or "XS/S".
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts (each with id, title, description,
        category, style_tags, size, condition, price, colors, brand, platform),
        sorted best-match first, at most config.SEARCH_RESULT_LIMIT of them.
        Returns an empty list when nothing matches.
    """
    listings = load_listings()

    # --- price filter ---
    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    # --- size filter (whole-token match only) ---
    if size is not None:
        size_lower = size.lower().strip()

        def _size_matches(listing_size: str) -> bool:
            # Split the listing size into tokens, e.g. "S/M" → ["s", "m"]
            tokens = re.split(r"[/\s,]+", listing_size.lower())
            return size_lower in tokens

        listings = [l for l in listings if _size_matches(str(l.get("size", "")))]

    # --- keyword scoring ---
    if not description or not description.strip():
        return listings[: config.SEARCH_RESULT_LIMIT]

    keywords = re.sub(r"[^\w\s]", " ", description.lower()).split()

    def _score(listing: dict) -> int:
        # Build a searchable blob from every text field
        blob = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            " ".join(listing.get("style_tags", [])),
            listing.get("brand", "") or "",
        ]).lower()
        return sum(1 for kw in keywords if kw in blob)

    scored = [(l, _score(l)) for l in listings]
    scored = [(l, s) for l, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [l for l, _ in scored][: config.SEARCH_RESULT_LIMIT]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  May be empty.

    Returns:
        A non-empty string with outfit suggestions. If the wardrobe is empty,
        returns general styling advice for the item rather than failing.
    """
    title = new_item.get("title", "this item")
    description = new_item.get("description", "")
    category = new_item.get("category", "")
    style_tags = ", ".join(new_item.get("style_tags", []))
    colors = ", ".join(new_item.get("colors", []))

    item_summary = (
        f"Item: {title}\n"
        f"Category: {category}\n"
        f"Style tags: {style_tags}\n"
        f"Colors: {colors}\n"
        f"Description: {description}"
    )

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        prompt = (
            f"A thrift shopper is considering buying this item:\n\n"
            f"{item_summary}\n\n"
            f"They have no saved wardrobe. Suggest two general outfit ideas "
            f"that would work with this item, naming specific clothing types "
            f"and explaining the vibe. Keep it concise — two to four sentences."
        )
    else:
        wardrobe_text = "\n".join(
            f"- {w.get('name', 'unknown')} ({w.get('color', '')} {w.get('type', '')})"
            for w in wardrobe_items
        )
        prompt = (
            f"A thrift shopper is considering buying this item:\n\n"
            f"{item_summary}\n\n"
            f"Their current wardrobe includes:\n{wardrobe_text}\n\n"
            f"Suggest one or two specific outfits using pieces from their "
            f"wardrobe above. Name the exact pieces and explain why they work "
            f"together. Keep it concise — two to four sentences."
        )

    return generate(prompt)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption mentioning the item, its price, and its
        platform. Returns a descriptive message if outfit is empty/whitespace.
    """
    if not outfit or not outfit.strip():
        return "No outfit suggestion available — cannot generate a fit card."

    title = new_item.get("title", "this thrift find")
    raw_price = new_item.get("price", 0)
    # Format price cleanly: drop the decimal if it is a whole number
    # so $18.0 becomes $18, but $18.50 stays $18.50.
    if isinstance(raw_price, (int, float)) and float(raw_price) == int(float(raw_price)):
        price_str = f"${int(float(raw_price))}"
    else:
        price_str = f"${float(raw_price):.2f}"
    platform = new_item.get("platform", "a thrift platform")
    style_tags = ", ".join(new_item.get("style_tags", []))

    prompt = (
        f"Write a short social-media caption (2–4 sentences) for a thrift find.\n\n"
        f"Item: {title}\n"
        f"Price: {price_str}\n"
        f"Platform: {platform}\n"
        f"Vibe/style: {style_tags}\n\n"
        f"Outfit idea: {outfit}\n\n"
        f"The caption should sound like a real post — casual, enthusiastic, "
        f"specific about the vibe. Mention the item, its exact price ({price_str}), "
        f"and the platform once each. Do not use generic phrases like "
        f"'thrift find of the century'. Do not alter the price — use {price_str} exactly."
    )

    return generate(prompt)
