# Cloud Kitchen Inventory Simulation

> **Johns Hopkins University — Module 3 / Assignment 3:** AI-Assisted Coding for
> a Cloud Kitchen Inventory Simulation.

A Python simulation of one shift in a delivery-only cloud kitchen where multiple
brands share one pantry. It processes orders against recipe-linked inventory,
fulfills them all-or-nothing with expiry-aware availability, deducts stock
cumulatively, plans restocking, and produces a business summary.

Built as an AI-assisted coding assignment using Claude (implementation) and
OpenAI Codex (independent review) — see `WRITEUP.md` and `AI_USAGE_LOG.md`.

## Requirements
- Python 3.10+ (developed on 3.14). Standard library only — no dependencies.

## Run the simulation
```bash
python3 main.py
```
Prints the full simulation and the end-of-shift summary, and writes `REPORT.md`
(a polished Markdown business report).

## Run the tests
```bash
python3 -m unittest -v
```
38 unit tests covering loading, recipe lookup, availability, fulfillment,
cumulative deduction, restock/expiry rules, the business summary, and the
menu-disabling and reporting enhancements.

## Files
| File | Purpose |
| --- | --- |
| `seed_data.py` | Starting data (recipes, inventory, orders, restock, status) |
| `main.py` | Simulation logic + console + Markdown report |
| `test_main.py` | Unit tests |
| `PROJECT_SPEC.md` | Design spec, business rules, decisions |
| `AI_USAGE_LOG.md` | How AI was used (Claude + Codex) |
| `REFLECTION.md` | Reflection on AI-assisted coding |
| `WRITEUP.md` | Full written response |
| `REPORT.md` | Generated business report (created on run) |

## Key design choice
The simulation runs at a fixed scenario date (`SIMULATION_DATE = 2026-05-10`),
not wall-clock time, so the seed data exercises every restock category and runs
are deterministic. Rationale in `PROJECT_SPEC.md §5`.
