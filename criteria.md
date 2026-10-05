# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
My search uses plain keyword overlap, which means an unusual phrasing can score
zero even when a matching item exists in the data. For example, "band shirt"
scores lower than "graphic tee" even though both describe the same kind of item.
I set 4 of 5 rather than 5 of 5 to account for one phrasing miss or a rate-limit
retry that produces an empty model response on the first attempt.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path is deterministic: the branch only checks whether `search_results` is
an empty list, which is never ambiguous. There is no model call involved, no
variation between runs, and no data edge case. Either the list is empty and the
agent stops, or it isn't. 5 of 5 is the right target because anything less would
mean the branch is broken on some runs, which is an architectural defect rather
than an acceptable miss rate.

---

## 3. State passes through cleanly: selected_item matches what suggest_outfit received

For 5 of 5 successful runs (runs where search_listings returns at least one
result), `session["selected_item"]` is a dict with a non-empty `"title"` field,
and the outfit suggestion string returned by `suggest_outfit` contains at least
one word from that item's title.

**Why this target:**
State failure is invisible in the final output — if the wrong item reaches
`suggest_outfit`, the fit card is generated for the wrong thing and nothing
crashes. The only way to catch it is to compare what the search found against
what the outfit tool actually received. I picked "at least one word from the
title" as the observable because `suggest_outfit` always names the item in its
response; if the item changed mid-session the name would no longer appear. 5 of
5 because state passing is either working or broken — there is no version of it
that works 4 out of 5 times.

---

## 4. The fit card mentions the item's price and platform every time

For 5 of 5 successful runs, `session["fit_card"]` is a string that contains the
item's price (as a number, e.g. "24" or "24.0") and the platform name (one of
"depop", "thredUp", or "poshmark").

**Why this target:**
The fit card prompt explicitly asks the model to mention price and platform once
each. These two facts are what make the caption actionable — without a price and
a platform, the reader cannot find or buy the item. A caption missing either is
not a useful fit card. I picked 5 of 5 because the prompt is explicit and the
model consistently includes what it is asked to include when the instruction is
direct. If it misses on even one of five tries, the prompt needs to be fixed, not
the target lowered.

---

## 5. The empty-wardrobe path returns a non-empty outfit suggestion

When the agent is run with an empty wardrobe (`wardrobe["items"]` is `[]`),
`session["outfit_suggestion"]` is a non-empty string (at least 20 characters)
in 5 of 5 tries, and `session["fit_card"]` is also non-empty.

**Why this target:**
A new user with no saved wardrobe is a realistic case, not an edge case —
someone just starting to thrift has nothing saved yet. If the agent crashes or
returns an empty string in this case, it is useless for its primary audience.
I chose "at least 20 characters" as the observable because an empty string or
a single-word fallback would technically be non-empty but would not be useful
advice. 5 of 5 because the empty-wardrobe branch in `suggest_outfit` is a
deliberate fallback — if it fails, the code is wrong, not the data.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
