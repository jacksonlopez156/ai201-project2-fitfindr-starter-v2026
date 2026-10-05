"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── query parsing ─────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Parse a plain-language query into description, size, and max_price.

    Uses regex to extract size tokens (S, M, L, XL, XS, etc.) and price
    ceilings ($N or "under N"). Everything remaining is the description.

    Returns a dict with keys: description (str), size (str|None),
    max_price (float|None).
    """
    text = query.strip()
    size = None
    max_price = None

    # --- extract max_price: "under $30", "$30", "under 30" ---
    price_match = re.search(r"(?:under\s+)?\$?(\d+(?:\.\d+)?)", text, re.I)
    if price_match:
        max_price = float(price_match.group(1))
        text = text[:price_match.start()] + text[price_match.end():]

    # --- extract size: standalone S, M, L, XL, XS, XXS, XXL, or "size N" ---
    size_match = re.search(
        r"\bsize\s+([A-Z]{1,3}|\d+)\b|(?<!\w)(XXS|XS|XL|XXL|[SML])(?!\w)",
        text, re.I
    )
    if size_match:
        size = (size_match.group(1) or size_match.group(2)).upper()
        text = text[:size_match.start()] + text[size_match.end():]

    # --- clean up leftover punctuation / filler words ---
    description = re.sub(r"[,\-]+", " ", text).strip()
    description = re.sub(r"\s+", " ", description)
    # Remove common stopwords that add no search value
    description = re.sub(r"\b(a|an|the|for|and|in|on|at|of|under|over|with|size)\b",
                         " ", description, flags=re.I).strip()
    description = re.sub(r"\s+", " ", description)

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language.
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. Check session["error"] first — if it isn't None,
        the run ended early and the later fields will still be None.

    Branch rule:
        If search_listings returns an empty list, put a message in
        session["error"] and return immediately — do NOT call suggest_outfit
        with nothing. Otherwise take the first result, continue to
        suggest_outfit, then create_fit_card.
        Implemented in: agent.py::run_agent
    """
    session = new_session(query, wardrobe)
    iteration = 0

    try:
        # ── step 1: parse the query ───────────────────────────────────────────
        iteration += 1
        trace.check_iterations(iteration)
        parsed = _parse_query(query)
        session["parsed"] = parsed

        # ── step 2: search listings ───────────────────────────────────────────
        iteration += 1
        trace.check_iterations(iteration)
        results = search_listings(
            description=parsed["description"],
            size=parsed["size"],
            max_price=parsed["max_price"],
        )
        session["search_results"] = results

        # ── BRANCH: if nothing came back, stop here ───────────────────────────
        if not results:
            desc = parsed["description"] or query
            hints = []
            if parsed["max_price"] is not None:
                hints.append(f"raise the price ceiling above ${parsed['max_price']:.0f}")
            if parsed["size"] is not None:
                hints.append(f"try a different size (searched for '{parsed['size']}')")
            if not hints:
                hints.append("try different keywords")
            session["error"] = (
                f"No listings matched '{desc}'. To find something, you could: "
                + "; or ".join(hints) + "."
            )
            return session

        # ── step 3: pick the top result ───────────────────────────────────────
        iteration += 1
        trace.check_iterations(iteration)
        session["selected_item"] = results[0]

        # ── step 4: suggest an outfit ─────────────────────────────────────────
        iteration += 1
        trace.check_iterations(iteration)
        outfit = suggest_outfit(
            new_item=session["selected_item"],
            wardrobe=session["wardrobe"],
        )
        session["outfit_suggestion"] = outfit

        # ── step 5: create the fit card ───────────────────────────────────────
        iteration += 1
        trace.check_iterations(iteration)
        fit_card = create_fit_card(
            outfit=session["outfit_suggestion"],
            new_item=session["selected_item"],
        )
        session["fit_card"] = fit_card

    except ModelUnavailable as exc:
        session["error"] = (
            f"The model couldn't be reached: {exc}. "
            "Check your GEMINI_API_KEY in .env and try again."
        )

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
