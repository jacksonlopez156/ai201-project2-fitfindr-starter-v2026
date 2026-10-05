# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr is a three-tool AI agent that helps thrift shoppers find and style
secondhand items. A user describes what they're looking for — like "vintage
graphic tee under $30" — and the agent searches a listings database, suggests
an outfit combining the find with pieces the user already owns, and writes a
short social-media caption they could actually post. If the search comes back
empty, the agent stops early and tells the user exactly what to change rather
than calling the model with nothing to work with.

---

## Tool Inventory

### `search_listings`

- **What it does:** Searches the listings database for items matching a
  description and optional size and price filters; scores results by keyword
  overlap and returns the best matches.
- **Inputs:** `description` (str) — keywords describing the item;
  `size` (str | None) — size token to filter by (e.g. `"M"`), or `None` to
  skip size filtering; `max_price` (float | None) — inclusive price ceiling
  in dollars, or `None` to skip price filtering.
- **Returns:** A list of listing dicts, each containing `id` (str),
  `title` (str), `description` (str), `category` (str), `style_tags`
  (list[str]), `size` (str), `condition` (str), `price` (float),
  `colors` (list[str]), `brand` (str | None), `platform` (str); sorted by
  keyword-overlap score, best match first, at most
  `config.SEARCH_RESULT_LIMIT` items.
- **When it has nothing:** Returns an empty list `[]` — never `None`, never
  raises. The loop branches on this.

### `suggest_outfit`

- **What it does:** Given the item the user is considering and their saved
  wardrobe, asks the model to suggest one or two specific outfits.
- **Inputs:** `new_item` (dict) — a listing dict from `search_listings`;
  `wardrobe` (dict) — a wardrobe dict with an `"items"` key holding a list
  of wardrobe item dicts (may be empty).
- **Returns:** A non-empty string of outfit suggestions, two to four
  sentences, naming specific pieces from the wardrobe when available.
- **When it has nothing:** When `wardrobe["items"]` is empty, returns
  general styling advice for the item type rather than raising or returning
  an empty string.

### `create_fit_card`

- **What it does:** Writes a short social-media caption for the thrift find,
  mentioning the item, price, and platform, styled to read like a real post.
- **Inputs:** `outfit` (str) — the outfit suggestion from `suggest_outfit`;
  `new_item` (dict) — the listing dict for the item being captioned.
- **Returns:** A two-to-four sentence caption string that mentions the
  item's title, its price as a number, and the platform name exactly once.
- **When it has nothing:** If `outfit` is empty or whitespace, returns the
  string `"No outfit suggestion available — cannot generate a fit card."`.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put a
human-readable message in `session["error"]` naming what the user could
change (price ceiling, size, or keywords) and return the session immediately
— do NOT call `suggest_outfit` with an empty results list. Otherwise, take
the first result, store it in `session["selected_item"]`, pass it to
`suggest_outfit` along with the wardrobe, store the response in
`session["outfit_suggestion"]`, then pass that and the item to
`create_fit_card`, storing the result in `session["fit_card"]`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex. A `re.search` pattern extracts the price
ceiling (`$30`, `under $30`, `under 30`), a second pattern extracts size
tokens (`S`, `M`, `L`, `XL`, `XS`, `XXS`, `XXL`, or `size N`), and the
remaining text — with common stopwords removed — becomes the keyword
description passed to `search_listings`. Implemented in
`agent.py::_parse_query`.

**What moves through the session:** `query` → `parsed` (description, size,
max_price) → `search_results` (list of listing dicts) → `selected_item`
(the first result) → `outfit_suggestion` (model response string) →
`fit_card` (model response string). `error` is set and the session returned
early if `search_results` is empty.

---

## Sample Run

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit Suggestion:** Pair the Y2K butterfly baby tee with the
  baggy straight-leg dark wash jeans and chunky white sneakers.

  **Why it works:** This combination nails the authentic turn-of-the-millennium
  aesthetic by balancing the fitted, cropped silhouette of the tee with the
  relaxed, low-key volume of the baggy jeans. Tossing on the black crossbody
  bag and layering the vintage black denim jacket over top pulls the whole look
  together with a cool, effortless edge.

  Fit card: Living in my Y2K era with the cutest little butterfly baby tee.
  Grab this piece on my depop right now for just $18.00! Style it with baggy
  dark-wash denim and chunky sneakers to instantly nail that effortless
  turn-of-the-millennium vibe.

0 model calls this session, 2 served from cache
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; r = search_listings('graphic tee', max_price=30); print(len(r), 'results'); [print(x['title'], x['price']) for x in r[:3]]"
7 results
Y2K Baby Tee — Butterfly Print 18.0
Graphic Tee — 2003 Tour Bootleg Style 24.0
Mesh Long-Sleeve Top — Black 15.0
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit:** Pair the Vintage Levi's 501 Jeans with the white ribbed tank top,
the oversized grey crewneck sweatshirt layered on top, and the chunky white
sneakers.

**Why it works:** This creates an effortless, streetwear-inspired casual look
where the relaxed grey crewneck and fresh white sneakers complement the classic
medium wash of the vintage denim.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Nothing beats the fit of broken-in vintage denim, and these classic Levi's 501
jeans in the dreamiest medium wash are absolute perfection. Throw them on with
some fresh white sneakers for that effortless streetwear look everyone's
chasing. Grab this staple for just $38.0 on depop before I change my mind and
keep them!
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* Help deciding how to handle size filtering safely —
  the data has sizes like "S/M", "One Size / Oversized", and "W30 L30", and
  a plain substring check (`"s" in "us 9"`) would match the wrong things.
- *What came back:* The suggestion was to split on `/`, spaces, and commas
  to tokenize the listing's size field and then test for exact token
  membership, so `"M"` would match `"m"` in `["s", "m"]` from `"S/M"` but
  not match `"xl"` or `"us"`.
- *What I changed:* Implemented `_size_matches()` in `tools.py` using
  `re.split(r"[/\s,]+", listing_size.lower())` and a token-membership check,
  replacing the substring approach I had initially drafted.

**Moment 2**

- *What I asked for:* Whether my error message for an empty search result
  was specific enough — the original draft just said "No results found."
- *What came back:* Feedback that "No results found" gives the user nothing
  actionable; a better message names the specific filters that were applied
  and suggests which ones to relax.
- *What I changed:* Rewrote the branch in `run_agent()` to build a hints
  list from the parsed filters — if a price ceiling was applied it suggests
  raising it; if a size was applied it names the size; if neither, it says
  to try different keywords. The message now reads like "No listings matched
  'designer ballgown'. To find something, you could: raise the price ceiling
  above $5; or try a different size (searched for 'XXS')."

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
