# AI_USAGE_LOG.md

Record of how AI was used on this project. Two AI tools were used deliberately,
in distinct roles, to mirror the assignment's "navigator / reviewer /
decision-maker" framing:

- **Claude (Claude Code)** — primary pair: planning, implementation, test
  authoring, debugging.
- **OpenAI Codex CLI** — independent *reviewer* run headlessly
  (`codex exec --sandbox read-only`) so a second model audited the code without
  being able to change it.

I (the human) stayed the decision-maker: I chose the simulation-date strategy,
accepted/rejected each AI finding, and owned the final code.

---

## Interaction 1 — Understand the provided baseline
- **Task:** Figure out what the instructor-provided `main.py`/`test_main.py`
  actually do before changing anything.
- **Prompt (Claude):** "Read all three files and explain end-to-end exactly what
  the code does, with the real run output."
- **Response summary:** Mapped the load/print layer and the simulation layer;
  confirmed all 20 provided tests pass and all 5 seed orders deliver.
- **Decision:** Accepted as analysis only. No code changed yet. Key realization:
  the provided code is a *quantity-only* simulation that never uses `expiry_date`
  in fulfillment.

## Interaction 2 — Independent review of the baseline (Codex)
- **Task:** Get a second opinion on requirement gaps before committing to fixes.
- **Prompt (Codex, read-only):** supplied the functional requirements (Req 3–7)
  and the simulation date, asked for a ranked list of correctness gaps with
  file:line, "do not write code."
- **Response summary:** Codex independently flagged the same three defects Claude
  found — (1) availability ignores expiry, (2) already-expired items never
  flagged, (3) restock can only emit one reason — **plus two more**: (4) no
  business summary exists, (5) the existing tests *encode* the wrong behavior
  (they expect expired Flour to be deducted).
- **Accepted:** All five findings. Two independent models agreeing raised
  confidence to high.
- **Rejected/deferred:** None. Finding (5) reframed my plan: updating those tests
  is *correcting wrong expectations*, which I documented rather than silently
  changing.

## Interaction 3 — Decision: how should expiry behave?
- **Task:** Decide whether expired stock should block fulfillment, and which
  simulation date to use.
- **Process:** Traced the seed expiry dates. Found they form three tiers (Jan =
  expired, May 12 = expiring soon, Oct/Nov = fresh) that are only coherent just
  before 2026-05-12. At the real "today" (2026-06-17) nothing is within 5 days of
  expiry, so Req 6's expiring-soon rule would be dead code.
- **Decision (mine):** Expiry **blocks** fulfillment (strict reading of Req 3 +
  Task 5), and `SIMULATION_DATE = 2026-05-10` so the seed data exercises every
  rule. Documented the rationale in `PROJECT_SPEC.md §5`.

## Interaction 4 — Implementation (Claude)
- **Task:** Implement the fixes incrementally.
- **Prompts (Claude):** one change at a time — extract business-rule constants;
  make `check_inventory_availability` expiry-aware; rewrite
  `calculate_restock_needs` to accumulate multiple reasons + flag expired;
  add `build_summary`/`print_summary`/`write_markdown_report` (Option D).
- **Accepted with edits:** Kept the restock schema change (`reasons` list +
  joined `reason` + `expiry_date`). Updated 6 existing tests to the corrected
  behavior and added 9 new tests. All 29 then 32 passing.

## Interaction 5 — Review of my changes (Codex)
- **Prompt (Codex, read-only):** "Re-review the updated code. Any remaining bugs?
  Is multiple-reasons genuinely satisfied? Does qty_needed make sense in every
  branch? Edge cases the tests miss?"
- **Response summary:** Confirmed multiple-reasons satisfied and `qty_needed`
  coherent. Flagged one **Medium** real bug: a failed order's `reason` can contain
  `" | "`, which breaks the Markdown table; plus minor items (summary aliases the
  restock list; untested edges).
- **Accepted:** Added `_md_cell()` pipe-escaping; switched `build_summary` to
  snapshot the restock list with `deepcopy`; added edge tests (expired+low qty,
  date boundaries, Markdown escaping).
- **Rejected:** The "duplicate inventory rows" concern — the seed schema is one
  row per ingredient, so I documented it as an explicit assumption instead of
  coding for a case that cannot occur with this data.

## Interaction 6 — Option C + final review (Codex)
- **Task:** Add dynamic menu disabling (Option C) and verify it.
- **Prompt (Codex, read-only):** "Review `evaluate_menu_availability` for
  correctness; is disabling on out-of-stock/expired but not low consistent?"
- **Response summary:** Consistency confirmed. Flagged one **High** gap: it
  disabled on `qty == 0` but not on "nonzero yet below one serving."
- **Accepted:** Added an `Insufficient quantity` branch + a test. Final suite: 37
  tests, all passing.
- **Rejected:** Codex's note that adding `recipe_data` before `reference_date` in
  `build_summary` is a back-compat risk — every real call site uses keywords or
  correct positions, and there are no external callers, so I left it.

---

## What this log demonstrates
- AI accelerated drafting and review, but **every** AI suggestion was evaluated:
  some accepted (pipe-escaping, insufficient-serving check), some reframed
  (test updates), some rejected (duplicate rows, param-order).
- Using a *second* model as an adversarial reviewer caught a real Markdown bug
  the implementer missed — concrete evidence of "review, don't rubber-stamp."
