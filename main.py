"""Cloud kitchen inventory simulation: order fulfillment, cumulative
inventory deduction, expiry-aware availability, restock planning, and a
business-friendly summary."""

from copy import deepcopy
from datetime import date, datetime

from seed_data import inventory, orders, recipes, restock, status

# --- Business-rule constants (Requirement 6) --------------------------------
# Centralized so thresholds are not hard-coded in the middle of the logic.
PAR_LEVEL_GRAMS = 10000           # target stock level we restock back up to
LOW_STOCK_THRESHOLD_GRAMS = 1000  # at/below this (but >0) = "Running low on stock"
EXPIRING_SOON_DAYS = 5            # within this many days of expiry = "Expiring soon"

# The simulation date. This is a *scenario* date, not wall-clock time, so runs
# are deterministic and tests are reproducible. It is set to just before the
# 2026-05-12 batch expiry so the seed data exercises every restock category:
# Jan-dated items (Chocolate, Pasta) read as already EXPIRED, the 2026-05-12
# batch (Flour, Romaine, Sugar) reads as EXPIRING SOON, and the rest are fresh.
# See PROJECT_SPEC.md for the full rationale.
SIMULATION_DATE = date(2026, 5, 10)

# Reason labels (single source of truth for restock/availability messaging).
REASON_EXPIRED = "Expired"
REASON_EXPIRING_SOON = "Expiring soon"
REASON_OUT_OF_STOCK = "Out of stock"
REASON_RUNNING_LOW = "Running low on stock"
REASON_NOT_IN_INVENTORY = "Not in inventory"
REASON_INSUFFICIENT_FOR_ORDER = "Insufficient quantity for order"


def load_recipes():
    """Return the seeded recipe records for use in the application."""
    # Assumption to verify: importing these module-level lists directly is acceptable
    # for Task 1, and we do not yet need defensive copying or a database/file loader.
    return recipes


def print_recipes(recipe_data):
    """Print every recipe and its ingredient requirements to the console."""
    print("\n=== Recipes ===")
    for recipe in recipe_data:
        print(f"Recipe ID: {recipe['recipe_id']}")
        print(f"Name: {recipe['name']}")
        print("Ingredients:")
        for ingredient in recipe["ingredients"]:
            print(f"  - {ingredient['name']}: {ingredient['qty_grams']} grams")
        print()


def load_inventory():
    """Return the seeded inventory records for the simulation."""
    # Assumption to verify: inventory quantities are intentionally stored in grams
    # for every ingredient, including items like buns that might later use unit counts.
    return inventory


def print_inventory(inventory_data):
    """Print every inventory item with quantity and expiry information."""
    print("\n=== Inventory ===")
    for item in inventory_data:
        print(f"Ingredient: {item['ingredient']}")
        print(f"Quantity: {item['qty_grams']} grams")
        print(f"Expiry Date: {item['expiry_date']}")
        print()


def load_orders():
    """Return the seeded customer order records."""
    # Assumption to verify: order item names are expected to match recipe names exactly.
    return orders


def print_orders(order_data):
    """Print every order, including its brand and requested items."""
    print("\n=== Orders ===")
    for order in order_data:
        print(f"Order ID: {order['order_id']}")
        print(f"Brand: {order['brand']}")
        print("Items:")
        for item in order["items"]:
            print(f"  - {item['item']}: {item['qty']}")
        print()


def load_restock():
    """Return the seeded restock recommendations."""
    # Incomplete / follow-up: the seed table is still available for baseline loading
    # tests, but the live restock output is now recalculated from final inventory.
    return restock


def print_restock(restock_data):
    """Print every restock item with quantity needed and reason."""
    print("\n=== Restock ===")
    for item in restock_data:
        print(f"Item: {item['item']}")
        print(f"Quantity Needed: {item['qty_needed_grams']} grams")
        print(f"Reason: {item['reason']}")
        print()


def load_status():
    """Return the seeded delivery status records."""
    # Uncertain: it is not yet clear whether status should remain independent seed
    # data or later be derived from order fulfillment results in the simulation.
    return status


def print_status(status_data):
    """Print every order status with delivery result and remark."""
    print("\n=== Status ===")
    for entry in status_data:
        print(f"Order ID: {entry['order_id']}")
        print(f"Delivered: {entry['delivered']}")
        print(f"Remark: {entry['remark']}")
        print()


def find_recipe_by_name(recipe_data, item_name):
    """Return the recipe that matches an order item name, or None if missing."""
    # Step 1: look through the recipe table for a recipe whose name matches
    # the order item exactly so we can determine the required ingredients.
    # Assumption to verify: recipe lookup currently relies on exact name matching
    # between Orders.item and Recipes.name, with no normalization or aliases.
    for recipe in recipe_data:
        if recipe["name"] == item_name:
            return recipe
    # Assumption to verify: case-insensitive matching, trimming, or brand-specific
    # recipe variants are not needed yet for successful recipe lookup.
    return None


def calculate_ingredient_requirements(recipe, quantity):
    """Return the total grams required for each ingredient in an order item."""
    requirements = []

    # Step 2: multiply each recipe ingredient quantity by the ordered item count
    # so we know the total grams needed to prepare that order item.
    for ingredient in recipe["ingredients"]:
        requirements.append(
            {
                "name": ingredient["name"],
                "required_qty_grams": ingredient["qty_grams"] * quantity,
            }
        )

    return requirements


def days_until_expiry(expiry_date_str, reference_date):
    """Return whole days from reference_date to an ISO expiry date (negative if past)."""
    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    return (expiry_date - reference_date).days


def check_inventory_availability(inventory_data, requirements, reference_date=None):
    """Check whether inventory can fulfill every required ingredient.

    An ingredient is available only if it (a) exists in inventory, (b) has enough
    grams, and (c) is NOT already expired as of reference_date. Expired stock is
    treated as unusable per Requirement 3, even when the gram count looks adequate.
    """
    if reference_date is None:
        reference_date = SIMULATION_DATE

    inventory_lookup = {item["ingredient"]: item for item in inventory_data}
    availability_results = []
    all_available = True

    # Step 3: compare each required ingredient against the inventory table to see
    # whether it exists, has enough grams, and is not expired.
    for requirement in requirements:
        inventory_item = inventory_lookup.get(requirement["name"])
        available_qty = inventory_item["qty_grams"] if inventory_item else 0

        # Expiry only applies when the ingredient exists and carries an expiry date.
        is_expired = False
        if inventory_item is not None and inventory_item.get("expiry_date"):
            is_expired = days_until_expiry(inventory_item["expiry_date"], reference_date) < 0

        has_enough = inventory_item is not None and available_qty >= requirement["required_qty_grams"]
        is_available = has_enough and not is_expired

        # Build a precise reason so failed orders can explain exactly what went wrong.
        if inventory_item is None:
            reason = "Not in inventory"
        elif is_expired:
            reason = "Expired"
        elif not has_enough:
            reason = "Insufficient quantity"
        else:
            reason = "Available"

        availability_results.append(
            {
                "ingredient": requirement["name"],
                "required_qty_grams": requirement["required_qty_grams"],
                "available_qty_grams": available_qty,
                "expiry_date": inventory_item.get("expiry_date") if inventory_item else None,
                "is_expired": is_expired,
                "is_available": is_available,
                "reason": reason,
            }
        )

        if not is_available:
            all_available = False

    return {"all_available": all_available, "details": availability_results}


def build_failed_order_restock_entry(availability_detail):
    """Create a restock entry for an ingredient that blocked a specific order."""
    available_qty = availability_detail["available_qty_grams"]
    failure_reason = availability_detail["reason"]

    if failure_reason == "Expired":
        restock_reason = REASON_EXPIRED
        qty_needed_grams = PAR_LEVEL_GRAMS
    elif failure_reason == "Not in inventory":
        restock_reason = REASON_NOT_IN_INVENTORY
        qty_needed_grams = PAR_LEVEL_GRAMS
    elif available_qty == 0:
        restock_reason = REASON_OUT_OF_STOCK
        qty_needed_grams = PAR_LEVEL_GRAMS
    else:
        restock_reason = REASON_INSUFFICIENT_FOR_ORDER
        qty_needed_grams = max(PAR_LEVEL_GRAMS - available_qty, 0)

    return {
        "item": availability_detail["ingredient"],
        "qty_needed_grams": qty_needed_grams,
        "reasons": [restock_reason],
        "reason": restock_reason,
        "expiry_date": availability_detail.get("expiry_date"),
    }


def merge_restock_recommendation(restock_data, recommendation):
    """Merge a recommendation into restock_data without losing existing reasons."""
    for item in restock_data:
        if item["item"] != recommendation["item"]:
            continue

        existing_reasons = item.get("reasons", item["reason"].split("; "))
        for reason in recommendation.get("reasons", [recommendation["reason"]]):
            if reason not in existing_reasons:
                existing_reasons.append(reason)

        item["reasons"] = existing_reasons
        item["reason"] = "; ".join(existing_reasons)
        item["qty_needed_grams"] = max(
            item["qty_needed_grams"], recommendation["qty_needed_grams"]
        )
        if not item.get("expiry_date"):
            item["expiry_date"] = recommendation.get("expiry_date")
        return

    restock_data.append(recommendation)


def combine_requirements(requirement_groups):
    """Merge repeated ingredient requirements into a single total per ingredient."""
    combined_requirements = {}

    # Step 2: combine ingredient demand across all items in the same order so
    # fulfillment is checked against the total grams needed for the entire order.
    for requirements in requirement_groups:
        for requirement in requirements:
            ingredient_name = requirement["name"]
            combined_requirements.setdefault(ingredient_name, 0)
            combined_requirements[ingredient_name] += requirement["required_qty_grams"]

    return [
        {"name": ingredient_name, "required_qty_grams": required_qty}
        for ingredient_name, required_qty in combined_requirements.items()
    ]


def deduct_inventory(inventory_data, requirements):
    """Subtract the used ingredient grams from inventory after a successful order."""
    inventory_lookup = {item["ingredient"]: item for item in inventory_data}

    # Step 4: deduct only after the full order passes the availability check so
    # we do not partially consume stock for orders that cannot be delivered.
    # Assumption to verify: partial stock should not be deducted for failed orders;
    # inventory changes only when the entire order is considered deliverable.
    for requirement in requirements:
        inventory_lookup[requirement["name"]]["qty_grams"] -= requirement["required_qty_grams"]


def apply_final_inventory_snapshot(inventory_data, final_inventory_data):
    """Copy the final cumulative inventory quantities back into the main table."""
    final_inventory_lookup = {
        item["ingredient"]: item["qty_grams"] for item in final_inventory_data
    }

    # Step 6: update the final inventory table only after all orders have been
    # processed so the printed inventory reflects the true remaining stock.
    for item in inventory_data:
        if item["ingredient"] in final_inventory_lookup:
            item["qty_grams"] = final_inventory_lookup[item["ingredient"]]


def update_status_entry(status_data, order_id, delivered, remark):
    """Update or create a status-table entry for a processed order."""
    for entry in status_data:
        if entry["order_id"] == order_id:
            entry["delivered"] = delivered
            entry["remark"] = remark
            return

    # Incomplete / follow-up: if later tasks formalize a stricter schema, we may
    # want to prevent new status rows and require every order to exist up front.
    status_data.append({"order_id": order_id, "delivered": delivered, "remark": remark})


def calculate_restock_needs(inventory_data, reference_date=None):
    """Build restock recommendations from final inventory using the Requirement 6 rules.

    An ingredient may qualify for MORE THAN ONE reason (e.g. both expired and low).
    All applicable reasons are preserved in a `reasons` list rather than overwritten.
    """
    if reference_date is None:
        reference_date = SIMULATION_DATE

    restock_recommendations = []

    for item in inventory_data:
        qty = item["qty_grams"]
        reasons = []

        # Expiry reasons. Expired stock is unusable and expiring-soon stock will
        # spoil before it is consumed, so either way the on-hand grams cannot be
        # counted on and we plan a full par-level replacement.
        needs_full_replacement = False
        if item.get("expiry_date"):
            days_left = days_until_expiry(item["expiry_date"], reference_date)
            if days_left < 0:
                reasons.append(REASON_EXPIRED)
                needs_full_replacement = True
            elif days_left <= EXPIRING_SOON_DAYS:
                reasons.append(REASON_EXPIRING_SOON)
                needs_full_replacement = True

        # Stock-level reasons. These accumulate alongside any expiry reason above,
        # so an item that is both expiring and low keeps BOTH labels (Requirement 6).
        if qty == 0:
            reasons.append(REASON_OUT_OF_STOCK)
        elif qty <= LOW_STOCK_THRESHOLD_GRAMS:
            reasons.append(REASON_RUNNING_LOW)

        if not reasons:
            continue

        # If the stock is unusable (expired/expiring), order a full par-level refill;
        # otherwise top up only the shortfall needed to reach par level.
        if needs_full_replacement:
            qty_needed_grams = PAR_LEVEL_GRAMS
        else:
            qty_needed_grams = PAR_LEVEL_GRAMS - qty

        restock_recommendations.append(
            {
                "item": item["ingredient"],
                "qty_needed_grams": qty_needed_grams,
                "reasons": reasons,
                "reason": "; ".join(reasons),  # joined string for display/back-compat
                "expiry_date": item.get("expiry_date"),
            }
        )

    return restock_recommendations


def refresh_restock_table(restock_data, inventory_data, reference_date=None):
    """Replace the live restock table with recommendations from final inventory."""
    # Step 7: rebuild the restock table after all orders have been processed so it
    # reflects the final inventory state; failed-order blockers are merged after this.
    # Incomplete / follow-up: this replaces the whole restock table each run, so it
    # does not preserve historical/manual restock notes outside the current simulation.
    restock_data.clear()
    restock_data.extend(calculate_restock_needs(inventory_data, reference_date))


def process_orders(
    recipe_data,
    inventory_data,
    order_data,
    status_data,
    restock_data,
    reference_date=None,
):
    """Process orders, update fulfillment status, deduct inventory, and add restocks."""
    if reference_date is None:
        reference_date = SIMULATION_DATE

    processed_orders = []
    working_inventory = deepcopy(inventory_data)
    failed_order_restock = []

    # Step 0: use a working inventory snapshot during processing so each order is
    # checked against stock remaining after previous successful orders, while the
    # final inventory table is only updated once the full order list is complete.
    # Assumption to verify: working_inventory is a deep copy, not a shared reference,
    # so interim deductions during processing do not immediately mutate inventory_data.
    # Incomplete / follow-up: this remains an in-memory simulation only; later tasks
    # may need transaction handling or persistence if inventory state is stored externally.

    for order in order_data:
        order_result = {
            "order_id": order["order_id"],
            "brand": order["brand"],
            "items": [],
            "order_requirements": [],
            "inventory_check": None,
            "fulfilled": False,
            "reason": "",
        }
        requirement_groups = []
        missing_recipe_items = []

        for item in order["items"]:
            # Step 1: find the recipe for the ordered menu item.
            recipe = find_recipe_by_name(recipe_data, item["item"])

            if recipe is None:
                # If an order item has no matching recipe, we do not stop the program
                # or attempt substitution. We record recipe_found=False, skip demand
                # calculation and inventory checking for that item, and continue.
                # Incomplete / follow-up: later tasks may convert this into a formal
                # rejection reason, validation error, or fulfillment status update.
                order_result["items"].append(
                    {
                        "item": item["item"],
                        "qty": item["qty"],
                        "recipe_found": False,
                        "requirements": [],
                    }
                )
                missing_recipe_items.append(item["item"])
                continue

            # Step 2: calculate the total ingredient grams needed for this order item.
            requirements = calculate_ingredient_requirements(recipe, item["qty"])
            requirement_groups.append(requirements)

            order_result["items"].append(
                {
                    "item": item["item"],
                    "qty": item["qty"],
                    "recipe_found": True,
                    "requirements": requirements,
                }
            )

        order_requirements = combine_requirements(requirement_groups)
        order_result["order_requirements"] = order_requirements

        # Step 3: check the inventory table against the total ingredient demand for
        # the whole order, not just individual items, before deciding fulfillment.
        # Because this uses working_inventory, Order 2 is checked against whatever
        # stock remains after Order 1 was successfully served.
        # If two orders compete for the same ingredient, the earlier successful order
        # consumes from working_inventory first, and the later order is evaluated
        # against the reduced quantity that remains.
        inventory_check = check_inventory_availability(
            working_inventory, order_requirements, reference_date
        )
        order_result["inventory_check"] = inventory_check

        missing_ingredients = [
            detail for detail in inventory_check["details"] if not detail["is_available"]
        ]

        if missing_recipe_items:
            reason_parts = [
                "No matching recipe for item(s): " + ", ".join(missing_recipe_items)
            ]
            if missing_ingredients:
                reason_parts.append(
                    "Unavailable ingredients: "
                    + ", ".join(
                        f"{detail['ingredient']} ({detail['reason']})"
                        for detail in missing_ingredients
                    )
                )

            order_result["fulfilled"] = False
            order_result["reason"] = " | ".join(reason_parts)
            update_status_entry(status_data, order["order_id"], False, order_result["reason"])
            for detail in missing_ingredients:
                failed_order_restock.append(build_failed_order_restock_entry(detail))
        elif inventory_check["all_available"]:
            # Step 4: when every required ingredient is available, mark the order as
            # delivered and deduct the used grams from the working inventory only.
            deduct_inventory(working_inventory, order_requirements)
            order_result["fulfilled"] = True
            order_result["reason"] = "Delivered"
            update_status_entry(status_data, order["order_id"], True, "Delivered")
        else:
            # Step 5: when any ingredient is missing or insufficient, do not deduct
            # inventory. Mark the order as not delivered, record the reason, and add
            # the shortage reason to status. The final restock table is rebuilt later
            # from ending inventory according to the Task 5 expiry/stock rules.
            # Note: this flow rejects the full order rather than allowing partial
            # fulfillment of the items that do have enough usable stock (all-or-nothing).
            missing_names = ", ".join(
                f"{detail['ingredient']} ({detail['reason']})"
                for detail in missing_ingredients
            )
            order_result["fulfilled"] = False
            order_result["reason"] = f"Unavailable ingredients: {missing_names}"
            update_status_entry(status_data, order["order_id"], False, order_result["reason"])
            for detail in missing_ingredients:
                failed_order_restock.append(build_failed_order_restock_entry(detail))

        processed_orders.append(order_result)

    apply_final_inventory_snapshot(inventory_data, working_inventory)
    refresh_restock_table(restock_data, inventory_data, reference_date)
    for recommendation in failed_order_restock:
        merge_restock_recommendation(restock_data, recommendation)

    return processed_orders


def print_order_processing_results(processed_orders):
    """Print recipe lookup, ingredient demand, inventory checks, and fulfillment."""
    print("\n=== Order Processing ===")
    for order in processed_orders:
        print(f"Order ID: {order['order_id']}")
        print(f"Brand: {order['brand']}")

        for item in order["items"]:
            print(f"Item: {item['item']}")
            print(f"Quantity Ordered: {item['qty']}")
            print(f"Recipe Found: {item['recipe_found']}")

            if not item["recipe_found"]:
                print("Inventory Check: Skipped because the recipe was not found.")
                print()
                continue

            print("Required Ingredients:")
            for requirement in item["requirements"]:
                print(
                    f"  - {requirement['name']}: "
                    f"{requirement['required_qty_grams']} grams required"
                )

            print()

        print("Combined Order Requirements:")
        for requirement in order["order_requirements"]:
            print(f"  - {requirement['name']}: {requirement['required_qty_grams']} grams required")

        print(f"All Ingredients Available: {order['inventory_check']['all_available']}")
        print("Inventory Details:")
        for detail in order["inventory_check"]["details"]:
            print(
                f"  - {detail['ingredient']}: "
                f"required={detail['required_qty_grams']} grams, "
                f"available={detail['available_qty_grams']} grams, "
                f"enough={detail['is_available']}"
            )

        print(f"Fulfilled: {order['fulfilled']}")
        print(f"Reason: {order['reason']}")
        print()


def summarize_expiry_concerns(inventory_data, reference_date=None):
    """Return inventory items that are expired or expiring soon as of reference_date."""
    if reference_date is None:
        reference_date = SIMULATION_DATE

    concerns = []
    for item in inventory_data:
        if not item.get("expiry_date"):
            continue
        days_left = days_until_expiry(item["expiry_date"], reference_date)
        if days_left < 0:
            state = REASON_EXPIRED
        elif days_left <= EXPIRING_SOON_DAYS:
            state = REASON_EXPIRING_SOON
        else:
            continue
        concerns.append(
            {
                "ingredient": item["ingredient"],
                "expiry_date": item["expiry_date"],
                "days_until_expiry": days_left,
                "state": state,
            }
        )
    return concerns


def evaluate_menu_availability(recipe_data, inventory_data, reference_date=None):
    """Flag menu items that should be disabled (Option C enhancement).

    A menu item is unavailable when any required ingredient is missing, out of
    stock, or expired — i.e. unusable. Evaluated against current (post-shift)
    inventory so the menu reflects what the kitchen can actually cook right now.
    Running-low (but non-zero, unexpired) stock does NOT disable an item, since
    at least one more serving can still be made.
    """
    if reference_date is None:
        reference_date = SIMULATION_DATE

    inventory_lookup = {item["ingredient"]: item for item in inventory_data}
    menu = []
    for recipe in recipe_data:
        blocked_by = []
        for ingredient in recipe["ingredients"]:
            inventory_item = inventory_lookup.get(ingredient["name"])
            needed = ingredient["qty_grams"]  # grams for a single serving
            if inventory_item is None:
                blocked_by.append({"ingredient": ingredient["name"], "reason": "Not in inventory"})
            elif inventory_item.get("expiry_date") and (
                days_until_expiry(inventory_item["expiry_date"], reference_date) < 0
            ):
                blocked_by.append({"ingredient": ingredient["name"], "reason": REASON_EXPIRED})
            elif inventory_item["qty_grams"] == 0:
                blocked_by.append({"ingredient": ingredient["name"], "reason": REASON_OUT_OF_STOCK})
            elif inventory_item["qty_grams"] < needed:
                # In stock, but not even enough for one serving -> still can't cook it.
                blocked_by.append(
                    {"ingredient": ingredient["name"], "reason": "Insufficient quantity"}
                )
        menu.append(
            {
                "item": recipe["name"],
                "available": not blocked_by,
                "blocked_by": blocked_by,
            }
        )
    return menu


def build_summary(
    processed_orders, inventory_data, restock_data, recipe_data=None, reference_date=None
):
    """Assemble a business-friendly summary dictionary (Requirement 7).

    Returning structured data (rather than only printing) lets the same summary
    feed both the console report and the Markdown export, and makes it testable.
    When recipe_data is supplied, a disabled-menu section is included (Option C).
    """
    if reference_date is None:
        reference_date = SIMULATION_DATE

    menu = (
        evaluate_menu_availability(recipe_data, inventory_data, reference_date)
        if recipe_data is not None
        else []
    )

    delivered = [order for order in processed_orders if order["fulfilled"]]
    not_delivered = [order for order in processed_orders if not order["fulfilled"]]

    return {
        "simulation_date": reference_date.isoformat(),
        "orders_total": len(processed_orders),
        "orders_delivered": len(delivered),
        "orders_not_delivered": len(not_delivered),
        "delivered": [
            {"order_id": order["order_id"], "brand": order["brand"]} for order in delivered
        ],
        "not_delivered": [
            {
                "order_id": order["order_id"],
                "brand": order["brand"],
                "reason": order["reason"],
            }
            for order in not_delivered
        ],
        "final_inventory": [
            {
                "ingredient": item["ingredient"],
                "qty_grams": item["qty_grams"],
                "expiry_date": item.get("expiry_date"),
            }
            for item in inventory_data
        ],
        "restock": deepcopy(restock_data),  # snapshot so later mutation can't alter summary
        "expiry_concerns": summarize_expiry_concerns(inventory_data, reference_date),
        "menu": menu,
    }


def print_summary(summary):
    """Print the business summary for a non-technical kitchen manager (Requirement 7)."""
    print("\n" + "=" * 50)
    print("  CLOUD KITCHEN END-OF-SHIFT SUMMARY")
    print(f"  Simulation date: {summary['simulation_date']}")
    print("=" * 50)

    print(
        f"\nOrders delivered: {summary['orders_delivered']} of {summary['orders_total']}"
    )
    for order in summary["delivered"]:
        print(f"  + Order {order['order_id']} ({order['brand']}): Delivered")

    print(f"\nOrders NOT delivered: {summary['orders_not_delivered']}")
    for order in summary["not_delivered"]:
        print(f"  - Order {order['order_id']} ({order['brand']}): {order['reason']}")

    print("\nFinal inventory levels:")
    for item in summary["final_inventory"]:
        print(f"  - {item['ingredient']}: {item['qty_grams']} g (expires {item['expiry_date']})")

    print("\nRestock recommendations:")
    if not summary["restock"]:
        print("  (none)")
    for item in summary["restock"]:
        print(
            f"  - {item['item']}: order {item['qty_needed_grams']} g "
            f"[{item['reason']}]"
        )

    print("\nExpiry concerns:")
    if not summary["expiry_concerns"]:
        print("  (none)")
    for concern in summary["expiry_concerns"]:
        if concern["state"] == REASON_EXPIRED:
            detail = f"expired {abs(concern['days_until_expiry'])} day(s) ago"
        else:
            detail = f"expires in {concern['days_until_expiry']} day(s)"
        print(f"  - {concern['ingredient']}: {concern['state']} ({detail})")

    if summary.get("menu"):
        disabled = [entry for entry in summary["menu"] if not entry["available"]]
        print("\nMenu items disabled (Option C):")
        if not disabled:
            print("  (none)")
        for entry in disabled:
            blockers = ", ".join(
                f"{block['ingredient']} ({block['reason']})" for block in entry["blocked_by"]
            )
            print(f"  - {entry['item']}: unavailable — {blockers}")
    print()


def _md_cell(value):
    """Escape a value for safe inclusion in a Markdown table cell.

    Free-text fields (brands, failure reasons) can contain pipe characters that
    would otherwise split a table row into extra columns, so we escape them.
    """
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_markdown_report(summary, file_path="REPORT.md"):
    """Write the summary to a polished Markdown business report (Option D enhancement)."""
    lines = []
    lines.append("# Cloud Kitchen — End-of-Shift Report")
    lines.append("")
    lines.append(f"**Simulation date:** {summary['simulation_date']}")
    lines.append("")
    lines.append(
        f"**Orders delivered:** {summary['orders_delivered']} of {summary['orders_total']}  "
    )
    lines.append(f"**Orders not delivered:** {summary['orders_not_delivered']}")
    lines.append("")

    lines.append("## Delivered Orders")
    lines.append("")
    if summary["delivered"]:
        lines.append("| Order | Brand |")
        lines.append("| --- | --- |")
        for order in summary["delivered"]:
            lines.append(f"| {order['order_id']} | {_md_cell(order['brand'])} |")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Orders Not Delivered")
    lines.append("")
    if summary["not_delivered"]:
        lines.append("| Order | Brand | Reason |")
        lines.append("| --- | --- | --- |")
        for order in summary["not_delivered"]:
            lines.append(
                f"| {order['order_id']} | {_md_cell(order['brand'])} "
                f"| {_md_cell(order['reason'])} |"
            )
    else:
        lines.append("_All orders fulfilled._")
    lines.append("")

    lines.append("## Final Inventory")
    lines.append("")
    lines.append("| Ingredient | Quantity (g) | Expiry |")
    lines.append("| --- | ---: | --- |")
    for item in summary["final_inventory"]:
        lines.append(
            f"| {_md_cell(item['ingredient'])} | {item['qty_grams']} | {item['expiry_date']} |"
        )
    lines.append("")

    lines.append("## Restock Recommendations")
    lines.append("")
    if summary["restock"]:
        lines.append("| Ingredient | Order (g) | Reason(s) | Expiry |")
        lines.append("| --- | ---: | --- | --- |")
        for item in summary["restock"]:
            lines.append(
                f"| {_md_cell(item['item'])} | {item['qty_needed_grams']} "
                f"| {_md_cell(item['reason'])} | {item.get('expiry_date', '')} |"
            )
    else:
        lines.append("_Nothing to restock._")
    lines.append("")

    lines.append("## Expiry Concerns")
    lines.append("")
    if summary["expiry_concerns"]:
        lines.append("| Ingredient | State | Expiry | Days |")
        lines.append("| --- | --- | --- | ---: |")
        for concern in summary["expiry_concerns"]:
            lines.append(
                f"| {_md_cell(concern['ingredient'])} | {concern['state']} "
                f"| {concern['expiry_date']} | {concern['days_until_expiry']} |"
            )
    else:
        lines.append("_No expiry concerns._")
    lines.append("")

    if summary.get("menu"):
        lines.append("## Menu Availability (Option C)")
        lines.append("")
        lines.append("| Menu Item | Status | Blocked By |")
        lines.append("| --- | --- | --- |")
        for entry in summary["menu"]:
            status = "Available" if entry["available"] else "DISABLED"
            blockers = ", ".join(
                f"{block['ingredient']} ({block['reason']})" for block in entry["blocked_by"]
            )
            lines.append(
                f"| {_md_cell(entry['item'])} | {status} | {_md_cell(blockers) or '—'} |"
            )
        lines.append("")

    report_text = "\n".join(lines)
    with open(file_path, "w", encoding="utf-8") as report_file:
        report_file.write(report_text)
    return report_text


def main():
    """Load seed tables, process fulfillment, and print the updated results."""
    # Assumption to verify: we process working copies of mutable tables so the seed
    # definitions stay unchanged across runs and tests.
    # Incomplete / follow-up: this script still prints results directly to the console
    # and does not yet persist updated inventory, restock, or status tables anywhere.
    recipe_data = load_recipes()
    inventory_data = deepcopy(load_inventory())
    order_data = load_orders()
    # Step 8: start with an empty live restock table because recommendations are
    # now generated from final inventory after all orders have been processed.
    restock_data = []
    status_data = deepcopy(load_status())
    processed_orders = process_orders(
        recipe_data,
        inventory_data,
        order_data,
        status_data,
        restock_data,
    )

    print_recipes(recipe_data)
    print_orders(order_data)
    print_order_processing_results(processed_orders)
    print_inventory(inventory_data)
    print_restock(restock_data)
    print_status(status_data)

    # Requirement 7: business-friendly end-of-shift summary, plus a Markdown
    # report export (Option D enhancement) written to REPORT.md.
    summary = build_summary(processed_orders, inventory_data, restock_data, recipe_data)
    print_summary(summary)
    write_markdown_report(summary)


if __name__ == "__main__":
    main()
