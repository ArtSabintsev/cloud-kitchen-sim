# Cloud Kitchen Inventory Simulation — Written Response

Follows the assignment's suggested structure. Companion documents:
`PROJECT_SPEC.md` (design), `AI_USAGE_LOG.md` (AI process), `REFLECTION.md`
(reflection, also Section 11 below).

## 1. Project Setup
Files: `seed_data.py` (data), `main.py` (logic + reporting), `test_main.py`
(38 unit tests), `PROJECT_SPEC.md`, `AI_USAGE_LOG.md`, `REFLECTION.md`, this
write-up, and a generated `REPORT.md`.

- **Run:** `python3 main.py` — prints the full simulation and writes `REPORT.md`.
- **Test:** `python3 -m unittest -v` (or `python3 -m unittest test_main`).
- **Setup notes:** Python 3.14, standard library only (no third-party deps). The
  provided `seed_data-1.py` was renamed to `seed_data.py` so `main.py`'s
  `from seed_data import ...` resolves.

## 2. Data Loading
The five seed tables (recipes, inventory, orders, restock, status) are loaded by
`load_*` functions and rendered by `print_*` functions (Requirement 1). I
inspected the *actual* schema rather than assuming one — notably that inventory
is one row per ingredient with an ISO `expiry_date`, and that the seed `restock`
and `status` tables are recomputed at runtime (the seed versions are retained
only so the loader tests have something to assert against).

## 3. Recipe Lookup and Ingredient Calculation
`find_recipe_by_name` does exact, case-sensitive name matching and returns `None`
for unknown items (handled gracefully, never crashes).
`calculate_ingredient_requirements` scales each ingredient by the ordered
quantity, and `combine_requirements` sums duplicate ingredients across an order's
items so availability is checked against whole-order demand (Requirement 2).

## 4. Inventory Availability
`check_inventory_availability` reports, per ingredient, required vs. available
grams, an `is_expired` flag, availability, and a precise reason
(`Available` / `Insufficient quantity` / `Expired` / `Not in inventory`). Expired
stock is treated as **unusable** even when the gram count is adequate
(Requirement 3) — see Section 7 / `PROJECT_SPEC.md §5` for the rationale.

## 5. Order Fulfillment
`process_orders` applies **all-or-nothing** fulfillment (Requirement 4): if every
required ingredient is available and unexpired, the order is marked Delivered and
the grams are deducted; otherwise it is Not Delivered, nothing is deducted, and
the status/`reason` records exactly which ingredients failed and why. Missing
recipes are reported as their own failure reason.

## 6. Cumulative Processing
Deductions run against a working deep-copy of inventory, so order *N* is checked
against what orders *1…N-1* left behind (Requirement 5). In the seed run, Order 5's
45 Chicken Burgers drain Chicken Breast to 800 g, which then drives a restock
recommendation. The final inventory table is written back only after all orders
are processed.

## 7. Restock and Expiry Logic
`calculate_restock_needs` flags Out of stock (0 g), Running low (≤1,000 g),
Expiring soon (≤5 days), and Expired (past date). Crucially, reasons **accumulate**
— an item that is both expiring and low keeps *both* labels in a `reasons` list
(Requirement 6), fixing a defect in the baseline that could only emit one reason.
Unusable (expired/expiring) stock requests a full 10,000 g par-level refill;
merely-low stock requests only the shortfall to par.

**Simulation date.** I use `SIMULATION_DATE = 2026-05-10`, not wall-clock time.
The seed expiry dates form three deliberate tiers (January = expired, 2026-05-12
= expiring soon, Oct/Nov = fresh) that are only coherent just before May 12; at
the real "today" the entire expiring-soon tier has rotted to expired and nothing
is within 5 days of expiry, which would make Req 6's expiring-soon rule dead code.
A fixed date also makes runs deterministic and tests reproducible.

## 8. Business Summary
`build_summary` produces a structured summary and `print_summary` renders it for
a non-technical manager (Requirement 7): delivered/not-delivered counts, failure
reasons, final inventory, restock recommendations, and expiry concerns. Result at
the simulation date: **4 of 5 delivered**; Order 3 fails on expired Pasta and
Chocolate; Chicken Breast is low; Flour/Romaine/Sugar are expiring soon.

**Enhancements (extra credit).** *Option D:* `write_markdown_report` exports a
polished `REPORT.md`. *Option C:* `evaluate_menu_availability` disables menu items
whose ingredients are missing, out of stock, expired, or below one serving — in
the seed run it correctly disables Pasta Alfredo and Chocolate Cake.

## 9. Refactoring Notes
Two concrete improvements (more in `AI_USAGE_LOG.md`):
1. **Extracted business-rule constants** (`PAR_LEVEL_GRAMS`,
   `LOW_STOCK_THRESHOLD_GRAMS`, `EXPIRING_SOON_DAYS`, `SIMULATION_DATE`, reason
   labels) instead of magic numbers/strings scattered through the logic.
2. **Refactored restock from `if/elif` to reason accumulation**, which both fixed
   the multiple-reasons requirement and removed the duplicated `10000`/`reason`
   assignments. Also hardened the Markdown export with `_md_cell()` pipe-escaping
   after an AI review caught that failure reasons can corrupt table rows.

## 10. AI Usage Summary
Two AI tools in distinct roles: **Claude** as the implementation pair and
**OpenAI Codex** (run headless, read-only) as an independent adversarial reviewer.
Three Codex review passes audited the baseline and my changes; they confirmed the
core fixes and caught a real Markdown-injection bug and an Option C edge case.
Every suggestion was evaluated, not rubber-stamped — accepted, reframed, or
rejected with reasons. Full transcript-level detail is in `AI_USAGE_LOG.md`.

## 11. Reflection
The full 400–600 word reflection is in **`REFLECTION.md`** and answers all six
required questions: how AI sped up the read/review loops; where it produced
plausible-but-wrong code (single-reason restock, expiry-blind fulfillment,
Markdown injection); how tests turned unease into verdicts and exposed tests that
encoded wrong expectations; what I changed vs. rejected; how `PROJECT_SPEC.md`
anchored the non-obvious simulation-date decision; and what I'd do differently
(spec-and-characterization-tests first, adversarial review earlier).
