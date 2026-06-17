# PROJECT_SPEC.md — Cloud Kitchen Inventory Simulation

> External memory for the project. Updated throughout the assignment.
> Status legend: ✅ done · 🟡 in progress · ⬜ not started

## 1. Project Purpose

Simulate one shift of a delivery-only **cloud kitchen** where multiple virtual
brands share one pantry. The program processes customer orders against
recipe-linked inventory, decides which orders can be fulfilled, deducts
ingredients cumulatively, plans restocking, tracks expiry risk, and produces a
business-friendly summary for a non-technical kitchen manager.

The assignment's real goal is to demonstrate **AI-assisted development under
human supervision** — planning, reviewing AI output critically, testing, and
debugging — not just shipping working code.

## 2. Files & Components

| File | Purpose | Status |
| --- | --- | --- |
| `seed_data.py` | Starting data: recipes, inventory, orders, restock, status | ✅ |
| `main.py` | Simulation logic + console + Markdown report | ✅ |
| `test_main.py` | Unit tests (38) | ✅ |
| `PROJECT_SPEC.md` | This file | ✅ (living) |
| `AI_USAGE_LOG.md` | Record of AI interactions | ✅ |
| `REFLECTION.md` | 400–600 word reflection | ✅ |
| `REPORT.md` | Generated business report (Option D) | ✅ generated on run |

### Key functions (`main.py`)
- `load_*` / `print_*` — load and display the five seed tables (Req 1).
- `find_recipe_by_name`, `calculate_ingredient_requirements`, `combine_requirements` — recipe lookup + quantity scaling (Req 2).
- `days_until_expiry`, `check_inventory_availability` — expiry-aware availability (Req 3).
- `deduct_inventory`, `process_orders` — fulfillment + cumulative deduction (Req 4–5).
- `calculate_restock_needs`, `refresh_restock_table` — restock & expiry rules (Req 6).
- `summarize_expiry_concerns`, `evaluate_menu_availability`, `build_summary`,
  `print_summary`, `write_markdown_report` — business summary + Option C/D
  reporting (Req 7).

## 3. Data Structures (as provided — inspected, not assumed)

- **recipes**: `list[{recipe_id, name, ingredients:[{name, qty_grams}]}]`
- **inventory**: `list[{ingredient, qty_grams, expiry_date "YYYY-MM-DD"}]` — **one row per ingredient**.
- **orders**: `list[{order_id, brand, items:[{item, qty}]}]`
- **restock** (seed): `list[{item, qty_needed_grams, reason}]` — *recomputed at runtime; seed kept only for load tests.*
- **status** (seed): `list[{order_id, delivered, remark}]` — *recomputed at runtime.*

## 4. Business Rules

| Rule | Value | Constant |
| --- | --- | --- |
| Par level (restock target) | 10,000 g | `PAR_LEVEL_GRAMS` |
| Running low | qty ≤ 1,000 g (and > 0) | `LOW_STOCK_THRESHOLD_GRAMS` |
| Expiring soon | within 5 days of sim date | `EXPIRING_SOON_DAYS` |
| Expired | expiry date strictly before sim date | (days < 0) |
| Simulation date | **2026-05-10** | `SIMULATION_DATE` |

- **Fulfillment is all-or-nothing.** A delivered order deducts all its grams; a
  failed order deducts nothing and records a reason.
- **Expired stock is unusable.** It blocks fulfillment (Req 3) and is flagged in
  restock/expiry concerns (Req 6).
- **Restock reasons accumulate.** An item can be flagged for multiple reasons
  (e.g. `Expired` + `Running low`); all are preserved (Req 6).
- **Restock quantity:** unusable stock (expired/expiring) → full par (10,000 g);
  merely low/out → top up the shortfall to par.

## 5. Design Decisions (and why)

1. **Simulation date = 2026-05-10, not wall-clock "today".**
   The seed expiry dates form three deliberate tiers: January (Chocolate, Pasta)
   = *expired*, 2026-05-12 (Flour, Romaine, Sugar) = *expiring soon*, Oct/Nov =
   *fresh*. That tiering is only coherent just before 2026-05-12. At the real
   "today" (2026-06-17) the entire "expiring soon" tier has rotted to "expired"
   and **nothing** is within 5 days of expiry, making Req 6's expiring-soon rule
   dead code. Using a fixed scenario date also makes runs deterministic and
   tests reproducible. Result at 2026-05-10: Orders 1,2,4,5 delivered; Order 3
   fails on expired Pasta/Chocolate; Chicken runs low from Order 5's 45 burgers.

2. **Expiry blocks fulfillment (strict reading of Req 3 + Task 5).** Req 3 lists
   "Expiry status" as a factor in deciding "whether the order can be fulfilled,"
   and Task 5 makes an expired-ingredient case a required test. Reporting-only
   would not satisfy "can be fulfilled."

3. **Restock entry schema extended** to `{item, qty_needed_grams, reasons[],
   reason (joined str), expiry_date}`. The `reasons` list is the source of truth
   for the multiple-reasons requirement; `reason` is a display/back-compat join.

4. **Restock table is rebuilt from final inventory** after all orders, then
   merged with failed-order blockers so Task 6 shortages are not lost when the
   final stock level is above the general low-stock threshold.

5. **Working-copy discipline.** `process_orders` deducts against a deep copy and
   writes back only at the end; `main()` deep-copies seed tables so seed data is
   never mutated across runs/tests.

## 6. Testing Plan / Status — ✅ 38 tests, all passing

- Loaders: types, counts, key fields (Req 1 / Task 3).
- Recipe lookup + scaling, missing recipe (Task 4).
- Availability: fresh available, expired unusable, missing (Task 5).
- Fulfillment: delivered, failed-on-shortage, expired-blocked, deduction, no
  deduction on failure, failed-order blockers added to restock even when final
  stock is not generally low (Task 6).
- Cumulative: shared-ingredient deduction, later-order starvation, final
  quantities (Task 7).
- Restock: out/low/expiring/expired, **multiple reasons**, qty per branch,
  date boundaries (0 / 5 / 6 days) (Task 8).
- Summary/menu/reporting: delivered/not-delivered counts, expiry concerns,
  Markdown pipe escaping, Option C menu disabling (Task 9 / Options C-D).

Run: `python3 -m unittest -v`

## 7. Known Issues / Assumptions

- **One inventory row per ingredient** is assumed (matches seed). Multiple
  batches of the same ingredient would collapse in the name→row lookup. Out of
  scope; documented rather than coded.
- **Recipe lookup is exact, case-sensitive** name matching (no aliases/trimming).
- **In-memory only** — no persistence; state resets each run.
- Quantities are grams for every ingredient, including unit-like items (buns).

## 8. Current / Next Task

- Current: ✅ All 11 required tasks + Option D complete; docs written.
- Next (if extended): persistence layer; partial fulfillment (Option A);
  predictive stockout (Option B); per-batch inventory.
